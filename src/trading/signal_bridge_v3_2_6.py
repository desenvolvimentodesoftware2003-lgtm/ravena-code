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
  - Utilizar Qwen 3.5 e Kimi K2.5 na OCI para orquestração e raciocínio avançado.
"""
import os
import sys
import time
import logging
import json
import hashlib
import asyncio
import importlib.util
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

try:
    import oci # Biblioteca OCI SDK para integração com Generative AI
except ImportError:
    oci = None

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
        logging.FileHandler(
            os.path.join(_LOG_DIR, f"signal_bridge_{datetime.now().strftime('%Y%m%d')}.log")
        )
    ]
)
logger = logging.getLogger("ravena.signal_bridge")

# ─────────────────────────────────────────────
# Configurações OCI e Carregamento de Config
# ─────────────────────────────────────────────
OCI_COMPARTMENT_ID = os.getenv("OCI_COMPARTMENT_ID")
QWEN_ENDPOINT_ID = os.getenv("QWEN_ENDPOINT_ID")
KIMI_ENDPOINT_ID = os.getenv("KIMI_ENDPOINT_ID")
CONFIG_PATH = os.getenv("RAVENA_CONFIG_PATH", "config_v3.json")

# Módulo de Filtro de Simulação (60 agentes)
_SIMULACAO_FILTER = None
try:
    _sf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "..", "simulation", "simulacao_filter_v3.2.6.py")
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
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar config: {e}")
        return {}

# ─────────────────────────────────────────────
# Lógica de Suitability Dinâmico (Recuperado v2.2.0)
# ─────────────────────────────────────────────
def determine_suitability_mode(balance: float, config: Dict[str, Any]) -> str:
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
    tech_confidence: float, 
    sentiment_score: float, 
    visual_confirmed: bool,
    audit_cleared: bool
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
# Lógica de Orquestração com LLMs OCI
# ─────────────────────────────────────────────
def get_llm_recommendation(prompt: str, endpoint_id: str) -> Dict[str, Any]:
    """Obtém recomendação do LLM na OCI."""
    if not oci:
        logger.warning("OCI SDK nao instalado. Simulando resposta do LLM.")
        return {"confidence_score": 0.95, "analysis": "Simulacao de analise tecnica positiva."}
    if not endpoint_id or not OCI_COMPARTMENT_ID:
        logger.warning("OCI endpoint ou compartment nao configurado. Simulando resposta.")
        return {"confidence_score": 0.95, "analysis": "Simulacao de analise tecnica positiva."}
    
    try:
        config_oci = oci.config.from_file()
        generative_ai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(config_oci)
        generate_text_details = oci.generative_ai_inference.models.GenerateTextDetails(
            compartment_id=OCI_COMPARTMENT_ID,
            endpoint_id=endpoint_id,
            prompt=prompt,
            max_tokens=512,
            temperature=0.7
        )
        response = generative_ai_client.generate_text(generate_text_details)
        return json.loads(response.data.generated_text)
    except Exception as e:
        logger.error(f"Erro ao obter recomendação do LLM: {e}")
        return {}

# ─────────────────────────────────────────────
# Processamento de Sinal Reintegrado v3.1.0
# ─────────────────────────────────────────────
def process_signal(raw_data: Dict[str, Any], current_balance: float = 0.0) -> Dict[str, Any]:
    """
    Processa o sinal bruto usando Qwen 3.5, Kimi K2.5 e Lógicas de Elite.

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
            - 'oci_analysis': Saída bruta da análise Qwen 3.5.
            - 'oci_decision': Saída bruta da decisão Kimi K2.5.
            - 'raw_search_agent_data': O relatório original completo do SearchAgent 360.
    """
    logger.info("Iniciando processamento de sinal reintegrado v3.1.0...")
    
    config_data = load_config()
    suitability_mode = determine_suitability_mode(current_balance, config_data)
    mode_params = config_data.get("suitability_dynamic_gate", {}).get("modes", {}).get(suitability_mode, {})

    # 1. Raciocínio e Análise com Qwen 3.5
    qwen_prompt = f"Analise os seguintes dados de mercado: {json.dumps(raw_data)}. Forneça análise técnica e score."
    qwen_analysis = get_llm_recommendation(qwen_prompt, QWEN_ENDPOINT_ID)
    
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

    # 5. Orquestração e Decisão Final com Kimi K2.5
    kimi_prompt = f"Com base na análise (Prob: {final_prob}): {json.dumps(qwen_analysis)}, formate o pacote de execução final."
    kimi_decision = get_llm_recommendation(kimi_prompt, KIMI_ENDPOINT_ID)

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
        "oci_analysis": qwen_analysis,
        "oci_decision": kimi_decision,
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
