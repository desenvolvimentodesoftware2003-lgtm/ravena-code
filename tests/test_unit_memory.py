import sys
import os
import tempfile
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "memory"))

import importlib.util
p = Path(__file__).parent.parent / "src" / "memory" / "memory_core_v3_2_6.py"
spec = importlib.util.spec_from_file_location("mem_mod", p)
mem = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mem)
EpisodicMemory = mem.EpisodicMemory
SemanticMemory = mem.SemanticMemory
MemoryManager = mem.MemoryManager

import unittest


class TestEpisodicMemory(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".json")
        self.mem = EpisodicMemory(filepath=self.tmp)

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_adicionar_e_recuperar(self):
        self.mem.adicionar("Alex", "Ola", "Oi!")
        epis = self.mem.recuperar(limite=10)
        self.assertEqual(len(epis), 1)
        self.assertEqual(epis[0].usuario, "Alex")

    def test_recuperar_por_usuario(self):
        self.mem.adicionar("Alex", "P1", "R1")
        self.mem.adicionar("Bob", "P2", "R2")
        epis = self.mem.recuperar(usuario="Alex")
        self.assertEqual(len(epis), 1)
        self.assertEqual(epis[0].pergunta, "P1")

    def test_buscar_por_termo(self):
        self.mem.adicionar("Alex", "qual o lucro?", "lucro de 5%")
        self.mem.adicionar("Alex", "qual a perda?", "perda de 2%")
        resultados = self.mem.buscar("lucro")
        self.assertEqual(len(resultados), 1)

    def test_persistencia(self):
        self.mem.adicionar("Alex", "teste", "ok")
        self.mem2 = EpisodicMemory(filepath=self.tmp)
        self.assertEqual(self.mem2.total, 1)


class TestSemanticMemory(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".json")
        self.mem = SemanticMemory(filepath=self.tmp)

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_adicionar_e_obter(self):
        self.mem.adicionar("versao", "3.2.6", fonte="teste")
        fato = self.mem.obter("versao")
        self.assertIsNotNone(fato)
        self.assertEqual(fato.valor, "3.2.6")

    def test_buscar_por_termo(self):
        self.mem.adicionar("brutality", "0.52", categoria="trading")
        self.mem.adicionar("alocacao", "2%", categoria="trading")
        resultados = self.mem.buscar("brutality")
        self.assertEqual(len(resultados), 1)

    def test_listar_categoria(self):
        self.mem.adicionar("k1", "v1", categoria="trading")
        self.mem.adicionar("k2", "v2", categoria="sistema")
        self.assertEqual(len(self.mem.listar_categoria("trading")), 1)
        self.assertEqual(len(self.mem.listar_categoria("sistema")), 1)


class TestMemoryManager(unittest.TestCase):

    def setUp(self):
        self.tmp_ep = tempfile.mktemp(suffix=".json")
        self.tmp_sem = tempfile.mktemp(suffix=".json")
        self.mgr = MemoryManager()
        self.mgr.episodica = EpisodicMemory(filepath=self.tmp_ep)
        self.mgr.semantica = SemanticMemory(filepath=self.tmp_sem)

    def tearDown(self):
        for f in [self.tmp_ep, self.tmp_sem]:
            if os.path.exists(f):
                os.remove(f)

    def test_fluxo_completo(self):
        self.mgr.registrar_interacao("Alex", "Ola", "Oi!")
        self.mgr.aprender("versao", "3.2.6", fonte="teste")
        ctx = self.mgr.contexto_recente("Alex")
        self.assertIn("Ola", ctx)
        self.assertEqual(self.mgr.lembrar("versao"), "3.2.6")
        diag = self.mgr.diagnostic()
        self.assertEqual(diag["episodios"], 1)
        self.assertEqual(diag["fatos"], 1)


if __name__ == "__main__":
    unittest.main()
