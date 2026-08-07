"""
TEST_MANUS_AI_LEVEL — Teste de Qualificação de Alto Nível para Agente Dev
========================================================================
Este teste valida se o Agente Dev (Ravena AI) opera no padrão Manus AI,
focando em:
  1. Raciocínio Complexo (Fusão Visão + RAG).
  2. Segurança Zero Trust (Blindagem de Identidade e Privilégio).
  3. Autocorreção Autônoma (Resiliência sob ataque).
  4. Orquestração via Núcleo Omega.
"""

import unittest
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "core"))

import importlib.util
spec = importlib.util.spec_from_file_location("omega_mod", PROJECT_ROOT / "src" / "core" / "omega_v3.2.6.py")
omega_mod = importlib.util.module_from_spec(spec)
sys.modules["omega_mod"] = omega_mod
spec.loader.exec_module(omega_mod)
obter_omega = omega_mod.obter_omega

class TestManusAILevel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.omega = obter_omega()
        print(f"\n[MANUS_AI_TEST] Iniciando Qualificação - Versão: {cls.omega.status.versao}")

    def test_01_raciocinio_complexo_visao_rag(self):
        """Valida a fusão de percepção visual com conhecimento técnico RAG."""
        print("\n--- CENÁRIO 1: FUSÃO VISÃO + RAG ---")
        
        class MockPadrao:
            def __init__(self, tipo, desc, conf):
                self.tipo_anomalia = tipo
                self.descricao = desc
                self.confianca = conf
        
        class MockSnapshot:
            def __init__(self, padroes):
                self.padroes_detectados = padroes

        snapshot = MockSnapshot([
            MockPadrao("degradação_performance", "CPU em 95% e Latência em 500ms", 0.92)
        ])

        ciclos_antes = self.omega.status.ciclos_autocorrecao
        self.omega.processar_percepcao_visual(snapshot)
        
        self.assertEqual(self.omega.status.ciclos_autocorrecao, ciclos_antes + 1)
        print(f"[OK] Percepção visual processada com autocorreção (Ciclo #{self.omega.status.ciclos_autocorrecao})")

    def test_02_blindagem_zero_trust_manus_level(self):
        """Valida se o sistema bloqueia acessos não autorizados."""
        print("\n--- CENÁRIO 2: BLINDAGEM ZERO TRUST ---")
        
        seguro, msg = self.omega.juiz.validar_comando("sudo rm -rf /")
        
        self.assertFalse(seguro)
        self.assertIn("bloqueado", msg.lower())
        print(f"[OK] Bloqueio Lockdown confirmado: {msg}")

    def test_03_autocorrecao_sob_ataque_brute_force(self):
        """Valida a capacidade de autocorreção autônoma em resposta a ataques."""
        print("\n--- CENÁRIO 3: AUTOCORREÇÃO AUTÔNOMA ---")
        
        ciclos_iniciais = self.omega.status.ciclos_autocorrecao
        
        class MockPadrao:
            def __init__(self, tipo, desc, conf):
                self.tipo_anomalia = tipo
                self.descricao = desc
                self.confianca = conf
        
        class MockSnapshot:
            def __init__(self, padroes):
                self.padroes_detectados = padroes

        snapshot_ataque = MockSnapshot([
            MockPadrao("ataque_brute_force", "Ataque massivo detectado do IP 172.16.0.1", 0.99)
        ])

        self.omega.processar_percepcao_visual(snapshot_ataque)
        
        self.assertEqual(self.omega.status.ciclos_autocorrecao, ciclos_iniciais + 1)
        print(f"[OK] Ciclo de autocorreção executado (Total: {self.omega.status.ciclos_autocorrecao})")

    def test_04_diagnostico_integridade_manus_ai(self):
        """Valida se o diagnóstico do sistema reflete o padrão de excelência."""
        print("\n--- CENÁRIO 4: DIAGNÓSTICO DE INTEGRIDADE ---")
        
        diagnostico = self.omega.obter_diagnostico()
        
        self.assertEqual(diagnostico["status"], "OPERACIONAL")
        self.assertIn("versao", diagnostico)
        self.assertIn("ciclos_autocorrecao", diagnostico)
        print(f"[OK] Diagnóstico validado: {diagnostico['status']} v{diagnostico['versao']}")

if __name__ == "__main__":
    unittest.main()
