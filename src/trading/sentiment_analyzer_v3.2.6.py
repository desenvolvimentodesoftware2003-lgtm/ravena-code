"""
MÓDULO DE ANÁLISE DE SENTIMENTO RAG — Ravena AI Trading Bot (v3.2.6)
==============================================================================
Integracao com Clarividencia (CoinGecko) + fallback CryptoPanic.
Responsabilidades:
  - Coleta de sentimento via Clarividencia (CoinGecko)
  - Fallback para CryptoPanic se api_key disponivel
  - Filtro de seguranca RAG para o TradeBrain
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("ravena.sentiment")

try:
    from src.clarividencia import get_sentiment as _cg_sentiment
    from src.clarividencia import get_sinais as _cg_sinais
    CLARIVIDENCIA_AVAILABLE = True
except ImportError:
    CLARIVIDENCIA_AVAILABLE = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class SentimentResult:
    """Resultado da analise de sentimento."""
    symbol: str
    score: float
    total_votes: int
    top_news: List[str]
    timestamp: float


class SentimentAnalyzer:
    """
    Analisador de Sentimento RAG.
    Fonte primaria: Clarividencia (CoinGecko).
    Fallback: CryptoPanic (se token configurado).
    """

    def __init__(self):
        self.api_token = os.environ.get("CRYPTOPANIC_API_TOKEN")
        self.base_url = "https://cryptopanic.com/api/v2/posts/"
        self.cache = {}
        self.cache_duration = 300

        if not self.api_token:
            logger.info("CRYPTOPANIC_API_TOKEN ausente. Usando Clarividencia (CoinGecko).")
        if not CLARIVIDENCIA_AVAILABLE:
            logger.warning("Clarividencia nao disponivel. Modo NEUTRO.")

    def _fetch_news_cryptopanic(self, symbol: str) -> List[Dict[str, Any]]:
        if not self.api_token or not HAS_REQUESTS:
            return []
        params = {
            "auth_token": self.api_token,
            "currencies": symbol.replace("USDT", ""),
            "kind": "news",
            "public": "true"
        }
        try:
            import requests
            r = requests.get(self.base_url, params=params, timeout=10)
            r.raise_for_status()
            return r.json().get("results", [])
        except Exception as e:
            logger.error(f"Erro CryptoPanic {symbol}: {e}")
            return []

    def analyze_sentiment(self, symbol: str) -> SentimentResult:
        now = time.time()
        if symbol in self.cache:
            cached_time, cached_result = self.cache[symbol]
            if now - cached_time < self.cache_duration:
                return cached_result

        # 1. Tenta Clarividencia (CoinGecko)
        if CLARIVIDENCIA_AVAILABLE:
            sent = _cg_sentiment(symbol)
            if sent and sent.score != 0.0:
                sinal = _cg_sinais(symbol)
                score = sent.score
                label = sent.classificacao
                signal_str = f"sinal: {sinal.acao if sinal else 'neutral'}"
                result = SentimentResult(
                    symbol=symbol, score=round(score, 2),
                    total_votes=abs(int(score * 100)),
                    top_news=[f"CoinGecko: {label} - {signal_str}"],
                    timestamp=now,
                )
                self.cache[symbol] = (now, result)
                logger.info(f"Sentimento {symbol} (Clarividencia): {result.score}")
                return result

        # 2. Fallback: CryptoPanic
        news_list = self._fetch_news_cryptopanic(symbol)
        if news_list:
            total_pos = sum(v.get("votes", {}).get("positive", 0) for v in news_list[:10])
            total_neg = sum(v.get("votes", {}).get("negative", 0) for v in news_list[:10])
            total_votes = total_pos + total_neg
            score = (total_pos - total_neg) / (total_votes or 1)
            top = [n.get("title", "") for n in news_list[:3]]
            result = SentimentResult(symbol, round(score, 2), total_votes, top, now)
            self.cache[symbol] = (now, result)
            return result

        # 3. Neutro
        result = SentimentResult(symbol, 0.0, 0, [], now)
        self.cache[symbol] = (now, result)
        return result

    def is_safe_to_trade(self, symbol: str, action: str) -> bool:
        sentiment = self.analyze_sentiment(symbol)
        if action.upper() == "BUY" and sentiment.score < -0.3:
            logger.warning(f"BLOQUEIO RAG: Bearish ({sentiment.score}) para COMPRA.")
            return False
        if action.upper() == "SELL" and sentiment.score > 0.3:
            logger.warning(f"BLOQUEIO RAG: Bullish ({sentiment.score}) para VENDA.")
            return False
        return True

if __name__ == "__main__":
    # Teste rápido
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze_sentiment("BTCUSDT")
    print(f"Resultado: {res}")
