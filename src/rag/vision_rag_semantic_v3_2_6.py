"""
RAVENA AIM v3.2.6 — vision_rag_semantic_v3_2_6.py
=================================================
Fusão Cognitiva: Integração de Visão Computacional e RAG.
Permite decisões inteligentes baseadas em percepção visual e contexto técnico.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configuração de Logging
logger = logging.getLogger("ravena.vision_rag_semantic")

@dataclass
class PadraoDetectado:
    tipo: str
    descricao: str
    confianca: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DecisaoAutonoma:
    acao: str
    fundamento: str
    confianca: float
    anomalia_origem: str
    contexto_rag_usado: List[str] = field(default_factory=list)

class VisionRAGSemantic:
    """Orquestra a fusão entre percepção visual e conhecimento RAG."""
    def __init__(self, rag_core: Any):
        self.rag = rag_core
        self.historico_decisoes = []

    def decodificar_percepcao(self, snapshot: Any) -> List[DecisaoAutonoma]:
        """
        Analisa padrões visuais, consulta o RAG para fundamentação técnica
        e propõe ações autônomas.
        """
        decisoes = []
        padroes = getattr(snapshot, 'padroes_detectados', [])
        
        for padrao in padroes:
            logger.info(f"Analisando padrão visual: {padrao.tipo} (Confiança: {padrao.confianca:.2f})")
            
            # 1. Consultar RAG para fundamentação técnica baseada no tipo de anomalia
            query_rag = f"Protocolo de segurança para {padrao.tipo} e {padrao.descricao}"
            contexto = self.rag.buscar_contexto(query_rag, top_k=2)
            
            # 2. Fundamentar a decisão com base no conhecimento técnico recuperado
            fundamento = "Decisão baseada em padrões visuais detectados."
            if contexto:
                fundamento += " Reforçado por protocolos técnicos: " + " | ".join([c['conteudo'][:100] for c in contexto])
            
            # 3. Determinar ação com base na gravidade e confiança
            acao = self._determinar_acao(padrao, contexto)
            
            decisao = DecisaoAutonoma(
                acao=acao,
                fundamento=fundamento,
                confianca=(padrao.confianca + 0.95) / 2, # Média entre visão e protocolo
                anomalia_origem=padrao.tipo,
                contexto_rag_usado=[c['id'] for c in contexto]
            )
            decisoes.append(decisao)
            self.historico_decisoes.append(decisao)
            
        return decisoes

    def _determinar_acao(self, padrao: PadraoDetectado, contexto: List[Dict[str, Any]]) -> str:
        """Lógica de decisão baseada em regras e contexto."""
        if padrao.confianca > 0.9:
            if "ataque" in padrao.tipo or "vulnerabilidade" in padrao.tipo:
                return "BLOQUEIO_IMEDIATO_E_ISOLAMENTO"
            if "hardware" in padrao.tipo or "falha" in padrao.tipo:
                return "ESCALONAMENTO_RECURSOS_E_ALERTA"
        
        return "MONITORAMENTO_INTENSIVO"
