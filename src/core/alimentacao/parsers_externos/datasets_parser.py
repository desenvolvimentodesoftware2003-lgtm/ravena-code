import re
import time
import logging
from typing import List, Optional, Iterator
from dataclasses import dataclass

try:
    from datasets import load_dataset, get_dataset_config_names
    _DATASETS_DISPONIVEL = True
except ImportError:
    _DATASETS_DISPONIVEL = False

logger = logging.getLogger("ravena.alimentacao.datasets")

@dataclass
class ItemDataset:
    texto: str
    fonte: str
    metadados: dict

class DatasetsParser:
    def __init__(self):
        if not _DATASETS_DISPONIVEL:
            logger.warning("biblioteca 'datasets' nao instalada. pip install datasets")
        self._estrategica = None

    def _get_estrategica(self):
        if self._estrategica is None:
            from src.core.alimentacao.estrategica import Estrategica
            self._estrategica = Estrategica(n_clusters=20)
        return self._estrategica

    def amostrar_fineweb(self, amostra: int = 500, split: str = "train") -> List[ItemDataset]:
        if not _DATASETS_DISPONIVEL:
            return []
        try:
            logger.info("Carregando FineWeb (amostra=%d)..." % amostra)
            dataset = load_dataset("HuggingFaceFW/fineweb", split=split, streaming=True)
            itens = []
            for i, exemplo in enumerate(dataset):
                if i >= amostra:
                    break
                texto = exemplo.get("text", "")
                if texto and len(texto) > 100:
                    itens.append(ItemDataset(
                        texto=texto[:5000],
                        fonte="fineweb",
                        metadados={"id": exemplo.get("id", i), "url": exemplo.get("url", "")}
                    ))
                if (i + 1) % 100 == 0:
                    logger.info("  FineWeb: %d/%d carregados..." % (i + 1, amostra))
            logger.info("FineWeb: %d itens carregados" % len(itens))
            return itens
        except Exception as e:
            logger.warning("Erro ao carregar FineWeb: %s" % e)
            return []

    def amostrar_redpajama(self, amostra: int = 500) -> List[ItemDataset]:
        if not _DATASETS_DISPONIVEL:
            return []
        try:
            logger.info("Carregando RedPajama (amostra=%d)..." % amostra)
            dataset = load_dataset("togethercomputer/RedPajama-Data-1T-Sample", split="train", streaming=True)
            itens = []
            for i, exemplo in enumerate(dataset):
                if i >= amostra:
                    break
                texto = exemplo.get("text", "")
                if texto and len(texto) > 100:
                    itens.append(ItemDataset(
                        texto=texto[:5000],
                        fonte="redpajama",
                        metadados={"id": exemplo.get("meta", {}).get("url", i)}
                    ))
                if (i + 1) % 100 == 0:
                    logger.info("  RedPajama: %d/%d..." % (i + 1, amostra))
            logger.info("RedPajama: %d itens" % len(itens))
            return itens
        except Exception as e:
            logger.warning("Erro RedPajama: %s" % e)
            return []

    def clusterizar_e_ingerir(self, itens: List[ItemDataset], alimentador,
                               prefixo: str = "topicos") -> int:
        if not itens:
            return 0
        textos = [i.texto for i in itens if i.texto]
        if not textos:
            return 0

        estrategica = self._get_estrategica()
        clusters = estrategica.clusterizar(textos)
        logger.info("Clusterizacao: %d clusters de %d itens" % (len(clusters), len(textos)))
        total = 0
        for i, cluster in enumerate(clusters):
            pergunta = "%s: %s" % (prefixo, ", ".join(cluster.palavras_chave[:5]))
            conteudo = cluster.representante_texto
            if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                try:
                    alimentador._ensinado_fn(
                        pergunta=pergunta,
                        conteudo=conteudo,
                        fonte="dataset:%s" % (itens[0].fonte if itens else "desconhecido"),
                        metadata={
                            "tipo": "cluster",
                            "cluster_id": cluster.centro_id,
                            "tamanho_cluster": cluster.tamanho,
                            "palavras_chave": cluster.palavras_chave[:10],
                            "prefixo": prefixo
                        }
                    )
                    total += 1
                except Exception as e:
                    logger.warning("Erro ao ingerir cluster: %s" % e)
        return total

    def ingerir_fineweb(self, alimentador, amostra: int = 500,
                         prefixo: str = "topicos conhecimento") -> int:
        itens = self.amostrar_fineweb(amostra)
        return self.clusterizar_e_ingerir(itens, alimentador, prefixo)

    def ingerir_redpajama(self, alimentador, amostra: int = 500,
                           prefixo: str = "topicos redpajama") -> int:
        itens = self.amostrar_redpajama(amostra)
        return self.clusterizar_e_ingerir(itens, alimentador, prefixo)
