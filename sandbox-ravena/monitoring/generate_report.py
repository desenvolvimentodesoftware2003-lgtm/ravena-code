#!/usr/bin/env python3
"""
Gerador de Relatórios - Sandbox Ravena
Gera relatórios detalhados dos testes de segurança
"""

import psycopg2
import json
from datetime import datetime
from jinja2 import Template

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
# TEMPLATE DO RELATÓRIO
# ============================================

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Segurança - Sandbox Ravena</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header .subtitle {
            opacity: 0.9;
            margin-top: 10px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-box .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-box .label {
            color: #666;
            margin-top: 5px;
        }
        .stat-box.critical .number { color: #dc3545; }
        .stat-box.warning .number { color: #ffc107; }
        .stat-box.success .number { color: #28a745; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #667eea;
            color: white;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
        }
        .badge-critical { background: #dc3545; color: white; }
        .badge-high { background: #ffc107; color: #333; }
        .badge-medium { background: #17a2b8; color: white; }
        .badge-low { background: #28a745; color: white; }
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.5s ease;
        }
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
        }
        .alert-danger {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffeeba;
            color: #856404;
        }
        .alert-success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Relatório de Segurança</h1>
        <div class="subtitle">Sandbox Ravena - Módulo de Jogos/Slots</div>
        <div class="subtitle">Gerado em: {{ report_date }}</div>
    </div>

    <div class="card">
        <h2>📊 Resumo Executivo</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="number">{{ total_attacks }}</div>
                <div class="label">Total de Ataques</div>
            </div>
            <div class="stat-box success">
                <div class="number">{{ blocked_attacks }}</div>
                <div class="label">Bloqueados</div>
            </div>
            <div class="stat-box critical">
                <div class="number">{{ successful_attacks }}</div>
                <div class="label">Bem-sucedidos</div>
            </div>
            <div class="stat-box {{ 'success' if success_rate >= 90 else 'warning' if success_rate >= 70 else 'critical' }}">
                <div class="number">{{ "%.1f"|format(success_rate) }}%</div>
                <div class="label">Taxa de Bloqueio</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ success_rate }}%"></div>
        </div>
        
        {% if success_rate < 70 %}
        <div class="alert alert-danger">
            <strong>⚠️ ALERTA CRÍTICO:</strong> A taxa de bloqueio está abaixo de 70%. 
            Ações imediatas são necessárias para melhorar a segurança do sistema.
        </div>
        {% elif success_rate < 90 %}
        <div class="alert alert-warning">
            <strong>⚡ ATENÇÃO:</strong> A taxa de bloqueio está entre 70-90%. 
            Recomenda-se implementar melhorias adicionais.
        </div>
        {% else %}
        <div class="alert alert-success">
            <strong>✅ BOM:</strong> A taxa de bloqueio está acima de 90%. 
            O sistema está respondendo adequadamente aos ataques.
        </div>
        {% endif %}
    </div>

    <div class="card">
        <h2>🎯 Ataques por Tipo</h2>
        <table>
            <thead>
                <tr>
                    <th>Tipo de Ataque</th>
                    <th>Total</th>
                    <th>Bloqueados</th>
                    <th>Bem-sucedidos</th>
                    <th>Severidade</th>
                </tr>
            </thead>
            <tbody>
                {% for attack in attacks_by_type %}
                <tr>
                    <td>{{ attack.type }}</td>
                    <td>{{ attack.total }}</td>
                    <td>{{ attack.blocked }}</td>
                    <td>{{ attack.total - attack.blocked }}</td>
                    <td>
                        <span class="badge badge-{{ attack.severity }}">
                            {{ attack.severity|upper }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>📝 Últimas Tentativas de Ataque</h2>
        <table>
            <thead>
                <tr>
                    <th>Data/Hora</th>
                    <th>Tipo</th>
                    <th>Endpoint</th>
                    <th>Status</th>
                    <th>IP</th>
                </tr>
            </thead>
            <tbody>
                {% for log in recent_attacks %}
                <tr>
                    <td>{{ log.timestamp }}</td>
                    <td>{{ log.attack_type }}</td>
                    <td>{{ log.endpoint }}</td>
                    <td>
                        <span class="badge badge-{{ 'success' if log.blocked else 'critical' }}">
                            {{ 'BLOQUEADO' if log.blocked else 'BEM-SUCEDIDO' }}
                        </span>
                    </td>
                    <td>{{ log.ip_address }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>🔐 Status de Segurança</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="number">{{ total_users }}</div>
                <div class="label">Usuários de Teste</div>
            </div>
            <div class="stat-box">
                <div class="number">{{ total_transactions }}</div>
                <div class="label">Transações</div>
            </div>
            <div class="stat-box">
                <div class="number">{{ active_sessions }}</div>
                <div class="label">Sessões Ativas</div>
            </div>
            <div class="stat-box">
                <div class="number">{{ total_logs }}</div>
                <div class="label">Logs de Auditoria</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>📋 Recomendações</h2>
        <div class="alert alert-warning">
            <h3>Corretivas Imediatas (0-24h)</h3>
            <ul>
                <li>Implementar Prepared Statements em todas as queries</li>
                <li>Adicionar validação rigorosa de entrada</li>
                <li>Configurar WAF com regras anti-SQLi</li>
                <li>Implementar rate limiting rigoroso</li>
            </ul>
        </div>
        
        <div class="alert alert-warning">
            <h3>Preventivas (1-7 dias)</h3>
            <ul>
                <li>Implementar criptografia de dados sensíveis</li>
                <li>Configurar backup automatizado</li>
                <li>Implementar alertas em tempo real</li>
                <li>Revisar permissões de banco de dados</li>
            </ul>
        </div>
        
        <div class="alert alert-success">
            <h3>Detecção (7-30 dias)</h3>
            <ul>
                <li>Integrar SIEM com logs</li>
                <li>Implementar monitoramento de comportamento</li>
                <li>Configurar auditoria periódica</li>
                <li>Criar programa de bug bounty</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <p>Relatório gerado automaticamente pela Sandbox Ravena</p>
        <p>⚠️ Este relatório é confidencial e deve ser tratado de acordo</p>
    </div>
</body>
</html>
"""

# ============================================
# FUNÇÕES
# ============================================

def get_db_connection():
    """Obtém conexão com o banco"""
    return psycopg2.connect(**DB_CONFIG)

def get_statistics():
    """Obtém estatísticas do banco"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total de ataques
    cursor.execute("SELECT COUNT(*) FROM attack_log")
    stats['total_attacks'] = cursor.fetchone()[0]
    
    # Ataques bloqueados
    cursor.execute("SELECT COUNT(*) FROM attack_log WHERE blocked = TRUE")
    stats['blocked_attacks'] = cursor.fetchone()[0]
    
    # Ataques bem-sucedidos
    stats['successful_attacks'] = stats['total_attacks'] - stats['blocked_attacks']
    
    # Taxa de bloqueio
    stats['success_rate'] = (stats['blocked_attacks'] / stats['total_attacks'] * 100) if stats['total_attacks'] > 0 else 0
    
    # Ataques por tipo
    cursor.execute("""
        SELECT attack_type, 
               COUNT(*) as total,
               SUM(CASE WHEN blocked THEN 1 ELSE 0 END) as blocked
        FROM attack_log
        GROUP BY attack_type
    """)
    
    attacks_by_type = []
    for row in cursor.fetchall():
        attack_type = row[0]
        total = row[1]
        blocked = row[2]
        
        # Determinar severidade
        if attack_type in ['sql_injection', 'remote_code_execution']:
            severity = 'critical'
        elif attack_type in ['brute_force', 'session_hijack']:
            severity = 'high'
        elif attack_type in ['xss', 'idor']:
            severity = 'medium'
        else:
            severity = 'low'
        
        attacks_by_type.append({
            'type': attack_type,
            'total': total,
            'blocked': blocked,
            'severity': severity
        })
    
    stats['attacks_by_type'] = attacks_by_type
    
    # Últimos ataques
    cursor.execute("""
        SELECT attack_type, endpoint, blocked, ip_address, timestamp
        FROM attack_log
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    stats['recent_attacks'] = [
        {
            'attack_type': row[0],
            'endpoint': row[1],
            'blocked': row[2],
            'ip_address': str(row[3]) if row[3] else 'N/A',
            'timestamp': row[4].strftime('%Y-%m-%d %H:%M:%S') if row[4] else 'N/A'
        }
        for row in cursor.fetchall()
    ]
    
    # Outras estatísticas
    cursor.execute("SELECT COUNT(*) FROM users")
    stats['total_users'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM transactions")
    stats['total_transactions'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > NOW()")
    stats['active_sessions'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM audit_log")
    stats['total_logs'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def generate_html_report(stats):
    """Gera relatório HTML"""
    template = Template(REPORT_TEMPLATE)
    
    html = template.render(
        report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **stats
    )
    
    return html

def save_report(html, filename):
    """Salva relatório em arquivo"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[OK] Relatório salvo em: {filename}")

# ============================================
# EXECUÇÃO PRINCIPAL
# ============================================

def main():
    """Função principal"""
    print("="*60)
    print("GERADOR DE RELATÓRIOS - SANDBOX RAVENA")
    print("="*60)
    
    try:
        # Obter estatísticas
        print("[INFO] Obtendo estatísticas do banco...")
        stats = get_statistics()
        
        # Gerar HTML
        print("[INFO] Gerando relatório HTML...")
        html = generate_html_report(stats)
        
        # Salvar arquivo
        filename = f"relatorio_seguranca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        save_report(html, filename)
        
        print("[OK] Relatório gerado com sucesso!")
        print(f"[INFO] Abra o arquivo {filename} no navegador")
        
    except Exception as e:
        print(f"[ERRO] Falha ao gerar relatório: {e}")
        raise

if __name__ == "__main__":
    main()
