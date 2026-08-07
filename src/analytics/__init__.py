"""Analytics: metricas unificadas do sistema e calculo de saude (HealthScore).

Disponibiliza:
- AnalyticsCore: agregacao de metricas de 6 sub-sistemas, persistencia historica, health check
- SystemMetrics: dataclass com snapshot completo de metricas do sistema
"""

from .analytics_core_v3_2_6 import AnalyticsCore, SystemMetrics

__all__ = ["AnalyticsCore", "SystemMetrics"]
