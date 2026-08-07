"""
VISION_MODULE — Módulo de Percepção Visual da Ravena AI
========================================================
Este módulo implementa a camada de percepção visual que permite à Ravena
"enxergar" o ambiente digital através de análise de logs, streams de vídeo,
imagens de monitoramento e padrões de comportamento em tempo real.

Responsabilidades:
  - Processar logs como dados visuais estruturados.
  - Analisar streams de vídeo/imagens de monitoramento.
  - Detectar padrões de segurança (ataques, falhas, anomalias).
  - Integrar com RAG para contexto inteligente.
  - Orquestrar ações autônomas baseadas em percepção.

Arquitetura:
  O módulo segue o padrão de pipeline visual:
  Entrada Visual → Pré-processamento → Extração de Features → 
  Análise de Padrões → Decisão Autônoma → Ação via Omega
"""

import os
import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import deque
import re

# ============================================================
# ENUMS E TIPOS
# ============================================================

class TipoEntradaVisual(Enum):
    """Tipos de entrada visual que a Ravena pode processar."""
    LOG_TEXTO = "log_texto"
    LOG_ESTRUTURADO = "log_estruturado"
    IMAGEM_MONITORAMENTO = "imagem_monitoramento"
    VIDEO_STREAM = "video_stream"
    METRICAS_TEMPO_REAL = "metricas_tempo_real"
    PADROES_REDE = "padroes_rede"

class NivelAmeaca(Enum):
    """Níveis de ameaça detectados pela visão."""
    NORMAL = "normal"
    SUSPEITA = "suspeita"
    ALERTA = "alerta"
    CRITICA = "critica"

class TipoAnomalia(Enum):
    """Tipos de anomalias que a Ravena pode reconhecer."""
    ATAQUE_BRUTE_FORCE = "ataque_brute_force"
    EXFILTRAÇÃO_DADOS = "exfiltração_dados"
    FALHA_HARDWARE = "falha_hardware"
    DEGRADAÇÃO_PERFORMANCE = "degradação_performance"
    COMPORTAMENTO_ANÔMALO = "comportamento_anômalo"
    ACESSO_NÃO_AUTORIZADO = "acesso_não_autorizado"
    TENTATIVA_ESCALAÇÃO = "tentativa_escalação"
    ANOMALIA_REDE = "anomalia_rede"

# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class FeatureVisual:
    """Feature extraída de uma entrada visual."""
    tipo: str
    valor: Any
    confiança: float  # 0.0 a 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    contexto: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PatrãoDetectado:
    """Padrão detectado pela análise visual."""
    tipo_anomalia: TipoAnomalia
    nivel_ameaca: NivelAmeaca
    confiança: float
    features_relacionadas: List[FeatureVisual]
    descricao: str
    recomendação_ação: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class SnapshotVisual:
    """Snapshot de uma análise visual completa."""
    entrada_tipo: TipoEntradaVisual
    features_extraidas: List[FeatureVisual]
    padroes_detectados: List[PatrãoDetectado]
    nivel_ameaca_geral: NivelAmeaca
    confiança_geral: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

# ============================================================
# EXTRATOR DE FEATURES VISUAIS
# ============================================================

