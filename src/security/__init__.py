"""Seguranca Zero Trust: auditoria, juiz universal, protocolos de seguranca e teste de penetracao.

Nota: classes de `*_v3.2.6.py` nao sao importaveis diretamente via `__init__.py`
devido ao ponto no nome do arquivo. Use importlib ou acesse pelo caminho absoluto.

Disponibiliza:
- JuizUniversal: auditor de decisoes e conformidade
- Auditor: analise estatica, sandbox e escopo de seguranca
- HackerAgent / HackerAgentElite / HackerAgentV328: agentes de teste de penetracao
- HeuristicLayer: camada heuristica de deteccao de anomalias
- BypassEngine: motor de bypass para fallback de seguranca
- SegurancaIAIntegrator: integracao de patches de seguranca IA
"""

from .juiz_universal import JuizUniversal
from .auditor import Auditor, AnalisadorEstatico, SandboxExecutor, AnalisadorRede, AnalisadorEscopo
from .hacker_agent import HackerAgent
from .hacker_agent_v328_alpha import HackerAgentV328
from .hacker_agent_v328_final import HackerAgentElite
from .hacker_heuristic_layer import HeuristicLayer
from .hacker_bypass_engine import BypassEngine
from .engine_patch_seguranca_ia import SegurancaIAIntegrator

__all__ = [
    "JuizUniversal",
    "Auditor",
    "AnalisadorEstatico",
    "SandboxExecutor",
    "AnalisadorRede",
    "AnalisadorEscopo",
    "HackerAgent",
    "HackerAgentV328",
    "HackerAgentElite",
    "HeuristicLayer",
    "BypassEngine",
    "SegurancaIAIntegrator",
]
