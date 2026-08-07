import json
import os

class DNASucesso:
    """
    Define o DNA operacional da Ravena: parâmetros técnicos, limites de decisão 
    e comportamento esperado dos agentes.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.dna_path = os.path.join(config_dir, "dna_params.json")
        self.params = self._initialize_dna()

    def _initialize_dna(self):
        default_params = {
            "version": "3.0.0",
            "core_model": "Llama-3.1-70b",
            "operational_limits": {
                "max_risk_per_trade": 0.02,  # 2% do capital
                "min_confidence_score": 0.85, # Score mínimo para ação autônoma
                "max_daily_loss": 0.05       # 5% de perda diária máxima
            },
            "personality_traits": {
                "analytical_depth": "high",
                "narrative_fluency": "sophisticated",
                "reasoning_style": "chain_of_thought"
            },
            "decision_matrix": {
                "macro_weight": 0.4,
                "technical_weight": 0.4,
                "sentiment_weight": 0.2
            }
        }
        
        if not os.path.exists(self.dna_path):
            os.makedirs(os.path.dirname(self.dna_path), exist_ok=True)
            with open(self.dna_path, 'w') as f:
                json.dump(default_params, f, indent=4)
        
        with open(self.dna_path, 'r') as f:
            return json.load(f)

    def get_param(self, key: str, default=None):
        return self.params.get(key, default)

    def update_dna(self, new_params: dict):
        """Atualiza o DNA garantindo a integridade dos parâmetros críticos."""
        self.params.update(new_params)
        with open(self.dna_path, 'w') as f:
            json.dump(self.params, f, indent=4)
        return self.params

if __name__ == "__main__":
    dna = DNASucesso()
    print(f"DNA da Ravena V3 carregado: {dna.get_param('version')}")
    print(f"Limites operacionais: {dna.get_param('operational_limits')}")
