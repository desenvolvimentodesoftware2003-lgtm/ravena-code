"""Utilitarios gerais: metricas de empatia, conectores externos, geracao cultural e readiness check.

Nota: classes de `*_v3.2.6.py` nao sao importaveis diretamente via `__init__.py`
devido ao ponto no nome do arquivo. Use importlib ou acesse pelo caminho absoluto.

Disponibiliza:
- ConectorSocialInstagram: integracao com Instagram Graph API
"""

from .social_connector import ConectorSocialInstagram, ClienteGraphAPI, PublicadorInstagram, MonitorInstagram

__all__ = [
    "ConectorSocialInstagram",
    "ClienteGraphAPI",
    "PublicadorInstagram",
    "MonitorInstagram",
]
