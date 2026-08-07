"""
extrair_exemplos_dataset.py — ONE-SHOT
Extrai exemplos expert do cognitive_treino.jsonl e registra no Professor.
Converte logs reais de interacao em pares (resposta_original + correcao_expert)
para alimentar o dataset de fine-tuning do futuro Ravena LLM.

Exclui automaticamente logs de erro/bug (stack traces, exceptions, crashes).
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJETO)

from src.core.professor import Professor

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("extrair_dataset")

# ─── PADROES DE EXCLUSAO (logs de erro/bug) ──────────────────────────────────
# Regra: nenhum padrao isolado dispara. So exclui se MULTIPLOS indicadores
# de erro aparecerem juntos, ou se for um padrao muito especifico de crash.

import re

_PADROES_CRASH = [
    "segmentation fault",
    "core dumped",
    "kernel panic",
    "stack overflow",
    "abort() called",
    "bus error",
]

def _is_error_log(log: dict) -> bool:
    """Retorna True se o log for realmente um log de erro/bug (baixo falso positivo)."""
    texto = (
        (log.get("pergunta", "") or "") + " " +
        (log.get("resposta", "") or "") + " " +
        (log.get("raciocinio", "") or "")
    ).lower()

    # 1. Crash inequivoco (padrao muito especifico — seguro disparar sozinho)
    for p in _PADROES_CRASH:
        if p in texto:
            return True

    # 2. Stack trace Python: exige MULTIPLOS marcadores juntos
    #    "traceback" + "file .py, line N" = muito provavelmente stack trace
    if "traceback" in texto and re.search(r"file.*\.py\", line \d+", texto):
        return True

    # 3. Erro estruturado: exige >= 3 indicadores simultaneos
    #    Um "error:" ou "exception:" sozinho nao basta (falso positivo alto)
    indicadores = 0
    if "traceback" in texto:
        indicadores += 1
    if re.search(r"\berror\b", texto):
        indicadores += 1
    if "exception" in texto:
        indicadores += 1
    if "failed with" in texto:
        indicadores += 1
    if "exit code" in texto:
        indicadores += 1
    if "stderr:" in texto or "stdout:" in texto:
        indicadores += 1
    if re.search(r"file.*\.py\", line \d+", texto):
        indicadores += 1

    return indicadores >= 3

# ─── MAPEAMENTO PERGUNTA → DISCIPLINA ───────────────────────────────────────

_KEYWORD_TO_DISCIPLINA = {
    "contextualidade": "auto_orquestracao",
    "fallback": "auto_orquestracao",
    "omega": "auto_orquestracao",
    "orquestrador": "auto_orquestracao",
    "chat": "auto_orquestracao",
    "telegram": "auto_orquestracao",
    "dashboard": "auto_orquestracao",
    "agentedev": "auto_agentes",
    "dev": "auto_agentes",
    "searchagent": "auto_agentes",
    "search": "auto_agentes",
    "design": "auto_agentes",
    "python": "auto_agentes",
    "docker": "auto_agentes",
    "git": "auto_agentes",
    "programa": "auto_agentes",
    "lockdown": "auto_seguranca",
    "security": "auto_seguranca",
    "seguranca": "auto_seguranca",
    "hacker": "auto_seguranca",
    "zero trust": "auto_seguranca",
    "juiz": "auto_seguranca",
    "signal": "auto_trading",
    "bybit": "auto_trading",
    "trade": "auto_trading",
    "trading": "auto_trading",
    "risk": "auto_trading",
    "scaling": "auto_trading",
    "sentiment": "auto_trading",
    "rag": "auto_rag",
    "chroma": "auto_rag",
    "embedding": "auto_rag",
    "conhecimento": "auto_rag",
    "conhecimentopith": "auto_rag",
    "authority": "auto_rag",
    "clarividencia": "auto_rag",
    "fotossintese": "auto_rag",
    "capital": "auto_rag",
    "brasil": "auto_rag",
    "geopolitica": "auto_rag",
    "guerra": "auto_rag",
    "historia": "auto_rag",
    "dengue": "auto_rag",
    "saude": "auto_rag",
    "ciencia": "auto_rag",
    "topicos": "auto_rag",
    "vision": "auto_visao",
    "visao": "auto_visao",
    "memoria": "auto_memoria",
    "memory": "auto_memoria",
    "analytics": "auto_analytics",
    "metrica": "auto_analytics",
    "empathy": "auto_analytics",
    "sensor": "auto_sensores",
    "cognitive": "auto_sensores",
    "dsl": "auto_dsl",
    "comando": "auto_dsl",
    "inteligencia artificial": "auto_inteligencia",
    "inteligencia": "auto_inteligencia",
    "qwen": "auto_inteligencia",
    "kimi": "auto_inteligencia",
    "encoder": "auto_inteligencia",
    "learning": "auto_learning",
    "lora": "auto_learning",
    "treinamento": "auto_learning",
    "dna": "auto_learning",
    "alimentacao": "auto_alimentacao",
    "ingestao": "auto_alimentacao",
    "wikipedia": "auto_alimentacao",
    "chunk": "auto_alimentacao",
    "lingua portuguesa": "auto_utilitarios",
    "portuguesa": "auto_utilitarios",
    "cultural": "auto_utilitarios",
    "social": "auto_utilitarios",
    "alucinacao": "auto_utilitarios",
    "professor": "auto_professor",
    "metodologia": "auto_professor",
    "didatica": "auto_professor",
    "etica": "auto_professor",
    "filosofia": "auto_professor",
}

# ─── RESPOSTAS CORRETAS ──────────────────────────────────────────────────────

_RESPOSTAS_CORRETAS = {
    "contextualidade": (
        "Contextualidade processa linguagem natural aplicando: "
        "remocao de stopwords em portugues, normalizacao textual, stemming "
        "e extracao de contexto de perguntas para classificacao precisa."
    ),
    "fallback inteligente": (
        "FallbackInteligente e o sistema de fallback da Ravena que, "
        "quando o modelo principal nao consegue responder com confianca >= 0.7, "
        "aplica templates de resposta por dominio (geografia, ciencia, tecnologia, etc.) "
        "ou solicita reformulacao da pergunta em caso de ambiguidade."
    ),
    "lockdown": (
        "Lockdown e o sistema de bloqueio proativo da Ravena: "
        "detecta ameacas (palavras de ataque, comandos de sistema, engenharia social) "
        "e atua com alerta/bloqueio/emergencia para proteger o sistema."
    ),
    "omega": (
        "Omega e o orquestrador central da Ravena, ponto de convergencia de todos os modulos. "
        "Gerencia ciclo de pensamento, conhecimento (RAG), seguranca (Zero Trust), "
        "sensores cognitivos, visao e integracao com agentes especializados."
    ),
    "conhecimentopith": (
        "ConhecimentoPith gerencia a base de conhecimento interna da Ravena com "
        "autoridades (authority_score por grupo tematico) e sistema de crencas. "
        "Grupos: geografia, ciencia, tecnologia, automotivo, historia, matematica, "
        "lingua, saude, filosofia."
    ),
    "python": (
        "Python e uma linguagem de programacao de alto nivel, interpretada, "
        "multiparadigma (orientada a objetos, funcional, estruturada). "
        "Usada extensivamente no ecossistema Ravena para implementacao de "
        "todos os modulos e agentes."
    ),
    "docker": (
        "Docker e uma plataforma de conteinerizacao que permite empacotar "
        "aplicacoes e suas dependencias em containers isolados. "
        "Usado pela Ravena para execucao em sandbox e isolamento de agentes de seguranca."
    ),
    "git": (
        "Git e um sistema de controle de versao distribuido, usado para "
        "versionar todo o codigo fonte do projeto Ravena AIM."
    ),
    "fotossintese": (
        "Fotossintese e o processo bioquimico realizado por plantas, algas e "
        "cianobacterias que converte energia luminosa em energia quimica, "
        "produzindo glicose e oxigenio a partir de dioxido de carbono e agua."
    ),
    "inteligencia artificial": (
        "Inteligencia Artificial e o campo da ciencia da computacao dedicado a "
        "criar sistemas capazes de realizar tarefas que normalmente exigem "
        "inteligencia humana. A Ravena implementa IA via modelos Qwen 3.5 (397B) "
        "para raciocinio e Kimi K2.5 para orquestracao."
    ),
    "segunda guerra mundial": (
        "A Segunda Guerra Mundial (1939-1945) foi o maior conflito armado da historia, "
        "envolvendo a maioria das nacoes do mundo. Dividida em Eixo (Alemanha, Italia, Japao) "
        "vs Aliados (EUA, URSS, Reino Unido, Franca). Resultou em aproximadamente 70 milhoes de mortos."
    ),
    "geopolitica": (
        "Geopolitica e o estudo da influencia de fatores geograficos, economicos e "
        "demograficos sobre a politica internacional e relacoes entre Estados."
    ),
    "etica": (
        "Etica e o ramo da filosofia que estuda os principios que orientam o "
        "comportamento humano, distinguindo certo e errado, bem e mal. "
        "Na IA, a etica aborda vies algoritmico, privacidade, transparencia e responsabilidade."
    ),
    "filosofia": (
        "Filosofia e a investigacao racional sobre questoes fundamentais da existencia, "
        "conhecimento, verdade, moral, mente e linguagem. Surgiu na Grecia Antiga "
        "com Socrates, Platao e Aristoteles."
    ),
    "dengue": (
        "Dengue e uma doeenca viral transmitida pelo mosquito Aedes aegypti. "
        "Sintomas incluem febre alta, dor de cabeca, dor atras dos olhos, "
        "dores musculares e articulares. A prevencao envolve eliminar focos de agua parada."
    ),
    "brasil": (
        "Brasil e o maior pais da America do Sul, com capital Brasilia. "
        "Possui 26 estados e 1 Distrito Federal. Idioma oficial: portugues."
    ),
    "lingua portuguesa": (
        "Lingua Portuguesa e uma lingua romanica originaria do latim vulgar, "
        "falada por cerca de 260 milhoes de pessoas em 9 paises. "
        "E o idioma oficial do Brasil, Portugal, Angola, Mocambique, Cabo Verde, "
        "Guine-Bissau, Sao Tome e Principe, Timor Leste e Guine Equatorial."
    ),
    "topicos conhecimento": (
        "Topicos de conhecimento sao os grupos tematicos da base de conhecimento da Ravena: "
        "geografia, ciencia, tecnologia, automotivo, historia, matematica, lingua, saude, filosofia. "
        "Cada topico possui authority_score que pondera a confianca das informacoes."
    ),
    "geopolitics and middle east": (
        "Geopolitics of the Middle East envolve analise de conflitos regionais, "
        "recursos naturais (petroleo), disputas territoriais e influencia de potencias globais. "
        "A Ravena utiliza o modulo Clarividencia para coletar dados atualizados."
    ),
}


def classificar_pergunta(pergunta: str) -> Optional[str]:
    p_lower = pergunta.lower().strip()
    for keyword, disciplina in _KEYWORD_TO_DISCIPLINA.items():
        if keyword in p_lower:
            return disciplina
    return "auto_rag"


def extrair_assunto(pergunta: str) -> str:
    p_lower = pergunta.lower().strip()
    for prefixo in ["o que e ", "o que faz a classe ", "o que faz "]:
        if p_lower.startswith(prefixo):
            return p_lower[len(prefixo):].strip()
    if p_lower.startswith("resumo de "):
        return p_lower[len("resumo de "):].strip()
    return p_lower


def gerar_correcao(pergunta: str, assunto: str, log: dict) -> dict:
    resposta_correta = _RESPOSTAS_CORRETAS.get(assunto)
    if not resposta_correta:
        resposta_correta = (
            f"Modulo/sistema responsavel por '{assunto}' no ecossistema Ravena. "
            f"Consulte a documentacao em docs/ ou o codigo fonte em src/ para detalhes."
        )
    return {
        "precisao_tecnica": 0.95,
        "completude": 0.90,
        "clareza": 0.85,
        "fundamentacao": 0.95,
        "_meta": {
            "resposta_correta": resposta_correta,
            "referencia": "cognitive_treino.jsonl",
            "timestamp_correcao": datetime.now().isoformat()
        }
    }


def log_para_resposta_original(log: dict) -> dict:
    return {
        "pergunta": log.get("pergunta", ""),
        "resposta_ravena": log.get("resposta", ""),
        "confianca": log.get("confianca", 0),
        "raciocinio": log.get("raciocinio", ""),
        "fonte": log.get("fonte", ""),
        "modulos_usados": log.get("modulos_usados", []),
        "authority_score": log.get("authority_score", 0),
        "timestamp_interacao": log.get("timestamp", ""),
        "precisao_tecnica": 0.3,
        "completude": 0.2,
        "clareza": 0.3,
        "fundamentacao": 0.1
    }


def carregar_logs_processados(caminho: str) -> set:
    if not os.path.exists(caminho):
        return set()
    with open(caminho, "r", encoding="utf-8") as f:
        return set(json.load(f))


def salvar_logs_processados(caminho: str, ids: set):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(sorted(ids), f, ensure_ascii=False, indent=2)


def main():
    prof = Professor()
    caminho_logs = os.path.join(_PROJETO, "data", "cognitive_treino.jsonl")
    caminho_tracking = os.path.join(_PROJETO, "data", "logs_processados.json")

    if not os.path.exists(caminho_logs):
        logger.error(f"Arquivo de logs nao encontrado: {caminho_logs}")
        return

    processados = carregar_logs_processados(caminho_tracking)
    processados_nesta_exec = set()

    with open(caminho_logs, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f if line.strip()]

    logger.info(f"Total de logs: {len(logs)}")
    logger.info(f"Ja processados: {len(processados)}")

    novos = 0
    ignorados = 0
    erros = 0
    excluidos = 0

    for i, log in enumerate(logs):
        log_id = f"{log.get('timestamp', '')}_{log.get('interacao_id', i)}"

        if log_id in processados:
            ignorados += 1
            continue

        # ─── FILTRO: excluir logs de erro/bug ────────────────────────────────
        if _is_error_log(log):
            logger.warning(f"[EXCLUIDO] Log {i} parece ser de erro/bug: {log.get('pergunta', '')[:40]}")
            processados_nesta_exec.add(log_id)  # marca como processado p/ nao tentar de novo
            excluidos += 1
            continue

        pergunta = log.get("pergunta", "")
        assunto = extrair_assunto(pergunta)
        disciplina = classificar_pergunta(pergunta)

        resposta_original = log_para_resposta_original(log)
        correcao_expert = gerar_correcao(pergunta, assunto, log)

        try:
            resultado = prof.corrigir(disciplina, resposta_original, correcao_expert)
            processados_nesta_exec.add(log_id)
            novos += 1
            logger.info(
                f"[{novos}] {pergunta[:40]:42s} -> {disciplina:20s} "
                f"expert#{resultado['total_exemplos_expert']}"
            )
        except Exception as e:
            logger.error(f"Erro ao processar log {i}: {e}")
            erros += 1

    processados.update(processados_nesta_exec)
    salvar_logs_processados(caminho_tracking, processados)

    llm = prof.boletim_llm()
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Novos: {novos} | Ignorados: {ignorados} | Excluidos(erro/bug): {excluidos} | Erros: {erros}")
    logger.info(f"Total exemplos expert: {llm['total_exemplos_expert']}")
    logger.info(f"Status dataset: {llm['status']}")
    logger.info(f"Progresso: {llm['progresso_percentual']}%")
    if llm['total_exemplos_expert'] >= 50:
        logger.info("DATASET PRONTO para fine-tuning!")
    else:
        logger.info(f"Faltam {50 - llm['total_exemplos_expert']} exemplos.")
    logger.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
