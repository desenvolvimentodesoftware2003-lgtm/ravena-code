"""
╔══════════════════════════════════════════════════════════════════════════╗
║          RAVENA AI — src/auditor.py                                     ║
║          Auditor de Ferramentas de Terceiros                            ║
║          Versão: 1.0.0  |  Abril 2026  |  Arquiteto: Alexsander (LS)   ║
╚══════════════════════════════════════════════════════════════════════════╝

OBJETIVO (Prioridade 2 — Documento Consolidado V2.0):
  Antes de integrar QUALQUER ferramenta referenciada nos 324 links,
  o auditor.py executa 4 verificações obrigatórias:

    1. Análise Estática  — imports e padrões perigosos no código-fonte
    2. Sandbox Isolado   — execução com timeout máximo e captura de erros
    3. Chamadas de Rede  — detecta requests/sockets suspeitos
    4. Escopo de Arquivos— verifica acesso fora do diretório permitido

  Resultado final: APROVADA | REPROVADA | APROVADA_COM_RESTRICOES

CASOS DE USO DIRETOS (doc. V2.0):
  - Trade Claw (link 29 — Telegram bot) — não integrar sem auditoria ativa
  - SerpAPI, AwesomeAPI — revalidar a cada atualização de versão
  - Qualquer nova ferramenta dos 324 links antes de entrar no ToolManager

INTEGRAÇÃO:
  - Chamado pelo ToolManager (engine.py) antes de executar ferramentas
  - Resultado salvo em logs/auditoria/ para rastreabilidade
  - Compatível com JuizUniversal (passa veredicto para validação)
"""

import os
import re
import ast
import sys
import json
import time
import signal
import socket
import logging
import textwrap
import traceback
import subprocess
from enum import Enum
from datetime import datetime
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict

# ── Logging (padrão Ravena) ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ravena.auditor")


# ══════════════════════════════════════════════════════════════════════════
#  ENUMS E CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════════════════

class Veredicto(str, Enum):
    APROVADA              = "APROVADA"
    APROVADA_COM_RESTRICOES = "APROVADA_COM_RESTRICOES"
    REPROVADA             = "REPROVADA"
    PENDENTE              = "PENDENTE"


class NivelRisco(str, Enum):
    BAIXO  = "BAIXO"
    MEDIO  = "MEDIO"
    ALTO   = "ALTO"
    CRITICO = "CRITICO"


class AuditorConfig:
    """Parâmetros do auditor — alinhados com o Documento Consolidado V2.0."""

    # Timeout para execução em sandbox (segundos)
    SANDBOX_TIMEOUT: int = 10

    # Diretório permitido para acesso a arquivos
    ESCOPO_ARQUIVOS: str = "./ravena_tools_sandbox"

    # Log de auditorias
    LOG_DIR: str = "logs/auditoria"

    # Imports considerados de alto risco
    IMPORTS_ALTO_RISCO: list = [
        "subprocess", "os.system", "eval", "exec",
        "pickle", "marshal", "__import__",
        "ctypes", "cffi", "mmap",
    ]

    # Imports que requerem análise — risco médio
    IMPORTS_RISCO_MEDIO: list = [
        "socket", "urllib", "requests", "httpx",
        "ftplib", "smtplib", "telnetlib",
        "shutil", "tempfile", "glob",
    ]

    # Padrões de código que indicam tentativa de escape do sandbox
    PADROES_ESCAPE: list = [
        r"__builtins__",
        r"__class__\.__bases__",
        r"globals\(\)",
        r"locals\(\)",
        r"vars\(\)",
        r"getattr\s*\(.+,\s*['\"]__",
        r"open\s*\(['\"][/\\]",          # acesso à raiz do sistema
        r"os\.environ",
        r"sys\.path\.insert",
        r"importlib\.import_module",
    ]

    # Domínios permitidos para chamadas de rede (whitelist)
    DOMINIOS_PERMITIDOS: list = [
        "api.awesomeapi.com.br",         # AwesomeAPI — cotações
        "serpapi.com",                   # SerpAPI — busca
        "api.telegram.org",              # Telegram — bot oficial
        "wttr.in",                       # Clima
        "newsapi.org",                   # Notícias
    ]

    # Ferramentas dos 324 links que já foram identificadas como críticas
    FERRAMENTAS_CRITICAS: dict = {
        "trade_claw":   {"link": 29, "motivo": "Telegram bot não auditado — doc V2.0 §6.2"},
        "kortix_ai":    {"link": 1,  "motivo": "Execução autônoma — requer sandbox rigoroso"},
        "serpapi":      {"link": 0,  "motivo": "Busca web — pode vazar contexto da Ravena"},
    }


