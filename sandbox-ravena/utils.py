#!/usr/bin/env python3
"""
Utilitários - Sandbox Ravena
Funções auxiliares para manutenção e análise
"""

import psycopg2
import json
import os
from datetime import datetime, timedelta
import argparse

# ============================================
# CONFIGURAÇÕES
# ============================================

DB_CONFIG = {
    'host': 'localhost',
    'database': 'ravena_sandbox',
    'user': 'ravena_test',
    'password': 'sandbox_password_123'
}

# ============================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================

def get_db_connection():
    """Obtém conexão com o banco"""
    return psycopg2.connect(**DB_CONFIG)

def show_statistics():
    """Mostra estatísticas gerais"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("ESTATÍSTICAS DA SANDBOX")
    print("="*60)
    
    # Total de usuários
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    print(f"\nUsuários: {total_users}")
    
    # Saldos
    cursor.execute("SELECT SUM(balance) FROM users")
    total_balance = cursor.fetchone()[0]
    print(f"Saldo Total: R$ {total_balance:,.2f}")
    
    # Transações
    cursor.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = cursor.fetchone()[0]
    print(f"Transações: {total_transactions}")
    
    # Apostas
    cursor.execute("SELECT COUNT(*) FROM slot_bets")
    total_bets = cursor.fetchone()[0]
    print(f"Apostas: {total_bets}")
    
    # Ataques
    cursor.execute("SELECT COUNT(*) FROM attack_log")
    total_attacks = cursor.fetchone()[0]
    print(f"Tentativas de Ataque: {total_attacks}")
    
    cursor.execute("SELECT COUNT(*) FROM attack_log WHERE blocked = TRUE")
    blocked_attacks = cursor.fetchone()[0]
    print(f"Ataques Bloqueados: {blocked_attacks}")
    
    # Taxa de bloqueio
    if total_attacks > 0:
        block_rate = (blocked_attacks / total_attacks) * 100
        print(f"Taxa de Bloqueio: {block_rate:.1f}%")
    
    # Sessões ativas
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()")
    active_sessions = cursor.fetchone()[0]
    print(f"Sessões Ativas: {active_sessions}")
    
    # Logs de auditoria
    cursor.execute("SELECT COUNT(*) FROM audit_log")
    total_logs = cursor.fetchone()[0]
    print(f"Logs de Auditoria: {total_logs}")
    
    print("\n" + "="*60)
    
    conn.close()

def show_recent_attacks(limit=20):
    """Mostra ataques recentes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print(f"ÚLTIMOS {limit} ATAQUES")
    print("="*60)
    
    cursor.execute("""
        SELECT attack_type, endpoint, blocked, ip_address, timestamp
        FROM attack_log
        ORDER BY timestamp DESC
        LIMIT %s
    """, (limit,))
    
    attacks = cursor.fetchall()
    
    if not attacks:
        print("\nNenhum ataque registrado")
    else:
        print(f"\n{'Tipo':<20} {'Endpoint':<20} {'Status':<10} {'IP':<15} {'Data/Hora'}")
        print("-" * 90)
        
        for attack in attacks:
            attack_type = attack[0]
            endpoint = attack[1] or 'N/A'
            blocked = "BLOQUEADO" if attack[2] else "FALHA"
            ip_address = str(attack[3]) if attack[3] else 'N/A'
            timestamp = attack[4].strftime('%Y-%m-%d %H:%M:%S') if attack[4] else 'N/A'
            
            print(f"{attack_type:<20} {endpoint:<20} {blocked:<10} {ip_address:<15} {timestamp}")
    
    print("\n" + "="*60)
    
    conn.close()

def show_users():
    """Mostra todos os usuários"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("USUÁRIOS DA SANDBOX")
    print("="*60)
    
    cursor.execute("SELECT username, email, balance, status FROM users ORDER BY username")
    users = cursor.fetchall()
    
    print(f"\n{'Usuário':<20} {'Email':<30} {'Saldo':<15} {'Status'}")
    print("-" * 80)
    
    for user in users:
        username = user[0]
        email = user[1]
        balance = f"R$ {user[2]:,.2f}"
        status = user[3]
        
        print(f"{username:<20} {email:<30} {balance:<15} {status}")
    
    print("\n" + "="*60)
    
    conn.close()

def reset_database():
    """Reseta o banco de dados para o estado inicial"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n[AVISO] Isso irá apagar todos os dados!")
    confirm = input("Tem certeza? (s/n): ")
    
    if confirm.lower() != 's':
        print("Operação cancelada")
        return
    
    print("\n[INFO] Resetando banco de dados...")
    
    # Limpar tabelas
    cursor.execute("TRUNCATE attack_log CASCADE")
    cursor.execute("TRUNCATE audit_log CASCADE")
    cursor.execute("TRUNCATE slot_bets CASCADE")
    cursor.execute("TRUNCATE transactions CASCADE")
    cursor.execute("TRUNCATE sessions CASCADE")
    
    # Resetar usuários
    cursor.execute("UPDATE users SET balance = 10000.00 WHERE username = 'attacker_001'")
    cursor.execute("UPDATE users SET balance = 5000.00 WHERE username = 'vitima_001'")
    cursor.execute("UPDATE users SET balance = 3464.00 WHERE username = 'vitima_002'")
    cursor.execute("UPDATE users SET balance = 0.00 WHERE username = 'lara_001'")
    
    conn.commit()
    
    print("[OK] Banco de dados resetado com sucesso!")
    
    conn.close()

