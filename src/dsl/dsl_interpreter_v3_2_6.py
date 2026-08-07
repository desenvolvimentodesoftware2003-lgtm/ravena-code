import shlex
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger("ravena.dsl_interpreter")


class CommandType(Enum):
    AGENT = "AGENT"
    MEMORY = "MEMORY"
    TRADE = "TRADE"
    SEARCH = "SEARCH"
    SENSOR = "SENSOR"
    VISION = "VISION"
    ANALYTICS = "ANALYTICS"
    RAG = "RAG"
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    HELP = "HELP"
    STATUS = "STATUS"


@dataclass
class CommandAST:
    command: CommandType
    args: List[str] = field(default_factory=list)
    kwargs: Dict[str, str] = field(default_factory=dict)
    raw: str = ""

    def __repr__(self):
        return f"CommandAST({self.command.value}, args={self.args})"


_CMD_MAP = {
    "AGENT": CommandType.AGENT,
    "AGENTS": CommandType.AGENT,
    "MEMORY": CommandType.MEMORY,
    "MEMORIA": CommandType.MEMORY,
    "TRADE": CommandType.TRADE,
    "TRADING": CommandType.TRADE,
    "SEARCH": CommandType.SEARCH,
    "BUSCA": CommandType.SEARCH,
    "SENSOR": CommandType.SENSOR,
    "SENSORS": CommandType.SENSOR,
    "VISION": CommandType.VISION,
    "VISAO": CommandType.VISION,
    "ANALYTICS": CommandType.ANALYTICS,
    "METRICAS": CommandType.ANALYTICS,
    "RAG": CommandType.RAG,
    "IMPORT": CommandType.IMPORT,
    "IMPORTAR": CommandType.IMPORT,
    "EXPORT": CommandType.EXPORT,
    "EXPORTAR": CommandType.EXPORT,
    "HELP": CommandType.HELP,
    "AJUDA": CommandType.HELP,
    "STATUS": CommandType.STATUS,
}


class DSLParseError(Exception):
    pass


class DSLParser:
    def parse(self, text: str) -> CommandAST:
        text = text.strip()
        if not text:
            raise DSLParseError("Comando vazio")
        try:
            parts = shlex.split(text)
        except ValueError as e:
            raise DSLParseError(f"Erro de sintaxe: {e}")
        cmd_str = parts[0].upper()
        cmd_type = _CMD_MAP.get(cmd_str)
        if cmd_type is None:
            raise DSLParseError(f"Comando desconhecido: '{cmd_str}'. Use HELP para lista de comandos.")
        args = parts[1:] if len(parts) > 1 else []
        return CommandAST(command=cmd_type, args=args, raw=text)


