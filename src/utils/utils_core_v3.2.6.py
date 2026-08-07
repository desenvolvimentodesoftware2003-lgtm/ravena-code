"""
RAVENA AI 3.0.0 — src/utils/utils_core.py
=========================================
Módulo de Utilitários e Observabilidade Refatorado.
Implementa MCP Mapper, Metrics Exporter e Dashboard Integration.
Baseado em: mcp_mapper.py, metrics_exporter.py e dashboard_integration.py (Legado).
"""

import os
import time
import json
import logging
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
from dataclasses import dataclass, field

# Configuração de Logging
logger = logging.getLogger("ravena.utils_core")

@dataclass
class MetricasSistema:
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    rag_latency_avg: float = 0.0
    total_queries_rag: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class ColetorMetricas:
    """Coletor de métricas de hardware e performance em tempo real."""
    def __init__(self, buffer_size: int = 100):
        self.historico = deque(maxlen=buffer_size)
        self.alertas = []
        self.rag_latencies = deque(maxlen=buffer_size)
        self.total_queries = 0

    def registrar_latencia_rag(self, latencia: float):
        self.rag_latencies.append(latencia)
        self.total_queries += 1

    def coletar_agora(self) -> MetricasSistema:
        avg_latency = sum(self.rag_latencies) / len(self.rag_latencies) if self.rag_latencies else 0.0
        m = MetricasSistema(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent,
            rag_latency_avg=round(avg_latency, 4),
            total_queries_rag=self.total_queries
        )
        self.historico.append(m)
        
        # Lógica de alerta simples
        if m.cpu_percent > 90 or m.memory_percent > 90:
            logger.warning(f"ALERTA DE RECURSOS: CPU {m.cpu_percent}%, MEM {m.memory_percent}%")
            self.alertas.append(f"Alta utilização detectada em {m.timestamp}")
            
        return m

class MCPMapperCore:
    """Mapeia e categoriza habilidades de servidores MCP."""
    def __init__(self, registry_path: str = "./config/mcp_registry.json"):
        self.registry_path = registry_path
        self.skills = {}
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)

    def mapear_habilidade(self, nome: str, descricao: str, endpoint: str):
        """Mapeia uma nova skill MCP e salva no registro local."""
        skill = {
            "nome": nome,
            "descricao": descricao,
            "endpoint": endpoint,
            "mapeado_em": datetime.now().isoformat()
        }
        self.skills[nome] = skill
        
        # Salvar registro
        with open(self.registry_path, "w") as f:
            json.dump(self.skills, f, indent=2)
            
        logger.info(f"Habilidade MCP mapeada: {nome}")
        return skill

class DashboardAdapter:
    """Integra métricas e status para visualização em dashboard."""
    def __init__(self, coletor: ColetorMetricas, mcp: MCPMapperCore):
        self.coletor = coletor
        self.mcp = mcp

    def gerar_snapshot_dashboard(self) -> Dict[str, Any]:
        """Gera um snapshot completo do sistema para o dashboard."""
        metricas = self.coletor.coletar_agora()
        return {
            "metricas": metricas.__dict__,
            "skills_mcp": list(self.mcp.skills.keys()),
            "alertas_ativos": self.coletor.alertas[-5:], # Últimos 5 alertas
            "timestamp": datetime.now().isoformat()
        }

class AgenteDevCore:
    """Agente especializado em desenvolvimento de software e resolução técnica."""
    def __init__(self, nome="Ravena_Dev"):
        self.nome = nome
        self.especialidades = ["Python", "Arquitetura", "Resolução de Problemas", "Boas Práticas"]

    def resolver_problema(self, enunciado: str) -> Dict[str, Any]:
        """Aplica lógica de desenvolvimento para resolver desafios técnicos."""
        logger.info(f"Agente Dev analisando: {enunciado[:50]}...")
        
        # Lógica de Resolução (Refatorada do legado)
        if "LRU" in enunciado.upper() or "CACHE" in enunciado.upper():
            return {
                "analise": "O desafio de cache LRU exige operações O(1).",
                "logica": "Uso de OrderedDict (Hash Map + Doubly Linked List).",
                "codigo": "from collections import OrderedDict\nclass LRUCache..."
            }
        
        return {
            "analise": "Análise técnica padrão.",
            "logica": "Eficiência algorítmica em Python.",
            "codigo": f"# Solução para: {enunciado}"
        }

class UtilsCore:
    """Núcleo de Utilitários da Ravena AI 3.0.0."""
    def __init__(self):
        self.metrics = ColetorMetricas()
        self.mcp = MCPMapperCore()
        self.dashboard = DashboardAdapter(self.metrics, self.mcp)
        self.dev = AgenteDevCore()
        
    def exportar_diagnostico_completo(self) -> str:
        """Exporta um diagnóstico textual completo do sistema."""
        snapshot = self.dashboard.gerar_snapshot_dashboard()
        return json.dumps(snapshot, indent=2)
