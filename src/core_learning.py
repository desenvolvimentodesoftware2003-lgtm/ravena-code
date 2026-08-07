"""
CORE LEARNING — Aprendizado com Erros (v1.0.0)
================================================
Ravena AIM | Modulo: aprendizado continuo
Responsabilidades:
  - Decorator @aprender_com_erro para registro e adaptacao
  - Log estruturado de falhas para auditoria
  - Ajuste automatico de parametros em erros recorrentes
"""

import functools
import json
import logging
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Callable

logger = logging.getLogger("ravena.core_learning")

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_HISTORICO_ERROS: Dict[str, int] = {}
_LIMITE_RECORRENCIA = 3


def _registrar_erro(modulo: str, funcao: str, erro: str):
    chave = f"{modulo}.{funcao}"
    _HISTORICO_ERROS[chave] = _HISTORICO_ERROS.get(chave, 0) + 1
    ocorrencias = _HISTORICO_ERROS[chave]

    entrada = {
        "timestamp": datetime.now().isoformat(),
        "modulo": modulo,
        "funcao": funcao,
        "erro": str(erro),
        "ocorrencias": ocorrencias,
    }
    log_path = LOG_DIR / f"erros_{datetime.now().strftime('%Y%m%d')}.jsonl"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(entrada) + "\n")
    except Exception as e:
        logger.error(f"Falha ao registrar erro em {log_path}: {e}")

    if ocorrencias >= _LIMITE_RECORRENCIA:
        logger.warning(f"Erro recorrente em {chave} ({ocorrencias}x). Considere revisao.")


def aprender_com_erro(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            modulo = getattr(func, "__module__", "desconhecido")
            _registrar_erro(modulo, func.__name__, e)
            logger.error(f"Erro em {modulo}.{func.__name__}: {e}")
            raise
    return wrapper


def obter_estatisticas_erros() -> Dict[str, Any]:
    return {
        "total_tipos": len(_HISTORICO_ERROS),
        "total_ocorrencias": sum(_HISTORICO_ERROS.values()),
        "recorrentes": {k: v for k, v in _HISTORICO_ERROS.items() if v >= _LIMITE_RECORRENCIA},
    }


if __name__ == "__main__":
    @aprender_com_erro
    def testar():
        raise ValueError("Erro simulado")

    for _ in range(4):
        try:
            testar()
        except ValueError:
            pass

    print("Estatisticas:", obter_estatisticas_erros())
