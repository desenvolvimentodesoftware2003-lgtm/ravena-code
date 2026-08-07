"""
RAVENA AI v3.2.6 — src/utils/external_api_manager.py
=====================================================
Módulo de Gerenciamento de APIs Externas.
Unifica a lógica de conectores (Instagram, Telegram, etc.) e facilita a adição de novas integrações.
"""

import logging
import json
from typing import Dict, Any, List, Optional

# Configuração de Logging
logger = logging.getLogger("ravena.utils.api_manager")

class ExternalAPIManager:
    """Gerenciador Unificado de Conectores Externos."""
    
    def __init__(self):
        self.version = "3.2.6"
        self.conectores = {}
        logger.info(f"ExternalAPIManager v{self.version} inicializado.")

    def registrar_conector(self, nome: str, conector_instancia: Any):
        """Registra um novo conector (ex: Instagram, Telegram, CRM)."""
        self.conectores[nome] = conector_instancia
        logger.info(f"Conector '{nome}' registrado com sucesso.")

    def executar_acao(self, conector_nome: str, acao: str, **kwargs) -> Dict[str, Any]:
        """
        Executa uma ação em um conector específico.
        Ex: executar_acao('instagram', 'publicar_post', imagem='...', legenda='...')
        """
        if conector_nome not in self.conectores:
            logger.error(f"Conector '{conector_nome}' não encontrado.")
            return {"status": "error", "message": f"Conector '{conector_nome}' não registrado."}
        
        conector = self.conectores[conector_nome]
        if not hasattr(conector, acao):
            logger.error(f"Ação '{acao}' não suportada pelo conector '{conector_nome}'.")
            return {"status": "error", "message": f"Ação '{acao}' não suportada."}
        
        logger.info(f"Executando '{acao}' no conector '{conector_nome}'...")
        try:
            metodo = getattr(conector, acao)
            resultado = metodo(**kwargs)
            return {"status": "success", "data": resultado}
        except Exception as e:
            logger.exception(f"Erro ao executar '{acao}' no conector '{conector_nome}': {str(e)}")
            return {"status": "error", "message": str(e)}

    def listar_conectores_ativos(self) -> List[str]:
        """Retorna a lista de conectores registrados."""
        return list(self.conectores.keys())

# Exemplo de uso (Simulado)
if __name__ == "__main__":
    # Mock de um conector
    class MockInstagram:
        def publicar_post(self, imagem, legenda):
            return f"Post publicado no Instagram: {legenda}"

    manager = ExternalAPIManager()
    manager.registrar_conector("instagram", MockInstagram())
    print(manager.executar_acao("instagram", "publicar_post", imagem="foto.jpg", legenda="Bora pra cima! 🚀"))
