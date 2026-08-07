import re
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

class ProtocoloZeroTrust:
    """
    Implementa os princípios do NIST SP 800-207: "Nunca confiar, sempre verificar".
    """
    def __init__(self):
        self.usuarios_confiaveis = ["admin", "dev_agente", "sre_bot"]
        self.permissoes = {
            "admin": ["*"],
            "dev_agente": ["read", "write", "execute_test"],
            "sre_bot": ["read", "audit"]
        }

    def validar_acesso(self, usuario: str, acao: str, recurso: str) -> Tuple[bool, str]:
        # 1. Verificar Identidade
        if usuario not in self.usuarios_confiaveis:
            return False, f"Identidade não confiável: {usuario}"
        
        # 2. Verificar Mínimo Privilégio
        user_perms = self.permissoes.get(usuario, [])
        if "*" in user_perms:
            return True, "Acesso total concedido (Admin)"
        
        if acao not in user_perms:
            return False, f"Usuário {usuario} não tem permissão para a ação: {acao}"
        
        # 3. Verificar Contexto (Simulado)
        # Em um ambiente real, verificaríamos IP, horário, MFA, etc.
        return True, f"Acesso Zero Trust validado para {usuario} em {recurso}"

class SRESecurity:
    """
    Incorpora práticas de segurança do Google SRE Book.
    """
    def __init__(self):
        self.vulnerabilidades_comuns = {
            "eval_exec": [r"eval\(", r"exec\("],
            "api_keys": [r"sk-[a-zA-Z0-9]{48}", r"AIza[0-9A-Za-z-_]{35}"],
            "insecure_os": [r"os\.system\(", r"subprocess\.Popen\(shell=True\)"]
        }

    def escaneamento_estatico(self, conteudo_arquivo: str) -> List[str]:
        problemas = []
        for vuln, padroes in self.vulnerabilidades_comuns.items():
            for padrao in padroes:
                if re.search(padrao, conteudo_arquivo):
                    problemas.append(f"Vulnerabilidade detectada: {vuln} (Padrão: {padrao})")
        return problemas

    def auditoria_configuracao(self, configs: Dict[str, Any]) -> List[str]:
        alertas = []
        if not configs.get("mfa_ativo", False):
            alertas.append("CONFIG_AUDIT: MFA não está ativo para o usuário.")
        if configs.get("porta_ssh", 22) == 22:
            alertas.append("CONFIG_AUDIT: Porta SSH padrão (22) detectada. Recomenda-se alteração.")
        return alertas

class SecurityLayer:
    """
    Fachada unificada para a Camada de Segurança e Blindagem.
    """
    def __init__(self):
        self.zero_trust = ProtocoloZeroTrust()
        self.sre = SRESecurity()
        self.logger = self._configurar_logger()

    def _configurar_logger(self):
        logger = logging.getLogger("SECURITY_LAYER")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [SECURITY] [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def validar_operacao(self, contexto: Dict[str, Any]) -> Tuple[bool, List[str]]:
        usuario = contexto.get("usuario", "desconhecido")
        acao = contexto.get("acao", "read")
        recurso = contexto.get("recurso", "sistema")
        conteudo = contexto.get("conteudo", "")
        configs = contexto.get("configs", {})

        erros = []

        # 1. Validação Zero Trust
        sucesso_zt, msg_zt = self.zero_trust.validar_acesso(usuario, acao, recurso)
        if not sucesso_zt:
            erros.append(msg_zt)
        else:
            self.logger.info(msg_zt)

        # 2. Escaneamento SRE (se houver conteúdo)
        if conteudo:
            problemas_sre = self.sre.escaneamento_estatico(conteudo)
            erros.extend(problemas_sre)

        # 3. Auditoria de Configuração
        if configs:
            alertas_config = self.sre.auditoria_configuracao(configs)
            erros.extend(alertas_config)

        if erros:
            for erro in erros:
                self.logger.error(f"VIOLAÇÃO DE SEGURANÇA: {erro}")
            return False, erros

        return True, ["Operação validada com sucesso pela SecurityLayer"]

if __name__ == "__main__":
    # Teste rápido da camada
    sec = SecurityLayer()
    
    contexto_valido = {
        "usuario": "dev_agente",
        "acao": "write",
        "recurso": "projeto_x",
        "configs": {"mfa_ativo": True, "porta_ssh": 2222}
    }
    
    contexto_invalido = {
        "usuario": "intruso",
        "acao": "delete",
        "recurso": "root",
        "conteudo": "eval(payload)",
        "configs": {"mfa_ativo": False}
    }

    print("\n--- TESTE CONTEXTO VÁLIDO ---")
    print(sec.validar_operacao(contexto_valido))

    print("\n--- TESTE CONTEXTO INVÁLIDO ---")
    print(sec.validar_operacao(contexto_invalido))