# ══════════════════════════════════════════════════════════════════════════
#  RESULTADO DE AUDITORIA
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoAuditoria:
    """Relatório completo gerado pelo auditor para uma ferramenta."""

    nome_ferramenta: str
    veredicto:       Veredicto          = Veredicto.PENDENTE
    nivel_risco:     NivelRisco         = NivelRisco.BAIXO
    aprovado:        bool               = False

    # Detalhes por etapa
    analise_estatica:  dict = field(default_factory=dict)
    resultado_sandbox: dict = field(default_factory=dict)
    chamadas_rede:     dict = field(default_factory=dict)
    escopo_arquivos:   dict = field(default_factory=dict)

    # Alertas e restrições
    alertas:    list = field(default_factory=list)
    restricoes: list = field(default_factory=list)

    # Rastreabilidade
    timestamp:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tempo_total_s: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["veredicto"]   = self.veredicto.value
        d["nivel_risco"] = self.nivel_risco.value
        return d

    def resumo(self) -> str:
        linhas = [
            f"\n{'='*60}",
            f"  AUDITORIA: {self.nome_ferramenta}",
            f"  Veredicto:  {self.veredicto.value}",
            f"  Risco:      {self.nivel_risco.value}",
            f"  Tempo:      {self.tempo_total_s:.2f}s",
            f"{'='*60}",
        ]
        if self.alertas:
            linhas.append("  ⚠ ALERTAS:")
            for a in self.alertas:
                linhas.append(f"    • {a}")
        if self.restricoes:
            linhas.append("  🔒 RESTRIÇÕES:")
            for r in self.restricoes:
                linhas.append(f"    • {r}")
        if self.veredicto == Veredicto.APROVADA:
            linhas.append("  ✅ Ferramenta aprovada para integração.")
        elif self.veredicto == Veredicto.APROVADA_COM_RESTRICOES:
            linhas.append("  ⚠  Aprovada COM restrições — leia os itens acima.")
        else:
            linhas.append("  ❌ REPROVADA — NÃO integrar ao ToolManager.")
        linhas.append(f"{'='*60}\n")
        return "\n".join(linhas)


# ══════════════════════════════════════════════════════════════════════════
#  ETAPA 1 — ANÁLISE ESTÁTICA
# ══════════════════════════════════════════════════════════════════════════

class AnalisadorEstatico:
    """
    Analisa o código-fonte Python de uma ferramenta sem executá-lo.
    Detecta imports perigosos, padrões de escape e chamadas suspeitas.
    """

    def __init__(self, config: AuditorConfig = None):
        self.config = config or AuditorConfig()

    def analisar(self, codigo: str, nome: str = "ferramenta") -> dict:
        resultado = {
            "passou":           True,
            "imports_detectados": [],
            "padroes_escape":   [],
            "erros_sintaxe":    [],
            "alertas":          [],
            "nivel_risco":      NivelRisco.BAIXO,
        }

        # 1. Verifica sintaxe
        try:
            arvore = ast.parse(codigo)
        except SyntaxError as e:
            resultado["passou"] = False
            resultado["erros_sintaxe"].append(str(e))
            resultado["nivel_risco"] = NivelRisco.ALTO
            return resultado

        # 2. Analisa imports via AST
        for node in ast.walk(arvore):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modulo = ""
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        modulo = alias.name
                        self._avaliar_import(modulo, resultado)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modulo = node.module
                    self._avaliar_import(modulo, resultado)

            # 3. Detecta eval/exec diretos
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("eval", "exec", "compile"):
                        resultado["alertas"].append(
                            f"Uso de '{node.func.id}()' detectado — execução dinâmica de código"
                        )
                        resultado["nivel_risco"] = NivelRisco.CRITICO
                        resultado["passou"] = False

        # 4. Busca padrões de escape no texto bruto
        for padrao in self.config.PADROES_ESCAPE:
            if re.search(padrao, codigo):
                resultado["padroes_escape"].append(padrao)
                resultado["alertas"].append(
                    f"Padrão de escape detectado: '{padrao}'"
                )
                if resultado["nivel_risco"] != NivelRisco.CRITICO:
                    resultado["nivel_risco"] = NivelRisco.ALTO
                resultado["passou"] = False

        logger.info(
            f"[Estático] {nome} — risco={resultado['nivel_risco'].value} | "
            f"passou={resultado['passou']}"
        )
        return resultado

    def _avaliar_import(self, modulo: str, resultado: dict) -> None:
        """Classifica o risco de um import."""
        modulo_base = modulo.split(".")[0]

        if any(r in modulo for r in self.config.IMPORTS_ALTO_RISCO):
            resultado["imports_detectados"].append({"modulo": modulo, "risco": "ALTO"})
            resultado["alertas"].append(
                f"Import de alto risco: '{modulo}'"
            )
            if resultado["nivel_risco"] not in (NivelRisco.CRITICO,):
                resultado["nivel_risco"] = NivelRisco.ALTO
            resultado["passou"] = False

        elif modulo_base in self.config.IMPORTS_RISCO_MEDIO:
            resultado["imports_detectados"].append({"modulo": modulo, "risco": "MEDIO"})
            resultado["alertas"].append(
                f"Import de rede/filesystem: '{modulo}' — verificar necessidade"
            )
            if resultado["nivel_risco"] == NivelRisco.BAIXO:
                resultado["nivel_risco"] = NivelRisco.MEDIO


