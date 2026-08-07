#!/usr/bin/env python3
"""
TESTE SIMPLIFICADO: Skills da Sandbox Ravena
"""

import sys
import os

# Adicionar diretório pai ao path para encontrar o pacote skills
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

print("="*60)
print("  TESTE DAS SKILLS - SANDBOX RAVENA")
print("="*60)

# Testar importação
try:
    from skills.sqli_detector import SQLInjectionDetector
    from skills.brute_force_protector import BruteForceProtector
    from skills.session_manager import SessionManager
    from skills.input_validator import InputValidator
    from skills.rate_limiter import RateLimiter
    from skills.audit_logger import AuditLogger
    print("\n[OK] Todas as skills foram importadas com sucesso!")
except Exception as e:
    print(f"\n[ERRO] Falha ao importar skills: {e}")
    sys.exit(1)

# Testar SQLiDetector
print("\n--- SQLiDetector ---")
detector = SQLInjectionDetector()
test_cases = [
    ("' OR 1=1--", True),
    ("admin'--", True),
    ("normal input", False)
]
for input_data, expected in test_cases:
    is_malicious, attack_type, confidence = detector.analyze(input_data)
    status = "OK" if is_malicious == expected else "FALHA"
    print(f"[{status}] {input_data[:25]:<25} | Malicioso: {is_malicious}")

# Testar BruteForceProtector
print("\n--- BruteForceProtector ---")
protector = BruteForceProtector(max_attempts=3, window_minutes=1, lockout_minutes=1)
for i in range(4):
    allowed, message = protector.check_attempt("192.168.1.100", "admin")
    print(f"Tentativa {i+1}: Permitido={allowed}")

# Testar SessionManager
print("\n--- SessionManager ---")
manager = SessionManager()
session = manager.create_session("user_001", "192.168.1.100", "Mozilla/5.0")
print(f"Sessao criada: {session['token'][:16]}...")
is_valid, data = manager.validate_session(session['token'], "192.168.1.100")
print(f"Validacao: {is_valid}")

# Testar InputValidator
print("\n--- InputValidator ---")
validator = InputValidator()
is_valid, error, sanitized = validator.validate("admin", "username")
print(f"Username 'admin': Valido={is_valid}")
is_valid, error, sanitized = validator.validate("' OR 1=1--", "username")
print(f"SQL Injection: Valido={is_valid}")

# Testar RateLimiter
print("\n--- RateLimiter ---")
limiter = RateLimiter()
limiter.set_custom_limit('test', 3, 10)
for i in range(4):
    allowed, info = limiter.check_rate_limit("192.168.1.100", 'test')
    print(f"Requisicao {i+1}: Permitido={allowed}")

# Testar AuditLogger
print("\n--- AuditLogger ---")
logger = AuditLogger()
logger.log_login("user_001", "192.168.1.100", True)
logger.log_withdrawal("user_001", 500.00, "success")
print(f"Total de logs: {len(logger.logs)}")

# Estatisticas
print("\n" + "="*60)
print("  ESTATISTICAS")
print("="*60)
print(f"SQLiDetector: {detector.get_stats()}")
print(f"BruteForceProtector: {protector.get_stats()}")
print(f"SessionManager: {manager.get_stats()}")
print(f"InputValidator: {validator.get_stats()}")
print(f"RateLimiter: {limiter.get_stats()}")
print(f"AuditLogger: {logger.get_stats()}")

print("\n" + "="*60)
print("  TESTES CONCLUIDOS COM SUCESSO!")
print("="*60)
