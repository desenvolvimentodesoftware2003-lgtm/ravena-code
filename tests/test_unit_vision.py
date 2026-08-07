import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.vision.vision_pipeline_v3_2_6 import (
    TipoEntradaVisual,
    NivelAmeaca,
    TipoAnomalia,
    FeatureVisual,
    PadreDetectado,
    SnapshotVisual,
    ExtratorDeFeaturesVisuais,
    AnalisadorDePadroes,
    ModuloPercepcaoVisual,
    VisionPipeline,
    inicializar_visao,
    obter_visao,
)


class TestEnums:
    def test_tipo_entrada_visual(self):
        assert TipoEntradaVisual.LOG_TEXTO.value == "log_texto"
        assert TipoEntradaVisual.METRICAS_TEMPO_REAL.value == "metricas_tempo_real"

    def test_nivel_ameaca(self):
        assert NivelAmeaca.NORMAL.value == "normal"
        assert NivelAmeaca.CRITICA.value == "critica"

    def test_tipo_anomalia(self):
        assert TipoAnomalia.ATAQUE_BRUTE_FORCE.value == "ataque_brute_force"
        assert TipoAnomalia.FALHA_HARDWARE.value == "falha_hardware"


class TestDataclasses:
    def test_feature_visual(self):
        f = FeatureVisual(tipo="ip", valor="192.168.1.1", confianca=0.95)
        assert f.tipo == "ip"
        assert f.valor == "192.168.1.1"
        assert f.confianca == 0.95
        assert f.timestamp is not None

    def test_padrao_detectado(self):
        f = FeatureVisual(tipo="test", valor=True, confianca=0.9)
        p = PadreDetectado(
            tipo_anomalia=TipoAnomalia.ATAQUE_BRUTE_FORCE,
            nivel_ameaca=NivelAmeaca.CRITICA,
            confianca=0.92,
            features_relacionadas=[f],
            descricao="Ataque detectado",
            recomendacao_acao="Bloquear",
        )
        assert p.tipo_anomalia == TipoAnomalia.ATAQUE_BRUTE_FORCE
        assert p.confianca == 0.92

    def test_snapshot_visual(self):
        snap = SnapshotVisual(
            entrada_tipo=TipoEntradaVisual.LOG_TEXTO,
            features_extraidas=[],
            padroes_detectados=[],
            nivel_ameaca_geral=NivelAmeaca.NORMAL,
            confianca_geral=0.0,
        )
        assert snap.entrada_tipo == TipoEntradaVisual.LOG_TEXTO
        assert snap.nivel_ameaca_geral == NivelAmeaca.NORMAL


class TestExtratorDeFeaturesVisuais:
    def test_extrair_de_log_texto(self):
        ext = ExtratorDeFeaturesVisuais()
        log = "192.168.1.100:5432 ERROR: Failed login from 192.168.1.101"
        features = ext.extrair_de_log_texto(log)
        tipos = [f.tipo for f in features]
        assert "ip_detectado" in tipos
        assert "porta_detectada" in tipos
        assert "erro_detectado" in tipos

    def test_extrair_de_log_sem_padroes(self):
        ext = ExtratorDeFeaturesVisuais()
        features = ext.extrair_de_log_texto("INFO: System started normally")
        assert len(features) == 0

    def test_extrair_de_metricas(self):
        ext = ExtratorDeFeaturesVisuais()
        metricas = {"cpu_percent": 95, "memory_percent": 90, "disk_percent": 50}
        features = ext.extrair_de_metricas(metricas)
        tipos = [f.tipo for f in features]
        assert "cpu_alto" in tipos
        assert "memoria_alta" in tipos
        assert "disco_normal" in tipos

    def test_extrair_de_metricas_normais(self):
        ext = ExtratorDeFeaturesVisuais()
        metricas = {"cpu_percent": 30, "memory_percent": 40, "disk_percent": 50}
        features = ext.extrair_de_metricas(metricas)
        tipos = [f.tipo for f in features]
        assert "cpu_normal" in tipos
        assert "memoria_normal" in tipos

    def test_extrair_por_tipo(self):
        ext = ExtratorDeFeaturesVisuais()
        features = ext.extrair("ERROR: 403 Forbidden from 10.0.0.1", TipoEntradaVisual.LOG_TEXTO)
        assert len(features) >= 2

    def test_extrair_metricas_por_tipo(self):
        ext = ExtratorDeFeaturesVisuais()
        features = ext.extrair('{"cpu_percent": 90}', TipoEntradaVisual.METRICAS_TEMPO_REAL)
        assert len(features) == 1
        assert features[0].tipo == "cpu_alto"

    def test_extrair_json_invalido(self):
        ext = ExtratorDeFeaturesVisuais()
        features = ext.extrair("not json", TipoEntradaVisual.METRICAS_TEMPO_REAL)
        assert len(features) == 0

    def test_extrair_tipo_desconhecido(self):
        ext = ExtratorDeFeaturesVisuais()
        features = ext.extrair("test", TipoEntradaVisual.VIDEO_STREAM)
        assert len(features) == 0


