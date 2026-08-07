"""
RAVENA AIM v3.2.6 — src/core/omega_orchestrator_v3.2.6.py
==========================================================
Orquestrador Omega — Ponto de Convergência e Roteamento.
Orquestra RAG, Segurança, Visão e Aprendizado.
Firewall inteligente: valida, roteia, bloqueia, audita.
"""

import os
import time
import logging
import json
import importlib.util
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

def _import_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# RAG Advanced (nome sem ponto, import normal)
try:
    from src.rag.rag_advanced import IndexadorRAG as RAGCore, Documento
except ImportError:
    RAGCore = None
    Documento = None

# Vision RAG Semantic (arquivo com underscore)
try:
    _vrs = _import_from_file("vrs_mod", os.path.join(_project_root, "src/rag/vision_rag_semantic_v3.2.6.py"))
    VisionRAGSemantic = _vrs.VisionRAGSemantic
    PadraoDetectado = _vrs.PadraoDetectado
    DecisaoAutonoma = _vrs.DecisaoAutonoma
except Exception:
    try:
        _vrs = _import_from_file("vrs_mod2", os.path.join(_project_root, "src/rag/vision_rag_semantic.py"))
        VisionRAGSemantic = _vrs.VisionRAGSemantic
        PadraoDetectado = None
        DecisaoAutonoma = _vrs.DecisaoAutonoma
    except Exception:
        VisionRAGSemantic = None
        PadraoDetectado = None
        DecisaoAutonoma = None

# Security Core v3.2.6 (arquivo com ponto)
try:
    _sc = _import_from_file("sec_core_mod", os.path.join(_project_root, "src/security/security_core_v3.2.6.py"))
    SecurityLayer = _sc.SecurityLayer
    LockdownV22 = _sc.LockdownV22
    AuditorCore = _sc.AuditorCore
except Exception:
    SecurityLayer = None
    LockdownV22 = None
    AuditorCore = None

# Utils Core v3.2.6 (arquivo com ponto)
try:
    _uc = _import_from_file("utils_core_mod", os.path.join(_project_root, "src/utils/utils_core_v3.2.6.py"))
    UtilsCore = _uc.UtilsCore
except Exception:
    UtilsCore = None

# Professor (sistema de ensino e avaliacao)
try:
    _pr = _import_from_file("professor_mod", os.path.join(_project_root, "src/core/professor.py"))
    Professor = _pr.Professor
except Exception:
    Professor = None

if not all([VisionRAGSemantic, SecurityLayer, UtilsCore]):
    logging.getLogger("ravena.omega_orchestrator").warning(
        "OmegaOrchestrator em modo degradado — alguns módulos não puderam ser carregados."
    )

# Configuração de Logging
logger = logging.getLogger("ravena.omega_orchestrator")

@dataclass
class StatusSistema:
    versao: str = "3.2.6-RAVENA-MODULAR"
    status_global: str = "INICIALIZANDO"
    soberania_ativa: bool = False
    modulos_carregados: List[str] = field(default_factory=list)
    alertas_ativos: int = 0
    uptime_inicio: float = field(default_factory=time.time)
    ciclos_autocorrecao: int = 0