class DSLInterpreter:
    def __init__(self):
        self.parser = DSLParser()
        self._handlers: Dict[CommandType, Callable] = {}
        self._history: List[Dict[str, Any]] = []
        self._system_refs: Dict[str, Any] = {}
        self._register_default_handlers()

    def register_handler(self, cmd_type: CommandType, handler: Callable[[CommandAST], str]):
        self._handlers[cmd_type] = handler

    def bind_system(self, name: str, ref: Any):
        self._system_refs[name] = ref

    def _register_default_handlers(self):
        self._handlers[CommandType.HELP] = self._cmd_help
        self._handlers[CommandType.STATUS] = self._cmd_status
        self._handlers[CommandType.AGENT] = self._cmd_agent
        self._handlers[CommandType.MEMORY] = self._cmd_memory
        self._handlers[CommandType.TRADE] = self._cmd_trade
        self._handlers[CommandType.SEARCH] = self._cmd_search
        self._handlers[CommandType.SENSOR] = self._cmd_sensor
        self._handlers[CommandType.VISION] = self._cmd_vision
        self._handlers[CommandType.ANALYTICS] = self._cmd_analytics
        self._handlers[CommandType.RAG] = self._cmd_rag
        self._handlers[CommandType.IMPORT] = self._cmd_import
        self._handlers[CommandType.EXPORT] = self._cmd_export

    def execute(self, text: str) -> str:
        try:
            ast = self.parser.parse(text)
        except DSLParseError as e:
            return f"[DSL] {e}"
        handler = self._handlers.get(ast.command)
        if not handler:
            return f"[DSL] Nenhum handler registrado para {ast.command.value}"
        try:
            result = handler(ast)
            self._history.append({"command": ast.raw, "result": result, "timestamp": datetime.now().isoformat()})
            return result
        except Exception as e:
            error_msg = f"[DSL] Erro ao executar '{ast.command.value}': {e}"
            self._history.append({"command": ast.raw, "error": str(e), "timestamp": datetime.now().isoformat()})
            logger.error(error_msg)
            return error_msg

    def execute_multi(self, text: str) -> List[str]:
        results = []
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            results.append(self.execute(line))
        return results

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._history[-limit:]

    def _cmd_help(self, ast: CommandAST) -> str:
        return (
            "COMANDOS DISPONIVEIS:\n"
            "  AGENT <nome> <instrucao>     — Envia instrucao a um agente\n"
            "  MEMORY STORE|GET <tipo> <dado>  — Gerencia memoria\n"
            "  TRADE SIMULATE|EXECUTE <lado> <ativo> <qtd> — Trading\n"
            "  SEARCH <consulta>            — Busca informacoes\n"
            "  SENSOR RUN|STATUS <nome>     — Controla sensores\n"
            "  VISION ANALYZE log|metrics <dado> — Analise visual\n"
            "  ANALYTICS health|summary     — Metricas do sistema\n"
            "  RAG QUERY <pergunta>         — Consulta RAG\n"
            "  IMPORT <caminho>             — Importa dados\n"
            "  EXPORT <formato>             — Exporta resultados\n"
            "  STATUS                       — Status do sistema\n"
            "  HELP                         — Esta ajuda\n"
            "Use # para comentarios. Use aspas para argumentos com espacos."
        )

    def _cmd_status(self, ast: CommandAST) -> str:
        lines = [f"Ravena AIM DSL Interpreter - Status", f"Modulos registrados: {len(self._system_refs)}"]
        for name, ref in self._system_refs.items():
            try:
                if hasattr(ref, "health_check"):
                    info = ref.health_check()
                    if isinstance(info, dict):
                        lines.append(f"  {name}: {info.get('status', info.get('all_ok', 'ok'))}")
                    else:
                        lines.append(f"  {name}: ok")
                elif hasattr(ref, "get_all_info"):
                    info = ref.get_all_info()
                    lines.append(f"  {name}: {len(info)} sensores")
                else:
                    lines.append(f"  {name}: disponivel")
            except Exception as e:
                lines.append(f"  {name}: erro ({e})")
        lines.append(f"Comandos no historico: {len(self._history)}")
        return "\n".join(lines)

    def _cmd_agent(self, ast: CommandAST) -> str:
        if len(ast.args) < 2:
            return "[DSL] Uso: AGENT <nome> <instrucao>"
        agent_name = ast.args[0]
        instruction = " ".join(ast.args[1:])
        orchestrator = self._system_refs.get("orchestrator")
        if orchestrator:
            try:
                if hasattr(orchestrator, "processar_entrada"):
                    result = orchestrator.processar_entrada("dsl", instruction)
                    return f"[AGENT {agent_name}] {result}"
                elif hasattr(orchestrator, "executar_comando_seguro"):
                    result = orchestrator.executar_comando_seguro(instruction)
                    return f"[AGENT {agent_name}] {result}"
            except Exception as e:
                return f"[AGENT {agent_name}] Erro: {e}"
        return f"[AGENT {agent_name}] Instrucao recebida (sem orchestrator vinculado): {instruction}"

    def _cmd_memory(self, ast: CommandAST) -> str:
        if not ast.args:
            return "[DSL] Uso: MEMORY STORE|GET <tipo> <dado>"
        sub = ast.args[0].upper()
        memory = self._system_refs.get("memory")
        if not memory:
            return "[MEMORY] Modulo de memoria nao vinculado"
        try:
            if sub == "STORE" and len(ast.args) >= 3:
                tipo = ast.args[1]
                conteudo = " ".join(ast.args[2:])
                if tipo == "episodic" or tipo == "episodica":
                    memory.registrar_interacao("dsl", conteudo, "ok", "dsl")
                elif tipo == "semantic" or tipo == "semantica":
                    memory.aprender("dsl_" + str(hash(conteudo))[:8], conteudo, fonte="dsl", categoria="general")
                else:
                    memory.registrar_interacao("dsl", conteudo, "ok", "dsl")
                return f"[MEMORY] Armazenado em {tipo}"
            elif sub == "GET" and len(ast.args) >= 2:
                tipo = ast.args[1]
                termo = " ".join(ast.args[2:]) if len(ast.args) > 2 else ""
                if tipo == "episodic" or tipo == "episodica" or tipo == "ultimas":
                    ctx = memory.contexto_recente("dsl", limite=5)
                    if ctx:
                        return "[MEMORY]\n" + ctx
                    return "[MEMORY] Nenhum registro episodico"
                elif tipo == "semantic" or tipo == "semantica":
                    if termo:
                        facts = memory.semantica.buscar(termo)
                        if facts:
                            return "[MEMORY] " + "\n".join(f"{f.chave}: {f.valor[:100]}" for f in facts)
                        return f"[MEMORY] Nada encontrado para '{termo}'"
                    cat = memory.semantica.listar_categoria("general")
                    if cat:
                        return "[MEMORY] " + "\n".join(f"{f.chave}: {f.valor[:100]}" for f in cat[:5])
                    return "[MEMORY] Nenhum fato semantico"
                return "[MEMORY] Uso: MEMORY GET episodic|semantic <termo>"
            return "[MEMORY] Uso: MEMORY STORE episodic|semantic <dado>"
        except Exception as e:
            return f"[MEMORY] Erro: {e}"

    def _cmd_trade(self, ast: CommandAST) -> str:
        if len(ast.args) < 3:
            return "[DSL] Uso: TRADE SIMULATE|EXECUTE <lado> <ativo> <qtd>"
        acao = ast.args[0].upper()
        lado = ast.args[1].upper()
        ativo = ast.args[2]
        qtd = ast.args[3] if len(ast.args) > 3 else "0"
        if acao == "SIMULATE":
            trading = self._system_refs.get("trading")
            if trading:
                return f"[TRADE SIMULATE] {lado} {ativo} {qtd} (simulado)"
            return f"[TRADE SIMULATE] {lado} {ativo} {qtd} (sem trading vinculado)"
        return f"[TRADE] Comando nao reconhecido: {acao}"

    def _cmd_search(self, ast: CommandAST) -> str:
        query = " ".join(ast.args) if ast.args else ""
        if not query:
            return "[SEARCH] Uso: SEARCH <consulta>"
        search = self._system_refs.get("search")
        if search:
            try:
                if hasattr(search, "buscar"):
                    result = search.buscar(query)
                    return f"[SEARCH] {result}"
                elif hasattr(search, "execute_search"):
                    result = search.execute_search(query)
                    return f"[SEARCH] {result}"
            except Exception as e:
                return f"[SEARCH] Erro: {e}"
        return f"[SEARCH] Consulta recebida (sem search vinculado): {query}"

    def _cmd_sensor(self, ast: CommandAST) -> str:
        if not ast.args:
            return "[DSL] Uso: SENSOR RUN|STATUS <nome>"
        sub = ast.args[0].upper()
        sensor_mgr = self._system_refs.get("sensor_manager")
        if not sensor_mgr:
            return "[SENSOR] SensorManager nao vinculado"
        if sub == "RUN":
            nome = ast.args[1] if len(ast.args) > 1 else ""
            if nome:
                records = sensor_mgr.run_sensor(nome)
                if records is None:
                    sensores = list(sensor_mgr.sensors.keys())
                    return f"[SENSOR] Sensor '{nome}' nao encontrado. Disponiveis: {sensores}"
                return f"[SENSOR] {nome}: {len(records)} registros coletados"
            results = sensor_mgr.run_all()
            total = sum(v["records"] for v in results.values())
            return f"[SENSOR] Todos os sensores executados: {total} registros"
        elif sub == "STATUS":
            info = sensor_mgr.get_all_info()
            lines = [f"{k}: {v['status']} (ingested: {v['items_ingested']})" for k, v in info.items()]
            return "[SENSOR]\n" + "\n".join(lines) if lines else "[SENSOR] Nenhum sensor registrado"
        return f"[SENSOR] Subcomando desconhecido: {sub}"

    def _cmd_vision(self, ast: CommandAST) -> str:
        if len(ast.args) < 2:
            return "[DSL] Uso: VISION ANALYZE log|metrics <dado>"
        sub = ast.args[0].upper()
        tipo = ast.args[1].lower()
        dado = " ".join(ast.args[2:]) if len(ast.args) > 2 else ""
        vision = self._system_refs.get("vision")
        if not vision:
            return "[VISION] Modulo de visao nao vinculado"
        try:
            if sub == "ANALYZE":
                if tipo == "log":
                    result = vision.process_log(dado)
                    return f"[VISION LOG] Features: {result['features']}, Padroes: {result['padroes']}, Nivel: {result['nivel_ameaca']}"
                elif tipo == "metrics":
                    result = vision.process_metrics(dado)
                    return f"[VISION METRICS] Features: {result['features']}, Padroes: {result['padroes']}, Nivel: {result['nivel_ameaca']}"
                return f"[VISION] Tipo desconhecido: {tipo}. Use log ou metrics."
            return f"[VISION] Subcomando desconhecido: {sub}"
        except Exception as e:
            return f"[VISION] Erro: {e}"

    def _cmd_analytics(self, ast: CommandAST) -> str:
        sub = ast.args[0].upper() if ast.args else "SUMMARY"
        analytics = self._system_refs.get("analytics")
        if not analytics:
            return "[ANALYTICS] Modulo de analytics nao vinculado"
        try:
            if sub == "HEALTH" or sub == "SAUDE":
                hc = analytics.health_check()
                subs_hc = hc.get("subsystems", {})
                subs_str = ", ".join(f"{k}: {'OK' if v else 'FALHA'}" for k, v in subs_hc.items()) if subs_hc else "sem subsistemas"
                score = hc.get("system_health_score", hc.get("health_score", 0))
                return f"[HEALTH] Status: {hc['status']} | Score: {score} | {subs_str}"
            elif sub == "SUMMARY" or sub == "RESUMO":
                summary = analytics.get_summary()
                if summary.get("status") == "NO_DATA":
                    return "[ANALYTICS] Sem dados de metricas registrados"
                health = summary.get("health_score", 0)
                cpu = summary.get("cpu_percent", 0)
                mem = summary.get("memory_percent", 0)
                win = summary.get("win_rate", 0)
                recs = summary.get("total_records", 0)
                return (
                    f"[SUMMARY] Status: {summary.get('status', 'N/A')} | "
                    f"Health: {health} | "
                    f"CPU: {cpu}% | "
                    f"RAM: {mem}% | "
                    f"Win Rate: {win} | "
                    f"Registros: {recs}"
                )
            return f"[ANALYTICS] Subcomando desconhecido: {sub}"
        except Exception as e:
            return f"[ANALYTICS] Erro: {e}"

    def _cmd_rag(self, ast: CommandAST) -> str:
        if len(ast.args) < 2:
            return "[DSL] Uso: RAG QUERY <pergunta>"
        sub = ast.args[0].upper()
        query = " ".join(ast.args[1:])
        if sub == "QUERY":
            rag = self._system_refs.get("rag")
            if rag:
                try:
                    if hasattr(rag, "buscar_contexto"):
                        results = rag.buscar_contexto(query, top_k=3)
                        if results:
                            texts = [r.get("conteudo", str(r))[:200] for r in results]
                            return "[RAG]\n" + "\n---\n".join(texts)
                        return "[RAG] Nenhum resultado encontrado"
                    elif hasattr(rag, "query"):
                        result = rag.query(query)
                        return f"[RAG] {result}"
                except Exception as e:
                    return f"[RAG] Erro: {e}"
            return f"[RAG] Consulta recebida (sem RAG vinculado): {query}"
        return f"[RAG] Subcomando desconhecido: {sub}"

    def _cmd_import(self, ast: CommandAST) -> str:
        caminho = " ".join(ast.args) if ast.args else ""
        if not caminho:
            return "[IMPORT] Uso: IMPORT <caminho>"
        return f"[IMPORT] Caminho recebido: {caminho} (implementacao de importacao pendente)"

    def _cmd_export(self, ast: CommandAST) -> str:
        formato = " ".join(ast.args) if ast.args else "json"
        return f"[EXPORT] Formato: {formato} (implementacao de exportacao pendente)"
