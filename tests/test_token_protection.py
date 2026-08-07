import sys
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

juiz_mod = import_from_file("juiz_universal_mod", PROJECT_ROOT / "src/security/juiz_universal.py")
JuizUniversal = juiz_mod.JuizUniversal

def testar_protecao_tokens():
    juiz = JuizUniversal()
    print("\n" + "="*50)
    print("TESTE DE PROTEÇÃO DE TOKENS E APIs - LOCKDOWN V2.2")
    print("="*50)

    testes = [
        ("Listar arquivos", "ls -la"),
        ("Vazamento de Token OpenAI", "Meu token é sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234"),
        ("Vazamento de Token Telegram", "Use o bot com o token 123456789:ABCDefghIJKLmnopQRSTuvwxYZ123456789"),
        ("Vazamento de Token GitHub", "A chave de acesso é ghp_123456789012345678901234567890123456"),
        ("Vazamento de API Key Google", "Chave do Maps: AIzaSyA12345678901234567890123456789012")
    ]

    for descricao, entrada in testes:
        print(f"\n[TESTE] {descricao}")
        seguro, msg = juiz.validar_comando(entrada)
        if not seguro:
            print(f"  [BLOQUEADO] {msg}")
        else:
            print(f"  [PERMITIDO] Entrada validada como segura.")

if __name__ == "__main__":
    testar_protecao_tokens()
