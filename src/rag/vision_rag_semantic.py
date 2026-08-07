"""
VISION_RAG_SEMANTIC — Ponto de Fusão entre Visão e Conhecimento (Prioridade 4)
=============================================================================
Este módulo é o "Ponto de Fusão" da Ravena AI, onde a percepção visual bruta
é convertida em conceitos semânticos e validada contra a base de conhecimento RAG.

Responsabilidades:
  - Decodificar anomalias visuais em termos técnicos.
  - Consultar o RAG para obter contexto e fundamentos sobre o que foi "visto".
  - Gerar decisões autônomas fundamentadas em expertise técnica.
  - Alimentar o Omega com ações de alta confiança.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Importações dos módulos base
try:
    from vision_module import SnapshotVisual, PatrãoDetectado, TipoAnomalia, NivelAmeaca
    from rag_advanced import IndexadorRAG, ResultadoBusca, ContextoEnriquecido
except ImportError:
    # Fallbacks para tipos básicos se os módulos não puderem ser importados diretamente
    class TipoAnomalia:
        ATAQUE_BRUTE_FORCE = "ataque_brute_force"
        DEGRADAÇÃO_PERFORMANCE = "degradação_performance"
    class NivelAmeaca:
        CRITICA = "critica"
        ALERTA = "alerta"

@dataclass
class DecisaoAutonoma:
    """Decisão tomada pela fusão Visão + RAG."""
    acao: str
    fundamento: str
    confianca: float
    anomalia_origem: str
    documentos_referencia: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class VisionRAGSemantic:
    """
    O "Ponto de Fusão" entre o que a Ravena vê e o que ela sabe.
    """
    def __init__(self, indexador_rag: Optional[Any] = None):
        self.rag = indexador_rag
        self.logger = self._configurar_logger()
        self.historico_decisoes = []

    def _configurar_logger(self):
        logger = logging.getLogger("VISION_RAG_SEMANTIC")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [VISION_RAG] [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def decodificar_percepcao(self, snapshot: Any) -> List[DecisaoAutonoma]:
        """
        Decodifica um snapshot visual usando o conhecimento do RAG.
        """
        self.logger.info(f"Iniciando decodificação de snapshot visual ({len(snapshot.padroes_detectados)} padrões)")
        decisoes = []

        for padrao in snapshot.padroes_detectados:
            # 1. Converter anomalia em query para o RAG
            query = self._gerar_query_do_padrao(padrao)
            
            # 2. Consultar RAG para contexto técnico
            contexto_tecnico = "Contexto padrão: Escalar recursos ou investigar processo."
            referencias = []
            
            if self.rag:
                resultados = self.rag.buscar(query, top_k=2)
                if resultados:
                    # Extrair o melhor fundamento do RAG
                    melhor_resultado = resultados[0]
                    contexto_tecnico = melhor_resultado.chunk.conteudo if hasattr(melhor_resultado, 'chunk') else str(melhor_resultado)
                    referencias = [r.documento.titulo for r in resultados if hasattr(r, 'documento')]

            # 3. Formular Decisão Autônoma
            decisao = DecisaoAutonoma(
                acao=self._mapear_acao_por_anomalia(padrao.tipo_anomalia),
                fundamento=contexto_tecnico,
                confianca=padrao.confianca,
                anomalia_origem=str(padrao.tipo_anomalia),
                documentos_referencia=referencias
            )
            decisoes.append(decisao)
            self.logger.info(f"Decisão formulada: {decisao.acao} (Confiança: {decisao.confianca:.2f})")

        self.historico_decisoes.extend(decisoes)
        return decisoes

    def _gerar_query_do_padrao(self, padrao: Any) -> str:
        """Gera uma query técnica baseada na anomalia detectada."""
        return f"Como mitigar {padrao.tipo_anomalia} e quais as melhores práticas de segurança para {padrao.descricao}"

    def _mapear_acao_por_anomalia(self, tipo_anomalia: Any) -> str:
        """Mapeia o tipo de anomalia para uma ação executável pelo Omega."""
        mapeamento = {
            "TipoAnomalia.ATAQUE_BRUTE_FORCE": "BLOQUEIO_IMEDIATO_IP",
            "TipoAnomalia.DEGRADAÇÃO_PERFORMANCE": "ESCALONAMENTO_RECURSOS",
            "TipoAnomalia.FALHA_HARDWARE": "NOTIFICAR_SRE_HARDWARE",
            "TipoAnomalia.EXFILTRAÇÃO_DADOS": "ATIVAR_LOCKDOWN_TOTAL",
            "ataque_brute_force": "BLOQUEIO_IMEDIATO_IP",
            "degradação_performance": "ESCALONAMENTO_RECURSOS"
        }
        # Fallback para string se for Enum
        tipo_str = str(tipo_anomalia)
        return mapeamento.get(tipo_str, "INVESTIGAR_ANOMALIA")

if __name__ == "__main__":
    # Teste rápido de integração
    print("--- TESTE DE INTEGRAÇÃO VISION_RAG_SEMANTIC ---")
    
    # Mock de Snapshot e Padrão
    class MockPadrao:
        def __init__(self, tipo, desc, conf):
            self.tipo_anomalia = tipo
            self.descricao = desc
            self.confianca = conf
    
    class MockSnapshot:
        def __init__(self, padroes):
            self.padroes_detectados = padroes

    snapshot_teste = MockSnapshot([
        MockPadrao("ataque_brute_force", "Múltiplas falhas de login do IP 192.168.1.100", 0.95),
        MockPadrao("degradação_performance", "CPU em 98% por 5 minutos", 0.88)
    ])

    fusao = VisionRAGSemantic()
    decisoes = fusao.decodificar_percepcao(snapshot_teste)
    
    for d in decisoes:
        print(f"\n[DECISÃO] Ação: {d.acao}")
        print(f"[FUNDAMENTO] {d.fundamento[:100]}...")
        print(f"[CONFIANÇA] {d.confianca:.2%}")
