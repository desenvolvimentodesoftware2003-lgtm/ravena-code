# ============================================
# CONTROLES DE ACESSO - SANDBOX RAVENA
# ============================================

## Visão Geral

Este documento define os controles de acesso, monitoramento, auditoria e isolamento da Sandbox Ravena, incluindo o agente **hacker**.

---

## 1. AGENTES AUTORIZADOS

### 1.1 Lista de Agentes e Permissões

| Agente | Tipo | Nível de Acesso | Serviços | Status |
|--------|------|------------------|----------|--------|
| **admin** | Administrador | Total | Todos | ATIVO |
| **pentester** | Testador | Total (testes) | App, DB, API | ATIVO |
| **security_engineer** | Engenheiro | Total (config) | Infra, Docker | ATIVO |
| **devops** | Operações | Total (infra) | Docker, Deploy | ATIVO |
| **security_analyst** | Analista | Leitura + Monitoramento | Grafana, Kibana | ATIVO |
| **soc** | Operações 24/7 | Leitura + Alertas | Grafana, SIEM | ATIVO |
| **ciso** | Gestão | Relatórios | Grafana (dash) | ATIVO |
| **hacker** | Penetration Tester | Total (testes controlados) | Todos (sandbox) | ATIVO |

---

## 2. PERFIL DO AGENTE HACKER

### 2.1 Definição do Perfil

```yaml
agente:
  nome: "hacker"
  tipo: "Penetration Tester"
  descricao: "Agente autorizado para testes de penetração na sandbox"
  status: "ATIVO"
  
acesso:
  tipo: "ferramentas_so"  # Usa ferramentas normais de sistema operacional
  nivel: "TOTAL"
  escopo: "sandbox_isolada"
  ferramentas:
    - nmap
    - curl
    - python3
    - sqlmap
    - nikto
    - netcat
  
servicos_autorizados:
  - ravena-app:8080
  - postgresql:5432
  - redis:6379
  - nginx:80
  - grafana:3000
  - kibana:5601
  
restricoes:
  - Nao pode acessar ambiente de producao
  - Nao pode modificar configuracoes de seguranca
  - Nao pode desabilitar logs
  - Todas as acoes sao auditadas
  - Relatorio obrigatorio apos testes
  
localizacao_laboratorio:
  diretorio: "~/hacker-lab"
  scripts:
    - 01_port_scan.sh
    - 02_sql_injection.sh
    - 03_xss_test.sh
    - 04_brute_force.sh
    - 05_idor_test.sh
    - 06_path_traversal.sh
    - 07_response_analysis.sh
    - 08_generate_report.sh
```

### 2.2 Acesso do Agente Hacker (FERRAMENTAS DE SO)

O agente hacker utiliza **ferramentas normais de sistema operacional** para executar testes de penetração, simulando um atacante real.

| Campo | Valor |
|-------|-------|
| **Laboratório** | `~/hacker-lab` |
| **Ferramentas** | nmap, curl, python3, sqlmap, nikto, netcat |
| **Autenticação** | Credenciais de teste (attacker_001/test123) |
| **Método** | Scripts shell e ferramentas CLI |

**Fluxo de Trabalho:**
```
1. Navegar: cd ~/hacker-lab
2. Reconhecimento: ./01_port_scan.sh
3. Enumeração: ./07_response_analysis.sh
4. Exploração: ./02_sql_injection.sh, ./03_xss_test.sh, etc.
5. Documentação: ./08_generate_report.sh
```

**Vantagens desta abordagem:**
- Simula um atacante real usando ferramentas reais
- Testa as defesas do sistema de verdade
- Não há "atalhos" ou funções especiais para o agente
- O agente deve descobrir vulnerabilidades como qualquer hacker

### 2.3 Habilidades do Agente Hacker

```
HABILIDADES AUTORIZADAS:
├── SQL Injection Testing
│   ├── UNION-based
│   ├── Blind SQLi
│   ├── Time-based
│   └── Error-based
├── XSS Testing
│   ├── Reflected XSS
│   ├── Stored XSS
│   └── DOM-based XSS
├── Authentication Testing
│   ├── Brute Force
│   ├── Session Management
│   └── Token Analysis
├── API Testing
│   ├── Endpoint Enumeration
│   ├── Parameter Tampering
│   └── IDOR Testing
└── Cryptography Testing
    ├── Weak Encryption
    ├── Key Management
    └── Hash Analysis
```

---

## 3. MONITORAMENTO CONTÍNUO

### 3.1 Definição

