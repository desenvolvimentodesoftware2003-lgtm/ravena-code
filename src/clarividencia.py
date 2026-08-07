"""
CLARIVIDENCIA — Ponte Inteligente de Dados (v1.1.0)
====================================================
Ravena AIM | Modulo: olhos e ouvidos
Fonte primaria: CoinGecko API (gratuita, sem chave)
Responsabilidades:
  - Consumir CoinGecko API para dados de mercado
  - Triangulacao de queries para busca inteligente
  - Analise de sentimento e sinais de mercado via price action
  - Fornecer dados enriquecidos para o SearchAgent 360 e Trading
"""

import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

import requests

logger = logging.getLogger("ravena.clarividencia")

API_BASE = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT = 10
CACHE_DURATION = 300

_MOCK_MODE = os.getenv("CLARIVIDENCIA_MOCK_MODE", "").lower() in ("true", "1", "yes")
_MOCK_DATA = {
    "BTC":     {"score": 0.65, "label": "bullish",  "signal": "buy",    "confidence": 0.72},
    "ETH":     {"score": 0.40, "label": "bullish",  "signal": "buy",    "confidence": 0.55},
    "SOL":     {"score": 0.30, "label": "neutral",  "signal": "hold",   "confidence": 0.50},
    "ADA":     {"score":-0.20, "label": "bearish",  "signal": "sell",   "confidence": 0.45},
    "DOGE":    {"score": 0.10, "label": "neutral",  "signal": "neutral","confidence": 0.30},
    "DEFAULT": {"score": 0.00, "label": "neutral",  "signal": "neutral","confidence": 0.00},
}

_COINGECKO_IDS = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "ADA": "cardano", "DOGE": "dogecoin", "BNB": "binancecoin",
    "XRP": "ripple", "DOT": "polkadot", "LINK": "chainlink",
    "AVAX": "avalanche-2", "MATIC": "matic-network", "UNI": "uniswap",
    "TRX": "tron", "SHIB": "shiba-inu", "LTC": "litecoin",
    "ATOM": "cosmos", "NEAR": "near", "OP": "optimism",
    "ARB": "arbitrum", "PEPE": "pepe", "INJ": "injective-protocol",
    "TIA": "celestia", "SEI": "sei-network", "SUI": "sui",
    "APT": "aptos", "FET": "fetch-ai", "RENDER": "render-token",
}

random.seed(42)


@dataclass
class SentimentoMercado:
    simbolo: str
    score: float
    classificacao: str
    fontes: int
    timestamp: float


@dataclass
class SinalMercado:
    simbolo: str
    acao: str
    confianca: float
    timestamp: float


class CacheSimples:
    def __init__(self, duracao: int = CACHE_DURATION):
        self._dados: Dict[str, Tuple[float, Any]] = {}
        self._duracao = duracao

    def get(self, chave: str) -> Optional[Any]:
        if chave in self._dados:
            ts, valor = self._dados[chave]
            if time.time() - ts < self._duracao:
                return valor
        return None

    def set(self, chave: str, valor: Any):
        self._dados[chave] = (time.time(), valor)


_cache = CacheSimples()

_BATCH_CACHE_DURATION = 240


def _extrair_ativo(simbolo: str) -> str:
    return simbolo.replace("USDT", "").replace("USDC", "").replace("/", "").upper()


def _coingecko_id(simbolo: str) -> Optional[str]:
    ativo = _extrair_ativo(simbolo)
    return _COINGECKO_IDS.get(ativo)


def _buscar_dados_mercado(simbolo: str) -> Optional[dict]:
    cache_key = f"mercado:{simbolo}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    coin_id = _coingecko_id(simbolo)
    if not coin_id:
        return None

    ids_usados = set()
    simbolo_id_map = {}
    for s, cid in _COINGECKO_IDS.items():
        if cid not in ids_usados:
            ids_usados.add(cid)
            simbolo_id_map.setdefault(cid, []).append(s)

    data = _get("/coins/markets", {
        "vs_currency": "usd",
        "ids": ",".join(sorted(ids_usados)),
        "order": "market_cap_desc",
        "per_page": 250,
        "sparkline": "false",
        "price_change_percentage": "7d",
    })
    if data and isinstance(data, list):
        normalizado = {}
        for item in data:
            raw = {
                "id": item.get("id"),
                "symbol": item.get("symbol"),
                "current_price": item.get("current_price"),
                "market_cap": item.get("market_cap"),
                "total_volume": item.get("total_volume"),
                "price_change_percentage_24h": item.get("price_change_percentage_24h"),
                "price_change_percentage_7d": item.get("price_change_percentage_7d_in_currency"),
                "market_cap_change_percentage_24h": item.get("market_cap_change_percentage_24h", 0),
            }
            normalizado[item.get("id")] = raw

        for cid, simbs in simbolo_id_map.items():
            coin_data = normalizado.get(cid, {})
            for s in simbs:
                # Cache via symbolic curto (ex: "BTC")
                _cache.set(f"mercado:{s}", coin_data)
                # Cache via simbolo trading (ex: "BTCUSDT", "BTCUSDC")
                _cache.set(f"mercado:{s}USDT", coin_data)
                _cache.set(f"mercado:{s}USDC", coin_data)

        cached_result = _cache.get(cache_key)
        if cached_result:
            return cached_result

    return None


