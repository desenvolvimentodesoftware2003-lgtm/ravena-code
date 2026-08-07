import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

logger = logging.getLogger("ravena.ml_pipeline")

@dataclass
class RelatorioSaude:
    total_interacoes: int = 0
    confianca_media: float = 0.0
    fontes: Dict[str, int] = field(default_factory=dict)
    estados_crenca: Dict[str, int] = field(default_factory=dict)
    autoridade_media_por_fonte: Dict[str, float] = field(default_factory=dict)
    autoridade_trend: float = 0.0
    clusters_perguntas: List[Dict[str, Any]] = field(default_factory=list)
    sugestoes: List[str] = field(default_factory=list)
    timestamp: str = ""

class MLPipeline:
    def __init__(self):
        self._projeto_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logger.info("MLPipeline ativo")

    def carregar(self, caminho_jsonl: str) -> pd.DataFrame:
        caminho = caminho_jsonl if os.path.isabs(caminho_jsonl) else os.path.join(self._projeto_raiz, caminho_jsonl)
        if not os.path.exists(caminho):
            logger.warning(f"Arquivo nao encontrado: {caminho}")
            return pd.DataFrame()
        registros = []
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                try:
                    registros.append(json.loads(linha))
                except json.JSONDecodeError:
                    continue
        df = pd.DataFrame(registros)
        logger.info(f"Carregados {len(df)} registros de {caminho}")
        return df

    def analisar(self, df: pd.DataFrame) -> RelatorioSaude:
        relatorio = RelatorioSaude()
        relatorio.timestamp = datetime.now().isoformat()

        if df.empty:
            relatorio.sugestoes.append("Nenhum dado para analisar. Execute algumas missoes primeiro.")
            return relatorio

        relatorio.total_interacoes = len(df)

        if "confianca" in df.columns:
            relatorio.confianca_media = round(float(df["confianca"].mean()), 4)

        if "fonte" in df.columns:
            relatorio.fontes = df["fonte"].value_counts().to_dict()

        if "estado_crenca" in df.columns:
            relatorio.estados_crenca = df["estado_crenca"].value_counts().to_dict()

        if "fonte" in df.columns and "authority_score" in df.columns:
            relatorio.autoridade_media_por_fonte = df.groupby("fonte")["authority_score"].mean().round(4).to_dict()

        if "authority_score" in df.columns and len(df) > 1:
            valores = df["authority_score"].values
            relatorio.autoridade_trend = round(float(valores[-1] - valores[0]), 4)

        if len(df) >= 5 and "pergunta" in df.columns:
            perguntas = df["pergunta"].dropna().tolist()
            if len(set(perguntas)) >= 5:
                try:
                    vectorizer = TfidfVectorizer(max_features=100, stop_words=None)
                    X = vectorizer.fit_transform(perguntas)
                    n_clusters = min(5, len(set(perguntas)))
                    if n_clusters >= 2 and X.shape[0] >= n_clusters:
                        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
                        labels = kmeans.fit_predict(X)
                        nomes_features = vectorizer.get_feature_names_out()
                        for i in range(n_clusters):
                            indices = np.where(labels == i)[0]
                            perguntas_cluster = [perguntas[j] for j in indices[:3]]
                            centro = kmeans.cluster_centers_[i]
                            top_idx = np.argsort(centro)[-5:]
                            palavras_chave = [nomes_features[idx] for idx in top_idx if idx < len(nomes_features)]
                            relatorio.clusters_perguntas.append({
                                "cluster": i,
                                "tamanho": int(len(indices)),
                                "exemplos": perguntas_cluster,
                                "palavras_chave": palavras_chave
                            })
                except Exception as e:
                    logger.warning(f"Erro no cluster: {e}")

        if relatorio.confianca_media < 0.5 and relatorio.total_interacoes > 0:
            relatorio.sugestoes.append("Confianca media baixa. Considere revisar as fontes de conhecimento.")

        if relatorio.estados_crenca.get("contestado", 0) > 2:
            relatorio.sugestoes.append(f"{relatorio.estados_crenca['contestado']} itens contestados. Priorizar resolucao.")

        if relatorio.autoridade_trend < -0.1:
            relatorio.sugestoes.append("Queda na autoridade media. Verificar qualidade das fontes.")

        if relatorio.autoridade_trend > 0.1:
            relatorio.sugestoes.append("Autoridade em alta. Bom sinal de aprendizado.")

        return relatorio

    def exportar_para_treino(self, caminho_jsonl: str, caminho_saida: Optional[str] = None) -> str:
        df = self.carregar(caminho_jsonl)
        if df.empty:
            return ""
        caminho_saida = caminho_saida or caminho_jsonl.replace(".jsonl", "_ml_treino.csv")
        cols_padrao = ["instruction", "reasoning", "response", "confidence", "source", "belief_state", "authority"]
        mapeamento = {
            "instruction": "pergunta",
            "reasoning": "raciocinio",
            "response": "resposta",
            "confidence": "confianca",
            "source": "fonte",
            "belief_state": "estado_crenca",
            "authority": "authority_score"
        }
        df_out = pd.DataFrame()
        for col_saida, col_origem in mapeamento.items():
            if col_origem in df.columns:
                df_out[col_saida] = df[col_origem]
        df_out.to_csv(caminho_saida, index=False, encoding="utf-8")
        logger.info(f"Exportado {len(df_out)} registros para {caminho_saida}")
        return caminho_saida