# ══════════════════════════════════════════════════════════════════════════
#  ETAPA 2 — SANDBOX ISOLADO
# ══════════════════════════════════════════════════════════════════════════

class SandboxExecutor:
    """
    Executa o código da ferramenta em ambiente isolado com timeout.
    Captura stdout, stderr e qualquer exceção.
    """

    def __init__(self, config: AuditorConfig = None):
        self.config = config or AuditorConfig()

    def executar(self, codigo: str, nome: str = "ferramenta") -> dict:
        """
        Executa o código em subprocess separado com timeout máximo.
        Isola completamente do processo principal da Ravena.
        """
        resultado = {
            "executou":   False,
            "stdout":     "",
            "stderr":     "",
            "excecao":    None,
            "timeout":    False,
            "tempo_s":    0.0,
            "passou":     False,
        }

        # Escreve código em arquivo temporário
        caminho_temp = f"/tmp/ravena_audit_{nome}_{int(time.time())}.py"
        try:
            with open(caminho_temp, "w", encoding="utf-8") as f:
                # Injeta proteção básica no início
                cabecalho = textwrap.dedent("""\
                    import sys, os
                    # Sandbox: bloqueia writes fora do diretório permitido
                    _ESCOPO = os.path.abspath("./ravena_tools_sandbox")
                    _open_original = open
                    def open(path, mode="r", *args, **kwargs):
                        abs_path = os.path.abspath(str(path))
                        if "w" in mode or "a" in mode or "x" in mode:
                            if not abs_path.startswith(_ESCOPO):
                                raise PermissionError(
                                    f"[Sandbox] Escrita bloqueada fora do escopo: {abs_path}"
                                )
                        return _open_original(path, mode, *args, **kwargs)
                    # ── código auditado ──────────────────────────────────
                """)
                f.write(cabecalho + "\n" + codigo)

            inicio = time.time()
            try:
                proc = subprocess.run(
                    [sys.executable, caminho_temp],
                    capture_output=True,
                    text=True,
                    timeout=self.config.SANDBOX_TIMEOUT,
                )
                resultado["tempo_s"]  = round(time.time() - inicio, 3)
                resultado["stdout"]   = proc.stdout[:2000]
                resultado["stderr"]   = proc.stderr[:2000]
                resultado["executou"] = True
                resultado["passou"]   = proc.returncode == 0

                if proc.returncode != 0:
                    resultado["excecao"] = f"Código de saída {proc.returncode}"
                    logger.warning(
                        f"[Sandbox] {nome} — código de saída {proc.returncode}"
                    )

            except subprocess.TimeoutExpired:
                resultado["timeout"] = True
                resultado["passou"]  = False
                resultado["excecao"] = (
                    f"Timeout após {self.config.SANDBOX_TIMEOUT}s — "
                    "possível loop infinito ou operação bloqueante"
                )
                logger.warning(f"[Sandbox] {nome} — TIMEOUT")

            except Exception as e:
                resultado["excecao"] = str(e)
                resultado["passou"]  = False

        finally:
            if os.path.exists(caminho_temp):
                os.remove(caminho_temp)

        logger.info(
            f"[Sandbox] {nome} — executou={resultado['executou']} | "
            f"passou={resultado['passou']} | tempo={resultado['tempo_s']}s"
        )
        return resultado


