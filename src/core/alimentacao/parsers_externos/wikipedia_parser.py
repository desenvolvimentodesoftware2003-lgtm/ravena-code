import logging
import re
import time
from dataclasses import dataclass
from typing import Any

_USER_AGENT = "RavenaAI/4.0 (https://github.com/ravena-aim; wiki-ingestion@ravena.ai)"

try:
    import wikipedia

    wikipedia.set_user_agent(_USER_AGENT)
    wikipedia.set_lang("pt")
    _WIKIPEDIA_DISPONIVEL = True
except ImportError:
    _WIKIPEDIA_DISPONIVEL = False

logger = logging.getLogger("ravena.alimentacao.wikipedia")


@dataclass
class ItemWikipedia:
    titulo: str
    resumo: str
    url: str
    categorias: list[str]
    palavras_chave: list[str]


class WikipediaParser:
    def __init__(self, lingua: str = "pt", timeout: int = 10):
        self._lingua = lingua
        self._timeout = timeout
        if _WIKIPEDIA_DISPONIVEL:
            wikipedia.set_user_agent(_USER_AGENT)
            wikipedia.set_lang(lingua)
        else:
            logger.warning("Biblioteca 'wikipedia' nao instalada. pip install wikipedia")

    def buscar_topico(self, titulo: str) -> ItemWikipedia | None:
        if not _WIKIPEDIA_DISPONIVEL:
            logger.error("wikipedia nao instalado")
            return None
        try:
            pagina = wikipedia.page(titulo, auto_suggest=True)
            if not pagina or not pagina.summary:
                logger.warning(f"Pagina vazia ou sem sumario: {titulo}")
                return None
            palavras = set(re.findall(r"\w+", pagina.summary.lower()))
            palavras_filtradas = [p for p in sorted(palavras, key=len, reverse=True) if len(p) > 3][:10]
            item = ItemWikipedia(
                titulo=pagina.title,
                resumo=pagina.summary,
                url=pagina.url,
                categorias=list(pagina.categories[:10]) if hasattr(pagina, "categories") else [],
                palavras_chave=palavras_filtradas,
            )
            logger.info(f"Wikipedia OK: '{item.titulo}' ({len(item.resumo)} chars)")
            return item
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"Ambigua: '{titulo}' -> opcoes: {e.options[:5]}")
            return None
        except wikipedia.exceptions.PageError:
            logger.warning(f"Pagina nao encontrada: '{titulo}'")
            return None
        except Exception as e:
            logger.warning(f"Erro ao buscar '{titulo}': {e}")
            return None

    def buscar_por_palavra_chave(self, keyword: str, limite: int = 10) -> list[ItemWikipedia]:
        if not _WIKIPEDIA_DISPONIVEL:
            return []
        try:
            resultados = wikipedia.search(keyword, results=limite)
        except Exception as e:
            logger.warning(f"Erro na busca por '{keyword}': {e}")
            return []
        itens = []
        for titulo in resultados:
            item = self.buscar_topico(titulo)
            if item:
                itens.append(item)
            time.sleep(0.3)
        logger.info(f"Wikipedia busca '{keyword}': {len(itens)}/{len(resultados)} itens")
        return itens

    def gerar_itens_para_pith(self, item: ItemWikipedia) -> tuple:
        pergunta = f"o que e {item.titulo.lower()}?"
        limite = 1500
        if len(item.resumo) > limite:
            paragrafos = item.resumo.split("\n")
            conteudo = ""
            for p in paragrafos:
                if len(conteudo) + len(p) > limite:
                    break
                conteudo += p + "\n"
            conteudo = conteudo.strip()
        else:
            conteudo = item.resumo
        metadados = {
            "fonte": "wikipedia",
            "url": item.url,
            "categorias": item.categorias[:5],
            "palavras_chave": item.palavras_chave[:8],
        }
        return pergunta, conteudo, metadados

    def ingerir_topicos(self, topicos: list[str], alimentador: Any) -> int:
        total = 0
        for topico in topicos:
            item = self.buscar_topico(topico)
            if not item:
                continue
            pergunta, conteudo, metadados = self.gerar_itens_para_pith(item)
            if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                try:
                    alimentador._ensinado_fn(
                        pergunta=pergunta, conteudo=conteudo, fonte="wikipedia", metadata=metadados
                    )
                    total += 1
                    logger.info(f"Ingerido: '{pergunta[:50]}'")
                except Exception as e:
                    logger.warning(f"Erro ao ingerir '{pergunta[:30]}': {e}")
            time.sleep(0.5)
        return total

    def ingerir_por_keywords(self, keywords: list[str], alimentador: Any, itens_por_keyword: int = 8) -> int:
        total = 0
        for kw in keywords:
            itens = self.buscar_por_palavra_chave(kw, limite=itens_por_keyword)
            for item in itens:
                pergunta, conteudo, metadados = self.gerar_itens_para_pith(item)
                if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                    try:
                        alimentador._ensinado_fn(
                            pergunta=pergunta, conteudo=conteudo, fonte="wikipedia", metadata=metadados
                        )
                        total += 1
                    except Exception as e:
                        logger.warning(f"Erro ao ingerir: {e}")
                time.sleep(0.3)
            time.sleep(1.0)
        logger.info(f"Wikipedia ingestao por keywords: {total} itens")
        return total
