"""Visao computacional: pipeline de percepcao visual, extracao de features e deteccao de anomalias.

Disponibiliza:
- VisionPipeline: API simplificada para processamento de logs e metricas
- ModuloPercepcaoVisual: pipeline completo com callbacks e historico de ameacas
- ExtratorDeFeaturesVisuais: extracao de features de logs (regex) e metricas (thresholds)
- AnalisadorDePadroes: deteccao de padroes (brute force, degradacao, falha de hardware)
- VisionRAGSemantic: ponte entre visao e RAG para contexto tecnico
"""

from .vision_pipeline_v3_2_6 import (
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

__all__ = [
    "TipoEntradaVisual",
    "NivelAmeaca",
    "TipoAnomalia",
    "FeatureVisual",
    "PadreDetectado",
    "SnapshotVisual",
    "ExtratorDeFeaturesVisuais",
    "AnalisadorDePadroes",
    "ModuloPercepcaoVisual",
    "VisionPipeline",
    "inicializar_visao",
    "obter_visao",
]
