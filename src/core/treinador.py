import os
import re
import json
import copy
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("ravena.treinador")

_PROJETO_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_CAMINHO_ERROS = os.path.join(_PROJETO_RAIZ, "data", "treino", "erros.jsonl")
_CAMINHO_EXTERNAS = os.path.join(_PROJETO_RAIZ, "data", "treino", "fontes_externas.jsonl")
_CAMINHO_FORMATADO = os.path.join(_PROJETO_RAIZ, "data", "treino", "treino_formatado.jsonl")
_CAMINHO_CHECKPOINT = os.path.join(_PROJETO_RAIZ, "data", "treino", "checkpoint")

_TEMPLATES_PARAFRASE = {
    "capital": [
        "Qual a capital de {entidade}?",
        "Capital de {entidade}:",
        "{entidade} tem qual capital?",
        "Qual cidade e a capital de {entidade}?",
        "Diga a capital de {entidade}.",
        "{entidade}, qual sua capital?",
    ],
    "descobriu": [
        "Quem descobriu {entidade}?",
        "{entidade} foi descoberto por quem?",
        "Qual o descobridor de {entidade}?",
        "Quem foi que descobriu {entidade}?",
        "A descoberta de {entidade} foi feita por quem?",
        "Quem e o explorador que descobriu {entidade}?",
    ],
    "continente": [
        "{entidade} fica em qual continente?",
        "Qual o continente de {entidade}?",
        "{entidade} esta localizado em que continente?",
        "De que continente e {entidade}?",
    ],
    "localizacao": [
        "Onde fica {entidade}?",
        "{entidade} esta localizado onde?",
        "Qual a localizacao de {entidade}?",
    ],
    "orgao": [
        "Qual orgao do corpo {funcao}?",
        "Que orgao e responsavel por {funcao}?",
        "O orgao que {funcao} e qual?",
        "Qual parte do corpo {funcao}?",
        "Nomeie o orgao que {funcao}.",
    ],
    "ferve": [
        "A agua ferve a quantos graus?",
        "Qual a temperatura de ebulicao da agua ao nivel do mar?",
        "A agua ferve a 100 graus Celsius ao nivel do mar?",
        "Em que temperatura a agua ferve ao nivel do mar?",
    ],
    "velocidade": [
        "Qual a velocidade da luz no vacuo?",
        "A luz viaja a que velocidade no vacuo?",
        "Quantos km por segundo e a velocidade da luz?",
        "Qual o valor exato da velocidade da luz no vacuo?",
    ],
    "capital_para_pais": [
        "Brasilia",
        "Paris",
        "Toquio",
        "Londres",
        "Washington",
        "Buenos Aires",
        "Lisboa",
        "Madri",
        "Roma",
        "Berlim",
    ],
    "categoria_verbo": {
        "descobriu": "descobriu",
        "e": "e",
        "sao": "sao",
        "faz": "faz",
        "tem": "tem",
        "fica": "fica",
        "bombeia": "bombeia",
        "ferve": "ferve",
    },
}

_SYSTEM_PROMPT_RAVENA = (
    "Voce e a Ravena, uma assistente objetiva e tecnica. "
    "Seja direta. Responda apenas com a informacao solicitada, sem rodeios."
)


@dataclass
class ExemploTreino:
    pergunta: str
    resposta_esperada: str
    topico: str = ""
    fonte: str = "pipeline"
    resposta_modelo: str = ""
    acertou: bool = False

    def para_chat(self) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": _SYSTEM_PROMPT_RAVENA},
            {"role": "user", "content": self.pergunta},
            {"role": "assistant", "content": self.resposta_esperada},
        ]

    def __hash__(self):
        return hash((self.pergunta.lower().strip(), self.resposta_esperada.lower().strip()))

    def __eq__(self, other):
        if not isinstance(other, ExemploTreino):
            return False
        return (self.pergunta.lower().strip() == other.pergunta.lower().strip()
                and self.resposta_esperada.lower().strip() == other.resposta_esperada.lower().strip())


