
import os
import json
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from collections import deque
import re
import chromadb
from chromadb.utils import embedding_functions

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
    GERAL = "geral"

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
# GERADOR DE EMBEDDINGS (REAL - via sentence-transformers)
# ============================================================

class GeradorEmbeddings:
    """Gera embeddings para chunks usando sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa o gerador.
        
        Args:
            model_name: Nome do modelo sentence-transformers a ser usado.
        """
        # Instalar sentence-transformers se não estiver instalado
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            print("Instalando sentence-transformers...")
            os.system("pip install sentence-transformers")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            print(f"Erro ao carregar modelo de embedding: {e}. Usando fallback de hash.")
            self.model = None

    def gerar(self, texto: str) -> List[float]:
        """Gera embedding para um texto."""
        if self.model:
            return self.model.encode(texto).tolist()
        else:
            # Fallback para hash se o modelo não carregar
            hash_obj = hashlib.sha256(texto.encode())
            hash_hex = hash_obj.hexdigest()
            embedding = []
            for i in range(384): # Dimensão padrão para all-MiniLM-L6-v2
                byte_val = int(hash_hex[i * 2 : i * 2 + 2], 16) if i * 2 < len(hash_hex) else 0
                embedding.append((byte_val - 128) / 128.0)
            return embedding

# ============================================================
# INDEXADOR RAG COM CHROMA DB
# ============================================================

class IndexadorRAGChroma:
    """Indexa e gerencia documentos para busca semântica usando ChromaDB."""

    def __init__(self, collection_name: str = "ravena_knowledge", path: str = "./chroma_db"):
        """
        Inicializa o indexador ChromaDB.
        
        Args:
            collection_name: Nome da coleção no ChromaDB.
            path: Caminho para o diretório de persistência do ChromaDB.
        """
        self.client = chromadb.PersistentClient(path=path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        self.chunker = ChunkerDocumentos()
        self.historico_buscas = deque(maxlen=1000)

    def adicionar_documento(self, documento: Documento) -> List[Chunk]:
        """Adiciona um documento à base de conhecimento ChromaDB."""
        chunks = self.chunker.fragmentar(documento)
        
        documents = [chunk.conteudo for chunk in chunks]
        metadatas = [
            {
                "documento_id": chunk.documento_id,
                "titulo": documento.titulo,
                "tipo": documento.tipo.value,
                "tags": json.dumps(documento.tags),
                "fonte": documento.fonte,
                "numero_chunk": chunk.numero,
                "timestamp": chunk.timestamp
            }
            for chunk in chunks
        ]
        ids = [chunk.id for chunk in chunks]

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return chunks

    def buscar_contexto(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Interface simplificada para busca de contexto compatível com o OmegaOrchestrator."""
        resultados = self.buscar(query, top_k=top_k)
        return [{"id": r.chunk.id, "conteudo": r.chunk.conteudo, "metadados": asdict(r.documento)} for r in resultados]

    def buscar(self, query: str, top_k: int = 5, tipo_filtro: Optional[TipoDocumento] = None) -> List[ResultadoBusca]:
        """Realiza busca semântica na base de conhecimento ChromaDB."""
        query_results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={
                "tipo": tipo_filtro.value
            } if tipo_filtro else None
        )

        resultados = []
        if query_results and query_results["documents"]:
            for i in range(len(query_results["documents"][0])):
                doc_content = query_results["documents"][0][i]
                metadata = query_results["metadatas"][0][i]
                distance = query_results["distances"][0][i]

                doc_id = metadata["documento_id"]
                # Reconstruir Documento e Chunk (simplificado para este exemplo)
                # Em um sistema real, você buscaria o documento completo por ID
                documento = Documento(
                    id=doc_id,
                    titulo=metadata["titulo"],
                    conteudo="", # Conteúdo completo não armazenado no metadata do chunk
                    tipo=TipoDocumento(metadata["tipo"]),
                    tags=json.loads(metadata["tags"]),
                    fonte=metadata["fonte"]
                )
                chunk = Chunk(
                    id=query_results["ids"][0][i],
                    documento_id=doc_id,
                    conteudo=doc_content,
                    numero=metadata["numero_chunk"]
                )
                
                # A relevância pode ser baseada na distância do embedding (menor distância = maior relevância)
                # Ou combinar com keyword matching como no script original
                relevancia = 1.0 - (distance / (distance + 1.0)) # Exemplo simples de normalização

                resultado = ResultadoBusca(
                    documento=documento,
                    chunk=chunk,
                    relevancia=relevancia,
                    motivo=f"Similaridade ChromaDB: {relevancia:.2f}",
                )
                resultados.append(resultado)

        # Registrar busca
        self.historico_buscas.append({
            "query": query,
            "resultados": len(resultados),
            "timestamp": datetime.now().isoformat(),
        })

        return resultados

    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas da base de conhecimento ChromaDB."""
        return {
            "total_documentos_indexados": self.collection.count(),
            "buscas_realizadas": len(self.historico_buscas),
            "timestamp": datetime.now().isoformat(),
        }

# ============================================================
# MÓDULO RAG AVANÇADO (Integrado com ChromaDB)
# ============================================================

class ModuloRAGAvançado:
    """Módulo RAG principal que integra indexação, busca e contexto com ChromaDB."""

    def __init__(self):
        """Inicializa o módulo RAG."""
        self.indexador = IndexadorRAGChroma()
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
    print("=== Adição de Documentos ===")
    stats = rag.adicionar_base_conhecimento(docs)
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
