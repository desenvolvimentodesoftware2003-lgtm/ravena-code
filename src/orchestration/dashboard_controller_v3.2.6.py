import json
import time
from datetime import datetime
import logging

logger = logging.getLogger("DashboardController")

class DashboardController:
    """
    Interface lógica para monitoramento em tempo real das atividades dos agentes,
    consumo de recursos e performance do sistema.
    """
    
    def __init__(self, stats_path: str = "data/dashboard_stats.json"):
        self.stats_path = stats_path
        self.current_metrics = {
            "uptime": 0,
            "active_agents": 0,
            "tokens_consumed": 0,
            "latency_ms": 0,
            "last_update": ""
        }

    def update_metrics(self, agent_id: str, tokens: int, latency: float):
        """Atualiza as métricas de performance do dashboard."""
        self.current_metrics["active_agents"] += 1
        self.current_metrics["tokens_consumed"] += tokens
        self.current_metrics["latency_ms"] = (self.current_metrics["latency_ms"] + latency) / 2
        self.current_metrics["last_update"] = str(datetime.now())
        self._save_stats()
        logger.info(f"Métricas atualizadas para o agente {agent_id}.")

    def _save_stats(self):
        try:
            with open(self.stats_path, 'w') as f:
                json.dump(self.current_metrics, f, indent=4)
        except Exception as e:
            logger.error(f"Erro ao salvar estatísticas do dashboard: {str(e)}")

    def get_realtime_status(self) -> dict:
        """Retorna o estado atual para ser consumido pela UI."""
        return self.current_metrics

    def log_agent_activity(self, agent_id: str, action: str, status: str):
        """Registra atividades específicas para visualização no dashboard."""
        log_entry = {
            "timestamp": str(datetime.now()),
            "agent": agent_id,
            "action": action,
            "status": status
        }
        # Em produção, isso seria enviado para um WebSocket ou Redis
        print(f"[DASHBOARD LOG] {log_entry}")

if __name__ == "__main__":
    db = DashboardController()
    db.update_metrics("ChatAgent", 150, 45.5)
    print(db.get_realtime_status())
