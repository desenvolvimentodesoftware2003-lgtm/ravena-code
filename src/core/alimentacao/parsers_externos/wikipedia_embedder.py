import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger("ravena.alimentacao.wikipedia_embedder")

MODELO_PADRAO = "paraphrase-multilingual-MiniLM-L12-v2"
COLECAO_PADRAO = "wikipedia_pt"
CAMINHO_CHROMA = "./chroma_db"


class WikipediaEmbedder:
    def __init__(self, modelo: str = MODELO_PADRAO, colecao: str = COLECAO_PADRAO):
        self._modelo_nome = modelo
        self._colecao_nome = colecao
        self._modelo = None
        self._client = None
        self._collection = None

    @property
    def modelo(self):
        if self._modelo is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Carregando modelo: {self._modelo_nome}")
            self._modelo = SentenceTransformer(self._modelo_nome)
        return self._modelo

    @property
    def client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings
            path = os.path.abspath(CAMINHO_CHROMA)
            logger.info(f"Conectando ChromaDB: {path}")
            self._client = chromadb.PersistentClient(
                path=path,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    @property
    def collection(self):
        if self._collection is None:
            import chromadb.utils.embedding_functions as ef
            fn = ef.SentenceTransformerEmbeddingFunction(model_name=self._modelo_nome)
            self._collection = self.client.get_or_create_collection(
                name=self._colecao_nome,
                embedding_function=fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Colecao '{self._colecao_nome}': {self._collection.count()} documentos")
        return self._collection

    def _hash_conteudo(self, texto: str) -> str:
        return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]

    def _ids_existentes(self) -> set:
        try:
            dados = self.collection.get(include=[])
            return set(dados["ids"]) if dados and dados.get("ids") else set()
        except Exception:
            return set()

    def indexar_jsonl(self, caminho_jsonl: str, lote: int = 64) -> Dict[str, int]:
        if not os.path.exists(caminho_jsonl):
            logger.warning(f"Arquivo nao encontrado: {caminho_jsonl}")
            return {"lidos": 0, "inseridos": 0, "ignorados": 0}

        logger.info(f"Indexando: {caminho_jsonl}")
        existentes = self._ids_existentes()
        registros = []
        with open(caminho_jsonl, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    registros.append(json.loads(linha))
                except json.JSONDecodeError:
                    continue

        lidos = len(registros)
        inseridos = 0
        ignorados = 0
        buffer = []
        vistos = set()

        for i, reg in enumerate(registros):
            texto = reg.get("conteudo", reg.get("texto", ""))
            if not texto:
                ignorados += 1
                continue
            doc_id = self._hash_conteudo(texto)
            if doc_id in existentes or doc_id in vistos:
                ignorados += 1
                continue
            vistos.add(doc_id)
            meta = reg.get("metadata", reg.get("meta", {}))
            metadados = {
                "titulo": str(meta.get("titulo", "")),
                "secao": str(meta.get("secao", "")),
                "parte": str(meta.get("parte", 1)),
                "pergunta": str(reg.get("pergunta", reg.get("input", ""))),
                "categorias": ",".join(meta.get("categorias", [])[:5]),
                "fonte": str(reg.get("fonte", "wikipedia_dump")),
            }
            buffer.append({"id": doc_id, "metadata": metadados, "document": texto})
            if len(buffer) >= lote:
                inseridos += self._inserir_lote(buffer)
                buffer = []

        if buffer:
            inseridos += self._inserir_lote(buffer)

        logger.info(f"Indexado: {lidos} lidos, {inseridos} inseridos, {ignorados} ignorados")
        return {"lidos": lidos, "inseridos": inseridos, "ignorados": ignorados}

    def _inserir_lote(self, buffer: List[Dict]) -> int:
        textos = [b["document"] for b in buffer]
        logger.info(f"Gerando embeddings para lote de {len(textos)} documentos...")
        embeddings = self.modelo.encode(textos, show_progress_bar=False).tolist()
        self.collection.add(
            ids=[b["id"] for b in buffer],
            embeddings=embeddings,
            metadatas=[b["metadata"] for b in buffer],
            documents=textos,
        )
        logger.info(f"Lote inserido: {len(buffer)} documentos")
        return len(buffer)

    def indexar_todos(self, diretorio: str) -> Dict[str, int]:
        totais = {"lidos": 0, "inseridos": 0, "ignorados": 0}
        for f in sorted(os.listdir(diretorio)):
            if f.endswith(".jsonl") and f != "manifest.json":
                caminho = os.path.join(diretorio, f)
                resultado = self.indexar_jsonl(caminho)
                for k in totais:
                    totais[k] += resultado[k]
        logger.info(f"Indexacao total: {totais}")
        return totais

    def buscar(self, consulta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Buscando: '{consulta}' (top_k={top_k})")
        resultados = self.collection.query(
            query_texts=[consulta],
            n_results=top_k,
        )
        items = []
        if resultados and resultados.get("ids"):
            for i in range(len(resultados["ids"][0])):
                items.append({
                    "id": resultados["ids"][0][i],
                    "documento": resultados["documents"][0][i] if resultados.get("documents") else "",
                    "distancia": resultados["distances"][0][i] if resultados.get("distances") else 0.0,
                    "metadata": resultados["metadatas"][0][i] if resultados.get("metadatas") else {},
                })
        return items

    def status(self) -> Dict[str, Any]:
        try:
            col = self.collection
            total = col.count()
            amostras = col.get(limit=3, include=["metadatas"])
            categorias_vistas = set()
            titulos_vistos = set()
            for m in amostras.get("metadatas", []):
                if m:
                    cats = m.get("categorias", "")
                    if cats:
                        for c in cats.split(","):
                            if c.strip():
                                categorias_vistas.add(c.strip())
                    titulo = m.get("titulo", "")
                    if titulo:
                        titulos_vistos.add(titulo)
            return {
                "colecao": self._colecao_nome,
                "modelo": self._modelo_nome,
                "total_documentos": total,
                "topicos_unicos": len(titulos_vistos),
                "categorias_unicas": len(categorias_vistas),
            }
        except Exception as e:
            return {"erro": str(e)}

    def limpar(self):
        try:
            self.client.delete_collection(self._colecao_nome)
            self._collection = None
            logger.info(f"Colecao '{self._colecao_nome}' deletada")
        except Exception as e:
            logger.warning(f"Erro ao limpar colecao: {e}")