def _sentimento_por_preco(pct_24h: float) -> Tuple[float, str]:
    if pct_24h > 5.0:
        return 0.9, "bullish_forte"
    if pct_24h > 2.0:
        return 0.6, "bullish"
    if pct_24h > 0.5:
        return 0.3, "levemente_bullish"
    if pct_24h > -0.5:
        return 0.0, "neutro"
    if pct_24h > -2.0:
        return -0.3, "levemente_bearish"
    if pct_24h > -5.0:
        return -0.6, "bearish"
    return -0.9, "bearish_forte"


def _sinal_por_preco(pct_24h: float, pct_7d: float, volume_mc_ratio: float) -> Tuple[str, float]:
    momentum = (pct_24h * 0.5) + (pct_7d * 0.5)
    if momentum > 3.0 and volume_mc_ratio > 0.05:
        return "buy", min(abs(momentum) / 10.0, 0.95)
    if momentum > 1.0 and volume_mc_ratio > 0.03:
        return "buy", 0.55
    if momentum < -3.0 and volume_mc_ratio > 0.05:
        return "sell", min(abs(momentum) / 10.0, 0.95)
    if momentum < -1.0 and volume_mc_ratio > 0.03:
        return "sell", 0.55
    return "neutral", max(0.0, 0.5 - abs(momentum) / 20.0)


def _get(endpoint: str, params: dict = None) -> Optional[dict]:
    if _MOCK_MODE:
        ativo = (params or {}).get("asset") or (params or {}).get("q") or "DEFAULT"
        ativo = ativo.upper().replace("USDT", "").replace("/", "")
        m = _MOCK_DATA.get(ativo, _MOCK_DATA["DEFAULT"])
        if endpoint == "/coins/market_data":
            return {"price_change_24h": m["score"] * 3, "market_cap_change_24h": m["score"] * 2}
        if endpoint == "/coins/sinal":
            return {"action": m["signal"], "confidence": m["confidence"]}
        if endpoint == "/global":
            return {"value": random.randint(25, 75), "classification": random.choice(["Fear", "Greed", "Neutral"]), "timestamp": time.time()}
        if endpoint == "/news":
            mock_articles = []
            for i in range(params.get("limit", 5) if params else 5):
                mock_articles.append({
                    "title": f"{ativo} {random.choice(['surges', 'drops', 'holds steady', 'shows strength'])} amid market {random.choice(['rallly', 'correction', 'uncertainty', 'optimism'])}",
                    "description": f"Analysts weigh in on {ativo} price action as trading volume {random.choice(['increases', 'decreases', 'remains flat'])}.",
                    "url": f"https://example.com/news/{ativo.lower()}-{i}",
                    "source": random.choice(["CoinTelegraph", "CoinDesk", "Decrypt", "The Block", "CryptoSlate"]),
                    "score": round(random.uniform(0.3, 0.95), 2),
                })
            return {"articles": mock_articles, "results": mock_articles}
        if endpoint == "/search":
            mock_results = []
            q = (params or {}).get("q", ativo)
            for i in range(params.get("limit", 5) if params else 5):
                mock_results.append({
                    "title": f"{q}: {random.choice(['Breaking', 'Analysis', 'Update', 'Report', 'Insight'])} #{i+1}",
                    "description": f"Latest developments and market analysis for {q}.",
                    "url": f"https://example.com/search/{q.lower().replace(' ', '-')}-{i}",
                    "source": random.choice(["CoinTelegraph", "CoinDesk", "Decrypt", "The Block"]),
                    "score": round(random.uniform(0.4, 0.98), 2),
                })
            return {"articles": mock_results, "results": mock_results}
        return None

    url = f"{API_BASE}{endpoint}"
    try:
        r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            logger.warning(f"CoinGecko rate limit (429) em {endpoint}. Aguardando 2s...")
            time.sleep(2)
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r.json()
        logger.warning(f"Clarividencia HTTP {r.status_code} em {endpoint}")
        return None
    except Exception as e:
        logger.error(f"Clarividencia erro em {endpoint}: {e}")
        return None


