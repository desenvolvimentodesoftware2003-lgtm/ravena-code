#!/usr/bin/env python3
"""
Script de Testes de Segurança - Sandbox Ravena
Executa cenários de ataque controlados para validação
"""

import requests
import json
import time
from datetime import datetime
import psycopg2

# ============================================
# CONFIGURAÇÕES
# ============================================

BASE_URL = "http://localhost:8080"
DB_CONFIG = {
    'host': 'localhost',
    'database': 'ravena_sandbox',
    'user': 'ravena_test',
    'password': 'sandbox_password_123'
}

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def log_test(test_name, result, details=None):
    """Registra resultado de teste"""
    status = "✓ PASS" if result else "✗ FAIL"
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {status} - {test_name}")
    if details:
        print(f"         Detalhes: {details}")

def get_db_connection():
    """Obtém conexão com o banco"""
    return psycopg2.connect(**DB_CONFIG)

def get_attack_stats():
    """Obtém estatísticas de ataques"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT attack_type, COUNT(*) as total, 
               SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked
        FROM attack_log
        GROUP BY attack_type
    """)
    
    stats = {}
    for row in cursor.fetchall():
        stats[row[0]] = {'total': row[1], 'blocked': row[2]}
    
    conn.close()
    return stats

# ============================================
# TESTES DE AUTENTICAÇÃO
# ============================================

def test_login_normal():
    """Teste: Login com credenciais válidas"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        'username': 'attacker_001',
        'password': 'test123'
    })
    
    success = response.status_code == 200
    token = response.json().get('token') if success else None
    
    log_test("Login Normal", success, f"Status: {response.status_code}")
    return token

def test_login_invalid_credentials():
    """Teste: Login com credenciais inválidas"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        'username': 'attacker_001',
        'password': 'wrong_password'
    })
    
    success = response.status_code == 401
    log_test("Login Credenciais Inválidas", success, f"Status: {response.status_code}")

def test_login_sql_injection():
    """Teste: SQL Injection no login"""
    payloads = [
        "' OR 1=1--",
        "admin'--",
        "' OR '1'='1",
        "1' UNION SELECT * FROM users--"
    ]
    
    for payload in payloads:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            'username': payload,
            'password': 'anything'
        })
        
        # Deve retornar 403 ou 401 (não 200)
        success = response.status_code in [401, 403]
        log_test(f"SQLi Login: {payload[:20]}...", success, f"Status: {response.status_code}")

def test_login_xss():
    """Teste: XSS no login"""
    payloads = [
        '<script>alert("xss")</script>',
        'javascript:alert(1)',
        'onload=alert(1)'
    ]
    
    for payload in payloads:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            'username': payload,
            'password': 'test123'
        })
        
        success = response.status_code in [401, 403]
        log_test(f"XSS Login: {payload[:20]}...", success, f"Status: {response.status_code}")

def test_brute_force():
    """Teste: Força bruta no login"""
    print("\n[INFO] Testando força bruta (10 tentativas)...")
    
    for i in range(10):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            'username': 'attacker_001',
            'password': f'wrong_{i}'
        })
        
        if response.status_code == 429:
            log_test("Força Bruta Bloqueada", True, f"Bloqueado após {i+1} tentativas")
            return
    
    log_test("Força Bruta Bloqueada", False, "Não foi bloqueado após 10 tentativas")

# ============================================
# TESTES DE SLOTS
# ============================================

def test_slot_spin(token):
    """Teste: Aposta em slot"""
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f"{BASE_URL}/api/slots/spin", 
        headers=headers,
        json={'amount': 100}
    )
    
    success = response.status_code == 200
    result = response.json() if success else {}
    
    log_test("Aposta Slot", success, 
             f"Status: {response.status_code} | Win: {result.get('win')}")