Monitoramento contínuo é o processo de coleta, análise e resposta a eventos de segurança em tempo real, 24/7.

### 3.2 Componentes Implementados

#### 3.2.1 Coleta de Métricas (Prometheus)

```yaml
# Configuração de coleta
scrape_configs:
  - job_name: 'ravena-security'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['ravena-app:8080']
    scrape_interval: 15s  # A cada 15 segundos
    
  - job_name: 'ravena-attacks'
    metrics_path: '/api/admin/attacks'
    static_configs:
      - targets: ['ravena-app:8080']
    scrape_interval: 5s  # A cada 5 segundos (mais frequente)
```

#### 3.2.2 Alertas em Tempo Real

```yaml
# Regras de alerta
groups:
  - name: security_alerts
    rules:
      # Alerta imediato para SQL Injection
      - alert: SQLInjectionDetected
        expr: increase(attack_log_total{type="sql_injection"}[1m]) > 0
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "SQL Injection detectado!"
          
      # Alerta para brute force
      - alert: BruteForceAttempt
        expr: increase(attack_log_total{type="brute_force"}[5m]) > 10
        for: 30s
        labels:
          severity: high
        annotations:
          summary: "Tentativa de brute force detectada"
          
      # Alerta para atividade do hacker
      - alert: HackerActivity
        expr: increase(attack_log_total{user="hacker_001"}[1m]) > 0
        for: 0s
        labels:
          severity: info
        annotations:
          summary: "Atividade do agente hacker registrada"
```

#### 3.2.3 Dashboard de Monitoramento

```
┌─────────────────────────────────────────────────────────────────┐
│                 DASHBOARD EM TEMPO REAL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ATIVIDADES EM TEMPO REAL                                       │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [████████████████████] Ataques Totais: 147                    │
│  [████████] SQL Injection: 23                                   │
│  [████] Brute Force: 12                                         │
│  [██] XSS: 5                                                    │
│  [█] Outros: 3                                                  │
│                                                                 │
│  STATUS DO SISTEMA                                              │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  CPU: 34%    MEM: 67%    DISK: 23%    NET: 12MB/s             │
│                                                                 │
│  ÚLTIMOS EVENTOS (ao vivo)                                      │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [14:32:15] SQL Injection bloqueado - IP: 192.168.1.100         │
│  [14:32:12] Login bem-sucedido - user: hacker_001              │
│  [14:32:10] Tentativa de saque - R$ 1.000,00                   │
│  [14:32:08] Brute force bloqueado - 5 tentativas               │
│  [14:32:05] Sessão criada - user: vitima_001                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Ferramentas de Monitoramento

| Ferramenta | Função | Frequência | Retenção |
|------------|--------|------------|----------|
| **Prometheus** | Métricas | 5-15s | 30 dias |
| **Grafana** | Dashboards | Tempo real | 30 dias |
| **Elasticsearch** | Logs | 1s | 90 dias |
| **Kibana** | Análise | Tempo real | 90 dias |
| **Alertmanager** | Alertas | Instantâneo | 30 dias |

### 3.4 Processo de Monitoramento

```
┌─────────────────────────────────────────────────────────────────┐
│              PROCESSO DE MONITORAMENTO CONTÍNUO                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. COLETA                                                      │
│     └─ Métricas e logs coletados a cada 5-15 segundos          │
│                                                                 │
│  2. PROCESSAMENTO                                               │
│     └─ Dados processados e indexados em tempo real              │
│                                                                 │
│  3. ANÁLISE                                                     │
│     └─ Padrões identificados e correlacionados                 │
│                                                                 │
│  4. ALERTA                                                      │
│     └─ Notificações enviadas para equipe de segurança          │
│                                                                 │
│  5. RESPOSTA                                                    │
│     └─ Ações automáticas ou manuais executadas                 │
│                                                                 │
│  6. DOCUMENTAÇÃO                                                │
│     └─ Todas as ações registradas para auditoria               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. AUDITORIA PERIÓDICA

### 4.1 Definição

Auditoria periódica é a revisão sistemática e agendada de logs, acessos e configurações para garantir conformidade e identificar anomalias.

### 4.2 Tipos de Auditoria

#### 4.2.1 Auditoria Diária

```yaml
auditoria_diaria:
  frequencia: "Diária"
  horario: "00:00 UTC"
  responsavel: "SOC"
  
  itens:
    - nome: "Logs de Ataque"
      fonte: "attack_log"
      filtros: "blocked=true, severity=critical"
      acao: "Relatório automático"
      
    - nome: "Tentativas de Login"
      fonte: "audit_log"
      filtros: "action=login"
      acao: "Verificar falhas"
      
    - nome: "Transações Financeiras"
      fonte: "transactions"
      filtros: "status=pending"
      acao: "Revisão manual"
```

