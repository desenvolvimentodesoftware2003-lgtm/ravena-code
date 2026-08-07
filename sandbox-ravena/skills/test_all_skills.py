#!/usr/bin/env python3
"""
TESTE: Todas as Skills Nativas da Sandbox
Executa testes em todas as skills disponíveis
"""

import sys
import os

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills import (
    sqli_detector,
    brute_force_protector,
    session_manager,
    input_validator,
    rate_limiter,
    audit_logger
)

def print_header(title):
    """Imprime cabeçalho"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_subheader(title):
    """Imprime subcabeçalho"""
    print(f"\n--- {title} ---")

def test_sqli_detector():
    """Testa SQLiDetector"""
    print_header("TESTE: SQL Injection Detector")
    
    test_cases = [
        ("' OR 1=1--", True),
        ("admin'--", True),
        ("' UNION SELECT * FROM users--", True),
        ("normal input", False),
        ("'; DROP TABLE users;--", True),
        ("1' AND '1'='1", True),
        ("hello world", False)
    ]
    
    for input_data, expected in test_cases:
        is_malicious, attack_type, confidence = sqli_detector.analyze(input_data)
        status = "OK" if is_malicious == expected else "FALHA"
        print(f"[{status}] Input: {input_data[:30]:<30} | Malicioso: {is_malicious} | Tipo: {attack_type}")
    
    print(f"\nEstatísticas: {sqli_detector.get_stats()}")

def test_brute_force_protector():
    """Testa BruteForceProtector"""
    print_header("TESTE: Brute Force Protector")
    
    protector = brute_force_protector
    
    # Resetar para teste
    protector.reset_lockout("192.168.1.100", "admin")
    
    print_subheader("Tentativas de Login")
    for i in range(7):
        allowed, message = protector.check_attempt("192.168.1.100", "admin")
        print(f"Tentativa {i+1}: Permitido={allowed} | Mensagem={message}")
    
    print(f"\nEstatísticas: {protector.get_stats()}")

def test_session_manager():
    """Testa SessionManager"""
    print_header("TESTE: Session Manager")
    
    manager = session_manager
    
    print_subheader("Criando Sessões")
    tokens = []
    for i in range(3):
        result = manager.create_session(
            user_id="user_001",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0"
        )
        tokens.append(result['token'])
        print(f"Sessão {i+1}: {result['token'][:16]}... | Expira: {result['expires_at']}")
    
    print_subheader("Validando Sessão")
    is_valid, data = manager.validate_session(tokens[0], "192.168.1.100")
    print(f"Válido: {is_valid} | Dados: {data}")
    
    print_subheader("Sessões do Usuário")
    sessions = manager.get_user_sessions("user_001")
    for s in sessions:
        print(f"  Token: {s['token']} | IP: {s['ip_address']}")
    
    print(f"\nEstatísticas: {manager.get_stats()}")

def test_input_validator():
    """Testa InputValidator"""
    print_header("TESTE: Input Validator")
    
    validator = input_validator
    
    print_subheader("Validação de Campos")
    test_cases = [
        ("admin", "username", True),
        ("' OR 1=1--", "username", False),
        ("user@example.com", "email", True),
        ("invalid-email", "email", False),
        ("100.50", "amount", True),
        ("-10", "amount", False)
    ]
    
    for value, field_type, expected in test_cases:
        is_valid, error, sanitized = validator.validate(value, field_type)
        status = "✓" if is_valid == expected else "✗"
        print(f"{status} {field_type}: {value[:20]:<20} | Válido: {is_valid} | Erro: {error}")
    
    print_subheader("Força de Senha")
    passwords = ["123456", "Abc@1234", "S3gura@Fort3"]
    for pwd in passwords:
        result = validator.validate_password_strength(pwd)
        print(f"{pwd:<15} | Score: {result['score']}% | Forte: {result['is_strong']}")
    
    print(f"\nEstatísticas: {validator.get_stats()}")

def test_rate_limiter():
    """Testa RateLimiter"""
    print_header("TESTE: Rate Limiter")
    
    limiter = rate_limiter
    
    # Criar limite personalizado para teste
    limiter.set_custom_limit('test_endpoint', 3, 10)
    
    print_subheader("Teste de Rate Limiting")
    test_key = "192.168.1.100"
    
    for i in range(5):
        allowed, info = limiter.check_rate_limit(test_key, 'test_endpoint')
        print(f"Requisição {i+1}: Permitido={allowed} | Info={info}")
    
    print(f"\nEstatísticas: {limiter.get_stats()}")

def test_audit_logger():
    """Testa AuditLogger"""
    print_header("TESTE: Audit Logger")
    
    logger = audit_logger
    
    print_subheader("Registrando Ações")
    logger.log_login("user_001", "192.168.1.100", True)
    logger.log_login("user_002", "192.168.1.101", False)
    logger.log_withdrawal("user_001", 500.00, "success")
    logger.log_slot_spin("user_001", 100.00, 250.00)
    logger.log_security_event("sql_injection", "10.0.0.1", {"payload": "' OR 1=1--"})
    
    print(f"Total de logs: {len(logger.logs)}")
    
    print_subheader("Verificação de Integridade")
    for log in logger.logs[:3]:
        is_valid = logger.verify_integrity(log)
        print(f"Log {log['id'][:8]}...: Válido={is_valid}")
    
    print_subheader("Logs Recentes")
    recent = logger.get_recent_logs(3)
    for log in recent:
        print(f"  [{log['severity'].upper()}] {log['action']}: {log['status']}")
    
    print(f"\nEstatísticas: {logger.get_stats()}")

def test_combined():
    """Testa uso combinado das skills"""
    print_header("TESTE: Uso Combinado (Proteção de Login)")
    
    # Simular login seguro
    def secure_login(username, password, ip_address):
        # 1. Verificar rate limit
        allowed, info = rate_limiter.check_rate_limit(ip_address, 'login')
        if not allowed:
            return {'error': 'Rate limit excedido'}, 429
        
        # 2. Verificar brute force
        allowed, message = brute_force_protector.check_attempt(ip_address, username)
        if not allowed:
            return {'error': message}, 429
        
        # 3. Validar inputs
        is_valid, error, _ = input_validator.validate(username, 'username')
        if not is_valid:
            return {'error': error}, 400
        
        # 4. Verificar SQL Injection
        is_malicious, _, _ = sqli_detector.analyze(username)
        if is_malicious:
            audit_logger.log_security_event('sql_injection', ip_address, {'input': username})
            return {'error': 'Entrada inválida'}, 400
        
        # 5. Autenticar (simulado - sempre sucesso para teste)
        success = True
        
        # 6. Registrar tentativa
        audit_logger.log_login(username, ip_address, success)
        
        if success:
            # 7. Criar sessão
            session = session_manager.create_session(username, ip_address, 'Mozilla/5.0')
            return {'token': session['token']}, 200
        else:
            return {'error': 'Credenciais inválidas'}, 401
    
    # Testar cenários
    test_cases = [
        ("admin", "pass123", "192.168.1.100", 200),
        ("' OR 1=1--", "pass", "192.168.1.101", 400),
        ("user", "pass", "192.168.1.102", 200),
    ]
    
    for username, password, ip, expected_status in test_cases:
        result, status = secure_login(username, password, ip)
        status_ok = "✓" if status == expected_status else "✗"
        print(f"{status_ok} Login: {username[:20]:<20} | Status: {status} | Result: {result}")

def main():
    """Função principal"""
    print("="*60)
    print("  TESTE DE TODAS AS SKILLS - SANDBOX RAVENA")
    print("="*60)
    
    # Executar testes
    test_sqli_detector()
    test_brute_force_protector()
    test_session_manager()
    test_input_validator()
    test_rate_limiter()
    test_audit_logger()
    test_combined()
    
    # Estatísticas globais
    print_header("ESTATÍSTICAS GLOBAIS")
    from skills import get_all_stats
    stats = get_all_stats()
    
    for skill_name, skill_stats in stats.items():
        print(f"\n{skill_name}:")
        for key, value in skill_stats.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("  TESTES CONCLUÍDOS")
    print("="*60)

if __name__ == "__main__":
    main()
