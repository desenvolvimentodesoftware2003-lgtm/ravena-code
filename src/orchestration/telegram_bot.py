"""
RAVENA AIM — Telegram Bot Module (httpx polling)
==================================================
v1.0.0 | Protocolo R6 | Zero Trust
Recepcao e resposta de mensagens do Telegram via polling direto com httpx.
Uso exclusivo de SecretsManager — sem tokens hardcoded.
Seguranca: whitelist de chat_ids, rate limiting, sem acesso a arquivos.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx

from src.core.secrets_manager import secrets

logger = logging.getLogger("ravena.telegram_bot")

API_BASE = "https://api.telegram.org"
RATE_LIMIT_SECONDS = 2
AUTHORIZED_CHAT_IDS: List[str] = []


def _carregar_chat_ids() -> List[str]:
    ids_str = secrets.get("TELEGRAM_CHAT_ID", required=False)
    if not ids_str:
        return []
    return [cid.strip() for cid in ids_str.split(",") if cid.strip()]


def _is_authorized(chat_id: int) -> bool:
    if not AUTHORIZED_CHAT_IDS:
        return True
    return str(chat_id) in AUTHORIZED_CHAT_IDS


class RateLimiter:
    def __init__(self, max_per_second: float = 1.0):
        self._last_time: Dict[int, float] = {}
        self._cooldown = 1.0 / max_per_second

    def check(self, user_id: int) -> bool:
        now = time.time()
        last = self._last_time.get(user_id, 0.0)
        if now - last < self._cooldown:
            return False
        self._last_time[user_id] = now
        return True


_rate_limiter = RateLimiter()


def _get_omega_diagnostic() -> Dict[str, Any]:
    try:
        from src.core.omega_v3_2_6 import obter_omega
        return obter_omega().obter_diagnostico()
    except Exception as e:
        logger.error(f"Omega diagnostic error: {e}")
        return {"versao": "N/A", "status": "INDISPONIVEL", "uptime_segundos": 0}


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.client = httpx.Client(timeout=httpx.Timeout(15.0, connect=10.0))
        self.base = f"{API_BASE}/bot{token}"
        self._offset = 0
        self._running = True

    def _api(self, method: str, data: dict = None) -> Optional[dict]:
        url = f"{self.base}/{method}"
        try:
            r = self.client.post(url, json=data or {}, timeout=15.0)
            if r.status_code == 401:
                logger.error("Token rejeitado pela API do Telegram.")
                self._running = False
                return None
            r.raise_for_status()
            result = r.json()
            if not result.get("ok"):
                logger.warning(f"Telegram API error: {result}")
                return None
            return result["result"]
        except httpx.HTTPStatusError as e:
            logger.error(f"Telegram API HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Telegram API error: {e}")
            return None

    def get_me(self) -> Optional[dict]:
        return self._api("getMe")

    def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> bool:
        result = self._api("sendMessage", {
            "chat_id": chat_id,
            "text": text[:4096],
            "parse_mode": parse_mode,
        })
        return result is not None

    def get_updates(self) -> List[dict]:
        result = self._api("getUpdates", {
            "offset": self._offset,
            "timeout": 10,
            "allowed_updates": ["message"],
        })
        return result or []

    def handle_update(self, update: dict):
        msg = update.get("message") or {}
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            return
        if not _is_authorized(chat_id):
            self.send_message(chat_id, "Acesso nao autorizado.")
            return
        user_id = msg.get("from", {}).get("id", 0)
        if not _rate_limiter.check(user_id):
            return
        text = (msg.get("text") or "").strip()
        if not text:
            return
        logger.info(f"Telegram msg from {chat_id}: {text[:80]}")
        if text.startswith("/"):
            self._handle_command(chat_id, text)
        else:
            self._handle_text(chat_id, text)

    def _handle_command(self, chat_id: int, text: str):
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/start":
            self.send_message(chat_id,
                "Ola! Sou o <b>Ravena AIM</b>.\n"
                "Use /help para ver os comandos.")
        elif cmd == "/help":
            self.send_message(chat_id,
                "Comandos:\n"
                "/start - Inicia\n"
                "/help - Ajuda\n"
                "/status - Status do sistema\n"
                "/chat <msg> - Enviar para Ravena\n\n"
                "Ou digite qualquer mensagem.")
        elif cmd == "/status":
            diag = _get_omega_diagnostic()
            self.send_message(chat_id,
                f"<b>Ravena AIM - Status</b>\n\n"
                f"Versao: {diag.get('versao', 'N/A')}\n"
                f"Status: {diag.get('status', 'N/A')}\n"
                f"Uptime: {diag.get('uptime_segundos', 0):.0f}s\n"
                f"Secrets: {secrets.source}")
        elif cmd == "/chat":
            if not args:
                self.send_message(chat_id, "Use: /chat <mensagem>")
                return
            self.send_message(chat_id, f"[Ravena] Processado: {args[:200]}")
        elif cmd == "/chat_id":
            self.send_message(chat_id, f"Seu Chat ID: <code>{chat_id}</code>")
        else:
            self.send_message(chat_id, f"Comando desconhecido: {cmd}")

    def _handle_text(self, chat_id: int, text: str):
        self.send_message(chat_id, f"[Ravena] Recebi: {text[:200]}")

    def poll_once(self) -> int:
        updates = self.get_updates()
        count = 0
        for upd in updates:
            self._offset = upd.get("update_id", 0) + 1
            self.handle_update(upd)
            count += 1
        return count

    def run(self):
        logger.info("Bot Telegram Ravena iniciado (polling httpx). Ctrl+C para parar.")
        me = self.get_me()
        if me:
            logger.info(f"Bot @{me.get('username')} ({me.get('first_name')}) conectado.")
        else:
            logger.error("Nao foi possivel conectar ao bot Telegram.")
            return
        try:
            while self._running:
                try:
                    self.poll_once()
                except Exception as e:
                    logger.error(f"Erro no polling: {e}")
                time.sleep(0.5)
        except KeyboardInterrupt:
            logger.info("Bot Telegram encerrado.")
        finally:
            self.client.close()

    def stop(self):
        self._running = False


def create_bot() -> Optional[TelegramBot]:
    token = secrets.get("TELEGRAM_BOT_TOKEN", required=False)
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN nao configurado no SecretsManager.")
        return None
    global AUTHORIZED_CHAT_IDS
    AUTHORIZED_CHAT_IDS = _carregar_chat_ids()
    if AUTHORIZED_CHAT_IDS:
        logger.info(f"Modo restrito: {len(AUTHORIZED_CHAT_IDS)} chat(s) autorizado(s).")
    else:
        logger.warning("Sem whitelist — qualquer chat podera interagir.")
    return TelegramBot(token)


def run_polling() -> None:
    bot = create_bot()
    if bot:
        bot.run()


if __name__ == "__main__":
    run_polling()
