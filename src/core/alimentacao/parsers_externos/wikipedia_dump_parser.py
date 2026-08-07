import os
import re
import bz2
import json
import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Iterator, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("ravena.alimentacao.wikipedia_dump")

_USER_AGENT = "RavenaAI/4.0 (https://github.com/ravena-aim; wiki-ingestion@ravena.ai)"

_PADRAO_TAGS_HTML = re.compile(r'<[^>]+>')
_PADRAO_REF = re.compile(r'<ref[^>]*>.*?</ref>', re.IGNORECASE | re.DOTALL)
_PADRAO_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)
_PADRAO_MULTISPACE = re.compile(r'  +')
_PADRAO_NEWLINES = re.compile(r'\n{3,}')
_PADRAO_TEMPLATE = re.compile(r'\{\{[^}]*\}\}')
_PADRAO_WIKILINK = re.compile(r'\[\[([^\]|]*?)(?:\|([^\]]*))?\]\]')
_PADRAO_BOLD = re.compile(r"'{2,}")
_PADRAO_IMAGEM = re.compile(r'\[\[(?:Imagem|Ficheiro|File|Image):[^\]]*\]\]', re.IGNORECASE)
_PADRAO_CATEGORIA = re.compile(r'\[\[Categoria:([^\|\]]+)(?:\|[^\]]*)?\]\]')
_PADRAO_BRACKETS_SOLTOS = re.compile(r'\[\[|\]\]')
_PADRAO_ENTITIES = re.compile(r'&(?:nbsp|amp|lt|gt|quot);')
_PADRAO_SECTION = re.compile(r'^=+\s*(.*?)\s*=+\s*$', re.MULTILINE)
_PADRAO_LISTA = re.compile(r'^[\*#]+', re.MULTILINE)

TAMANHO_MINIMO_ARTIGO = 200
TAMANHO_MAXIMO_ARTIGO = 100_000

@dataclass
class ArtigoWikipedia:
    titulo: str
    id: int
    texto: str
    categorias: List[str] = field(default_factory=list)
    secoes: List[Tuple[str, str]] = field(default_factory=list)

