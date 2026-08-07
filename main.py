"""
RAVENA AIM v3.2.6 — Entrypoint Principal
=========================================
CLI para orquestrar todos os subsistemas: health check, trading, chat, dev.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ravena.main")

def cmd_health(args):
    from tests.health_check import test_module, test_secrets_manager, test_zero_trust
    from tests.health_check import test_omega_orchestrator_module, test_omega_v326, test_omega_legacy
    from tests.health_check import test_ravena_model, test_auditor, test_hacker_agent
    from tests.health_check import test_hacker_v328, test_security_core, test_rag_advanced
    from tests.health_check import test_rag_v326, test_signal_bridge, test_bybit_connector
    from tests.health_check import test_trade_brain, test_social_connector, test_telegram_bot
    from tests.health_check import test_engine_patch, test_external_api_manager
    from tests.health_check import test_zero_trust_to_omega, test_secrets_audit, test_rag_ingest_query
    from tests.health_check import results

    tests = [
        ("SecretsManager", test_secrets_manager),
        ("ZeroTrust Protocol", test_zero_trust),
        ("OmegaOrchestrator v3.2.6", test_omega_orchestrator_module),
        ("Omega v3.2.6", test_omega_v326),
        ("Omega (legacy)", test_omega_legacy),
        ("Ravena Model", test_ravena_model),
        ("Auditor", test_auditor),
        ("Hacker Agent v3.2.7", test_hacker_agent),
        ("Hacker Agent v3.2.8 Final", test_hacker_v328),
        ("Security Core v3.2.7", test_security_core),
        ("RAG Advanced", test_rag_advanced),
        ("RAG Advanced v3.2.6", test_rag_v326),
        ("Signal Bridge", test_signal_bridge),
        ("Bybit Connector", test_bybit_connector),
        ("Trade Brain", test_trade_brain),
        ("Social Connector", test_social_connector),
        ("Telegram Bot", test_telegram_bot),
        ("Engine Patch", test_engine_patch),
        ("External API Manager", test_external_api_manager),
        ("ZeroTrust to OmegaOrchestrator", test_zero_trust_to_omega),
        ("Secrets Audit", test_secrets_audit),
        ("RAG Ingest + Query", test_rag_ingest_query),
    ]
    for name, func in tests:
        test_module(name, func)
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print(f"\nHealth Check: {passed}/{total} passed")
    return 0 if passed == total else 1

def cmd_trade(args):
    from src.trading.bybit_connector_v3_2_6 import BybitConnector
    from src.trading.signal_bridge_v3_2_6 import process_signal
    bc = BybitConnector()
    logger.info(f"BybitConnector inicializado: {bc}")
    logger.info(f"Modo: paper-trade | Signal Bridge disponível")
    return 0

def cmd_chat(args):
    logger.info("Modo chat interativo (pressione Ctrl+C para sair)")
    try:
        while True:
            user_input = input("\n> ")
            if user_input.lower() in ("sair", "exit", "quit"):
                break
            print(f"Ravena: processando: {user_input}")
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrando chat.")
    return 0

def cmd_dev(args):
    import code
    vars = {
        "PROJECT_ROOT": PROJECT_ROOT,
        "os": os,
        "json": json,
        "logger": logger,
    }
    banner = f"Ravena AIM v3.2.6 — Console Interativo\n{PROJECT_ROOT}"
    code.interact(local=vars, banner=banner)
    return 0

def cmd_serve(args):
    from src.api.server import app
    import uvicorn
    port = int(os.environ.get("API_PORT", "8000"))
    host = os.environ.get("API_HOST", "0.0.0.0")
    logger.info(f"Ravena AIM API v3.2.6 em http://{host}:{port}")
    logger.info(f"Documentação em http://{host}:{port}/docs")
    uvicorn.run(app, host=host, port=port)
    return 0

def cmd_telegram(args):
    from src.orchestration.telegram_bot import run_polling
    logger.info("Iniciando bot Telegram Ravena...")
    run_polling()
    return 0

def main():
    parser = argparse.ArgumentParser(description="Ravena AIM v3.2.6")
    parser.add_argument("command", nargs="?", default="health", choices=["health", "trade", "chat", "dev", "serve", "telegram"])
    args = parser.parse_args()

    commands = {
        "health": cmd_health,
        "trade": cmd_trade,
        "chat": cmd_chat,
        "dev": cmd_dev,
        "serve": cmd_serve,
        "telegram": cmd_telegram,
    }
    sys.exit(commands[args.command](args))

if __name__ == "__main__":
    main()
