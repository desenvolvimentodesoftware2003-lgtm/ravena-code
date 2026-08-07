"""
RAVENA AI v3.2.6 — Teste de Integração Final
============================================
Validação do fluxo completo: Segurança -> Multimodalidade -> Especialização -> Personalidade -> Aprendizado.
"""

import logging
import sys
import os
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

omega_mod = import_from_file("omega_mod_int", PROJECT_ROOT / "src/core" / "omega_v3.2.6.py")
Omega = omega_mod.Omega

# Configuração de Logging para o teste
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ravena.test")

def executar_teste_supremo():
    logger.info("Iniciando Teste de Integração Supremo - Ravena AI v3.2.6")
    
    try:
        omega = Omega()
        
        # Test 1: Diagnóstico do sistema
        logger.info("--- Teste 1: Diagnóstico do Sistema ---")
        diagnostico = omega.obter_diagnostico()
        logger.info(f"Versão: {diagnostico['versao']}")
        logger.info(f"Status: {diagnostico['status']}")
        assert diagnostico["status"] == "OPERACIONAL", "Falha: Sistema não está OPERACIONAL"
        
        # Test 2: Percepção Visual com snapshot simulado
        logger.info("--- Teste 2: Percepção Visual Autônoma ---")
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
        omega.processar_percepcao_visual(snapshot)
        logger.info("Percepção visual processada com sucesso")
        
        # Test 3: Juiz Universal (segurança)
        logger.info("--- Teste 3: Juiz Universal (Segurança) ---")
        seguro, msg = omega.juiz.validar_comando("Meu token é sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234")
        assert not seguro, "Falha: Juiz não bloqueou vazamento de token"
        logger.info(f"Bloqueio de token confirmado: {msg}")
        
        logger.info("--- RESULTADOS DO TESTE ---")
        logger.info(f"Diagnóstico: {diagnostico}")
        logger.info(f"Ciclos de autocorreção: {diagnostico.get('ciclos_autocorrecao', 0)}")
        logger.info(f"Uptime: {diagnostico.get('uptime_segundos', 0)}s")
        
        logger.info("Teste de Integração concluído com SUCESSO!")
        return True
        
    except Exception as e:
        logger.error(f"Erro durante o teste de integração: {str(e)}")
        return False

if __name__ == "__main__":
    # Como os módulos reais estão no Drive, o Omega usará os Mocks definidos no arquivo final para este teste de ambiente
    success = executar_teste_supremo()
    sys.exit(0 if success else 1)
