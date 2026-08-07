import re
import logging
from typing import List, Tuple

logger = logging.getLogger("ravena.alimentacao.chunker")

_PADRAO_HEADING = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
_TAMANHO_FIXO_PADRAO = 1000
_SOBREPOSICAO_PADRAO = 100

class Chunker:
    def __init__(self, tamanho_fixo: int = _TAMANHO_FIXO_PADRAO,
                 sobreposicao: int = _SOBREPOSICAO_PADRAO):
        self._tamanho_fixo = tamanho_fixo
        self._sobreposicao = sobreposicao

    def chunk_hierarquico(self, texto: str) -> List[Tuple[str, str]]:
        if not texto or not texto.strip():
            return []

        linhas = texto.split("\n")
        secoes = []
        titulo_atual = "Documento"
        conteudo_atual = []

        for linha in linhas:
            match = _PADRAO_HEADING.match(linha)
            if match:
                if conteudo_atual:
                    secoes.append((titulo_atual, "\n".join(conteudo_atual).strip()))
                nivel = len(match.group(0)) - len(match.group(0).lstrip("#"))
                titulo_atual = match.group(1).strip()
                conteudo_atual = []
            else:
                conteudo_atual.append(linha)

        if conteudo_atual:
            secoes.append((titulo_atual, "\n".join(conteudo_atual).strip()))

        resultado = []
        for titulo, conteudo in secoes:
            if not conteudo:
                continue
            if len(conteudo) <= self._tamanho_fixo:
                resultado.append((titulo, conteudo))
            else:
                subchunks = self._dividir_grande(titulo, conteudo)
                resultado.extend(subchunks)

        return resultado

    def chunk_fixo(self, texto: str) -> List[Tuple[str, str]]:
        if not texto or not texto.strip():
            return []

        palavras = texto.split()
        chunks = []
        chunk_atual = []
        tamanho_atual = 0

        for palavra in palavras:
            chunk_atual.append(palavra)
            tamanho_atual += len(palavra) + 1
            if tamanho_atual >= self._tamanho_fixo:
                chunks.append(" ".join(chunk_atual))
                palavras_sobrepor = []
                tam_sobrepor = 0
                for p in reversed(chunk_atual):
                    palavras_sobrepor.insert(0, p)
                    tam_sobrepor += len(p) + 1
                    if tam_sobrepor >= self._sobreposicao:
                        break
                chunk_atual = palavras_sobrepor
                tamanho_atual = tam_sobrepor

        if chunk_atual:
            chunks.append(" ".join(chunk_atual))

        return [(f"Trecho {i+1}", c) for i, c in enumerate(chunks) if len(c) > 50]

    def _dividir_grande(self, titulo: str, texto: str) -> List[Tuple[str, str]]:
        paragrafos = [p.strip() for p in re.split(r'\n\s*\n', texto) if p.strip()]
        chunks = []
        chunk_atual = []
        tamanho_atual = 0

        for paragrafo in paragrafos:
            if tamanho_atual + len(paragrafo) > self._tamanho_fixo and chunk_atual:
                chunks.append((titulo, "\n\n".join(chunk_atual)))
                chunk_atual = []
                tamanho_atual = 0
            chunk_atual.append(paragrafo)
            tamanho_atual += len(paragrafo)

        if chunk_atual:
            chunks.append((titulo, "\n\n".join(chunk_atual)))

        return chunks

    def chunk(self, texto: str, modo: str = "hierarquico") -> List[Tuple[str, str]]:
        if modo == "hierarquico":
            return self.chunk_hierarquico(texto)
        return self.chunk_fixo(texto)