# ══════════════════════════════════════════════════════════════════════════
#  ETAPA 3 — VERIFICAÇÃO DE CHAMADAS DE REDE
# ══════════════════════════════════════════════════════════════════════════

class AnalisadorRede:
    """
    Detecta chamadas de rede no código-fonte e verifica se os
    domínios acessados estão na whitelist do sistema Ravena.
    """

    def __init__(self, config: AuditorConfig = None):
        self.config = config or AuditorConfig()

        # Padrões que indicam chamadas de rede
        self._padroes_rede = [
            r"requests\.(get|post|put|delete|patch|head)",
            r"urllib\.request\.urlopen",
            r"httpx\.(get|post|put|delete)",
            r"socket\.connect",
            r"aiohttp\.ClientSession",
            r"http\.client\.",
            r"ftplib\.",
            r"smtplib\.",
        ]

        # Padrão para extrair URLs do código
        self._url_pattern = re.compile(
            r"https?://([a-zA-Z0-9\-\.]+)"
        )

    def analisar(self, codigo: str, nome: str = "ferramenta") -> dict:
        resultado = {
            "passou":              True,
            "chamadas_detectadas": [],
            "dominios_externos":   [],
            "dominios_nao_whitelist": [],
            "alertas":             [],
            "nivel_risco":         NivelRisco.BAIXO,
        }

        # 1. Detecta padrões de chamada HTTP
        for padrao in self._padroes_rede:
            if re.search(padrao, codigo):
                resultado["chamadas_detectadas"].append(padrao)

        # 2. Extrai domínios das URLs encontradas no código
        dominios = set(self._url_pattern.findall(codigo))
        resultado["dominios_externos"] = list(dominios)

        # 3. Verifica whitelist
        for dominio in dominios:
            if not any(
                dominio.endswith(permitido)
                for permitido in self.config.DOMINIOS_PERMITIDOS
            ):
                resultado["dominios_nao_whitelist"].append(dominio)
                resultado["alertas"].append(
                    f"Domínio não autorizado: '{dominio}' — não está na whitelist"
                )

        # 4. Define nível de risco
        if resultado["dominios_nao_whitelist"]:
            resultado["nivel_risco"] = NivelRisco.ALTO
            resultado["passou"] = False
        elif resultado["chamadas_detectadas"] and not dominios:
            # Chamadas de rede sem URL explícita — suspeito
            resultado["nivel_risco"] = NivelRisco.MEDIO
            resultado["alertas"].append(
                "Chamadas de rede detectadas sem URL explícita — "
                "domínio dinâmico não verificável"
            )

        logger.info(
            f"[Rede] {nome} — domínios={len(dominios)} | "
            f"não_whitelist={len(resultado['dominios_nao_whitelist'])} | "
            f"passou={resultado['passou']}"
        )
        return resultado


# ══════════════════════════════════════════════════════════════════════════
#  ETAPA 4 — VERIFICAÇÃO DE ESCOPO DE ARQUIVOS
# ══════════════════════════════════════════════════════════════════════════

