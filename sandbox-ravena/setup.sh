#!/bin/bash
# ============================================
# CONFIGURAÇÃO AUTOMÁTICA - SANDBOX RAVENA
# ============================================

echo "============================================"
echo "  CONFIGURAÇÃO AUTOMÁTICA"
echo "  Sandbox Ravena"
echo "============================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.yml" ]; then
    echo "[ERRO] Execute este script no diretório sandbox-ravena"
    exit 1
fi

# Fase 1: Verificar pré-requisitos
echo "[FASE 1] Verificando pré-requisitos..."
echo "----------------------------------------"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "[ERRO] Docker não está instalado"
    echo "[INFO] Instale Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "[ERRO] Docker Compose não está instalado"
    echo "[INFO] Instale Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não está instalado"
    echo "[INFO] Instale Python: https://www.python.org/downloads/"
    exit 1
fi

echo "[OK] Todos os pré-requisitos estão instalados"
echo ""

# Fase 2: Instalar dependências Python
echo "[FASE 2] Instalando dependências Python..."
echo "----------------------------------------"

pip install -r requirements.txt
pip install psycopg2-binary jinja2 requests

echo "[OK] Dependências instaladas"
echo ""

# Fase 3: Criar diretórios
echo "[FASE 3] Criando estrutura de diretórios..."
echo "----------------------------------------"

mkdir -p logs/nginx
mkdir -p logs/redis
mkdir -p logs/postgres
mkdir -p data/postgres
mkdir -p data/elasticsearch
mkdir -p monitoring/grafana

echo "[OK] Diretórios criados"
echo ""

# Fase 4: Copiar variáveis de ambiente
echo "[FASE 4] Configurando variáveis de ambiente..."
echo "----------------------------------------"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[OK] Arquivo .env criado"
else
    echo "[INFO] Arquivo .env já existe"
fi

echo ""

# Fase 5: Verificar portas
echo "[FASE 5] Verificando portas..."
echo "----------------------------------------"

ports=(8080 80 3000 5601 9090 9200 5432 6379)
ports_available=true

for port in "${ports[@]}"; do
    if netstat -tuln | grep -q ":$port"; then
        echo "[AVISO] Porta $port já está em uso"
        ports_available=false
    fi
done

if [ "$ports_available" = false ]; then
    echo ""
    echo "[AVISO] Algumas portas estão em uso"
    echo "[INFO] Certifique-se de que as portas estão disponíveis"
    echo ""
    read -p "Deseja continuar mesmo assim? (s/n): " continue_anyway
    if [ "$continue_anyway" != "s" ]; then
        echo "[INFO] Configuração cancelada"
        exit 0
    fi
else
    echo "[OK] Todas as portas estão disponíveis"
fi

echo ""

# Fase 6: Iniciar containers
echo "[FASE 6] Iniciando containers Docker..."
echo "----------------------------------------"

docker-compose up -d

echo "[OK] Containers iniciados"
echo ""

# Fase 7: Aguardar inicialização
echo "[FASE 7] Aguardando serviços inicializarem..."
echo "----------------------------------------"

echo "Aguardando 30 segundos para inicialização completa..."
sleep 30

# Verificar se o servidor está respondendo
for i in {1..30}; do
    if curl -s http://localhost:8080/health | grep -q "healthy"; then
        echo "[OK] Servidor Ravena está saudável"
        break
    fi
    echo "[INFO] Aguardando servidor... ($i/30)"
    sleep 2
done

echo ""

# Fase 8: Executar testes básicos
echo "[FASE 8] Executando testes básicos..."
echo "----------------------------------------"

# Verificar se o servidor está rodando
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "[OK] Servidor respondendo"
else
    echo "[ERRO] Servidor não está respondendo"
fi

# Verificar banco de dados
if docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "SELECT 1;" > /dev/null 2>&1; then
    echo "[OK] Banco de dados conectado"
else
    echo "[ERRO] Falha na conexão com banco"
fi

echo ""

# Fase 9: Gerar relatório inicial
echo "[FASE 9] Gerando relatório inicial..."
echo "----------------------------------------"

python monitoring/generate_report.py

echo ""

# Resumo final
echo "============================================"
echo "  CONFIGURAÇÃO CONCLUÍDA"
echo "============================================"
echo ""
echo "SANDBOX RAVENA ESTÁ PRONTA!"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Acesse a aplicação: http://localhost:8080"
echo "2. Execute os testes: python tests/security_tests.py"
echo "3. Acesse o Grafana: http://localhost:3000"
echo "4. Acesse o Kibana: http://localhost:5601"
echo ""
echo "COMANDOS ÚTEIS:"
echo "- Verificar sandbox: ./verify_sandbox.sh"
echo "- Parar sandbox: ./stop_sandbox.sh"
echo "- Limpar dados: ./cleanup.sh"
echo ""
echo "CREDENCIAIS:"
echo "- Aplicação: attacker_001 / test123"
echo "- Grafana: admin / sandbox_monitor_123"
echo "- Banco: ravena_test / sandbox_password_123"
echo ""
echo "============================================"
