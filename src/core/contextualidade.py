import re
import unicodedata
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("ravena.contextualidade")

STOPWORDS_PT = frozenset({
    "a", "ante", "apos", "ate", "com", "contra", "de", "desde", "em", "entre",
    "para", "por", "perante", "sem", "sob", "sobre", "tras", "trás",
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "me", "te", "se", "nos", "vos", "lhe", "lhes",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "vosso", "vossa", "vossos", "vossas",
    "esse", "essa", "esses", "essas", "este", "esta", "estes", "estas",
    "aquele", "aquela", "aqueles", "aquelas", "aquilo",
    "isto", "isso", "aquilo",
    "que", "quem", "qual", "quais", "cujo", "cuja", "cujos", "cujas",
    "quanto", "quanta", "quantos", "quantas",
    "quando", "onde", "como", "porque", "porque", "por que", "pois",
    "portanto", "contudo", "todavia", "entretanto", "no entanto",
    "mas", "porem", "porém", "todavia", "contudo",
    "e", "nem", "tambem", "ou", "ou...ou",
    "nao", "não", "nem", "nunca", "jamais", "sequer",
    "sim", "claro", "certo",
    "eu", "tu", "ele", "ela", "nos", "vos", "eles", "elas",
    "mim", "ti", "si",
    "da", "do", "das", "dos", "dum", "duns", "duma", "dumas",
    "num", "numa", "nuns", "numas",
    "na", "no", "nas", "nos",
    "pelo", "pela", "pelos", "pelas",
    "ao", "aos", "à", "as",
    "muito", "pouco", "mais", "menos", "tanto", "quanto",
    "algum", "alguma", "alguns", "algumas",
    "nenhum", "nenhuma", "nenhuns", "nenhumas",
    "todo", "toda", "todos", "todas",
    "outro", "outra", "outros", "outras",
    "cada", "certo", "certa", "certos", "certas",
    "varios", "vari as", "vários", "várias",
    "tal", "tais", "qualquer", "quaisquer",
    "la", "la", "ca", "cá", "ai", "ali", "ai", "ali", "aqui", "acolá", "acola",
    "so", "só", "apenas", "somente",
    "agora", "ja", "já", "ainda", "sempre", "nunca",
    "depois", "antes", "durante", "enquanto",
    "tambem", "também",
    "ser", "estar", "ter", "haver", "fazer", "dizer",
    "foi", "era", "sao", "são", "estao", "estão", "estava",
    "tem", "têm", "tinha", "havia",
    "vai", "vão", "vai",
    "pode", "podem", "poderia",
    "deve", "devem", "deveria",
    "fica", "ficam", "ficou",
    "passa", "passam", "passou",
})

INTERJECOES = frozenset({
    "nossa", "nossa senhora", "meu deus", "meu deus do ceu", "meu santo",
    "ah", "oh", "ih", "eh", "uh", "ai", "ui", "ei", "oi", "olá", "ola",
    "uau", "oba", "ebaaaa", "ebaaa",
    "poxa", "caramba", "puxa", "caraca", "barbaridade",
    "virgem", "credo", "cruz credo",
    "eita", "epa", "opa",
    "ufa", "ufaaa",
    "arre", "chi", "hum", "hmm", "ahn", "ahn", "ahn",
    "psiu", "psit",
    "alto la", "alto la",
    "bem", "bom", "otimo", "ótimo",
    "beleza", "blz", "show",
    "xis", "xispe",
})

PARTICULAS_REMOVIDAS = frozenset({
    "que", "e", "mas", "ou", "se", "como", "quando", "onde", "porque",
    "pois", "portanto", "contudo", "entretanto", "todavia",
})

_SIMILARIDADE_GRUPO_MIN = 0