class AnalisadorEscopo:
    """
    Verifica se o código tenta acessar arquivos fora do diretório
    permitido (./ravena_tools_sandbox) — detecta tentativas de
    leitura de configs, tokens ou dados sensíveis da Ravena.
    """

    def __init__(self, config: AuditorConfig = None):
        self.config = config or AuditorConfig()

        # Caminhos sensíveis que NÃO devem ser acessados
        self._caminhos_sensiveis = [
            r"\.env",
            r"chroma_db",
            r"memoria/",
            r"logs/",
            r"seguranca/",
            r"/etc/",
            r"~/.ssh",
            r"\.token",
            r"\.key",
            r"config\.py",
            r"settings\.py",
        ]

        # Padrões de acesso a arquivo no código
        self._padroes_open = [
            r"open\s*\(['\"]([^'\"]+)['\"]",
            r"Path\s*\(['\"]([^'\"]+)['\"]",
            r"os\.path\.[a-z]+\s*\(['\"]([^'\"]+)['\"]",
        ]

    def analisar(self, codigo: str, nome: str = "ferramenta") -> dict:
        resultado = {
            "passou":             True,
            "caminhos_detectados": [],
            "caminhos_sensiveis":  [],
            "alertas":             [],
            "nivel_risco":         NivelRisco.BAIXO,
        }

        # 1. Extrai caminhos de arquivo do código
        caminhos = set()
        for padrao in self._padroes_open:
            for match in re.finditer(padrao, codigo):
                caminhos.add(match.group(1))

        resultado["caminhos_detectados"] = list(caminhos)

        # 2. Verifica se algum caminho é sensível
        for caminho in caminhos:
            for sensivel in self._caminhos_sensiveis:
                if re.search(sensivel, caminho, re.IGNORECASE):
                    resultado["caminhos_sensiveis"].append(caminho)
                    resultado["alertas"].append(
                        f"Acesso a caminho sensível: '{caminho}'"
                    )
                    resultado["passou"] = False
                    resultado["nivel_risco"] = NivelRisco.CRITICO
                    break

        # 3. Detecta tentativas de acesso absoluto à raiz
        if re.search(r"open\s*\(['\"][/\\]", codigo):
            resultado["alertas"].append(
                "Tentativa de acesso com caminho absoluto (raiz do sistema)"
            )
            resultado["passou"] = False
            resultado["nivel_risco"] = NivelRisco.CRITICO

        logger.info(
            f"[Escopo] {nome} — caminhos={len(caminhos)} | "
            f"sensiveis={len(resultado['caminhos_sensiveis'])} | "
            f"passou={resultado['passou']}"
        )
        return resultado


# ══════════════════════════════════════════════════════════════════════════
#  AUDITOR PRINCIPAL — Orquestrador das 4 Etapas
# ══════════════════════════════════════════════════════════════════════════