class ExtratordeFeaturesVisuais:
    """Extrai features de diferentes tipos de entrada visual."""

    def __init__(self):
        """Inicializa o extrator."""
        self.padroes_regex = {
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "porta": r":(\d{1,5})\b",
            "timestamp_log": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            "erro": r"(?:ERROR|FAIL|EXCEPTION|CRITICAL)\b",
            "autenticacao": r"(?:AUTH|LOGIN|PASSWORD|CREDENTIAL)",
            "acesso_negado": r"(?:DENIED|FORBIDDEN|UNAUTHORIZED|403|401)",
        }

    def extrair_de_log_texto(self, log: str) -> List[FeatureVisual]:
        """Extrai features de um log em texto."""
        features = []

        # Detectar IPs
        ips = re.findall(self.padroes_regex["ip_address"], log)
        for ip in ips:
            features.append(FeatureVisual(
                tipo="ip_detectado",
                valor=ip,
                confiança=0.95,
                contexto={"origem": "regex_ip"},
            ))

        # Detectar portas
        portas = re.findall(self.padroes_regex["porta"], log)
        for porta in portas:
            features.append(FeatureVisual(
                tipo="porta_detectada",
                valor=porta,
                confiança=0.90,
                contexto={"origem": "regex_porta"},
            ))

        # Detectar erros
        if re.search(self.padroes_regex["erro"], log):
            features.append(FeatureVisual(
                tipo="erro_detectado",
                valor=True,
                confiança=0.98,
                contexto={"origem": "regex_erro"},
            ))

        # Detectar atividades de autenticação
        if re.search(self.padroes_regex["autenticacao"], log):
            features.append(FeatureVisual(
                tipo="atividade_autenticacao",
                valor=True,
                confiança=0.92,
                contexto={"origem": "regex_auth"},
            ))

        # Detectar acessos negados
        if re.search(self.padroes_regex["acesso_negado"], log):
            features.append(FeatureVisual(
                tipo="acesso_negado",
                valor=True,
                confiança=0.97,
                contexto={"origem": "regex_acesso"},
            ))

        return features

    def extrair_de_metricas(self, metricas: Dict[str, Any]) -> List[FeatureVisual]:
        """Extrai features de métricas de tempo real."""
        features = []

        if "cpu_percent" in metricas:
            cpu = metricas["cpu_percent"]
            features.append(FeatureVisual(
                tipo="cpu_alto" if cpu > 80 else "cpu_normal",
                valor=cpu,
                confiança=0.99,
                contexto={"limiar": 80},
            ))

        if "memory_percent" in metricas:
            mem = metricas["memory_percent"]
            features.append(FeatureVisual(
                tipo="memoria_alta" if mem > 80 else "memoria_normal",
                valor=mem,
                confiança=0.99,
                contexto={"limiar": 80},
            ))

        if "disk_percent" in metricas:
            disco = metricas["disk_percent"]
            features.append(FeatureVisual(
                tipo="disco_cheio" if disco > 85 else "disco_normal",
                valor=disco,
                confiança=0.99,
                contexto={"limiar": 85},
            ))

        return features

# ============================================================
# ANALISADOR DE PADRÕES
# ============================================================

