import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dsl.dsl_interpreter_v3_2_6 import (
    DSLInterpreter,
    DSLParser,
    CommandType,
    CommandAST,
    DSLParseError,
)


class TestDSLParser:
    def test_parse_agent(self):
        parser = DSLParser()
        ast = parser.parse("AGENT SearchAgent find news")
        assert ast.command == CommandType.AGENT
        assert ast.args == ["SearchAgent", "find", "news"]

    def test_parse_memory(self):
        parser = DSLParser()
        ast = parser.parse('MEMORY STORE episodic "hello world"')
        assert ast.command == CommandType.MEMORY
        assert ast.args == ["STORE", "episodic", "hello world"]

    def test_parse_trade(self):
        parser = DSLParser()
        ast = parser.parse("TRADE SIMULATE BUY BTC 1000")
        assert ast.command == CommandType.TRADE
        assert ast.args == ["SIMULATE", "BUY", "BTC", "1000"]

    def test_parse_search(self):
        parser = DSLParser()
        ast = parser.parse('SEARCH "latest crypto news"')
        assert ast.command == CommandType.SEARCH
        assert ast.args == ["latest crypto news"]

    def test_parse_sensor(self):
        parser = DSLParser()
        ast = parser.parse("SENSOR RUN FileSensor")
        assert ast.command == CommandType.SENSOR
        assert ast.args == ["RUN", "FileSensor"]

    def test_parse_vision(self):
        parser = DSLParser()
        ast = parser.parse('VISION ANALYZE log "ERROR 403"')
        assert ast.command == CommandType.VISION
        assert ast.args == ["ANALYZE", "log", "ERROR 403"]

    def test_parse_analytics_health(self):
        parser = DSLParser()
        ast = parser.parse("ANALYTICS health")
        assert ast.command == CommandType.ANALYTICS
        assert ast.args == ["health"]

    def test_parse_rag(self):
        parser = DSLParser()
        ast = parser.parse('RAG QUERY "What is Bitcoin?"')
        assert ast.command == CommandType.RAG
        assert ast.args == ["QUERY", "What is Bitcoin?"]

    def test_parse_help(self):
        parser = DSLParser()
        ast = parser.parse("HELP")
        assert ast.command == CommandType.HELP
        assert ast.args == []

    def test_parse_status(self):
        parser = DSLParser()
        ast = parser.parse("STATUS")
        assert ast.command == CommandType.STATUS

    def test_parse_import(self):
        parser = DSLParser()
        ast = parser.parse("IMPORT /path/to/file.json")
        assert ast.command == CommandType.IMPORT

    def test_parse_export(self):
        parser = DSLParser()
        ast = parser.parse("EXPORT json")
        assert ast.command == CommandType.EXPORT

    def test_parse_vazio(self):
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="Comando vazio"):
            parser.parse("")

    def test_parse_apenas_espacos(self):
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="Comando vazio"):
            parser.parse("   ")

    def test_parse_comando_desconhecido(self):
        parser = DSLParser()
        with pytest.raises(DSLParseError, match="Comando desconhecido"):
            parser.parse("XYZ some args")

    def test_parse_agent_portugues(self):
        parser = DSLParser()
        ast = parser.parse("MEMORIA STORE episodic teste")
        assert ast.command == CommandType.MEMORY

    def test_parse_busca_portugues(self):
        parser = DSLParser()
        ast = parser.parse("BUSCA noticias")
        assert ast.command == CommandType.SEARCH

    def test_parse_ajuda(self):
        parser = DSLParser()
        ast = parser.parse("AJUDA")
        assert ast.command == CommandType.HELP

    def test_parse_metricas(self):
        parser = DSLParser()
        ast = parser.parse("METRICAS health")
        assert ast.command == CommandType.ANALYTICS

    def test_parse_visao(self):
        parser = DSLParser()
        ast = parser.parse("VISAO ANALYZE log erro")
        assert ast.command == CommandType.VISION