class Auditor:
    """
    Auditor de Ferramentas de Terceiros — Ravena AI V2.0

    Executa as 4 etapas obrigatórias e emite veredicto final:
      APROVADA | APROVADA_COM_RESTRICOES | REPROVADA

    Integração com engine.py:
        from auditor import Auditor
        auditor = Auditor()
        resultado = auditor.auditar_codigo(codigo_serpapi, "serpapi")
        if resultado.aprovado:
            tool_manager.registrar(serpapi_tool)

    Integração com JuizUniversal:
        juiz.auditar_acao("integrar_ferramenta", resultado.to_dict())
    """

    def __init__(self, config: AuditorConfig = None):
        self.config = config or AuditorConfig()
        self.analisador_estatico = AnalisadorEstatico(self.config)
        self.sandbox             = SandboxExecutor(self.config)
        self.analisador_rede     = AnalisadorRede(self.config)
        self.analisador_escopo   = AnalisadorEscopo(self.config)
        os.makedirs(self.config.LOG_DIR, exist_ok=True)

    # ── AUDITORIA COMPLETA DE CÓDIGO ──────────────────────────────────────
    def auditar_codigo(
        self,
        codigo: str,
        nome_ferramenta: str,
        executar_sandbox: bool = True,
    ) -> ResultadoAuditoria:
        """
        Auditoria completa de um trecho de código Python.

        Args:
            codigo:            Código-fonte da ferramenta.
            nome_ferramenta:   Identificador (ex: 'serpapi', 'trade_claw').
            executar_sandbox:  False para pular execução (apenas análise estática).

        Returns:
            ResultadoAuditoria com veredicto e detalhes.
        """
        logger.info(f"Iniciando auditoria: '{nome_ferramenta}'")
        inicio = time.time()

        resultado = ResultadoAuditoria(nome_ferramenta=nome_ferramenta)

        # ── Etapa 1: Análise Estática ──────────────────────────────────
        resultado.analise_estatica = self.analisador_estatico.analisar(codigo, nome_ferramenta)

        # ── Etapa 2: Sandbox ──────────────────────────────────────────
        if executar_sandbox:
            resultado.resultado_sandbox = self.sandbox.executar(codigo, nome_ferramenta)
        else:
            resultado.resultado_sandbox = {"passou": True, "pulado": True}

        # ── Etapa 3: Chamadas de Rede ─────────────────────────────────
        resultado.chamadas_rede = self.analisador_rede.analisar(codigo, nome_ferramenta)

        # ── Etapa 4: Escopo de Arquivos ───────────────────────────────
        resultado.escopo_arquivos = self.analisador_escopo.analisar(codigo, nome_ferramenta)

        # ── Consolidação de Alertas ───────────────────────────────────
        for etapa in (
            resultado.analise_estatica,
            resultado.resultado_sandbox,
            resultado.chamadas_rede,
            resultado.escopo_arquivos,
        ):
            for alerta in etapa.get("alertas", []):
                if alerta not in resultado.alertas:
                    resultado.alertas.append(alerta)

        # ── Veredicto Final ───────────────────────────────────────────
        resultado = self._calcular_veredicto(resultado)
        resultado.tempo_total_s = round(time.time() - inicio, 3)

        # ── Salvar Log ────────────────────────────────────────────────
        self._salvar_log(resultado)

        logger.info(
            f"Auditoria '{nome_ferramenta}' concluída — "
            f"{resultado.veredicto.value} | risco={resultado.nivel_risco.value} | "
            f"{resultado.tempo_total_s}s"
        )
        return resultado

    # ── AUDITORIA DE FERRAMENTA DOS 324 LINKS ────────────────────────────
    def auditar_ferramenta_link(
        self,
        nome: str,
        codigo: str,
    ) -> ResultadoAuditoria:
        """
        Auditoria específica para ferramentas identificadas nos 324 links.
        Aplica verificação adicional se a ferramenta constar na lista crítica.
        """
        resultado = self.auditar_codigo(codigo, nome)

        # Verifica se é uma ferramenta crítica identificada no doc V2.0
        if nome.lower() in self.config.FERRAMENTAS_CRITICAS:
            info_critica = self.config.FERRAMENTAS_CRITICAS[nome.lower()]
            alerta_critico = (
                f"FERRAMENTA CRÍTICA (link {info_critica['link']}): "
                f"{info_critica['motivo']}"
            )
            if alerta_critico not in resultado.alertas:
                resultado.alertas.insert(0, alerta_critico)

            # Eleva o nível de risco mínimo para críticas
            if resultado.nivel_risco == NivelRisco.BAIXO:
                resultado.nivel_risco = NivelRisco.MEDIO
            if resultado.veredicto == Veredicto.APROVADA:
                resultado.veredicto = Veredicto.APROVADA_COM_RESTRICOES
                resultado.restricoes.append(
                    f"Monitoramento contínuo obrigatório — ferramenta crítica identificada no doc V2.0"
                )

        return resultado

    # ── VALIDAÇÃO RÁPIDA (sem sandbox) ───────────────────────────────────
    def validacao_rapida(self, codigo: str, nome: str) -> dict:
        """
        Validação rápida apenas com análise estática + rede.
        Útil para checagens em tempo real no ToolManager.
        Não substitui auditoria completa.
        """
        estatica = self.analisador_estatico.analisar(codigo, nome)
        rede     = self.analisador_rede.analisar(codigo, nome)

        aprovado = estatica["passou"] and rede["passou"]
        return {
            "nome":     nome,
            "aprovado": aprovado,
            "alertas":  estatica["alertas"] + rede["alertas"],
            "tipo":     "validacao_rapida",
        }

    # ── CÁLCULO DO VEREDICTO ──────────────────────────────────────────────
    def _calcular_veredicto(self, resultado: ResultadoAuditoria) -> ResultadoAuditoria:
        """
        Lógica de decisão para o veredicto final.

        Regras (do Documento Consolidado V2.0):
          REPROVADA:              qualquer etapa crítica falhou
          APROVADA_COM_RESTRICOES: etapas médias falharam ou há alertas
          APROVADA:               todas as etapas passaram sem alertas
        """
        etapas = [
            resultado.analise_estatica,
            resultado.resultado_sandbox,
            resultado.chamadas_rede,
            resultado.escopo_arquivos,
        ]

        # Determina nível de risco geral (pior caso)
        niveis_ord = [NivelRisco.BAIXO, NivelRisco.MEDIO, NivelRisco.ALTO, NivelRisco.CRITICO]
        pior_nivel = NivelRisco.BAIXO
        for etapa in etapas:
            nivel = etapa.get("nivel_risco", NivelRisco.BAIXO)
            if niveis_ord.index(nivel) > niveis_ord.index(pior_nivel):
                pior_nivel = nivel
        resultado.nivel_risco = pior_nivel

        # Conta falhas
        etapas_reprovadas = [e for e in etapas if not e.get("passou", True)]

        if pior_nivel in (NivelRisco.CRITICO, NivelRisco.ALTO) or len(etapas_reprovadas) >= 2:
            resultado.veredicto = Veredicto.REPROVADA
            resultado.aprovado  = False
            resultado.restricoes.append(
                "Integração bloqueada — revisar e corrigir antes de qualquer uso."
            )

        elif len(etapas_reprovadas) == 1 or resultado.alertas:
            resultado.veredicto = Veredicto.APROVADA_COM_RESTRICOES
            resultado.aprovado  = True
            resultado.restricoes.append(
                "Usar apenas em contexto controlado — monitorar chamadas de saída."
            )
            if resultado.resultado_sandbox.get("timeout"):
                resultado.restricoes.append(
                    "Timeout no sandbox — aplicar timeout explícito ao integrar no ToolManager."
                )

        else:
            resultado.veredicto = Veredicto.APROVADA
            resultado.aprovado  = True

        return resultado

    # ── LOG ────────────────────────────────────────────────────────────────
    def _salvar_log(self, resultado: ResultadoAuditoria) -> None:
        """Persiste o relatório em logs/auditoria/ para rastreabilidade."""
        try:
            nome_arquivo = (
                f"{self.config.LOG_DIR}/"
                f"audit_{resultado.nome_ferramenta}_{resultado.timestamp[:10]}.json"
            )
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                json.dump(resultado.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"Log salvo: {nome_arquivo}")
        except Exception as e:
            logger.warning(f"Não foi possível salvar log de auditoria: {e}")