class TestAnalisadorDePadroes:
    def test_analisar_features_vazias(self):
        analisador = AnalisadorDePadroes()
        padroes = analisador.analisar_features([])
        assert len(padroes) == 0

    def test_analisar_acessos_negados(self):
        analisador = AnalisadorDePadroes()
        features = [FeatureVisual(tipo="acesso_negado", valor=True, confianca=0.97) for _ in range(3)]
        padroes = analisador.analisar_features(features)
        assert len(padroes) == 1
        assert padroes[0].tipo_anomalia == TipoAnomalia.ATAQUE_BRUTE_FORCE

    def test_analisar_cpu_memoria_alta(self):
        analisador = AnalisadorDePadroes()
        features = [
            FeatureVisual(tipo="cpu_alto", valor=95, confianca=0.99),
            FeatureVisual(tipo="memoria_alta", valor=90, confianca=0.99),
        ]
        padroes = analisador.analisar_features(features)
        tipos = [p.tipo_anomalia for p in padroes]
        assert TipoAnomalia.DEGRADACAO_PERFORMANCE in tipos

    def test_calcular_nivel_ameaca_geral(self):
        analisador = AnalisadorDePadroes()
        f = FeatureVisual(tipo="test", valor=True, confianca=0.9)
        padroes = [
            PadreDetectado(
                tipo_anomalia=TipoAnomalia.ATAQUE_BRUTE_FORCE,
                nivel_ameaca=NivelAmeaca.CRITICA,
                confianca=0.92,
                features_relacionadas=[f],
                descricao="test",
                recomendacao_acao="test",
            )
        ]
        nivel, conf = analisador.calcular_nivel_ameaca_geral(padroes)
        assert nivel == NivelAmeaca.CRITICA
        assert conf == 0.92

    def test_calcular_nivel_ameaca_sem_padroes(self):
        analisador = AnalisadorDePadroes()
        nivel, conf = analisador.calcular_nivel_ameaca_geral([])
        assert nivel == NivelAmeaca.NORMAL
        assert conf == 0.0


class TestModuloPercepcaoVisual:
    def test_processar_log_texto(self):
        modulo = ModuloPercepcaoVisual()
        log = "ERROR: 403 Forbidden from 192.168.1.1"
        snapshot = modulo.processar_entrada_visual(log, TipoEntradaVisual.LOG_TEXTO)
        assert len(snapshot.features_extraidas) >= 2
        assert snapshot.entrada_tipo == TipoEntradaVisual.LOG_TEXTO

    def test_obter_status_sem_dados(self):
        modulo = ModuloPercepcaoVisual()
        status = modulo.obter_status_visual()
        assert status["status"] == "sem_dados"

    def test_obter_status_com_dados(self):
        modulo = ModuloPercepcaoVisual()
        modulo.processar_entrada_visual("ERROR", TipoEntradaVisual.LOG_TEXTO)
        status = modulo.obter_status_visual()
        assert status["status"] == "operacional"

    def test_historico_ameacas(self):
        modulo = ModuloPercepcaoVisual()
        log = "403 DENIED from 10.0.0.1\n403 DENIED from 10.0.0.1"
        modulo.processar_entrada_visual(log, TipoEntradaVisual.LOG_TEXTO)
        ameacas = modulo.obter_historico_ameacas()
        assert len(ameacas) >= 1

    def test_callback_ameaca(self):
        modulo = ModuloPercepcaoVisual()
        chamadas = []
        def callback(padrao):
            chamadas.append(padrao)
        modulo.registrar_callback_ameaca(callback)
        log = "403 DENIED from 10.0.0.1\n403 DENIED from 10.0.0.1"
        modulo.processar_entrada_visual(log, TipoEntradaVisual.LOG_TEXTO)
        assert len(chamadas) >= 1

    def test_processar_metricas(self):
        modulo = ModuloPercepcaoVisual()
        snapshot = modulo.processar_entrada_visual(
            '{"cpu_percent": 95, "memory_percent": 90}',
            TipoEntradaVisual.METRICAS_TEMPO_REAL,
        )
        assert len(snapshot.features_extraidas) == 2


class TestVisionPipeline:
    def test_process_log(self):
        pipeline = VisionPipeline()
        result = pipeline.process_log("ERROR 403 from 192.168.1.1")
        assert result["features"] >= 2
        assert "nivel_ameaca" in result

    def test_process_metrics(self):
        pipeline = VisionPipeline()
        result = pipeline.process_metrics('{"cpu_percent": 95, "memory_percent": 90}')
        assert result["features"] == 2
        assert result["nivel_ameaca"] != "normal"

    def test_get_status(self):
        pipeline = VisionPipeline()
        status = pipeline.get_status()
        assert status["status"] == "sem_dados"

    def test_get_threats(self):
        pipeline = VisionPipeline()
        pipeline.process_log("403 DENIED from 10.0.0.1\n403 DENIED from 10.0.0.1")
        threats = pipeline.get_threats()
        assert len(threats) >= 1


class TestSingleton:
    def test_inicializar_visao(self):
        visao = inicializar_visao()
        assert isinstance(visao, ModuloPercepcaoVisual)

    def test_obter_visao(self):
        v1 = obter_visao()
        v2 = obter_visao()
        assert v1 is v2
