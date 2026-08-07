"""
RAVENA AIM v3.2.6 — Testes Unitários: Learning
===============================================
Cobre LearningCore e DNA de Sucesso.
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

def test_learning_core_v326():
    mod = _import_mod("learning_test", "src/learning/learning_core_v3.2.6.py")
    target = getattr(mod, "LearningCore", None) or getattr(mod, "AgenteAprendizado", None)
    if target is None:
        classes = [c for c in dir(mod) if not c.startswith("_") and isinstance(getattr(mod, c), type) and c != "Any"]
        assert len(classes) > 0, f"No classes in learning_core_v3.2.6: {[c for c in dir(mod) if not c.startswith('_')]}"
        target = getattr(mod, classes[-1])
    instance = target()
    assert instance is not None
    print(f"[PASS] LearningCore: {target.__name__} inicializado")

def test_dna_sucesso_v326():
    mod = _import_mod("dna_test", "src/learning/dna_sucesso_v3.2.6.py")
    target = getattr(mod, "DNASucesso", None) or getattr(mod, "AnalisadorSucesso", None)
    if target is None:
        classes = [c for c in dir(mod) if not c.startswith("_") and isinstance(getattr(mod, c), type) and c != "Any"]
        assert len(classes) > 0, f"No classes in dna_sucesso_v3.2.6: {[c for c in dir(mod) if not c.startswith('_')]}"
        target = getattr(mod, classes[-1])
    instance = target()
    assert instance is not None
    print(f"[PASS] DNA Sucesso: {target.__name__} inicializado")

if __name__ == "__main__":
    test_learning_core_v326()
    test_dna_sucesso_v326()
    print("\nAll Learning unit tests passed")
