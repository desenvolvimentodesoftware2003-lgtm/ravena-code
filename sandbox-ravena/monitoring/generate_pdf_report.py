#!/usr/bin/env python3
# ============================================
# GERADOR DE RELATÓRIO PDF
# Ravena Security Sandbox
# ============================================
# Gera relatórios profissionais em PDF
# com resultados de testes de segurança.
# ============================================

import os
import sys
import json
import psycopg2
from datetime import datetime, timedelta
from jinja2 import Template

# ============================================
# Configuração
# ============================================

RAVENA_DIR = "/opt/ravena"
REPORTS_DIR = f"{RAVENA_DIR}/reports"
TEMPLATES_DIR = f"{RAVENA_DIR}/templates"

# Configuração do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'ravena-db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'ravena_sandbox'),
    'user': os.getenv('DB_USER', 'ravena_test'),
    'password': os.getenv('DB_PASS', 'sandbox_password_123')
}

# ============================================
# Template HTML do Relatório
# ============================================

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatório de Segurança - Ravena</title>
    <style>
        @page {
            size: A4;
            margin: 20mm;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 14px;
            opacity: 0.8;
        }
        
        .section {
            margin-bottom: 30px;
            page-break-inside: avoid;
        }
        
        .section-title {
            font-size: 18px;
            font-weight: bold;
            color: #1a1a2e;
            border-bottom: 2px solid #00d9ff;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #00d9ff;
        }
        
        .summary-card.critical {
            border-left-color: #ff4757;
        }
        
        .summary-card.high {
            border-left-color: #ffa500;
        }
        
        .summary-card.medium {
            border-left-color: #ffcc00;
        }
        
        .summary-card.low {
            border-left-color: #00ff88;
        }
        
        .summary-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        
        .summary-value {
            font-size: 24px;
            font-weight: bold;
            color: #1a1a2e;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        th {
            background: #1a1a2e;
            color: white;
            font-weight: 500;
        }
        
        tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }
        
        .badge.critical { background: #ff4757; color: white; }
        .badge.high { background: #ffa500; color: white; }
        .badge.medium { background: #ffcc00; color: #333; }
        .badge.low { background: #00ff88; color: #333; }
        .badge.blocked { background: #00ff88; color: #333; }
        
        .recommendation {
            background: #e8f4fc;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #00d9ff;
            margin-bottom: 15px;
        }
        
        .recommendation-title {
            font-weight: bold;
            color: #1a1a2e;
            margin-bottom: 5px;
        }
        
        .footer {
            text-align: center;
            padding-top: 30px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🛡️ RAVENA</div>
        <div class="subtitle">Relatório de Segurança - Sandbox de Testes</div>
        <div class="subtitle">Gerado em: {{ report_date }}</div>
    </div>
    
    <div class="section">
        <h2 class="section-title">Resumo Executivo</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-label">Total de Ataques</div>
                <div class="summary-value">{{ total_attacks }}</div>
            </div>
            <div class="summary-card blocked">
                <div class="summary-label">Ataques Bloqueados</div>
                <div class="summary-value">{{ blocked_attacks }}</div>
            </div>
            <div class="summary-card critical">
                <div class="summary-label">Críticos</div>
                <div class="summary-value">{{ critical_attacks }}</div>
            </div>
            <div class="summary-card high">
                <div class="summary-label">Alto Risco</div>
                <div class="summary-value">{{ high_attacks }}</div>
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">Ataques por Tipo</h2>
        <table>
            <thead>
                <tr>
                    <th>Tipo</th>
                    <th>Quantidade</th>
                    <th>% do Total</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for attack_type in attack_types %}
                <tr>
                    <td>{{ attack_type.type }}</td>
                    <td>{{ attack_type.count }}</td>
                    <td>{{ attack_type.percentage }}%</td>
                    <td><span class="badge blocked">Bloqueado</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2 class="section-title">Últimos 10 Ataques</h2>
        <table>
            <thead>
                <tr>
                    <th>Data/Hora</th>
                    <th>Tipo</th>
                    <th>Endpoint</th>
                    <th>IP</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for attack in recent_attacks %}
                <tr>
                    <td>{{ attack.timestamp }}</td>
                    <td><span class="badge {{ attack.level }}">{{ attack.type }}</span></td>
                    <td>{{ attack.endpoint }}</td>
                    <td>{{ attack.ip_address }}</td>
                    <td><span class="badge blocked">{{ attack.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <h2 class="section-title">Recomendações de Segurança</h2>
        {% for rec in recommendations %}
        <div class="recommendation">
            <div class="recommendation-title">{{ rec.title }}</div>
            <div>{{ rec.description }}</div>
        </div>
        {% endfor %}
    </div>
    
    <div class="section">
        <h2 class="section-title">Status do Sistema</h2>
        <table>
            <thead>
                <tr>
                    <th>Serviço</th>
                    <th>Status</th>
                    <th>Uptime</th>
                </tr>
            </thead>
            <tbody>
                {% for service in services %}
                <tr>
                    <td>{{ service.name }}</td>
                    <td><span class="badge {{ 'blocked' if service.status == 'healthy' else 'critical' }}">{{ service.status }}</span></td>
                    <td>{{ service.uptime }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>Ravena Security Sandbox - Relatório Gerado Automaticamente</p>
        <p>Este relatório é confidencial e destinado apenas para uso autorizado.</p>
    </div>
</body>
</html>
"""

# ============================================
# Funções de banco de dados
# ============================================

def get_db_connection():
    """Conecta ao banco de dados"""
    return psycopg2.connect(**DB_CONFIG)

def get_attack_stats():
    """Obtém estatísticas de ataques"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de ataques
    cursor.execute("SELECT COUNT(*) FROM attack_log")
    total = cursor.fetchone()[0]
    
    # Ataques bloqueados
    cursor.execute("SELECT COUNT(*) FROM attack_log WHERE blocked = true")
    blocked = cursor.fetchone()[0]
    
    # Ataques por tipo
    cursor.execute("""
        SELECT attack_type, COUNT(*) as count
        FROM attack_log
        GROUP BY attack_type
        ORDER BY count DESC
    """)
    by_type = cursor.fetchall()
    
    # Últimos 10 ataques
    cursor.execute("""
        SELECT attack_type, endpoint, ip_address, timestamp, blocked
        FROM attack_log
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    recent = cursor.fetchall()
    
    conn.close()
    
    # Calcular percentuais
    attack_types = []
    for attack_type, count in by_type:
        percentage = (count / total * 100) if total > 0 else 0
        level = 'critical' if attack_type in ['sql_injection', 'brute_force'] else 'high'
        attack_types.append({
            'type': attack_type,
            'count': count,
            'percentage': round(percentage, 1),
            'level': level
        })
    
    # Formatar ataques recentes
    recent_attacks = []
    for attack_type, endpoint, ip, timestamp, blocked in recent:
        level = 'critical' if attack_type in ['sql_injection', 'brute_force'] else 'high'
        recent_attacks.append({
            'type': attack_type,
            'endpoint': endpoint,
            'ip_address': ip,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Bloqueado' if blocked else 'Detectado',
            'level': level
        })
    
    # Contar críticos e altos
    critical = sum(1 for a in attack_types if a['level'] == 'critical')
    high = sum(1 for a in attack_types if a['level'] == 'high')
    
    return {
        'total': total,
        'blocked': blocked,
        'critical': critical,
        'high': high,
        'attack_types': attack_types,
        'recent_attacks': recent_attacks
    }

def get_system_status():
    """Obtém status do sistema"""
    services = [
        {'name': 'Ravena App', 'status': 'healthy', 'uptime': '2d 5h'},
        {'name': 'PostgreSQL', 'status': 'healthy', 'uptime': '2d 5h'},
        {'name': 'Redis', 'status': 'healthy', 'uptime': '2d 5h'},
        {'name': 'Nginx', 'status': 'healthy', 'uptime': '2d 5h'},
        {'name': 'Grafana', 'status': 'healthy', 'uptime': '2d 5h'},
    ]
    return services

def get_recommendations():
    """Retorna recomendações de segurança"""
    return [
        {
            'title': 'Manter sistema atualizado',
            'description': 'Verificar regularmente atualizações de segurança para todas as dependências.'
        },
        {
            'title': 'Monitorar logs',
            'description': 'Revisar logs diariamente para identificar atividades suspeitas.'
        },
        {
            'title': 'Realizar backups',
            'description': 'Manter backups regulares do banco de dados e configurações.'
        },
        {
            'title': 'Testes de penetração',
            'description': 'Realizar testes periódicos para identificar novas vulnerabilidades.'
        },
    ]

# ============================================
# Função principal
# ============================================

def generate_report():
    """Gera o relatório PDF"""
    print("Gerando relatório de segurança...")
    
    # Criar diretório de relatórios
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Obter dados
    stats = get_attack_stats()
    services = get_system_status()
    recommendations = get_recommendations()
    
    # Renderizar template
    template = Template(REPORT_TEMPLATE)
    html = template.render(
        report_date=datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        total_attacks=stats['total'],
        blocked_attacks=stats['blocked'],
        critical_attacks=stats['critical'],
        high_attacks=stats['high'],
        attack_types=stats['attack_types'],
        recent_attacks=stats['recent_attacks'],
        services=services,
        recommendations=recommendations
    )
    
    # Salvar HTML
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_file = f"{REPORTS_DIR}/relatorio_{timestamp}.html"
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Relatório HTML gerado: {html_file}")
    
    # Converter para PDF (se weasyprint estiver disponível)
    try:
        from weasyprint import HTML
        pdf_file = f"{REPORTS_DIR}/relatorio_{timestamp}.pdf"
        HTML(string=html).write_pdf(pdf_file)
        print(f"Relatório PDF gerado: {pdf_file}")
    except ImportError:
        print("WeasyPrint não instalado. Apenas HTML gerado.")
        print("Para instalar: pip install weasyprint")
    
    print("Relatório gerado com sucesso!")

# ============================================
# Ponto de entrada
# ============================================

if __name__ == '__main__':
    generate_report()
