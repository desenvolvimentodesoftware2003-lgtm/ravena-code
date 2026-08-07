"""
RAVENA AI — Secrets Manager (Gerenciador Centralizado de Credenciais)
=====================================================================
Versão: 1.0.0-beta
Inspirado no modelo do Google Colab Secrets.

Este módulo centraliza TODA a leitura de credenciais sensíveis.
Nenhum outro módulo deve acessar os.environ diretamente para secrets.

Hierarquia de carregamento (prioridade decrescente):
  1. OCI Vault (produção) — via OCI SDK
  2. Variáveis de ambiente do sistema (container/docker)
  3. Arquivo .env local (desenvolvimento) — via python-dotenv

USO:
  from src.core.secrets_manager import secrets
  
  bybit_key = secrets.get("BYBIT_API_KEY")
  oci_compartment = secrets.get("OCI_COMPARTMENT_ID")
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Configuração de Logging
logger = logging.getLogger("ravena.secrets")


class SecretsManager:
    """
    Gerenciador centralizado de secrets.
    Similar ao Google Colab Secrets: você cadastra as chaves uma vez
    e o código só referencia por NOME.
    """

    # ─────────────────────────────────────────────
    # REGISTRO DE TODAS AS SECRETS DO SISTEMA
    # ─────────────────────────────────────────────
    REGISTRY = {
        # 🔴 CRÍTICO - Segurança Interna
        "RAVENA_ZERO_TRUST_SECRET": {
            "description": "Chave HMAC para assinatura de tokens entre módulos",
            "severity": "CRITICAL",
            "module": "security/zero_trust",
            "required": True,
            "default": None,  # NUNCA ter default para secrets críticos
        },
        # 🟠 ALTO - Trading (Bybit)
        "BYBIT_API_KEY": {
            "description": "API Key da exchange Bybit",
            "severity": "HIGH",
            "module": "trading/bybit_connector",
            "required": True,
            "default": None,
        },
        "BYBIT_API_SECRET": {
            "description": "API Secret da exchange Bybit",
            "severity": "HIGH",
            "module": "trading/bybit_connector",
            "required": True,
            "default": None,
        },
        # 🟠 ALTO - Oracle Cloud Infrastructure
        "OCI_COMPARTMENT_ID": {
            "description": "OCID do compartment na Oracle Cloud",
            "severity": "HIGH",
            "module": "core/ravena_model, trading/signal_bridge",
            "required": True,
            "default": None,
        },
        "QWEN_ENDPOINT_ID": {
            "description": "Endpoint ID do modelo Qwen na OCI",
            "severity": "HIGH",
            "module": "core/ravena_model, trading/signal_bridge",
            "required": True,
            "default": None,
        },
        "KIMI_ENDPOINT_ID": {
            "description": "Endpoint ID do modelo Kimi na OCI",
            "severity": "HIGH",
            "module": "core/ravena_model, trading/signal_bridge",
            "required": True,
            "default": None,
        },
        # 🟡 MÉDIO - Redes Sociais
        "INSTAGRAM_ACCESS_TOKEN": {
            "description": "Token de acesso à API do Instagram",
            "severity": "MEDIUM",
            "module": "utils/social_connector",
            "required": False,
            "default": "",
        },
        "INSTAGRAM_ACCOUNT_ID": {
            "description": "ID da conta do Instagram",
            "severity": "MEDIUM",
            "module": "utils/social_connector",
            "required": False,
            "default": "",
        },
        "INSTAGRAM_APP_ID": {
            "description": "App ID do aplicativo Instagram/Meta",
            "severity": "MEDIUM",
            "module": "utils/social_connector",
            "required": False,
            "default": "",
        },
        "INSTAGRAM_APP_SECRET": {
            "description": "App Secret do aplicativo Instagram/Meta",
            "severity": "MEDIUM",
            "module": "utils/social_connector",
            "required": False,
            "default": "",
        },
        "TELEGRAM_BOT_TOKEN": {
            "description": "Token do bot do Telegram",
            "severity": "MEDIUM",
            "module": "utils/telegram_bot",
            "required": False,
            "default": "",
        },
        "TELEGRAM_CHAT_ID": {
            "description": "Chat ID para notificações do Telegram",
            "severity": "MEDIUM",
            "module": "utils/telegram_bot",
            "required": False,
            "default": "",
        },
        "OPENAI_API_KEY": {
            "description": "API Key da OpenAI (fallback LLM)",
            "severity": "MEDIUM",
            "module": "utils/external_api_manager",
            "required": False,
            "default": "",
        },
        # 🔵 BAIXO - Configuração
        "LLM_MODE": {
            "description": "Modo de operação do LLM (local/hibrido/cloud)",
            "severity": "LOW",
            "module": "utils/social_connector",
            "required": False,
            "default": "hibrido",
        },
        "RAVENA_SOBERANIA": {
            "description": "Flag de ativação do modo soberano",
            "severity": "LOW",
            "module": "core/omega_orchestrator",
            "required": False,
            "default": "false",
        },
        "RAVENA_CONFIG_PATH": {
            "description": "Caminho para o arquivo config_v3.json",
            "severity": "LOW",
            "module": "core/omega",
            "required": False,
            "default": "config/config_v3.json",
        },
        "RAVENA_ENV": {
            "description": "Ambiente de execução (development/production)",
            "severity": "LOW",
            "module": "global",
            "required": False,
            "default": "development",
        },
    }

    def __init__(self):
        self._cache: Dict[str, Optional[str]] = {}
        self._source: str = "unknown"
        self._loaded = False
        self._load()

    def _load(self):
        """Carrega secrets na ordem de prioridade."""
        # Tentativa 1: OCI Vault (produção)
        if os.getenv("RAVENA_ENV") == "production":
            if self._load_from_oci_vault():
                self._source = "OCI Vault"
                self._loaded = True
                logger.info("Secrets carregados do OCI Vault (produção).")
                return

        # Tentativa 2: Variáveis de ambiente do sistema
        env_count = self._load_from_env()
        if env_count > 0:
            self._source = "environment"
            self._loaded = True
            logger.info(f"Secrets carregados de variáveis de ambiente ({env_count} encontrados).")
            return

        # Tentativa 3: Arquivo .env local
        if self._load_from_dotenv():
            self._source = "dotenv (.env)"
            self._loaded = True
            logger.info("Secrets carregados do arquivo .env local.")
            return

        logger.warning("Nenhuma fonte de secrets encontrada. Sistema operando sem credenciais.")

    def _load_from_oci_vault(self) -> bool:
        """Carrega secrets do OCI Vault Service."""
        try:
            import oci
            config = oci.config.from_file()
            vault_client = oci.vault.VaultsClient(config)
            secrets_client = oci.secrets.SecretsClient(config)

            # O vault_id deve estar configurado como env var
            vault_id = os.getenv("OCI_VAULT_ID")
            compartment_id = os.getenv("OCI_COMPARTMENT_ID")

            if not vault_id or not compartment_id:
                return False

            # Listar secrets do vault
            secrets_list = vault_client.list_secrets(compartment_id=compartment_id).data

            for secret in secrets_list:
                if secret.secret_name in self.REGISTRY:
                    # Buscar o valor do secret
                    bundle = secrets_client.get_secret_bundle(secret_id=secret.id).data
                    import base64
                    value = base64.b64decode(bundle.secret_bundle_content.content).decode()
                    self._cache[secret.secret_name] = value

            return len(self._cache) > 0

        except Exception as e:
            logger.debug(f"OCI Vault não disponível: {e}")
            return False

    def _load_from_env(self) -> int:
        """Carrega secrets das variáveis de ambiente do sistema."""
        count = 0
        for key in self.REGISTRY:
            value = os.environ.get(key)
            if value:
                self._cache[key] = value
                count += 1
        return count

    def _load_from_dotenv(self) -> bool:
        """Carrega secrets do arquivo .env local."""
        try:
            from dotenv import load_dotenv

            # Buscar .env no diretório raiz do projeto
            env_paths = [
                Path.cwd() / ".env",
                Path(__file__).parent.parent.parent / ".env",
                Path.home() / "ravena-aim" / ".env",
            ]

            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"Arquivo .env carregado de: {env_path}")
                    # Recarregar do ambiente após dotenv
                    return self._load_from_env() > 0

            return False

        except ImportError:
            logger.debug("python-dotenv não instalado. Pulando .env.")
            return False

    def get(self, key: str, required: bool = None) -> Optional[str]:
        """
        Obtém o valor de um secret pelo nome.
        
        Similar ao Google Colab:
          from google.colab import userdata
          userdata.get('OPENAI_API_KEY')
        
        Aqui:
          from src.core.secrets_manager import secrets
          secrets.get('OPENAI_API_KEY')
        """
        # Verificar cache primeiro
        if key in self._cache and self._cache[key]:
            return self._cache[key]

        # Fallback para env var direta
        value = os.environ.get(key)
        if value:
            self._cache[key] = value
            return value

        # Verificar se tem default no registry
        if key in self.REGISTRY:
            default = self.REGISTRY[key].get("default")
            is_required = required if required is not None else self.REGISTRY[key].get("required", False)

            if is_required and not default:
                logger.error(
                    f"⚠️ SECRET OBRIGATÓRIO NÃO ENCONTRADO: {key} "
                    f"(módulo: {self.REGISTRY[key]['module']})"
                )
                return None

            return default

        logger.warning(f"Secret '{key}' não está registrado no REGISTRY.")
        return None

    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Retorna o status de todos os secrets (sem valores, apenas status)."""
        status = {}
        for key, meta in self.REGISTRY.items():
            has_value = bool(self._cache.get(key) or os.environ.get(key))
            status[key] = {
                "description": meta["description"],
                "severity": meta["severity"],
                "module": meta["module"],
                "loaded": has_value,
                "source": self._source if has_value else "NOT_SET",
            }
        return status

    def audit(self) -> Dict[str, Any]:
        """
        Executa auditoria de segurança nos secrets.
        Retorna relatório de conformidade.
        """
        report = {
            "total_secrets": len(self.REGISTRY),
            "loaded": 0,
            "missing_critical": [],
            "missing_high": [],
            "source": self._source,
            "compliant": True,
        }

        for key, meta in self.REGISTRY.items():
            has_value = bool(self._cache.get(key) or os.environ.get(key))
            if has_value:
                report["loaded"] += 1
            elif meta["required"]:
                if meta["severity"] == "CRITICAL":
                    report["missing_critical"].append(key)
                    report["compliant"] = False
                elif meta["severity"] == "HIGH":
                    report["missing_high"].append(key)
                    report["compliant"] = False

        return report

    @property
    def source(self) -> str:
        """Retorna a fonte atual dos secrets."""
        return self._source

    @property
    def is_production(self) -> bool:
        """Verifica se está em modo produção."""
        return self.get("RAVENA_ENV") == "production"


