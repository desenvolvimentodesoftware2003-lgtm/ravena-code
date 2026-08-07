"""
RAVENA AIM v3.2.6 — Testes Unitários: RAG
==========================================
Cobre RAGCore, VisionRAGSemantic, módulos de visão.
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

def test_rag_advanced():
    mod = _import_mod("rag_adv_test", "src/rag/rag_advanced.py")
    target = getattr(mod, "ModuloRAGAvançado", None)
    assert target is not None, "ModuloRAGAvançado not found"
    instance = target()
    assert instance is not None
    print(f"[PASS] ModuloRAGAvançado inicializado")

def test_rag_advanced_v326():
    mod = _import_mod("rag_v326_test", "src/rag/rag_advanced_v3.2.6.py")
    classes = [c for c in dir(mod) if not c.startswith("_") and isinstance(getattr(mod, c), type)]
    assert len(classes) > 0, f"No classes in rag_advanced_v3.2.6"
    print(f"[PASS] RAG v3.2.6 classes: {len(classes)}")

def test_vision_rag_semantic():
    mod = _import_mod("vrs_test", "src/rag/vision_rag_semantic_v3_2_6.py")
    target = getattr(mod, "VisionRAGSemantic", None)
    assert target is not None, "VisionRAGSemantic not found"
    padrao = getattr(mod, "PadraoDetectado", None)
    assert padrao is not None, "PadraoDetectado not found"
    dec = getattr(mod, "DecisaoAutonoma", None)
    assert dec is not None, "DecisaoAutonoma not found"
    print(f"[PASS] VisionRAGSemantic + PadraoDetectado + DecisaoAutonoma")

def test_rag_core_v326():
    mod = _import_mod("rag_core_test", "src/rag/rag_core_v3.2.6.py")
    classes = [c for c in dir(mod) if not c.startswith("_") and isinstance(getattr(mod, c), type)]
    assert len(classes) > 0, f"No classes in rag_core_v3.2.6"
    print(f"[PASS] RAG Core v3.2.6 classes: {classes}")

if __name__ == "__main__":
    test_rag_advanced()
    test_rag_advanced_v326()
    test_vision_rag_semantic()
    test_rag_core_v326()
    print("\nAll RAG unit tests passed")
