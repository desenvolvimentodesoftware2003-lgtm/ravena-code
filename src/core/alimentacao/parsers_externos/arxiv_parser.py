import re
import time
import logging
from typing import List, Optional
from dataclasses import dataclass

try:
    import arxiv
    _ARXIV_DISPONIVEL = True
except ImportError:
    _ARXIV_DISPONIVEL = False

logger = logging.getLogger("ravena.alimentacao.arxiv")

@dataclass
class ItemArxiv:
    titulo: str
    resumo: str
    autores: List[str]
    ano: str
    url: str
    categorias: List[str]

class ArxivParser:
    def __init__(self):
        if not _ARXIV_DISPONIVEL:
            logger.warning("biblioteca 'arxiv' nao instalada. pip install arxiv")
        self._client = arxiv.Client(page_size=10, delay_seconds=3, num_retries=3) if _ARXIV_DISPONIVEL else None

    def buscar(self, query: str, max_resultados: int = 10) -> List[ItemArxiv]:
        if not self._client:
            return []
        try:
            search = arxiv.Search(query=query, max_results=max_resultados, sort_by=arxiv.SortCriterion.Relevance)
            itens = []
            for resultado in self._client.results(search):
                item = ItemArxiv(
                    titulo=resultado.title,
                    resumo=resultado.summary,
                    autores=[a.name for a in resultado.authors[:5]],
                    ano=str(resultado.published.year),
                    url=resultado.entry_id,
                    categorias=resultado.categories[:5]
                )
                itens.append(item)
            logger.info("arXiv '%s': %d resultados" % (query[:50], len(itens)))
            return itens
        except Exception as e:
            logger.warning("Erro arXiv busca '%s': %s" % (query[:30], e))
            return []

    def gerar_item_pith(self, item: ItemArxiv) -> tuple:
        autor_str = ", ".join(item.autores[:3])
        pergunta = "resumo de %s" % item.titulo.lower().rstrip(".")
        resumo_limpo = re.sub(r'\s+', ' ', item.resumo).strip()
        if len(resumo_limpo) > 2000:
            resumo_limpo = resumo_limpo[:2000] + "..."
        conteudo = "Titulo: %s\nAutores: %s\nAno: %s\nResumo: %s" % (
            item.titulo, autor_str, item.ano, resumo_limpo
        )
        metadados = {
            "fonte": "arxiv",
            "autores": item.autores[:5],
            "ano": item.ano,
            "url": item.url,
            "categorias": item.categorias
        }
        return pergunta, conteudo, metadados

    def ingerir_por_keywords(self, keywords: List[str], alimentador,
                              itens_por_kw: int = 5) -> int:
        total = 0
        for kw in keywords:
            itens = self.buscar(kw, max_resultados=itens_por_kw)
            for item in itens:
                pergunta, conteudo, metadados = self.gerar_item_pith(item)
                if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                    try:
                        alimentador._ensinado_fn(
                            pergunta=pergunta,
                            conteudo=conteudo,
                            fonte="arxiv",
                            metadata=metadados
                        )
                        total += 1
                    except Exception as e:
                        logger.warning("Erro ao ingerir arXiv: %s" % e)
                time.sleep(0.5)
        logger.info("arXiv ingestao: %d itens de %d keywords" % (total, len(keywords)))
        return total
