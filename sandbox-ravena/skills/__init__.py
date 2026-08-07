"""
SKILLS NATIVAS - SANDBOX RAVENA
================================

Este módulo contém todas as skills nativas da sandbox para testes de segurança.
ATENÇÃO: Estas skills só funcionam no ambiente isolado da sandbox.

Skills Disponíveis:
- SQLiDetector: Detecção de SQL Injection
- BruteForceProtector: Proteção contra força bruta
- SessionManager: Gerenciamento de sessões
- InputValidator: Validação de entradas
- RateLimiter: Limitação de taxa de requisições
- AuditLogger: Logger de auditoria
"""

__version__ = "1.0.0"
__author__ = "Sandbox Ravena"

# Importar todas as skills
from .sqli_detector import SQLInjectionDetector, sqli_detector
from .brute_force_protector import BruteForceProtector, brute_force_protector
from .session_manager import SessionManager, session_manager
from .input_validator import InputValidator, input_validator
from .rate_limiter import RateLimiter, rate_limiter, rate_limit
from .audit_logger import AuditLogger, audit_logger

# Versão das skills
SKILLS_VERSION = "1.0.0"

# Listar todas as skills disponíveis
AVAILABLE_SKILLS = [
    {
        'name': 'SQLiDetector',
        'description': 'Detector de SQL Injection',
        'module': 'sqli_detector',
        'instance': sqli_detector
    },
    {
        'name': 'BruteForceProtector',
        'description': 'Protetor contra força bruta',
        'module': 'brute_force_protector',
        'instance': brute_force_protector
    },
    {
        'name': 'SessionManager',
        'description': 'Gerenciador de sessões',
        'module': 'session_manager',
        'instance': session_manager
    },
    {
        'name': 'InputValidator',
        'description': 'Validador de entradas',
        'module': 'input_validator',
        'instance': input_validator
    },
    {
        'name': 'RateLimiter',
        'description': 'Limitador de taxa de requisições',
        'module': 'rate_limiter',
        'instance': rate_limiter
    },
    {
        'name': 'AuditLogger',
        'description': 'Logger de auditoria',
        'module': 'audit_logger',
        'instance': audit_logger
    }
]


def get_skill_info():
    """Retorna informações sobre todas as skills"""
    return {
        'version': SKILLS_VERSION,
        'skills': AVAILABLE_SKILLS,
        'total': len(AVAILABLE_SKILLS)
    }


def get_all_stats():
    """Retorna estatísticas de todas as skills"""
    stats = {}
    
    for skill in AVAILABLE_SKILLS:
        skill_instance = skill['instance']
        if hasattr(skill_instance, 'get_stats'):
            stats[skill['name']] = skill_instance.get_stats()
    
    return stats


# Aviso de segurança
SECURITY_WARNING = """
=================================================================
                    AVISO DE SEGURANCA
=================================================================
  Estas skills sao projetadas APENAS para a Sandbox Ravena.

  NAO use estas skills em:
  - Ambientes de producao
  - Sistemas com dados reais
  - Aplicacoes de terceiros

  Uso inadequado pode resultar em danos e responsabilidade
  legal.
=================================================================
"""

print(SECURITY_WARNING)
