import os
import sys
import json
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.sensors.sensors_core_v3_2_6 import (
    SensorStatus,
    DataIngestionSensor,
    FileSensor,
    APISensor,
    MetricSensor,
    SensorManager,
)


class TestSensorStatus:
    def test_values(self):
        assert SensorStatus.INACTIVE.value == "inactive"
        assert SensorStatus.ACTIVE.value == "active"
        assert SensorStatus.ERROR.value == "error"
        assert SensorStatus.DISABLED.value == "disabled"


class TestFileSensor:
    def test_coleta_arquivos(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.log"), "w") as f:
                f.write("ERROR: test log line\n")
            with open(os.path.join(tmpdir, "data.json"), "w") as f:
                json.dump({"key": "value"}, f)
            with open(os.path.join(tmpdir, "not_watched.txt"), "w") as f:
                f.write("skip")
            sensor = FileSensor("test_fs", watch_dir=tmpdir, extensions=[".log", ".json"])
            records = sensor.run_once()
            assert len(records) == 2
            sources = [r["source"] for r in records]
            assert "test.log" in sources
            assert "data.json" in sources
            assert sensor.items_ingested == 2
            assert sensor.status == SensorStatus.ACTIVE

    def test_diretorio_inexistente(self):
        sensor = FileSensor("bad_dir", watch_dir="/nonexistent/path/xyz")
        records = sensor.run_once()
        assert len(records) == 0

    def test_arquivos_ja_processados(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = os.path.join(tmpdir, "test.log")
            with open(fpath, "w") as f:
                f.write("content")
            sensor = FileSensor("dedup", watch_dir=tmpdir)
            r1 = sensor.run_once()
            assert len(r1) == 1
            r2 = sensor.run_once()
            assert len(r2) == 0

    def test_get_info(self):
        sensor = FileSensor("info_test", watch_dir="/tmp")
        info = sensor.get_info()
        assert info["name"] == "info_test"
        assert info["watch_dir"] == "/tmp"
        assert info["processed_files"] == 0

    def test_registra_callback(self):
        results = []
        def cb(data):
            results.append(data)
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "a.log"), "w") as f:
                f.write("cb test")
            sensor = FileSensor("cb_fs", watch_dir=tmpdir)
            sensor.register_callback(cb)
            sensor.run_once()
        assert len(results) == 1
        assert results[0]["sensor"] == "cb_fs"


class TestAPISensor:
    def test_get_info(self):
        sensor = APISensor("api_test", endpoint="https://api.example.com/data")
        info = sensor.get_info()
        assert info["name"] == "api_test"
        assert info["endpoint"] == "https://api.example.com/data"
        assert info["method"] == "GET"

    def test_erro_rede(self):
        sensor = APISensor("bad_api", endpoint="https://invalid.nonexistent.api.test.xyz")
        records = sensor.run_once()
        assert len(records) == 0
        assert sensor.status == SensorStatus.ERROR


class TestMetricSensor:
    def test_coleta_metricas(self):
        sensor = MetricSensor("sys_metrics")
        records = sensor.run_once()
        if records:
            assert len(records) == 1
            assert records[0]["content_type"] == "metrics"
            assert "cpu_percent" in records[0]["content"]
            assert sensor.status == SensorStatus.ACTIVE

    def test_get_info(self):
        sensor = MetricSensor("m_info")
        info = sensor.get_info()
        assert info["name"] == "m_info"


class TestSensorManager:
    def test_register_e_get(self):
        mgr = SensorManager()
        sensor = FileSensor("fs1", watch_dir="/tmp")
        mgr.register(sensor)
        assert mgr.get("fs1") is sensor
        assert mgr.get("nonexistent") is None

    def test_run_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "a.log"), "w") as f:
                f.write("line1")
            mgr = SensorManager()
            mgr.register(FileSensor("fs1", watch_dir=tmpdir))
            results = mgr.run_all()
            assert "fs1" in results
            assert results["fs1"]["records"] == 1

    def test_run_sensor_inexistente(self):
        mgr = SensorManager()
        result = mgr.run_sensor("no_sensor")
        assert result is None

    def test_get_all_info(self):
        mgr = SensorManager()
        mgr.register(FileSensor("fs1", watch_dir="/tmp"))
        mgr.register(APISensor("api1", endpoint="https://example.com"))
        info = mgr.get_all_info()
        assert "fs1" in info
        assert "api1" in info

    def test_health_check_vazio(self):
        mgr = SensorManager()
        hc = mgr.health_check()
        assert hc["total_sensors"] == 0
        assert hc["all_ok"] is False

    def test_health_check_com_sensores(self):
        mgr = SensorManager()
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "f.log"), "w") as f:
                f.write("data")
            mgr.register(FileSensor("fs1", watch_dir=tmpdir))
            mgr.run_all()
            hc = mgr.health_check()
            assert hc["total_sensors"] == 1
            assert hc["active"] == 1

    def test_registro_historico(self):
        mgr = SensorManager()
        mgr.register(APISensor("bad", endpoint="https://invalid.test.xyz"))
        mgr.run_all()
        hist = mgr.get_recent_history()
        assert len(hist) == 0

    def test_clear_history(self):
        mgr = SensorManager()
        mgr.register(MetricSensor("m1"))
        mgr.run_all()
        mgr.clear_history()
        assert len(mgr.get_recent_history()) == 0

    def test_callback_via_manager(self):
        results = []
        def cb(data):
            results.append(data["source"])
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "cb.log"), "w") as f:
                f.write("callback data")
            sensor = FileSensor("cb_mgr", watch_dir=tmpdir)
            sensor.register_callback(cb)
            mgr = SensorManager()
            mgr.register(sensor)
            mgr.run_all()
        assert len(results) == 1
        assert "cb.log" in results