class WikipediaDumpParser:
    def __init__(self, lingua: str = "pt", chunk_size: int = 1500):
        self._lingua = lingua
        self._chunk_size = chunk_size

    def baixar_dump(self, destino: str, lingua: Optional[str] = None) -> str:
        import urllib.request
        lang = lingua or self._lingua
        url = f"https://dumps.wikimedia.org/{lang}wiki/latest/{lang}wiki-latest-pages-articles.xml.bz2"
        caminho = os.path.join(destino, f"{lang}wiki-latest-pages-articles.xml.bz2")
        os.makedirs(destino, exist_ok=True)
        logger.info(f"Baixando {url} para {caminho}")
        req = urllib.request.Request(url, headers={
            "User-Agent": "RavenaAI/4.0 (https://github.com/ravena-aim; wiki-ingestion@ravena.ai)"
        })
        with urllib.request.urlopen(req) as response:
            with open(caminho, "wb") as f:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    logger.info(f"Baixado {os.path.getsize(caminho) / 1024 / 1024:.0f} MB")
        logger.info(f"Download concluido: {caminho}")
        return caminho

    def listar_dumps_disponiveis(self, lingua: Optional[str] = None) -> List[str]:
        import urllib.request
        import json
        lang = lingua or self._lingua
        url = f"https://dumps.wikimedia.org/{lang}wiki/latest/"
        try:
            from html.parser import HTMLParser
            class LinkParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.links = []
                def handle_starttag(self, tag, attrs):
                    if tag == "a":
                        for name, val in attrs:
                            if name == "href" and val.endswith(".bz2"):
                                self.links.append(val)
            req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req) as f:
                html = f.read().decode("utf-8")
            parser = LinkParser()
            parser.feed(html)
            return [url + link for link in parser.links if "pages-articles" in link]
        except Exception as e:
            logger.warning(f"Erro ao listar dumps: {e}")
            return [url + f"{lang}wiki-latest-pages-articles.xml.bz2"]

    def estimar_tamanho_dump(self, lingua: Optional[str] = None) -> Optional[int]:
        import urllib.request
        lang = lingua or self._lingua
        url = f"https://dumps.wikimedia.org/{lang}wiki/latest/{lang}wiki-latest-pages-articles.xml.bz2"
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": _USER_AGENT})
            with urllib.request.urlopen(req) as f:
                return int(f.headers.get("Content-Length", 0))
        except Exception as e:
            logger.warning(f"Erro ao estimar tamanho: {e}")
            return None

    def iterar_artigos(self, caminho_dump: str) -> Iterator[ArtigoWikipedia]:
        if caminho_dump.endswith(".bz2"):
            arquivo = bz2.open(caminho_dump, "rt", encoding="utf-8", errors="replace")
        else:
            arquivo = open(caminho_dump, "rt", encoding="utf-8", errors="replace")

        ns = "{http://www.mediawiki.org/xml/export-0.11/}"
        buffer = ""
        dentro_page = False
        for linha in arquivo:
            if "<page>" in linha:
                dentro_page = True
                buffer = linha
            elif dentro_page:
                buffer += linha
                if "</page>" in linha:
                    artigo = self._parse_page_xml(buffer, ns)
                    if artigo:
                        yield artigo
                    buffer = ""
                    dentro_page = False

    def _parse_page_xml(self, xml_str: str, ns: str) -> Optional[ArtigoWikipedia]:
        try:
            wrapper = f'<root xmlns="{ns.strip("{}")}">{xml_str}</root>'
            root = ET.fromstring(wrapper)
            page = root[0]
        except Exception:
            return None
        titulo_elem = page.find(f"{ns}title")
        id_elem = page.find(f"{ns}id")
        rev = page.find(f"{ns}revision")
        if rev is None:
            return None
        texto_elem = rev.find(f"{ns}text")
        if titulo_elem is None or texto_elem is None or texto_elem.text is None:
            return None
        titulo = titulo_elem.text.strip()
        artigo_id = int(id_elem.text) if id_elem is not None and id_elem.text and id_elem.text.isdigit() else 0
        texto = texto_elem.text
        if not titulo or not texto:
            return None
        return self._processar_artigo(
            titulo=titulo,
            id=artigo_id,
            texto=texto
        )

    def _processar_artigo(self, titulo: str, id: int, texto: str) -> Optional[ArtigoWikipedia]:
        if not texto or len(texto) < TAMANHO_MINIMO_ARTIGO:
            return None
        if len(texto) > TAMANHO_MAXIMO_ARTIGO:
            texto = texto[:TAMANHO_MAXIMO_ARTIGO]
        if texto.startswith("#REDIRECT") or texto.startswith("#redirect"):
            return None
        categorias = self._extrair_categorias(texto)
        texto_limpo = self._limpar_wikitext(texto)
        if len(texto_limpo) < TAMANHO_MINIMO_ARTIGO:
            return None
        secoes = self._extrair_secoes(texto_limpo)
        return ArtigoWikipedia(
            titulo=titulo,
            id=id,
            texto=texto_limpo,
            categorias=categorias,
            secoes=secoes
        )

    def _limpar_wikitext(self, texto: str) -> str:
        texto = _PADRAO_REF.sub("", texto)
        texto = _PADRAO_COMMENT.sub("", texto)
        texto = _PADRAO_TEMPLATE.sub("", texto)
        texto = _PADRAO_IMAGEM.sub("", texto)
        texto = _PADRAO_WIKILINK.sub(self._substituir_wikilink, texto)
        texto = _PADRAO_BOLD.sub("", texto)
        texto = _PADRAO_TAGS_HTML.sub("", texto)
        linhas = []
        for linha in texto.split("\n"):
            linha = linha.strip()
            if linha and not linha.startswith("|") and not linha.startswith("!"):
                if not linha.startswith("}}") and not linha.startswith("{{"):
                    linhas.append(linha)
        texto = "\n".join(linhas)
        texto = _PADRAO_BRACKETS_SOLTOS.sub("", texto)
        texto = _PADRAO_ENTITIES.sub(" ", texto)
        texto = _PADRAO_MULTISPACE.sub(" ", texto)
        texto = _PADRAO_NEWLINES.sub("\n\n", texto)
        return texto.strip()

    @staticmethod
    def _substituir_wikilink(match: re.Match) -> str:
        alvo, texto = match.groups()
        if texto and texto.strip():
            return texto.strip()
        if alvo and alvo.strip():
            return alvo.strip()
        return ""

    def _extrair_categorias(self, texto: str) -> List[str]:
        categorias = re.findall(r'\[\[Categoria:([^\|\]]+)(?:\|[^\]]*)?\]\]', texto)
        return [c.strip() for c in categorias[:20]]

    def _extrair_secoes(self, texto: str) -> List[Tuple[str, str]]:
        secoes = []
        partes = re.split(r'(^=+[^=]+=+\s*$)', texto, flags=re.MULTILINE)
        titulo_atual = "Introducao"
        conteudo_atual = []
        for parte in partes:
            match = re.match(r'^=+\s*(.+?)\s*=+\s*$', parte.strip())
            if match:
                if conteudo_atual:
                    secoes.append((titulo_atual, "\n".join(conteudo_atual).strip()))
                titulo_atual = match.group(1).strip()
                conteudo_atual = []
            else:
                conteudo_atual.append(parte)
        if conteudo_atual:
            secoes.append((titulo_atual, "\n".join(conteudo_atual).strip()))
        return [(t, c) for t, c in secoes if len(c) > 50]

    def chunk_artigo(self, artigo: ArtigoWikipedia) -> List[Tuple[str, str, Dict[str, Any]]]:
        chunks = []
        if artigo.secoes:
            for titulo_secao, conteudo in artigo.secoes:
                if len(conteudo) > self._chunk_size:
                    subchunks = self._chunk_grande(conteudo, self._chunk_size)
                    for i, sub in enumerate(subchunks):
                        pergunta = f"o que e {artigo.titulo.lower()} - {titulo_secao.lower()} (parte {i+1})?"
                        chunks.append((pergunta, sub, {
                            "fonte": "wikipedia_dump",
                            "titulo": artigo.titulo,
                            "secao": titulo_secao,
                            "parte": i + 1,
                            "categorias": artigo.categorias[:5]
                        }))
                else:
                    pergunta = f"o que e {artigo.titulo.lower()} - {titulo_secao.lower()}?"
                    chunks.append((pergunta, conteudo, {
                        "fonte": "wikipedia_dump",
                        "titulo": artigo.titulo,
                        "secao": titulo_secao,
                        "categorias": artigo.categorias[:5]
                    }))
        else:
            if len(artigo.texto) > self._chunk_size:
                subchunks = self._chunk_grande(artigo.texto, self._chunk_size)
                for i, sub in enumerate(subchunks):
                    pergunta = f"o que e {artigo.titulo.lower()}? (parte {i+1})"
                    chunks.append((pergunta, sub, {
                        "fonte": "wikipedia_dump",
                        "titulo": artigo.titulo,
                        "parte": i + 1,
                        "categorias": artigo.categorias[:5]
                    }))
            else:
                pergunta = f"o que e {artigo.titulo.lower()}?"
                chunks.append((pergunta, artigo.texto, {
                    "fonte": "wikipedia_dump",
                    "titulo": artigo.titulo,
                    "categorias": artigo.categorias[:5]
                }))
        return chunks

    def _chunk_grande(self, texto: str, tamanho: int) -> List[str]:
        paragrafos = texto.split("\n")
        chunks = []
        chunk_atual = []
        tam_atual = 0
        for p in paragrafos:
            if tam_atual + len(p) > tamanho and chunk_atual:
                chunks.append("\n".join(chunk_atual))
                chunk_atual = []
                tam_atual = 0
            chunk_atual.append(p)
            tam_atual += len(p)
        if chunk_atual:
            chunks.append("\n".join(chunk_atual))
        return [c for c in chunks if len(c) > 50]

    def ingerir_dump_no_alimentador(self, caminho_dump: str, alimentador: Any,
                                      max_artigos: Optional[int] = None,
                                      categorias_filtro: Optional[List[str]] = None) -> int:
        from src.core.alimentacao.manifest import ManifestIngestao
        total = 0
        for i, artigo in enumerate(self.iterar_artigos(caminho_dump)):
            if max_artigos and i >= max_artigos:
                break
            if categorias_filtro and not any(cat in artigo.categorias for cat in categorias_filtro):
                continue
            chunks = self.chunk_artigo(artigo)
            for pergunta, conteudo, metadados in chunks:
                if hasattr(alimentador, "_ensinado_fn") and alimentador._ensinado_fn:
                    try:
                        alimentador._ensinado_fn(
                            pergunta=pergunta,
                            conteudo=conteudo,
                            fonte="wikipedia_dump",
                            metadata=metadados
                        )
                        total += 1
                    except Exception as e:
                        logger.warning(f"Erro ao ingerir chunk: {e}")
                else:
                    from src.core.alimentacao.ingestao import PipelineIngestao
                    logger.warning("Alimentador sem funcao ensinar_fn conectada")
                    return total
            if (i + 1) % 100 == 0:
                logger.info(f"Processados {i+1} artigos, {total} chunks ingeridos")
        logger.info(f"Ingestao concluida: {total} chunks de {i+1} artigos")
        return total