# ─────────────────────────────────────────────
# INSTÂNCIA GLOBAL (Singleton)
# ─────────────────────────────────────────────
secrets = SecretsManager()


# ─────────────────────────────────────────────
# FUNÇÕES DE CONVENIÊNCIA
# ─────────────────────────────────────────────
def get_secret(key: str) -> Optional[str]:
    """Atalho para secrets.get(key)."""
    return secrets.get(key)


def check_health() -> bool:
    """Verifica se os secrets críticos estão carregados."""
    audit = secrets.audit()
    return audit["compliant"]


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  RAVENA AIM — Auditoria de Secrets")
    print("=" * 60)
    print(f"\n  Fonte: {secrets.source}")
    print(f"  Ambiente: {secrets.get('RAVENA_ENV')}")
    print()

    status = secrets.get_all()
    for key, info in status.items():
        icon = "✅" if info["loaded"] else "❌"
        print(f"  {icon} [{info['severity']:8s}] {key}")
        print(f"     └─ {info['description']}")
        print()

    audit = secrets.audit()
    print(f"\n  Carregados: {audit['loaded']}/{audit['total_secrets']}")
    if audit["compliant"]:
        print("  ✅ SISTEMA CONFORME — Todos os secrets críticos presentes.")
    else:
        print("  ❌ SISTEMA NÃO CONFORME:")
        for key in audit["missing_critical"]:
            print(f"     🔴 FALTANDO: {key}")
        for key in audit["missing_high"]:
            print(f"     🟠 FALTANDO: {key}")
