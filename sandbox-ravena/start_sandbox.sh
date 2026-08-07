#!/bin/bash
# ============================================
# SCRIPT DE INICIALIZAÇÃO - SANDBOX RAVENA
# ============================================

echo "============================================"
echo "  INICIANDO SANDBOX RAVENA"
echo "  Ambiente Isolado para Testes de Segurança"
echo "============================================"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "[ERRO] Docker não está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "[ERRO] Docker Compose não está instalado"
    exit 1
fi

# Criar diretórios necessários
echo "[INFO] Criando estrutura de diretórios..."
mkdir -p logs/nginx
mkdir -p logs/redis
mkdir -p logs/postgres
mkdir -p data/postgres
mkdir -p data/elasticsearch
mkdir -p monitoring/grafana

# Verificar se a porta 8080 está disponível
if netstat -tuln | grep -q ":8080"; then
    echo "[AVISO] Porta 8080 já está em uso"
    echo "[INFO] Parando serviço na porta 8080..."
    fuser -k 8080/tcp 2>/dev/null
fi

# Iniciar containers
echo "[INFO] Iniciando containers Docker..."
docker-compose up -d

# Aguardar serviços inicializarem
echo "[INFO] Aguardando serviços inicializarem..."
sleep 10

# Verificar status dos containers
echo "[INFO] Verificando status dos containers..."
docker-compose ps

# Verificar health check
echo "[INFO] Verificando health check..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health | grep -q "healthy"; then
        echo "[OK] Servidor Ravena está saudável"
        break
    fi
    echo "[INFO] Aguardando servidor... ($i/30)"
    sleep 2
done

# Exibir informações de acesso
echo ""
echo "============================================"
echo "  SANDBOX INICIADA COM SUCESSO"
echo "============================================"
echo ""
echo "SERVIÇOS DISPONÍVEIS:"
echo "  - Servidor Ravena:  http://localhost:8080"
echo "  - Nginx:            http://localhost:80"
echo "  - Grafana:          http://localhost:3000"
echo "  - Kibana:           http://localhost:5601"
echo "  - PostgreSQL:       localhost:5432"
echo ""
echo "CREDENCIAIS:"
echo "  - Usuário teste:    attacker_001"
echo "  - Senha:            test123"
echo "  - Admin:            admin_test"
echo "  - Senha admin:      admin123"
echo ""
echo "PARA EXECUTAR TESTES:"
echo "  python tests/security_tests.py"
echo ""
echo "PARA PARAR A SANDBOX:"
echo "  docker-compose down"
echo ""
echo "============================================"