_GRUPOS_PADRAO_LOCAL = {
    "geografia": frozenset({
        "capital", "pais", "cidade", "rio", "estado", "regiao", "continente",
        "oceano", "mapa", "fronteira", "habitante", "populacao", "localiza",
        "bandeira", "clima", "relevo", "latitude", "longitude", "territorio",
        "nacao", "municipio", "norte", "sul", "leste", "oeste", "lugar",
    }),
    "ciencia": frozenset({
        "agua", "fotossintese", "energia", "bioquimico", "quimica", "fisica",
        "biologia", "celula", "dna", "atomo", "molecula", "reacao", "elemento",
        "composto", "forca", "movimento", "gravidade", "temperatura", "pressao",
        "volume", "massa", "densidade", "eletron", "proton", "neutron",
        "organismo", "especie", "ecossistema", "habitat", "evolucao", "genetica",
        "proteina", "enzima", "metabolismo", "fossil", "mineral", "rocha",
        "vulcao", "tornado", "furacao", "terremoto", "cientista", "experimento",
        "laboratorio", "teoria", "lei", "cientifico", "luz", "cor",
        "espectro", "dispersao", "atmosfera", "ceu", "som", "onda",
        "eletromagnetico", "visivel", "frequencia",
    }),
    "tecnologia": frozenset({
        "python", "programacao", "software", "computador", "algoritmo", "codigo",
        "linguagem", "compilador", "dados", "inteligencia", "ia", "rede",
        "internet", "servidor", "aplicativo", "sistema", "hardware", "memoria",
        "processador", "banco", "api", "frontend", "backend", "dev", "bug",
        "funcao", "variavel", "loop", "classe", "objeto", "metodo", "biblioteca",
        "framework", "script", "terminal", "comando", "docker", "git", "nuvem",
        "site", "app", "programa", "web", "digital", "tecnologia", "informatica",
    }),
    "automotivo": frozenset({
        "pneu", "carro", "motor", "roda", "freio", "embreagem", "cambio",
        "oleo", "combustivel", "gasolina", "etanol", "direcao", "suspensao",
        "amortecedor", "radiador", "bateria", "alternador", "ignicao", "vela",
        "injetor", "turbo", "escapamento", "catalisador", "pistao", "cilindro",
        "valvula", "correia", "filtro", "lâmpada", "farol", "painel",
        "hodometro", "velocimetro", "tanque", "porta", "vidro", "travas",
        "alarme", "airbag", "abs", "cambio", "embreagem", "embreagem",
        "estofado", "lataria", "pintura", "parachoques", "para lama",
        "retrovisor", "limpador", "buzina", "ignicao", "partida",
        "oficina", "mecanico", "revisao", "troca", "vazamento", "superaquecer",
    }),
    "historia": frozenset({
        "descobriu", "guerra", "imperio", "revolucao", "seculo", "ano", "data",
        "epoca", "periodo", "antigo", "civilizacao", "historia", "fundador",
        "inventou", "criou", "imperador", "rei", "rainha", "presidente",
        "ditador", "colonia", "independencia", "batalha", "tratado", "nazismo",
        "feudal", "renascimento", "iluminismo", "escravidao", "democracia",
        "república", "monarquia", "reinado", "dinastia", "arqueologia", "pre historia",
        "medieval", "moderno", "contemporaneo", "antiguidade",
    }),
    "matematica": frozenset({
        "numero", "formula", "equacao", "calculo", "geometria", "algebra",
        "teorema", "logaritmo", "funcao", "derivada", "integral", "estatistica",
        "probabilidade", "soma", "subtracao", "divisao", "multiplicacao",
        "matriz", "vetor", "angulo", "triangulo", "quadrado", "circulo",
        "porcentagem", "media", "mediana", "moda", "desvio", "padrao",
        "limite", "sequencia", "serie", "conjunto", "intervalo", "grafico",
    }),
    "lingua": frozenset({
        "significa", "palavra", "lingua", "idioma", "traducao", "portugues",
        "ingles", "espanhol", "sinonimo", "antonimo", "gramatica", "verbo",
        "substantivo", "adjetivo", "adverbio", "preposicao", "conjugacao",
        "ortografia", "acentuacao", "pontuacao", "silaba", "ditongo", "hiato",
        "fonetica", "semantica", "morfologia", "sintaxe", "prefixo", "sufixo",
        "radical", "letra", "alfabeto", "texto", "frase", "paragrafo",
    }),
    "saude": frozenset({
        "doenca", "saude", "medico", "sintoma", "tratamento", "virus",
        "bacteria", "vacina", "remedio", "hospital", "alimentacao", "exercicio",
        "corpo", "mental", "febre", "dor", "cirurgia", "diagnostico",
        "prevencao", "cancer", "diabetes", "colesterol", "pressao", "cardiaco",
        "respiratorio", "digestivo", "nervoso", "muscular", "esqueletico",
        "pele", "cabelo", "unha", "visao", "audicao", "olfato", "paladar",
        "tato", "nutricao", "dieta", "vitamina", "mineral", "caloria",
        "carboidrato", "gordura", "imunidade", "alergia", "inflamacao",
        "infeccao", "ferimento", "queimadura", "fratura", "medicamento",
        "receita", "exame", "consulta", "clinico", "dentista", "psicologo",
    }),
    "filosofia": frozenset({
        "filosofia", "existencia", "etica", "moral", "pensador", "logica",
        "conhecimento", "verdade", "razao", "mente", "consciencia", "significado",
        "proposito", "socrates", "platao", "aristoteles", "nietzsche", "kant",
        "descartes", "estoico", "epicuro", "sofista", "dialetica", "metafisica",
        "epistemologia", "axiologia", "estetica", "politica", "justica",
        "liberdade", "igualdade", "dever", "virtude", "felicidade", "bem",
        "mal", "dualismo", "materialismo", "idealismo", "realismo",
        "pragmatismo", "ceticismo", "dogmatismo", "ontologia", "teleologia",
    }),
}

_EXCECOES_CURTAS = frozenset({
    "ia", "cpu", "api", "dna", "rna", "hp", "pc", "tv", "cd", "dvd", "usb",
    "hd", "ssd", "ram", "rom", "bios", "led", "lcd", "pdf", "xml", "json",
    "html", "css", "js", "py", "go", "c", "io", "id", "me", "mg", "km",
})

_EXCECOES_REMOVIDAS = frozenset({
    "nao", "não", "sim", "bem", "bom", "mau", "ma", "ja", "já", "so", "só",
    "da", "do", "das", "dos", "num", "numa", "na", "no", "nas", "nos",
    "ao", "aos", "la", "la", "ca", "cá",
})


