import json
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from collections import deque

logger = logging.getLogger("ravena.vision_pipeline")


class TipoEntradaVisual(Enum):
    LOG_TEXTO = "log_texto"
    LOG_ESTRUTURADO = "log_estruturado"
    IMAGEM_MONITORAMENTO = "imagem_monitoramento"
    VIDEO_STREAM = "video_stream"
    METRICAS_TEMPO_REAL = "metricas_tempo_real"
    PADROES_REDE = "padroes_rede"


class NivelAmeaca(Enum):
    NORMAL = "normal"
    SUSPEITA = "suspeita"
    ALERTA = "alerta"
    CRITICA = "critica"


class TipoAnomalia(Enum):
    ATAQUE_BRUTE_FORCE = "ataque_brute_force"
    EXFILTRACAO_DADOS = "exfiltracao_dados"
    FALHA_HARDWARE = "falha_hardware"
    DEGRADACAO_PERFORMANCE = "degradacao_performance"
    COMPORTAMENTO_ANOMALO = "comportamento_anomalo"
    ACESSO_NAO_AUTORIZADO = "acesso_nao_autorizado"
    TENTATIVA_ESCALACAO = "tentativa_escalacao"
    ANOMALIA_REDE = "anomalia_rede"


@dataclass
class FeatureVisual:
    tipo: str
    valor: Any
    confianca: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    contexto: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PadreDetectado:
    tipo_anomalia: TipoAnomalia
    nivel_ameaca: NivelAmeaca
    confianca: float
    features_relacionadas: List[FeatureVisual]
    descricao: str
    recomendacao_acao: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SnapshotVisual:
    entrada_tipo: TipoEntradaVisual
    features_extraidas: List[FeatureVisual]
    padroes_detectados: List[PadreDetectado]
    nivel_ameaca_geral: NivelAmeaca
    confianca_geral: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ExtratorDeFeaturesVisuais:
    def __init__(self):
        self.padroes_regex = {
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
            "porta": r":(\d{1,5})\b",
            "timestamp_log": r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            "erro": r"(?:ERROR|FAIL|EXCEPTION|CRITICAL)\b",
            "autenticacao": r"(?:AUTH|LOGIN|PASSWORD|CREDENTIAL)",
            "acesso_negado": r"(?:DENIED|FORBIDDEN|UNAUTHORIZED|403|401)",
        }

    def extrair_de_log_texto(self, log: str) -> List[FeatureVisual]:
        features = []
        ips = re.findall(self.padroes_regex["ip_address"], log)
        for ip in ips:
            features.append(FeatureVisual(tipo="ip_detectado", valor=ip, confianca=0.95, contexto={"origem": "regex_ip"}))
        portas = re.findall(self.padroes_regex["porta"], log)
        for porta in portas:
            features.append(FeatureVisual(tipo="porta_detectada", valor=porta, confianca=0.90, contexto={"origem": "regex_porta"}))
        if re.search(self.padroes_regex["erro"], log):
            features.append(FeatureVisual(tipo="erro_detectado", valor=True, confianca=0.98, contexto={"origem": "regex_erro"}))
        if re.search(self.padroes_regex["autenticacao"], log):
            features.append(FeatureVisual(tipo="atividade_autenticacao", valor=True, confianca=0.92, contexto={"origem": "regex_auth"}))
        if re.search(self.padroes_regex["acesso_negado"], log):
            features.append(FeatureVisual(tipo="acesso_negado", valor=True, confianca=0.97, contexto={"origem": "regex_acesso"}))
        return features

    def extrair_de_metricas(self, metricas: Dict[str, Any]) -> List[FeatureVisual]:
        features = []
        if "cpu_percent" in metricas:
            cpu = metricas["cpu_percent"]
            features.append(FeatureVisual(tipo="cpu_alto" if cpu > 80 else "cpu_normal", valor=cpu, confianca=0.99, contexto={"limiar": 80}))
        if "memory_percent" in metricas:
            mem = metricas["memory_percent"]
            features.append(FeatureVisual(tipo="memoria_alta" if mem > 80 else "memoria_normal", valor=mem, confianca=0.99, contexto={"limiar": 80}))
        if "disk_percent" in metricas:
            disco = metricas["disk_percent"]
            features.append(FeatureVisual(tipo="disco_cheio" if disco > 85 else "disco_normal", valor=disco, confianca=0.99, contexto={"limiar": 85}))
        return features

    def extrair(self, entrada: str, tipo: TipoEntradaVisual) -> List[FeatureVisual]:
        if tipo == TipoEntradaVisual.LOG_TEXTO:
            return self.extrair_de_log_texto(entrada)
        elif tipo == TipoEntradaVisual.METRICAS_TEMPO_REAL:
            try:
                metricas = json.loads(entrada)
                return self.extrair_de_metricas(metricas)
            except json.JSONDecodeError:
                return []
        return []


