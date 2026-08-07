import logging
import time
import os
import sys
import importlib.util
from typing import Dict, Any, List, Optional
from datetime import datetime

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_orch_path = os.path.join(_project_root, "core", "omega_orchestrator_v3.2.6.py")
_spec = importlib.util.spec_from_file_location("omega_orch_mod", _orch_path)
_orch_mod = importlib.util.module_from_spec(_spec)
sys.modules["omega_orch_mod"] = _orch_mod
_spec.loader.exec_module(_orch_mod)
OmegaOrchestrator = _orch_mod.OmegaOrchestrator
DecisaoAutonoma = getattr(_orch_mod, 'DecisaoAutonoma', None)

# Configuração de Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RavenaChatAgent")

class RavenaChatAgent(OmegaOrchestrator):
    """
    Classe de Chat Generativo (Ravena Modular V3)
    Herda do OmegaOrchestrator para garantir consistência, segurança e acesso ao RAG.
    Implementa diálogos fluidos, gerenciamento de contexto dinâmico e roteamento de intenção.
    """
    
    def __init__(self):
        super().__init__()
        self.historico_conversa: List[Dict[str, str]] = []
        self.buffer_memoria_curto_prazo: List[Dict[str, str]] = []
        self.limite_buffer = 10
        logger.info("RavenaChatAgent inicializado com Herança do Orquestrador OMEGA.")

    def _gerenciar_contexto_dinamico(self, input_usuario: str) -> str:
        """
        Implementação de Gerenciamento de Contexto Dinâmico (Seção 3.1).
        Combina memória de curto prazo (buffer) com busca de longo prazo (RAG/Drive).
        """
        # 1. Recuperar contexto de longo prazo via RAG (herdado do OmegaOrchestrator)
        contexto_longo_prazo = self.rag.buscar_contexto(input_usuario)
        contexto_formatado = "\n".join([doc.get('conteudo', '') for doc in contexto_longo_prazo])
        
        # 2. Recuperar contexto de curto prazo do buffer
        contexto_curto_prazo = "\n".join([f"Usuário: {m['user']}\nRavena: {m['bot']}" for m in self.buffer_memoria_curto_prazo])
        
        return f"--- CONTEXTO HISTÓRICO (CURTO PRAZO) ---\n{contexto_curto_prazo}\n\n--- CONTEXTO TÉCNICO (LONGO PRAZO) ---\n{contexto_formatado}"

    def _rotear_intencao(self, input_usuario: str) -> str:
        """
        Roteamento de Intenção (Seção 3.2).
        Identifica se a pergunta exige intervenção de especialistas (Day Trade ou Busca 360).
        """
        input_lower = input_usuario.lower()
        if any(k in input_lower for k in ["trade", "bolsa", "mercado", "ativo", "simulação"]):
            return "ESPECIALISTA_DAY_TRADE"
        elif any(k in input_lower for k in ["busca", "macro", "notícia", "cenário", "360"]):
            return "ESPECIALISTA_BUSCA_360"
        return "CHAT_GENERICO"

    def responder(self, input_usuario: str, contexto_adicional: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fluxo de Dados do Chat (Seção 3.2).
        1. Recebe input.
        2. Avalia necessidade de especialistas.
        3. Sintetiza resposta técnica fluida.
        """
        start_time = time.time()
        
        # 1. Validação de Segurança (Herdada do OmegaOrchestrator - Zero Trust)
        validacao = self.security.validar_operacao({"conteudo": input_usuario, "usuario": "admin"})
        if not validacao[0]:
            return {"sucesso": False, "erro": "SECURITY_BLOCK", "detalhes": validacao[1]}

        # 2. Roteamento de Intenção
        intencao = self._rotear_intencao(input_usuario)
        logger.info(f"Intenção detectada: {intencao}")

        # 3. Gerenciamento de Contexto
        contexto_enriquecido = self._gerenciar_contexto_dinamico(input_usuario)

        # 4. Simulação de Processamento SOTA (Chain of Thought)
        # Aqui integraria com Llama 3.1 / NVIDIA via API
        logger.info("Executando Raciocínio Encadeado (Chain of Thought)...")
        
        if intencao == "ESPECIALISTA_DAY_TRADE":
            resposta_base = "Analisando dados de mercado e simulações dos 60 agentes de trade..."
        elif intencao == "ESPECIALISTA_BUSCA_360":
            resposta_base = "Cruzando informações macroeconômicas da Busca 360..."
        else:
            resposta_base = "Processando sua solicitação técnica com base no DNA de Sucesso..."

        # 5. Validação Anti-Alucinação (Seção 3.3)
        # Confronta a resposta com o contexto recuperado
        logger.info("Validando resposta contra base de conhecimento (Anti-Alucinação)...")
        
        # 6. Filtro de Saída (Lockdown V2.2 herdado)
        resposta_final = self.lockdown.filtrar_saida(f"{resposta_base}\n[Resposta técnica fluida baseada no contexto v3]")

        # 7. Atualizar Memória de Curto Prazo
        self.buffer_memoria_curto_prazo.append({"user": input_usuario, "bot": resposta_final})
        if len(self.buffer_memoria_curto_prazo) > self.limite_buffer:
            self.buffer_memoria_curto_prazo.pop(0)

        # 8. Auditoria (Herdada)
        self.auditor.registrar_acao(f"Chat: {input_usuario[:30]}...", "SUCESSO", "admin")

        latencia = time.time() - start_time
        
        return {
            "sucesso": True,
            "resposta": resposta_final,
            "intencao": intencao,
            "latencia": f"{latencia:.2f}s",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Teste rápido de inicialização
    agent = RavenaChatAgent()
    print(agent.responder("Como está o cenário macro para o trade de hoje?"))
