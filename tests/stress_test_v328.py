import json
import logging
import os
import sys
import time
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

hacker_mod = import_from_file("hacker_mod_stress", PROJECT_ROOT / "src/security/hacker_agent.py")
HackerAgent = hacker_mod.HackerAgent
agente_mod = import_from_file("agente_dev_mod_stress", PROJECT_ROOT / "src/orchestration/agente_dev_v3.2.6.py")
AgenteDev = agente_mod.AgenteDev

# Configuração de Logging para o Teste de Estresse
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(PROJECT_ROOT / "tests" / "stress_test_v3.2.8.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Ravena_Stress_Test_v3.2.8")

def run_stress_test():
    logger.info("=== INICIANDO TESTE DE ESTRESSE: PONTE INTELIGENTE v3.2.8 ===")
    
    hacker = HackerAgent()
    dev = AgenteDev(nome="Ravena_Dev_Original_Test")
    
    # Cenários de Teste de Estresse (Múltiplas Ameaças)
    cenarios = [
        {"alvo": "https://secure-wallet-login-update.com", "tipo": "url", "descricao": "Phishing de Carteira (Padrão: login-update)"},
        {"alvo": "https://fake-exchange.io/verify-account", "tipo": "url", "descricao": "Fake Exchange (Domínio Suspeito)"},
        {"alvo": "import threading; x = 0; def inc(): x += 1", "tipo": "codigo", "descricao": "Race Condition (Sem Lock)"},
        {"alvo": "https://scam-trading.com/secure-wallet", "tipo": "url", "descricao": "Scam Trading (Múltiplos Padrões)"}
    ]
    
    logger.info(f"Agentes Ativos: {hacker.nome} (Hacker) & {dev.nome} (Dev)")
    logger.info(f"Total de cenários para processamento: {len(cenarios)}")
    
    resultados_finais = []

    for i, cenario in enumerate(cenarios, 1):
        logger.info(f"\n--- Processando Cenário {i}: {cenario['descricao']} ---")
        
        # 1. Hacker analisa e gera vacina
        logger.info(f"[Hacker] Analisando alvo: {cenario['alvo']}")
        if cenario['tipo'] == "url":
            analise = hacker.analisar_ameaca(cenario['alvo'])
        else:
            analise = hacker.auditar_codigo_ofensivo(cenario['alvo'])
            # Adaptar formato para gerar_relatorio_vacina se necessário
            analise['veredito'] = "AMEAÇA_DETECTADA" if analise.get('vulnerabilidades_encontradas', 0) > 0 else "SEGURO"
            analise['detalhes'] = analise.get('lista_vulnerabilidades', [])
            analise['timestamp'] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        logger.info(f"[Hacker] Veredito: {analise.get('veredito')}")
        
        if analise.get('veredito') == "AMEAÇA_DETECTADA":
            relatorio_vacina = hacker.gerar_relatorio_vacina(analise)
            logger.info("[Hacker] Relatório de Vacina gerado.")
            
            # 2. Dev absorve e aplica
            logger.info("[Dev] Absorvendo vacina e aplicando patches...")
            resultado_dev = dev.absorver_relatorio_vacina(relatorio_vacina)
            
            if resultado_dev.get("status") == "SUCESSO":
                logger.info(f"[Dev] ✅ Vacina aplicada com sucesso: {resultado_dev.get('id_vacina')}")
                resultados_finais.append(True)
            else:
                logger.error(f"[Dev] ❌ Falha ao aplicar vacina: {resultado_dev.get('erro')}")
                resultados_finais.append(False)
        else:
            logger.info("[Hacker] Alvo considerado seguro. Nenhuma vacina necessária.")
            resultados_finais.append(True)

    # Resumo Final
    logger.info("\n=== RESUMO DO TESTE DE ESTRESSE ===")
    sucessos = resultados_finais.count(True)
    falhas = resultados_finais.count(False)
    logger.info(f"Cenários Processados: {len(cenarios)}")
    logger.info(f"Sucessos: {sucessos}")
    logger.info(f"Falhas: {falhas}")
    
    if falhas == 0:
        logger.info("✅ TESTE DE ESTRESSE CONCLUÍDO COM SUCESSO TOTAL!")
    else:
        logger.warning("⚠️ TESTE DE ESTRESSE CONCLUÍDO COM ALGUMAS FALHAS.")

if __name__ == "__main__":
    run_stress_test()