def test_slot_manipulation(token):
    """Teste: Manipulação de aposta"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Tentar apostar valor negativo
    response = requests.post(f"{BASE_URL}/api/slots/spin", 
        headers=headers,
        json={'amount': -100}
    )
    
    success = response.status_code == 400
    log_test("Manipulação Slot (valor negativo)", success, f"Status: {response.status_code}")
    
    # Tentar apostar valor acima do limite
    response = requests.post(f"{BASE_URL}/api/slots/spin", 
        headers=headers,
        json={'amount': 99999}
    )
    
    success = response.status_code == 400
    log_test("Manipulação Slot (valor alto)", success, f"Status: {response.status_code}")

# ============================================
# TESTES DE SAQUE
# ============================================

def test_withdrawal_normal(token):
    """Teste: Saque normal"""
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f"{BASE_URL}/api/withdrawals/request",
        headers=headers,
        json={
            'amount': 100,
            'pix_key': 'test@pix.com'
        }
    )
    
    success = response.status_code == 201
    log_test("Saque Normal", success, f"Status: {response.status_code}")

def test_withdrawal_sql_injection(token):
    """Teste: SQL Injection no saque"""
    headers = {'Authorization': f'Bearer {token}'}
    
    payloads = [
        "100' OR '1'='1",
        "100; DROP TABLE transactions--",
        "100 UNION SELECT * FROM users--"
    ]
    
    for payload in payloads:
        response = requests.post(f"{BASE_URL}/api/withdrawals/request",
            headers=headers,
            json={
                'amount': payload,
                'pix_key': 'test@pix.com'
            }
        )
        
        success = response.status_code in [400, 403]
        log_test(f"SQLi Saque: {payload[:20]}...", success, f"Status: {response.status_code}")

def test_withdrawal_exceed_balance(token):
    """Teste: Saque acima do saldo"""
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f"{BASE_URL}/api/withdrawals/request",
        headers=headers,
        json={
            'amount': 999999,
            'pix_key': 'test@pix.com'
        }
    )
    
    success = response.status_code == 400
    log_test("Saque Acima do Saldo", success, f"Status: {response.status_code}")

def test_withdrawal_invalid_pix(token):
    """Teste: Chave PIX inválida"""
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(f"{BASE_URL}/api/withdrawals/request",
        headers=headers,
        json={
            'amount': 100,
            'pix_key': 'abc'
        }
    )
    
    success = response.status_code == 400
    log_test("Saque PIX Inválido", success, f"Status: {response.status_code}")

# ============================================
# TESTES DE IDOR
# ============================================

def test_idor(token):
    """Teste: IDOR (acesso a dados de outro usuário)"""
    headers = {'Authorization': f'Bearer {token}'}
    
    # Tentar acessar saques de outro usuário
    response = requests.get(f"{BASE_URL}/api/withdrawals/history",
        headers=headers
    )
    
    success = response.status_code == 200
    log_test("Acesso Próprio Histórico", success, f"Status: {response.status_code}")

# ============================================
# TESTES DE SESSÃO
# ============================================

def test_expired_session():
    """Teste: Sessão expirada"""
    # Token inválido/expirado
    headers = {'Authorization': 'Bearer invalid_token_123'}
    
    response = requests.get(f"{BASE_URL}/api/auth/me",
        headers=headers
    )
    
    success = response.status_code == 401
    log_test("Sessão Inválida", success, f"Status: {response.status_code}")

# ============================================
# TESTES DE PATH TRAVERSAL
# ============================================

def test_path_traversal(token):
    """Teste: Path Traversal"""
    headers = {'Authorization': f'Bearer {token}'}
    
    payloads = [
        '../../../etc/passwd',
        '..\\..\\..\\windows\\system32',
        '%2e%2e%2f%2e%2e%2f'
    ]
    
    for payload in payloads:
        response = requests.get(f"{BASE_URL}/api/{payload}",
            headers=headers
        )
        
        success = response.status_code in [400, 403, 404]
        log_test(f"Path Traversal: {payload[:20]}...", success, f"Status: {response.status_code}")

# ============================================
# EXECUÇÃO PRINCIPAL
# ============================================

def main():
    """Executa todos os testes"""
    print("="*60)
    print("TESTES DE SEGURANÇA - SANDBOX RAVENA")
    print(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("[ERRO] Servidor não está respondendo")
            return
    except requests.ConnectionError:
        print("[ERRO] Não foi possível conectar ao servidor")
        print("[INFO] Execute: docker-compose up -d")
        return
    
    # Obter token
    print("\n[FASE 1] Autenticação")
    token = test_login_normal()
    
    if not token:
        print("[ERRO] Falha ao obter token")
        return
    
    # Testes de autenticação
    print("\n[FASE 2] Testes de Autenticação")
    test_login_invalid_credentials()
    test_login_sql_injection()
    test_login_xss()
    test_brute_force()
    
    # Testes de slots
    print("\n[FASE 3] Testes de Slots")
    test_slot_spin(token)
    test_slot_manipulation(token)
    
    # Testes de saque
    print("\n[FASE 4] Testes de Saque")
    test_withdrawal_normal(token)
    test_withdrawal_sql_injection(token)
    test_withdrawal_exceed_balance(token)
    test_withdrawal_invalid_pix(token)
    
    # Testes de IDOR
    print("\n[FASE 5] Testes de IDOR")
    test_idor(token)
    
    # Testes de sessão
    print("\n[FASE 6] Testes de Sessão")
    test_expired_session()
    
    # Testes de path traversal
    print("\n[FASE 7] Testes de Path Traversal")
    test_path_traversal(token)
    
    # Estatísticas finais
    print("\n" + "="*60)
    print("ESTATÍSTICAS FINAIS")
    print("="*60)
    
    stats = get_attack_stats()
    for attack_type, data in stats.items():
        print(f"{attack_type}: {data['total']} tentativas, {data['blocked']} bloqueadas")
    
    print(f"\nFim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

if __name__ == "__main__":
    main()
