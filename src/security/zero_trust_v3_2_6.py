import hmac
import hashlib
import time
import os
import logging
from functools import wraps

logger = logging.getLogger("ZeroTrust")


def _load_secret_key() -> str:
    """Carrega a chave secreta do ambiente. NUNCA usar valor hardcoded em produção."""
    try:
        from src.core.secrets_manager import secrets
        key = secrets.get("RAVENA_ZERO_TRUST_SECRET")
        if key:
            return key
    except ImportError:
        pass
    # Fallback para variável de ambiente direta
    key = os.environ.get("RAVENA_ZERO_TRUST_SECRET")
    if key:
        return key
    # AVISO: Valor padrão apenas para desenvolvimento local
    logger.warning(
        "⚠️ RAVENA_ZERO_TRUST_SECRET não definido! "
        "Usando chave padrão de desenvolvimento. NÃO USE EM PRODUÇÃO!"
    )
    return "ravena_core_secret_dev_only_2026"


class ZeroTrustProtocol:
    """
    Implementa a blindagem de segurança e controle de acessos dentro da 
    arquitetura modular da Ravena V3.
    """

    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = _load_secret_key()
        self.secret_key = secret_key.encode()
        self.access_logs = []

    def generate_token(self, module_id: str) -> str:
        """Gera um token de acesso temporário para um módulo específico."""
        timestamp = str(int(time.time())).encode()
        message = module_id.encode() + timestamp
        signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
        return f"{signature}.{timestamp.decode()}"

    def validate_access(self, module_id: str, token: str) -> bool:
        """Valida se o token de acesso é legítimo e não expirou."""
        try:
            signature, timestamp = token.split(".")
            current_time = int(time.time())

            # 1. Verificar expiração (TTL de 60 segundos)
            if current_time - int(timestamp) > 60:
                logger.warning(f"Acesso negado para {module_id}: Token expirado.")
                return False

            # 2. Validar assinatura
            message = module_id.encode() + timestamp.encode()
            expected_signature = hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()

            if hmac.compare_digest(signature, expected_signature):
                logger.info(f"Acesso concedido para o módulo: {module_id}")
                return True
            else:
                logger.error(f"Acesso negado para {module_id}: Assinatura inválida.")
                return False
        except Exception as e:
            logger.error(f"Erro na validação Zero Trust: {str(e)}")
            return False


def secure_module(module_id: str):
    """Decorator para proteger funções/métodos com o protocolo Zero Trust."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Em um cenário real, o token viria do contexto da requisição
            token = kwargs.get('auth_token')
            zt = ZeroTrustProtocol()
            if zt.validate_access(module_id, token):
                return func(self, *args, **kwargs)
            else:
                raise PermissionError(f"Módulo {module_id} bloqueado pelo Protocolo Zero Trust.")
        return wrapper
    return decorator


if __name__ == "__main__":
    zt = ZeroTrustProtocol()
    m_id = "orchestration_core"
    tkn = zt.generate_token(m_id)
    print(f"Token gerado: {tkn}")
    print(f"Validação: {zt.validate_access(m_id, tkn)}")
