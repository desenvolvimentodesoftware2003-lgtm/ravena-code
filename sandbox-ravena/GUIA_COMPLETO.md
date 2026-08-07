# ============================================
# GUIA COMPLETO - SANDBOX RAVENA
# ============================================

## Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação](#instalação)
4. [Uso Básico](#uso-básico)
5. [Testes de Segurança](#testes-de-seurança)
6. [Monitoramento](#monitoramento)
7. [Utilitários](#utilitários)
8. [Troubleshooting](#troubleshooting)
9. [Referências](#referências)

---

## Visão Geral

A **Sandbox Ravena** é um ambiente isolado para testes de segurança do módulo de jogos/slots. O objetivo é permitir que desenvolvedores e administradores testem a segurança de suas aplicações em um ambiente controlado, identificando e corrigindo vulnerabilidades antes da produção.

### Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    SANDBOX ISOLADA                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   Nginx      │────▶│   Ravena     │────▶│  PostgreSQL  │ │
│  │   (Proxy)    │     │   (App)      │     │  (Database)  │ │
│  └──────────────┘     └──────────────┘     └──────────────┘ │
│         │                    │                    │         │
│         │              ┌─────┴─────┐              │         │
│         │              │   Redis   │              │         │
│         │              │  (Cache)  │              │         │
│         │              └───────────┘              │         │
│         │                                         │         │
│  ┌──────┴──────┐                         ┌────────┴───────┐ │
│  │  Grafana    │                         │    Kibana      │ │
│  │ (Dashboard) │                         │ (Log Analysis) │ │
│  └─────────────┘                         └────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Pré-requisitos

### Software Necessário

| Software | Versão Mínima | Link |
|----------|---------------|------|
| Docker | 20.10+ | https://docs.docker.com/get-docker/ |
| Docker Compose | 2.0+ | https://docs.docker.com/compose/install/ |
| Python | 3.8+ | https://www.python.org/downloads/ |
| pip | 20.0+ | Incluído com Python |

### Hardware Mínimo

- **CPU:** 2 cores
- **RAM:** 4 GB
- **Disco:** 10 GB livres
- **Sistema:** Windows 10+, macOS 10.15+, Ubuntu 20.04+

---

## Instalação

### 1. Clonar o Repositório

```bash
# Navegar até o diretório de instalação
cd C:\Users\DELL\Downloads

# O diretório já foi criado
cd sandbox-ravena
```

### 2. Instalar Dependências Python

```bash
# Executar script de instalação
./install_deps.sh

# Ou manualmente:
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar conforme necessário
# As configurações padrão já funcionam para a sandbox
```

### 4. Iniciar a Sandbox

```bash
# Executar script de inicialização
./start_sandbox.sh

# Ou manualmente:
docker-compose up -d
```

### 5. Verificar Instalação

```bash
# Verificar status dos containers
docker-compose ps

# Verificar health check
curl http://localhost:8080/health
```

---

## Uso Básico

### Acessar a Aplicação

- **URL:** http://localhost:8080
- **Usuário:** attacker_001
- **Senha:** test123

### Credenciais de Teste

| Usuário | Senha | Saldo | Perfil |
|---------|-------|-------|--------|
| attacker_001 | test123 | R$ 10.000,00 | Atacante |
| vitima_001 | test123 | R$ 5.000,00 | Vítima |
| vitima_002 | test123 | R$ 3.464,00 | Vítima |
| lara_001 | test123 | R$ 0,00 | Conta Laranja |
| admin_test | admin123 | R$ 0,00 | Administrador |

### Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/health` | GET | Health check |
| `/api/auth/login` | POST | Autenticação |
| `/api/auth/me` | GET | Dados do usuário |
| `/api/slots/spin` | POST | Aposta em slot |
| `/api/withdrawals/request` | POST | Solicitar saque |
| `/api/withdrawals/history` | GET | Histórico de saques |
| `/api/admin/attacks` | GET | Log de ataques |

---

## Testes de Segurança

### Executar Todos os Testes

```bash
python tests/security_tests.py
```

### Tipos de Testes

#### 1. Testes de Autenticação
- Login com credenciais válidas
- Login com credenciais inválidas
- SQL Injection no login
- XSS no login
- Força bruta

#### 2. Testes de Slots
- Aposta normal
- Manipulação de valor de aposta
- Aposta acima do limite

#### 3. Testes de Saque
- Saque normal
- SQL Injection no saque
- Saque acima do saldo
- Chave PIX inválida

#### 4. Testes de IDOR
- Acesso a dados de outros usuários
- Manipulação de IDs

#### 5. Testes de Sessão
- Sessão expirada
- Token inválido

#### 6. Testes de Path Traversal
- Tentativas de acesso a arquivos do sistema

### Analisar Resultados

```bash
# Ver estatísticas
python utils.py --stats

# Ver ataques recentes
python utils.py --attacks 50

# Gerar relatório HTML
python monitoring/generate_report.py
```

---

## Monitoramento

### Grafana

- **URL:** http://localhost:3000
- **Usuário:** admin
- **Senha:** sandbox_monitor_123

#### Dashboards Disponíveis

1. **Security Dashboard**
   - Total de ataques
   - Ataques bloqueados
   - Taxa de bloqueio
   - Ataques por tipo

2. **Performance Dashboard**
   - Requisições por segundo
   - Tempo de resposta
   - Taxa de erro

3. **System Dashboard**
   - Uso de CPU
   - Uso de memória
   - Uso de disco

### Kibana

- **URL:** http://localhost:5601

#### Visualizar Logs

1. Acesse Kibana
2. Vá em **Discover**
3. Selecione o index pattern `ravena-attacks-*`
4. Filtre por tipo de ataque

### Prometheus

- **URL:** http://localhost:9090

#### Consultas Úteis

```promql
# Total de ataques
attack_log_total

# Ataques bloqueados
attack_log_blocked

# Taxa de bloqueio
attack_log_blocked / attack_log_total * 100

# Ataques por segundo
rate(attack_log_total[5m])
```

### Alertas

- **URL:** http://localhost:9093

#### Tipos de Alerta

| Alerta | Severidade | Descrição |
|--------|------------|-----------|
| HighAttackRate | Crítico | Taxa alta de ataques |
| SQLInjectionDetected | Crítico | SQL Injection detectado |
| BruteForceDetected | Alto | Brute force detectado |
| ServiceDown | Crítico | Serviço indisponível |

---

## Utilitários

### Comandos Disponíveis

```bash
# Mostrar estatísticas
python utils.py --stats

# Mostrar ataques recentes
python utils.py --attacks [limite]

# Mostrar usuários
python utils.py --users

# Exportar logs
python utils.py --export [arquivo]

# Limpar logs antigos
python utils.py

# Menu interativo
python utils.py
```

### Exportar Dados

```bash
# Exportar logs para JSON
python utils.py --export logs_export.json

# Exportar com data automática
python utils.py --export
```

### Limpar Dados

```bash
# Limpar logs antigos (7 dias)
python utils.py

# Selecionar opção 6: Limpar logs antigos
```

### Resetar Banco de Dados

```bash
# Via utilitário
python utils.py

# Selecionar opção 4: Resetar banco de dados
```

---

## Troubleshooting

### Problemas Comuns

#### 1. Docker não inicia

```bash
# Verificar se Docker está rodando
docker info

# Reiniciar Docker
# Windows: Reiniciar o Docker Desktop
# Linux: sudo systemctl restart docker
```

#### 2. Porta já em uso

```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux
sudo lsof -i :8080
sudo kill -9 <PID>
```

#### 3. Container não inicia

```bash
# Ver logs do container
docker-compose logs ravena-app

# Verificar status
docker-compose ps
```

#### 4. Banco de dados não conecta

```bash
# Reiniciar banco
docker-compose restart ravena-db

# Aguardar inicialização
sleep 10

# Verificar logs
docker-compose logs ravena-db
```

#### 5. Grafana não mostra dados

```bash
# Verificar se Prometheus está rodando
curl http://localhost:9090

# Verificar fonte de dados no Grafana
# Settings > Data Sources > Prometheus
```

### Comandos de Diagnóstico

```bash
# Ver status de todos os containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f ravena-app

# Executar bash em um container
docker exec -it ravena-app bash

# Conectar ao banco
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox
```

### Limpeza Completa

```bash
# Parar e remover containers
docker-compose down -v

# Remover dados
rm -rf data/*
rm -rf logs/*

# Recriar tudo
./start_sandbox.sh
```

---

## Referências

### Documentação

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/)

### Segurança

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Ferramentas

- [Burp Suite](https://portswigger.net/burp)
- [OWASP ZAP](https://www.zaproxy.org/)
- [Nmap](https://nmap.org/)
- [SQLMap](https://sqlmap.org/)

---

## Licença

Este projeto é para fins educacionais e de testes de segurança. O uso deste software para fins ilegais é de inteira responsabilidade do usuário.

---

## Contato

Para reportar bugs ou vulnerabilidades, por favor abra uma issue no repositório.