class AnalisadorDePadroes:
    def __init__(self, rag_context: Optional[Dict[str, Any]] = None):
        self.rag_context = rag_context or {}
        self.historico_features = deque(maxlen=1000)

    def analisar_features(self, features: List[FeatureVisual]) -> List[PadreDetectado]:
        padroes = []
        self.historico_features.extend(features)
        acessos_negados = [f for f in features if f.tipo == "acesso_negado"]
        if acessos_negados:
            padroes.append(PadreDetectado(
                tipo_anomalia=TipoAnomalia.ATAQUE_BRUTE_FORCE,
                nivel_ameaca=NivelAmeaca.CRITICA,
                confianca=min(0.92, 0.5 + len(acessos_negados) * 0.1),
                features_relacionadas=acessos_negados,
                descricao=f"{len(acessos_negados)} tentativas de acesso negado detectadas",
                recomendacao_acao="Bloquear IP origem, ativar Lockdown, notificar admin",
            ))
        cpu_alto = [f for f in features if f.tipo == "cpu_alto"]
        mem_alta = [f for f in features if f.tipo == "memoria_alta"]
        if cpu_alto:
            padroes.append(PadreDetectado(
                tipo_anomalia=TipoAnomalia.DEGRADACAO_PERFORMANCE,
                nivel_ameaca=NivelAmeaca.ALERTA,
                confianca=0.88,
                features_relacionadas=cpu_alto + mem_alta,
                descricao="CPU elevada detectada" if not mem_alta else "CPU e memoria elevadas simultaneamente",
                recomendacao_acao="Investigar processos" if not mem_alta else "Investigar processos, considerar escalacao",
            ))
        disco_cheio = [f for f in features if f.tipo == "disco_cheio"]
        if disco_cheio:
            padroes.append(PadreDetectado(
                tipo_anomalia=TipoAnomalia.FALHA_HARDWARE,
                nivel_ameaca=NivelAmeaca.ALERTA,
                confianca=0.95,
                features_relacionadas=disco_cheio,
                descricao="Espaco em disco critico",
                recomendacao_acao="Liberar espaco, arquivar logs antigos",
            ))
        return padroes

    def calcular_nivel_ameaca_geral(self, padroes: List[PadreDetectado]) -> Tuple[NivelAmeaca, float]:
        if not padroes:
            return NivelAmeaca.NORMAL, 0.0
        p_max = max(padroes, key=lambda p: p.confianca)
        return p_max.nivel_ameaca, p_max.confianca