class OmegaOrchestrator:
    """Orquestrador Omega da Ravena AIM v3.2.6. Firewall inteligente: valida, roteia, audita."""
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(OmegaOrchestrator, cls).__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self):
        if self._inicializado:
            return
            
        self.status = StatusSistema()
        
        # Inicializar sub-módulos refatorados (com fallback gracioso)
        self.rag = RAGCore() if RAGCore else None
        self.security = SecurityLayer() if SecurityLayer else None
        self.lockdown = LockdownV22() if LockdownV22 else None
        self.auditor = AuditorCore() if AuditorCore else None
        self.utils = UtilsCore() if UtilsCore else None
        
        # Inicializar Fusão Cognitiva (Visão + RAG)
        if VisionRAGSemantic and self.rag:
            self.fusao_cognitiva = VisionRAGSemantic(self.rag)
        else:
            self.fusao_cognitiva = None
        
        # Professor (ensino e avaliacao transversal)
        self.professor = Professor() if Professor else None

        # Componentes adicionais
        self.memoria_episodica = []
        
        self._inicializar_sistema()
        self._inicializado = True

    def _inicializar_sistema(self):
        logger.info("Iniciando OMEGA Orchestrator v3.2.6 - Modo Modular Ativo")
        
        # 1. Validar Soberania (Configuração de Ambiente)
        self.status.soberania_ativa = os.getenv("RAVENA_SOBERANIA", "false").lower() == "true"
        if self.status.soberania_ativa:
            logger.info("MODO SOBERANO ATIVO: Blindagem e processamento local prioritário.")
        
        # 2. Carregar Módulos e Registrar Status
        modulos_disponiveis = []
        if self.rag: modulos_disponiveis.append("rag_core")
        if self.security: modulos_disponiveis.append("security_core")
        if self.lockdown: modulos_disponiveis.append("lockdown_v2.2")
        if self.auditor: modulos_disponiveis.append("auditor_core")
        if self.fusao_cognitiva: modulos_disponiveis.append("vision_rag_semantic")
        if self.professor: modulos_disponiveis.append("professor")
        
        self.status.modulos_carregados = modulos_disponiveis
        self.status.status_global = "OPERACIONAL" if modulos_disponiveis else "DEGRADADO"
        logger.info(f"Sistema {self.status.status_global} com {len(modulos_disponiveis)} módulos integrados.")

    def processar_percepcao_visual(self, snapshot: Any):
        """Processa um snapshot visual, decodifica via RAG e orquestra ações autônomas."""
        if not self.fusao_cognitiva:
            logger.warning("Fusão Cognitiva não disponível — módulo VisionRAG não carregado.")
            return []
            
        logger.info("Iniciando processamento de percepção visual autônoma (Fusão Cognitiva)...")
        
        # 1. Decodificar percepção visual em decisões fundamentadas
        decisoes = self.fusao_cognitiva.decodificar_percepcao(snapshot)
        
        if not decisoes:
            logger.info("Nenhuma anomalia crítica detectada pela visão.")
            return []
        
        # 2. Orquestrar ações baseadas nas decisões
        for decisao in decisoes:
            logger.info(f"ORQUESTRAÇÃO AUTÔNOMA: Executando ação {decisao.acao} (Confiança: {decisao.confianca:.2f})")
            self._executar_acao_autonoma(decisao)
            
        return decisoes

    def _executar_acao_autonoma(self, decisao):
        """Executa uma ação autônoma com validação de segurança e auditoria."""
        # Registrar ação no log de auditoria
        if self.auditor:
            self.auditor.registrar_acao(
                f"Ação Autônoma: {decisao.acao} | Fundamento: {decisao.fundamento[:50]}...", 
                "SUCESSO", 
                "OMEGA_AUTONOMO"
            )
        
        # Simulação de execução de ação (pode ser expandida com ToolManager)
        if "BLOQUEIO" in decisao.acao:
            logger.warning(f"EXECUTANDO BLOQUEIO DE SEGURANÇA: {decisao.anomalia_origem}")
        elif "ESCALONAMENTO" in decisao.acao:
            logger.info(f"EXECUTANDO ESCALONAMENTO DE RECURSOS: {decisao.anomalia_origem}")
            
        self.status.ciclos_autocorrecao += 1

    def executar_missao(self, comando: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executa uma tarefa orquestrando RAG e Segurança."""
        contexto = contexto or {"usuario": "admin"}
        usuario = contexto.get("usuario", "admin")
        
        # 1. Validação de Segurança (Zero Trust)
        if self.security:
            contexto["conteudo"] = comando
            seguro, erros = self.security.validar_operacao(contexto)
            
            if not seguro:
                logger.warning(f"BLOQUEIO DE SEGURANÇA: {erros}")
                if self.auditor:
                    self.auditor.registrar_acao(f"Comando bloqueado: {comando}", f"Erros: {erros}", usuario)
                return {"sucesso": False, "erro": "SECURITY_BLOCK", "detalhes": erros}
        
        # 2. Consulta RAG para Contexto
        contexto_rag = []
        if self.rag:
            logger.info(f"Consultando base de conhecimento RAG para: {comando}")
            start_rag = time.time()
            contexto_rag = self.rag.buscar_contexto(comando)
            if self.utils and hasattr(self.utils, 'metrics'):
                self.utils.metrics.registrar_latencia_rag(time.time() - start_rag)
        
        # 3. Processamento Cognitivo (Simulado)
        logger.info("Processando comando com contexto enriquecido...")
        resposta_bruta = f"Processado com base em {len(contexto_rag)} documentos."
        
        # 4. Filtro de Saída (Lockdown V2.2)
        resposta_final = self.lockdown.filtrar_saida(resposta_bruta) if self.lockdown else resposta_bruta
        
        # 5. Auditoria Final
        if self.auditor:
            self.auditor.registrar_acao(f"Missão executada: {comando}", "SUCESSO", usuario)
        
        return {
            "sucesso": True,
            "resposta": resposta_final,
            "contexto_usado": [c['id'] for c in contexto_rag] if contexto_rag else [],
            "timestamp": datetime.now().isoformat()
        }

    def obter_diagnostico(self) -> Dict[str, Any]:
        uptime = time.time() - self.status.uptime_inicio
        return {
            "versao": self.status.versao,
            "status": self.status.status_global,
            "soberania": self.status.soberania_ativa,
            "modulos": self.status.modulos_carregados,
            "uptime": round(uptime, 2),
            "alertas": self.status.alertas_ativos
        }

# Singleton helper
def obter_orquestrador() -> OmegaOrchestrator:
    return OmegaOrchestrator()
