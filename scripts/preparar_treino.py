"""
PREPARAR TREINO
===============
1. Coleta erros do pipeline
2. Gera parafrases (multiplas versoes da mesma pergunta)
3. Ingere fontes externas (Wikipedia, docs, etc)
4. Remove duplicatas
5. Exporta dataset formatado para fine-tuning
"""

import os
import sys
import json
import logging

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJETO_RAIZ)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("preparar")

from src.core.treinador import Treinador
from src.core.professor import Professor


def coletar_pipeline(t: Treinador):
    """Coleta todos os resultados do pipeline"""
    caminho = os.path.join(_PROJETO_RAIZ, "data", "pipeline_resultados.json")
    if not os.path.exists(caminho):
        logger.warning("Nenhum resultado de pipeline encontrado")
        return 0

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    resultados = dados.get("resultados", [])
    if not resultados:
        logger.warning("Pipeline sem resultados")
        return 0

    adicionados = t.coletar_pipeline(resultados)
    logger.info(f"{adicionados} exemplos do pipeline")
    return adicionados


def coletar_externas(t: Treinador):
    """Coleta de fontes externas via Alimentador"""
    adicionados = 0
    try:
        from src.core.alimentacao.alimentador import Alimentador
        from src.core.alimentacao.templates import GeradorPergunta

        alim = Alimentador(_PROJETO_RAIZ)
        gerador = GeradorPergunta()

        # Ingere documentos do core
        temas = ["ravena_core", "docs_pessoais", "base_tecnica"]
        for tema in temas:
            resultados = alim.ingerir_tema(tema, forcar=False)
            for res in resultados:
                if res.status != "ingerido":
                    continue

            logger.info(f"Tema '{tema}' ingerido via Alimentador")

        logger.info(f"Fontes externas: {adicionados} exemplos")
    except ImportError as e:
        logger.warning(f"Alimentador nao disponivel: {e}")
    except Exception as e:
        logger.warning(f"Erro ao coletar externas: {e}")

    return adicionados


def gerar_wikipedia_fatos() -> int:
    """Gera exemplos estruturados da Wikipedia via templates manuais"""
    caminho = os.path.join(_PROJETO_RAIZ, "data", "treino", "fontes_externas.jsonl")
    if os.path.exists(caminho) and os.path.getsize(caminho) > 1000:
        logger.info("fontes_externas.jsonl ja existe e contem dados")
        return 0

    FATOS = {
        "geografia": [
            ("Qual a capital da Argentina?", "Buenos Aires", "geografia/capitais"),
            ("Qual a capital do Canada?", "Ottawa", "geografia/capitais"),
            ("Qual o pais mais populoso do mundo?", "India", "geografia/paises"),
            ("Onde esta localizado o Rio Nilo?", "Africa", "geografia/geral"),
            ("Qual o maior deserto quente do mundo?", "Saara", "geografia/geral"),
            ("Quantos oceanos existem na Terra?", "5", "geografia/geral"),
            ("Qual o pais com mais habitantes da America do Sul?", "Brasil", "geografia/paises"),
        ],
        "ciencia": [
            ("Qual a formula quimica da agua?", "H2O", "ciencia/quimica"),
            ("Qual o planeta mais quente do sistema solar?", "Venus", "ciencia/astronomia"),
            ("Quantos cromossomos tem o ser humano?", "46", "ciencia/biologia"),
            ("Qual o musculo mais forte do corpo humano?", "Masseter", "ciencia/biologia"),
            ("A fotossintese produz oxigenio?", "Sim", "ciencia/biologia"),
            ("Qual o ponto de ebulicao da agua em Celsius?", "100", "ciencia/fisica"),
            ("O atomo e a menor parte de um elemento?", "Sim", "ciencia/quimica"),
        ],
        "historia": [
            ("Em que ano foi a Revolucao Francesa?", "1789", "historia/geral"),
            ("Quem foi o primeiro imperador do Brasil?", "Dom Pedro I", "historia/brasil"),
            ("O Brasil foi descoberto em 1500?", "Sim", "historia/brasil"),
            ("Quem descobriu a America?", "Cristovao Colombo", "historia/geral"),
            ("Em que ano caiu o Imperio Romano do Ocidente?", "476", "historia/antiga"),
        ],
        "tecnologia": [
            ("O que significa HTTP?", "Protocolo de Transferencia de Hipertexto", "tecnologia/geral"),
            ("O que e um banco de dados relacional?", "Banco que organiza dados em tabelas", "tecnologia/programacao"),
            ("O que e uma API?", "Interface de Programacao de Aplicacoes", "tecnologia/programacao"),
            ("Windows e um sistema operacional?", "Sim", "tecnologia/hardware"),
            ("Linux e um sistema operacional de codigo aberto?", "Sim", "tecnologia/hardware"),
        ],
        "lingua": [
            ("'Amor' e um substantivo abstrato?", "Sim", "lingua/gramatica"),
            ("'Lindo' e um adjetivo?", "Sim", "lingua/gramatica"),
            ("A palavra 'casa' tem quantas letras?", "4", "lingua/geral"),
            ("'Correndo' e uma forma nominal do verbo correr?", "Sim", "lingua/gramatica"),
        ],
        "cultura": [
            ("Qual o maior estadio do Brasil?", "Maracana", "cultura/geral"),
            ("A capoeira e uma arte marcial brasileira?", "Sim", "cultura/geral"),
            ("O frevo e um ritmo musical de Pernambuco?", "Sim", "cultura/geral"),
            ("Qual o livro mais vendido do mundo?", "Biblia", "cultura/geral"),
        ],
    }

    contador = 0
    with open(caminho, "w", encoding="utf-8") as f:
        for assunto, fatos in FATOS.items():
            for pergunta, resposta, topico in fatos:
                f.write(json.dumps({
                    "pergunta": pergunta,
                    "resposta_esperada": resposta,
                    "topico": topico,
                    "fonte": "wikipedia_template",
                }, ensure_ascii=False) + "\n")
                contador += 1

    logger.info(f"{contador} fatos da Wikipedia via templates em {caminho}")
    return contador


def main():
    logger.info("=" * 50)
    logger.info("PREPARANDO DATASET DE TREINO")
    logger.info("=" * 50)

    t = Treinador()
    logger.info(f"Existentes: {len(t.exemplos)}")
    logger.info(json.dumps(t.estatisticas(), indent=2, ensure_ascii=False))

    # 1. Pipeline errors
    coletar_pipeline(t)

    # 2. Wikipedia templates
    gerar_wikipedia_fatos()

    # 3. External JSONL
    t.coletar_jsonl(
        os.path.join(_PROJETO_RAIZ, "data", "treino", "fontes_externas.jsonl"),
        fonte="externa"
    )

    # 4. Augment
    antes = len(t.exemplos)
    t.aumentar(por_exemplo=3)
    depois = len(t.exemplos)
    logger.info(f"Aumentacao: {antes} -> {depois} ({depois - antes} novas)")

    # 5. Salvar
    caminho_erros = t.salvar_erros()
    caminho_formatado = t.preparar_dataset()

    # 6. Stats
    stats = t.estatisticas()
    logger.info("=" * 50)
    logger.info("RESUMO DO DATASET")
    logger.info(json.dumps(stats, indent=2, ensure_ascii=False))
    logger.info(f"Dataset formatado: {caminho_formatado}")
    logger.info(f"Erros salvos: {caminho_erros}")
    logger.info("=" * 50)

    return stats


if __name__ == "__main__":
    main()
