"""
RAVENA AIM — E2E Integrity Validator v3.2.6
===========================================
Valida a integridade do pipeline E2E: módulos, testes, relatórios e configurações.
"""

import importlib.util
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

results = []
start_time = time.time()

def check(label, ok, detail=""):
    elapsed = round(time.time() - start_time, 3)
    status = "PASS" if ok else "FAIL"
    icon = "✅" if ok else "❌"
    print(f"  {icon} {label}: {status} | {detail}")
    results.append({"check": label, "status": status, "detail": detail, "time_ms": int(elapsed * 1000)})

def import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

print("=" * 60)
print("  RAVENA AIM — E2E INTEGRITY VALIDATOR v3.2.6")
print(f"  Started: {datetime.now().isoformat()}")
print("=" * 60)

print("\n--- Phase 1: Directory Structure ---")
dirs = [
    "src/core", "src/security", "src/trading", "src/rag",
    "src/learning", "src/orchestration", "src/simulation",
    "src/utils", "tests", ".github/workflows"
]
for d in dirs:
    check(f"Directory {d}", (PROJECT_ROOT / d).exists())

print("\n--- Phase 2: Critical Modules ---")
modules = [
    ("Omega v3.2.6", "src/core/omega_v3.2.6.py", "Omega"),
    ("Omega Orchestrator v3.2.6", "src/core/omega_orchestrator_v3.2.6.py"),
    ("Hacker Agent", "src/security/hacker_agent.py", "HackerAgent"),
    ("Security Core v3.2.7", "src/security/security_core_v3.2.7.py", "SecurityCore"),
    ("Zero Trust v3.2.6", "src/security/zero_trust_v3.2.6.py", "ZeroTrustProtocol"),
    ("Secrets Manager", "src/core/secrets_manager.py"),
    ("RAG Advanced", "src/rag/rag_advanced.py"),
    ("Bybit Connector", "src/trading/bybit_connector_v3.2.6.py"),
    ("Signal Bridge", "src/trading/signal_bridge_v3.2.6.py"),
    ("Trade Brain", "src/trading/trade_brain_v3.2.6.py"),
    ("Agente Dev", "src/orchestration/agente_dev_v3.2.6.py", "AgenteDev"),
    ("External API Manager", "src/utils/external_api_manager_v3.2.6.py"),
    ("Telegram Bot", "src/utils/telegram_bot_refinement_v3.2.6.py"),
]
for name, rel_path, *class_names in modules:
    fp = PROJECT_ROOT / rel_path
    if not fp.exists():
        check(f"Module {name}", False, f"File not found: {rel_path}")
        continue
    try:
        mod = import_from_file(f"val_{name.lower().replace(' ', '_')}", fp)
        if class_names:
            found = all(hasattr(mod, cn) for cn in class_names)
            check(f"Module {name}", found, f"Classes: {class_names}")
        else:
            check(f"Module {name}", True, "Loaded successfully")
    except Exception as e:
        check(f"Module {name}", False, str(e))

print("\n--- Phase 3: Test Scripts ---")
tests = [
    "tests/health_check.py",
    "tests/test_elite_v327.py",
    "tests/test_token_protection.py",
    "tests/test_integration_v3.2.6.py",
    "tests/stress_test_v328.py",
    "tests/global_validation_test_v3.2.6.py",
]
for t in tests:
    fp = PROJECT_ROOT / t
    check(f"Test {t}", fp.exists(), f"Size: {fp.stat().st_size if fp.exists() else 0} bytes")

print("\n--- Phase 4: Reports ---")
reports = [
    "tests/health_check_report.json",
    "tests/health_check_report.md",
    "tests/health_check_report.html",
    "tests/stress_test_v3.2.8.log",
]
for r in reports:
    fp = PROJECT_ROOT / r
    exists = fp.exists()
    size = fp.stat().st_size if exists else 0
    check(f"Report {r}", exists, f"Size: {size} bytes")

print("\n--- Phase 5: CI/CD Config ---")
cicd = [".github/workflows/e2e-tests.yml"]
for c in cicd:
    fp = PROJECT_ROOT / c
    check(f"CI/CD {c}", fp.exists(), f"Size: {fp.stat().st_size if fp.exists() else 0} bytes")

print("\n--- Phase 6: JSON Report Integrity ---")
report_path = PROJECT_ROOT / "tests" / "health_check_report.json"
if report_path.exists():
    try:
        with open(report_path) as f:
            data = json.load(f)
        required_keys = ["timestamp", "version", "summary", "results", "verdict"]
        missing = [k for k in required_keys if k not in data]
        check("JSON Schema", not missing, f"Missing keys: {missing}" if missing else "All keys present")
        total = data["summary"]["total"]
        results_count = len(data["results"])
        check("JSON counts match", total == results_count, f"Summary total={total}, Results count={results_count}")
        score = data["summary"]["health_score"]
        check(f"Health score", score >= 90, f"Score: {score}%")
    except Exception as e:
        check("JSON Integrity", False, str(e))
else:
    check("JSON Report", False, "File not found")

total_time = round(time.time() - start_time, 2)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")

print(f"\n{'=' * 60}")
print(f"  VALIDATION COMPLETE")
print(f"  Total checks: {len(results)}")
print(f"  ✅ PASS: {passed}")
print(f"  ❌ FAIL: {failed}")
print(f"  Time: {total_time}s")

report = {
    "timestamp": datetime.now().isoformat(),
    "version": "3.2.6",
    "summary": {"total": len(results), "passed": passed, "failed": failed, "time_seconds": total_time},
    "results": results,
    "verdict": "PASS" if failed == 0 else "FAIL"
}

out_path = PROJECT_ROOT / "tests" / "e2e_integrity_report.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\n  Report saved: {out_path}")

if failed == 0:
    print("\n  ✅ E2E Integrity: ALL CHECKS PASSED")
else:
    print(f"\n  ⚠️  E2E Integrity: {failed} check(s) failed")

sys.exit(0 if failed == 0 else 1)