class ModuloPercepcaoVisual:
    def __init__(self, rag_context: Optional[Dict[str, Any]] = None):
        self.rag_context = rag_context or {}
        self.extrator = ExtratorDeFeaturesVisuais()
        self.analisador = AnalisadorDePadroes(rag_context)
        self.historico_snapshots = deque(maxlen=100)
        self.callbacks_ameaca = []

    def registrar_callback_ameaca(self, callback: Callable[[PadreDetectado], None]):
        self.callbacks_ameaca.append(callback)

    def processar_entrada_visual(self, entrada: str, tipo: TipoEntradaVisual) -> SnapshotVisual:
        features = self.extrator.extrair(entrada, tipo)
        padroes = self.analisador.analisar_features(features)
        nivel_ameaca, confianca = self.analisador.calcular_nivel_ameaca_geral(padroes)
        snapshot = SnapshotVisual(
            entrada_tipo=tipo,
            features_extraidas=features,
            padroes_detectados=padroes,
            nivel_ameaca_geral=nivel_ameaca,
            confianca_geral=confianca,
        )
        self.historico_snapshots.append(snapshot)
        if nivel_ameaca != NivelAmeaca.NORMAL:
            for padrao in padroes:
                for callback in self.callbacks_ameaca:
                    try:
                        callback(padrao)
                    except Exception as e:
                        logger.error(f"Erro no callback de ameaca: {e}")
        return snapshot

    def obter_historico_ameacas(self, ultimos_n: int = 50) -> List[Dict[str, Any]]:
        ameacas = []
        for snapshot in list(self.historico_snapshots):
            if snapshot.nivel_ameaca_geral != NivelAmeaca.NORMAL:
                for padrao in snapshot.padroes_detectados:
                    ameacas.append({
                        "tipo": padrao.tipo_anomalia.value,
                        "nivel": padrao.nivel_ameaca.value,
                        "confianca": padrao.confianca,
                        "descricao": padrao.descricao,
                        "recomendacao": padrao.recomendacao_acao,
                        "timestamp": padrao.timestamp,
                    })
        return ameacas[-ultimos_n:]

    def obter_status_visual(self) -> Dict[str, Any]:
        snapshots = list(self.historico_snapshots)
        if not snapshots:
            return {"status": "sem_dados", "ameacas_detectadas": 0, "nivel_maximo": "normal"}
        recente = snapshots[-1]
        criticas = sum(1 for p in recente.padroes_detectados if p.nivel_ameaca == NivelAmeaca.CRITICA)
        return {
            "status": "operacional",
            "ameacas_detectadas": len(recente.padroes_detectados),
            "nivel_maximo": recente.nivel_ameaca_geral.value,
            "confianca": recente.confianca_geral,
            "criticas": criticas,
            "timestamp": recente.timestamp,
        }


_modulo_visao_global = None


def inicializar_visao(rag_context: Optional[Dict[str, Any]] = None) -> ModuloPercepcaoVisual:
    global _modulo_visao_global
    if _modulo_visao_global is None:
        _modulo_visao_global = ModuloPercepcaoVisual(rag_context)
    return _modulo_visao_global


def obter_visao() -> ModuloPercepcaoVisual:
    global _modulo_visao_global
    if _modulo_visao_global is None:
        _modulo_visao_global = ModuloPercepcaoVisual()
    return _modulo_visao_global


class VisionPipeline:
    def __init__(self):
        self.modulo = ModuloPercepcaoVisual()

    def process_log(self, log_text: str) -> Dict[str, Any]:
        snapshot = self.modulo.processar_entrada_visual(log_text, TipoEntradaVisual.LOG_TEXTO)
        return {
            "features": len(snapshot.features_extraidas),
            "padroes": len(snapshot.padroes_detectados),
            "nivel_ameaca": snapshot.nivel_ameaca_geral.value,
            "confianca": snapshot.confianca_geral,
            "status": self.modulo.obter_status_visual(),
        }

    def process_metrics(self, metrics_json: str) -> Dict[str, Any]:
        snapshot = self.modulo.processar_entrada_visual(metrics_json, TipoEntradaVisual.METRICAS_TEMPO_REAL)
        return {
            "features": len(snapshot.features_extraidas),
            "padroes": len(snapshot.padroes_detectados),
            "nivel_ameaca": snapshot.nivel_ameaca_geral.value,
            "confianca": snapshot.confianca_geral,
        }

    def get_status(self) -> Dict[str, Any]:
        return self.modulo.obter_status_visual()

    def get_threats(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.modulo.obter_historico_ameacas(limit)
