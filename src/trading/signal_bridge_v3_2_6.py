"""
SIGNAL_BRIDGE — Tradutor de Sinais / Ponte de Dados (v3.1.0-REINTEGRATED)
========================================================================
Ravena AI Trading Bot | Versão: 3.1.0 | Data: 20 de Abril de 2026
Este módulo é o "tecido conectivo" que transforma a inteligência coletada
pelo Agente de Busca 360 em comandos de execução precisos.
Responsabilidades:
  - Receber o relatório bruto do Agente de Busca 360 e compactar em um "Pacote de Execução".
  - Aplicar o filtro de Suitability Dinâmico baseado no saldo USDT (Recuperado v2.2.0).
  - Calcular a Probabilidade de Sucesso Ponderada (Recuperado v2.2.0).
  - Integrar-se ao HealthMonitor do Self-Healing V2.2.0.
  - Orquestrar análise (Qwen) e decisão (Kimi) com modelos LOCAIS em
    data/models via llama.cpp — sem OCI e sem resposta simulada.
"""

import asyncio
import hashlib
import importlib.util
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────
# Configuração de Logging
# ─────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(_LOG_DIR, f"signal_bridge_{datetime.now().strftime('%Y%m%d')}.log")),
    ],
)
logger = logging.getLogger("ravena.signal_bridge")


def _achar_config_v3() -> str:
    """Caminho de config_v3.json, independente do cwd.

    O default era o caminho RELATIVO "config_v3.json": da raiz do repo
    funcionava, de qualquer outro diretorio devolvia {} sem erro
    visivel — e ai suitability_mode, audit_required e o limiar de
    brutalidade saem do default em vez do arquivo. Foi o que fez
    test_manus_ai_level.py reprovar (ciclos_autocorrecao 0 != 1) num
    checkout onde o arquivo nao estava na raiz.

    Ordem: $RAVENA_CONFIG_PATH, depois config/config_v3.json subindo a
    partir da pasta deste modulo. O caminho solto segue aceito para
    checkout antigo.
    """
    env = os.getenv("RAVENA_CONFIG_PATH")
    if env:
        return env
    d = Path(__file__).resolve().parent
    for _ in range(6):
        p = d / "config" / "config_v3.json"
        if p.is_file():
            return str(p)
        p = d / "config_v3.json"
        if p.is_file():
            return str(p)
        novo = d.parent
        if novo == d:
            break
        d = novo
    return "config/config_v3.json"


# ─────────────────────────────────────────────
# Modelos LOCAIS (llama.cpp) e Carregamento de Config
# ─────────────────────────────────────────────
# Trilho real de inferência: GGUFs em data/models, um modelo residente
# por vez (qwen=análise, kimi=decisão), sob demanda. Sem OCI e sem
# fallback simulado: falha real vira log de erro e dict vazio — quem
# consome cai no dado bruto, nunca em número inventado.
_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MODELOS_LOCAIS = {
    "qwen": os.path.join(_RAIZ_PROJETO, "data", "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf"),
    "kimi": os.path.join(_RAIZ_PROJETO, "data", "models", "Qwen3.5-9B-Kimi-k3-Distilled.Q4_K_M.gguf"),
}
_CACHE_MODELOS: dict[str, Any] = {}
CONFIG_PATH = os.getenv("RAVENA_CONFIG_PATH") or _achar_config_v3()

# Módulo de Filtro de Simulação (60 agentes)
_SIMULACAO_FILTER = None
try:
    _sf_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "simulation", "simulacao_filter_v3_2_6.py"
    )
    _sf_path = os.path.abspath(_sf_path)
    _spec_sf = importlib.util.spec_from_file_location("simulacao_filter_mod", _sf_path)
    _sf_mod = importlib.util.module_from_spec(_spec_sf)
    _spec_sf.loader.exec_module(_sf_mod)
    _SIMULACAO_FILTER = _sf_mod
    logger.info(f"SimulacaoFilter carregado de {_sf_path}")
