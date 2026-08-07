"""Memoria: sistema de memoria episodica e semantica com persistencia JSON.

Disponibiliza:
- MemoryManager: gerenciador unificado de memoria (episodica + semantica)
- EpisodicMemory: memoria de curto prazo (historico de interacoes por usuario)
- SemanticMemory: memoria de longo prazo (fatos e conhecimento categorizado)
"""

from .memory_core_v3_2_6 import MemoryManager, EpisodicMemory, SemanticMemory

__all__ = ["MemoryManager", "EpisodicMemory", "SemanticMemory"]
