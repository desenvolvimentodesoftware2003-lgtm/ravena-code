import logging
import re
from typing import Dict, Any, List

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramBotRefinement")

class TelegramBotRefinement:
    """
    Ajusta as métricas de observabilidade no bot para identificação proativa 
    de alucinações ou desvios lógicos nas respostas dos agentes.
    """
    
    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        self.hallucination_patterns = [
            r"\[REDACTED\]", r"\[ERROR\]", r"NaN", r"undefined",
            r"como um modelo de linguagem IA", r"não tenho acesso a dados em tempo real"
        ]
        self.interaction_history: List[Dict[str, Any]] = []

    def evaluate_response(self, agent_response: str, context_data: str) -> Dict[str, Any]:
        """Avalia a resposta do agente contra o contexto e padrões de alucinação."""
        logger.info("Avaliando resposta do agente para o Telegram.")
        
        # 1. Verificação de padrões de alucinação
        hallucination_score = self._check_hallucination_patterns(agent_response)
        
        # 2. Verificação de consistência com o contexto (Mock)
        consistency_score = self._check_context_consistency(agent_response, context_data)
        
        # 3. Cálculo do score final de confiança
        final_score = (hallucination_score + consistency_score) / 2
        
        is_reliable = final_score >= self.confidence_threshold
        
        evaluation = {
            "is_reliable": is_reliable,
            "confidence_score": final_score,
            "hallucination_risk": 1.0 - hallucination_score,
            "action": "send_to_user" if is_reliable else "flag_for_review"
        }
        
        if not is_reliable:
            logger.warning(f"Resposta com baixa confiança detectada: {final_score}")
        
        return evaluation

    def _check_hallucination_patterns(self, response: str) -> float:
        """Retorna um score de 0.0 a 1.0 baseado na ausência de padrões de erro."""
        matches = 0
        for pattern in self.hallucination_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                matches += 1
        
        score = 1.0 - (matches / len(self.hallucination_patterns))
        return max(0.0, score)

    def _check_context_consistency(self, response: str, context: str) -> float:
        """Verifica se termos-chave do contexto estão presentes na resposta."""
        if not context: return 1.0
        
        context_terms = set(re.findall(r'\w+', context.lower()))
        response_terms = set(re.findall(r'\w+', response.lower()))
        
        if not context_terms: return 1.0
        
        intersection = context_terms.intersection(response_terms)
        score = len(intersection) / len(context_terms) if context_terms else 1.0
        
        return min(1.0, score * 2.0) # Multiplicador para dar peso à presença de termos

    def log_interaction(self, user_id: str, input_text: str, output_text: str, eval_data: dict):
        """Registra a interação para auditoria futura."""
        entry = {
            "user_id": user_id,
            "input": input_text,
            "output": output_text,
            "evaluation": eval_data
        }
        self.interaction_history.append(entry)
        logger.info(f"Interação registrada para o usuário {user_id}.")

if __name__ == "__main__":
    bot = TelegramBotRefinement()
    resp = "O mercado de cripto está em alta hoje com o Bitcoin a 70k."
    ctx = "Bitcoin 70k mercado alta"
    print(f"Avaliação de Resposta: {bot.evaluate_response(resp, ctx)}")
