import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("ravena.cognitive_sensors")

class CognitiveSensor:
    def __init__(self, caminho_jsonl: Optional[str] = None):
        _projeto_raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self._caminho = caminho_jsonl or os.path.join(_projeto_raiz, "data", "cognitive_treino.jsonl")
        self._sessao_id = str(uuid.uuid4())[:8]
        self._contador = 0
        os.makedirs(os.path.dirname(self._caminho), exist_ok=True)
        logger.info(f"CognitiveSensor ativo — sessao {self._sessao_id} -> {self._caminho}")

    def capturar(self, pergunta: str, raciocinio: str, resposta: str,
                 confianca: float = 0.0, fonte: str = "conhecimento_interno",
                 estado_crenca: str = "ativo", authority_score: float = 0.0,
                 origem: str = "usuario", score_ameaca: float = 0.0,
                 diagnostico_extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._contador += 1
        entrada = {
            "timestamp": datetime.now().isoformat(),
            "sessao_id": self._sessao_id,
            "interacao_id": self._contador,
            "pergunta": pergunta,
            "raciocinio": raciocinio,
            "resposta": resposta,
            "confianca": round(confianca, 4),
            "fonte": fonte,
            "estado_crenca": estado_crenca,
            "authority_score": round(authority_score, 4),
            "origem": origem,
            "score_ameaca": round(score_ameaca, 4)
        }
        if diagnostico_extra:
            for chave in ("modulos_usados", "tempo_total_ms", "ciclos_pensamento"):
                if chave in diagnostico_extra:
                    entrada[chave] = diagnostico_extra[chave]
        try:
            with open(self._caminho, "a", encoding="utf-8") as f:
                f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Erro ao escrever JSONL: {e}")
        return entrada

    def exportar_para_treino(self, caminho_saida: Optional[str] = None,
                             formato: str = "jsonl") -> str:
        caminho_saida = caminho_saida or self._caminho.replace(".jsonl", "_treino.jsonl")
        if not os.path.exists(self._caminho):
            logger.warning("Nenhum dado para exportar")
            return ""
        with open(self._caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        with open(caminho_saida, "w", encoding="utf-8") as f:
            for linha in linhas:
                dado = json.loads(linha)
                entrada_treino = {
                    "instruction": dado.get("pergunta", ""),
                    "reasoning": dado.get("raciocinio", ""),
                    "response": dado.get("resposta", ""),
                    "confidence": dado.get("confianca", 0.0),
                    "source": dado.get("fonte", ""),
                    "belief_state": dado.get("estado_crenca", ""),
                    "authority": dado.get("authority_score", 0.0)
                }
                f.write(json.dumps(entrada_treino, ensure_ascii=False) + "\n")
        logger.info(f"Exportado {len(linhas)} interacoes para treino -> {caminho_saida}")
        return caminho_saida

    def estatisticas(self) -> Dict[str, Any]:
        if not os.path.exists(self._caminho):
            return {"total": 0}
        with open(self._caminho, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        total = len(linhas)
        fontes: Dict[str, int] = {}
        estados: Dict[str, int] = {}
        confiancas = []
        for linha in linhas:
            try:
                dado = json.loads(linha)
                fonte = dado.get("fonte", "desconhecida")
                fontes[fonte] = fontes.get(fonte, 0) + 1
                estado = dado.get("estado_crenca", "desconhecido")
                estados[estado] = estados.get(estado, 0) + 1
                confiancas.append(dado.get("confianca", 0))
            except json.JSONDecodeError:
                continue
        return {
            "total": total,
            "sessao_id": self._sessao_id,
            "fontes": fontes,
            "estados": estados,
            "confianca_media": round(sum(confiancas) / len(confiancas), 4) if confiancas else 0.0
        }

    def limpar(self):
        if os.path.exists(self._caminho):
            os.remove(self._caminho)
        self._contador = 0
        logger.info("Dados cognitivos limpos")


if __name__ == "__main__":
    import json

    sensor = CognitiveSensor()
    sensor.capturar(
        pergunta="qual e a capital do brasil",
        raciocinio="Contexto recuperado de usuario: Brasilia",
        resposta="Brasilia",
        confianca=0.95,
        fonte="usuario",
        estado_crenca="ativo",
        authority_score=0.9,
        diagnostico_extra={"modulos_usados": ["conhecimento", "pensar"], "tempo_total_ms": 3.5}
    )
    sensor.capturar(
        pergunta="o que e python",
        raciocinio="Contexto recuperado de aprendizado: linguagem de programacao",
        resposta="Python e uma linguagem de programacao interpretada",
        confianca=0.7,
        fonte="aprendizado",
        diagnostico_extra={"modulos_usados": ["conhecimento", "pensar"], "tempo_total_ms": 2.1}
    )

    print("=== ESTATISTICAS ===")
    print(json.dumps(sensor.estatisticas(), indent=2, ensure_ascii=False))

    print()
    print("=== EXPORTAR PARA TREINO ===")
    caminho = sensor.exportar_para_treino()
    with open(caminho, "r") as f:
        for linha in f.readlines()[:2]:
            print(json.loads(linha))

    sensor.limpar()
