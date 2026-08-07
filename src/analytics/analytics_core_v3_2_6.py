import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger("ravena.analytics_core")

HEALTHY_THRESHOLD = 0.7
WARNING_THRESHOLD = 0.4

@dataclass
class SystemMetrics:
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    rag_latency_avg_ms: float = 0.0
    empathy_mes: float = 0.0
    api_latency_ms: float = 0.0
    system_health_score: float = 0.0
    active_agents: int = 0
    total_queries_rag: int = 0
    signals_dispatched: int = 0
    signals_blocked: int = 0
    win_rate: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AnalyticsCore:
    def __init__(self, history_path: str = "data/analytics_history.json", max_history: int = 500):
        self.history_path = history_path
        self.history: deque = deque(maxlen=max_history)
        self._ensure_data_dir()
        self._load_history()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.history_path) or ".", exist_ok=True)

    def _load_history(self):
        try:
            with open(self.history_path) as f:
                data = json.load(f)
                for item in data[-self.history.maxlen:]:
                    self.history.append(item)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def _save_history(self):
        try:
            with open(self.history_path, "w") as f:
                json.dump(list(self.history), f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar historico de metricas: {e}")

    def register_snapshot(self, metrics: SystemMetrics) -> Dict[str, Any]:
        snapshot = {
            "timestamp": metrics.timestamp,
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_percent": metrics.disk_percent,
            "rag_latency_avg_ms": metrics.rag_latency_avg_ms,
            "empathy_mes": metrics.empathy_mes,
            "api_latency_ms": metrics.api_latency_ms,
            "system_health_score": metrics.system_health_score,
            "active_agents": metrics.active_agents,
            "total_queries_rag": metrics.total_queries_rag,
            "signals_dispatched": metrics.signals_dispatched,
            "signals_blocked": metrics.signals_blocked,
            "win_rate": metrics.win_rate,
        }
        self.history.append(snapshot)
        self._save_history()
        return snapshot

    def calculate_health_score(
        self,
        cpu: float,
        memory: float,
        api_latency_ms: float,
        empathy_mes: float,
        rag_latency_ms: float,
        win_rate: float = 0.0,
    ) -> float:
        weights = {"cpu": 0.15, "memory": 0.15, "api": 0.25, "empathy": 0.20, "rag": 0.15, "win_rate": 0.10}
        cpu_score = max(0.0, 1.0 - cpu / 100.0)
        mem_score = max(0.0, 1.0 - memory / 100.0)
        api_score = 1.0 if api_latency_ms < 0 else max(0.0, 1.0 - api_latency_ms / 2000.0)
        empathy_score = max(0.0, empathy_mes)
        rag_score = 1.0 if rag_latency_ms < 0 else max(0.0, 1.0 - rag_latency_ms / 5000.0)
        win_score = max(0.0, win_rate)
        score = (
            cpu_score * weights["cpu"]
            + mem_score * weights["memory"]
            + api_score * weights["api"]
            + empathy_score * weights["empathy"]
            + rag_score * weights["rag"]
            + win_score * weights["win_rate"]
        )
        return round(score, 4)

    def get_latest(self) -> Optional[Dict[str, Any]]:
        return self.history[-1] if self.history else None

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return list(self.history)[-limit:]

    def get_average_health_score(self, window: int = 10) -> float:
        recent = list(self.history)[-window:]
        if not recent:
            return 0.0
        scores = [s.get("system_health_score", 0) for s in recent]
        return round(sum(scores) / len(scores), 4)

    def get_summary(self) -> Dict[str, Any]:
        latest = self.get_latest()
        if not latest:
            return {"status": "NO_DATA", "message": "Nenhuma metrica registrada"}
        avg_health = self.get_average_health_score()
        status = "HEALTHY" if avg_health >= HEALTHY_THRESHOLD else "WARNING" if avg_health >= WARNING_THRESHOLD else "CRITICAL"
        return {
            "status": status,
            "health_score": latest.get("system_health_score", 0),
            "avg_health_score_10": avg_health,
            "empathy_mes": latest.get("empathy_mes", 0),
            "api_latency_ms": latest.get("api_latency_ms", 0),
            "rag_latency_avg_ms": latest.get("rag_latency_avg_ms", 0),
            "win_rate": latest.get("win_rate", 0),
            "cpu_percent": latest.get("cpu_percent", 0),
            "memory_percent": latest.get("memory_percent", 0),
            "active_agents": latest.get("active_agents", 0),
            "signals_dispatched": latest.get("signals_dispatched", 0),
            "signals_blocked": latest.get("signals_blocked", 0),
            "total_records": len(self.history),
            "timestamp": latest.get("timestamp"),
        }

    def health_check(self) -> Dict[str, Any]:
        latest = self.get_latest()
        if not latest:
            return {"status": "NO_DATA", "subsystems": {}}
        score = latest.get("system_health_score", 0)
        subsystems = {
            "cpu": latest.get("cpu_percent", 0) < 90,
            "memory": latest.get("memory_percent", 0) < 90,
            "api": latest.get("api_latency_ms", 0) < 1000 or latest.get("api_latency_ms", 0) < 0,
            "empathy": latest.get("empathy_mes", 0) >= HEALTHY_THRESHOLD,
            "rag": latest.get("rag_latency_avg_ms", 0) < 3000 or latest.get("rag_latency_avg_ms", 0) < 0,
        }
        all_ok = all(subsystems.values())
        return {
            "status": "HEALTHY" if (score >= HEALTHY_THRESHOLD and all_ok) else "DEGRADED" if score >= WARNING_THRESHOLD else "CRITICAL",
            "system_health_score": score,
            "subsystems": subsystems,
            "all_subsystems_ok": all_ok,
        }

    def clear_history(self):
        self.history.clear()
        self._save_history()
        logger.info("Historico de metricas limpo")