def triangulate_query(topic: str) -> List[str]:
    cache_key = f"triangulate:{topic}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    queries = [
        topic,
        f"{topic} crypto",
        f"{topic} news today",
        f"{topic} price analysis",
        f"{topic} market",
    ]
    _cache.set(cache_key, queries)
    return queries


def search_sources(queries: List[str]) -> List[Dict[str, Any]]:
    results = []
    seen_urls = set()
    for q in queries[:3]:
        data = _get("/search", {"q": q, "limit": 5})
        if data:
            articles = data.get("articles", data.get("results", []))
            for item in articles:
                url = item.get("url", item.get("link", ""))
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("description", item.get("snippet", "")),
                        "link": url,
                        "source": item.get("source", item.get("source_title", "")),
                        "score": item.get("score", 0.5),
                    })
    return results


def filter_judge(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not results:
        return []
    scored = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
    return scored[:5]


def get_sentiment(simbolo: str) -> Optional[SentimentoMercado]:
    cache_key = f"sentiment:{simbolo}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    ativo = _extrair_ativo(simbolo)

    if _MOCK_MODE:
        m = _MOCK_DATA.get(ativo, _MOCK_DATA["DEFAULT"])
        resultado = SentimentoMercado(
            simbolo=simbolo,
            score=m["score"],
            classificacao=m["label"],
            fontes=random.randint(3, 12),
            timestamp=time.time(),
        )
        _cache.set(cache_key, resultado)
        return resultado

    data = _buscar_dados_mercado(simbolo)
    if data and data.get("current_price") is not None:
        pct_24h = float(data.get("price_change_percentage_24h") or 0.0)
        score, rotulo = _sentimento_por_preco(pct_24h)

        resultado = SentimentoMercado(
            simbolo=simbolo,
            score=score,
            classificacao=rotulo,
            fontes=int(data.get("market_cap_change_percentage_24h") or 0),
            timestamp=time.time(),
        )
        _cache.set(cache_key, resultado)
        logger.info(f"Sentimento {simbolo} (CG): {resultado.score:.2f} ({resultado.classificacao}) via price {pct_24h:+.2f}%")
        return resultado

    return SentimentoMercado(simbolo=simbolo, score=0.0, classificacao="neutro", fontes=0, timestamp=time.time())


def get_fear_greed() -> Optional[Dict[str, Any]]:
    cached = _cache.get("fear_greed")
    if cached:
        return cached

    if _MOCK_MODE:
        valor = random.randint(25, 75)
        classificacao = "Greed" if valor > 53 else "Fear" if valor < 47 else "Neutral"
        data = {"value": valor, "classification": classificacao, "timestamp": time.time()}
        _cache.set("fear_greed", data)
        return data

    data = _get("/global")
    if data:
        gd = data.get("data", {})
        mcap_pct = gd.get("market_cap_change_percentage_24h_usd", 0) or 0
        btc_dom = gd.get("market_cap_percentage", {}).get("btc", 45) or 45

        fear_greed_value = 50 + (mcap_pct * 1.5)
        if btc_dom > 55:
            fear_greed_value -= 10
        elif btc_dom < 40:
            fear_greed_value += 10
        fear_greed_value = max(5, min(95, int(fear_greed_value)))

        if fear_greed_value > 53:
            classificacao = "Greed"
        elif fear_greed_value < 47:
            classificacao = "Fear"
        else:
            classificacao = "Neutral"

        resultado = {
            "value": fear_greed_value,
            "classification": classificacao,
            "timestamp": time.time(),
        }
        _cache.set("fear_greed", resultado)
        logger.info(f"Fear & Greed (CG): {resultado['value']} - {resultado['classification']}")
        return resultado

    return None


def get_sinais(simbolo: str) -> Optional[SinalMercado]:
    cache_key = f"sinais:{simbolo}"
    cached = _cache.get(cache_key)
    if cached:
        return cached

    ativo = _extrair_ativo(simbolo)

    if _MOCK_MODE:
        m = _MOCK_DATA.get(ativo, _MOCK_DATA["DEFAULT"])
        resultado = SinalMercado(
            simbolo=simbolo,
            acao=m["signal"],
            confianca=m["confidence"],
            timestamp=time.time(),
        )
        _cache.set(cache_key, resultado)
        return resultado

    data = _buscar_dados_mercado(simbolo)
    if data and data.get("current_price") is not None:
        pct_24h = float(data.get("price_change_percentage_24h") or 0.0)
        pct_7d_raw = data.get("price_change_percentage_7d") or 0.0
        if isinstance(pct_7d_raw, dict):
            pct_7d = float(pct_7d_raw.get("usd", 0))
        else:
            pct_7d = float(pct_7d_raw)
        volume = float(data.get("total_volume") or 0)
        mcap = float(data.get("market_cap") or 1)
        volume_mc_ratio = volume / max(mcap, 1)

        acao, confianca = _sinal_por_preco(pct_24h, pct_7d, volume_mc_ratio)
        resultado = SinalMercado(
            simbolo=simbolo,
            acao=acao,
            confianca=round(confianca, 2),
            timestamp=time.time(),
        )
        _cache.set(cache_key, resultado)
        logger.info(f"Sinal {simbolo} (CG): {resultado.acao} conf={resultado.confianca:.2f}")
        return resultado

    return SinalMercado(simbolo=simbolo, acao="neutral", confianca=0.0, timestamp=time.time())


_RSS_FEEDS = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("CryptoSlate", "https://cryptoslate.com/feed/"),
]

