"""Pipeline de trading: sinal a execucao com auditoria, gestao de risco e self-healing.

Nota: classes em `*_v3.2.6.py` nao sao importaveis diretamente via `__init__.py`
devido ao ponto no nome do arquivo. Use importlib ou acesse pelo caminho absoluto.

Disponibiliza:
- StepScaling: estrategia de entrada em grades (escalonamento por passos)
"""

from .step_scaling import StepScaling, EscalaPasso

__all__ = [
    "StepScaling",
    "EscalaPasso",
]
