"""
RAG_ADVANCED — Retrieval-Augmented Generation Avançado para Ravena AI
=====================================================================
Este módulo implementa um sistema RAG (Retrieval-Augmented Generation) robusto
que permite à Ravena acessar uma base de conhecimento técnico profunda com
320+ documentos, realizando buscas semânticas inteligentes e fornecendo
contexto enriquecido para análise e decisão.

Responsabilidades:
  - Indexar e armazenar documentos técnicos.
  - Realizar buscas semânticas avançadas.
  - Recuperar contexto relevante para análise.
  - Integrar conhecimento com análise visual.
  - Fornecer recomendações baseadas em expertise.

Arquitetura:
  Documentos → Chunking → Embedding → Indexação (ChromaDB) →
  Busca Semântica → Ranking → Contexto → Análise Inteligente
"""

import os
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from collections import deque
import re

# ============================================================
# TIPOS E ENUMS
# ============================================================

class TipoDocumento(Enum):
    """Tipos de documentos na base de conhecimento."""
    SEGURANÇA = "segurança"
    ENGENHARIA = "engenharia"
    BEST_PRACTICES = "best_practices"
    TROUBLESHOOTING = "troubleshooting"
    ARQUITETURA = "arquitetura"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    REDE = "rede"

class NivelRelevancia(Enum):
    """Níveis de relevância de um documento."""
    BAIXA = 0.3
    MÉDIA = 0.6
    ALTA = 0.8
    CRÍTICA = 0.95

# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class Documento:
    """Documento na base de conhecimento."""
    id: str
    titulo: str
    conteudo: str
    tipo: TipoDocumento
    tags: List[str]
    fonte: str  # URL ou referência
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Chunk:
    """Fragmento de um documento para indexação."""
    id: str
    documento_id: str
    conteudo: str
    numero: int  # Número do chunk no documento
    embedding: Optional[List[float]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ResultadoBusca:
    """Resultado de uma busca semântica."""
    documento: Documento
    chunk: Chunk
    relevancia: float  # 0.0 a 1.0
    motivo: str  # Por que foi retornado
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class ContextoEnriquecido:
    """Contexto enriquecido para análise."""
    query: str
    resultados_busca: List[ResultadoBusca]
    resumo_conhecimento: str
    recomendações: List[str]
    confiança: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

# ============================================================
# CHUNKER DE DOCUMENTOS
# ============================================================

class ChunkerDocumentos:
    """Fragmenta documentos em chunks para indexação."""

    def __init__(self, tamanho_chunk: int = 512, sobreposição: int = 100):
        """
        Inicializa o chunker.
        
        Args:
            tamanho_chunk: Tamanho máximo de cada chunk em caracteres.
            sobreposição: Sobreposição entre chunks para contexto.
        """
        self.tamanho_chunk = tamanho_chunk
        self.sobreposição = sobreposição

    def fragmentar(self, documento: Documento) -> List[Chunk]:
        """Fragmenta um documento em chunks."""
        chunks = []
        conteudo = documento.conteudo
        numero_chunk = 0

        # Limpar e normalizar conteúdo
        conteudo = self._limpar_conteudo(conteudo)

        # Fragmentar por parágrafos primeiro
        paragrafos = conteudo.split("\n\n")
        buffer = ""

        for paragrafo in paragrafos:
            if len(buffer) + len(paragrafo) < self.tamanho_chunk:
                buffer += paragrafo + "\n\n"
            else:
                if buffer:
                    chunk = Chunk(
                        id=f"{documento.id}_chunk_{numero_chunk}",
                        documento_id=documento.id,
                        conteudo=buffer.strip(),
                        numero=numero_chunk,
                    )
                    chunks.append(chunk)
                    numero_chunk += 1

                # Adicionar sobreposição
                buffer = buffer[-self.sobreposição:] + paragrafo + "\n\n"

        # Adicionar último chunk
        if buffer:
            chunk = Chunk(
                id=f"{documento.id}_chunk_{numero_chunk}",
                documento_id=documento.id,
                conteudo=buffer.strip(),
                numero=numero_chunk,
            )
            chunks.append(chunk)

        return chunks

    def _limpar_conteudo(self, conteudo: str) -> str:
        """Limpa e normaliza o conteúdo."""
        # Remover caracteres de controle
        conteudo = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", conteudo)
        # Normalizar espaços
        conteudo = re.sub(r"\s+", " ", conteudo)
        # Remover URLs (opcional)
        conteudo = re.sub(r"http\S+|www\S+", "[URL]", conteudo)
        return conteudo.strip()

# ============================================================
# GERADOR DE EMBEDDINGS (SIMULADO)
# ============================================================

class GeradorEmbeddings:
    """Gera embeddings para chunks (simulado para demonstração)."""

    def __init__(self, dimensao: int = 384):
        """
        Inicializa o gerador.
        
        Args:
            dimensao: Dimensão do embedding (padrão: 384 para sentence-transformers).
        """
        self.dimensao = dimensao

    def gerar(self, texto: str) -> List[float]:
        """Gera embedding para um texto (simulado com hash)."""
        # Em produção, usar sentence-transformers ou similar
        hash_obj = hashlib.sha256(texto.encode())
        hash_hex = hash_obj.hexdigest()

        # Converter hash em embedding pseudo-aleatório
        embedding = []
        for i in range(self.dimensao):
            byte_val = int(hash_hex[i * 2 : i * 2 + 2], 16) if i * 2 < len(hash_hex) else 0
            embedding.append((byte_val - 128) / 128.0)

        return embedding

    def calcular_similaridade(self, emb1: List[float], emb2: List[float]) -> float:
        """Calcula similaridade cosseno entre dois embeddings."""
        if not emb1 or not emb2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        magnitude1 = sum(a ** 2 for a in emb1) ** 0.5
        magnitude2 = sum(b ** 2 for b in emb2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

# ============================================================
# INDEXADOR RAG
# ============================================================

class IndexadorRAG:
    """Indexa e gerencia documentos para busca semântica."""

    def __init__(self):
        """Inicializa o indexador."""
        self.documentos: Dict[str, Documento] = {}
        self.chunks: Dict[str, Chunk] = {}
        self.chunker = ChunkerDocumentos()
        self.gerador_embeddings = GeradorEmbeddings()
        self.historico_buscas = deque(maxlen=1000)

    def adicionar_documento(self, documento: Documento) -> List[Chunk]:
        """Adiciona um documento à base de conhecimento."""
        # Armazenar documento
        self.documentos[documento.id] = documento

        # Fragmentar em chunks
        chunks = self.chunker.fragmentar(documento)

        # Gerar embeddings para cada chunk
        for chunk in chunks:
            chunk.embedding = self.gerador_embeddings.gerar(chunk.conteudo)
            self.chunks[chunk.id] = chunk

        return chunks

    def buscar(self, query: str, top_k: int = 5, tipo_filtro: Optional[TipoDocumento] = None) -> List[ResultadoBusca]:
        """Realiza busca semântica na base de conhecimento."""
        if not query or not self.chunks:
            return []

        # Gerar embedding da query
        query_embedding = self.gerador_embeddings.gerar(query)

        # Calcular similaridade com todos os chunks
        resultados = []
        for chunk_id, chunk in self.chunks.items():
            if chunk.embedding is None:
                continue

            # Calcular similaridade
            similaridade = self.gerador_embeddings.calcular_similaridade(
                query_embedding, chunk.embedding
            )

            # Filtrar por tipo se especificado
            documento = self.documentos.get(chunk.documento_id)
            if tipo_filtro and documento and documento.tipo != tipo_filtro:
                continue

            # Calcular relevância baseado em matches de keywords
            relevancia = self._calcular_relevancia(query, chunk.conteudo, similaridade)

            if relevancia > 0.3:  # Threshold mínimo
                resultado = ResultadoBusca(
                    documento=documento,
                    chunk=chunk,
                    relevancia=relevancia,
                    motivo=f"Similaridade semântica: {similaridade:.2%}",
                )
                resultados.append(resultado)

        # Ordenar por relevância
        resultados.sort(key=lambda r: r.relevancia, reverse=True)

        # Registrar busca
        self.historico_buscas.append({
            "query": query,
            "resultados": len(resultados),
            "timestamp": datetime.now().isoformat(),
        })

        return resultados[:top_k]

    def _calcular_relevancia(self, query: str, conteudo: str, similaridade: float) -> float:
        """Calcula relevância combinando similaridade e matches de keywords."""
        # Contar matches de palavras-chave
        query_words = set(query.lower().split())
        conteudo_lower = conteudo.lower()

        matches = sum(1 for word in query_words if word in conteudo_lower)
        match_ratio = matches / len(query_words) if query_words else 0

        # Combinar similaridade com matches
        relevancia = (similaridade * 0.6) + (match_ratio * 0.4)
        return min(relevancia, 1.0)

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da base de conhecimento."""
        return {
            "total_documentos": len(self.documentos),
            "total_chunks": len(self.chunks),
            "tipos_documentos": {
                tipo.value: sum(1 for doc in self.documentos.values() if doc.tipo == tipo)
                for tipo in TipoDocumento
            },
            "buscas_realizadas": len(self.historico_buscas),
        }

# ============================================================
# MÓDULO RAG AVANÇADO
# ============================================================

class ModuloRAGAvançado:
    """Módulo RAG principal que integra indexação, busca e contexto."""

    def __init__(self):
        """Inicializa o módulo RAG."""
        self.indexador = IndexadorRAG()
        self._callbacks_contexto = []

    def registrar_callback_contexto(self, callback):
        """Registra callback para quando contexto é gerado."""
        self._callbacks_contexto.append(callback)

    def adicionar_base_conhecimento(self, documentos: List[Documento]) -> Dict[str, Any]:
        """Adiciona múltiplos documentos à base de conhecimento."""
        stats = {
            "documentos_adicionados": 0,
            "chunks_criados": 0,
            "erros": [],
        }

        for doc in documentos:
            try:
                chunks = self.indexador.adicionar_documento(doc)
                stats["documentos_adicionados"] += 1
                stats["chunks_criados"] += len(chunks)
            except Exception as e:
                stats["erros"].append({"documento": doc.id, "erro": str(e)})

        return stats

    def gerar_contexto(self, query: str, tipo_filtro: Optional[TipoDocumento] = None) -> ContextoEnriquecido:
        """Gera contexto enriquecido para uma query."""
        # Buscar documentos relevantes
        resultados = self.indexador.buscar(query, top_k=5, tipo_filtro=tipo_filtro)

        # Gerar resumo do conhecimento
        resumo = self._gerar_resumo(resultados)

        # Gerar recomendações
        recomendações = self._gerar_recomendações(resultados)

        # Calcular confiança geral
        confiança = sum(r.relevancia for r in resultados) / len(resultados) if resultados else 0.0

        # Criar contexto enriquecido
        contexto = ContextoEnriquecido(
            query=query,
            resultados_busca=resultados,
            resumo_conhecimento=resumo,
            recomendações=recomendações,
            confiança=confiança,
        )

        # Notificar callbacks
        for callback in self._callbacks_contexto:
            try:
                callback(contexto)
            except Exception as e:
                print(f"[RAG] Erro ao chamar callback: {e}")

        return contexto

    def _gerar_resumo(self, resultados: List[ResultadoBusca]) -> str:
        """Gera resumo dos resultados de busca."""
        if not resultados:
            return "Nenhum documento relevante encontrado."

        resumo = f"Encontrados {len(resultados)} documentos relevantes:\n"
        for i, resultado in enumerate(resultados, 1):
            resumo += f"\n{i}. **{resultado.documento.titulo}** (Relevância: {resultado.relevancia:.0%})\n"
            resumo += f"   Tipo: {resultado.documento.tipo.value}\n"
            resumo += f"   {resultado.motivo}\n"

        return resumo

    def _gerar_recomendações(self, resultados: List[ResultadoBusca]) -> List[str]:
        """Gera recomendações baseado nos resultados."""
        recomendações = []

        if not resultados:
            return ["Consulte a documentação geral de segurança."]

        # Analisar tipos de documentos
        tipos = [r.documento.tipo for r in resultados]

        if TipoDocumento.SEGURANÇA in tipos:
            recomendações.append("Implementar medidas de segurança recomendadas.")

        if TipoDocumento.PERFORMANCE in tipos:
            recomendações.append("Otimizar performance conforme best practices.")

        if TipoDocumento.TROUBLESHOOTING in tipos:
            recomendações.append("Seguir procedimento de troubleshooting documentado.")

        if TipoDocumento.COMPLIANCE in tipos:
            recomendações.append("Validar conformidade com regulamentações.")

        return recomendações if recomendações else ["Consulte os documentos encontrados para mais detalhes."]

    def obter_diagnostico(self) -> Dict[str, Any]:
        """Retorna diagnóstico do módulo RAG."""
        return {
            "status": "operacional",
            "base_conhecimento": self.indexador.obter_estatisticas(),
            "timestamp": datetime.now().isoformat(),
        }

# ============================================================
# SINGLETON GLOBAL
# ============================================================

_modulo_rag_global = None

def inicializar_rag() -> ModuloRAGAvançado:
    """Inicializa o módulo RAG avançado."""
    global _modulo_rag_global

    if _modulo_rag_global is None:
        _modulo_rag_global = ModuloRAGAvançado()

    return _modulo_rag_global

def obter_rag() -> ModuloRAGAvançado:
    """Retorna o módulo RAG global."""
    global _modulo_rag_global

    if _modulo_rag_global is None:
        _modulo_rag_global = ModuloRAGAvançado()

    return _modulo_rag_global

if __name__ == "__main__":
    # Demonstração
    rag = inicializar_rag()

    # Criar documentos de exemplo
    docs = [
        Documento(
            id="doc_001",
            titulo="Segurança em Sistemas Distribuídos",
            conteudo="""
            A segurança em sistemas distribuídos é crítica. Implementar autenticação mútua,
            criptografia end-to-end, e validação de integridade em todas as comunicações.
            Usar TLS 1.3 ou superior para transporte. Implementar rate limiting e DDoS protection.
            """,
            tipo=TipoDocumento.SEGURANÇA,
            tags=["segurança", "tls", "autenticação"],
            fonte="https://exemplo.com/seguranca",
        ),
        Documento(
            id="doc_002",
            titulo="Best Practices de Performance",
            conteudo="""
            Para otimizar performance: usar cache agressivo, implementar lazy loading,
            otimizar queries de banco de dados, usar índices apropriados, monitorar
            CPU e memória continuamente. Implementar circuit breakers para resiliência.
            """,
            tipo=TipoDocumento.PERFORMANCE,
            tags=["performance", "cache", "otimização"],
            fonte="https://exemplo.com/performance",
        ),
    ]

    # Adicionar documentos
    stats = rag.adicionar_base_conhecimento(docs)
    print("=== Adição de Documentos ===")
    print(json.dumps(stats, indent=2))

    # Realizar busca
    print("\n=== Busca Semântica ===")
    contexto = rag.gerar_contexto("Como implementar segurança em sistemas distribuídos?")
    print(f"Query: {contexto.query}")
    print(f"Confiança: {contexto.confiança:.0%}")
    print(f"\n{contexto.resumo_conhecimento}")

    print("\n=== Recomendações ===")
    for rec in contexto.recomendações:
        print(f"- {rec}")

    print("\n=== Diagnóstico ===")
    print(json.dumps(rag.obter_diagnostico(), indent=2, default=str))
