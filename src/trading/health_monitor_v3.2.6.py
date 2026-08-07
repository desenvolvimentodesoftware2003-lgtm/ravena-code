"""
HEALTH_MONITOR — Monitor de Saúde do Self-Healing V2.2.0
=========================================================
Ravena AI Trading Bot | Versão: 2.2.0 | Data: 11 de Abril de 2026

Este módulo é o "sistema nervoso central" do Omega Self-Healing.
Ele recebe os relatórios de saúde da SignalBridge como sensor primário
e decide quando acionar o fallback (Emulador de Cliques) ou emitir
alertas para o Telegram.

Responsabilidades:
  - Monitorar a latência da API Bybit em tempo real.
  - Receber o heartbeat da SignalBridge e validar seu estado.
  - Acionar o protocolo Soberania Omega quando a API falha.
  - Registrar todos os eventos de saúde no log de auditoria.
"""

import time
import logging
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ravena.health_monitor")


class SystemHealth(Enum):
    """Estado de saúde geral do sistema."""
    HEALTHY   = "HEALTHY"    # Tudo funcionando normalmente
    DEGRADED  = "DEGRADED"   # API lenta mas funcional
    CRITICAL  = "CRITICAL"   # API fora do ar — fallback ativo
    UNKNOWN   = "UNKNOWN"    # Estado não determinado


class HealthMonitor:
    """
    Monitor de Saúde do Self-Healing V2.2.0.

    Atua como o "árbitro" entre a SignalBridge e o DayTradeAgent,
    garantindo que os sinais cheguem na ponta da execução mesmo
    quando a API da Bybit está instável.
    """

    def __init__(
        self,
        api_timeout_ms: int = 800,
        check_interval_sec: int = 30,
        alert_callback: Optional[Callable] = None
    ):
        """
        Args:
            api_timeout_ms: Latência máxima tolerada antes de acionar fallback.
            check_interval_sec: Intervalo entre verificações de saúde.
            alert_callback: Função de callback para enviar alertas (ex: Telegram).
        """
        self.api_timeout_ms = api_timeout_ms
        self.check_interval_sec = check_interval_sec
        self.alert_callback = alert_callback
        self.system_health = SystemHealth.UNKNOWN
        self._last_check = 0.0
        self._api_latency_history = []
        self._bridge_reports = []

    def check_api_health(self, bybit_url: str = "https://api.bybit.com") -> Dict[str, Any]:
        """
        Verifica a saúde da API Bybit medindo a latência do endpoint de tempo.

        Returns:
            Dicionário com latência, status e método de execução recomendado.
        """
        import requests

        ping_url = f"{bybit_url}/v5/market/time"
        start = time.time()
        try:
            resp = requests.get(ping_url, timeout=2)
            latency_ms = (time.time() - start) * 1000
            self._api_latency_history.append(latency_ms)

            # Manter apenas os últimos 10 registros
            if len(self._api_latency_history) > 10:
                self._api_latency_history.pop(0)

            avg_latency = sum(self._api_latency_history) / len(self._api_latency_history)

            if latency_ms <= self.api_timeout_ms:
                self.system_health = SystemHealth.HEALTHY
                execution_method = "API"
            elif latency_ms <= self.api_timeout_ms * 2:
                self.system_health = SystemHealth.DEGRADED
                execution_method = "API"  # Ainda tenta a API, mas com alerta
                logger.warning(
                    f"[HEALTH] API DEGRADADA: {latency_ms:.0f}ms "
                    f"(threshold: {self.api_timeout_ms}ms)"
                )
            else:
                self.system_health = SystemHealth.CRITICAL
                execution_method = "CLICK_EMULATOR"
                self._trigger_soberania_omega(latency_ms)

            return {
                "status": self.system_health.value,
                "latency_ms": round(latency_ms, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "execution_method": execution_method,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.system_health = SystemHealth.CRITICAL
            logger.error(f"[HEALTH] API Bybit inacessível: {e}")
            self._trigger_soberania_omega(timeout=True)
            return {
                "status": SystemHealth.CRITICAL.value,
                "latency_ms": -1,
                "avg_latency_ms": -1,
                "execution_method": "CLICK_EMULATOR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def receive_bridge_report(self, report: Dict[str, Any]) -> None:
        """
        Recebe o relatório de saúde da SignalBridge.
        A SignalBridge é o sensor primário do HealthMonitor.
        """
        self._bridge_reports.append(report)
        logger.info(
            f"[HEALTH] Relatório da Bridge recebido | "
            f"Status: {report.get('status')} | "
            f"Despachados: {report.get('total_dispatched')} | "
            f"Bloqueados: {report.get('total_blocked')}"
        )

        # Verificar se a bridge está em estado de fallback
        if report.get("status") == "FALLBACK":
            logger.warning(
                "[HEALTH] Bridge em modo FALLBACK — "
                "Soberania Omega ativo via Emulador de Cliques."
            )
            if self.alert_callback:
                self.alert_callback(
                    "WARNING",
                    "⚡ Soberania Omega ativado: Bridge usando Emulador de Cliques."
                )

    def get_system_status(self) -> Dict[str, Any]:
        """Retorna o status completo do sistema para o dashboard."""
        avg_latency = (
            sum(self._api_latency_history) / len(self._api_latency_history)
            if self._api_latency_history else -1
        )
        return {
            "system_health": self.system_health.value,
            "api_avg_latency_ms": round(avg_latency, 2),
            "api_timeout_threshold_ms": self.api_timeout_ms,
            "bridge_reports_received": len(self._bridge_reports),
            "last_bridge_status": (
                self._bridge_reports[-1].get("status")
                if self._bridge_reports else "N/A"
            ),
            "timestamp": datetime.now().isoformat()
        }

    def _trigger_soberania_omega(
        self,
        latency_ms: float = 0,
        timeout: bool = False
    ) -> None:
        """
        Aciona o protocolo Soberania Omega quando a API falha.
        Notifica o sistema para redirecionar todos os comandos
        ao Emulador de Cliques.
        """
        msg = (
            f"🔴 SOBERANIA OMEGA ATIVADO: "
            f"{'Timeout de conexão' if timeout else f'Latência crítica ({latency_ms:.0f}ms)'}. "
            f"Redirecionando para Emulador de Cliques."
        )
        logger.critical(f"[HEALTH] {msg}")

        if self.alert_callback:
            self.alert_callback("CRITICAL", msg)
