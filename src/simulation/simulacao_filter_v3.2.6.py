"""
RAVENA AI V3.2.6 — src/simulation/simulacao_filter.py
=====================================================
Filtro de Elite baseado em 60 Agentes de Simulacao com dados reais.
Conectado a Clarividencia (CoinGecko) e integrado ao SignalBridge.
"""

import random
import time
import logging
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ravena.simulation_filter")

try:
    from src.clarividencia import get_sentiment, get_sinais, get_fear_greed
    _CG_DISPONIVEL = True
except ImportError:
    _CG_DISPONIVEL = False

ESTILOS = ["momentum", "contrarian", "swing", "scalping", "grid",
           "breakout", "reversal", "dca", "hodl", "arbitrage"]


@dataclass
class ResultadoSimulacao:
    agente_id: int
    sucesso: bool
    lucro_estimado: float
    confianca: float
    cenario: str
    estilo: str


class SimulacaoFilter:
    """
    Orquestra 60 agentes de simulacao alimentados por dados reais de mercado.
    Cada agente usa um estilo diferente de trading e dados do CoinGecko.
    """

    def __init__(self, num_agentes: int = 60):
        self.num_agentes = num_agentes
        self.cenarios = ["Bullish", "Bearish", "Sideways", "Black Swan", "High Volatility"]
        self._cache_mercado = {}
        logger.info(f"SimulacaoFilter inicializado com {self.num_agentes} agentes.")

    def _carregar_dados_mercado(self, simbolo: str) -> dict:
        """Carrega dados reais de mercado da Clarividencia (CoinGecko)."""
        if simbolo in self._cache_mercado:
            return self._cache_mercado[simbolo]

        dados = {
            "sentiment_score": 0.0,
            "sentiment_label": "neutro",
            "signal_action": "neutral",
            "signal_confidence": 0.0,
            "fear_greed_value": 50,
            "fear_greed_label": "Neutral",
        }

        if _CG_DISPONIVEL:
            sent = get_sentiment(simbolo)
            if sent:
                dados["sentiment_score"] = sent.score
                dados["sentiment_label"] = sent.classificacao
            sinal = get_sinais(simbolo)
            if sinal:
                dados["signal_action"] = sinal.acao
                dados["signal_confidence"] = sinal.confianca
            fg = get_fear_greed()
            if fg:
                dados["fear_greed_value"] = fg.get("value", 50)
                dados["fear_greed_label"] = fg.get("classification", "Neutral")

        self._cache_mercado[simbolo] = dados
        return dados

    async def _simular_agente(self, agente_id: int, sinal: Dict[str, Any],
                              dados_mercado: dict) -> ResultadoSimulacao:
        """Simula um agente usando dados reais de mercado + variacao de estilo."""
        await asyncio.sleep(random.uniform(0.005, 0.02))

        cenario = random.choice(self.cenarios)
        estilo = ESTILOS[agente_id % len(ESTILOS)]

        sent_score = dados_mercado.get("sentiment_score", 0.0)
        fg_value = dados_mercado.get("fear_greed_value", 50)
        signal_conf = dados_mercado.get("signal_confidence", 0.0)
        signal_action = dados_mercado.get("signal_action", "neutral")

        # Probabilidade base vinda do mercado real
        base_prob = 0.5 + (sent_score * 0.15) + ((50 - fg_value) / 100 * 0.15) + (signal_conf * 0.1)
        base_prob = max(0.1, min(0.95, base_prob))

        # Ajuste por estilo de trading
        if estilo == "momentum":
            prob = base_prob + 0.05 if abs(sent_score) > 0.3 else base_prob - 0.05
        elif estilo == "contrarian":
            prob = base_prob + 0.08 if abs(sent_score) > 0.5 else base_prob - 0.03
        elif estilo == "breakout":
            prob = base_prob + 0.10 if signal_conf > 0.5 else base_prob - 0.05
        elif estilo == "dca":
            prob = base_prob + 0.03
        elif estilo == "scalping":
            prob = base_prob + 0.06 if abs(sent_score) < 0.3 else base_prob - 0.05
        else:
            prob = base_prob

        prob = max(0.05, min(0.98, prob))

        # Ajuste por cenario
        if cenario == "Black Swan":
            prob *= 0.6
        elif cenario == "High Volatility":
            prob *= 0.85 if abs(sent_score) > 0.3 else 0.75

        sucesso = random.random() < prob

        # Lucro estimado baseado na confianca do sinal + sentimento
        lucro_base = signal_conf * 30 + abs(sent_score) * 20
        if sucesso:
            lucro = random.uniform(lucro_base * 0.3, lucro_base * 1.5)
        else:
            lucro = random.uniform(-lucro_base * 0.8, -lucro_base * 0.2)

        confianca = prob * random.uniform(0.85, 1.0)
        confianca = min(confianca, 0.99)

        return ResultadoSimulacao(
            agente_id=agente_id,
            sucesso=sucesso,
            lucro_estimado=round(lucro, 2),
            confianca=round(confianca, 4),
            cenario=cenario,
            estilo=estilo,
        )

    async def validar_sinal(self, sinal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa 60 simulacoes em paralelo usando dados reais de mercado.
        Retorna score de brutalidade para o SignalBridge.
        """
        simbolo = sinal.get("symbol") or sinal.get("ativo", "BTCUSDT")
        logger.info(f"Validacao de elite para {simbolo} ({self.num_agentes} agentes)")

        dados_mercado = self._carregar_dados_mercado(simbolo)

        tasks = [self._simular_agente(i, sinal, dados_mercado) for i in range(self.num_agentes)]
        resultados = await asyncio.gather(*tasks)

        sucessos = [r for r in resultados if r.sucesso]
        taxa_vitoria = len(sucessos) / self.num_agentes
        lucro_medio = sum(r.lucro_estimado for r in resultados) / self.num_agentes
        confianca_media = sum(r.confianca for r in resultados) / self.num_agentes

        # Distribuicao por estilo
        estilo_stats = {}
        for r in resultados:
            estilo_stats.setdefault(r.estilo, {"total": 0, "sucessos": 0})
            estilo_stats[r.estilo]["total"] += 1
            if r.sucesso:
                estilo_stats[r.estilo]["sucessos"] += 1

        score_brutalidade = (taxa_vitoria * 0.5) + (confianca_media * 0.3) + (min(lucro_medio, 50) / 50 * 0.2)
        score_brutalidade = max(0.0, min(1.0, score_brutalidade))

        passou_filtro = taxa_vitoria >= 0.65 and lucro_medio > 0

        logger.info(f"Brutalidade: {score_brutalidade:.4f} | Vitoria: {taxa_vitoria:.2%} | Lucro: {lucro_medio:.2f}")

        return {
            "passou_filtro": passou_filtro,
            "taxa_vitoria": round(taxa_vitoria, 4),
            "lucro_medio": round(lucro_medio, 2),
            "confianca_media": round(confianca_media, 4),
            "score_brutalidade": round(score_brutalidade, 4),
            "detalhes_agentes": len(resultados),
            "dados_mercado": dados_mercado,
            "estilos": estilo_stats,
        }

# Exemplo de uso (para testes internos)
if __name__ == "__main__":
    filtro = SimulacaoFilter()
    sinal_teste = {"id": "SIG-999", "tipo": "LONG", "ativo": "BTC/USDT"}
    resultado = asyncio.run(filtro.validar_sinal(sinal_teste))
    print(f"Resultado do Filtro: {resultado}")
