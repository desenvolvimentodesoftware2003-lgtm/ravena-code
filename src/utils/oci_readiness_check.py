"""
RAVENA AI v3.2.7 — src/utils/oci_readiness_check.py
==================================================
Script de Diagnóstico de Prontidão para Migração OCI.
Verifica se o ambiente atual cumpre os requisitos do Protocolo R6.
"""
import os
import sys
import platform
import json
import logging

# Configuração de Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("ravena.readiness")

class ReadinessChecker:
    def __init__(self):
        self.results = {
            "system": {},
            "dependencies": {},
            "security": {},
            "overall_status": "PENDING"
        }

    def check_system(self):
        logger.info("Verificando requisitos de sistema...")
        self.results["system"]["os"] = platform.system()
        self.results["system"]["python_version"] = sys.version.split()[0]
        
        # Requisito: Python 3.11+
        version_ok = sys.version_info >= (3, 11)
        self.results["system"]["python_ok"] = version_ok
        return version_ok

    def check_dependencies(self):
        logger.info("Verificando dependências de software...")
        required = ["oci", "cryptography", "langchain", "chromadb"]
        missing = []
        for lib in required:
            try:
                __import__(lib)
                self.results["dependencies"][lib] = "INSTALLED"
            except ImportError:
                self.results["dependencies"][lib] = "MISSING"
                missing.append(lib)
        
        self.results["dependencies"]["missing_count"] = len(missing)
        return len(missing) == 0

    def check_security_r6(self):
        logger.info("Verificando conformidade com Protocolo R6 (Checkpoints Iniciais)...")
        # Verificar se o HackerAgent está presente
        hacker_present = os.path.exists("/home/ubuntu/Ravena_AI_Core_Infrastructure/06_Arquitetura_Modular_e_Versoes/ravena-modular_v3/src/security/hacker_agent.py")
        self.results["security"]["hacker_agent_present"] = hacker_present
        
        # Verificar se o SecurityCore v3.2.7 está presente
        security_v327 = os.path.exists("/home/ubuntu/Ravena_AI_Core_Infrastructure/06_Arquitetura_Modular_e_Versoes/ravena-modular_v3/src/security/security_core_v3.2.7.py")
        self.results["security"]["security_core_v327_present"] = security_v327
        
        return hacker_present and security_v327

    def run_all(self):
        s_ok = self.check_system()
        d_ok = self.check_dependencies()
        sec_ok = self.check_security_r6()
        
        if s_ok and d_ok and sec_ok:
            self.results["overall_status"] = "READY_FOR_OCI"
        else:
            self.results["overall_status"] = "NOT_READY"
            
        return self.results

if __name__ == "__main__":
    checker = ReadinessChecker()
    report = checker.run_all()
    print("\n--- RELATÓRIO DE PRONTIDÃO OCI (RAVENA v3.2.7) ---")
    print(json.dumps(report, indent=4))
    
    if report["overall_status"] == "READY_FOR_OCI":
        print("\n✅ SISTEMA PRONTO PARA MIGRAÇÃO OCI.")
    else:
        print("\n❌ SISTEMA NÃO ESTÁ PRONTO. VERIFIQUE AS DEPENDÊNCIAS ACIMA.")
