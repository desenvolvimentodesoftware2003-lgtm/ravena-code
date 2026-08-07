"""
RAVENA AI 3.0.0 — src/rag/rag_core.py
====================================
Módulo RAG (Retrieval-Augmented Generation) Refatorado.
Integra busca semântica avançada, ChromaDB Real e sentence-transformers.
"""

import os
import re
import json
import uuid
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field

# Dependências Reais
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Configuração de Logging
logger = logging.getLogger("ravena.rag_core")

class TipoDocumento(Enum):
    SEGURANCA = "seguranca"
    ENGENHARIA = "engenharia"
    ARQUITETURA = "arquitetura"
    CONHECIMENTO_GERAL = "geral"

@dataclass
class Documento:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    titulo: str = "Sem Título"
    conteudo: str = ""
    categoria: str = "geral"
    tags: List[str] = field(default_factory=list)
    fonte: str = "manual"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

class EmbeddingGenerator:
    """Wrapper sobre SentenceTransformer para geração de vetores."""
    _instancia = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if EmbeddingGenerator._instancia is None:
            logger.info(f"Carregando modelo de embeddings: {model_name}")
            EmbeddingGenerator._instancia = SentenceTransformer(model_name)
        self.modelo = EmbeddingGenerator._instancia

    def gerar(self, textos: List[str]) -> List[List[float]]:
        return self.modelo.encode(textos, convert_to_numpy=True).tolist()

class VectorStoreManager:
    """Gerencia a persistência no ChromaDB Real."""
    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "ravena_knowledge"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Conectado ao ChromaDB em {db_path}, Coleção: {collection_name}")

    def adicionar(self, ids: List[str], documentos: List[str], metadados: List[Dict[str, Any]], embeddings: List[List[float]]):
        self.collection.add(
            ids=ids,
            documents=documentos,
            metadatas=metadados,
            embeddings=embeddings
        )
        logger.info(f"Adicionados {len(ids)} itens ao VectorStore.")

    def buscar(self, query_embedding: List[float], top_k: int = 5) -> Dict[str, Any]:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

class RAGCore:
    """Núcleo RAG da Ravena AI 3.0.0 com ChromaDB e Embeddings Reais."""
    def __init__(self):
        self.embeddings = EmbeddingGenerator()
        self.store = VectorStoreManager()

    def indexar_documento(self, doc: Documento):
        # Lógica simplificada de chunking (pode ser expandida conforme necessário)
        chunks = [doc.conteudo[i:i+512] for i in range(0, len(doc.conteudo), 448)]
        ids = [f"{doc.id}_ch_{i}" for i in range(len(chunks))]
        metadatas = [{
            "doc_id": doc.id,
            "titulo": doc.titulo,
            "categoria": doc.categoria,
            "fonte": doc.fonte,
            "tags": ",".join(doc.tags)
        } for _ in chunks]
        
        # Gerar embeddings reais
        embeddings_list = self.embeddings.gerar(chunks)
        
        # Salvar no ChromaDB
        self.store.adicionar(ids, chunks, metadatas, embeddings_list)
        return len(chunks)

    def buscar_contexto(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_emb = self.embeddings.gerar([query])[0]
        results = self.store.buscar(query_emb, top_k)
        
        contexto = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                contexto.append({
                    "id": results['ids'][0][i],
                    "conteudo": results['documents'][0][i],
                    "metadados": results['metadatas'][0][i],
                    "distancia": results['distances'][0][i] if 'distances' in results else None
                })
        return contexto