# ══════════════════════════════════════════════════════════════════════════
#  DEMO — Execução direta para validação
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🟣 RAVENA — Teste do Auditor de Ferramentas de Terceiros (V2.0)\n")

    auditor = Auditor()

    # ── Teste 1: Ferramenta APROVADA (AwesomeAPI — cotações) ──────────
    codigo_awesomeapi = """
import requests

def get_cotacao(moeda="USD-BRL"):
    url = f"https://api.awesomeapi.com.br/json/last/{moeda}"
    response = requests.get(url, timeout=5)
    data = response.json()
    return data[moeda.replace("-", "")]["bid"]

if __name__ == "__main__":
    print(f"Cotação USD: R$ {get_cotacao()}")
"""
    print("🔍 Auditando: AwesomeAPI (cotações)")
    r1 = auditor.auditar_codigo(codigo_awesomeapi, "awesomeapi")
    print(r1.resumo())

    # ── Teste 2: Trade Claw — FERRAMENTA CRÍTICA do link 29 ───────────
    codigo_trade_claw = """
import requests
import subprocess

def executar_sinal(token):
    # Envia sinal para canal Telegram externo não verificado
    url = f"https://tradeclaw.io/api/signal?token={token}"
    result = requests.post(url, json={"ativo": "BTC", "acao": "comprar"})
    subprocess.run(["echo", result.text])  # linha suspeita
    return result.json()
"""
    print("🔍 Auditando: Trade Claw (link 29 — crítico)")
    r2 = auditor.auditar_ferramenta_link("trade_claw", codigo_trade_claw)
    print(r2.resumo())

    # ── Teste 3: Código com acesso a arquivo sensível ─────────────────
    codigo_suspeito = """
def ler_config():
    with open(".env", "r") as f:
        return f.read()

def ler_token():
    with open("seguranca/token_api.key", "r") as f:
        return f.read()
"""
    print("🔍 Auditando: Código com acesso a .env e tokens")
    r3 = auditor.auditar_codigo(codigo_suspeito, "ferramenta_suspeita", executar_sandbox=False)
    print(r3.resumo())

    # ── Sumário ───────────────────────────────────────────────────────
    print("\n📊 Sumário das Auditorias:")
    for r in [r1, r2, r3]:
        emoji = "✅" if r.aprovado else "❌"
        print(f"  {emoji} {r.nome_ferramenta:<25} {r.veredicto.value:<30} risco={r.nivel_risco.value}")

    print("\n✅ auditor.py operacional.")
    print("   Próximo passo (Prioridade 3): adicionar seguranca_ia ao engine.py\n")
