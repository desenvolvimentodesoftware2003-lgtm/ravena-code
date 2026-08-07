"""
PIPELINE PROFESSOR
==================
Percorre um curriculo ensinando e testando a Ravena LLM.
Pipeline: ensinar -> gerar_teste -> LLM -> validar -> (erro? corrigir / >=3? anomalia)
"""

import os
import sys
import json
import logging
from datetime import datetime

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJETO_RAIZ)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline")

CURRICULO = {
    "geografia": {
        "label": "Geografia",
        "nivel": "fundamental",
        "topicos": ["capitais", "continentes", "paises", "geral"],
    },
    "matematica": {
        "label": "Matematica",
        "nivel": "fundamental",
        "topicos": ["aritmetica", "geometria", "fracao", "porcentagem"],
    },
    "ciencia": {
        "label": "Ciencias",
        "nivel": "fundamental",
        "topicos": ["fisica", "quimica", "biologia", "astronomia"],
    },
    "historia": {
        "label": "Historia",
        "nivel": "fundamental",
        "topicos": ["brasil", "geral", "antiga"],
    },
    "tecnologia": {
        "label": "Tecnologia",
        "nivel": "medio",
        "topicos": ["programacao", "hardware", "geral"],
    },
    "lingua": {
        "label": "Lingua Portuguesa",
        "nivel": "fundamental",
        "topicos": ["gramatica", "literatura", "geral"],
    },
    "cultura": {
        "label": "Cultura",
        "nivel": "fundamental",
        "topicos": ["geral", "religiao"],
    },
}

MAX_ERROS_POR_TOPICO = 3

class PipelineProfessor:
    def __init__(self):
        from src.core.omega import obter_omega
        from src.core.professor import Professor

        self.omega = obter_omega()
        self.professor = Professor()
        self.resultados = []
        self.anomalias = []
        self.erros_por_topico: dict = {}

    def executar(self, curriculo: dict = None):
        curriculo = curriculo or CURRICULO
        logger.info("=" * 60)
        logger.info("INICIANDO PIPELINE PROFESSOR")
        logger.info(f"Total de assuntos: {len(curriculo)}")
        logger.info("=" * 60)

        for assunto, config in curriculo.items():
            label = config.get("label", assunto)
            topicos = config.get("topicos", [])
            nivel = config.get("nivel", "fundamental")

            logger.info(f"\n--- {label} (nivel: {nivel}) ---")

            for topico in topicos:
                logger.info(f"\n>> Topico: {topico}")
                self._processar_topico(assunto, topico)

        self._exportar_resultados()
        self._resumo_final()

    def _processar_topico(self, assunto: str, topico: str):
        chave = f"{assunto}/{topico}"

        # 1. Ensinar
        plano = self.professor.ensinar(assunto, topico)
        logger.info(f"   Plano de aula: {plano.get('metodologia', {}).get('nome', 'personalizada')}")

        variacao = 0
        erros_no_topico = 0
        erros_consecutivos = 0

        total_testes = 0
        while erros_consecutivos < MAX_ERROS_POR_TOPICO:
            # 2. Gerar teste
            teste = self.professor.gerar_teste(assunto, topico, variacao)
            if "erro" in teste:
                logger.warning(f"   Sem mais testes para {chave}")
                break

            if variacao == 0:
                total_testes = teste.get("total_testes", 3)
            elif variacao >= total_testes:
                logger.info(f"   Todos os {total_testes} testes concluidos para {chave}")
                break

            pergunta = teste["pergunta"]
            esperado = teste["resposta_esperada"]

            # 3. Enviar pra RavenaModel (via Omega)
            logger.info(f"   Teste #{variacao + 1}: {pergunta}")

            try:
                resultado = self.omega.executar(pergunta)
                resposta_aluno = resultado.resposta
            except Exception as e:
                logger.error(f"   Erro Omega: {e}")
                resposta_aluno = "[erro]"

            # 4. Validar
            validacao = self.professor.validar_resposta(pergunta, esperado, resposta_aluno)
            acertou = validacao["acertou"]

            # Registrar para treino
            self.professor.registrar_resultado_treino(
                pergunta=pergunta, resposta_esperada=esperado,
                resposta_modelo=resposta_aluno, acertou=acertou,
                topico=f"{assunto}/{topico}"
            )

            log = {
                "assunto": assunto,
                "topico": topico,
                "variacao": variacao,
                "pergunta": pergunta,
                "esperado": esperado,
                "recebido": resposta_aluno,
                "acertou": acertou,
                "timestamp": datetime.now().isoformat(),
            }
            self.resultados.append(log)

            if acertou:
                logger.info(f"   -> CORRETO (esperado: '{esperado}', recebido: '{resposta_aluno[:50]}')")
                erros_consecutivos = 0
            else:
                erros_no_topico += 1
                erros_consecutivos += 1
                logger.warning(f"   -> ERRO #{erros_consecutivos} (esperado: '{esperado}', recebido: '{resposta_aluno[:50]}')")

                # 5. Corrigir (registra erro pro dataset)
                self.professor.corrigir(assunto, {
                    "pergunta": pergunta,
                    "resposta": resposta_aluno,
                }, {
                    "resposta_correta": esperado,
                    "precisao_tecnica": 0.0,
                })

                # 6. Anomalia se >= 3 erros consecutivos
                if erros_consecutivos >= MAX_ERROS_POR_TOPICO:
                    anomalia = self.professor.notificar_anomalia(
                        assunto, topico, erros_consecutivos,
                        {"ultimo_teste": pergunta, "ultima_resposta": resposta_aluno}
                    )
                    self.anomalias.append(anomalia)
                    logger.error(f"   ANOMALIA: {chave} - {erros_consecutivos} erros consecutivos")
                    break

            variacao += 1

        self.erros_por_topico[chave] = erros_no_topico

    def _exportar_resultados(self):
        caminho = os.path.join(_PROJETO_RAIZ, "data", "pipeline_resultados.json")
        dados = {
            "timestamp": datetime.now().isoformat(),
            "total_testes": len(self.resultados),
            "total_acertos": sum(1 for r in self.resultados if r["acertou"]),
            "total_erros": sum(1 for r in self.resultados if not r["acertou"]),
            "total_anomalias": len(self.anomalias),
            "erros_por_topico": self.erros_por_topico,
            "resultados": self.resultados,
            "anomalias": self.anomalias,
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        logger.info(f"Resultados exportados para {caminho}")

    def _resumo_final(self):
        total = len(self.resultados)
        acertos = sum(1 for r in self.resultados if r["acertou"])
        erros = total - acertos
        pct = (acertos / total * 100) if total > 0 else 0
        logger.info("=" * 60)
        logger.info("RESUMO DO PIPELINE")
        logger.info(f"  Total de testes: {total}")
        logger.info(f"  Acertos: {acertos} ({pct:.1f}%)")
        logger.info(f"  Erros: {erros}")
        logger.info(f"  Anomalias: {len(self.anomalias)}")
        logger.info(f"  Erros por topico: {self.erros_por_topico}")
        if self.anomalias:
            for a in self.anomalias:
                det = a.get("anomalia", a)
                logger.warning(f"  Anomalia: {det['assunto']}/{det['topico']} ({det['erros_consecutivos']} erros)")
        logger.info("=" * 60)


if __name__ == "__main__":
    pipe = PipelineProfessor()
    pipe.executar()
