import os
import re
import logging
from typing import Optional, List

logger = logging.getLogger("ravena.alimentacao.templates")

_PADRAO_HEADING_TEXTO = re.compile(r'^(.*?)[.?:!]?\s*$')

_PREFIXOS_VERBO = [
    "o que e", "qual e", "qual a", "o que sao", "quais sao", "como funciona",
    "o que significa", "o que faz", "para que serve", "quem e",
    "quando", "onde", "por que", "como"
]

class GeradorPergunta:
    def gerar(self, titulo: str, tipo: str = "md_section",
              nome_arquivo: Optional[str] = None) -> str:
        titulo = titulo.strip().lower()

        if not titulo or titulo in ("documento",):
            if nome_arquivo:
                nome = os.path.splitext(nome_arquivo)[0].replace("_", " ").replace("-", " ")
                return f"o que e {nome}?"
            return ""

        if tipo in ("py_class", "py_class_fallback"):
            return f"o que faz a classe {titulo}?"

        if tipo == "py_function":
            return f"o que faz a funcao {titulo}?"

        if tipo == "json_key":
            return f"o que e {titulo} na configuracao?"

        if any(titulo.lower().startswith(p) for p in _PREFIXOS_VERBO):
            return titulo.rstrip(".?!") + "?"

        titulo_limpo = re.sub(r'^#+\s*', '', titulo).strip()
        return f"o que e {titulo_limpo}?"

    def gerar_resumo(self, titulo: str, autores: str = "",
                     ano: str = "") -> str:
        partes = [f"resumo de {titulo.strip().lower()}"]
        if autores:
            partes.append(f"por {autores}")
        if ano:
            partes.append(f"({ano})")
        return " ".join(partes)

    def gerar_topicos(self, palavras_chave: List[str]) -> str:
        return f"topicos sobre {', '.join(palavras_chave[:5])}"



