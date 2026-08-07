"""Orquestracao de agentes: coordenacao de modulos, chat, busca especializada e dashboard.

Nota: classes de `*_v3.2.6.py` nao sao importaveis diretamente via `__init__.py`
devido ao ponto no nome do arquivo. Use importlib ou acesse pelo caminho absoluto.

Disponibiliza:
- TelegramBot: bot do Telegram para interface com usuario
"""

from .telegram_bot import TelegramBot, RateLimiter

__all__ = [
    "TelegramBot",
    "RateLimiter",
]
