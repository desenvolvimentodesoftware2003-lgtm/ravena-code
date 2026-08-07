"""RAG (Retrieval-Augmented Generation): busca semântica, indexacao ChromaDB e visao.

Nota: classes em `*_v3.2.6.py` nao sao importaveis diretamente via `__init__.py`
devido ao ponto no nome do arquivo. Use importlib ou acesse pelo caminho absoluto.
Classes em `vision_module.py` contem caracteres acentuados no nome,
acessiveis via getattr ou importlib.

Disponibiliza:
- VisionRAGSemantic: fusao cognitiva entre percepcao visual e conhecimento RAG
"""

from .vision_rag_semantic_v3_2_6 import VisionRAGSemantic

__all__ = [
    "VisionRAGSemantic",
]
