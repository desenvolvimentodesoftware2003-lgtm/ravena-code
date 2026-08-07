import os
import sys
import subprocess
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("ravena.tools")

_COMANDOS_PROIBIDOS = [
    "rm -rf /", "rm -rf ~", "rm -rf .",
    "sudo", "format", "chmod 777", "chmod -R 777",
    "dd if=", "mkfs", "fdisk", "shutdown", "reboot",
    "> /dev/sda", "| shutdown", "init 0", "init 6"
]

class RavenaTools:
    def __init__(self, root_path: Optional[str] = None):
        self._root = root_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logger.info(f"RavenaTools ativo — raiz: {self._root}")

    def _safe_path(self, path: str) -> str:
        caminho_absoluto = path if os.path.isabs(path) else os.path.normpath(os.path.join(self._root, path))
        caminho_real = os.path.realpath(caminho_absoluto)
        if not caminho_real.startswith(os.path.realpath(self._root)):
            raise PermissionError(f"Acesso negado: {path} esta fora da raiz do projeto")
        return caminho_real

    def ler(self, path: str) -> Tuple[bool, str]:
        try:
            caminho = self._safe_path(path)
            if not os.path.isfile(caminho):
                return False, f"Arquivo nao encontrado: {path}"
            with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                conteudo = f.read()
            return True, conteudo
        except PermissionError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro ao ler {path}: {e}"

    def escrever(self, path: str, conteudo: str) -> Tuple[bool, str]:
        try:
            caminho = self._safe_path(path)
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(conteudo)
            logger.info(f"Arquivo escrito: {path}")
            return True, f"Arquivo {path} atualizado."
        except PermissionError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Erro ao escrever {path}: {e}"

    def listar(self, directory: str = ".") -> Tuple[bool, List[str]]:
        try:
            caminho = self._safe_path(directory)
            if not os.path.isdir(caminho):
                return False, [f"Diretorio nao encontrado: {directory}"]
            conteudos = os.listdir(caminho)
            return True, conteudos
        except PermissionError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Erro ao listar {directory}: {e}"]

    def executar(self, comando: str, timeout: int = 30) -> Dict[str, Any]:
        for proibido in _COMANDOS_PROIBIDOS:
            if proibido in comando.lower():
                logger.warning(f"Comando bloqueado: {comando[:80]}")
                return {
                    "sucesso": False,
                    "stdout": "",
                    "stderr": f"Comando bloqueado por seguranca: '{proibido}' nao permitido",
                    "exit_code": -1
                }
        try:
            logger.info(f"Executando: {comando[:120]}")
            resultado = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self._root
            )
            return {
                "sucesso": resultado.returncode == 0,
                "stdout": resultado.stdout,
                "stderr": resultado.stderr,
                "exit_code": resultado.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "sucesso": False,
                "stdout": "",
                "stderr": f"Comando excedeu timeoute limite de {timeout}s",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "sucesso": False,
                "stdout": "",
                "stderr": f"Erro ao executar comando: {e}",
                "exit_code": -1
            }

    def validar_comando(self, comando: str) -> Tuple[bool, str]:
        for proibido in _COMANDOS_PROIBIDOS:
            if proibido in comando.lower():
                return False, f"Comando contem operacao proibida: '{proibido}'"
        if not comando or not comando.strip():
            return False, "Comando vazio"
        return True, "ok"


if __name__ == "__main__":
    tools = RavenaTools()
    print(f"Raiz: {tools._root}")

    sucesso, conteudo = tools.ler("config/omega_config.json")
    print(f"Ler config: {'OK' if sucesso else 'FALHA'} ({len(conteudo) if sucesso else 0} chars)")

    sucesso, arquivos = tools.listar("src/core")
    print(f"Listar src/core: {'OK' if sucesso else 'FALHA'} -> {len(arquivos)} arquivos")

    resultado = tools.executar("echo teste")

    print(f"Executar echo: {'OK' if resultado['sucesso'] else 'FALHA'} -> {resultado['stdout'].strip()}")

    valido, msg = tools.validar_comando("rm -rf /")
    print(f"Validar 'rm -rf /': {'BLOQUEADO' if not valido else 'PERMITIDO'} ({msg})")
