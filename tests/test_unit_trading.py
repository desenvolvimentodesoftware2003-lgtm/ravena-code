"""
RAVENA AIM v3.2.6 — Testes Unitários: Trading
==============================================
Cobre BybitConnector, RiskManager, SignalBridge.
"""

import sys
import importlib.util
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def _import_mod(name, rel_path):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def test_bybit_connector():
    mod = _import_mod("bybit_test", "src/trading/bybit_connector_v3.2.6.py")
    target = getattr(mod, "BybitConnector", None)
    assert target is not None, "BybitConnector class not found"
    instance = target()
    assert instance is not None
    print(f"[PASS] BybitConnector inicializado")

def test_risk_manager():
    mod = _import_mod("risk_test", "src/trading/risk_manager_v3.2.6.py")
    target = getattr(mod, "RiskManager", None)
    assert target is not None, "RiskManager class not found"
    instance = target()
    assert instance is not None
    print(f"[PASS] RiskManager inicializado")

def test_signal_bridge():
    mod = _import_mod("signal_test", "src/trading/signal_bridge_v3.2.6.py")
    funcs = ["process_signal", "determine_suitability_mode", "calculate_success_probability"]
    for f in funcs:
        assert hasattr(mod, f), f"Function {f} not found in signal_bridge"
    print(f"[PASS] SignalBridge functions: {funcs}")

def test_sentiment_analyzer():
    mod = _import_mod("sentiment_test", "src/trading/sentiment_analyzer_v3.2.6.py")
    classes = [c for c in dir(mod) if not c.startswith("_") and isinstance(getattr(mod, c), type)]
    assert len(classes) > 0, f"No classes found in sentiment_analyzer"
    print(f"[PASS] SentimentAnalyzer classes: {classes}")

if __name__ == "__main__":
    test_bybit_connector()
    test_risk_manager()
    test_signal_bridge()
    test_sentiment_analyzer()
    print("\nAll trading unit tests passed")