_RSS_CACHE_DURATION = 600


def _parse_rss() -> List[Dict[str, Any]]:
    cached = _cache.get("rss_all")
    if cached:
        return cached

    import feedparser

    todas = []
    for nome, url in _RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                todas.append({
                    "title": entry.get("title", ""),
                    "snippet": entry.get("summary", "")[:300],
                    "link": entry.get("link", ""),
                    "source": nome,
                    "published": entry.get("published", ""),
                    "score": 0.5,
                })
        except Exception as e:
            logger.warning(f"RSS {nome} falhou: {e}")

    todas.sort(key=lambda x: x.get("published", ""), reverse=True)
    _cache.set("rss_all", todas)
    logger.info(f"RSS: {len(todas)} noticias carregadas de {len(_RSS_FEEDS)} fontes")
    return todas


def get_ultimas_noticias(limite: int = 10, filtro: str = "") -> List[Dict[str, Any]]:
    if _MOCK_MODE:
        data = _get("/news", {"limit": limite})
        if data:
            return data.get("articles", data.get("results", []))[:limite]
        return []

    noticias = _parse_rss()
    if filtro:
        f = filtro.lower()
        noticias = [n for n in noticias if f in n["title"].lower() or f in n["snippet"].lower()]
    return noticias[:limite]


class MarkdownReader:
    @staticmethod
    def fetch_and_clean(url: str) -> Optional[str]:
        try:
            r = requests.get(url, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                texto = r.text
                import re
                texto = re.sub(r"<[^>]+>", " ", texto)
                texto = re.sub(r"\s+", " ", texto).strip()
                return texto[:5000]
            return None
        except Exception as e:
            logger.error(f"MarkdownReader erro ao buscar {url}: {e}")
            return None


class ClarividenciaExterna:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        logger.info("Clarividencia v1.1.0 (CoinGecko) inicializada.")

    def triangulate_query(self, topic: str) -> List[str]:
        return triangulate_query(topic)

    def search_sources(self, queries: List[str]) -> List[Dict[str, Any]]:
        return search_sources(queries)

    def filter_judge(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return filter_judge(results)


if __name__ == "__main__":
    print(f"Mock Mode: {_MOCK_MODE}")
    print(f"Fonte: CoinGecko API")
    for ativo in ("BTC", "ETH", "SOL", "ADA", "DOGE"):
        sent = get_sentiment(ativo)
        print(f"  {ativo}: score={sent.score:.2f}, {sent.classificacao}")
    sinais = get_sinais("BTC")
    print(f"Sinais BTC: acao={sinais.acao}, confianca={sinais.confianca:.2f}")
    fg = get_fear_greed()
    print(f"Fear & Greed: {fg}")
    noticias = get_ultimas_noticias(3)
    print(f"Noticias: {len(noticias)} encontradas (CoinGecko nao tem noticias)")
