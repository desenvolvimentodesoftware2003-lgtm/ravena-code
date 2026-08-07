"""
MÓDULO DE MONITORAMENTO E LOGS — Ravena AI Trading Bot (Prioridade 4)
=====================================================================
Integração com Telegram para envio de notificações em tempo real
sobre execução de ordens, atingimento de Stop Loss/Take Profit
e status geral do sistema.

Responsabilidades:
  - Envio de mensagens formatadas para o Telegram
  - Registro de logs locais em arquivo
  - Monitoramento de saúde do bot (Heartbeat)
  - Alertas críticos (ex: saldo insuficiente, erro de API)

Padrões de Segurança:
  - Token do bot e Chat ID via variáveis de ambiente
  - Tratamento de falhas de rede para não travar o bot principal
"""

import os
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

# Configuração de Logging Local
log_dir = os.path.join(os.path.expanduser("~"), "logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("ravena.monitor")

class TelegramNotifier:
    """
    Notificador via Telegram Bot API.
    """
    
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Credenciais do Telegram não encontradas. Notificações desativadas.")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
            
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envia uma mensagem de texto para o chat configurado.
        """
        if not self.enabled:
            logger.info(f"[Telegram Desativado] Mensagem: {text}")
            return False
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Falha ao enviar mensagem para o Telegram: {e}")
            return False
            
    def notify_trade_execution(self, symbol: str, action: str, qty: str, price: str, order_type: str):
        """
        Notifica a execução de uma ordem.
        """
        emoji = "🟢" if action.upper() == "BUY" else "🔴"
        
        msg = (
            f"<b>{emoji} ORDEM EXECUTADA</b>\n\n"
            f"<b>Ativo:</b> {symbol}\n"
            f"<b>Ação:</b> {action.upper()}\n"
            f"<b>Tipo:</b> {order_type}\n"
            f"<b>Quantidade:</b> {qty}\n"
            f"<b>Preço:</b> {price}\n\n"
            f"<i>Ravena AI Trading Bot</i>"
        )
        
        logger.info(f"Notificando execução de trade: {action} {qty} {symbol} @ {price}")
        self.send_message(msg)
        
    def notify_alert(self, level: str, message: str):
        """
        Notifica um alerta do sistema (Info, Warning, Critical).
        """
        emojis = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "CRITICAL": "🚨"
        }
        
        emoji = emojis.get(level.upper(), "🔔")
        
        msg = (
            f"<b>{emoji} ALERTA DO SISTEMA ({level.upper()})</b>\n\n"
            f"{message}\n\n"
            f"<i>Ravena AI Trading Bot</i>"
        )
        
        logger.log(getattr(logging, level.upper(), logging.INFO), f"Alerta: {message}")
        self.send_message(msg)
        
    def notify_heartbeat(self, balance: float, active_positions: int):
        """
        Envia um status periódico de saúde do bot.
        """
        msg = (
            f"<b>💓 HEARTBEAT - STATUS OK</b>\n\n"
            f"<b>Saldo Atual:</b> {balance:.2f} USDT\n"
            f"<b>Posições Ativas:</b> {active_positions}\n"
            f"<b>Uptime:</b> OK\n\n"
            f"<i>Ravena AI Trading Bot</i>"
        )
        
        logger.info("Enviando heartbeat")
        self.send_message(msg)

if __name__ == "__main__":
    # Teste simples
    notifier = TelegramNotifier()
    notifier.notify_alert("INFO", "Módulo de monitoramento inicializado com sucesso.")
