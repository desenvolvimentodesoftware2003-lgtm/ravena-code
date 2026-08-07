import os
import re
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    _SKLEARN_DISPONIVEL = True
except ImportError:
    _SKLEARN_DISPONIVEL = False

logger = logging.getLogger("ravena.alimentacao.estrategica")

@dataclass
class ClusterInfo:
    centro_id: int
    palavras_chave: List[str]
    tamanho: int
    representante_texto: str

class Estrategica:
    def __init__(self, n_clusters: int = 20, similaridade_max: float = 0.8):
        self._n_clusters = n_clusters
        self._similaridade_max = similaridade_max

    def clusterizar(self, textos: List[str]) -> List[ClusterInfo]:
        if not _SKLEARN_DISPONIVEL:
            logger.warning("scikit-learn nao instalado. Use: pip install scikit-learn")
            return self._fallback_sem_ml(textos)

        if len(textos) < self._n_clusters:
            logger.warning(f"Poucos textos ({len(textos)}) para {self._n_clusters} clusters")
            self._n_clusters = max(2, len(textos) // 2)

        try:
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words=None,
                min_df=1,
                max_df=0.9
            )
            tfidf = vectorizer.fit_transform(textos)
            feature_names = vectorizer.get_feature_names_out()
        except Exception as e:
            logger.warning(f"Erro no TF-IDF: {e}, usando fallback")
            return self._fallback_sem_ml(textos)

        if tfidf.shape[0] < 2:
            return [ClusterInfo(
                centro_id=0,
                palavras_chave=list(feature_names[:10]),
                tamanho=1,
                representante_texto=textos[0][:500]
            )]

        try:
            kmeans = KMeans(
                n_clusters=min(self._n_clusters, tfidf.shape[0]),
                random_state=42,
                n_init="auto"
            )
            rotulos = kmeans.fit_predict(tfidf)
        except Exception as e:
            logger.warning(f"Erro no KMeans: {e}, usando fallback")
            return self._fallback_sem_ml(textos)

        clusters: Dict[int, List[int]] = {}
        for i, rotulo in enumerate(rotulos):
            clusters.setdefault(int(rotulo), []).append(i)

        resultado = []
        for rotulo, indices in clusters.items():
            centro = kmeans.cluster_centers_[rotulo]
            top_indices = centro.argsort()[-10:][::-1]
            palavras_chave = [feature_names[i] for i in top_indices if i < len(feature_names)]

            rep_idx = indices[0]
            resultado.append(ClusterInfo(
                centro_id=int(rotulo),
                palavras_chave=palavras_chave,
                tamanho=len(indices),
                representante_texto=textos[rep_idx][:500]
            ))

        resultado.sort(key=lambda c: c.tamanho, reverse=True)
        return resultado

    def _fallback_sem_ml(self, textos: List[str]) -> List[ClusterInfo]:
        logger.info("Usando fallback: amostragem simples (sem ML)")
        step = max(1, len(textos) // self._n_clusters)
        resultado = []
        for i in range(0, len(textos), step):
            texto = textos[i]
            palavras = set(re.findall(r'\w+', texto.lower()))
            palavras_ordenadas = sorted(palavras, key=lambda p: len(p), reverse=True)
            resultado.append(ClusterInfo(
                centro_id=i // step,
                palavras_chave=palavras_ordenadas[:10],
                tamanho=1,
                representante_texto=texto[:500]
            ))
        return resultado

    def selecionar_representantes(self, textos: List[str]) -> List[tuple]:
        clusters = self.clusterizar(textos)
        representantes = []
        for c in clusters:
            idx = c.centro_id
            if idx < len(textos):
                pergunta = f"topicos sobre {', '.join(c.palavras_chave[:5])}"
                representantes.append((pergunta, c.representante_texto))
        return representantes

    def verificar_similaridade(self, texto_novo: str, textos_existentes: List[str]) -> float:
        if not _SKLEARN_DISPONIVEL or not textos_existentes:
            return 0.0
        todos = textos_existentes + [texto_novo]
        try:
            vectorizer = TfidfVectorizer(max_features=500, min_df=1)
            tfidf = vectorizer.fit_transform(todos)
            from sklearn.metrics.pairwise import cosine_similarity
            similaridades = cosine_similarity(tfidf[-1:], tfidf[:-1])[0]
            return float(max(similaridades)) if len(similaridades) > 0 else 0.0
        except Exception as e:
            logger.warning(f"Erro ao verificar similaridade: {e}")
            return 0.0

    def filtrar_por_similaridade(self, novos_textos: List[str],
                                  existentes: List[str]) -> List[str]:
        if not _SKLEARN_DISPONIVEL or not existentes:
            return novos_textos
        filtrados = []
        for texto in novos_textos:
            sim = self.verificar_similaridade(texto, existentes)
            if sim < self._similaridade_max:
                filtrados.append(texto)
            else:
                logger.debug(f"Texto similar demais ({sim:.2f}), pulando")
        return filtrados
