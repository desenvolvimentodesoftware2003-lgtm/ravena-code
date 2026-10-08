"""Sensores: pipeline de ingestao cognitiva de dados internos e externos.

Disponibiliza:
- SensorManager: orquestrador de todos os sensores com historico e health check
- FileSensor: ingestao de arquivos (diretorios monitorados com deduplicacao)
- APISensor: polling de endpoints HTTP com suporte a GET/POST
- MetricSensor: coleta de metricas do sistema via psutil (CPU, RAM, disco)
- DataIngestionSensor: classe base abstrata para criacao de novos sensores
"""

from .sensors_core_v3_2_6 import (
    APISensor,
    DataIngestionSensor,
    FileSensor,
    MetricSensor,
    SensorManager,
    SensorStatus,
)

__all__ = [
    "SensorStatus",
    "DataIngestionSensor",
    "FileSensor",
    "APISensor",
    "MetricSensor",
    "SensorManager",
]
