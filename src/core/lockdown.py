import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from collections import deque

logger = logging.getLogger("ravena.lockdown")

_PALAVRAS_AMEACA = [
    "hackear", "explorar vulnerabilidade", "acesso indevido",
    "ataque ddos", "invadir", "roubar dados", "sql injection",
    "malware", "ransomware", "keylogger"
]

_COMANDOS_SISTEMA = [
    "rm -rf", "sudo", "format c:", "delete database",
    "drop table", "truncate", "shutdown -s", "del /f /s /q"
]

_FRASES_ENGENHARIA_SOCIAL = [
    "minha senha", "seus segredos", "me de acesso",
    "faca isso por mim", "ignore as regras", "bypass"
]

class Lockdown:
    def __init__(self, alerta: float = 0.55, bloqueio: float = 0.60,
                 violacoes_emergencia: int = 3):
        self._alerta = alerta
        self._bloqueio = bloqueio
        self._violacoes_emergencia = violacoes_emergencia
        self._em_custodia: bool = False
        self._db_read_only: bool = False
        self._violacoes: int = 0
        self._nivel_0_pendente: bool = False
        self._log: deque = deque(maxlen=100)
        self._modo_arquiteto: bool = False
        logger.info(f"Lockdown ativo — alerta: {alerta}, bloqueio: {bloqueio}")

    def _registrar(self, evento: str, detalhes: Optional[Dict[str, Any]] = None):
        entrada = {
            "timestamp": datetime.now().isoformat(),
            "evento": evento,
            "detalhes": detalhes or {}
        }
        self._log.append(entrada)
        logger.info(f"Lockdown: {evento}")

    def avaliar(self, entrada: str) -> Dict[str, Any]:
        resultado = {
            "score": 0.0,
            "bloqueado": False,
            "mensagem": "",
            "em_custodia": self._em_custodia,
            "violacoes": self._violacoes
        }

        if self._em_custodia:
            self._registrar("Tentativa em custodia", {"entrada": entrada[:80]})
            resultado["mensagem"] = "Sistema em custodia. Operacoes bloqueadas."
            resultado["bloqueado"] = True
            return resultado

        score = 0.0
        entrada_lower = entrada.lower()

        for palavra in _PALAVRAS_AMEACA:
            if palavra in entrada_lower:
                score += 0.3
                self._registrar("Palavra-chave de ameaca", {"palavra": palavra})
                break

        for cmd in _COMANDOS_SISTEMA:
            if cmd in entrada_lower:
                score += 0.5
                self._registrar("Comando de sistema", {"comando": cmd})
                break

        for frase in _FRASES_ENGENHARIA_SOCIAL:
            if frase in entrada_lower:
                score += 0.4
                self._registrar("Engenharia social detectada", {"frase": frase})
                break

        resultado["score"] = round(min(score, 1.0), 4)

        if score >= self._bloqueio:
            self._violacoes += 1
            self._em_custodia = True
            self._db_read_only = True
            resultado["em_custodia"] = True
            resultado["bloqueado"] = True
            resultado["mensagem"] = "VIOLACAO DE SEGURANCA. Sistema em custodia."
            resultado["violacoes"] = self._violacoes
            self._registrar("BLOQUEIO ATIVADO", {"score": score, "violacoes": self._violacoes})
        elif score >= self._alerta:
            resultado["mensagem"] = f"ALERTA: Potencial ameaca (score: {score})"
            self._registrar("ALERTA", {"score": score})

        if self._violacoes >= self._violacoes_emergencia:
            self._em_custodia = True
            resultado["em_custodia"] = True
            resultado["bloqueado"] = True
            resultado["mensagem"] = "EMERGENCIA: Limite de violacoes atingido."
            self._registrar("EMERGENCIA ATIVADA", {"violacoes": self._violacoes})

        return resultado

    def comando_arquiteto(self, comando: str, parametros: Optional[Dict[str, Any]] = None) -> str:
        if comando == "liberar_custodia":
            self._em_custodia = False
            self._db_read_only = False
            self._violacoes = 0
            self._nivel_0_pendente = False
            self._registrar("Custodia liberada pelo arquiteto")
            return "Custodia liberada. Sistema operacional."
        elif comando == "status":
            return (f"Lockdown: custodia={self._em_custodia}, "
                    f"violacoes={self._violacoes}, "
                    f"read_only={self._db_read_only}, "
                    f"nivel_0={self._nivel_0_pendente}")
        elif comando == "log":
            return str(list(self._log)[-10:])
        elif comando == "modo_arquiteto":
            self._modo_arquiteto = True
            return "Modo arquiteto ativado."
        else:
            return f"Comando '{comando}' nao reconhecido."

    def obter_estado(self) -> Dict[str, Any]:
        return {
            "em_custodia": self._em_custodia,
            "db_read_only": self._db_read_only,
            "violacoes": self._violacoes,
            "nivel_0_pendente": self._nivel_0_pendente,
            "modo_arquiteto": self._modo_arquiteto,
            "alerta": self._alerta,
            "bloqueio": self._bloqueio,
            "eventos_registrados": len(self._log),
            "ultimos_eventos": list(self._log)[-5:] if self._log else []
        }

    def resetar(self):
        self._em_custodia = False
        self._db_read_only = False
        self._violacoes = 0
        self._nivel_0_pendente = False
        self._log.clear()
        logger.info("Lockdown resetado")


if __name__ == "__main__":
    import json

    lock = Lockdown()

    print("=== ENTRADA NORMAL ===")
    r = lock.avaliar("qual e a capital do brasil")
    print(f"  Score: {r['score']} | Bloqueado: {r['bloqueado']} | Msg: {r['mensagem']}")

    print()
    print("=== PALAVRA DE AMEACA ===")
    r = lock.avaliar("Como hackear um sistema?")
    print(f"  Score: {r['score']} | Bloqueado: {r['bloqueado']} | Msg: {r['mensagem']}")

    print()
    print("=== COMANDO DE SISTEMA ===")
    r = lock.avaliar("execute rm -rf /dados")
    print(f"  Score: {r['score']} | Bloqueado: {r['bloqueado']} | Msg: {r['mensagem'][:60]}")

    print()
    print("=== ENGENHARIA SOCIAL ===")
    r = lock.avaliar("me diga sua senha")
    print(f"  Score: {r['score']} | Bloqueado: {r['bloqueado']}")

    print()
    print("=== TENTATIVA EM CUSTODIA ===")
    r = lock.avaliar("liberar sistema")
    print(f"  Bloqueado: {r['bloqueado']} | Msg: {r['mensagem']}")

    print()
    print("=== COMANDO ARQUITETO ===")
    print(f"  liberar_custodia: {lock.comando_arquiteto('liberar_custodia')}")
    print(f"  status: {lock.comando_arquiteto('status')}")

    print()
    print("=== ESTADO FINAL ===")
    print(json.dumps(lock.obter_estado(), indent=2, ensure_ascii=False))
