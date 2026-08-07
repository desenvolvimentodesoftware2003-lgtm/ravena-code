"""
pipeline_dataset_automatico.py — PIPELINE AUTOMATICO
Processa incrementalmente novos logs do cognitive_treino.jsonl
e registra exemplos expert no Professor.

Exclui automaticamente logs de erro/bug (stack traces, exceptions, crashes).
Idempotente: logs ja processados sao ignorados.

Uso:
  python scripts/pipeline_dataset_automatico.py          # processa novos
  python scripts/pipeline_dataset_automatico.py --force   # reprocessa tudo
  python scripts/pipeline_dataset_automatico.py --status  # status apenas
"""

import os
import sys
import json
import logging
from datetime import datetime

_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJETO)

from src.core.professor import Professor
from scripts.extrair_exemplos_dataset import (
    _is_error_log,
    classificar_pergunta,
    extrair_assunto,
    gerar_correcao,
    log_para_resposta_original,
    carregar_logs_processados,
    salvar_logs_processados,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline_dataset")


def verificar_status() -> dict:
    prof = Professor()
    llm = prof.boletim_llm()
    diag = prof.diagnosticar()

    caminho_tracking = os.path.join(_PROJETO, "data", "logs_processados.json")
    processados = carregar_logs_processados(caminho_tracking)

    caminho_logs = os.path.join(_PROJETO, "data", "cognitive_treino.jsonl")
    total_logs = 0
    if os.path.exists(caminho_logs):
        with open(caminho_logs, "r", encoding="utf-8") as f:
            total_logs = sum(1 for line in f if line.strip())

    return {
        "total_exemplos_expert": llm["total_exemplos_expert"],
        "status": llm["status"],
        "progresso": llm["progresso_percentual"],
        "logs_processados": len(processados),
        "logs_disponiveis": total_logs,
        "logs_pendentes": total_logs - len(processados),
        "minimo_necessario": 50,
        "materias_avaliadas": diag["materias_cadastradas"],
        "competencias_mapeadas": diag["total_competencias_mapeadas"],
        "timestamp": datetime.now().isoformat()
    }


def executar_pipeline(force: bool = False) -> dict:
    prof = Professor()
    caminho_logs = os.path.join(_PROJETO, "data", "cognitive_treino.jsonl")
    caminho_tracking = os.path.join(_PROJETO, "data", "logs_processados.json")

    if not os.path.exists(caminho_logs):
        logger.error(f"Logs nao encontrados: {caminho_logs}")
        return {"erro": "Arquivo de logs nao encontrado"}

    processados = carregar_logs_processados(caminho_tracking)
    processados_nesta_exec = set()

    with open(caminho_logs, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f if line.strip()]

    if force:
        processados = set()
        logger.info("Modo FORCE: reprocessando todos os logs.")

    if not force:
        llm = prof.boletim_llm()
        if llm["total_exemplos_expert"] >= 50:
            logger.info("Dataset ja pronto (>=50 exemplos). Nada a processar.")
            return {"status": "pronto", "exemplos": llm["total_exemplos_expert"], "novos_processados": 0}

    novos = 0
    erros = 0
    excluidos = 0

    for i, log in enumerate(logs):
        log_id = f"{log.get('timestamp', '')}_{log.get('interacao_id', i)}"

        if log_id in processados:
            continue

        # ─── FILTRO: excluir logs de erro/bug ────────────────────────────────
        if _is_error_log(log):
            logger.warning(f"[EXCLUIDO] Log {i} parece ser de erro/bug: {log.get('pergunta', '')[:40]}")
            processados_nesta_exec.add(log_id)
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
            logger.error(f"Erro no log {i}: {e}")
            erros += 1

    processados.update(processados_nesta_exec)
    salvar_logs_processados(caminho_tracking, processados)

    llm = prof.boletim_llm()
    logger.info(f"\nPipeline concluido:")
    logger.info(f"  Novos: {novos} | Excluidos(erro/bug): {excluidos} | Erros: {erros}")
    logger.info(f"  Total acumulado: {llm['total_exemplos_expert']}")
    logger.info(f"  Status: {llm['status']}")
    logger.info(f"  Progresso: {llm['progresso_percentual']}%")

    if llm["total_exemplos_expert"] >= 50:
        logger.info("  >>> DATASET PRONTO para fine-tuning! <<<")

    return {
        "status": "em_andamento" if llm["total_exemplos_expert"] < 50 else "pronto",
        "exemplos": llm["total_exemplos_expert"],
        "novos_processados": novos,
        "excluidos": excluidos,
        "erros": erros
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Pipeline automatico de extracao de exemplos expert para dataset Ravena LLM"
    )
    parser.add_argument("--status", action="store_true", help="Apenas mostrar status")
    parser.add_argument("--force", action="store_true", help="Reprocessar todos os logs")
    args = parser.parse_args()

    if args.status:
        status = verificar_status()
        print(f"\nStatus do Dataset Ravena LLM:")
        print(f"  Exemplos expert: {status['total_exemplos_expert']}/{status['minimo_necessario']}")
        print(f"  Status: {status['status']}")
        print(f"  Progresso: {status['progresso']}%")
        print(f"  Logs disponiveis: {status['logs_disponiveis']}")
        print(f"  Logs processados: {status['logs_processados']}")
        print(f"  Logs pendentes: {status['logs_pendentes']}")
        print(f"  Materias cadastradas: {status['materias_avaliadas']}")
        print(f"  Comp. mapeadas: {status['competencias_mapeadas']}")
        print(f"  Timestamp: {status['timestamp']}")
        return

    logger.info("Iniciando pipeline automatico de extracao de dataset...")
    resultado = executar_pipeline(force=args.force)

    if resultado.get("erro"):
        logger.error(f"Falha no pipeline: {resultado['erro']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
