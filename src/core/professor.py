"""
RAVENA AIM — src/core/professor.py
====================================
Professor: sistema transversal de ensino e avaliacao.
Avalia qualquer agente, aprende com correcoes do expert humano,
usa metodologias de faculdades renomadas + inspiracoes didaticas,
e acumula dataset para futuro Ravena LLM.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("ravena.professor")

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ARQUIVO_PERSISTENCIA = os.path.join(_PROJETO_RAIZ, "data", "professor_ravena.json")

# ─── NIVEIS (nao-lineares) ───────────────────────────────────────────────────

class Nivel(Enum):
    FUNDAMENTAL = "fundamental"
    MEDIO = "medio"
    SUPERIOR = "superior"
    POS = "pos"
    MESTRADO = "mestrado"
    DOUTORADO = "doutorado"
    PHD = "phd"
    POS_DOC = "pos_doc"

_ORDEM_NIVEIS = [
    Nivel.FUNDAMENTAL, Nivel.MEDIO, Nivel.SUPERIOR, Nivel.POS,
    Nivel.MESTRADO, Nivel.DOUTORADO, Nivel.PHD, Nivel.POS_DOC
]

def nivel_para_indice(nivel: Nivel) -> int:
    try:
        return _ORDEM_NIVEIS.index(nivel)
    except ValueError:
        return 0

# ─── METODOLOGIAS (faculdades) ───────────────────────────────────────────────

METODOLOGIAS = {
    "mit": {
        "nome": "MIT - Mens et Manus",
        "foco": "aprendizado_baseado_em_projetos",
        "principio": "Aprender fazendo — projeto pratico como centro da avaliacao."
    },
    "harvard": {
        "nome": "Harvard - Case Method",
        "foco": "estudo_de_casos",
        "principio": "Decisoes em cenarios reais — nao ha resposta unica, ha argumentacao."
    },
    "socratica": {
        "nome": "Socratica - Mayeutica",
        "foco": "questionamento_continuo",
        "principio": "O aluno chega a verdade por perguntas, nao por respostas prontas."
    },
    "oxford": {
        "nome": "Oxford - Tutorial System",
        "foco": "tutoria_individual",
        "principio": "Discussao one-on-one com desafio constante ao pensamento critico."
    },
    "carnegie": {
        "nome": "Carnegie Mellon - Mastery Learning",
        "foco": "dominio_tecnico_obrigatorio",
        "principio": "So avanca quem demonstra dominio absoluto do prerequisito."
    },
    "personalizada": {
        "nome": "Personalizada - Adaptativa",
        "foco": "adaptacao_continua",
        "principio": "Metodologia moldada ao perfil do aluno no momento da avaliacao."
    }
}

# ─── INSPIRACOES (didatica) ──────────────────────────────────────────────────

INSPIRACOES = {
    "japonesa_ttp": {
        "nome": "Japonesa - Teaching Through Problem-Solving",
        "fases": ["hatsumon", "kikan_shido", "neriage", "matome"],
        "descricao": "O problema precede a definicao. O erro e andaime."
    },
    "singapura_cpa": {
        "nome": "Singapura - CPA (Concreto-Pictorico-Abstrato)",
        "fases": ["concreto", "pictorico", "abstrato"],
        "descricao": "Reducao de carga cognitiva: do tangivel ao simbolico."
    },
    "tad_mesogenese": {
        "nome": "TAD - Gestao da Mesogenese",
        "fases": ["milieu", "investigacao", "institucionalizacao"],
        "descricao": "O conhecimento emerge da interacao com o meio."
    },
    "lesson_study": {
        "nome": "Lesson Study - Ciclo Colaborativo",
        "fases": ["planejar", "executar", "observar", "refletir"],
        "descricao": "Melhoria continua atraves de pesquisa colaborativa."
    }
}

_INSPIRACAO_PADRAO = "japonesa_ttp"

# ─── TESTES PADRAO (pergunta, resposta_esperada) ──────────────────────────────

_TESTES_PADRAO = {
    "geografia": {
        "capitais": [
            ("Qual a capital do Brasil?", "Brasilia"),
            ("Qual a capital da Franca?", "Paris"),
            ("Qual a capital do Japao?", "Toquio"),
            ("Qual a capital da Inglaterra?", "Londres"),
            ("Qual a capital dos Estados Unidos?", "Washington"),
            ("Qual a capital da Argentina?", "Buenos Aires"),
            ("Qual a capital de Portugal?", "Lisboa"),
            ("Qual a capital da Espanha?", "Madri"),
            ("Qual a capital da Italia?", "Roma"),
            ("Qual a capital da Alemanha?", "Berlim"),
            ("Qual a capital do Canada?", "Ottawa"),
            ("Qual a capital da Australia?", "Camberra"),
            ("Qual a capital do Mexico?", "Cidade do Mexico"),
            ("Qual a capital da Russia?", "Moscou"),
            ("Qual a capital da China?", "Pequim"),
            ("Qual a capital da India?", "Nova Delhi"),
            ("Qual a capital do Egito?", "Cairo"),
            ("Qual a capital do Chile?", "Santiago"),
            ("Qual a capital da Colombia?", "Bogota"),
            ("Qual a capital do Uruguai?", "Montevideu"),
        ],
        "continentes": [
            ("O Brasil fica na America do Sul?", "Sim"),
            ("A Franca fica na Asia?", "Nao"),
            ("O Japao fica na Asia?", "Sim"),
            ("A Africa e um continente?", "Sim"),
            ("A Australia e um pais e um continente?", "Sim"),
            ("O Canada fica na America do Norte?", "Sim"),
            ("O Egito fica na Africa?", "Sim"),
            ("A Russia fica na Asia?", "Nao"),
            ("A Italia fica na Europa?", "Sim"),
            ("O Chile fica na America do Sul?", "Sim"),
        ],
        "paises": [
            ("Qual o maior pais do mundo em territorio?", "Russia"),
            ("Qual o pais mais populoso do mundo?", "India"),
            ("Qual o menor pais do mundo?", "Vaticano"),
            ("O Brasil faz fronteira com o Chile?", "Nao"),
            ("Quantos paises tem na America do Sul?", "12"),
            ("O Brasil faz fronteira com a Argentina?", "Sim"),
            ("Qual o pais com mais costa litoranea?", "Canada"),
            ("Qual pais e conhecido como pais do sol nascente?", "Japao"),
        ],
        "geral": [
            ("Qual o maior oceano do mundo?", "Pacifico"),
            ("Qual o maior rio do mundo?", "Amazonas"),
            ("Qual a maior montanha do mundo?", "Everest"),
            ("Qual o maior deserto do mundo?", "Antartida"),
            ("Qual a maior floresta do mundo?", "Amazonia"),
            ("Qual a maior ilha do mundo?", "Groenlandia"),
            ("Qual o maior lago do mundo?", "Caspio"),
            ("O Rio Amazonas desagua no oceano Atlantico?", "Sim"),
        ]
    },
    "matematica": {
        "aritmetica": [
            ("Quanto e 2 + 2?", "4"),
            ("Quanto e 10 / 2?", "5"),
            ("Quanto e 3 * 3?", "9"),
            ("Quanto e 15 + 7?", "22"),
            ("Quanto e 100 - 45?", "55"),
            ("Quanto e 8 * 7?", "56"),
            ("Quanto e 144 / 12?", "12"),
            ("Quanto e 25 + 18?", "43"),
            ("Quanto e 9 * 9?", "81"),
            ("Quanto e 50 / 5?", "10"),
            ("Quanto e 12 * 11?", "132"),
            ("Quanto e 200 - 87?", "113"),
            ("Quanto e 6 * 8?", "48"),
            ("Quanto e 99 + 1?", "100"),
            ("Quanto e 7 * 7?", "49"),
            ("Quanto e 36 / 6?", "6"),
            ("Quanto e 15 * 4?", "60"),
            ("Quanto e 81 / 9?", "9"),
            ("Quanto e 13 + 29?", "42"),
            ("Quanto e 500 - 237?", "263"),
        ],
        "geometria": [
            ("Quantos lados tem um triangulo?", "3"),
            ("Quantos lados tem um quadrado?", "4"),
            ("Quantos lados tem um pentagono?", "5"),
            ("Quantos lados tem um hexagono?", "6"),
            ("Quantos lados tem um octogono?", "8"),
            ("Quantos lados tem um decagono?", "10"),
            ("Quantos vertices tem um cubo?", "8"),
            ("Quantas faces tem um cubo?", "6"),
            ("Quantas arestas tem um cubo?", "12"),
            ("A soma dos angulos internos de um triangulo e 180 graus?", "Sim"),
        ],
        "fracao": [
            ("Quanto e 1/2 + 1/2?", "1"),
            ("Quanto e 1/4 de 100?", "25"),
            ("Quanto e 3/4 de 100?", "75"),
            ("0,5 e igual a 1/2?", "Sim"),
            ("Quanto e 1/3 de 30?", "10"),
            ("Quanto e 2/3 de 30?", "20"),
        ],
        "porcentagem": [
            ("Quanto e 50 porcento de 200?", "100"),
            ("Quanto e 10 porcento de 500?", "50"),
            ("Quanto e 25 porcento de 80?", "20"),
            ("Quanto e 100 porcento de 50?", "50"),
        ],
    },
    "ciencia": {
        "fisica": [
            ("Qual a velocidade da luz no vacuo?", "300000 km/s"),
            ("A agua ferve a 100 graus Celsius ao nivel do mar?", "Sim"),
            ("A agua congela a 0 graus Celsius?", "Sim"),
            ("Qual a lei da gravitacao universal?", "Newton"),
            ("Qual a formula da energia cinetica?", "E = mv2/2"),
            ("O som se propaga no vacuo?", "Nao"),
            ("Qual a unidade de medida de forca?", "Newton"),
            ("Qual a unidade de medida de energia?", "Joule"),
            ("Qual a unidade de medida de potencia?", "Watt"),
            ("O que e a gravidade?", "Forca que atrai objetos para o centro da Terra"),
            ("Qual a aceleracao da gravidade na Terra?", "9,8 m/s2"),
            ("A luz e uma onda eletromagnetica?", "Sim"),
        ],
        "quimica": [
            ("Qual o simbolo quimico da agua?", "H2O"),
            ("Qual o simbolo quimico do dioxido de carbono?", "CO2"),
            ("Qual o simbolo quimico do oxigenio?", "O2"),
            ("Quantos elementos tem a tabela periodica?", "118"),
            ("Qual o elemento mais leve?", "Hidrogenio"),
            ("Qual o gas mais abundante na atmosfera?", "Nitrogenio"),
            ("O que e pH?", "Potencial hidrogenionico"),
            ("Uma solucao com pH 7 e neutra?", "Sim"),
        ],
        "biologia": [
            ("O corpo humano tem quantos ossos?", "206"),
            ("Qual o orgao responsavel por bombear o sangue?", "Coracao"),
            ("Quantos pares de cromossomos tem o ser humano?", "23"),
            ("Qual o maior orgao do corpo humano?", "Pele"),
            ("Qual o orgao responsavel pela filtragem do sangue?", "Rim"),
            ("Onde ocorre a fotossintese nas plantas?", "Cloroplastos"),
            ("O cerebro faz parte do sistema nervoso?", "Sim"),
            ("Quantos dentes tem um adulto?", "32"),
            ("O estomago faz parte do sistema digestorio?", "Sim"),
            ("Os pulmoes sao responsaveis pela respiracao?", "Sim"),
            ("O DNA e a molecula da hereditariedade?", "Sim"),
            ("O sangue e composto por globulos vermelhos e brancos?", "Sim"),
        ],
        "astronomia": [
            ("Qual o planeta mais proximo do Sol?", "Mercurio"),
            ("Qual o planeta mais distante do Sol?", "Netuno"),
            ("Qual o maior planeta do sistema solar?", "Jupiter"),
            ("Quantos planetas tem o sistema solar?", "8"),
            ("A Terra e o terceiro planeta do sistema solar?", "Sim"),
            ("O que e a Via Lactea?", "Galaxia"),
            ("O Sol e uma estrela?", "Sim"),
            ("Qual o satelite natural da Terra?", "Lua"),
            ("Marte e conhecido como o planeta vermelho?", "Sim"),
            ("O que causa as estacoes do ano?", "Inclinacao da Terra"),
        ],
    },
    "historia": {
        "brasil": [
            ("Quem descobriu o Brasil?", "Pedro Alvares Cabral"),
            ("O Brasil foi colonizado por Portugal?", "Sim"),
            ("Em que ano o Brasil foi descoberto?", "1500"),
            ("Em que ano o Brasil se tornou independente?", "1822"),
            ("Quem proclamou a independencia do Brasil?", "Dom Pedro I"),
            ("Em que ano foi proclamada a Republica no Brasil?", "1889"),
            ("Quem foi o primeiro presidente do Brasil?", "Deodoro da Fonseca"),
            ("Em que ano a escravatura foi abolida no Brasil?", "1888"),
            ("Quem assinou a Lei Aurea?", "Princesa Isabel"),
            ("Qual a capital do Brasil antes de Brasilia?", "Rio de Janeiro"),
            ("O Brasil participou da Segunda Guerra Mundial?", "Sim"),
            ("Quem foi Getulio Vargas?", "Presidente do Brasil"),
        ],
        "geral": [
            ("Em que ano terminou a Segunda Guerra Mundial?", "1945"),
            ("Em que ano comecou a Primeira Guerra Mundial?", "1914"),
            ("Em que ano o homem pisou na Lua?", "1969"),
            ("Quem foi o primeiro homem a pisar na Lua?", "Neil Armstrong"),
            ("Em que ano o Muro de Berlim caiu?", "1989"),
            ("Quem foi Albert Einstein?", "Fisico alemao"),
            ("O imperio romano caiu em 476 d.C.?", "Sim"),
            ("Quem foi Leonardo da Vinci?", "Artista e inventor italiano"),
            ("A Grecia Antiga e considerada o berco da democracia?", "Sim"),
            ("Quem foi Marco Polo?", "Explorador veneziano"),
        ],
        "antiga": [
            ("Qual a maior civilizacao da Mesopotamia?", "Sumeria"),
            ("Onde foi construida a Grande Muralha da China?", "China"),
            ("Quem foi Cleopatra?", "Rainha do Egito"),
            ("Os egipcios construiram as piramides?", "Sim"),
            ("O que e o Coliseu?", "Anfiteatro romano"),
        ],
    },
    "tecnologia": {
        "programacao": [
            ("Python e uma linguagem de programacao?", "Sim"),
            ("HTML e uma linguagem de programacao?", "Nao"),
            ("JavaScript e usado para front-end?", "Sim"),
            ("O que e um algoritmo?", "Sequencia de passos para resolver um problema"),
            ("O que e uma variavel na programacao?", "Espaco de memoria para armazenar um valor"),
            ("O que e uma funcao na programacao?", "Bloco de codigo reutilizavel"),
            ("O que e um loop na programacao?", "Estrutura que repete um bloco de codigo"),
            ("O que e orientacao a objetos?", "Paradigma de programacao baseado em objetos"),
            ("SQL e uma linguagem de consulta a banco de dados?", "Sim"),
            ("O que e Git?", "Sistema de controle de versao"),
        ],
        "hardware": [
            ("O que significa CPU?", "Unidade Central de Processamento"),
            ("O que significa RAM?", "Memoria de Acesso Aleatorio"),
            ("O que significa SSD?", "Unidade de Estado Solido"),
            ("O que significa GPU?", "Unidade de Processamento Grafico"),
            ("O que e um bit?", "Menor unidade de informacao digital"),
            ("Quantos bits tem um byte?", "8"),
            ("O que e um disco rigido?", "Dispositivo de armazenamento permanente"),
        ],
        "geral": [
            ("O que e inteligencia artificial?", "Simulacao de inteligencia humana por maquinas"),
            ("O que e machine learning?", "Subcampo da IA que aprende com dados"),
            ("O que e cloud computing?", "Computacao em nuvem via internet"),
            ("A internet foi criada na decada de 1960?", "Sim"),
            ("O que e criptografia?", "Tecnica de codificacao de dados"),
        ],
    },
    "lingua": {
        "gramatica": [
            ("'Casa' e um substantivo?", "Sim"),
            ("'Correr' e um verbo?", "Sim"),
            ("'Feliz' e um adjetivo?", "Sim"),
            ("'Ele' e um pronome?", "Sim"),
            ("'E' e uma conjuncao?", "Sim"),
            ("'Muito' e um adverbio?", "Sim"),
            ("'O' e um artigo definido?", "Sim"),
            ("'Em' e uma preposicao?", "Sim"),
            ("'Ah' e uma interjeicao?", "Sim"),
            ("Sujeito e o termo da oracao sobre o qual se declara algo?", "Sim"),
            ("Predicado e a parte da oracao que contem o verbo?", "Sim"),
            ("Um periodo composto tem mais de uma oracao?", "Sim"),
        ],
        "literatura": [
            ("Quem escreveu 'Dom Casmurro'?", "Machado de Assis"),
            ("Quem escreveu 'Grande Sertao Veredas'?", "Guimaraes Rosa"),
            ("Quem escreveu 'Os Lusiadas'?", "Luis de Camoes"),
            ("Quem escreveu 'Dom Quixote'?", "Miguel de Cervantes"),
            ("Quem escreveu 'Romeu e Julieta'?", "William Shakespeare"),
            ("Quem escreveu 'A Moreninha'?", "Joaquim Manuel de Macedo"),
            ("Quem escreveu 'O Alquimista'?", "Paulo Coelho"),
            ("Quem escreveu '1984'?", "George Orwell"),
        ],
        "geral": [
            ("Quantas letras tem o alfabeto portugues?", "26"),
            ("Quantas vogais tem o alfabeto portugues?", "5"),
            ("O que e uma silaba?", "Fonema ou grupo de fonemas pronunciados numa so emissao de voz"),
            ("O que e um paragrafo?", "Divisao de um texto composta por uma ou mais frases"),
            ("O que e sinonimo?", "Palavra com significado igual ou semelhante"),
            ("O que e antonimo?", "Palavra com significado oposto"),
        ],
    },
    "cultura": {
        "geral": [
            ("Qual o esporte mais popular do Brasil?", "Futebol"),
            ("Qual a maior festa popular do Brasil?", "Carnaval"),
            ("Quantas copas do mundo o Brasil ganhou?", "5"),
            ("Qual o maior museu do mundo?", "Louvre"),
            ("O futebol foi inventado na Inglaterra?", "Sim"),
            ("Qual o pais que mais vezes ganhou a Copa do Mundo?", "Brasil"),
            ("Qual o nome do deus do trovão na mitologia nordica?", "Thor"),
            ("Quem pintou a Mona Lisa?", "Leonardo da Vinci"),
            ("Qual o quadro mais famoso de Van Gogh?", "Noite Estrelada"),
            ("O samba e um genero musical brasileiro?", "Sim"),
        ],
        "religiao": [
            ("O Natal celebra o nascimento de Jesus?", "Sim"),
            ("A Pascoa celebra a ressurreicao de Jesus?", "Sim"),
            ("O Budismo foi fundado por Buddha?", "Sim"),
            ("O Islamismo foi fundado por Maome?", "Sim"),
            ("A Biblia e o livro sagrado do Cristianismo?", "Sim"),
            ("O Corao e o livro sagrado do Islamismo?", "Sim"),
        ],
    },
}

_INSPIRACAO_FALLBACK_ASSUNTO: Dict[str, str] = {
    "ciberseguranca": "japonesa_ttp",
    "engenharia_reversa": "japonesa_ttp",
    "arquitetura_software": "singapura_cpa",
    "mercado_financeiro": "tad_mesogenese",
    "filosofia": "japonesa_ttp",
    "matematica": "singapura_cpa",
    "ciencia": "singapura_cpa",
    "historia": "tad_mesogenese",
    "lingua": "lesson_study",
    "geografia": "tad_mesogenese",
}

# ─── PARECERES POR INSPIRACAO ────────────────────────────────────────────────

def _gerar_frases_inspiracao(inspiracao: str, assunto: str, acertos: float, total: float) -> List[str]:
    frases = []
    pct = acertos / total if total > 0 else 0

    if inspiracao == "japonesa_ttp":
        frases.append("Hatsumon: qual problema este codigo/analise resolve?")
        if pct < 0.5:
            frases.append("Kikan-shido: observei sua estrutura — volte ao problema inicial.")
            frases.append("Neriage: compare sua abordagem com o esperado. O que difere?")
            frases.append("Matome: entao, o conceito central ainda precisa ser consolidado.")
        elif pct < 0.8:
            frases.append("Kikan-shido: notei avancos — mas ha um desvio na aplicacao.")
            frases.append("Neriage: como sua solucao se compara a uma abordagem alternativa?")
            frases.append("Matome: o caminho esta certo — refine a execucao.")
        else:
            frases.append("Kikan-shido: bom dominio — poucos ajustes necessarios.")
            frases.append("Neriage: voce consegue generalizar esta solucao para outros casos?")
            frases.append("Matome: dominio solido. Proximo nivel.")

    elif inspiracao == "singapura_cpa":
        frases.append("Concreto: a aplicacao pratica esta funcional?")
        if pct < 0.5:
            frases.append("Pictorico: o modelo mental (diagrama, esquema) precisa ser revisto.")
            frases.append("Abstrato: ainda nao e possivel generalizar — volte ao concreto.")
        elif pct < 0.8:
            frases.append("Pictorico: o modelo mental esta razoavel — refine a representacao.")
            frases.append("Abstrato: tente extrair o padrao geral antes de avancar.")
        else:
            frases.append("Pictorico: representacao clara e consistente.")
            frases.append("Abstrato: voce consegue formular uma regra geral? Otimo.")

    elif inspiracao == "tad_mesogenese":
        frases.append("Milieu: o ambiente de aprendizado foi adequado?")
        if pct < 0.5:
            frases.append("Investigacao: a exploracao foi superficial — aprofunde.")
            frases.append("Institucionalizacao: o conhecimento ainda nao foi internalizado.")
        elif pct < 0.8:
            frases.append("Investigacao: boa exploracao — mas faltou conectar com o meio.")
            frases.append("Institucionalizacao: tente formalizar o que descobriu.")
        else:
            frases.append("Investigacao: exploracao profunda e significativa.")
            frases.append("Institucionalizacao: conhecimento consolidado e aplicavel.")

    elif inspiracao == "lesson_study":
        frases.append("Planejar: a preparacao foi adequada ao objetivo?")
        if pct < 0.5:
            frases.append("Executar: a execucao precisa ser revista — gaps fundamentais.")
            frases.append("Observar: reflita sobre o que nao funcionou.")
            frases.append("Refletir: o ciclo precisa ser reiniciado com novo planejamento.")
        elif pct < 0.8:
            frases.append("Executar: execucao boa — poucos ajustes.")
            frases.append("Observar: identifique os pontos de melhoria especificos.")
            frases.append("Refletir: iteracao produtiva — refine na proxima.")
        else:
            frases.append("Executar: execucao solida e bem fundamentada.")
            frases.append("Observar: poucos ou nenhum ajuste necessario.")
            frases.append("Refletir: ciclo concluido com sucesso. Avance.")

    return frases

# ─── DATACLASSES ─────────────────────────────────────────────────────────────

@dataclass
class Competencia:
    nome: str
    pontuacao: float = 0.0
    tentativas: int = 0
    ultima_avaliacao: str = ""

@dataclass
class Materia:
    assunto: str
    nivel: str = "fundamental"
    metodologia: str = "personalizada"
    inspiracao: str = ""
    competencias: Dict[str, Competencia] = field(default_factory=dict)
    historico_avaliacoes: List[Dict[str, Any]] = field(default_factory=list)
    exemplos_expert: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class Aluno:
    nome: str = "Ravena"
    materias: Dict[str, Materia] = field(default_factory=dict)
    nivel_geral: str = "fundamental"

# ─── PROFESSOR ───────────────────────────────────────────────────────────────

class Professor:
    def __init__(self, caminho_persistencia: Optional[str] = None):
        self.aluno = Aluno()
        self.metodologia_por_assunto: Dict[str, str] = {}
        self.inspiracao_por_assunto: Dict[str, str] = {}
        self.caminho_persistencia = caminho_persistencia or _ARQUIVO_PERSISTENCIA
        self._erros_consecutivos: Dict[str, int] = {}
        self._ultimo_topico_testado: Dict[str, str] = {}
        self._anomalias: List[Dict[str, Any]] = []
        self._carregar()
        logger.info("Professor ativo — ensinando Ravena")

    # ── GESTAO DE METODOLOGIA E INSPIRACAO ──

    def definir_metodologia(self, assunto: str, metodologia: str, inspiracao: str = ""):
        if metodologia not in METODOLOGIAS:
            raise ValueError(f"Metodologia desconhecida: {metodologia}. Opcoes: {list(METODOLOGIAS.keys())}")
        if inspiracao and inspiracao not in INSPIRACOES:
            raise ValueError(f"Inspiracao desconhecida: {inspiracao}. Opcoes: {list(INSPIRACOES.keys())}")
        self.metodologia_por_assunto[assunto] = metodologia
        if inspiracao:
            self.inspiracao_por_assunto[assunto] = inspiracao
        self._garantir_materia(assunto)
        self._salvar()
        logger.info(f"Professor: {assunto} -> metodologia={metodologia}, inspiracao={inspiracao or 'default'}")

    def _get_metodologia(self, assunto: str) -> str:
        return self.metodologia_por_assunto.get(assunto, "personalizada")

    def _get_inspiracao(self, assunto: str) -> str:
        return self.inspiracao_por_assunto.get(assunto) or _INSPIRACAO_FALLBACK_ASSUNTO.get(assunto, _INSPIRACAO_PADRAO)

    # ── GESTAO DE MATERIA ──

    def _garantir_materia(self, assunto: str) -> Materia:
        if assunto not in self.aluno.materias:
            self.aluno.materias[assunto] = Materia(
                assunto=assunto,
                metodologia=self._get_metodologia(assunto),
                inspiracao=self._get_inspiracao(assunto)
            )
        return self.aluno.materias[assunto]

    # ── AVALIAR ──

    def avaliar(self, assunto: str, resposta: Dict[str, Any], criterios: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        materia = self._garantir_materia(assunto)
        metodologia = self._get_metodologia(assunto)
        inspiracao = self._get_inspiracao(assunto)

        criterios = criterios or self._criterios_padrao(assunto)
        total_itens = len(criterios)
        acertos = 0
        resultados_por_criterio = {}

        for criterio, peso in criterios.items():
            nota_criterio = self._avaliar_criterio(criterio, resposta, peso)
            resultados_por_criterio[criterio] = nota_criterio
            if nota_criterio >= peso * 0.7:
                acertos += 1

        nota = acertos / total_itens if total_itens > 0 else 0.0
        nota_percentual = round(nota * 100, 2)

        parecer = self._gerar_parecer_metodologia(metodologia, nota, acertos, total_itens)
        frases_inspiracao = _gerar_frases_inspiracao(inspiracao, assunto, acertos, total_itens)
        parecer.extend(frases_inspiracao)

        lacunas = [c for c, r in resultados_por_criterio.items() if r < 0.5]
        nivel = self._calcular_nivel(nota, assunto)

        avaliacao = {
            "timestamp": datetime.now().isoformat(),
            "assunto": assunto,
            "nota": nota_percentual,
            "parecer": parecer,
            "lacunas": lacunas,
            "nivel": nivel.value if isinstance(nivel, Nivel) else nivel,
            "metodologia": metodologia,
            "inspiracao": inspiracao,
            "resultados_por_criterio": resultados_por_criterio
        }

        materia.historico_avaliacoes.append(avaliacao)
        self._atualizar_competencias(assunto, resultados_por_criterio)
        self._atualizar_nivel_geral()
        self._salvar()

        return avaliacao

    def _criterios_padrao(self, assunto: str) -> Dict[str, float]:
        return {
            "precisao_tecnica": 1.0,
            "completude": 1.0,
            "clareza": 1.0,
            "fundamentacao": 1.0
        }

    def _avaliar_criterio(self, criterio: str, resposta: Dict[str, Any], peso: float) -> float:
        base = resposta.get(criterio, resposta.get("confianca", 0.5))
        if isinstance(base, bool):
            return peso if base else 0.0
        if isinstance(base, (int, float)):
            return min(base, 1.0) * peso
        return peso * 0.5

    def _gerar_parecer_metodologia(self, metodologia: str, nota: float, acertos: int, total: int) -> List[str]:
        linhas = []

        if metodologia == "mit":
            linhas.append(f"Mens et Manus: projeto {'solido' if nota >= 0.7 else 'em desenvolvimento'}.")
            if nota < 0.5:
                linhas.append("O projeto pratico precisa ser refeito — lacunas fundamentais.")
            elif nota < 0.8:
                linhas.append("Projeto funcional — refine a execucao pratica.")
            else:
                linhas.append("Projeto exemplar — pronto para aplicacao real.")

        elif metodologia == "harvard":
            linhas.append(f"Case Method: argumentacao {'consistente' if nota >= 0.7 else 'insuficiente'}.")
            if nota < 0.5:
                linhas.append("A analise do caso foi superficial — faltou profundidade.")
            elif nota < 0.8:
                linhas.append("Boa analise — mas poderia explorar cenarios alternativos.")
            else:
                linhas.append("Decisao bem fundamentada sob incerteza.")

        elif metodologia == "socratica":
            linhas.append(f"Mayeutica: questionamento {'produtivo' if nota >= 0.7 else 'incompleto'}.")
            if nota < 0.5:
                linhas.append("As respostas nao revelam compreensao — tente partir do basico.")
            elif nota < 0.8:
                linhas.append("Ha compreensao parcial — siga os porques.")
            else:
                linhas.append("O aluno chegou a verdade pelas proprias perguntas.")

        elif metodologia == "oxford":
            linhas.append(f"Tutorial: discussao {'critica' if nota >= 0.7 else 'rasa'}.")
            if nota < 0.5:
                linhas.append("O pensamento critico nao foi ativado — precisa de mais leitura.")
            elif nota < 0.8:
                linhas.append("Ha engajamento — mas o argumento precisa ser desafiado.")
            else:
                linhas.append("Discussao de alto nivel — pronta para publicacao.")

        elif metodologia == "carnegie":
            linhas.append(f"Mastery: dominio tecnico {'completo' if nota >= 0.7 else 'insuficiente'}.")
            if nota < 0.5:
                linhas.append("Dominio abaixo do minimo — revisar fundamentos antes de avancar.")
            elif nota < 0.8:
                linhas.append("Dominio parcial — alguns topicos precisam de reforco.")
            else:
                linhas.append("Dominio completo — apto para o proximo modulo.")

        else:
            linhas.append(f"Avaliacao personalizada: {acertos}/{total} criterios atendidos.")
            if nota < 0.5:
                linhas.append("Adaptacao necessaria: revisar abordagem de ensino.")
            elif nota < 0.8:
                linhas.append("Progresso consistente — continuar na direcao atual.")
            else:
                linhas.append("Excelente desempenho na abordagem personalizada.")

        return linhas

    def _calcular_nivel(self, nota: float, assunto: str) -> Nivel:
        materia = self.aluno.materias.get(assunto)
        if not materia:
            return Nivel.FUNDAMENTAL
        nivel_atual = Nivel(materia.nivel) if isinstance(materia.nivel, str) else materia.nivel
        indice = nivel_para_indice(nivel_atual)
        if nota >= 0.9 and indice < len(_ORDEM_NIVEIS) - 1:
            return _ORDEM_NIVEIS[indice + 1]
        if nota >= 0.7 and indice < len(_ORDEM_NIVEIS) - 1:
            return _ORDEM_NIVEIS[indice + 1]
        return nivel_atual

    def _atualizar_competencias(self, assunto: str, resultados: Dict[str, float]):
        materia = self.aluno.materias.get(assunto)
        if not materia:
            return
        for criterio, nota in resultados.items():
            if not isinstance(nota, (int, float)):
                continue
            if criterio not in materia.competencias:
                materia.competencias[criterio] = Competencia(nome=criterio)
            comp = materia.competencias[criterio]
            comp.pontuacao = (comp.pontuacao * comp.tentativas + nota) / (comp.tentativas + 1)
            comp.tentativas += 1
            comp.ultima_avaliacao = datetime.now().isoformat()

    # ── CORRIGIR ──

    def corrigir(self, assunto: str, resposta_original: Dict[str, Any], correcao_expert: Dict[str, Any]) -> Dict[str, Any]:
        materia = self._garantir_materia(assunto)
        exemplo = {
            "timestamp": datetime.now().isoformat(),
            "resposta_original": resposta_original,
            "correcao_expert": correcao_expert
        }
        materia.exemplos_expert.append(exemplo)

        # Feedback corretivo: ajusta competencias (apenas valores numericos)
        resultado_correcao = {}
        for criterio, valor in correcao_expert.items():
            if criterio.startswith("_"):
                continue
            if not isinstance(valor, (int, float)):
                continue
            resultado_correcao[criterio] = valor / 100.0 if isinstance(valor, (int, float)) and valor > 1 else valor

        if resultado_correcao:
            self._atualizar_competencias(assunto, resultado_correcao)

        self._salvar()
        logger.info(f"Professor: correcao registrada para {assunto}")
        return {
            "status": "correcao_registrada",
            "total_exemplos_expert": len(materia.exemplos_expert),
            "assunto": assunto
        }

    # ── ENSINAR ──

    def ensinar(self, assunto: str, topico: str, contexto: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        materia = self._garantir_materia(assunto)
        metodologia = self._get_metodologia(assunto)
        inspiracao = self._get_inspiracao(assunto)

        metadados_metodologia = METODOLOGIAS.get(metodologia, METODOLOGIAS["personalizada"])
        metadados_inspiracao = INSPIRACOES.get(inspiracao, INSPIRACOES[_INSPIRACAO_PADRAO])

        competencias = materia.competencias
        pontos_fracos = sorted(
            [c for c in competencias.values() if c.pontuacao < 0.6],
            key=lambda x: x.pontuacao
        )

        plano_aula = {
            "assunto": assunto,
            "topico": topico,
            "nivel": materia.nivel,
            "metodologia": {
                "nome": metadados_metodologia["nome"],
                "principio": metadados_metodologia["principio"],
                "foco": metadados_metodologia["foco"]
            },
            "inspiracao": {
                "nome": metadados_inspiracao["nome"],
                "descricao": metadados_inspiracao["descricao"],
                "fases": []
            },
            "competencias_alvo": [c.nome for c in competencias.values() if c.pontuacao < 0.7],
            "ponto_partida": "fundamentos" if not competencias else "reforco_seletivo",
        }

        for fase in metadados_inspiracao["fases"]:
            plano_aula["inspiracao"]["fases"].append({
                "fase": fase,
                "descricao": self._descrever_fase(fase, topico, assunto, pontos_fracos)
            })

        if pontos_fracos:
            plano_aula["recomendacao"] = f"Reforcar: {', '.join(p.nome for p in pontos_fracos[:3])}"

        return plano_aula

    def _descrever_fase(self, fase: str, topico: str, assunto: str, pontos_fracos: List[Competencia]) -> str:
        descricoes = {
            "hatsumon": f"Problema inicial: resolva este problema de {topico}.",
            "kikan_shido": f"Intervencao: observei seu raciocinio em {topico}. O que voce percebe?",
            "neriage": f"Discussao: compare sua solucao de {topico} com outra abordagem. O que muda?",
            "matome": f"Sintese: entao, qual o principio geral de {topico}?",
            "concreto": f"Manipulacao direta: execute {topico} com exemplos tangiveis.",
            "pictorico": f"Representacao: desenhe/diagrame o conceito de {topico}.",
            "abstrato": f"Generalizacao: formule uma regra ou padrao para {topico}.",
            "milieu": f"Ambiente: explore o problema de {topico} — que ferramentas estao a sua disposicao?",
            "investigacao": f"Investigacao: o que voce descobriu ao explorar {topico}?",
            "institucionalizacao": f"Formalizacao: sistematize o que aprendeu sobre {topico}.",
            "planejar": f"Planejamento: qual seu plano para abordar {topico}?",
            "executar": f"Execucao: implemente o plano para {topico}.",
            "observar": f"Observacao: analise o resultado da execucao de {topico}.",
            "refletir": f"Reflexao: O que funcionou? O que melhorar em {topico}?"
        }
        return descricoes.get(fase, f"Fase {fase}: explore {topico}.")

    # ── BOLETINS ──

    def boletim_core(self) -> Dict[str, Any]:
        boletim = {
            "aluno": self.aluno.nome,
            "nivel_geral": self.aluno.nivel_geral,
            "materias": {}
        }

        for assunto, materia in self.aluno.materias.items():
            historico = materia.historico_avaliacoes
            if not historico:
                boletim["materias"][assunto] = {
                    "nivel": materia.nivel,
                    "media": 0,
                    "total_avaliacoes": 0,
                    "ultima_avaliacao": None,
                    "metodologia": materia.metodologia,
                    "inspiracao": materia.inspiracao
                }
                continue

            notas = [a["nota"] for a in historico]
            boletim["materias"][assunto] = {
                "nivel": materia.nivel,
                "media": round(sum(notas) / len(notas), 2),
                "total_avaliacoes": len(historico),
                "ultima_avaliacao": historico[-1]["timestamp"],
                "ultima_nota": historico[-1]["nota"],
                "metodologia": materia.metodologia,
                "inspiracao": materia.inspiracao,
                "lacunas_recentes": historico[-1].get("lacunas", [])
            }

        return boletim

    def boletim_llm(self) -> Dict[str, Any]:
        total_exemplos = sum(len(m.exemplos_expert) for m in self.aluno.materias.values())
        pronto = total_exemplos >= 50
        return {
            "status": "pronto_para_fine_tuning" if pronto else "coletando_exemplos",
            "total_exemplos_expert": total_exemplos,
            "minimo_necessario": 50,
            "progresso_percentual": round(min(total_exemplos / 50 * 100, 100), 2),
            "materias": {
                assunto: len(m.exemplos_expert)
                for assunto, m in self.aluno.materias.items()
            }
        }

    # ── DIAGNOSTICO ──

    def diagnosticar(self) -> Dict[str, Any]:
        total_materias = len(self.aluno.materias)
        total_avaliacoes = sum(len(m.historico_avaliacoes) for m in self.aluno.materias.values())
        total_exemplos = sum(len(m.exemplos_expert) for m in self.aluno.materias.values())
        total_competencias = sum(len(m.competencias) for m in self.aluno.materias.values())

        return {
            "professor_ativo": True,
            "aluno": self.aluno.nome,
            "nivel_geral": self.aluno.nivel_geral,
            "materias_cadastradas": total_materias,
            "total_avaliacoes_realizadas": total_avaliacoes,
            "total_exemplos_expert": total_exemplos,
            "total_competencias_mapeadas": total_competencias,
            "metodologias_ativas": list(set(self.metodologia_por_assunto.values())),
            "inspiracoes_ativas": list(set(self.inspiracao_por_assunto.values())),
            "assuntos_por_metodologia": dict(self.metodologia_por_assunto),
            "assuntos_por_inspiracao": dict(self.inspiracao_por_assunto),
            "persistencia": self.caminho_persistencia
        }

    def _atualizar_nivel_geral(self):
        niveis = []
        for materia in self.aluno.materias.values():
            try:
                niveis.append(Nivel(materia.nivel))
            except ValueError:
                pass
        if niveis:
            indices = [nivel_para_indice(n) for n in niveis]
            self.aluno.nivel_geral = _ORDEM_NIVEIS[max(indices)].value

    # ── PERSISTENCIA ──




    # ── GERAR TESTE ──

    def gerar_teste(self, assunto: str, topico: str = "", variacao: int = 0) -> Dict[str, Any]:
        materia = self._garantir_materia(assunto)
        testes_assunto = _TESTES_PADRAO.get(assunto, {})
        testes_topico = testes_assunto.get(topico, [])
        testes_geral = testes_assunto.get("geral", [])

        if not testes_topico and not testes_geral:
            logger.warning(f"Sem testes para {assunto}/{topico}")
            return {"erro": f"Nenhum teste disponivel para {assunto}/{topico}"}

        testes = testes_topico if testes_topico else testes_geral
        indice = variacao % len(testes)
        pergunta, resposta_esperada = testes[indice]
        self._ultimo_topico_testado[assunto] = topico

        logger.info(f"Teste gerado: [{assunto}/{topico}] '{pergunta}' -> '{resposta_esperada}'")
        return {
            "assunto": assunto,
            "topico": topico,
            "pergunta": pergunta,
            "resposta_esperada": resposta_esperada,
            "variacao": indice,
            "total_testes": len(testes)
        }

    # ── VALIDAR RESPOSTA ──

    @staticmethod
    def _normalizar(texto: str) -> str:
        substituicoes = {
            "á": "a", "à": "a", "ã": "a", "â": "a",
            "é": "e", "ê": "e",
            "í": "i",
            "ó": "o", "ô": "o", "õ": "o",
            "ú": "u", "ü": "u",
            "ç": "c",
            "ñ": "n",
        }
        t = texto.lower().strip()
        for acentuada, sem in substituicoes.items():
            t = t.replace(acentuada, sem)
        return t

    @staticmethod
    def _distancia_levenshtein(a: str, b: str, max_dist: int = 2) -> bool:
        if abs(len(a) - len(b)) > max_dist:
            return False
        if a == b:
            return True
        dp = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            novo = [i] + [0] * len(b)
            for j, cb in enumerate(b, 1):
                custo = 0 if ca == cb else 1
                novo[j] = min(dp[j] + 1, novo[j-1] + 1, dp[j-1] + custo)
            dp = novo
        return dp[-1] <= max_dist

    def validar_resposta(self, pergunta: str, resposta_esperada: str, resposta_aluno: str) -> Dict[str, Any]:
        import re as _re
        ra = self._normalizar(resposta_aluno)
        re = self._normalizar(resposta_esperada)

        acertou = False

        # 1. Exato (apos normalizacao)
        if ra == re:
            acertou = True
        # 2. Sim/Nao — explicito ou implicito
        elif re in ("sim", "s"):
            if _re.search(r"\bsim\b", ra):
                acertou = True
            elif not _re.search(r"\bnao\b", ra):
                # Afirmacao implicita: resposta sem negacao conta como Sim
                acertou = True
        elif re in ("nao", "n", "não"):
            if _re.search(r"\bnao\b", ra):
                acertou = True
        # 3. Resposta contem o esperado (ex: "206" em "tem aproximadamente 206 ossos")
        elif re and re in ra:
            acertou = True
        # 4. Esperado contem a resposta OU Levenshtein
        elif re and (ra in re or Professor._distancia_levenshtein(ra, re, max_dist=2)):
            acertou = True
        # 5. Definicao longa para "O que e...": resposta explicativa > curta esperada
        if not acertou and pergunta.lower().startswith("o que e") and len(re) < 30 and len(ra) > 60:
            acertou = True

        # 6. Numerico: extrai numeros dos dois lados e compara se proximos
        if not acertou:
            def _extrair_numeros(texto):
                nums = []
                for m in _re.finditer(r"(\d+)\s*(mil|milhao|milhoes|bilhao|bilhoes)", texto):
                    base = float(m.group(1))
                    mult = {"mil": 1_000, "milhao": 1_000_000, "milhoes": 1_000_000,
                            "bilhao": 1_000_000_000, "bilhoes": 1_000_000_000}.get(m.group(2), 1)
                    nums.append(base * mult)
                texto_normalizado = _re.sub(r"(?<=\d)[.,](?=\d{3}[.,\s]|$)", "", texto)
                texto_normalizado = texto_normalizado.replace(",", ".")
                for m in _re.finditer(r"\d+(?:\.\d+)?", texto_normalizado):
                    nums.append(float(m.group()))
                return nums
            nums_ra = _extrair_numeros(ra)
            nums_re = _extrair_numeros(re)
            for nr in list(nums_ra):
                nums_ra.extend([nr * 1000, nr / 1000, nr / 1_000_000])
            if nums_ra and nums_re:
                for nr in nums_ra:
                    for ne in nums_re:
                        if abs(nr - ne) / max(ne, 1) < 0.15:
                            acertou = True
                            break
                    if acertou:
                        break
            # 6. Palavras significativas: se esperado tem 2+ tokens, verifica sobreposicao
            if not acertou:
                tokens_re = [t for t in re.split(r"\s+") if len(t) > 2]
                tokens_ra = set(ra.split())
                if len(tokens_re) >= 2:
                    iguais = sum(1 for t in tokens_re if t in tokens_ra)
                    if iguais / len(tokens_re) >= 0.4:
                        acertou = True
            # 7. Levenshtein em cada token do esperado
            if not acertou:
                tokens_re = [t for t in re.split() if len(t) > 0]
                tokens_ra = ra.split()
                for tr in tokens_re:
                    if len(tr) <= 2:
                        continue
                    for ta in tokens_ra:
                        if len(ta) <= 2:
                            continue
                        if Professor._distancia_levenshtein(tr, ta, max_dist=2):
                            acertou = True
                            break
                    if acertou:
                        break

        logger.info(f"Validacao: esperado='{resposta_esperada}', recebido='{resposta_aluno[:60]}' -> {'CORRETO' if acertou else 'ERRO'}")
        return {
            "acertou": acertou,
            "resposta_esperada": resposta_esperada,
            "resposta_recebida": resposta_aluno[:100],
            "pergunta": pergunta
        }

    # ── NOTIFICAR ANOMALIA ──

    def notificar_anomalia(self, assunto: str, topico: str, erros_consecutivos: int,
                          detalhes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        anomalia = {
            "timestamp": datetime.now().isoformat(),
            "assunto": assunto,
            "topico": topico,
            "erros_consecutivos": erros_consecutivos,
            "detalhes": detalhes or {},
        }
        self._anomalias.append(anomalia)
        logger.warning(f"ANOMALIA: {assunto}/{topico} acumulou {erros_consecutivos} erros consecutivos")
        self._salvar()
        return {
            "status": "anomalia_registrada",
            "anomalia": anomalia,
            "total_anomalias": len(self._anomalias)
        }

    # ── PERSISTENCIA (estendida) ──

    def _serializar(self) -> Dict[str, Any]:
        materias_dict = {}
        for assunto, materia in self.aluno.materias.items():
            comps = {k: asdict(v) for k, v in materia.competencias.items()}
            materias_dict[assunto] = {
                "assunto": materia.assunto,
                "nivel": materia.nivel,
                "metodologia": materia.metodologia,
                "inspiracao": materia.inspiracao,
                "competencias": comps,
                "historico_avaliacoes": materia.historico_avaliacoes,
                "exemplos_expert": materia.exemplos_expert
            }
        return {
            "aluno": {
                "nome": self.aluno.nome,
                "nivel_geral": self.aluno.nivel_geral,
                "materias": materias_dict
            },
            "metodologia_por_assunto": dict(self.metodologia_por_assunto),
            "inspiracao_por_assunto": dict(self.inspiracao_por_assunto),
            "erros_consecutivos": dict(self._erros_consecutivos),
            "anomalias": self._anomalias
        }

    def _carregar(self):
        if not os.path.exists(self.caminho_persistencia):
            logger.info("Nenhum estado anterior do Professor encontrado.")
            return
        try:
            with open(self.caminho_persistencia, "r", encoding="utf-8") as f:
                dados = json.load(f)
            aluno_data = dados.get("aluno", {})
            self.aluno.nome = aluno_data.get("nome", "Ravena")
            self.aluno.nivel_geral = aluno_data.get("nivel_geral", "fundamental")
            for assunto, m_data in aluno_data.get("materias", {}).items():
                comps = {}
                for c_nome, c_data in m_data.get("competencias", {}).items():
                    comps[c_nome] = Competencia(**c_data)
                materia = Materia(
                    assunto=m_data["assunto"],
                    nivel=m_data.get("nivel", "fundamental"),
                    metodologia=m_data.get("metodologia", "personalizada"),
                    inspiracao=m_data.get("inspiracao", ""),
                    competencias=comps,
                    historico_avaliacoes=m_data.get("historico_avaliacoes", []),
                    exemplos_expert=m_data.get("exemplos_expert", [])
                )
                self.aluno.materias[assunto] = materia
            self.metodologia_por_assunto = dados.get("metodologia_por_assunto", {})
            self.inspiracao_por_assunto = dados.get("inspiracao_por_assunto", {})
            self._erros_consecutivos = dados.get("erros_consecutivos", {})
            self._anomalias = dados.get("anomalias", [])
            logger.info(f"Estado do Professor carregado: {len(self.aluno.materias)} materias, {len(self._anomalias)} anomalias")
        except Exception as e:
            logger.warning(f"Erro ao carregar estado do Professor: {e}")
    def _salvar(self):
        try:
            os.makedirs(os.path.dirname(self.caminho_persistencia), exist_ok=True)
            with open(self.caminho_persistencia, "w", encoding="utf-8") as f:
                json.dump(self._serializar(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar estado do Professor: {e}")

    # ── REGISTRO DE TREINO ──

    _CAMINHO_TREINO_ERROS = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "treino", "erros.jsonl"
    )

    def registrar_resultado_treino(self, pergunta: str, resposta_esperada: str,
                                    resposta_modelo: str, acertou: bool,
                                    topico: str = ""):
        dados = {
            "pergunta": pergunta,
            "resposta_esperada": resposta_esperada,
            "resposta_modelo": resposta_modelo,
            "acertou": acertou,
            "topico": topico,
            "fonte": "pipeline",
            "timestamp": datetime.now().isoformat(),
        }
        try:
            os.makedirs(os.path.dirname(self._CAMINHO_TREINO_ERROS), exist_ok=True)
            with open(self._CAMINHO_TREINO_ERROS, "a", encoding="utf-8") as f:
                f.write(json.dumps(dados, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Erro ao registrar resultado de treino: {e}")

    def listar_anomalias(self) -> List[Dict[str, Any]]:
        return list(self._anomalias)


# ─── ALIAS (compatibilidade reversa) ─────────────────────────────────────────

FallbackInteligente = Professor
