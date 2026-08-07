import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "trading"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import importlib.util
import unittest
from unittest.mock import patch, MagicMock

p = Path(__file__).parent.parent / "src" / "trading" / "step_scaling.py"
spec = importlib.util.spec_from_file_location("step_scaling_mod", p)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
StepScaling = mod.StepScaling


class TestStepScaling(unittest.TestCase):

    def test_inicializacao(self):
        s = StepScaling(testnet=True)
        self.assertTrue(s.testnet)

    def test_grade_calcula_passos(self):
        s = StepScaling(testnet=True)
        mock_session = MagicMock()
        mock_session.place_order.return_value = {"retCode": 0}
        s._session = mock_session
        passos = s.pendurar_grade("BTCUSDT", "buy", 50000.0, 0.001, num_passos=2, dist_percentual=0.01, multiplicador=1.5)
        self.assertEqual(len(passos), 2)
        self.assertEqual(passos[0].nivel, 1)
        self.assertEqual(passos[1].nivel, 2)
        self.assertAlmostEqual(passos[0].quantidade, 0.001 * 1.5, places=4)
        self.assertAlmostEqual(passos[1].quantidade, 0.001 * 1.5 ** 2, places=4)

    def test_estrategia_sem_preco(self):
        s = StepScaling(testnet=True)
        with patch.object(s, 'obter_preco_atual', return_value=None):
            r = s.executar_estrategia("BTCUSDT", "buy", 0.001)
            self.assertEqual(r["status"], "ERRO")

    def test_estrategia_completa(self):
        s = StepScaling(testnet=True)
        with patch.object(s, 'obter_preco_atual', return_value=50000.0):
            with patch.object(s, 'abrir_posicao', return_value=True):
                with patch.object(s, 'pendurar_grade', return_value=[]):
                    r = s.executar_estrategia("BTCUSDT", "buy", 0.001)
                    self.assertEqual(r["status"], "EXECUTADO")


if __name__ == "__main__":
    unittest.main()
