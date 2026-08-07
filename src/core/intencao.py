import re
import logging

logger = logging.getLogger("ravena.intencao")

_PADROES_SAUDACAO = [
    r"^ol[áa]",
    r"^oi[\s\.!,]?$",
    r"^bom\s+dia",
    r"^boa\s+(tarde|noite)",
    r"^(tudo\s+bem|como\s+vai)",
    r"^hey\b",
    r"^hello\b",
    r"^hi\b",
    r"^(e a[ií]|fal[oa]i|fala[oa])\b",
    r"(tudo\s+bem|como\s+vai)",
    r"^oi[\s,!]*tudo\s+bem",
]

_PADROES_PERGUNTA = [
    r"^(qual|quais|que|o\s*que|quem|quando|onde|como|por\s*que|porquê|quanto[a]?s?)\b",
    r"^o\s+que\s+[ée]\b",
    r"^o\s+que\s+são\b",
    r"^explique\b",
    r"^explicar\b",
    r"^resuma\b",
    r"^resumir\b",
]

_PADROES_COMANDO = [
    r"^(faça|faca|crie|execute|rode|gere|mostre|liste|analise|implemente|teste|delete|remova|adicione|busque|procure|calcule|traduza)\b",
    r"^(criar|executar|rodar|gerar|mostrar|listar|analisar|implementar|testar|deletar|remover|adicionar|buscar|procurar|calcular|traduzir)\b",
]

_SAUDACOES_RESPOSTA = {
    "default": "Olá! Como posso ajudar você hoje?",
    "manha": "Bom dia! Em que posso ser útil?",
    "tarde": "Boa tarde! Como posso ajudar?",
    "noite": "Boa noite! Como posso auxiliar?",
}

_RESPOSTAS_INTENCAO: dict = {
    "saudacao": {
        "resposta": "",
        "sucesso": True,
    },
    "vazio": {
        "resposta": "Por favor, digite uma pergunta ou comando.",
        "sucesso": False,
        "erro": "INPUT_VAZIO",
    },
    "ambigua": {
        "resposta": "Pode reformular? Não entendi o que você quer dizer.",
        "sucesso": False,
        "erro": "INTENCAO_AMBIGUA",
        "sugestao": "Tente fazer uma pergunta mais específica ou usar um comando claro.",
    },
}


def _detectar_saudacao(texto: str) -> str:
    tl = texto.lower().strip()
    for padrao in _PADROES_SAUDACAO:
        if re.search(padrao, tl):
            return "default"
    return ""


def _detectar_comando(texto: str) -> bool:
    tl = texto.lower().strip()
    for padrao in _PADROES_COMANDO:
        if re.search(padrao, tl):
            return True
    return False


def _detectar_pergunta(texto: str) -> bool:
    tl = texto.lower().strip()
    if tl.endswith("?"):
        return True
    for padrao in _PADROES_PERGUNTA:
        if re.search(padrao, tl):
            return True
    return False


class ClassificadorIntencao:
    def classificar(self, texto: str) -> dict:
        if not texto or not texto.strip():
            return {
                "tipo": "vazio",
                "confianca": 1.0,
                "resposta": _RESPOSTAS_INTENCAO["vazio"]["resposta"],
                "payload": dict(_RESPOSTAS_INTENCAO["vazio"]),
            }

        texto_limpo = texto.strip()
        palavras = texto_limpo.split()

        # Saudacao
        saudacao = _detectar_saudacao(texto_limpo)
        if saudacao and len(palavras) <= 5:
            resposta = _SAUDACOES_RESPOSTA.get("default")
            return {
                "tipo": "saudacao",
                "confianca": 0.95,
                "resposta": resposta,
                "payload": {"resposta": resposta, "sucesso": True},
            }

        # Ambiguo: 1-2 palavras sem ser pergunta
        if len(palavras) <= 2 and not _detectar_pergunta(texto_limpo) and not _detectar_comando(texto_limpo):
            return {
                "tipo": "ambigua",
                "confianca": 0.7,
                "resposta": _RESPOSTAS_INTENCAO["ambigua"]["resposta"],
                "payload": dict(_RESPOSTAS_INTENCAO["ambigua"]),
            }

        # Comando
        if _detectar_comando(texto_limpo):
            return {
                "tipo": "comando",
                "confianca": 0.85,
                "resposta": None,
                "payload": None,
            }

        # Pergunta (fallback)
        if _detectar_pergunta(texto_limpo):
            return {
                "tipo": "pergunta",
                "confianca": 0.8,
                "resposta": None,
                "payload": None,
            }

        # Generico — provavelmente pergunta sem marcador explicito
        return {
            "tipo": "pergunta",
            "confianca": 0.6,
            "resposta": None,
            "payload": None,
        }