except Exception as e:
    logger.warning(f"SimulacaoFilter nao carregado: {e}")


def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar config: {e}")
        return {}


# ─────────────────────────────────────────────
# Lógica de Suitability Dinâmico (Recuperado v2.2.0)
# ─────────────────────────────────────────────
def determine_suitability_mode(balance: float, config: dict[str, Any]) -> str:
    """Determina o modo de suitability com base no saldo USDT."""
    modes = config.get("suitability_dynamic_gate", {}).get("modes", {})
    if balance < modes.get("AGGRESSIVE", {}).get("balance_limit", 10000):
        return "AGGRESSIVE"
    elif balance < modes.get("MODERATE", {}).get("balance_limit", 50000):
        return "MODERATE"
    else:
        return "CONSERVATIVE"


# ─────────────────────────────────────────────
# Cálculo de Probabilidade Ponderada (Recuperado v2.2.0)
# ─────────────────────────────────────────────
def calculate_success_probability(
    tech_confidence: float, sentiment_score: float, visual_confirmed: bool, audit_cleared: bool
) -> float:
    """
    Calcula a probabilidade final baseada nos pesos originais:
    - Técnica: 40%
    - Sentimento: 35%
    - Visual: 25%
    - Bônus Auditoria: +5%
    """
    prob = (tech_confidence * 0.40) + (abs(sentiment_score) * 0.35)
    if visual_confirmed:
        prob += 0.25
    if audit_cleared:
        prob += 0.05

    return min(prob, 1.0)


# ─────────────────────────────────────────────
# Orquestração com LLMs locais (llama.cpp) — sem OCI, sem simulação
# ─────────────────────────────────────────────
def _obter_modelo(papel: str):
    """RavenaModel do papel, carregado sob demanda.

    Só UM modelo residente por vez: a máquina tem RAM limitada e dois
    GGUFs juntos empurravam o processo para o swap (medido: 149s de
    geração no 9B contra ~30s com o outro descarregado). Descarrega o
    modelo do outro papel antes de carregar este — o cache fica na
    página quente do disco, o custo é só o reload (~2s no 1.5B, ~8s
    no 9B) uma vez por ciclo de sinal.
    """
    modelo = _CACHE_MODELOS.get(papel)
    if modelo is None:
        for outro, m in list(_CACHE_MODELOS.items()):
            if outro != papel:
                m.descarregar()
                _CACHE_MODELOS.pop(outro, None)
                logger.info("Modelo %r descarregado para liberar RAM", outro)
        from src.core.ravena_model import RavenaModel

        modelo = RavenaModel(caminho_gguf=_MODELOS_LOCAIS[papel])
        if not modelo.carregar():
            return None
        _CACHE_MODELOS[papel] = modelo
    return modelo


def _extrair_json(texto: str) -> dict[str, Any] | None:
    """Primeiro objeto JSON válido do texto (o modelo às vezes embrulha em prosa)."""
    texto = (texto or "").strip()
    if not texto:
        return None
    ini, fim = texto.find("{"), texto.rfind("}")
    candidatos = [texto] if ini == 0 else [texto[ini : fim + 1]]
    if ini != 0:
        candidatos.append(texto)
    for fatia in candidatos:
        try:
            obj = json.loads(fatia)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def get_llm_recommendation(prompt: str, papel: str) -> dict[str, Any]:
    """Recomendação do modelo LOCAL do papel ("qwen" ou "kimi").

    Resposta real do GGUF em data/models — sem OCI e sem simulação.
    Qualquer falha (arquivo ausente, carga, geração, JSON inválido)
    loga erro e devolve {}: o chamador cai no dado bruto, nunca em
    número inventado.
    """
    caminho = _MODELOS_LOCAIS.get(papel)
    if not caminho:
        logger.error("Papel de LLM desconhecido: %r", papel)
        return {}
    if not os.path.exists(caminho):
        logger.error("GGUF ausente para o papel %r: %s", papel, caminho)
        return {}
    modelo = _obter_modelo(papel)
    if modelo is None:
        logger.error("Modelo local %r falhou ao carregar.", papel)
        return {}

    instrucao = (
        " Responda SOMENTE com um JSON válido, sem texto fora dele, no formato: "
        '{"confidence_score": <número entre 0 e 1>, "analysis": "<análise objetiva em português>"}'
    )
    # forcar_json: gramática do llama.cpp — resposta começa em "{" desde
    # o 1º token (corta o raciocínio em prosa do distill Kimi) e sai
    # parseável. 320 tokens dão folga para o JSON completo.
    texto = modelo.gerar_resposta(prompt + instrucao, max_tokens=320, temperatura=0.2, forcar_json=True)
    if not texto or texto.startswith("Erro"):
        logger.error("Geração falhou no papel %r: %s", papel, texto)
        return {}
    dados = _extrair_json(texto)
    if dados is None:
        logger.error("Resposta do papel %r sem JSON válido: %.200s", papel, texto)
        return {}
    try:
        score = float(dados.get("confidence_score", 0.0))
    except (TypeError, ValueError):
        score = 0.0
    dados["confidence_score"] = min(max(score, 0.0), 1.0)
    dados.setdefault("analysis", "")
    return dados


