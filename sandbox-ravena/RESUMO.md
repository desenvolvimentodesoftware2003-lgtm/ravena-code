# ============================================
# RESUMO - SANDBOX RAVENA
# ============================================

## Arquivos Criados

### Configuração Principal
- `docker-compose.yml` - Configuração dos containers
- `docker-compose.override.yml` - Configurações adicionais
- `Dockerfile.ravena` - Dockerfile da aplicação
- `requirements.txt` - Dependências Python
- `.env.example` - Variáveis de ambiente
- `.gitignore` - Arquivos ignorados pelo Git

### Scripts de Inicialização
- `start_sandbox.sh` - Iniciar sandbox
- `stop_sandbox.sh` - Parar sandbox
- `cleanup.sh` - Limpar dados
- `install_deps.sh` - Instalar dependências
- `verify_sandbox.sh` - Verificar sandbox
- `run_all.sh` - Executar tudo

### Aplicação
- `app.py` - Servidor principal
- `utils.py` - Utilitários

### Configuração do Nginx
- `nginx/nginx.conf` - Configuração do Nginx

### Inicialização do Banco
- `init-scripts/01-init.sql` - Script de inicialização do PostgreSQL

### Testes
- `tests/security_tests.py` - Script de testes de segurança

### Monitoramento
- `monitoring/security_monitor.py` - Monitor de segurança
- `monitoring/generate_report.py` - Gerador de relatórios
- `monitoring/setup_grafana.py` - Configuração do Grafana
- `monitoring/README.md` - Documentação do monitoramento

### Configuração do Grafana
- `monitoring/grafana/dashboard.json` - Dashboard principal

### Configuração do Prometheus
- `monitoring/prometheus/prometheus.yml` - Configuração do Prometheus
- `monitoring/prometheus/alert_rules.yml` - Regras de alerta

### Configuração do Alertmanager
- `monitoring/alertmanager/alertmanager.yml` - Configuração do Alertmanager

### Configuração do Elasticsearch
- `monitoring/elasticsearch/index_patterns.json` - Index patterns

### Documentação
- `README.md` - Documentação principal
- `GUIA_COMPLETO.md` - Guia completo de uso
- `monitoring/README.md` - Documentação do monitoramento

---

## Estrutura de Diretórios

```
sandbox-ravena/
├── docker-compose.yml
├── docker-compose.override.yml
├── Dockerfile.ravena
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── GUIA_COMPLETO.md
├── app.py
├── utils.py
├── start_sandbox.sh
├── stop_sandbox.sh
├── cleanup.sh
├── install_deps.sh
├── verify_sandbox.sh
├── run_all.sh
├── nginx/
│   └── nginx.conf
├── init-scripts/
│   └── 01-init.sql
├── tests/
│   └── security_tests.py
├── monitoring/
│   ├── README.md
│   ├── security_monitor.py
│   ├── generate_report.py
│   ├── setup_grafana.py
│   ├── grafana/
│   │   └── dashboard.json
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alert_rules.yml
│   ├── alertmanager/
│   │   └── alertmanager.yml
│   └── elasticsearch/
│       └── index_patterns.json
├── logs/
├── data/
└── monitoring/
    └── grafana/
```

---

## Início Rápido

### 1. Instalar Dependências
```bash
cd sandbox-ravena
./install_deps.sh
```

### 2. Iniciar Sandbox
```bash
./start_sandbox.sh
```

### 3. Executar Testes
```bash
python tests/security_tests.py
```

### 4. Gerar Relatório
```bash
python monitoring/generate_report.py
```

### 5. Verificar Sandbox
```bash
./verify_sandbox.sh
```

---

## Serviços

| Serviço | Porta | URL |
|---------|-------|-----|
| Servidor Ravena | 8080 | http://localhost:8080 |
| Nginx | 80 | http://localhost:80 |
| Grafana | 3000 | http://localhost:3000 |
| Kibana | 5601 | http://localhost:5601 |
| Prometheus | 9090 | http://localhost:9090 |
| Elasticsearch | 9200 | http://localhost:9200 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

---

## Credenciais

### Aplicação
| Usuário | Senha | Perfil |
|---------|-------|--------|
| attacker_001 | test123 | Atacante |
| vitima_001 | test123 | Vítima |
| vitima_002 | test123 | Vítima |
| lara_001 | test123 | Conta Laranja |
| admin_test | admin123 | Administrador |

### Banco de Dados
- **Host:** localhost
- **Port:** 5432
- **Database:** ravena_sandbox
- **User:** ravena_test
- **Password:** sandbox_password_123

### Grafana
- **URL:** http://localhost:3000
- **User:** admin
- **Password:** sandbox_monitor_123

---

## Comandos Úteis

```bash
# Iniciar sandbox
./start_sandbox.sh

# Parar sandbox
./stop_sandbox.sh

# Verificar sandbox
./verify_sandbox.sh

# Executar testes
python tests/security_tests.py

# Gerar relatório
python monitoring/generate_report.py

# Ver estatísticas
python utils.py --stats

# Ver ataques recentes
python utils.py --attacks 50

# Exportar logs
python utils.py --export

# Limpar dados
./cleanup.sh
```

---

## Funcionalidades

### 1. Servidor da Ravena
- Autenticação JWT
- Sistema de slots
- Sistema de saques
- Validação de segurança
- Logs de auditoria

### 2. Banco de Dados
- Tabelas de teste
- Triggers de auditoria
- Funções de validação
- Dados fictícios

### 3. Monitoramento
- Dashboard em tempo real
- Alertas automáticos
- Análise de logs
- Métricas de performance

### 4. Testes de Segurança
- SQL Injection
- XSS
- Brute Force
- IDOR
- Path Traversal
- Manipulação de dados

---

## Segurança

### Isolamento
- Container de rede isolado
- Dados 100% fictícios
- Sem acesso externo

### Monitoramento
- Todos os ataques registrados
- Logs imutáveis
- Alertas automáticos

### Controles
- Rate limiting
- Validação de entrada
- Autenticação forte

---

## Solução de Problemas

### Containers não iniciam
```bash
docker-compose logs
```

### Porta em uso
```bash
netstat -ano | findstr :8080
taskkill /PID <PID> /F
```

### Banco não conecta
```bash
docker-compose restart ravena-db
```

### Grafana não mostra dados
```bash
# Verificar Prometheus
curl http://localhost:9090

# Reiniciar Grafana
docker-compose restart ravena-grafana
```

---

## Referências

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/documentation)
- [Nginx](https://nginx.org/en/docs/)
- [Grafana](https://grafana.com/docs/)
- [Prometheus](https://prometheus.io/docs/)
- [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Kibana](https://www.elastic.co/guide/en/kibana/current/)
- [OWASP](https://owasp.org/)

---

## Licença

Este projeto é para fins educacionais e de testes de segurança. O uso deste software para fins ilegais é de inteira responsabilidade do usuário.
