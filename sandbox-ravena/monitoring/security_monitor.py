#!/usr/bin/env python3
"""
Monitor de Segurança - Sandbox Ravena
Detecta e registra tentativas de ataque em tempo real
"""

import psycopg2
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class SecurityMonitor:
    def __init__(self):
        self.db_config = {
            'host': 'ravena-db',
            'database': 'ravena_sandbox',
            'user': 'ravena_test',
            'password': 'sandbox_password_123'
        }
        self.attack_patterns = {
            'sql_injection': [
                "' OR 1=1",
                "' OR '1'='1",
                "UNION SELECT",
                "DROP TABLE",
                "INSERT INTO",
                "DELETE FROM",
                "--",
                ";",
                "/*",
                "XP_",
                "EXEC(",
                "CHAR(",
                "0x",
                "WAITFOR",
                "BENCHMARK("
            ],
            'xss': [
                '<script>',
                'javascript:',
                'onload=',
                'onerror=',
                'alert(',
                'document.cookie',
                'eval(',
                'innerHTML'
            ],
            'path_traversal': [
                '../',
                '..\\',
                '%2e%2e',
                'etc/passwd',
                'etc/shadow',
                'proc/self'
            ],
            'brute_force': [
                'admin',
                'password',
                '123456',
                'qwerty',
                'letmein'
            ]
        }
        self.alert_thresholds = {
            'sql_injection': 3,
            'brute_force': 10,
            'session_hijack': 5,
            'idor': 5
        }
        self.running = False
        self.attack_counts = defaultdict(int)
        
    def connect_db(self):
        """Conecta ao banco de dados"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            print(f"[ERRO] Falha na conexão: {e}")
            return None
    
    def detect_sql_injection(self, payload):
        """Detecta tentativas de SQL Injection"""
        if not payload:
            return False
        payload_upper = str(payload).upper()
        for pattern in self.attack_patterns['sql_injection']:
            if pattern.upper() in payload_upper:
                return True
        return False
    
    def detect_xss(self, payload):
        """Detecta tentativas de XSS"""
        if not payload:
            return False
        payload_lower = str(payload).lower()
        for pattern in self.attack_patterns['xss']:
            if pattern.lower() in payload_lower:
                return True
        return False
    
    def detect_path_traversal(self, payload):
        """Detecta tentativas de Path Traversal"""
        if not payload:
            return False
        payload_lower = str(payload).lower()
        for pattern in self.attack_patterns['path_traversal']:
            if pattern.lower() in payload_lower:
                return True
        return False
    
    def log_attack(self, attack_type, endpoint, payload, ip_address, user_agent, blocked=False):
        """Registra tentativa de ataque no banco"""
        conn = self.connect_db()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO attack_log 
                (attack_type, endpoint, payload, ip_address, user_agent, blocked)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (attack_type, endpoint, str(payload)[:1000], ip_address, user_agent, blocked))
            
            conn.commit()
            self.attack_counts[attack_type] += 1
            
            # Alerta se threshold excedido
            if self.attack_counts[attack_type] >= self.alert_thresholds.get(attack_type, 10):
                self.send_alert(attack_type)
            
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao registrar ataque: {e}")
            return False
        finally:
            conn.close()
    
    def send_alert(self, attack_type):
        """Envia alerta de segurança"""
        print(f"\n{'='*60}")
        print(f"[ALERTA CRÍTICO] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tipo de ataque: {attack_type}")
        print(f"Total de tentativas: {self.attack_counts[attack_type]}")
        print(f"{'='*60}\n")
        
        # Registrar alerta
        conn = self.connect_db()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_log (table_name, operation, new_data, ip_address)
                    VALUES ('SECURITY_ALERT', 'ALERT', %s, %s)
                """, (
                    json.dumps({
                        'attack_type': attack_type,
                        'count': self.attack_counts[attack_type],
                        'alert_level': 'CRITICAL'
                    }),
                    '127.0.0.1'
                ))
                conn.commit()
            except Exception as e:
                print(f"[ERRO] Falha ao registrar alerta: {e}")
            finally:
                conn.close()
    
    def analyze_log(self, log_entry):
        """Analisa um registro de log em busca de ataques"""
        try:
            data = json.loads(log_entry)
            endpoint = data.get('endpoint', '')
            payload = data.get('payload', '')
            ip_address = data.get('ip_address', '')
            user_agent = data.get('user_agent', '')
            
            # Verificar cada tipo de ataque
            if self.detect_sql_injection(payload):
                self.log_attack('sql_injection', endpoint, payload, ip_address, user_agent, True)
                return {'blocked': True, 'type': 'sql_injection'}
            
            if self.detect_xss(payload):
                self.log_attack('xss', endpoint, payload, ip_address, user_agent, True)
                return {'blocked': True, 'type': 'xss'}
            
            if self.detect_path_traversal(payload):
                self.log_attack('path_traversal', endpoint, payload, ip_address, user_agent, True)
                return {'blocked': True, 'type': 'path_traversal'}
            
            return {'blocked': False, 'type': None}
            
        except Exception as e:
            print(f"[ERRO] Falha na análise: {e}")
            return {'blocked': False, 'type': None}
    
    def get_statistics(self):
        """Retorna estatísticas de segurança"""
        conn = self.connect_db()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # Total de ataques
            cursor.execute("SELECT COUNT(*) FROM attack_log")
            total_attacks = cursor.fetchone()[0]
            
            # Ataques bloqueados
            cursor.execute("SELECT COUNT(*) FROM attack_log WHERE blocked = TRUE")
            blocked_attacks = cursor.fetchone()[0]
            
            # Ataques por tipo
            cursor.execute("""
                SELECT attack_type, COUNT(*) 
                FROM attack_log 
                GROUP BY attack_type
            """)
            by_type = dict(cursor.fetchall())
            
            # Último ataque
            cursor.execute("""
                SELECT attack_type, timestamp 
                FROM attack_log 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            last_attack = cursor.fetchone()
            
            return {
                'total_attacks': total_attacks,
                'blocked_attacks': blocked_attacks,
                'success_rate': (blocked_attacks / total_attacks * 100) if total_attacks > 0 else 0,
                'by_type': by_type,
                'last_attack': {
                    'type': last_attack[0] if last_attack else None,
                    'timestamp': last_attack[1].isoformat() if last_attack else None
                }
            }
        except Exception as e:
            print(f"[ERRO] Falha ao obter estatísticas: {e}")
            return None
        finally:
            conn.close()
    
    def generate_report(self):
        """Gera relatório de segurança"""
        stats = self.get_statistics()
        if not stats:
            return "Falha ao gerar relatório"
        
        report = f"""
{'='*60}
RELATÓRIO DE SEGURANÇA - SANDBOX RAVENA
Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

RESUMO:
- Total de tentativas de ataque: {stats['total_attacks']}
- Ataques bloqueados: {stats['blocked_attacks']}
- Taxa de bloqueio: {stats['success_rate']:.2f}%

ATAQUES POR TIPO:
"""
        for attack_type, count in stats['by_type'].items():
            report += f"- {attack_type}: {count}\n"
        
        if stats['last_attack']['type']:
            report += f"""
ÚLTIMO ATAQUE:
- Tipo: {stats['last_attack']['type']}
- Data/Hora: {stats['last_attack']['timestamp']}
"""
        
        report += f"""
{'='*60}
FIM DO RELATÓRIO
{'='*60}
"""
        
        return report
    
    def monitor_loop(self):
        """Loop principal de monitoramento"""
        print(f"[INFO] Monitor de segurança iniciado em {datetime.now()}")
        print(f"[INFO] Thresholds: {self.alert_thresholds}")
        
        self.running = True
        
        while self.running:
            try:
                # Verificar estatísticas a cada 30 segundos
                stats = self.get_statistics()
                if stats:
                    print(f"[STATS] Total: {stats['total_attacks']} | "
                          f"Bloqueados: {stats['blocked_attacks']} | "
                          f"Taxa: {stats['success_rate']:.1f}%")
                
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n[INFO] Monitor interrompido pelo usuário")
                self.running = False
            except Exception as e:
                print(f"[ERRO] Erro no loop: {e}")
                time.sleep(5)
    
    def start(self):
        """Inicia o monitor"""
        print("Iniciando monitor de segurança...")
        self.monitor_loop()


if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.start()
