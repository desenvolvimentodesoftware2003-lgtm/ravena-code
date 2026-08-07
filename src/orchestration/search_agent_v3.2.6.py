"""
RAVENA AIM — Agente de Busca 360 (v1.1.0)
============================================
Refatorado: integracao com Clarividencia v1.0.0, ValidadorVeracidade v1.0.0, CoreLearning v1.0.0.
Responsabilidades:
  - Orquestrar buscas inteligentes via Clarividencia
  - Validar veracidade das informacoes coletadas
  - Fornecer dados enriquecidos para SignalBridge e Trading
"""

import logging
from typing import Dict, List, Optional

from src.clarividencia import ClarividenciaExterna, MarkdownReader
from src.validador_veracidade import ValidadorVeracidade
from src.core_learning import aprender_com_erro

logger = logging.getLogger("ravena.search_agent")

class SearchAgent:
    """
    Agente de Busca da Ravena AI.
    Encapsula a lógica de Clarividência Externa para ser usada por outros módulos.
    """

    def __init__(self, api_key: str = None):
        self.clarividencia = ClarividenciaExterna(api_key=api_key)
        self.validador = ValidadorVeracidade()
        self.reader = MarkdownReader()

    @aprender_com_erro
    def search_and_synthesize(self, topic: str, deep_search: bool = False) -> Dict:
        logger.info(f"[SearchAgent] Iniciando busca para: '{topic}'")

        queries = self.clarividencia.triangulate_query(topic)
        raw_results = self.clarividencia.search_sources(queries)
        filtered_sources = self.clarividencia.filter_judge(raw_results)

        if not filtered_sources:
            return {"topic": topic, "status": "no_results", "message": "Nenhuma fonte densa encontrada."}

        best = filtered_sources[0]
        content = best.get("snippet", "")
        source_url = best.get("link", "")

        if deep_search and source_url:
            deep = self.reader.fetch_and_clean(source_url)
            if deep:
                content = deep[:2000]

        is_valid, confidence, reason = self.validador.validar_informacao(topic, content, "web_search")

        return {
            "topic": topic,
            "status": "success" if is_valid else "low_confidence",
            "content": content,
            "source_url": source_url,
            "source_title": best.get("title", "Fonte Desconhecida"),
            "confidence": round(confidence, 3),
            "is_valid": is_valid,
            "reason": reason,
            "metadata": {
                "total_found": len(raw_results),
                "total_filtered": len(filtered_sources),
                "queries_used": queries,
            },
        }

    def preparar_para_trading(self, simbolo: str, tech_confidence: float = 0.5) -> Dict:
        from src.clarividencia import get_sentiment, get_sinais

        sentimento = get_sentiment(simbolo)
        sinais = get_sinais(simbolo)

        return {
            "symbol": simbolo,
            "tech_confidence": tech_confidence,
            "sentiment_score": sentimento.score if sentimento else 0.0,
            "sentiment_label": sentimento.classificacao if sentimento else "neutro",
            "signal_action": sinais.acao if sinais else "neutral",
            "signal_confidence": sinais.confianca if sinais else 0.0,
            "visual_confirmed": False,
            "audit_cleared": False,
            "timestamp": __import__("time").time(),
        }

if __name__ == "__main__":
    agent = SearchAgent()
    result = agent.search_and_synthesize("Bitcoin ETF impacto mercado", deep_search=False)
    print(f"\nTopic: {result['topic']}")
    print(f"Status: {result['status']}")
    print(f"Confianca: {result.get('confidence', 0)}")
    print(f"Fonte: {result.get('source_url', 'N/A')}")

    print("\n--- Teste preparar_para_trading ---")
    trade_data = agent.preparar_para_trading("BTCUSDT", tech_confidence=0.7)
    for k, v in trade_data.items():
        if k != "timestamp":
            print(f"  {k}: {v}")
