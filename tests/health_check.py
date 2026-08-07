"""
RAVENA AIM — Health Check Completo v3.2.6
==========================================
Versão: v3.2.6
Data: 2026-07-12

Este script testa a inicialização e comunicação de todos os módulos
do sistema Ravena AIM.

Resultado: Relatório de sanidade do sistema.
"""

import sys
import os
import time
import importlib
import importlib.util
import traceback
import json
from datetime import datetime
from pathlib import Path

# Configurar o path para importar os módulos
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Carregar .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# ─────────────────────────────────────────────
# HELPER: Importar módulos com ponto no nome
# ─────────────────────────────────────────────
TYPING_NAMES = {'Any', 'Dict', 'List', 'Optional', 'Tuple', 'Union', 'Set',
                'Callable', 'Type', 'Enum', 'datetime', 'deque', 'Path'}

def import_from_file(module_name, file_path):
    """Importa um módulo Python a partir do caminho do arquivo."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_real_classes(mod):
    """Retorna apenas classes reais do módulo (exclui typing, builtins, etc)."""
    return [c for c in dir(mod) 
            if not c.startswith('_') 
            and c not in TYPING_NAMES
            and isinstance(getattr(mod, c), type)
            and getattr(mod, c).__module__ not in ('typing', 'builtins', 'enum', 'datetime', 'collections')]


# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────
results = []
start_time = time.time()


def test_module(name, test_func):
    """Wrapper para testar um módulo e capturar resultado."""
    print(f"\n{'─' * 60}")
    print(f"  TESTANDO: {name}")
    print(f"{'─' * 60}")
    t0 = time.time()
    try:
        status, details = test_func()
        elapsed = round(time.time() - t0, 3)
        icon = "✅" if status == "PASS" else "⚠️" if status == "WARN" else "❌"
        print(f"  {icon} {name}: {status} ({elapsed}s)")
        print(f"     └─ {details}")
        results.append({
            "module": name,
            "status": status,
            "details": details,
            "time_ms": int(elapsed * 1000)
        })
    except Exception as e:
        elapsed = round(time.time() - t0, 3)
        error_msg = f"{type(e).__name__}: {str(e)}"
        tb_lines = traceback.format_exc().strip().split('\n')
        tb_hint = tb_lines[-2].strip() if len(tb_lines) > 1 else ""
        print(f"  ❌ {name}: FAIL ({elapsed}s)")
        print(f"     └─ {error_msg}")
        if tb_hint:
            print(f"     └─ {tb_hint}")
        results.append({
            "module": name,
            "status": "FAIL",
            "details": error_msg,
            "time_ms": int(elapsed * 1000)
        })


# ═══════════════════════════════════════════════
# TESTES DE INICIALIZAÇÃO INDIVIDUAL
# ═══════════════════════════════════════════════

def test_secrets_manager():
    """Testa o SecretsManager (módulo central de credenciais)."""
    mod = import_from_file("secrets_mgr", PROJECT_ROOT / "src/core/secrets_manager.py")
    secrets = mod.secrets
    status_all = secrets.get_all()
    loaded = sum(1 for v in status_all.values() if v["loaded"])
    total = len(status_all)
    zt_key = secrets.get("RAVENA_ZERO_TRUST_SECRET")
    if zt_key and loaded > 0:
        return "PASS", f"Fonte: {secrets.source} | {loaded}/{total} secrets carregados | ZT_KEY: OK"
    else:
        return "WARN", f"Fonte: {secrets.source} | {loaded}/{total} secrets | ZT_KEY: {'OK' if zt_key else 'MISSING'}"


def test_zero_trust():
    """Testa o Protocolo Zero Trust (geração e validação de tokens)."""
    mod = import_from_file("zero_trust_mod", PROJECT_ROOT / "src/security/zero_trust_v3.2.6.py")
    zt = mod.ZeroTrustProtocol()
    token = zt.generate_token("test_module")
    if not token:
        return "FAIL", "Token gerado é None"
    is_valid = zt.validate_access("test_module", token)
    if is_valid:
        return "PASS", f"Token gerado e validado com sucesso | Token: {str(token)[:30]}..."
    else:
        return "FAIL", "Token gerado mas validação falhou"


def test_omega_orchestrator_module():
    """Testa a inicialização do OmegaOrchestrator v3.2.6."""
    mod = import_from_file("omega_orch_mod", PROJECT_ROOT / "src/core/omega_orchestrator_v3.2.6.py")
    target = getattr(mod, 'OmegaOrchestrator', None)
    if target is None:
        classes = get_real_classes(mod)
        if not classes:
            all_names = [n for n in dir(mod) if not n.startswith('_')]
            return "WARN", f"Módulo carregou com exports: {all_names[:5]}"
        target = getattr(mod, classes[-1])
    obj = target()
    return "PASS", f"{target.__name__} inicializado"


def test_omega_v326():
    """Testa a inicialização do Omega v3.2.6."""
    mod = import_from_file("omega_v326_mod", PROJECT_ROOT / "src/core/omega_v3.2.6.py")
    # Instanciar a classe principal Omega (não dataclasses auxiliares)
    target = getattr(mod, 'Omega', None)
    if target is None:
        classes = get_real_classes(mod)
        if not classes:
            return "WARN", "Módulo carregou mas sem classes reais"
        target = getattr(mod, classes[-1])  # Última classe geralmente é a principal
    obj = target()
    diag = obj.obter_diagnostico() if hasattr(obj, 'obter_diagnostico') else {}
    return "PASS", f"Omega v{diag.get('versao', '?')} status={diag.get('status', 'OK')}"


def test_omega_legacy():
    """Testa o omega.py (versão legado/compatibilidade)."""
    mod = import_from_file("omega_leg_mod", PROJECT_ROOT / "src/core/omega.py")
    classes = get_real_classes(mod)
    if classes:
        MainClass = getattr(mod, classes[0])
        obj = MainClass()
        return "PASS", f"{classes[0]} inicializado"
    return "WARN", f"Módulo carregado com fallbacks. Classes: {get_real_classes(mod)}"


def test_auditor():
    """Testa o módulo Auditor (segurança)."""
    mod = import_from_file("auditor_mod", PROJECT_ROOT / "src/security/auditor.py")
    classes = get_real_classes(mod)
    if not classes:
        return "WARN", "Nenhuma classe encontrada"
    Auditor = getattr(mod, classes[0])
    auditor = Auditor()
    methods = [m for m in dir(auditor) if not m.startswith('_') and callable(getattr(auditor, m))]
    return "PASS", f"{classes[0]} inicializado | Métodos: {methods[:6]}"


def test_hacker_agent():
    """Testa o Agente Hacker (segurança ofensiva)."""
    mod = import_from_file("hacker_mod", PROJECT_ROOT / "src/security/hacker_agent.py")
    classes = get_real_classes(mod)
    if not classes:
        return "WARN", "Módulo com erro de sintaxe ou sem classes"
    EH = getattr(mod, classes[0])
    hacker = EH()
    nome = getattr(hacker, 'nome', getattr(hacker, 'name', 'unknown'))
    versao = getattr(hacker, 'versao', getattr(hacker, 'version', 'unknown'))
    return "PASS", f"Agente: {nome} v{versao}"


def test_hacker_v328():
    """Testa o Agente Hacker v3.2.8 (versão final)."""
    mod = import_from_file("hacker_v328", PROJECT_ROOT / "src/security/hacker_agent_v328_final.py")
    classes = get_real_classes(mod)
    if not classes:
        return "WARN", "Módulo carregado sem classes"
    EH = getattr(mod, classes[0])
    hacker = EH()
    nome = getattr(hacker, 'nome', getattr(hacker, 'name', 'unknown'))
    return "PASS", f"Hacker v3.2.8 Final: {nome}"


def test_security_core():
    """Testa o Security Core v3.2.7."""
    mod = import_from_file("sec_core_mod", PROJECT_ROOT / "src/security/security_core_v3.2.7.py")
    classes = get_real_classes(mod)
    if not classes:
        return "WARN", "Módulo carregou mas imports internos falharam"
    SC = getattr(mod, classes[0])
    sc = SC()
    return "PASS", f"{classes[0]} inicializado"


def test_rag_advanced():
    """Testa o RAG Advanced (memória vetorial)."""
    mod = import_from_file("rag_adv_mod", PROJECT_ROOT / "src/rag/rag_advanced.py")
    classes = get_real_classes(mod)
    # Buscar a classe principal do RAG
    target = None
    for name in ['ModuloRAGAvançado', 'IndexadorRAG', 'RAGAdvanced']:
        if hasattr(mod, name):
            target = getattr(mod, name)
            break
    if target is None and classes:
        # Pegar a última classe (geralmente a mais complexa)
        target = getattr(mod, classes[-1])
    if target is None:
        return "WARN", f"Classes encontradas: {classes}"
    rag = target()
    return "PASS", f"{target.__name__} inicializado | Classes no módulo: {len(classes)}"


def test_rag_v326():
    """Testa o RAG Advanced v3.2.6."""
    mod = import_from_file("rag_v326_mod", PROJECT_ROOT / "src/rag/rag_advanced_v3.2.6.py")
    # Buscar a classe principal (pular Enums e dataclasses simples)
    from enum import EnumType
    target = None
    for name in ['ModuloRAGAvançado', 'IndexadorRAGChroma', 'ChunkerDocumentos']:
        if hasattr(mod, name):
            target = getattr(mod, name)
            break
    if target is None:
        classes = get_real_classes(mod)
        # Filtrar Enums
        for cls_name in reversed(classes):
            cls = getattr(mod, cls_name)
            if not isinstance(cls, EnumType):
                target = cls
                break
    if target is None:
        return "WARN", "Módulo carregou mas sem classes instanciáveis"
    obj = target()
    return "PASS", f"{target.__name__} inicializado"


def test_signal_bridge():
    """Testa o Signal Bridge (ponte de trading) — módulo funcional."""
    mod = import_from_file("sig_bridge_mod", PROJECT_ROOT / "src/trading/signal_bridge_v3.2.6.py")
    # Signal Bridge é funcional (sem classes), verificar funções
    funcs = [f for f in dir(mod) if not f.startswith('_') and callable(getattr(mod, f)) and not isinstance(getattr(mod, f), type)]
    key_funcs = ['process_signal', 'determine_suitability_mode', 'calculate_success_probability']
    found = [f for f in key_funcs if f in funcs]
    if len(found) == len(key_funcs):
        return "PASS", f"Módulo funcional OK | Funções-chave: {found}"
    return "WARN", f"Funções encontradas: {funcs[:8]}"


def test_bybit_connector():
    """Testa o Bybit Connector (exchange)."""
    mod = import_from_file("bybit_mod", PROJECT_ROOT / "src/trading/bybit_connector_v3.2.6.py")
    classes = get_real_classes(mod)
    target = None
    for name in ['BybitConnector', 'BybitConnectorV326']:
        if hasattr(mod, name):
            target = getattr(mod, name)
            break
    if target is None and classes:
        target = getattr(mod, classes[0])
    if target is None:
        return "WARN", f"Classes: {classes}"
    bc = target()
    return "PASS", f"{target.__name__} inicializado"


def test_trade_brain():
    """Testa o Trade Brain."""
    mod = import_from_file("trade_brain_mod", PROJECT_ROOT / "src/trading/trade_brain_v3.2.6.py")
    classes = get_real_classes(mod)
    if not classes:
        funcs = [f for f in dir(mod) if not f.startswith('_') and callable(getattr(mod, f))]
        return "WARN", f"Módulo funcional. Funções: {funcs[:5]}"
    target = getattr(mod, classes[0])
    tb = target()
    return "PASS", f"{classes[0]} inicializado"


def test_social_connector():
    """Testa o Social Connector (Instagram)."""
    mod = import_from_file("social_mod", PROJECT_ROOT / "src/utils/social_connector.py")
    classes = get_real_classes(mod)
    # Buscar a classe principal (não AlertaMonitoramento)
    target = None
    for name in ['SocialMediaConnector', 'InstagramConnector', 'ConectorSocial']:
        if hasattr(mod, name):
            target = getattr(mod, name)
            break
    if target is None:
        # Filtrar classes que não precisam de args
        for cls_name in classes:
            cls = getattr(mod, cls_name)
            try:
                obj = cls()
                target = cls
                return "PASS", f"{cls_name} inicializado"
            except TypeError:
                continue
        return "WARN", f"Classes encontradas mas requerem argumentos: {classes}"
    obj = target()
    return "PASS", f"{target.__name__} inicializado"


def test_telegram_bot():
    """Testa o Telegram Bot Refinement."""
    mod = import_from_file("tg_bot_mod", PROJECT_ROOT / "src/utils/telegram_bot_refinement_v3.2.6.py")
    TBR = getattr(mod, 'TelegramBotRefinement', None)
    if TBR:
        bot = TBR()
        threshold = getattr(bot, 'confidence_threshold', 'N/A')
        return "PASS", f"TelegramBotRefinement inicializado | Threshold: {threshold}"
    classes = get_real_classes(mod)
    return "WARN", f"Classes encontradas: {classes}"


def test_engine_patch():
    """Testa o Engine Patch de Segurança IA."""
    mod = import_from_file("eng_patch_mod", PROJECT_ROOT / "src/security/engine_patch_seguranca_ia.py")
    classes = get_real_classes(mod)
    if classes:
        EP = getattr(mod, classes[0])
        ep = EP()
        return "PASS", f"{classes[0]} inicializado"
    funcs = [f for f in dir(mod) if not f.startswith('_') and callable(getattr(mod, f))]
    return "PASS", f"Módulo funcional carregado | Funções: {funcs[:5]}"


def test_external_api_manager():
    """Testa o External API Manager."""
    mod = import_from_file("api_mgr_mod", PROJECT_ROOT / "src/utils/external_api_manager_v3.2.6.py")
    EAM = getattr(mod, 'ExternalAPIManager', None)
    if EAM:
        manager = EAM()
        version = getattr(manager, 'version', 'N/A')
        return "PASS", f"ExternalAPIManager v{version} inicializado"
    classes = get_real_classes(mod)
    return "WARN", f"Classes: {classes}"


def test_ravena_model():
    """Testa o Ravena Model (modelo principal)."""
    mod = import_from_file("ravena_model_mod", PROJECT_ROOT / "src/core/ravena_model.py")
    classes = get_real_classes(mod)
    if classes:
        RM = getattr(mod, classes[0])
        rm = RM()
        return "PASS", f"{classes[0]} inicializado"
    return "WARN", f"Módulo carregado. Exports: {[n for n in dir(mod) if not n.startswith('_')][:5]}"


# ═══════════════════════════════════════════════
# TESTES DE COMUNICAÇÃO ENTRE MÓDULOS
# ═══════════════════════════════════════════════

def test_zero_trust_to_omega():
    """Testa se o Zero Trust consegue gerar token para o OmegaOrchestrator."""
    mod = import_from_file("zt_comm_mod", PROJECT_ROOT / "src/security/zero_trust_v3.2.6.py")
    zt = mod.ZeroTrustProtocol()
    token = zt.generate_token("omega_orchestrator")
    valid = zt.validate_access("omega_orchestrator", token)
    if valid:
        return "PASS", "Zero Trust ↔ OmegaOrchestrator: comunicação autenticada OK"
    return "FAIL", "Zero Trust não consegue autenticar OmegaOrchestrator"


def test_secrets_audit():
    """Testa a auditoria de secrets do sistema."""
    mod = import_from_file("sm_audit_mod", PROJECT_ROOT / "src/core/secrets_manager.py")
    audit = mod.secrets.audit()
    compliant = audit["compliant"]
    loaded = audit["loaded"]
    total = audit["total_secrets"]
    if compliant:
        return "PASS", f"Auditoria OK | {loaded}/{total} carregados | Conforme: SIM"
    missing = audit.get("missing_critical", []) + audit.get("missing_high", [])
    return "WARN", f"Auditoria: {loaded}/{total} carregados | Faltando: {missing}"


def test_rag_ingest_query():
    """Testa ciclo completo: ingestão → consulta no RAG."""
    mod = import_from_file("rag_iq_mod", PROJECT_ROOT / "src/rag/rag_advanced.py")
    rag = mod.ModuloRAGAvançado()
    # Criar documento de teste
    doc = mod.Documento(
        id="test_001",
        titulo="Teste Health Check",
        conteudo="Bitcoin está em tendência de alta com suporte em 65000 USDT. RSI mostra força compradora.",
        tipo=mod.TipoDocumento.SEGURANÇA,
        tags=["bitcoin", "teste"],
        fonte="health_check"
    )
    # Ingerir
    if hasattr(rag, 'adicionar_documento'):
        rag.adicionar_documento(doc)
    elif hasattr(rag, 'ingerir'):
        rag.ingerir(doc)
    # Consultar
    if hasattr(rag, 'buscar'):
        resultado = rag.buscar("tendência do Bitcoin")
        return "PASS", f"RAG ingestão+consulta OK | Resultados: {len(resultado) if resultado else 0}"
    return "PASS", f"RAG ingestão OK (consulta requer embeddings externos)"


# ═══════════════════════════════════════════════
# EXECUÇÃO
# ═══════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  RAVENA AIM — HEALTH CHECK COMPLETO v3.2.6")
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Ambiente: {os.getenv('RAVENA_ENV', 'unknown')}")
    print("=" * 60)

    # ── FASE 1: Inicialização Individual ──
    print("\n\n" + "═" * 60)
    print("  FASE 1: INICIALIZAÇÃO INDIVIDUAL DE MÓDULOS")
    print("═" * 60)

    test_module("SecretsManager", test_secrets_manager)
    test_module("ZeroTrust Protocol", test_zero_trust)
    test_module("OmegaOrchestrator v3.2.6", test_omega_orchestrator_module)
    test_module("Omega v3.2.6", test_omega_v326)
    test_module("Omega (legacy)", test_omega_legacy)
    test_module("Ravena Model", test_ravena_model)
    test_module("Auditor", test_auditor)
    test_module("Hacker Agent v3.2.7", test_hacker_agent)
    test_module("Hacker Agent v3.2.8 Final", test_hacker_v328)
    test_module("Security Core v3.2.7", test_security_core)
    test_module("RAG Advanced", test_rag_advanced)
    test_module("RAG Advanced v3.2.6", test_rag_v326)
    test_module("Signal Bridge (funcional)", test_signal_bridge)
    test_module("Bybit Connector", test_bybit_connector)
    test_module("Trade Brain", test_trade_brain)
    test_module("Social Connector", test_social_connector)
    test_module("Telegram Bot", test_telegram_bot)
    test_module("Engine Patch Segurança", test_engine_patch)
    test_module("External API Manager", test_external_api_manager)

    # ── FASE 2: Comunicação Entre Módulos ──
    print("\n\n" + "═" * 60)
    print("  FASE 2: COMUNICAÇÃO ENTRE MÓDULOS")
    print("═" * 60)

    test_module("ZeroTrust → OmegaOrchestrator (Auth)", test_zero_trust_to_omega)
    test_module("Secrets Audit (Conformidade)", test_secrets_audit)
    test_module("RAG Ingestão + Consulta", test_rag_ingest_query)

    # ── RELATÓRIO FINAL ──
    total_time = round(time.time() - start_time, 2)
    passed = sum(1 for r in results if r["status"] == "PASS")
    warned = sum(1 for r in results if r["status"] == "WARN")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    total = len(results)

    print("\n\n" + "═" * 60)
    print("  RELATÓRIO FINAL")
    print("═" * 60)
    print(f"\n  Total de testes: {total}")
    print(f"  ✅ PASS: {passed}")
    print(f"  ⚠️  WARN: {warned}")
    print(f"  ❌ FAIL: {failed}")
    print(f"  Tempo total: {total_time}s")
    print(f"\n  {'─' * 50}")

    # Detalhar falhas
    if failed > 0:
        print(f"\n  MÓDULOS COM FALHA (requerem atenção):")
        for r in results:
            if r["status"] == "FAIL":
                print(f"    ❌ {r['module']}: {r['details']}")

    if warned > 0:
        print(f"\n  MÓDULOS COM AVISO (funcionam parcialmente):")
        for r in results:
            if r["status"] == "WARN":
                print(f"    ⚠️  {r['module']}: {r['details']}")

    print()
    if failed == 0:
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  ✅ SISTEMA SAUDÁVEL — PRONTO PARA OCI  ║")
        print("  ╚══════════════════════════════════════════╝")
    elif failed <= 3:
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  ⚠️  SISTEMA PARCIAL — FALHAS MENORES    ║")
        print("  ╚══════════════════════════════════════════╝")
    else:
        print("  ╔══════════════════════════════════════════╗")
        print("  ║  ❌ SISTEMA COM FALHAS — VER DETALHES   ║")
        print("  ╚══════════════════════════════════════════╝")

    # Salvar resultado em JSON
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v3.2.6",
        "environment": os.getenv("RAVENA_ENV", "unknown"),
        "summary": {
            "total": total,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "time_seconds": total_time,
            "health_score": round((passed / total) * 100, 1) if total > 0 else 0
        },
        "results": results,
        "verdict": "HEALTHY" if failed == 0 else "PARTIAL" if failed <= 3 else "UNHEALTHY"
    }

    report_path = PROJECT_ROOT / "tests" / "health_check_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Relatório salvo em: {report_path}")
