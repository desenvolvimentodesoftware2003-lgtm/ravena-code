# SANDBOX RAVENA - Testes de Segurança

Ambiente isolado para testes de penetração e análise de segurança do módulo de jogos/slots.

## ⚠️ AVISO IMPORTANTE

Este projeto é exclusivamente para fins educacionais e de testes de segurança em ambiente controlado. O uso deste código para fins ilegais é de inteira responsabilidade do usuário.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.8+ instalado
- Mínimo de 4GB de RAM disponível
- Conexão com internet (apenas para download das imagens)

## 🚀 Instalação Rápida

### 1. Clonar o repositório
```bash
cd C:\Users\DELL\Downloads\sandbox-ravena
```

### 2. Iniciar a sandbox
```bash
# Windows (PowerShell)
.\start_sandbox.sh

# Linux/Mac
chmod +x start_sandbox.sh
./start_sandbox.sh
```

### 3. Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 4. Executar testes
```bash
python tests/security_tests.py
```

## 🏗️ Arquitetura

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
│  │   Grafana   │                         │    Kibana      │ │
│  │ (Dashboard) │                         │ (Log Analysis) │ │
│  └─────────────┘                         └────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Ravena App | 8080 | Servidor principal da aplicação |
| Nginx | 80 | Reverse proxy com rate limiting |
| PostgreSQL | 5432 | Banco de dados principal |
| Redis | 6379 | Cache e sessões |
| Grafana | 3000 | Dashboard de monitoramento |
| Kibana | 5601 | Análise de logs |

## 📊 Credenciais

### Usuários de Teste
| Usuário | Senha | Saldo | Perfil |
|---------|-------|-------|--------|
| attacker_001 | test123 | R$ 10.000,00 | Atacante |
| vitima_001 | test123 | R$ 5.000,00 | Vítima |
| vitima_002 | test123 | R$ 3.464,00 | Vítima |
| lara_001 | test123 | R$ 0,00 | Conta Laranja |
| admin_test | admin123 | R$ 0,00 | Administrador |

### Banco de Dados
```
Host: localhost
Port: 5432
Database: ravena_sandbox
User: ravena_test
Password: sandbox_password_123
```

## 🧪 Testes Disponíveis

### 1. Testes de Autenticação
- Login com credenciais válidas
- Login com credenciais inválidas
- SQL Injection no login
- XSS no login
- Força bruta

### 2. Testes de Slots
- Aposta normal
- Manipulação de valor de aposta
- Aposta acima do limite

### 3. Testes de Saque
- Saque normal
- SQL Injection no saque
- Saque acima do saldo
- Chave PIX inválida

### 4. Testes de IDOR
- Acesso a dados de outros usuários
- Manipulação de IDs

### 5. Testes de Sessão
- Sessão expirada
- Token inválido

### 6. Testes de Path Traversal
- Tentativas de acesso a arquivos do sistema

## 📈 Monitoramento

### Grafana
Acesse http://localhost:3000
- Login: admin
- Senha: sandbox_monitor_123

### Kibana
Acesse http://localhost:5601
- Visualize logs em tempo real
- Analise tentativas de ataque

## 📁 Estrutura de Diretórios

```
sandbox-ravena/
├── docker-compose.yml      # Configuração dos containers
├── Dockerfile.ravena       # Dockerfile da aplicação
├── requirements.txt        # Dependências Python
├── app.py                  # Servidor principal
├── start_sandbox.sh        # Script de inicialização
├── nginx/
│   └── nginx.conf          # Configuração do Nginx
├── init-scripts/
│   └── 01-init.sql         # Inicialização do banco
├── monitoring/
│   ├── security_monitor.py # Monitor de segurança
│   └── grafana/            # Configurações do Grafana
├── tests/
│   └── security_tests.py   # Script de testes
├── logs/                   # Logs dos serviços
└── data/                   # Dados persistidos
```

## 🛡️ Segurança da Sandbox

### Isolamento
- Container de rede isolado (sem acesso externo)
- Dados 100% fictícios
- Sem conexão com ambiente de produção

### Monitoramento
- Todos os ataques são registrados
- Logs imutáveis
- Alertas automáticos

### Controles
- Rate limiting em endpoints sensíveis
- WAF com regras de detecção
- Validação de entrada em todas as rotas

## 🔍 Debugging

### Ver logs em tempo real
```bash
# Todos os containers
docker-compose logs -f

# Apenas servidor
docker-compose logs -f ravena-app

# Apenas banco
docker-compose logs -f ravena-db
```

### Conectar ao banco
```bash
docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox
```

### Verificar status
```bash
docker-compose ps
```

## 📝 Comandos Úteis

```bash
# Iniciar sandbox
docker-compose up -d

# Parar sandbox
docker-compose down

# Rebuild após mudanças
docker-compose up -d --build

# Limpar tudo (incluindo dados)
docker-compose down -v
rm -rf data/*

# Executar testes
python tests/security_tests.py

# Gerar relatório
python monitoring/security_monitor.py --report
```

## 🐛 Solução de Problemas

### Porta já em uso
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Linux
sudo lsof -i :8080
sudo kill -9 <PID>
```

### Container não inicia
```bash
docker-compose logs ravena-app
```

### Banco não conecta
```bash
docker-compose restart ravena-db
sleep 5
docker-compose logs ravena-db
```

## 📚 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/auth-external.html)

## ⚖️ Aviso Legal

Este software é fornecido "como está", sem garantia de qualquer tipo. O uso deste software para testar sistemas sem autorização explícita do proprietário é ilegal e pode resultar em processos criminais e civis.

O autor não se responsabiliza pelo uso indevido deste software.

## 📞 Contato

Para报告ar bugs ou vulnerabilidades, por favor abra uma issue no repositório.
