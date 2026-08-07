"""
RAVENA AI v3.2.7 — src/security/security_core.py
===============================================
Núcleo de Segurança Estendido: Integração com Especialista Hacker.
Mantém a interface original para o OmegaOrchestrator, mas adiciona inteligência ofensiva.
"""
import logging
from typing import Dict, Any, Tuple
try:
    from src.security.hacker_agent import HackerAgent
except ImportError:
    try:
        from .hacker_agent import HackerAgent
    except ImportError:
        import importlib.util, sys, os
        _dir = os.path.dirname(os.path.abspath(__file__))
        _spec = importlib.util.spec_from_file_location("hacker_agent", os.path.join(_dir, "hacker_agent.py"))
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        HackerAgent = _mod.HackerAgent

# Configuração de Logging
logger = logging.getLogger("ravena.security_core")

class SecurityCore:
    """
    Núcleo de Segurança da Ravena AI.
    Atua como a primeira linha de defesa e agora orquestra o Red Team.
    """
    def __init__(self):
        self.versao = "3.2.7"
        # O Especialista Hacker é instanciado internamente (Extensão Modular)
        self.hacker_elite = HackerAgent()
        logger.info(f"SecurityCore v{self.versao} inicializado com Especialista Hacker integrado.")

    def validar_operacao(self, contexto: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida uma operação contra políticas de segurança (Zero Trust).
        Interface mantida para compatibilidade com o OmegaOrchestrator.
        """
        comando = contexto.get("conteudo", "")
        usuario = contexto.get("usuario", "admin")
        
        logger.info(f"Validando operação para usuário {usuario}: {comando[:50]}...")

        # 1. Verificações Básicas (Legado/Existente)
        if "rm -rf" in comando or "DROP TABLE" in comando:
            return False, "COMANDO_PROIBIDO: Tentativa de destruição de dados detectada."

        # 2. Inteligência Ofensiva (Novo: Especialista Hacker)
        # Se o comando envolver URLs ou análise de código, invocamos o Hacker Elite
        if "http" in comando:
            logger.info("Invocando Especialista Hacker para análise de URL externa...")
            analise = self.hacker_elite.analisar_ameaca(comando, tipo="url")
            if analise["veredito"] == "AMEAÇA_DETECTADA":
                return False, f"HACKER_BLOCK: {', '.join(analise['detalhes'])}"

        # 3. Auditoria de Código (Se o contexto indicar desenvolvimento)
        if contexto.get("tipo") == "dev_code":
            logger.info("Invocando Especialista Hacker para auditoria ofensiva de código...")
            auditoria = self.hacker_elite.auditar_codigo_ofensivo(comando)
            if auditoria["vulnerabilidades_encontradas"] > 0:
                # Aqui poderíamos apenas avisar ou bloquear dependendo da política
                logger.warning(f"Vulnerabilidades detectadas pelo Hacker: {auditoria['lista_vulnerabilidades']}")

        return True, ""

    def executar_analise_profunda(self, alvo: str, tipo: str) -> Dict[str, Any]:
        """
        Método adicional para análises sob demanda do usuário ou do OmegaOrchestrator.
        """
        if tipo == "decodificacao":
            return self.hacker_elite.decodificar_diretorio(alvo)
        return self.hacker_elite.analisar_ameaca(alvo, tipo)

if __name__ == "__main__":
    # Teste de integração
    security = SecurityCore()
    ctx_perigoso = {"conteudo": "Acesse https://scam-trading.com/verify-account", "usuario": "tester"}
    valido, erro = security.validar_operacao(ctx_perigoso)
    print(f"Validação (URL Perigosa): {valido} | Erro: {erro}")
    
    ctx_seguro = {"conteudo": "Listar arquivos do diretório src", "usuario": "tester"}
    valido, erro = security.validar_operacao(ctx_seguro)
    print(f"Validação (Comando Seguro): {valido} | Erro: {erro}")