#### 4.2.2 Auditoria Semanal

```yaml
auditoria_semanal:
  frequencia: "Semanal"
  horario: "Domingos, 02:00 UTC"
  responsavel: "Security Analyst"
  
  itens:
    - nome: "Análise de Tendências"
      fonte: "attack_log + audit_log"
      periodo: "7 dias"
      acao: "Relatório de tendências"
      
    - nome: "Revisão de Usuários"
      fonte: "users + sessions"
      acao: "Identificar contas inativas"
      
    - nome: "Configurações de Segurança"
      fonte: "nginx.conf + docker-compose.yml"
      acao: "Verificar mudanças"
```

#### 4.2.3 Auditoria Mensal

```yaml
auditoria_mensal:
  frequencia: "Mensal"
  horario: "1º dia, 03:00 UTC"
  responsavel: "CISO"
  
  itens:
    - nome: "Relatório Executivo"
      fonte: "Todas as fontes"
      acao: "Consolidado para diretoria"
      
    - nome: "Testes de Penetração"
      fonte: "Pentester"
      acao: "Validar vulnerabilidades"
      
    - nome: "Revisão de Políticas"
      fonte: "Configurações"
      acao: "Atualizar políticas"
      
    - nome: "Compliance"
      fonte: "Logs + Configurações"
      acao: "Verificar conformidade"
```

### 4.3 Checklists de Auditoria

#### 4.3.1 Auditoria Diária

```
CHECKLIST - AUDITORIA DIÁRIA
Data: ___________  Responsável: ___________

[ ] Verificar logs de ataque das últimas 24h
[ ] Analisar tentativas de login falhas
[ ] Revisar transações pendentes
[ ] Verificar status dos serviços
[ ] Confirmar integridade dos backups
[ ] Atualizar dashboard de métricas
[ ] Enviar relatório para equipe

Assinatura: ___________
```

#### 4.3.2 Auditoria Semanal

```
CHECKLIST - AUDITORIA SEMANAL
Semana: ___________  Responsável: ___________

[ ] Analisar tendências de ataque
[ ] Revisar usuários ativos/inativos
[ ] Verificar configurações de segurança
[ ] Testar processos de backup
[ ] Revisar alertas de performance
[ ] Documentar incidentes
[ ] Preparar relatório semanal

Assinatura: ___________
```

#### 4.3.3 Auditoria Mensal

```
CHECKLIST - AUDITORIA MENSAL
Mês: ___________  Responsável: ___________

[ ] Gerar relatório executivo
[ ] Coordenar testes de penetração
[ ] Revisar políticas de segurança
[ ] Verificar compliance
[ ] Apresentar resultados à diretoria
[ ] Atualizar plano de contingência
[ ] Definir metas do próximo mês

Assinatura: ___________
```

### 4.4 Relatórios de Auditoria

#### 4.4.1 Template de Relatório Diário

```markdown
# RELATÓRIO DE AUDITORIA DIÁRIA
**Data:** [DATA]
**Responsável:** [NOME]

## Resumo Executivo
- Total de ataques: [NÚMERO]
- Ataques bloqueados: [NÚMERO]
- Taxa de bloqueio: [PERCENTUAL]

## Detalhes
### Ataques por Tipo
- SQL Injection: [NÚMERO]
- Brute Force: [NÚMERO]
- XSS: [NÚMERO]

### Usuários Ativos
- Logins hoje: [NÚMERO]
- Falhas de login: [NÚMERO]

### Transações
- Saques solicitados: [NÚMERO]
- Saques aprovados: [NÚMERO]
- Valor total: R$ [VALOR]

## Incidentes
[SE HOUVER]

## Recomendações
[SE HOUVER]

## Conclusão
Status geral: [BOM/REGULAR/CRÍTICO]
```

### 4.5 Frequência de Auditorias

| Tipo | Frequência | Responsável | Duração Estimada |
|------|------------|-------------|------------------|
| Diária | Todo dia | SOC | 30 minutos |
| Semanal | Domingos | Security Analyst | 2 horas |
| Mensal | 1º dia | CISO | 4 horas |
| Trimestral | A cada 3 meses | CISO + Auditoria | 8 horas |
| Anual | Janeiro | CISO + Diretoria | 1 dia |

---

## 5. ISOLAMENTO TOTAL

### 5.1 Definição

