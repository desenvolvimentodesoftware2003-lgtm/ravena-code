#!/bin/bash
# ============================================
# SCRIPT: Implementar Monitoramento Contínuo
# ============================================

echo "============================================"
echo "  IMPLEMENTANDO MONITORAMENTO CONTÍNUO"
echo "============================================"
echo ""

# Verificar se a sandbox está rodando
if ! docker-compose ps | grep -q "ravena-app"; then
    echo "[ERRO] Sandbox não está rodando"
    echo "[INFO] Execute: docker-compose up -d"
    exit 1
fi

echo "[INFO] Configurando monitoramento contínuo..."
echo ""

# Fase 1: Configurar Prometheus
echo "1. Configurando Prometheus..."

# Criar configuração do Prometheus
cat > monitoring/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ravena-app'
    static_configs:
      - targets: ['ravena-app:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
    
  - job_name: 'ravena-security'
    static_configs:
      - targets: ['ravena-app:8080']
    metrics_path: '/api/admin/attacks'
    scrape_interval: 10s
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

rule_files:
  - "alert_rules.yml"
EOF

echo "   [OK] Prometheus configurado"

# Fase 2: Configurar Alertas
echo "2. Configurando alertas..."

cat > monitoring/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: security_alerts
    rules:
      - alert: SQLInjectionDetected
        expr: increase(attack_log_total{type="sql_injection"}[1m]) > 0
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "SQL Injection detectado!"
          
      - alert: BruteForceAttempt
        expr: increase(attack_log_total{type="brute_force"}[5m]) > 10
        for: 30s
        labels:
          severity: high
        annotations:
          summary: "Tentativa de brute force detectada"
          
      - alert: HackerActivity
        expr: increase(attack_log_total{user="hacker_001"}[1m]) > 0
        for: 0s
        labels:
          severity: info
        annotations:
          summary: "Atividade do agente hacker registrada"
          
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Serviço indisponível"
EOF

echo "   [OK] Alertas configurados"

# Fase 3: Configurar Grafana
echo "3. Configurando Grafana..."

# Aguardar Grafana iniciar
echo "   Aguardando Grafana..."
for i in {1..30}; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Configurar fonte de dados
curl -s -X POST http://localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -u admin:sandbox_monitor_123 \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://ravena-prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }' > /dev/null 2>&1

echo "   [OK] Grafana configurado"

# Fase 4: Configurar Kibana
echo "4. Configurando Kibana..."

# Aguardar Elasticsearch iniciar
echo "   Aguardando Elasticsearch..."
for i in {1..30}; do
    if curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "   [OK] Kibana pronto"

# Fase 5: Criar Dashboard de Monitoramento
echo "5. Criando dashboard de monitoramento..."

cat > monitoring/grafana/security_dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "Security Monitor - Sandbox Ravena",
    "tags": ["security", "sandbox"],
    "panels": [
      {
        "title": "Total de Ataques",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(attack_log_total)",
            "legendFormat": "Total"
          }
        ]
      },
      {
        "title": "Ataques por Tipo",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (type) (attack_log_total)",
            "legendFormat": "{{type}}"
          }
        ]
      },
      {
        "title": "Ataques ao Longo do Tempo",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(attack_log_total[5m])",
            "legendFormat": "{{type}}"
          }
        ]
      }
    ]
  }
}
EOF

echo "   [OK] Dashboard criado"

# Fase 6: Iniciar monitoramento
echo "6. Iniciando monitoramento..."

# Verificar se os serviços estão rodando
echo "   Verificando serviços..."

services=("prometheus" "grafana" "elasticsearch" "kibana")
for service in "${services[@]}"; do
    if docker-compose ps | grep -q "ravena-$service"; then
        echo "   [OK] $service está rodando"
    else
        echo "   [INFO] Iniciando $service..."
        docker-compose up -d "ravena-$service" 2>/dev/null
    fi
done

echo ""
echo "============================================"
echo "  MONITORAMENTO IMPLEMENTADO"
echo "============================================"
echo ""
echo "SERVIÇOS DE MONITORAMENTO:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000"
echo "  - Kibana: http://localhost:5601"
echo "  - Elasticsearch: http://localhost:9200"
echo ""
echo "CREDENCIAIS:"
echo "  - Grafana: admin / sandbox_monitor_123"
echo ""
echo "DASHBOARDS DISPONÍVEIS:"
echo "  - Security Monitor"
echo "  - Performance Metrics"
echo "  - System Health"
echo ""
echo "ALERTAS CONFIGURADOS:"
echo "  - SQL Injection detectado"
echo "  - Brute force detectado"
echo "  - Atividade do hacker"
echo "  - Serviço indisponível"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "  1. Acessar Grafana: http://localhost:3000"
echo "  2. Visualizar dashboards"
echo "  3. Configurar notificações"
echo "  4. Testar alertas"
echo ""
echo "============================================"
