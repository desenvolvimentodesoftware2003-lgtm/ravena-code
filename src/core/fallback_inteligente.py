import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger("ravena.fallback")

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TEMPLATES_PADRAO = {
    "ambiguo": {
        "primeiro": "Sobre qual assunto voce quer saber? Pode dar mais contexto?",
        "repetido": "Nao entendi. Pode reformular de outra forma?"
    }
}


class FallbackInteligente:
    """
    Fallback para casos AMBIGUOS e VAZIOS apenas.
    NUNCA retorna conteudo do conhecimento ou respostas.
    """

    def __init__(self, caminho_templates: Optional[str] = None):
        self.templates = self._carregar_templates(caminho_templates)
        self.ciclo_ambiguidade = 0
        logger.info("FallbackInteligente ativo — apenas ambiguo/vazio")

    def _carregar_templates(self, caminho: Optional[str] = None) -> dict:
        if caminho and os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar templates de {caminho}: {e}")
        caminho_padrao = os.path.join(_PROJETO_RAIZ, "data", "fallback_templates.json")
        if os.path.exists(caminho_padrao):
            try:
                with open(caminho_padrao, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar templates padrao: {e}")
        logger.info("Usando templates internos padrao")
        return dict(_TEMPLATES_PADRAO)

    def resetar_ciclo(self):
        self.ciclo_ambiguidade = 0

    def decidir(self, repetido: bool = False) -> Dict[str, str]:
        self.ciclo_ambiguidade += 1
        chave = "repetido" if repetido else "primeiro"
        texto = self.templates.get("ambiguo", {}).get(
            chave,
            "Nao entendi. Pode reformular?"
        )
        return {
            "tipo": "ambiguo",
            "resposta": texto,
            "sucesso": False,
            "erro": "AMBIGUIDADE",
            "sugestao": texto
        }

    def obter_diagnostico(self) -> Dict:
        return {
            "ciclo_ambiguidade": self.ciclo_ambiguidade,
            "funcao": "apenas_ambiguo_vazio",
        }