class AnalisadorDePadroes:
    """Analisa features para detectar padrões e anomalias."""

    def __init__(self, rag_context: Optional[Dict[str, Any]] = None):
        """
        Inicializa o analisador.
        
        Args:
            rag_context: Contexto do RAG com conhecimento técnico.
        """
        self.rag_context = rag_context or {}
        self.historico_features = deque(maxlen=1000)

    def analisar_features(self, features: List[FeatureVisual]) -> List[PatrãoDetectado]:
        """Analisa features para detectar padrões."""
        padroes = []
        self.historico_features.extend(features)

        # Detectar múltiplos acessos negados (possível ataque brute force)
        acessos_negados = [f for f in features if f.tipo == "acesso_negado"]
        if len(acessos_negados) >= 5:
            padroes.append(PatrãoDetectado(
                tipo_anomalia=TipoAnomalia.ATAQUE_BRUTE_FORCE,
                nivel_ameaca=NivelAmeaca.CRITICA,
                confiança=0.92,
                features_relacionadas=acessos_negados,
                descricao="Múltiplas tentativas de acesso negado detectadas em curto período",
                recomendação_ação="Bloquear IP origem, ativar Lockdown, notificar admin",
            ))

        # Detectar CPU/Memória alta (possível DoS ou falha)
        cpu_alto = [f for f in features if f.tipo == "cpu_alto"]
        mem_alta = [f for f in features if f.tipo == "memoria_alta"]
        if cpu_alto and mem_alta:
            padroes.append(PatrãoDetectado(
                tipo_anomalia=TipoAnomalia.DEGRADAÇÃO_PERFORMANCE,
                nivel_ameaca=NivelAmeaca.ALERTA,
                confiança=0.88,
                features_relacionadas=cpu_alto + mem_alta,
                descricao="CPU e memória elevadas simultaneamente",
                recomendação_ação="Investigar processos, considerar escalação",
            ))

        # Detectar disco cheio (falha potencial)
        disco_cheio = [f for f in features if f.tipo == "disco_cheio"]
        if disco_cheio:
            padroes.append(PatrãoDetectado(
                tipo_anomalia=TipoAnomalia.FALHA_HARDWARE,
                nivel_ameaca=NivelAmeaca.ALERTA,
                confiança=0.95,
                features_relacionadas=disco_cheio,
                descricao="Espaço em disco crítico",
                recomendação_ação="Liberar espaço, arquivar logs antigos",
            ))

        return padroes

    def calcular_nivel_ameaca_geral(self, padroes: List[PatrãoDetectado]) -> Tuple[NivelAmeaca, float]:
        """Calcula o nível de ameaça geral baseado nos padrões."""
        if not padroes:
            return NivelAmeaca.NORMAL, 0.0

        # Encontrar o padrão com maior confiança
        padrão_max = max(padroes, key=lambda p: p.confiança)

        if padrão_max.nivel_ameaca == NivelAmeaca.CRITICA:
            return NivelAmeaca.CRITICA, padrão_max.confiança
        elif padrão_max.nivel_ameaca == NivelAmeaca.ALERTA:
            return NivelAmeaca.ALERTA, padrão_max.confiança
        elif padrão_max.nivel_ameaca == NivelAmeaca.SUSPEITA:
            return NivelAmeaca.SUSPEITA, padrão_max.confiança

        return NivelAmeaca.NORMAL, 0.0

# ============================================================
# MÓDULO DE PERCEPÇÃO VISUAL
# ============================================================

class ModuloPercepçãoVisual:
    """Módulo principal de percepção visual da Ravena."""

    def __init__(self, rag_context: Optional[Dict[str, Any]] = None):
        """
        Inicializa o módulo.
        
        Args:
            rag_context: Contexto do RAG para análise inteligente.
        """
        self.rag_context = rag_context or {}
        self.extrator = ExtratordeFeaturesVisuais()
        self.analisador = AnalisadorDePadroes(rag_context)
        self.historico_snapshots = deque(maxlen=100)
        self._callbacks_ameaca = []

    def registrar_callback_ameaca(self, callback: Callable[[PatrãoDetectado], None]):
        """Registra callback para quando uma ameaça é detectada."""
        self._callbacks_ameaca.append(callback)

    def processar_entrada_visual(self, entrada: str, tipo: TipoEntradaVisual) -> SnapshotVisual:
        """Processa uma entrada visual e retorna análise completa."""
        features = []

        # Extrair features baseado no tipo
        if tipo == TipoEntradaVisual.LOG_TEXTO:
            features = self.extrator.extrair_de_log_texto(entrada)
        elif tipo == TipoEntradaVisual.METRICAS_TEMPO_REAL:
            try:
                metricas = json.loads(entrada)
                features = self.extrator.extrair_de_metricas(metricas)
            except json.JSONDecodeError:
                pass

        # Analisar features
        padroes = self.analisador.analisar_features(features)

        # Calcular nível de ameaça geral
        nivel_ameaca, confiança = self.analisador.calcular_nivel_ameaca_geral(padroes)

        # Criar snapshot
        snapshot = SnapshotVisual(
            entrada_tipo=tipo,
            features_extraidas=features,
            padroes_detectados=padroes,
            nivel_ameaca_geral=nivel_ameaca,
            confiança_geral=confiança,
        )

        # Armazenar no histórico
        self.historico_snapshots.append(snapshot)

        # Notificar callbacks se houver ameaça
        if nivel_ameaca != NivelAmeaca.NORMAL:
            for padrao in padroes:
                for callback in self._callbacks_ameaca:
                    try:
                        callback(padrao)
                    except Exception as e:
                        print(f"[VISION] Erro ao chamar callback: {e}")

        return snapshot

    def obter_historico_ameacas(self, ultimos_n: int = 50) -> List[Dict[str, Any]]:
        """Retorna histórico de ameaças detectadas."""
        ameacas = []
        for snapshot in list(self.historico_snapshots):
            if snapshot.nivel_ameaca != NivelAmeaca.NORMAL:
                for padrao in snapshot.padroes_detectados:
                    ameacas.append({
                        "tipo": padrao.tipo_anomalia.value,
                        "nivel": padrao.nivel_ameaca.value,
                        "confiança": padrao.confiança,
                        "descricao": padrao.descricao,
                        "recomendação": padrao.recomendação_ação,
                        "timestamp": padrao.timestamp,
                    })

        return ameacas[-ultimos_n:]

    def obter_status_visual(self) -> Dict[str, Any]:
        """Retorna status visual agregado."""
        snapshots = list(self.historico_snapshots)
        if not snapshots:
            return {
                "status": "sem_dados",
                "ameacas_detectadas": 0,
                "nivel_maximo": "normal",
            }

        snapshot_recente = snapshots[-1]
        ameacas_criticas = sum(1 for p in snapshot_recente.padroes_detectados if p.nivel_ameaca == NivelAmeaca.CRITICA)

        return {
            "status": "operacional",
            "ameacas_detectadas": len(snapshot_recente.padroes_detectados),
            "nivel_maximo": snapshot_recente.nivel_ameaca_geral.value,
            "confiança": snapshot_recente.confiança_geral,
            "criticas": ameacas_criticas,
            "timestamp": snapshot_recente.timestamp,
        }

