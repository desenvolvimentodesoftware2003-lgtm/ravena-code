"""
VALIDADOR VERACIDADE — Modulo de Validacao de Informacao (v1.0.0)
=================================================================
Ravena AIM | Modulo: seguranca cognitiva
Extraido e atualizado de security_core_v3.2.6.
Responsabilidades:
  - Validar veracidade de informacoes coletadas
  - Cruzar dados com base de conhecimento
  - Pontuar confianca das fontes
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("ravena.validador_veracidade")


class ValidadorVeracidade:
    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def validar_informacao(self, topico: str, conteudo: str, tipo: str = "web_search") -> Tuple[bool, float, str]:
        if not conteudo:
            return False, 0.0, "Conteudo vazio"

        score = 0.0
        razoes = []

        if tipo == "web_search":
            score += self._validar_comprimento(conteudo)
            score += self._validar_entidades(conteudo)
            score += self._validar_fontes(conteudo)
            score += self._validar_coerencia(topico, conteudo)
            score /= 4.0

            if score < 0.3:
                razoes.append("Baixa confianca no conteudo")
            if score < self.threshold:
                razoes.append("Abaixo do threshold de seguranca")

        is_valido = score >= self.threshold
        motivo = "; ".join(razoes) if razoes else ("Valido" if is_valido else "Invalido")
        logger.info(f"Veracidade para '{topico[:40]}': {score:.2f} {'✓' if is_valido else '✗'}")
        return is_valido, round(score, 3), motivo

    def _validar_comprimento(self, texto: str) -> float:
        if len(texto) > 500:
            return 1.0
        if len(texto) > 200:
            return 0.7
        if len(texto) > 50:
            return 0.4
        return 0.1

    def _validar_entidades(self, texto: str) -> float:
        padroes = [
            r"\b[A-Z]{2,}\b",
            r"\b\d+[.,]\d+\b",
            r"\b(bitcoin|btc|ethereum|eth|usdt|blockchain|defi)\b",
            r"\b(million|billion|percent|%)\b",
        ]
        encontrados = sum(1 for p in padroes if re.search(p, texto, re.IGNORECASE))
        return min(1.0, encontrados / len(padroes))

    def _validar_fontes(self, texto: str) -> float:
        padroes_citacao = [
            r"(according to|source|report|study|data from|per )",
            r"\b(coin(desk|telegraph)|bloomberg|reuters|cnbc|forbes|the block)\b",
            r"\[\d+\]",
            r"http[s]?://",
        ]
        encontrados = sum(1 for p in padroes_citacao if re.search(p, texto, re.IGNORECASE))
        return min(1.0, encontrados / len(padroes_citacao))

    def _validar_coerencia(self, topico: str, texto: str) -> float:
        termos_topico = set(re.findall(r"\w+", topico.lower()))
        termos_texto = set(re.findall(r"\w+", texto.lower()))
        if not termos_topico:
            return 0.5
        intersecao = termos_topico.intersection(termos_texto)
        return min(1.0, len(intersecao) / len(termos_topico) * 1.5)


if __name__ == "__main__":
    v = ValidadorVeracidade()
    is_ok, score, motivo = v.validar_informacao("Bitcoin ETF", "According to Bloomberg, the Bitcoin ETF approved by SEC reached $1 billion in volume. Source: CoinDesk.")
    print(f"Valido: {is_ok}, Score: {score}, Motivo: {motivo}")
