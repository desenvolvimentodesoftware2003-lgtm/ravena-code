"""
STEP SCALING — Grade de Seguranca para Posicoes (v1.0.0)
==========================================================
Ravena AIM | Modulo: execucao inteligente
Baseado no conceito de Step Scaling com Martingale suave.
Responsabilidades:
  - Apos sinal aprovado, abre posicao a mercado
  - Pendura ordens limitadas em grade para proteger a posicao
  - Aumenta lote progressivamente (1.5x) para melhorar preco medio
  - Segue Zero Trust: todas as operacoes via SecretsManager
"""

import logging
import time
import os
import sys
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from core.secrets_manager import secrets

logger = logging.getLogger("ravena.step_scaling")


@dataclass
class EscalaPasso:
    nivel: int
    lado: str
    quantidade: float
    preco: float
    status: str = "pendente"


class StepScaling:
    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        self._session = None
        logger.info(f"StepScaling v1.0.0 inicializado (testnet={testnet}).")

    @property
    def _bybit(self):
        if self._session is None:
            from pybit.unified_trading import HTTP
            api_key = secrets.get("BYBIT_API_KEY", required=False)
            api_secret = secrets.get("BYBIT_API_SECRET", required=False)
            modo = secrets.get("BYBIT_MODE", required=False)
            is_demo = modo == "demo"
            self._session = HTTP(
                testnet=self.testnet or is_demo,
                api_key=api_key or "",
                api_secret=api_secret or "",
            )
        return self._session

    def obter_preco_atual(self, simbolo: str) -> Optional[float]:
        try:
            ticker = self._bybit.get_tickers(category="linear", symbol=simbolo)
            return float(ticker["result"]["list"][0]["lastPrice"])
        except Exception as e:
            logger.error(f"Erro ao obter preco de {simbolo}: {e}")
            return None

    def abrir_posicao(self, simbolo: str, lado: str, quantidade: float) -> bool:
        try:
            resp = self._bybit.place_order(
                category="linear",
                symbol=simbolo,
                side=lado.capitalize(),
                orderType="Market",
                qty=quantidade,
            )
            ret = resp.get("retCode", -1)
            if ret == 0:
                logger.info(f"Posicao aberta: {lado} {quantidade} {simbolo}")
                return True
            logger.error(f"Falha ao abrir posicao: {resp.get('retMsg', 'erro')}")
            return False
        except Exception as e:
            logger.error(f"Erro ao abrir posicao {simbolo}: {e}")
            return False

    def pendurar_grade(
        self,
        simbolo: str,
        lado: str,
        preco_entrada: float,
        lote_inicial: float,
        num_passos: int = 3,
        dist_percentual: float = 0.01,
        multiplicador: float = 1.5,
    ) -> List[EscalaPasso]:
        """
        Pendura ordens limitadas em grade.
        - lado: 'buy' ou 'sell'
        - Se buy: ordens abaixo do preco (preco medio melhora)
        - Se sell: ordens acima do preco
        - lote aumenta 1.5x a cada passo (martingale suave)
        """
        passos = []
        is_buy = lado.lower() == "buy"

        for i in range(1, num_passos + 1):
            tamanho = round(lote_inicial * (multiplicador**i), 4)
            if is_buy:
                preco_step = round(preco_entrada * (1 - dist_percentual * i), 2)
                side = "Buy"
            else:
                preco_step = round(preco_entrada * (1 + dist_percentual * i), 2)
                side = "Sell"

            try:
                resp = self._bybit.place_order(
                    category="linear",
                    symbol=simbolo,
                    side=side,
                    orderType="Limit",
                    qty=tamanho,
                    price=preco_step,
                    timeInForce="GTC",
                )
                if resp.get("retCode") == 0:
                    logger.info(f"Step {i}: {side} {tamanho} @ {preco_step}")
                    passos.append(EscalaPasso(i, side, tamanho, preco_step, "pendente"))
                else:
                    logger.warning(f"Step {i} falhou: {resp.get('retMsg', '')}")
                    passos.append(EscalaPasso(i, side, tamanho, preco_step, "erro"))
            except Exception as e:
                logger.error(f"Erro no step {i}: {e}")
                passos.append(EscalaPasso(i, side, tamanho, preco_step, "erro"))

            time.sleep(0.3)

        return passos

    def executar_estrategia(
        self,
        simbolo: str,
        lado: str,
        lote_base: float,
        num_passos: int = 3,
        dist_percentual: float = 0.01,
    ) -> Dict[str, Any]:
        preco = self.obter_preco_atual(simbolo)
        if not preco:
            return {"status": "ERRO", "motivo": "Preco nao disponivel"}

        ok = self.abrir_posicao(simbolo, lado, lote_base)
        if not ok:
            return {"status": "ERRO", "motivo": "Falha ao abrir posicao"}

        passos = self.pendurar_grade(simbolo, lado, preco, lote_base, num_passos, dist_percentual)
        return {
            "status": "EXECUTADO",
            "simbolo": simbolo,
            "lado": lado,
            "lote_base": lote_base,
            "preco_entrada": preco,
            "passos": [{"nivel": p.nivel, "lado": p.lado, "qty": p.quantidade, "preco": p.preco, "status": p.status} for p in passos],
            "timestamp": time.time(),
        }


if __name__ == "__main__":
    print("StepScaling v1.0.0 carregado. Use executar_estrategia() para testar.")
