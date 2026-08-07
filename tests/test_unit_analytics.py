import os
import sys
import json
import tempfile
import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analytics.analytics_core_v3_2_6 import AnalyticsCore, SystemMetrics, HEALTHY_THRESHOLD, WARNING_THRESHOLD


@pytest.fixture(autouse=True)
def temp_history():
    tmp = tempfile.mktemp(suffix=".json")
    yield tmp
    if os.path.exists(tmp):
        os.remove(tmp)


class TestSystemMetrics:
    def test_criacao_padrao(self):
        m = SystemMetrics()
        assert m.cpu_percent == 0.0
        assert m.system_health_score == 0.0
        assert m.timestamp is not None

    def test_criacao_com_valores(self):
        m = SystemMetrics(cpu_percent=45.0, memory_percent=60.0, empathy_mes=0.85, api_latency_ms=150.0)
        assert m.cpu_percent == 45.0
        assert m.empathy_mes == 0.85


class TestAnalyticsCore:
    def test_inicializacao(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        assert core.get_latest() is None
        assert core.get_average_health_score() == 0.0

    def test_register_snapshot(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        m = SystemMetrics(cpu_percent=50.0, memory_percent=60.0, system_health_score=0.85)
        snap = core.register_snapshot(m)
        assert snap["cpu_percent"] == 50.0
        assert snap["system_health_score"] == 0.85
        assert core.get_latest()["cpu_percent"] == 50.0

    def test_persistencia_entre_instancias(self, temp_history):
        core1 = AnalyticsCore(history_path=temp_history)
        m1 = SystemMetrics(cpu_percent=30.0, memory_percent=40.0, system_health_score=0.9)
        core1.register_snapshot(m1)

        core2 = AnalyticsCore(history_path=temp_history)
        assert core2.get_latest()["cpu_percent"] == 30.0
        assert core2.get_latest()["system_health_score"] == 0.9

    def test_calculate_health_score_ideal(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        score = core.calculate_health_score(cpu=10, memory=20, api_latency_ms=50, empathy_mes=0.95, rag_latency_ms=100, win_rate=0.8)
        assert score > HEALTHY_THRESHOLD
        assert score <= 1.0

    def test_calculate_health_score_critico(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        score = core.calculate_health_score(cpu=95, memory=95, api_latency_ms=5000, empathy_mes=0.1, rag_latency_ms=10000, win_rate=0.0)
        assert score < WARNING_THRESHOLD

    def test_calculate_health_score_api_indisponivel(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        score = core.calculate_health_score(cpu=30, memory=40, api_latency_ms=-1, empathy_mes=0.8, rag_latency_ms=-1, win_rate=0.5)
        assert score > HEALTHY_THRESHOLD

    def test_get_summary_sem_dados(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        summary = core.get_summary()
        assert summary["status"] == "NO_DATA"

    def test_get_summary_com_dados(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        m = SystemMetrics(cpu_percent=30, memory_percent=40, system_health_score=0.85)
        core.register_snapshot(m)
        summary = core.get_summary()
        assert summary["status"] == "HEALTHY"
        assert summary["cpu_percent"] == 30

    def test_health_check_tudo_ok(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        m = SystemMetrics(cpu_percent=30, memory_percent=40, api_latency_ms=100, empathy_mes=0.85, rag_latency_avg_ms=200, system_health_score=0.85)
        core.register_snapshot(m)
        hc = core.health_check()
        assert hc["status"] == "HEALTHY"
        assert hc["all_subsystems_ok"] is True

    def test_health_check_cpu_alta(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        m = SystemMetrics(cpu_percent=95, memory_percent=40, api_latency_ms=100, empathy_mes=0.85, system_health_score=0.85)
        core.register_snapshot(m)
        hc = core.health_check()
        assert hc["subsystems"]["cpu"] is False

    def test_health_sem_dados(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        hc = core.health_check()
        assert hc["status"] == "NO_DATA"

    def test_get_history_limit(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        for i in range(20):
            core.register_snapshot(SystemMetrics(cpu_percent=float(i), memory_percent=float(i * 2)))
        hist = core.get_history(limit=5)
        assert len(hist) == 5
        assert hist[-1]["cpu_percent"] == 19.0

    def test_media_health_score(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        for i in range(5):
            core.register_snapshot(SystemMetrics(system_health_score=round(i / 10, 2)))
        media = core.get_average_health_score(window=5)
        assert 0.2 <= media <= 0.3

    def test_clear_history(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        core.register_snapshot(SystemMetrics(cpu_percent=50))
        assert core.get_latest() is not None
        core.clear_history()
        assert core.get_latest() is None
        assert core.get_average_health_score() == 0.0

    def test_max_history_respeitado(self, temp_history):
        core = AnalyticsCore(history_path=temp_history, max_history=5)
        for i in range(20):
            core.register_snapshot(SystemMetrics(cpu_percent=float(i)))
        assert len(core.history) == 5
        assert core.history[-1]["cpu_percent"] == 19.0

    def test_integration_fluxo_completo(self, temp_history):
        core = AnalyticsCore(history_path=temp_history)
        health = core.calculate_health_score(cpu=35, memory=50, api_latency_ms=120, empathy_mes=0.88, rag_latency_ms=400, win_rate=0.65)
        m = SystemMetrics(
            cpu_percent=35,
            memory_percent=50,
            disk_percent=55,
            rag_latency_avg_ms=400,
            empathy_mes=0.88,
            api_latency_ms=120,
            system_health_score=health,
            active_agents=3,
            total_queries_rag=150,
            signals_dispatched=45,
            signals_blocked=5,
            win_rate=0.65,
        )
        core.register_snapshot(m)
        summary = core.get_summary()
        hc = core.health_check()
        assert summary["status"] == "HEALTHY"
        assert hc["status"] == "HEALTHY"
        assert summary["active_agents"] == 3
        assert summary["total_records"] == 1
