"""API REST: endpoints seguros que consomem credenciais exclusivamente via SecretsManager.

Disponibiliza:
- app: instancia FastAPI configurada para producao
- create_app: factory para criacao da aplicacao com dependencias injetadas
"""

from .server import app, create_app

__all__ = ["app", "create_app"]
