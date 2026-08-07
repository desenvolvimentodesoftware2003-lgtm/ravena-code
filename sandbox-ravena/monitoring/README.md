# ============================================
# MONITORAMENTO - SANDBOX RAVENA
# ============================================

## Visão Geral

O sistema de monitoramento da Sandbox Ravena fornece visibilidade completa sobre:
- Tentativas de ataque em tempo real
- Performance da aplicação
- Uso de recursos
- Logs de auditoria

## Stack de Monitoramento

```
┌─────────────────────────────────────────────────────────────┐
│                    STACK DE MONITORAMENTO                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │  Prometheus  │────▶│   Grafana    │────▶│   Alertas    │ │
│  │  (Métricas)  │     │ (Dashboard)  │     │  (Notifica)  │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│         │                    │                    │         │
│         │              ┌─────┴─────┐              │         │
│         │              │ Alertmgr  │              │         │
│         │              │ (Alertas) │              │         │
│         │              └───────────┘              │         │
│         │                                         │         │
│  ┌──────┴──────┐                         ┌────────┴───────┐ │
│  │Elasticsearch│                         │     Kibana     │ │
│  │   (Logs)    │                         │ (Visualização) │ │
│  └─────────────┘                         └────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Serviços

### 1. Prometheus
- **Porta:** 9090
- **Função:** Coleta e armazenamento de métricas
- **Acesso:** http://localhost:9090

### 2. Grafana
- **Porta:** 3000
- **Função:** Visualização de métricas e dashboards
- **Acesso:** http://localhost:3000
- **Credenciais:** admin / sandbox_monitor_123

### 3. Elasticsearch
- **Porta:** 9200
- **Função:** Armazenamento e indexação de logs
- **Acesso:** http://localhost:9200

### 4. Kibana
- **Porta:** 5601
- **Função:** Visualização e análise de logs
- **Acesso:** http://localhost:5601

### 5. Alertmanager
- **Porta:** 9093
- **Função:** Gerenciamento e notificação de alertas
- **Acesso:** http://localhost:9093

## Métricas Coletadas

### Métricas de Segurança
- `attack_log_total` - Total de tentativas de ataque
- `attack_log_blocked` - Ataques bloqueados
- `attack_log_success` - Ataques bem-sucedidos

### Métricas de Performance
- `http_requests_total` - Total de requisições HTTP
- `http_request_duration_seconds` - Duração das requisições
- `http_requests_in_flight` - Requisições em andamento

### Métricas de Sistema
- `node_cpu_seconds_total` - Uso de CPU
- `node_memory_MemTotal_bytes` - Memória total
- `node_filesystem_avail_bytes` - Espaço em disco

## Dashboards

### Dashboard Principal
O dashboard principal inclui:
- Total de ataques
- Ataques bloqueados
- Taxa de bloqueio (%)
- Ataques por tipo
- Ataques ao longo do tempo
- Últimas tentativas de ataque

### Dashboard de Performance
- Requisições por segundo
- Tempo de resposta médio
- Taxa de erro
- Conexões ativas

### Dashboard de Sistema
- Uso de CPU
- Uso de memória
- Uso de disco
- Tráfego de rede

## Alertas

### Alertas Críticos
- **HighAttackRate:** Taxa alta de ataques (>10/s)
- **SQLInjectionDetected:** SQL Injection detectado
- **ServiceDown:** Serviço indisponível

### Alertas de Alto Nível
- **BruteForceDetected:** Brute force detectado
- **HighCPUUsage:** Uso de CPU alto (>80%)
- **HighMemoryUsage:** Uso de memória alto (>80%)

### Alertas de Médio Nível
- **InvalidSession:** Tentativas de sequestro de sessão
- **DiskSpaceLow:** Espaço em disco baixo (<20%)

## Configuração

### Prometheus
Arquivo: `monitoring/prometheus/prometheus.yml`

### Alert Rules
Arquivo: `monitoring/prometheus/alert_rules.yml`

### Alertmanager
Arquivo: `monitoring/alertmanager/alertmanager.yml`

### Elasticsearch
Arquivo: `monitoring/elasticsearch/index_patterns.json`

### Grafana
Arquivo: `monitoring/grafana/dashboard.json`

## Comandos Úteis

### Ver métricas no Prometheus
```bash
# Total de ataques
attack_log_total

# Ataques bloqueados
attack_log_blocked

# Taxa de bloqueio
attack_log_blocked / attack_log_total * 100
```

### Ver logs no Kibana
```bash
# Ataques nas últimas 24 horas
attack_log.timestamp >= now-24h

# Apenas SQL Injection
attack_log.attack_type: "sql_injection"

# Ataques bloqueados
attack_log.blocked: true
```

### Ver alertas
```bash
# Alertas ativos
http://localhost:9093/#/alerts

# Regras de alerta
http://localhost:9090/alerts
```

## Troubleshooting

### Prometheus não coleta métricas
1. Verificar se os targets estão UP: http://localhost:9090/targets
2. Verificar logs do Prometheus: `docker-compose logs prometheus`

### Grafana não mostra dados
1. Verificar se a fonte de dados está configurada
2. Verificar se o Prometheus está respondendo
3. Verificar logs do Grafana: `docker-compose logs grafana`

### Elasticsearch não indexa logs
1. Verificar se o Elasticsearch está rodando: `curl http://localhost:9200`
2. Verificar se os index patterns estão criados
3. Verificar logs do Elasticsearch: `docker-compose logs elasticsearch`

## Referências

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/)
