import os
import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "security"))

import importlib.util

def _import_mod(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

omega_mod = _import_mod("omega_mod", PROJECT_ROOT / "src" / "core" / "omega_v3_2_6.py")
juiz_mod = _import_mod("juiz_mod", PROJECT_ROOT / "src" / "security" / "juiz_universal.py")
rag_mod = _import_mod("rag_mod", PROJECT_ROOT / "src" / "rag" / "rag_core_v3.2.6.py")

Omega = omega_mod.Omega
JuizUniversal = juiz_mod.JuizUniversal
RAGCore = rag_mod.RAGCore

logger = logging.getLogger("ravena.modular_main")

class RavenaModular:
    def __init__(self):
        print("=" * 50)
        print("INICIALIZANDO ARQUITETURA MODULAR RAVENA V3.2.6")
        print("=" * 50)

        self.omega = Omega()
        self.juiz = JuizUniversal()
        self.rag = RAGCore()
        self.historico = []

        diagnostico = self.omega.obter_diagnostico()
        print(f"[RAVENA] Omega: {diagnostico['status']} v{diagnostico['versao']}")

        print("=" * 50)
        print("SISTEMA PRONTO PARA OPERACAO")
        print("=" * 50)

    def processar_entrada(self, usuario, texto):
        saudacoes = ["oi", "ola", "bom dia", "boa tarde", "boa noite", "e ai", "opa"]
        if texto.lower().strip() in saudacoes:
            return "Ola! Sou a Ravena, sua assistente modular. Como posso te ajudar hoje?"

        seguro, msg = self.juiz.validar_comando(texto)
        if not seguro:
            return f"[BLOQUEADO] {msg}"

        self.juiz.auditar_acao(f"Processando entrada: {texto}", usuario)

        contexto = ""
        try:
            resultados = self.rag.buscar(texto, k=3)
            if resultados:
                contexto = f"Contexto: {resultados[0][0]}"
        except Exception:
            pass

        return f"[RAVENA] Entrada processada: {texto[:60]}... | Auditoria: OK | RAG: {'com contexto' if contexto else 'sem contexto'}"

    def executar_comando_seguro(self, comando):
        seguro, msg = self.juiz.validar_comando(comando)
        if not seguro:
            return msg
        self.juiz.auditar_acao(f"Executando comando: {comando}", "sistema")
        return f"Comando '{comando}' executado com sucesso (simulacao)."

    def obter_diagnostico(self):
        return self.omega.obter_diagnostico()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ravena = RavenaModular()

    print("\n--- TESTE 1: Interacao Basica ---")
    resp1 = ravena.processar_entrada("Alex", "Ola Ravena, como funciona sua arquitetura modular?")
    print(f"Resposta: {resp1}")

    print("\n--- TESTE 2: Seguranca (Lockdown V2.2) ---")
    resp2 = ravena.executar_comando_seguro("sudo rm -rf /")
    print(f"Resultado: {resp2}")

    print("\n--- TESTE 3: Diagnostico ---")
    diag = ravena.obter_diagnostico()
    print(f"Diagnostico: {diag['status']} v{diag['versao']} | Ciclos: {diag['ciclos_autocorrecao']}")

    print("\n" + "=" * 50)
    print("EXECUCAO DA ARQUITETURA CONCLUIDA")
    print("=" * 50)
