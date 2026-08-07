#!/bin/bash
# ============================================
# SCRIPT DE VERIFICAÇÃO - SANDBOX RAVENA
# ============================================

echo "============================================"
echo "  VERIFICAÇÃO DA SANDBOX RAVENA"
echo "============================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar serviço
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=$3
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}[✓]${NC} $service_name está funcionando"
        return 0
    else
        echo -e "${RED}[✗]${NC} $service_name não está funcionando"
        return 1
    fi
}

# Função para verificar container
check_container() {
    local container_name=$1
    
    if docker ps --format '{{.Names}}' | grep -q "$container_name"; then
        echo -e "${GREEN}[✓]${NC} Container $container_name está rodando"
        return 0
    else
        echo -e "${RED}[✗]${NC} Container $container_name não está rodando"
        return 1
    fi
}

# Contadores
total_checks=0
passed_checks=0

# ============================================
# VERIFICAÇÕES
# ============================================

echo "1. Verificando containers..."
echo "----------------------------------------"

containers=("ravena-app" "ravena-db" "ravena-redis" "ravena-nginx" "ravena-elasticsearch" "ravena-kibana")

for container in "${containers[@]}"; do
    total_checks=$((total_checks + 1))
    if check_container "$container"; then
        passed_checks=$((passed_checks + 1))
    fi
done

echo ""
echo "2. Verificando serviços..."
echo "----------------------------------------"

# Verificar servidor principal
total_checks=$((total_checks + 1))
if check_service "Servidor Ravena" "http://localhost:8080/health" "200"; then
    passed_checks=$((passed_checks + 1))
fi

# Verificar Grafana
total_checks=$((total_checks + 1))
if check_service "Grafana" "http://localhost:3000/api/health" "200"; then
    passed_checks=$((passed_checks + 1))
fi

# Verificar Kibana
total_checks=$((total_checks + 1))
if check_service "Kibana" "http://localhost:5601/api/status" "200"; then
    passed_checks=$((passed_checks + 1))
fi

# Verificar Prometheus
total_checks=$((total_checks + 1))
if check_service "Prometheus" "http://localhost:9090/-/healthy" "200"; then
    passed_checks=$((passed_checks + 1))
fi

# Verificar Elasticsearch
total_checks=$((total_checks + 1))
if check_service "Elasticsearch" "http://localhost:9200/_cluster/health" "200"; then
    passed_checks=$((passed_checks + 1))
fi

echo ""
echo "3. Verificando banco de dados..."
echo "----------------------------------------"

# Verificar conexão com banco
total_checks=$((total_checks + 1))
if docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}[✓]${NC} Conexão com banco de dados OK"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}[✗]${NC} Falha na conexão com banco de dados"
fi

# Verificar tabelas
total_checks=$((total_checks + 1))
if docker exec -it ravena-db psql -U ravena_test -d ravena_sandbox -c "\dt" > /dev/null 2>&1; then
    echo -e "${GREEN}[✓]${NC} Tabelas do banco OK"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}[✗]${NC} Falha ao acessar tabelas"
fi

echo ""
echo "4. Verificando dependências Python..."
echo "----------------------------------------"

# Verificar Python
total_checks=$((total_checks + 1))
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} Python3 instalado"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}[✗]${NC} Python3 não encontrado"
fi

# Verificar dependências
total_checks=$((total_checks + 1))
if python3 -c "import requests, psycopg2, json" 2>/dev/null; then
    echo -e "${GREEN}[✓]${NC} Dependências Python OK"
    passed_checks=$((passed_checks + 1))
else
    echo -e "${RED}[✗]${NC} Dependências Python faltando"
fi

echo ""
echo "5. Verificando portas..."
echo "----------------------------------------"

ports=(8080 80 3000 5601 9090 9200 5432 6379)

for port in "${ports[@]}"; do
    total_checks=$((total_checks + 1))
    if netstat -tuln | grep -q ":$port"; then
        echo -e "${GREEN}[✓]${NC} Porta $port está em uso"
        passed_checks=$((passed_checks + 1))
    else
        echo -e "${YELLOW}[!]${NC} Porta $port não está em uso"
    fi
done

echo ""
echo "============================================"
echo "  RESULTADO DA VERIFICAÇÃO"
echo "============================================"
echo ""

# Calcular porcentagem
percentage=$((passed_checks * 100 / total_checks))

# Exibir resultado
echo "Total de verificações: $total_checks"
echo "Verificações aprovadas: $passed_checks"
echo "Porcentagem: $percentage%"
echo ""

if [ $percentage -eq 100 ]; then
    echo -e "${GREEN}[✓] SANDBOX ESTÁ FUNCIONANDO PERFEITAMENTE${NC}"
elif [ $percentage -ge 80 ]; then
    echo -e "${YELLOW}[!] SANDBOX ESTÁ FUNCIONANDO COM ALERTAS${NC}"
else
    echo -e "${RED}[✗] SANDBOX ESTÁ COM PROBLEMAS${NC}"
fi

echo ""
echo "============================================"
echo "  PRÓXIMOS PASSOS"
echo "============================================"
echo ""

if [ $percentage -lt 100 ]; then
    echo "1. Verificar logs dos containers com problemas"
    echo "2. Reiniciar containers: docker-compose restart"
    echo "3. Verificar se todas as portas estão disponíveis"
    echo "4. Executar: ./start_sandbox.sh"
else
    echo "1. Executar testes: python tests/security_tests.py"
    echo "2. Gerar relatório: python monitoring/generate_report.py"
    echo "3. Acessar Grafana: http://localhost:3000"
    echo "4. Acessar Kibana: http://localhost:5601"
fi

echo ""
echo "============================================"