# ─────────────────────────────────────────────
# Processamento de Sinal Reintegrado v3.1.0
# ─────────────────────────────────────────────
def process_signal(raw_data: dict[str, Any], current_balance: float = 0.0) -> dict[str, Any]:
    """
    Processa o sinal bruto usando Qwen e Kimi locais e Lógicas de Elite.

    Args:
        raw_data (Dict[str, Any]): O relatório bruto do SearchAgent 360, contendo:
            - 'symbol': Símbolo do ativo (ex: 'BTC/USDT')
            - 'tech_confidence': Confiança técnica inicial (float)
            - 'sentiment_score': Score de sentimento (float)
            - 'visual_confirmed': Confirmação visual (bool)
            - 'audit_cleared': Status de auditoria (bool)
            - Outros metadados e indicadores técnicos brutos.
        current_balance (float): Saldo atual em USDT para determinar o modo de suitability.

    Returns:
        Dict[str, Any]: O pacote de execução completo contendo:
            - 'packet_id': Identificador único do pacote.
            - 'timestamp': Data e hora do processamento.
            - 'symbol': Ativo alvo.
            - 'suitability_mode': Modo de risco aplicado.
            - 'success_probability': Probabilidade final calculada.
            - 'status': READY, REJECTED ou HOLD.
            - 'brutality_check': Booleano indicando se passou no threshold de elite.
            - 'sentiment_score': Valor de sentimento usado no cálculo.
            - 'visual_confirmed': Status de confirmação visual.
            - 'audit_cleared': Status de limpeza de auditoria.
            - 'tech_confidence': Confiança técnica final (pós-LLM).
            - 'llm_analysis': Saída real da análise Qwen (modelo local).
            - 'llm_decision': Saída real da decisão Kimi (modelo local).
            - 'raw_search_agent_data': O relatório original completo do SearchAgent 360.
    """
    logger.info("Iniciando processamento de sinal reintegrado v3.1.0...")

    config_data = load_config()
    suitability_mode = determine_suitability_mode(current_balance, config_data)
    mode_params = config_data.get("suitability_dynamic_gate", {}).get("modes", {}).get(suitability_mode, {})

    # 1. Raciocínio e Análise com Qwen (modelo local)
    qwen_prompt = f"Analise os seguintes dados de mercado: {json.dumps(raw_data)}. Forneça análise técnica e score."
    qwen_analysis = get_llm_recommendation(qwen_prompt, "qwen")

    tech_conf = qwen_analysis.get("confidence_score", raw_data.get("tech_confidence", 0.0))
    sent_score = raw_data.get("sentiment_score", 0.0)
    visual_conf = raw_data.get("visual_confirmed", False)
    audit_status = raw_data.get("audit_cleared", False)

    # 2. Filtros de Modo de Suitability
    if abs(sent_score) < mode_params.get("sentiment_threshold", 0.15):
        logger.warning(f"Sinal bloqueado: Sentimento insuficiente para modo {suitability_mode}")
        return {"status": "REJECTED", "reason": "Sentimento insuficiente"}

    if mode_params.get("audit_required") and not audit_status:
        logger.warning("Sinal em HOLD: Aguardando Auditoria (Tijolo 10)")
        return {"status": "HOLD", "reason": "Aguardando Auditoria"}

    # 3. Cálculo da Probabilidade Final (Recuperado)
    final_prob = calculate_success_probability(tech_conf, sent_score, visual_conf, audit_status)

    # 4. Filtro de Elite: 60 Agentes de Simulação com dados reais
    simulacao_result = None
    try:
        filtro = _SIMULACAO_FILTER.SimulacaoFilter(num_agentes=60)
        simulacao_result = asyncio.run(filtro.validar_sinal(raw_data))
        score_brut = simulacao_result.get("score_brutalidade", 0.5)
        final_prob = (final_prob * 0.6) + (score_brut * 0.4)
        logger.info(f"60 agentes: brutalidade={score_brut:.4f} | prob hibrida={final_prob:.4f}")
    except Exception as e:
        logger.warning(f"Filtro de simulacao: {e}")

    # 5. Orquestração e Decisão Final com Kimi (modelo local)
    kimi_prompt = (
        f"Com base na análise (Prob: {final_prob}): {json.dumps(qwen_analysis)}, formate o pacote de execução final."
    )
    kimi_decision = get_llm_recommendation(kimi_prompt, "kimi")

    # 6. Formatação do Pacote de Execução (Elite v3.1.0)
    brutality_threshold = config_data.get("core_settings", {}).get("brutality_threshold", 0.85)

    status = "READY" if final_prob >= brutality_threshold else "REJECTED"
    if simulacao_result and not simulacao_result.get("passou_filtro"):
        logger.warning(f"Sinal REPROVADO pelos 60 agentes ({simulacao_result.get('taxa_vitoria', 0):.2%})")
        status = "REJECTED"

    execution_package = {
        "packet_id": hashlib.sha256(str(time.time()).encode()).hexdigest(),
        "timestamp": datetime.now().isoformat(),
        "symbol": raw_data.get("symbol", "BTC/USDT"),
        "suitability_mode": suitability_mode,
        "success_probability": round(final_prob, 4),
        "status": status,
        "brutality_check": status == "READY",
        "sentiment_score": sent_score,
        "visual_confirmed": visual_conf,
        "audit_cleared": audit_status,
        "tech_confidence": tech_conf,
        "simulacao_60_agentes": simulacao_result,
        "llm_analysis": qwen_analysis,
        "llm_decision": kimi_decision,
        "raw_search_agent_data": raw_data,
    }

    if status == "READY":
        try:
            _ss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "step_scaling.py")
            _spec_ss = importlib.util.spec_from_file_location("step_scaling_mod", _ss_path)
            _ss_mod = importlib.util.module_from_spec(_spec_ss)
            _spec_ss.loader.exec_module(_ss_mod)
            step = _ss_mod.StepScaling(testnet=True)
            ativo = raw_data.get("symbol", "").replace("/", "")
            lado = raw_data.get("signal", "buy")
            lote = max(round(current_balance * 0.02 / 50000, 4), 0.001)
            resultado = step.executar_estrategia(ativo, lado, lote)
            execution_package["step_scaling"] = resultado
            logger.info(f"StepScaling executado: {resultado['status']} em {ativo}")
        except Exception as e:
            logger.warning(f"StepScaling nao executado: {e}")
            execution_package["step_scaling"] = {"status": "ERRO", "motivo": str(e)}

    logger.info(f"Sinal processado: {execution_package['status']} (Prob: {final_prob:.4f})")
    return execution_package


if __name__ == "__main__":
    print("Módulo Signal Bridge v3.1.0-REINTEGRATED carregado com sucesso!")
