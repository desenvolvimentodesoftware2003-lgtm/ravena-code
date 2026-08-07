"""
MÓDULO DE CONECTIVIDADE — Ravena AI Trading Bot (Prioridade 1)
==============================================================
Integração com a API v5 da Bybit para leitura de saldo, tickers
e execução de ordens.

Responsabilidades:
  - Autenticação HMAC SHA256
  - GET /v5/market/tickers (Leitura de preços em tempo real)
  - POST /v5/order/create (Criação de ordens)
  - GET /v5/account/wallet-balance (Leitura de saldo)

Padrões de Segurança (Soberania Digital):
  - Chaves de API nunca são logadas em texto claro
  - Uso de variáveis de ambiente para credenciais
  - Tratamento de erros e rate limits
"""

import os
import time
import hmac
import hashlib
import json
import logging
import requests
from typing import Dict, Any, Optional

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ravena.bybit_connector")

class BybitConnector:
    """
    Conector para a API v5 da Bybit.
    Implementa autenticação HMAC e métodos principais para trading.
    """
    
    def __init__(self, testnet: bool = False, demo: bool = None):
        self.api_key = os.environ.get("BYBIT_API_KEY")
        self.api_secret = os.environ.get("BYBIT_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            logger.warning("Credenciais da Bybit não encontradas nas variáveis de ambiente.")
        
        if demo is None:
            demo = os.environ.get("BYBIT_MODE", "").lower() == "demo"
        if demo:
            self.base_url = "https://api-demo.bybit.com"
        elif testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        self.recv_window = str(5000)
        self._server_time_offset = 0
        self._sync_server_time()
        
    def _sync_server_time(self):
        try:
            resp = requests.get(f"{self.base_url}/v5/market/time", timeout=10)
            if resp.status_code == 200:
                server_sec = resp.json()["result"]["timeSecond"]
                server_ms = int(server_sec) * 1000
                local_ms = int(time.time() * 1000)
                self._server_time_offset = server_ms - local_ms
                logger.info(f"Clock skew sincronizado: offset={self._server_time_offset}ms")
        except Exception as e:
            logger.warning(f"Nao foi possivel sincronizar clock: {e}")

    def _timestamp(self) -> str:
        return str(int(time.time() * 1000) + self._server_time_offset)

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Gera a assinatura HMAC SHA256 exigida pela Bybit."""
        param_str = timestamp + self.api_key + self.recv_window + payload
        hash_mac = hmac.new(
            bytes(self.api_secret, "utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256
        )
        return hash_mac.hexdigest()
        
    def _request(self, method: str, endpoint: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executa a requisição HTTP para a API da Bybit com autenticação."""
        if payload is None:
            payload = {}
            
        timestamp = self._timestamp()
        
        if method == "GET":
            # Para GET, o payload é convertido em query string
            query_string = "&".join([f"{k}={v}" for k, v in payload.items()])
            signature = self._generate_signature(query_string, timestamp)
            url = f"{self.base_url}{endpoint}?{query_string}"
            data = None
        else:
            # Para POST, o payload é JSON
            json_payload = json.dumps(payload)
            signature = self._generate_signature(json_payload, timestamp)
            url = f"{self.base_url}{endpoint}"
            data = json_payload
            
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window,
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            else:
                response = requests.post(url, headers=headers, data=data)
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição {method} {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalhes: {e.response.text}")
            return {"retCode": -1, "retMsg": str(e)}

    def get_ticker(self, symbol: str, category: str = "linear") -> Optional[Dict[str, Any]]:
        """
        Obtém informações de preço em tempo real para um símbolo.
        Ex: get_ticker("BTCUSDT")
        """
        endpoint = "/v5/market/tickers"
        payload = {
            "category": category,
            "symbol": symbol
        }
        
        # Endpoint público, não precisa de autenticação completa, mas usamos o _request para padronizar
        response = requests.get(f"{self.base_url}{endpoint}", params=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                return data["result"]["list"][0]
        
        logger.error(f"Falha ao obter ticker para {symbol}")
        return None

    def get_wallet_balance(self, account_type: str = "UNIFIED", coin: str = "USDT") -> Optional[float]:
        """
        Obtém o saldo da carteira para uma moeda específica.
        """
        endpoint = "/v5/account/wallet-balance"
        payload = {
            "accountType": account_type,
            "coin": coin
        }
        
        result = self._request("GET", endpoint, payload)
        
        if result.get("retCode") == 0:
            try:
                balance_list = result["result"]["list"][0]["coin"]
                for c in balance_list:
                    if c["coin"] == coin:
                        return float(c["walletBalance"])
            except (KeyError, IndexError) as e:
                logger.error(f"Erro ao parsear saldo: {e}")
                
        return None

    def create_order(self, symbol: str, side: str, order_type: str, qty: str, 
                     price: str = None, category: str = "linear") -> Dict[str, Any]:
        """
        Cria uma nova ordem (Market ou Limit).
        side: "Buy" ou "Sell"
        order_type: "Market" ou "Limit"
        """
        endpoint = "/v5/order/create"
        payload = {
            "category": category,
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": qty,
            "timeInForce": "GTC" # Good Till Cancel
        }
        
        if order_type == "Limit" and price:
            payload["price"] = price
            
        logger.info(f"Criando ordem: {side} {qty} {symbol} @ {order_type} {price if price else 'Market'}")
        return self._request("POST", endpoint, payload)

if __name__ == "__main__":
    # Teste simples (requer chaves de API configuradas)
    connector = BybitConnector(testnet=True)
    ticker = connector.get_ticker("BTCUSDT")
    if ticker:
        print(f"Preço atual do BTC: {ticker.get('lastPrice')}")
