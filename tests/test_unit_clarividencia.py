import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest
from unittest.mock import patch, MagicMock

import clarividencia as cv


class TestClarividencia(unittest.TestCase):

    def test_get_sentiment_btc(self):
        sent = cv.get_sentiment("BTCUSDT")
        self.assertIsNotNone(sent)
        self.assertEqual(sent.simbolo, "BTCUSDT")
        self.assertIn(sent.classificacao, ["bullish_forte", "bullish", "levemente_bullish", "neutro", "levemente_bearish", "bearish", "bearish_forte"])

    def test_get_sinais_btc(self):
        sinal = cv.get_sinais("BTCUSDT")
        self.assertIsNotNone(sinal)
        self.assertIn(sinal.acao, ["buy", "sell", "neutral"])

    def test_get_fear_greed(self):
        fg = cv.get_fear_greed()
        self.assertIsNotNone(fg)
        self.assertIn("value", fg)
        self.assertIn("classification", fg)

    def test_triangulate_query(self):
        qs = cv.triangulate_query("bitcoin")
        self.assertTrue(len(qs) >= 3)

    def test_search_sources(self):
        results = cv.search_sources(["bitcoin"])
        self.assertIsInstance(results, list)

    def test_get_ultimas_noticias(self):
        with patch.object(cv, '_MOCK_MODE', True):
            n = cv.get_ultimas_noticias(3)
            self.assertIsInstance(n, list)

    def test_filter_judge(self):
        items = [{"title": "a", "score": 0.3}, {"title": "b", "score": 0.9}, {"title": "c", "score": 0.6}]
        filtered = cv.filter_judge(items)
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered[0]["title"], "b")


if __name__ == "__main__":
    unittest.main()