class TestDSLInterpreter:
    def test_help(self):
        dsl = DSLInterpreter()
        result = dsl.execute("HELP")
        assert result.startswith("COMANDOS DISPONIVEIS")

    def test_status_sem_modulos(self):
        dsl = DSLInterpreter()
        result = dsl.execute("STATUS")
        assert "Modulos registrados: 0" in result

    def test_comando_vazio(self):
        dsl = DSLInterpreter()
        result = dsl.execute("")
        assert "Comando vazio" in result

    def test_comando_desconhecido(self):
        dsl = DSLInterpreter()
        result = dsl.execute("INVALIDCMD")
        assert "Comando desconhecido" in result

    def test_agent_sem_orchestrator(self):
        dsl = DSLInterpreter()
        result = dsl.execute("AGENT TestAgent hello")
        assert "sem orchestrator vinculado" in result

    def test_memory_sem_modulo(self):
        dsl = DSLInterpreter()
        result = dsl.execute("MEMORY STORE episodic test")
        assert "nao vinculado" in result

    def test_trade_simulate(self):
        dsl = DSLInterpreter()
        result = dsl.execute("TRADE SIMULATE BUY BTC 1000")
        assert "TRADE SIMULATE" in result

    def test_search_sem_modulo(self):
        dsl = DSLInterpreter()
        result = dsl.execute("SEARCH bitcoin news")
        assert "sem search vinculado" in result

    def test_sensor_sem_manager(self):
        dsl = DSLInterpreter()
        result = dsl.execute("SENSOR RUN FileSensor")
        assert "SensorManager nao vinculado" in result

    def test_vision_sem_modulo(self):
        dsl = DSLInterpreter()
        result = dsl.execute('VISION ANALYZE log "ERROR 403"')
        assert "nao vinculado" in result

    def test_analytics_sem_modulo(self):
        dsl = DSLInterpreter()
        result = dsl.execute("ANALYTICS health")
        assert "nao vinculado" in result

    def test_rag_sem_modulo(self):
        dsl = DSLInterpreter()
        result = dsl.execute("RAG QUERY What is Bitcoin")
        assert "sem RAG vinculado" in result

    def test_import(self):
        dsl = DSLInterpreter()
        result = dsl.execute("IMPORT /tmp/data.json")
        assert "IMPORT" in result

    def test_export(self):
        dsl = DSLInterpreter()
        result = dsl.execute("EXPORT csv")
        assert "EXPORT" in result

    def test_execute_multi(self):
        dsl = DSLInterpreter()
        results = dsl.execute_multi("HELP\nSTATUS\n# comment\nHELP")
        assert len(results) == 3

    def test_history(self):
        dsl = DSLInterpreter()
        dsl.execute("HELP")
        dsl.execute("STATUS")
        hist = dsl.get_history()
        assert len(hist) == 2
        assert hist[0]["command"] == "HELP"

    def test_handler_personalizado(self):
        dsl = DSLInterpreter()
        dsl.register_handler(CommandType.HELP, lambda ast: "custom help")
        assert dsl.execute("HELP") == "custom help"

    def test_bind_system(self):
        dsl = DSLInterpreter()
        mock = type("Mock", (), {"health_check": lambda self: {"status": "HEALTHY"}})()
        dsl.bind_system("analytics", mock)
        result = dsl.execute("ANALYTICS health")
        assert "HEALTHY" in result

    def test_bind_memory_real(self):
        from src.memory.memory_core_v3_2_6 import MemoryManager
        dsl = DSLInterpreter()
        memory = MemoryManager()
        dsl.bind_system("memory", memory)
        result = dsl.execute('MEMORY STORE episodic "testando memoria"')
        assert "Armazenado" in result
        result2 = dsl.execute("MEMORY GET episodic")
        assert "testando memoria" in result2 or "Nenhum" in result2

    def test_bind_vision_real(self):
        from src.vision.vision_pipeline_v3_2_6 import VisionPipeline
        dsl = DSLInterpreter()
        vision = VisionPipeline()
        dsl.bind_system("vision", vision)
        result = dsl.execute('VISION ANALYZE log "ERROR 403 from 10.0.0.1"')
        assert "VISION LOG" in result
        assert "Features" in result

    def test_bind_analytics_real(self):
        from src.analytics.analytics_core_v3_2_6 import AnalyticsCore
        import tempfile
        dsl = DSLInterpreter()
        tmp = tempfile.mktemp(suffix=".json")
        analytics = AnalyticsCore(history_path=tmp)
        dsl.bind_system("analytics", analytics)
        result = dsl.execute("ANALYTICS health")
        assert "NO_DATA" in result or "sem subsistemas" in result
        result2 = dsl.execute("ANALYTICS summary")
        assert "Sem dados" in result2
        if os.path.exists(tmp):
            os.remove(tmp)

    def test_bind_sensor_real(self):
        import tempfile
        from src.sensors.sensors_core_v3_2_6 import SensorManager, FileSensor
        dsl = DSLInterpreter()
        mgr = SensorManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.log"), "w") as f:
                f.write("log data")
            mgr.register(FileSensor("fs1", watch_dir=tmpdir))
            dsl.bind_system("sensor_manager", mgr)
            result = dsl.execute("SENSOR RUN fs1")
            assert "1 registros" in result
            result2 = dsl.execute("SENSOR STATUS")
            assert "fs1" in result2

    def test_erro_no_handler(self):
        dsl = DSLInterpreter()
        def failing(ast):
            raise ValueError("erro interno")
        dsl.register_handler(CommandType.SEARCH, failing)
        result = dsl.execute("SEARCH algo")
        assert "Erro ao executar" in result
        assert "erro interno" in result

    def test_trade_args_insuficientes(self):
        dsl = DSLInterpreter()
        result = dsl.execute("TRADE SIMULATE")
        assert "Uso" in result

    def test_sensor_subcomando_invalido(self):
        dsl = DSLInterpreter()
        from src.sensors.sensors_core_v3_2_6 import SensorManager
        mgr = SensorManager()
        dsl.bind_system("sensor_manager", mgr)
        result = dsl.execute("SENSOR INVALID")
        assert "Subcomando desconhecido" in result

    def test_vision_args_insuficientes(self):
        dsl = DSLInterpreter()
        result = dsl.execute("VISION")
        assert "Uso" in result

    def test_memory_get_sem_resultados(self):
        from src.memory.memory_core_v3_2_6 import MemoryManager, EpisodicMemory, SEMANTIC_FILE, EPISODIC_FILE
        import tempfile
        dsl = DSLInterpreter()
        tmp_ep = tempfile.mktemp(suffix="_ep.json")
        tmp_sem = tempfile.mktemp(suffix="_sem.json")
        mem = MemoryManager()
        mem.episodica = EpisodicMemory(filepath=tmp_ep)
        dsl.bind_system("memory", mem)
        result = dsl.execute("MEMORY GET episodic")
        assert "Nenhum" in result
        for p in [tmp_ep, tmp_sem]:
            if os.path.exists(p):
                os.remove(p)