class Treinador:
    def __init__(self):
        self.exemplos: List[ExemploTreino] = []
        self._carregar_existentes()

    # ─── COLETA ────────────────────────────────────────────────────────────────

    def coletar_pipeline(self, pipeline_resultados: List[Dict[str, Any]]) -> int:
        adicionados = 0
        for r in pipeline_resultados:
            ex = ExemploTreino(
                pergunta=r["pergunta"],
                resposta_esperada=r["esperado"],
                topico=r.get("topico", ""),
                fonte="pipeline",
                resposta_modelo=r.get("recebido", ""),
                acertou=r.get("acertou", False),
            )
            if ex not in self.exemplos:
                self.exemplos.append(ex)
                adicionados += 1
        logger.info(f"Coletados {adicionados} novos exemplos do pipeline")
        return adicionados

    def coletar_jsonl(self, caminho: str, fonte: str = "externa") -> int:
        if not os.path.exists(caminho):
            logger.warning(f"Arquivo nao encontrado: {caminho}")
            return 0
        adicionados = 0
        with open(caminho, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                try:
                    dados = json.loads(linha)
                except json.JSONDecodeError:
                    continue
                pergunta = dados.get("pergunta") or dados.get("instruction") or dados.get("question", "")
                resposta = dados.get("resposta_esperada") or dados.get("output") or dados.get("answer", "")
                if not pergunta or not resposta:
                    continue
                ex = ExemploTreino(
                    pergunta=pergunta.strip(),
                    resposta_esperada=resposta.strip(),
                    topico=dados.get("topico", ""),
                    fonte=fonte,
                )
                if ex not in self.exemplos:
                    self.exemplos.append(ex)
                    adicionados += 1
        logger.info(f"Coletados {adicionados} exemplos de {caminho}")
        return adicionados

    # ─── AUMENTACAO ───────────────────────────────────────────────────────────

    def _categoria_para_templates(self, pergunta: str) -> List[str]:
        pl = pergunta.lower()
        if re.search(r"capital\s+(d[eo]s?|d(a|o))?\s+\w+", pl) or re.search(r"capital d", pl):
            return _TEMPLATES_PARAFRASE["capital"]
        if re.search(r"(quem|descobriu|descobridor)", pl):
            return _TEMPLATES_PARAFRASE["descobriu"]
        if re.search(r"(fica|continente|localizado)", pl):
            return _TEMPLATES_PARAFRASE["continente"] + _TEMPLATES_PARAFRASE["localizacao"]
        if re.search(r"(orgao|bombeia|cora)", pl):
            return _TEMPLATES_PARAFRASE["orgao"]
        if re.search(r"(ferve|ebulicao|100 graus)", pl):
            return _TEMPLATES_PARAFRASE["ferve"]
        if re.search(r"(velocidade da luz)", pl):
            return _TEMPLATES_PARAFRASE["velocidade"]
        return []

    def _extrair_entidade(self, pergunta: str) -> Optional[str]:
        pl = pergunta.lower()
        m = re.search(r"(capital\s+d[eo]s?\s+)(.+)", pl)
        if m:
            return m.group(2).strip().rstrip("?")
        m = re.search(r"(descobriu\s+)(.+)", pl)
        if m:
            return m.group(2).strip().rstrip("?")
        m = re.search(r"(fica\s+no?\s+|localizado\s+no?\s+|continente\s+d[eo]s?\s+)(.+)", pl)
        if m:
            return m.group(2).strip().rstrip("?")
        return None

    def _extrair_funcao(self, pergunta: str) -> Optional[str]:
        pl = pergunta.lower()
        m = re.search(r"orgao\s+(do corpo\s+)?(que|responsavel por)\s+(.+)", pl)
        if m:
            return m.group(3).strip().rstrip("?")
        m = re.search(r"(bombeia|faz o sangue circular|responsavel por)\s+(.+)", pl)
        if m:
            return m.group(2).strip().rstrip("?")
        return None

    def _gerar_parafrases(self, ex: ExemploTreino) -> List[ExemploTreino]:
        parafrases = []
        templates = self._categoria_para_templates(ex.pergunta)

        if templates:
            entidade = self._extrair_entidade(ex.pergunta)
            funcao = self._extrair_funcao(ex.pergunta)

            for tmpl in templates:
                if entidade and "{entidade}" in tmpl:
                    nova_pergunta = tmpl.replace("{entidade}", entidade)
                elif funcao and "{funcao}" in tmpl:
                    nova_pergunta = tmpl.replace("{funcao}", funcao)
                else:
                    continue

                novo = ExemploTreino(
                    pergunta=nova_pergunta,
                    resposta_esperada=ex.resposta_esperada,
                    topico=ex.topico,
                    fonte="aumentacao:" + ex.fonte,
                )
                if novo not in self.exemplos and novo not in parafrases:
                    parafrases.append(novo)

        return parafrases

    def aumentar(self, por_exemplo: int = 3) -> int:
        novos = []
        for ex in self.exemplos:
            parafrases = self._gerar_parafrases(ex)
            for pf in parafrases[:por_exemplo]:
                if pf not in self.exemplos and pf not in novos:
                    novos.append(pf)
        self.exemplos.extend(novos)
        logger.info(f"Aumentacao: {len(novos)} novas parafrases geradas (total: {len(self.exemplos)})")
        return len(novos)

    # ─── PREPARACAO ───────────────────────────────────────────────────────────

    def preparar_dataset(self, caminho_saida: str = None) -> str:
        caminho_saida = caminho_saida or _CAMINHO_FORMATADO
        vistos = set()
        with open(caminho_saida, "w", encoding="utf-8") as f:
            for ex in self.exemplos:
                chat = ex.para_chat()
                chave = json.dumps(chat, ensure_ascii=False)
                if chave in vistos:
                    continue
                vistos.add(chave)
                f.write(json.dumps({"messages": chat, "fonte": ex.fonte}, ensure_ascii=False) + "\n")
        logger.info(f"Dataset formatado salvo em {caminho_saida} ({len(vistos)} exemplos)")
        return caminho_saida

    # ─── PERSISTENCIA ─────────────────────────────────────────────────────────

    def salvar_erros(self, caminho: str = None) -> str:
        caminho = caminho or _CAMINHO_ERROS
        vistos = set()
        with open(caminho, "w", encoding="utf-8") as f:
            for ex in self.exemplos:
                chave = f"{ex.pergunta}|{ex.resposta_esperada}"
                if chave in vistos:
                    continue
                vistos.add(chave)
                f.write(json.dumps({
                    "pergunta": ex.pergunta,
                    "resposta_esperada": ex.resposta_esperada,
                    "topico": ex.topico,
                    "fonte": ex.fonte,
                    "resposta_modelo": ex.resposta_modelo,
                    "acertou": ex.acertou,
                }, ensure_ascii=False) + "\n")
        logger.info(f"{len(vistos)} exemplos salvos em {caminho}")
        return caminho

    def _carregar_existentes(self):
        for caminho in [_CAMINHO_ERROS, _CAMINHO_EXTERNAS]:
            if os.path.exists(caminho):
                self.coletar_jsonl(caminho, fonte=os.path.basename(caminho).replace(".jsonl", ""))

    def estatisticas(self) -> Dict[str, Any]:
        acertos = sum(1 for ex in self.exemplos if ex.acertou)
        erros = sum(1 for ex in self.exemplos if not ex.acertou and ex.resposta_modelo)
        sem_resposta = sum(1 for ex in self.exemplos if not ex.resposta_modelo)
        fontes = {}
        for ex in self.exemplos:
            fontes[ex.fonte] = fontes.get(ex.fonte, 0) + 1
        topicos = {}
        for ex in self.exemplos:
            if ex.topico:
                topicos[ex.topico] = topicos.get(ex.topico, 0) + 1
        return {
            "total_exemplos": len(self.exemplos),
            "unicos": len({json.dumps(ex.para_chat(), ensure_ascii=False) for ex in self.exemplos}),
            "acertos": acertos,
            "erros": erros,
            "sem_resposta_modelo": sem_resposta,
            "fontes": fontes,
            "topicos": topicos,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    t = Treinador()
    print(json.dumps(t.estatisticas(), indent=2, ensure_ascii=False))
