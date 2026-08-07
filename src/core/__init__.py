"""Nucleo central da Ravena AIM: modelos de linguagem, orquestrador Omega e gerenciamento de segredos.

Nota: Omega e OmegaOrchestrator estao em `omega_v3_2_6.py` e `omega_orchestrator_v3.2.6.py`
(importaveis via importlib devido ao ponto no nome do arquivo).
Use o helper `_import_mod` de `tests/test_unit_rag.py` ou acesse diretamente
pelo caminho absoluto.

Disponibiliza:
- RavenaModel: interface para modelos de linguagem (Qwen, Kimi)
- SecretsManager: gerenciamento seguro de credenciais e chaves de API
"""

from .secrets_manager import SecretsManager
from .ravena_model import RavenaModel

__all__ = [
    "SecretsManager",
    "RavenaModel",
]