if __name__ == "__main__":
    import tempfile, uuid

    ml = MLPipeline()
    dados_teste = [
        {"pergunta": "qual e a capital do brasil", "raciocinio": "Brasilia", "resposta": "Brasilia",
         "confianca": 0.95, "fonte": "usuario", "estado_crenca": "ativo", "authority_score": 0.9},
        {"pergunta": "o que e python", "raciocinio": "linguagem interpretada", "resposta": "Python e linguagem",
         "confianca": 0.7, "fonte": "aprendizado", "estado_crenca": "ativo", "authority_score": 0.7},
        {"pergunta": "qual e a capital da franca", "raciocinio": "Paris", "resposta": "Paris",
         "confianca": 0.9, "fonte": "usuario", "estado_crenca": "ativo", "authority_score": 0.9},
        {"pergunta": "quem descobriu o brasil", "raciocinio": "1500", "resposta": "Cabral",
         "confianca": 0.4, "fonte": "documento", "estado_crenca": "contestado", "authority_score": 0.5},
        {"pergunta": "o que e fotossintese", "raciocinio": "energia luminosa", "resposta": "processo bioquimico",
         "confianca": 0.6, "fonte": "aprendizado", "estado_crenca": "resolvido", "authority_score": 0.65}
    ]

    caminho_temp = os.path.join(tempfile.gettempdir(), f"teste_ml_{uuid.uuid4().hex[:8]}.jsonl")
    with open(caminho_temp, "w", encoding="utf-8") as f:
        for d in dados_teste:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    df = ml.carregar(caminho_temp)
    print(f"DataFrame: {len(df)} linhas x {len(df.columns)} colunas")
    print(f"Colunas: {list(df.columns)}")
    print()

    rel = ml.analisar(df)
    print("=== RELATORIO DE SAUDE ===")
    print(f"  Interacoes: {rel.total_interacoes}")
    print(f"  Confianca media: {rel.confianca_media}")
    print(f"  Fontes: {rel.fontes}")
    print(f"  Estados: {rel.estados_crenca}")
    print(f"  Authority trend: {rel.autoridade_trend}")
    print(f"  Sugestoes: {rel.sugestoes}")
    print(f"  Clusters: {len(rel.clusters_perguntas)}")

    csv_path = ml.exportar_para_treino(caminho_temp)
    print(f"\nExportado para: {csv_path}")

    os.remove(caminho_temp)
