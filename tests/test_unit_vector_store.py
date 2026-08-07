import sys
import os
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "vector_store"))

import importlib.util
p = Path(__file__).parent.parent / "src" / "vector_store" / "vector_store_v3_2_6.py"
spec = importlib.util.spec_from_file_location("vs_mod", p)
vs_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs_mod)
VectorStoreManager = vs_mod.VectorStoreManager

import unittest


class TestVectorStoreManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.vs = VectorStoreManager(path=self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_listar_colecoes_inicial(self):
        colecoes = self.vs.listar_colecoes()
        self.assertIsInstance(colecoes, list)

    def test_criar_e_listar_colecao(self):
        self.vs.criar_colecao("test_collection")
        colecoes = self.vs.listar_colecoes()
        self.assertIn("test_collection", colecoes)

    def test_adicionar_e_contar(self):
        self.vs.criar_colecao("test_data")
        ids = self.vs.adicionar(
            textos=["Bitcoin subiu 5% hoje", "Ethereum em queda"],
            metadados=[{"fonte": "coindesk"}, {"fonte": "cointelegraph"}],
            colecao="test_data",
        )
        self.assertEqual(len(ids), 2)
        self.assertEqual(self.vs.contar(colecao="test_data"), 2)

    def test_buscar(self):
        self.vs.criar_colecao("test_search")
        self.vs.adicionar(
            textos=["O preco do Bitcoin subiu", "Noticias sobre Ethereum"],
            colecao="test_search",
        )
        resultados = self.vs.buscar("Bitcoin", k=1, colecao="test_search")
        self.assertTrue(len(resultados) >= 1)
        self.assertIn("documento", resultados[0])

    def test_health_check(self):
        health = self.vs.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertIn("colecoes", health)
        self.assertIn("stats", health)

    def test_deletar_colecao(self):
        self.vs.criar_colecao("to_delete")
        self.assertIn("to_delete", self.vs.listar_colecoes())
        self.vs.deletar_colecao("to_delete")
        self.assertNotIn("to_delete", self.vs.listar_colecoes())


if __name__ == "__main__":
    unittest.main()
