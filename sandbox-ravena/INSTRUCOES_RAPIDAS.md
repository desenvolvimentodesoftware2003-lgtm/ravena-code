# ============================================
# INSTRUÇÕES DE USO RÁPIDO
# ============================================

## Para Iniciar a Sandbox (Windows)

### Opção 1: Configuração Automática (Recomendado)
```batch
# Navegue até o diretório
cd C:\Users\DELL\Downloads\sandbox-ravena

# Execute a configuração automática
setup.bat
```

### Opção 2: Inicialização Manual
```batch
# Navegue até o diretório
cd C:\Users\DELL\Downloads\sandbox-ravena

# Inicie a sandbox
start_sandbox.bat
```

---

## Para Verificar se Está Funcionando

```batch
# Verificar status
verify_sandbox.bat
```

---

## Para Executar Testes de Segurança

```batch
# Executar todos os testes
python tests/security_tests.py
```

---

## Para Gerar Relatório

```batch
# Gerar relatório HTML
python monitoring/generate_report.py
```

---

## Para Parar a Sandbox

```batch
# Parar sandbox
stop_sandbox.bat
```

---

## Para Limpar Todos os Dados

```batch
# Limpar dados
cleanup.bat
```

---

## URLs de Acesso

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Aplicação** | http://localhost:8080 | attacker_001 / test123 |
| **Grafana** | http://localhost:3000 | admin / sandbox_monitor_123 |
| **Kibana** | http://localhost:5601 | - |
| **Prometheus** | http://localhost:9090 | - |

---

## Estrutura de Diretórios

```
sandbox-ravena/
├── setup.bat                    # Configuração automática
├── start_sandbox.bat           # Iniciar sandbox
├── stop_sandbox.bat            # Parar sandbox
├── cleanup.bat                 # Limpar dados
├── verify_sandbox.bat          # Verificar sandbox
├── app.py                      # Servidor principal
├── docker-compose.yml          # Configuração Docker
├── tests/
│   └── security_tests.py       # Testes de segurança
├── monitoring/
│   ├── generate_report.py      # Gerador de relatórios
│   └── grafana/
│       └── dashboard.json      # Dashboard Grafana
└── README.md                   # Documentação
```

---

## Comandos Úteis

### Docker
```batch
# Ver status dos containers
docker-compose ps

# Ver logs
docker-compose logs -f

# Reiniciar serviço
docker-compose restart ravena-app

# Parar tudo
docker-compose down
```

### Python
```batch
# Ver estatísticas
python utils.py --stats

# Ver ataques recentes
python utils.py --attacks 50

# Exportar logs
python utils.py --export
```

---

## Solução de Problemas

### Docker não inicia
1. Abra o Docker Desktop
2. Aguarde inicializar
3. Execute `docker ps` para verificar

### Porta já em uso
```batch
# Verificar processo
netstat -ano | findstr :8080

# Matar processo
taskkill /PID <PID> /F
```

### Container não inicia
```batch
# Ver logs
docker-compose logs ravena-app

# Reiniciar
docker-compose down
docker-compose up -d
```

### Banco não conecta
```batch
# Reiniciar banco
docker-compose restart ravena-db

# Aguardar 10 segundos
timeout /t 10

# Verificar logs
docker-compose logs ravena-db
```

---

## Notas Importantes

1. **Docker Desktop deve estar rodando** antes de executar os scripts
2. **Aguarde a inicialização completa** (aproximadamente 30 segundos)
3. **Todas as portas devem estar livres** (8080, 80, 3000, 5601, 9090, 9200, 5432, 6379)
4. **Os dados são fictícios** - não há dados reais de usuários
5. **A sandbox é isolada** - não há acesso à internet externa

---

## Suporte

Se encontrar problemas:
1. Execute `verify_sandbox.bat` para diagnóstico
2. Verifique os logs em `docker-compose logs`
3. Reinicie o Docker Desktop
4. Consulte o `GUIA_COMPLETO.md` para mais detalhes
