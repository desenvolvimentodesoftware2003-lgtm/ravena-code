# ============================================
# SCRIPTS PARA WINDOWS - SANDBOX RAVENA
# ============================================

## Scripts Disponíveis

### 1. setup.bat
**Configuração automática da sandbox**

```batch
setup.bat
```

Este script:
- Verifica pré-requisitos (Docker, Docker Compose, Python)
- Instala dependências Python
- Cria estrutura de diretórios
- Configura variáveis de ambiente
- Inicia containers Docker
- Aguarda inicialização
- Executa testes básicos
- Gera relatório inicial

### 2. start_sandbox.bat
**Inicia a sandbox**

```batch
start_sandbox.bat
```

Este script:
- Verifica se está no diretório correto
- Inicia containers Docker
- Exibe informações de acesso

### 3. stop_sandbox.bat
**Para a sandbox**

```batch
stop_sandbox.bat
```

Este script:
- Pede confirmação
- Para todos os containers
- Exibe instruções para reiniciar

### 4. cleanup.bat
**Limpa todos os dados**

```batch
cleanup.bat
```

Este script:
- Pede confirmação
- Para e remove containers
- Remove volumes Docker
- Remove dados persistidos
- Remove logs

### 5. verify_sandbox.bat
**Verifica status da sandbox**

```batch
verify_sandbox.bat
```

Este script:
- Verifica status dos containers
- Testa conectividade dos serviços
- Verifica banco de dados
- Exibe resumo da verificação

---

## Ordem de Execução

### Instalação Primeira Vez
```batch
setup.bat
```

### Uso Diário
```batch
# Iniciar sandbox
start_sandbox.bat

# Verificar status
verify_sandbox.bat

# Parar sandbox
stop_sandbox.bat

# Limpar dados (quando necessário)
cleanup.bat
```

---

## Pré-requisitos para Windows

### 1. Docker Desktop
- Baixe: https://docs.docker.com/desktop/install/windows-install/
- Instale e reinicie o computador

### 2. Docker Compose
- Geralmente já vem com Docker Desktop
- Verifique: `docker-compose --version`

### 3. Python
- Baixe: https://www.python.org/downloads/
- Marque "Add Python to PATH" durante instalação
- Verifique: `python --version`

### 4. cURL
- Geralmente já vem com Windows 10+
- Verifique: `curl --version`

---

## Solução de Problemas

### Erro: "docker-compose" não é reconhecido
```batch
# Verificar se Docker Desktop está rodando
docker ps

# Se não estiver, inicie o Docker Desktop
```

### Erro: "python" não é reconhecido
```batch
# Verificar se Python está no PATH
python --version

# Se não estiver, reinstale Python com "Add to PATH"
```

### Erro: Porta já em uso
```batch
# Verificar qual processo está usando a porta
netstat -ano | findstr :8080

# Matar o processo (substitua <PID> pelo número)
taskkill /PID <PID> /F
```

### Erro: Container não inicia
```batch
# Ver logs do container
docker-compose logs ravena-app

# Reiniciar containers
docker-compose down
docker-compose up -d
```

### Erro: Banco de dados não conecta
```batch
# Reiniciar container do banco
docker-compose restart ravena-db

# Aguardar 10 segundos
timeout /t 10

# Verificar logs
docker-compose logs ravena-db
```

---

## Comandos Úteis do Docker

```batch
# Ver status dos containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f ravena-app

# Reiniciar um serviço
docker-compose restart ravena-app

# Parar tudo
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Reconstruir containers
docker-compose up -d --build
```

---

## Portas Utilizadas

| Porta | Serviço | URL |
|-------|---------|-----|
| 8080 | Servidor Ravena | http://localhost:8080 |
| 80 | Nginx | http://localhost:80 |
| 3000 | Grafana | http://localhost:3000 |
| 5601 | Kibana | http://localhost:5601 |
| 9090 | Prometheus | http://localhost:9090 |
| 9200 | Elasticsearch | http://localhost:9200 |
| 5432 | PostgreSQL | localhost:5432 |
| 6379 | Redis | localhost:6379 |

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

## Notas Importantes

1. **Execute os scripts como Administrador** se encontrar erros de permissão
2. **Aguarde a inicialização completa** antes de acessar os serviços
3. **Verifique se as portas estão livres** antes de iniciar
4. **Mantenha o Docker Desktop rodando** durante o uso
5. **Faça backup dos dados** antes de executar cleanup.bat

---

## Suporte

Se encontrar problemas:
1. Verifique se todos os pré-requisitos estão instalados
2. Execute `verify_sandbox.bat` para diagnóstico
3. Consulte os logs em `docker-compose logs`
4. Reinicie o Docker Desktop se necessário