Isolamento total é a separação física e lógica da sandbox de qualquer rede ou sistema externo, garantindo que não haja comunicação não autorizada.

### 5.2 Camadas de Isolamento

#### 5.2.1 Isolamento de Rede (Docker)

```yaml
# docker-compose.yml
networks:
  ravena-sandbox:
    driver: bridge
    internal: true  # SEM ACESSO EXTERNO
    ipam:
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

services:
  ravena-app:
    networks:
      - ravena-sandbox
    # NÃO expor portas para hosts externos
    # Apenas para comunicação interna
```

#### 5.2.2 Isolamento de Processos

```yaml
# Containers isolados
services:
  ravena-app:
    isolation: process  # Windows
    # ou
    security_opt:
      - no-new-privileges:true
    read_only: true  # Sistema de arquivos read-only
    tmpfs:
      - /tmp
      - /var/run
```

#### 5.2.3 Isolamento de Dados

```sql
-- Usuário do banco com permissões mínimas
CREATE ROLE ravena_app_role;
GRANT CONNECT ON DATABASE ravena_sandbox TO ravena_app_role;
GRANT USAGE ON SCHEMA public TO ravena_app_role;
GRANT SELECT, INSERT, UPDATE ON users TO ravena_app_role;
GRANT SELECT, INSERT, UPDATE ON transactions TO ravena_app_role;

-- REVOGAR acesso a dados sensíveis
REVOKE ALL ON audit_log FROM ravena_app_role;
REVOKE ALL ON attack_log FROM ravena_app_role;
```

### 5.3 Verificações de Isolamento

#### 5.3.1 Teste de Conectividade Externa

```bash
#!/bin/bash
# Script de verificação de isolamento

echo "=== VERIFICAÇÃO DE ISOLAMENTO ==="

# 1. Testar acesso à internet
echo "1. Testando acesso à internet..."
if ping -c 1 google.com &> /dev/null; then
    echo "   [FALHA] Acesso à internet detectado!"
else
    echo "   [OK] Sem acesso à internet"
fi

# 2. Testar DNS externo
echo "2. Testando DNS externo..."
if nslookup google.com &> /dev/null; then
    echo "   [FALHA] DNS externo acessível!"
else
    echo "   [OK] DNS externo bloqueado"
fi

# 3. Testar portas externas
echo "3. Testando portas externas..."
if nc -z -w1 8.8.8.8 53 &> /dev/null; then
    echo "   [FALHA] Porta externa acessível!"
else
    echo "   [OK] Portas externas bloqueadas"
fi

# 4. Verificar containers
echo "4. Verificando containers..."
docker network inspect ravena-sandbox | grep "Internal"

echo "=== FIM DA VERIFICAÇÃO ==="
```

#### 5.3.2 Monitoramento de Tráfego

```yaml
# Configuração de monitoramento de tráfego
monitoring:
  traffic_analysis:
    enabled: true
    interfaces:
      - docker0
      - br-ravena-sandbox
    alerts:
      - external_connection_attempt
      - dns_leak
      - unusual_traffic_pattern
    
    logging:
      enabled: true
      destination: /var/log/traffic/
      retention: 30_days
```

### 5.4 Controles de Isolamento

| Camada | Controle | Status | Responsável |
|--------|----------|--------|-------------|
| **Rede** | Docker internal network | ✅ ATIVO | DevOps |
| **Rede** | Sem roteamento externo | ✅ ATIVO | DevOps |
| **Rede** | DNS interno apenas | ✅ ATIVO | DevOps |
| **Processo** | Containers isolados | ✅ ATIVO | DevOps |
| **Processo** | Sem privilégios extras | ✅ ATIVO | DevOps |
| **Dados** | Permissões mínimas | ✅ ATIVO | DBA |
| **Dados** | Logs imutáveis | ✅ ATIVO | DBA |
| **Aplicação** | Validação de entrada | ✅ ATIVO | Developer |
| **Aplicação** | Rate limiting | ✅ ATIVO | Security Engineer |

### 5.5 Procedimentos de Emergência