# ============================================================
# SINGLETON GLOBAL
# ============================================================

_modulo_visao_global = None

def inicializar_visao(rag_context: Optional[Dict[str, Any]] = None) -> ModuloPercepçãoVisual:
    """Inicializa o módulo de percepção visual."""
    global _modulo_visao_global

    if _modulo_visao_global is None:
        _modulo_visao_global = ModuloPercepçãoVisual(rag_context)

    return _modulo_visao_global

def obter_visao() -> ModuloPercepçãoVisual:
    """Retorna o módulo de percepção visual global."""
    global _modulo_visao_global

    if _modulo_visao_global is None:
        _modulo_visao_global = ModuloPercepçãoVisual()

    return _modulo_visao_global

if __name__ == "__main__":
    # Demonstração
    visao = inicializar_visao()

    # Simular análise de log
    log_exemplo = """
    2026-04-09T16:35:22 ERROR: Failed login attempt from 192.168.1.100:5432
    2026-04-09T16:35:23 ERROR: Failed login attempt from 192.168.1.100:5432
    2026-04-09T16:35:24 ERROR: Failed login attempt from 192.168.1.100:5432
    2026-04-09T16:35:25 CRITICAL: Access DENIED for user admin
    2026-04-09T16:35:26 CRITICAL: Access DENIED for user root
    """

    snapshot = visao.processar_entrada_visual(log_exemplo, TipoEntradaVisual.LOG_TEXTO)

    print("=== Análise Visual ===")
    print(f"Tipo de Entrada: {snapshot.entrada_tipo.value}")
    print(f"Features Extraídas: {len(snapshot.features_extraidas)}")
    print(f"Padrões Detectados: {len(snapshot.padroes_detectados)}")
    print(f"Nível de Ameaça: {snapshot.nivel_ameaca_geral.value}")
    print(f"Confiança: {snapshot.confiança_geral:.2%}")

    print("\n=== Padrões Detectados ===")
    for padrao in snapshot.padroes_detectados:
        print(f"- {padrao.tipo_anomalia.value}: {padrao.descricao}")
        print(f"  Nível: {padrao.nivel_ameaca.value} | Confiança: {padrao.confiança:.2%}")
        print(f"  Ação: {padrao.recomendação_ação}")

    print("\n=== Status Visual ===")
    print(json.dumps(visao.obter_status_visual(), indent=2))
