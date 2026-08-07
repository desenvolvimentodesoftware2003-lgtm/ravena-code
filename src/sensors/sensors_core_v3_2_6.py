import os
import json
import time
import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from collections import deque

logger = logging.getLogger("ravena.sensors_core")


class SensorStatus(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class DataIngestionSensor(ABC):
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.status = SensorStatus.INACTIVE
        self.last_run: Optional[str] = None
        self.items_ingested = 0
        self.errors = 0
        self._callbacks: List[Callable] = []

    def register_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._callbacks.append(callback)

    def _notify(self, data: Dict[str, Any]):
        for cb in self._callbacks:
            try:
                cb(data)
            except Exception as e:
                logger.error(f"Callback error in sensor '{self.name}': {e}")

    def _make_record(self, source: str, content: Any, content_type: str = "raw") -> Dict[str, Any]:
        raw = json.dumps(content, default=str) if not isinstance(content, str) else content
        return {
            "id": hashlib.md5(raw.encode()).hexdigest()[:12],
            "sensor": self.name,
            "source": source,
            "content_type": content_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        pass

    def run_once(self) -> List[Dict[str, Any]]:
        try:
            records = self.collect()
            self.items_ingested += len(records)
            self.last_run = datetime.now().isoformat()
            self.status = SensorStatus.ACTIVE
            for record in records:
                self._notify(record)
            return records
        except Exception as e:
            self.errors += 1
            self.status = SensorStatus.ERROR
            logger.error(f"Sensor '{self.name}' failed: {e}")
            return []

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "last_run": self.last_run,
            "items_ingested": self.items_ingested,
            "errors": self.errors,
        }


class FileSensor(DataIngestionSensor):
    def __init__(self, name: str, watch_dir: str, extensions: Optional[List[str]] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.watch_dir = watch_dir
        self.extensions = extensions or [".json", ".log", ".txt", ".csv"]
        self._processed_files: set = set()

    def collect(self) -> List[Dict[str, Any]]:
        records = []
        if not os.path.isdir(self.watch_dir):
            logger.warning(f"Watch dir '{self.watch_dir}' not found")
            return records
        for fname in os.listdir(self.watch_dir):
            fpath = os.path.join(self.watch_dir, fname)
            if not os.path.isfile(fpath):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in self.extensions:
                continue
            if fpath in self._processed_files:
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self._processed_files.add(fpath)
                records.append(self._make_record(source=fname, content=content, content_type=ext.lstrip(".")))
                logger.info(f"FileSensor '{self.name}' ingested: {fname}")
            except Exception as e:
                logger.error(f"FileSensor '{self.name}' error reading {fname}: {e}")
        return records

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info["watch_dir"] = self.watch_dir
        info["processed_files"] = len(self._processed_files)
        return info


class APISensor(DataIngestionSensor):
    def __init__(self, name: str, endpoint: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.endpoint = endpoint
        self.method = method.upper()
        self.headers = headers or {}

    def collect(self) -> List[Dict[str, Any]]:
        import requests
        if self.method == "GET":
            resp = requests.get(self.endpoint, headers=self.headers, timeout=self.config.get("timeout", 10))
        elif self.method == "POST":
            resp = requests.post(self.endpoint, headers=self.headers, json=self.config.get("body", {}), timeout=self.config.get("timeout", 10))
        else:
            logger.warning(f"Unsupported method {self.method}")
            return []
        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception:
                data = resp.text
            return [self._make_record(source=self.endpoint, content=data, content_type="json" if isinstance(data, dict) else "text")]
        else:
            logger.warning(f"APISensor '{self.name}' returned {resp.status_code}")
            return []

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info["endpoint"] = self.endpoint
        info["method"] = self.method
        return info


class MetricSensor(DataIngestionSensor):
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)

    def collect(self) -> List[Dict[str, Any]]:
        try:
            import psutil
            metrics = {
                "cpu_percent": psutil.cpu_percent(interval=0),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "cpu_count": psutil.cpu_count(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
            return [self._make_record(source="system", content=metrics, content_type="metrics")]
        except ImportError:
            return []


class SensorManager:
    def __init__(self):
        self.sensors: Dict[str, DataIngestionSensor] = {}
        self._run_history: deque = deque(maxlen=200)

    def register(self, sensor: DataIngestionSensor):
        self.sensors[sensor.name] = sensor
        logger.info(f"Sensor registered: {sensor.name}")

    def get(self, name: str) -> Optional[DataIngestionSensor]:
        return self.sensors.get(name)

    def run_all(self) -> Dict[str, Any]:
        results = {}
        for name, sensor in self.sensors.items():
            records = sensor.run_once()
            results[name] = {"records": len(records), "status": sensor.status.value}
            for record in records:
                self._run_history.append(record)
        return results

    def run_sensor(self, name: str) -> Optional[List[Dict[str, Any]]]:
        sensor = self.sensors.get(name)
        if not sensor:
            logger.warning(f"Sensor '{name}' not found")
            return None
        records = sensor.run_once()
        for record in records:
            self._run_history.append(record)
        return records

    def get_all_info(self) -> Dict[str, Any]:
        return {name: s.get_info() for name, s in self.sensors.items()}

    def health_check(self) -> Dict[str, Any]:
        total = len(self.sensors)
        active = sum(1 for s in self.sensors.values() if s.status == SensorStatus.ACTIVE)
        errors = sum(1 for s in self.sensors.values() if s.status == SensorStatus.ERROR)
        return {
            "total_sensors": total,
            "active": active,
            "errors": errors,
            "total_ingested": sum(s.items_ingested for s in self.sensors.values()),
            "all_ok": errors == 0 and total > 0,
        }

    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self._run_history)[-limit:]

    def clear_history(self):
        self._run_history.clear()
        for sensor in self.sensors.values():
            sensor.items_ingested = 0
            sensor.errors = 0
