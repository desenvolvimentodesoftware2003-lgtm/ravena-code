"""
VECTOR_STORE — Gerenciamento Programatico do ChromaDB (v3.2.6)
===============================================================
Ravena AIM | Modulo: persistencia vetorial
Responsabilidades:
  - Gerenciar colecoes ChromaDB (criar, listar, deletar)
  - Operacoes em lote (add, delete, search)
  - Health check e estatisticas do banco vetorial
  - Interface unificada para os modulos RAG
"""

import os
import logging
import time
from typing import List, Dict, Optional, Any

logger = logging.getLogger("ravena.vector_store")

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    logger.warning("chromadb nao instalado. pip install chromadb")


class VectorStoreManager:
    """Gerenciador programatico do ChromaDB."""

    def __init__(self, path: str = "./chroma_db", default_collection: str = "ravena_knowledge"):
        self.path = os.path.abspath(path)
        self.default_collection_name = default_collection
        self._client = None
        self._collections: Dict[str, Any] = {}
        logger.info(f"VectorStoreManager: path={self.path}")

    @property
    def client(self):
        if self._client is None:
            if chromadb is None:
                raise RuntimeError("chromadb nao instalado")
            self._client = chromadb.PersistentClient(
                path=self.path,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def listar_colecoes(self) -> List[str]:
        return [c.name for c in self.client.list_collections()]

    def criar_colecao(self, nome: str, metadata: Optional[Dict] = None):
        if nome not in self.listar_colecoes():
            self.client.create_collection(name=nome, metadata=metadata)
            logger.info(f"Colecao criada: {nome}")

    def deletar_colecao(self, nome: str):
        if nome in self.listar_colecoes():
            self.client.delete_collection(nome)
            logger.info(f"Colecao deletada: {nome}")

    def _colecao(self, nome: Optional[str] = None):
        nome = nome or self.default_collection_name
        if nome not in self._collections:
            self._collections[nome] = self.client.get_or_create_collection(name=nome)
        return self._collections[nome]

    def adicionar(self, textos: List[str], metadados: Optional[List[Dict]] = None, ids: Optional[List[str]] = None, colecao: Optional[str] = None):
        col = self._colecao(colecao)
        import uuid
        ids_gerados = ids or [str(uuid.uuid4()) for _ in textos]
        col.add(documents=textos, metadatas=metadados, ids=ids_gerados)
        return ids_gerados

    def buscar(self, query: str, k: int = 5, colecao: Optional[str] = None) -> List[Dict[str, Any]]:
        col = self._colecao(colecao)
        resultados = col.query(query_texts=[query], n_results=k)
        items = []
        if resultados and resultados.get("ids"):
            for i, doc_id in enumerate(resultados["ids"][0]):
                items.append({
                    "id": doc_id,
                    "documento": resultados["documents"][0][i] if resultados.get("documents") else "",
                    "metadata": resultados["metadatas"][0][i] if resultados.get("metadatas") else {},
                    "distancia": resultados["distances"][0][i] if resultados.get("distances") else 0.0,
                })
        return items

    def deletar(self, ids: List[str], colecao: Optional[str] = None):
        col = self._colecao(colecao)
        col.delete(ids=ids)

    def contar(self, colecao: Optional[str] = None) -> int:
        col = self._colecao(colecao)
        return col.count()

    def health_check(self) -> Dict[str, Any]:
        try:
            colecoes = self.listar_colecoes()
            stats = {}
            for c in colecoes:
                col = self._colecao(c)
                stats[c] = col.count()
            return {
                "status": "healthy",
                "path": self.path,
                "colecoes": len(colecoes),
                "stats": stats,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"status": "unhealthy", "erro": str(e), "timestamp": time.time()}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vs = VectorStoreManager()
    print("Colecoes:", vs.listar_colecoes())
    print("Health:", vs.health_check())