```
┌─────────────────────────────────────────────────────────────────┐
│              PROCEDIMENTO DE EMERGÊNCIA                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. DETECÇÃO DE ISOLAMENTO COMPROMETIDO                        │
│     └─ Alerta automático gerado                                 │
│                                                                 │
│  2. CONFINAMENTO IMEDIATO                                       │
│     └─ Desligar todos os containers                             │
│     └─ Bloquear todas as conexões                               │
│                                                                 │
│  3. INVESTIGAÇÃO                                                │
│     └─ Analisar logs de tráfego                                 │
│     └─ Identificar fonte do comprometimento                     │
│                                                                 │
│  4. REMEDIAÇÃO                                                  │
│     └─ Corrigir vulnerabilidade                                 │
│     └─ Atualizar controles                                      │
│                                                                 │
│  5. RESTAURAÇÃO                                                 │
│     └─ Restaurar sandbox de backup                              │
│     └─ Validar isolamento                                       │
│                                                                 │
│  6. DOCUMENTAÇÃO                                                │
│     └─ Documentar incidente                                     │
│     └─ Atualizar procedimentos                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.6 Métricas de Isolamento

```yaml
metricas_isolamento:
  - nome: "Tentativas de Conexão Externa"
    tipo: "counter"
    meta: 0
    alerta: "> 0"
    
  - nome: "Tráfego de Saída"
    tipo: "gauge"
    meta: "< 1KB/min"
    alerta: "> 10KB/min"
    
  - nome: "DNS Queries Externos"
    tipo: "counter"
    meta: 0
    alerta: "> 0"
    
  - nome: "Integridade de Containers"
    tipo: "boolean"
    meta: true
    alerta: "false"
```

---

## 6. IMPLEMENTAÇÃO

### 6.1 Scripts de Configuração

#### 6.1.1 Configurar Laboratório do Agente Hacker

```bash
#!/bin/bash
# hacker-lab/setup_lab.sh

echo "Configurando laboratório do agente hacker..."

# Executar script de configuração
chmod +x hacker-lab/setup_lab.sh
./hacker-lab/setup_lab.sh

echo "Laboratório configurado com sucesso!"
echo "Acesse: cd ~/hacker-lab"
```

#### 6.1.2 Verificar Isolamento

```bash
#!/bin/bash
# scripts/verify_isolation.sh

echo "Verificando isolamento da sandbox..."

# Executar testes de isolamento
./tests/isolation_test.sh

# Verificar status dos containers
docker-compose ps

# Verificar regras de rede
docker network inspect ravena-sandbox

echo "Verificação concluída!"
```

#### 6.1.3 Iniciar Monitoramento

```bash
#!/bin/bash
# scripts/start_monitoring.sh

echo "Iniciando monitoramento contínuo..."

# Iniciar Prometheus
docker-compose up -d prometheus

# Iniciar Grafana
docker-compose up -d grafana

# Iniciar Elasticsearch
docker-compose up -d elasticsearch

# Iniciar Kibana
docker-compose up -d kibana

# Configurar dashboards
python monitoring/setup_grafana.py

echo "Monitoramento iniciado!"
```

### 6.2 Checklist de Implementação

```
CHECKLIST - IMPLEMENTAÇÃO DOS CONTROLES
Data: ___________  Responsável: ___________

AGENTE HACKER:
[ ] Credenciais criadas
[ ] Permissões configuradas
[ ] Teste de acesso realizado
[ ] Monitoramento ativado

MONITORAMENTO CONTÍNUO:
[ ] Prometheus configurado
[ ] Grafana operational
[ ] Alertas configurados
[ ] Dashboards criados

AUDITORIA PERIÓDICA:
[ ] Agendamentos configurados
[ ] Checklists criados
[ ] Templates de relatório prontos
[ ] Responsáveis definidos

ISOLAMENTO TOTAL:
[ ] Rede isolada verificada
[ ] Sem acesso externo confirmado
[ ] DNS interno configurado
[ ] Logs de tráfego ativos

Assinatura: ___________
```

---

## 7. RESUMO

### Agentes e Acessos

| Agente | Acesso | Monitoramento | Auditoria |
|--------|--------|---------------|-----------|
| admin | Total | Sim | Sim |
| pentester | Testes | Sim | Sim |
| security_engineer | Config | Sim | Sim |
| devops | Infra | Sim | Sim |
| security_analyst | Leitura | Sim | Sim |
| soc | Monitoramento | Sim | Sim |
| ciso | Relatórios | Sim | Sim |
| **hacker** | **Testes** | **Sim** | **Sim** |

### Controles Implementados

1. ✅ **Monitoramento Contínuo** - 24/7 em tempo real
2. ✅ **Auditoria Periódica** - Diária, Semanal, Mensal
3. ✅ **Isolamento Total** - Sem acesso externo

### Próximos Passos

1. Executar scripts de configuração
2. Validar isolamento
3. Iniciar monitoramento
4. Treinar equipe
5. Iniciar testes

---

**Status:** PENDENTE DE IMPLEMENTAÇÃO
**Versão:** 1.0
**Data:** 31/07/2026
