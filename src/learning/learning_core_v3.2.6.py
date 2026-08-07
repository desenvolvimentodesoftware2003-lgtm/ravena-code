"""
RAVENA AI 3.0.0 — src/learning/learning_core.py
==============================================
Módulo de Aprendizado e Evolução Contínua Refatorado.
Implementa Pipeline de Retreinamento e Fine-tuning LoRA.
Baseado em: finetune_lora.py e pipeline_retrain.py (Legado).
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

# Configuração de Logging
logger = logging.getLogger("ravena.learning_core")

@dataclass
class ExemploTreinamento:
    prompt: str
    completion: str
    fonte: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

class PipelineRetreinamento:
    """Coleta, consolida e prepara dados para evolução do modelo."""
    def __init__(self, buffer_path: str = "./data/training_buffer.jsonl", threshold: int = 10):
        self.buffer_path = buffer_path
        self.threshold = threshold
        self.buffer = []
        os.makedirs(os.path.dirname(buffer_path), exist_ok=True)

    def adicionar_exemplo(self, prompt: str, completion: str, fonte: str = "feedback_usuario"):
        exemplo = ExemploTreinamento(prompt=prompt, completion=completion, fonte=fonte)
        self.buffer.append(exemplo)
        
        # Persistir no buffer local
        with open(self.buffer_path, "a") as f:
            f.write(json.dumps(exemplo.__dict__) + "\n")
            
        logger.info(f"Exemplo adicionado ao buffer de retreinamento. Buffer: {len(self.buffer)}")
        
        if len(self.buffer) >= self.threshold:
            self.disparar_consolidacao()

    def disparar_consolidacao(self):
        """Consolida o buffer em um dataset para fine-tuning."""
        dataset_file = f"./data/datasets/dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        os.makedirs(os.path.dirname(dataset_file), exist_ok=True)
        
        with open(dataset_file, "w") as f:
            for ex in self.buffer:
                f.write(json.dumps(ex.__dict__) + "\n")
                
        logger.info(f"Dataset consolidado em {dataset_file}. Pronto para Fine-tuning LoRA.")
        self.buffer = [] # Limpar buffer após consolidação

class FineTuningLoRA:
    """Serviço de adaptação de modelos via LoRA (Simulado)."""
    def __init__(self, base_model: str = "Llama-3-8B"):
        self.base_model = base_model
        self.status = "IDLE"

    def treinar_adapter(self, dataset_path: str):
        """Simula o disparo de um treinamento LoRA."""
        if not os.path.exists(dataset_path):
            logger.error(f"Dataset não encontrado: {dataset_path}")
            return False
            
        self.status = "TRAINING"
        logger.info(f"Iniciando Fine-tuning LoRA no modelo {self.base_model} usando {dataset_path}...")
        
        # Simulação de tempo de treinamento
        # Em produção, aqui chamaria o script finetune_lora.py ou usaria a biblioteca PEFT
        self.status = "COMPLETED"
        logger.info("Treinamento LoRA concluído. Novo adapter salvo em ./models/adapters/ravena_v3_latest/")
        return True

class LearningCore:
    """Núcleo de Aprendizado da Ravena AI 3.0.0."""
    def __init__(self):
        self.pipeline = PipelineRetreinamento()
        self.finetune = FineTuningLoRA()

    def aprender_com_interacao(self, prompt: str, completion: str, confianca: float):
        """Aprende automaticamente se a confiança for alta o suficiente."""
        if confianca > 0.9:
            self.pipeline.adicionar_exemplo(prompt, completion, fonte="autonomo_alta_confianca")
            return True
        return False
