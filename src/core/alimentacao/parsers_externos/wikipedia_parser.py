import os
import re
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

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
    categorias: List[str]
    palavras_chave: List[str]

class WikipediaParser:
    def __init__(self, lingua: str = "pt", timeout: int = 10):
        self._lingua = lingua
        self._timeout = timeout
        if _WIKIPEDIA_DISPONIVEL:
            wikipedia.set_user_agent(_USER_AGENT)
            wikipedia.set_lang(lingua)
        else:
            logger.warning("Biblioteca 'wikipedia' nao instalada. pip install wikipedia")

    def buscar_topico(self, titulo: str) -> Optional[ItemWikipedia]:
        if not _WIKIPEDIA_DISPONIVEL:
            logger.error("wikipedia nao instalado")
            return None
        try:
            pagina = wikipedia.page(titulo, auto_suggest=True)
            if not pagina or not pagina.summary:
                logger.warning("Pagina vazia ou sem sumario: %s" % titulo)
                return None
            palavras = set(re.findall(r'\w+', pagina.summary.lower()))
            palavras_filtradas = [p for p in sorted(palavras, key=len, reverse=True) if len(p) > 3][:10]
            item = ItemWikipedia(
                titulo=pagina.title,
                resumo=pagina.summary,
                url=pagina.url,
                categorias=list(pagina.categories[:10]) if hasattr(pagina, "categories") else [],
                palavras_chave=palavras_filtradas
            )
            logger.info("Wikipedia OK: '%s' (%d chars)" % (item.titulo, len(item.resumo)))
            return item
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning("Ambigua: '%s' -> opcoes: %s" % (titulo, e.options[:5]))
            return None
        except wikipedia.exceptions.PageError:
            logger.warning("Pagina nao encontrada: '%s'" % titulo)
            return None
        except Exception as e:
            logger.warning("Erro ao buscar '%s': %s" % (titulo, e))
            return None

    def buscar_por_palavra_chave(self, keyword: str, limite: int = 10) -> List[ItemWikipedia]:
        if not _WIKIPEDIA_DISPONIVEL:
            return []
        try:
            resultados = wikipedia.search(keyword, results=limite)
        except Exception as e:
            logger.warning("Erro na busca por '%s': %s" % (keyword, e))
            return []
        itens = []
        for titulo in resultados:
            item = self.buscar_topico(titulo)
            if item:
                itens.append(item)
            time.sleep(0.3)
        logger.info("Wikipedia busca '%s': %d/%d itens" % (keyword, len(itens), len(resultados)))
        return itens

    def gerar_itens_para_pith(self, item: ItemWikipedia) -> tuple:
        pergunta = "o que e %s?" % item.titulo.lower()
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
            "palavras_chave": item.palavras_chave[:8]
        }
        return pergunta, conteudo, metadados

    def ingerir_topicos(self, topicos: List[str], alimentador: Any) -> int:
        total = 0
        for topico in topicos:
            item = self.buscar_topico(topico)
            if not item:
                continue
            pergunta, conteudo, metadados = self.gerar_itens_para_pith(item)
            if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                try:
                    alimentador._ensinado_fn(
                        pergunta=pergunta,
                        conteudo=conteudo,
                        fonte="wikipedia",
                        metadata=metadados
                    )
                    total += 1
                    logger.info("Ingerido: '%s'" % pergunta[:50])
                except Exception as e:
                    logger.warning("Erro ao ingerir '%s': %s" % (pergunta[:30], e))
            time.sleep(0.5)
        return total

    def ingerir_por_keywords(self, keywords: List[str],
                              alimentador: Any,
                              itens_por_keyword: int = 8) -> int:
        total = 0
        for kw in keywords:
            itens = self.buscar_por_palavra_chave(kw, limite=itens_por_keyword)
            for item in itens:
                pergunta, conteudo, metadados = self.gerar_itens_para_pith(item)
                if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                    try:
                        alimentador._ensinado_fn(
                            pergunta=pergunta,
                            conteudo=conteudo,
                            fonte="wikipedia",
                            metadata=metadados
                        )
                        total += 1
                    except Exception as e:
                        logger.warning("Erro ao ingerir: %s" % e)
                time.sleep(0.3)
            time.sleep(1.0)
        logger.info("Wikipedia ingestao por keywords: %d itens" % total)
        return total