def export_logs(filename=None):
    """Exporta logs para JSON"""
    if not filename:
        filename = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\n[INFO] Exportando logs para {filename}...")
    
    # Exportar ataques
    cursor.execute("""
        SELECT attack_type, endpoint, payload, blocked, ip_address, user_agent, timestamp
        FROM attack_log
        ORDER BY timestamp DESC
    """)
    
    attacks = []
    for row in cursor.fetchall():
        attacks.append({
            'attack_type': row[0],
            'endpoint': row[1],
            'payload': row[2],
            'blocked': row[3],
            'ip_address': str(row[4]) if row[4] else None,
            'user_agent': row[5],
            'timestamp': row[6].isoformat() if row[6] else None
        })
    
    # Exportar auditoria
    cursor.execute("""
        SELECT table_name, operation, old_data, new_data, user_id, ip_address, timestamp
        FROM audit_log
        ORDER BY timestamp DESC
    """)
    
    audit = []
    for row in cursor.fetchall():
        audit.append({
            'table_name': row[0],
            'operation': row[1],
            'old_data': row[2],
            'new_data': row[3],
            'user_id': str(row[4]) if row[4] else None,
            'ip_address': str(row[5]) if row[5] else None,
            'timestamp': row[6].isoformat() if row[6] else None
        })
    
    # Salvar em JSON
    data = {
        'export_date': datetime.now().isoformat(),
        'attacks': attacks,
        'audit': audit
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Logs exportados com sucesso!")
    print(f"[INFO] Arquivo: {filename}")
    print(f"[INFO] Total de ataques: {len(attacks)}")
    print(f"[INFO] Total de auditoria: {len(audit)}")
    
    conn.close()

def cleanup_old_logs(days=7):
    """Limpa logs antigos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"\n[INFO] Limpando logs com mais de {days} dias...")
    
    # Calcular data limite
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Contar registros antigos
    cursor.execute("SELECT COUNT(*) FROM attack_log WHERE timestamp < %s", (cutoff_date,))
    old_attacks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp < %s", (cutoff_date,))
    old_audit = cursor.fetchone()[0]
    
    print(f"[INFO] Registros antigos encontrados:")
    print(f"  - Ataques: {old_attacks}")
    print(f"  - Auditoria: {old_audit}")
    
    confirm = input("\nDeseja remover? (s/n): ")
    
    if confirm.lower() != 's':
        print("Operação cancelada")
        return
    
    # Remover registros antigos
    cursor.execute("DELETE FROM attack_log WHERE timestamp < %s", (cutoff_date,))
    cursor.execute("DELETE FROM audit_log WHERE timestamp < %s", (cutoff_date,))
    
    conn.commit()
    
    print(f"[OK] Registros antigos removidos!")
    
    conn.close()

# ============================================
# MENU PRINCIPAL
# ============================================

def show_menu():
    """Mostra o menu principal"""
    print("\n" + "="*60)
    print("UTILITÁRIOS - SANDBOX RAVENA")
    print("="*60)
    print("\n1. Mostrar estatísticas")
    print("2. Mostrar ataques recentes")
    print("3. Mostrar usuários")
    print("4. Resetar banco de dados")
    print("5. Exportar logs")
    print("6. Limpar logs antigos")
    print("0. Sair")
    print("\n" + "="*60)

def main():
    """Função principal"""
    while True:
        show_menu()
        choice = input("\nEscolha uma opção: ")
        
        if choice == '1':
            show_statistics()
        elif choice == '2':
            limit = input("Quantos ataques mostrar? (padrão: 20): ")
            limit = int(limit) if limit.isdigit() else 20
            show_recent_attacks(limit)
        elif choice == '3':
            show_users()
        elif choice == '4':
            reset_database()
        elif choice == '5':
            export_logs()
        elif choice == '6':
            days = input("Dias para manter? (padrão: 7): ")
            days = int(days) if days.isdigit() else 7
            cleanup_old_logs(days)
        elif choice == '0':
            print("\nSaindo...")
            break
        else:
            print("\n[ERRO] Opção inválida")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    # Verificar se foram passados argumentos
    parser = argparse.ArgumentParser(description='Utilitários da Sandbox Ravena')
    parser.add_argument('--stats', action='store_true', help='Mostrar estatísticas')
    parser.add_argument('--attacks', type=int, help='Mostrar ataques recentes')
    parser.add_argument('--users', action='store_true', help='Mostrar usuários')
    parser.add_argument('--export', type=str, help='Exportar logs para arquivo')
    
    args = parser.parse_args()
    
    if args.stats:
        show_statistics()
    elif args.attacks:
        show_recent_attacks(args.attacks)
    elif args.users:
        show_users()
    elif args.export:
        export_logs(args.export)
    else:
        main()
