import re
import logging
from typing import List, Tuple

logger = logging.getLogger("ravena.alimentacao.validador")

_PADRAO_LIXO = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
_PADRAO_BINARIO = re.compile(r'[\x00-\x08\x0e-\x1f]')

class ValidadorRegra1:
    def __init__(self, chars_minimos: int = 20, densidade_alfabetica_min: float = 0.4):
        self._chars_minimos = chars_minimos
        self._densidade_alfabetica_min = densidade_alfabetica_min

    def validar(self, texto: str) -> Tuple[bool, str]:
        if not texto or not texto.strip():
            return False, "vazio"

        texto_limpo = _PADRAO_LIXO.sub("", texto).strip()

        if len(texto_limpo) < self._chars_minimos:
            return False, f"muito_curto ({len(texto_limpo)} chars < {self._chars_minimos})"

        if _PADRAO_BINARIO.search(texto_limpo):
            return False, "conteudo_binario"

        chars_alfabeticos = sum(1 for c in texto_limpo if c.isalpha())
        densidade = chars_alfabeticos / max(len(texto_limpo), 1)
        if densidade < self._densidade_alfabetica_min:
            return False, f"densidade_alfabetica_baixa ({densidade:.2f} < {self._densidade_alfabetica_min})"

        return True, "ok"

    def validar_item(self, pergunta: str, conteudo: str) -> Tuple[bool, str]:
        val_pergunta, motivo_p = self.validar(pergunta)
        if not val_pergunta:
            return False, f"pergunta_{motivo_p}"
        val_conteudo, motivo_c = self.validar(conteudo)
        if not val_conteudo:
            return False, f"conteudo_{motivo_c}"
        return True, "ok"

    def filtrar(self, itens: List[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        resultado = []
        for pergunta, conteudo in itens:
            valido, motivo = self.validar_item(pergunta, conteudo)
            if valido:
                resultado.append((pergunta, conteudo, "ok"))
            else:
                logger.debug(f"Item rejeitado: {motivo} - '{pergunta[:40]}...'")
        return resultado
