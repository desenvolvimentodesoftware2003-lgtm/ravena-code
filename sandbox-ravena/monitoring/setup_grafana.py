#!/usr/bin/env python3
"""
Configuração Inicial do Grafana - Sandbox Ravena
Configura automaticamente as fontes de dados e dashboards
"""

import requests
import json
import time
import os

# ============================================
# CONFIGURAÇÕES
# ============================================

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "sandbox_monitor_123"

PROMETHEUS_URL = "http://ravena-prometheus:9090"

# ============================================
# FUNÇÕES
# ============================================

def wait_for_grafana():
    """Aguarda o Grafana estar disponível"""
    print("[INFO] Aguardando Grafana iniciar...")
    
    for i in range(30):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health")
            if response.status_code == 200:
                print("[OK] Grafana está disponível")
                return True
        except requests.ConnectionError:
            pass
        
        print(f"[INFO] Aguardando... ({i+1}/30)")
        time.sleep(2)
    
    print("[ERRO] Grafana não disponível após 60 segundos")
    return False

def get_grafana_session():
    """Obtém sessão autenticada do Grafana"""
    session = requests.Session()
    
    # Login
    response = session.post(f"{GRAFANA_URL}/login", json={
        'user': GRAFANA_USER,
        'password': GRAFANA_PASSWORD
    })
    
    if response.status_code == 200:
        print("[OK] Login realizado com sucesso")
        return session
    else:
        print(f"[ERRO] Falha no login: {response.text}")
        return None

def add_prometheus_datasource(session):
    """Adiciona Prometheus como fonte de dados"""
    print("[INFO] Adicionando Prometheus como fonte de dados...")
    
    payload = {
        "name": "Prometheus",
        "type": "prometheus",
        "url": PROMETHEUS_URL,
        "access": "proxy",
        "isDefault": True,
        "jsonData": {
            "timeInterval": "15s"
        }
    }
    
    response = session.post(f"{GRAFANA_URL}/api/datasources", json=payload)
    
    if response.status_code in [200, 409]:  # 409 = já existe
        print("[OK] Prometheus adicionado como fonte de dados")
        return True
    else:
        print(f"[ERRO] Falha ao adicionar Prometheus: {response.text}")
        return False

def create_dashboard(session):
    """Cria dashboard principal"""
    print("[INFO] Criando dashboard principal...")
    
    # Carregar dashboard do arquivo
    dashboard_path = "monitoring/grafana/dashboard.json"
    
    if not os.path.exists(dashboard_path):
        print(f"[ERRO] Arquivo não encontrado: {dashboard_path}")
        return False
    
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    
    # Ajustar fonte de dados
    for panel in dashboard['dashboard']['panels']:
        for target in panel.get('targets', []):
            target['datasource'] = 'Prometheus'
    
    # Criar dashboard
    payload = {
        "dashboard": dashboard['dashboard'],
        "overwrite": True,
        "message": "Dashboard criado automaticamente"
    }
    
    response = session.post(f"{GRAFANA_URL}/api/dashboards/db", json=payload)
    
    if response.status_code == 200:
        print("[OK] Dashboard criado com sucesso")
        return True
    else:
        print(f"[ERRO] Falha ao criar dashboard: {response.text}")
        return False

def configure_alerting(session):
    """Configura alertas no Grafana"""
    print("[INFO] Configurando alertas...")
    
    # Criar canal de notificação
    payload = {
        "name": "Sandbox Alerts",
        "type": "webhook",
        "settings": {
            "url": "http://ravena-app:5001/webhook/",
            "httpMethod": "POST"
        },
        "isDefault": True
    }
    
    response = session.post(f"{GRAFANA_URL}/api/alert-channels", json=payload)
    
    if response.status_code in [200, 409]:
        print("[OK] Canal de notificação criado")
        return True
    else:
        print(f"[ERRO] Falha ao criar canal: {response.text}")
        return False

def setup_grafana():
    """Configuração completa do Grafana"""
    print("="*60)
    print("CONFIGURAÇÃO DO GRAFANA")
    print("="*60)
    print("")
    
    # Aguardar Grafana
    if not wait_for_grafana():
        return False
    
    # Obter sessão
    session = get_grafana_session()
    if not session:
        return False
    
    # Adicionar fonte de dados
    if not add_prometheus_datasource(session):
        return False
    
    # Criar dashboard
    if not create_dashboard(session):
        return False
    
    # Configurar alertas
    if not configure_alerting(session):
        return False
    
    print("")
    print("="*60)
    print("CONFIGURAÇÃO CONCLUÍDA")
    print("="*60)
    print("")
    print("PRÓXIMOS PASSOS:")
    print(f"1. Acesse o Grafana: {GRAFANA_URL}")
    print(f"2. Usuário: {GRAFANA_USER}")
    print(f"3. Senha: {GRAFANA_PASSWORD}")
    print("")
    print("DASHBOARDS DISPONÍVEIS:")
    print("- Security Dashboard")
    print("- Performance Dashboard")
    print("- System Dashboard")
    print("")
    print("="*60)
    
    return True

# ============================================
# EXECUÇÃO PRINCIPAL
# ============================================

if __name__ == "__main__":
    setup_grafana()