def normalizar_acentos(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()


class Contextualidade:
    def __init__(self):
        self._grupos = {nome: palavras for nome, palavras in _GRUPOS_PADRAO_LOCAL.items()}
        logger.info(f"Contextualidade ativa — {len(self._grupos)} grupos, "
                     f"{len(STOPWORDS_PT)} stopwords, {len(INTERJECOES)} interjeicoes")

    def processar(self, texto: str) -> Dict[str, Any]:
        if not texto or not texto.strip():
            return {"original": texto or "", "limpa": "", "nucleo": [], "grupo_sugerido": "geral", "tem_ruido": False, "ruidos_removidos": {}}

        original = texto.strip()
        ruidos = {"interjeicoes": [], "stopwords": [], "particulas": [], "curtas": [], "acentos": []}
        estado_atual = original

        passo, estado_atual, removidos = self._remover_interjeicoes(estado_atual)
        ruidos["interjeicoes"] = removidos

        passo, estado_atual, removidos = self._remover_excecoes(estado_atual)
        ruidos["stopwords"].extend(removidos)

        passo, estado_atual, removidos = self._remover_particulas(estado_atual)
        ruidos["particulas"] = removidos

        nucleo, removidos = self._extrair_nucleo(estado_atual)
        ruidos["curtas"] = removidos

        limpa = " ".join(nucleo)
        grupo_sugerido = self._classificar(limpa)

        total_removidos = sum(len(v) for v in ruidos.values())
        tem_ruido = total_removidos > 0

        return {
            "original": original,
            "limpa": limpa,
            "nucleo": nucleo,
            "grupo_sugerido": grupo_sugerido,
            "tem_ruido": tem_ruido,
            "ruidos_removidos": ruidos,
            "total_ruido": total_removidos,
        }

    def limpar_para_classificacao(self, texto: str) -> str:
        return self.processar(texto)["limpa"]

    def _remover_interjeicoes(self, texto: str) -> Tuple[str, str, List[str]]:
        removidas = []
        palavras = texto.split()
        restantes = []
        for p in palavras:
            pl = p.lower()
            if pl in INTERJECOES:
                removidas.append(p)
            else:
                restantes.append(p)
        return "remover_interjeicoes", " ".join(restantes), removidas

    def _remover_excecoes(self, texto: str) -> Tuple[str, str, List[str]]:
        removidas = []
        palavras = texto.split()
        restantes = []
        for p in palavras:
            if p.lower() in _EXCECOES_REMOVIDAS:
                removidas.append(p)
            else:
                restantes.append(p)
        return "remover_excecoes", " ".join(restantes), removidas

    def _remover_particulas(self, texto: str) -> Tuple[str, str, List[str]]:
        removidas = []
        palavras = texto.split()
        restantes = []
        for p in palavras:
            pl = p.lower()
            if pl in PARTICULAS_REMOVIDAS or pl in STOPWORDS_PT:
                removidas.append(p)
            else:
                restantes.append(p)
        return "remover_particulas", " ".join(restantes), removidas

    def _extrair_nucleo(self, texto: str) -> Tuple[List[str], List[str]]:
        removidas = []
        nucleo = []
        for p in texto.split():
            pl = p.lower()
            if len(pl) <= 2 and pl not in _EXCECOES_CURTAS:
                removidas.append(p)
            else:
                nucleo.append(pl)
        return nucleo, removidas

    def _classificar(self, texto_limpo: str) -> str:
        if not texto_limpo:
            return "geral"
        palavras_texto = set(texto_limpo.split())
        melhor_grupo = "geral"
        melhor_pontuacao = 0
        for grupo, palavras_grupo in self._grupos.items():
            intersecao = palavras_texto & palavras_grupo
            pontuacao = len(intersecao)
            if pontuacao > melhor_pontuacao:
                melhor_pontuacao = pontuacao
                melhor_grupo = grupo
        return melhor_grupo

    def obter_diagnostico(self) -> Dict[str, Any]:
        return {
            "grupos": len(self._grupos),
            "stopwords": len(STOPWORDS_PT),
            "interjeicoes": len(INTERJECOES),
        }


if __name__ == "__main__":
    import json

    cx = Contextualidade()

    exemplos = [
        "nossa o meu pneu do meu carro virou",
        "qual e a capital do brasil",
        "o que e python",
        "ah nao sei o que fazer com esse febre",
        "quem foi Socrates mesmo",
        "poxa meu computador esta lento",
        "qual a formula da agua",
        "nossa senhora que dor de cabeca",
        "bem me diga como resolver essa equacao",
        "caramba essa luz do farol queimou",
    ]

    print(f"{'ORIGINAL':<50} {'LIMPA':<40} {'GRUPO':<15} {'RUIDO':>5}")
    print("-" * 115)
    for ex in exemplos:
        res = cx.processar(ex)
        print(f"{res['original']:<50} {res['limpa']:<40} {res['grupo_sugerido']:<15} {res['total_ruido']:>5}")
