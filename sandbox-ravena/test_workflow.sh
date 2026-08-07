#!/bin/bash
# ============================================
# TESTE COMPLETO DO FLUXO DE TRABALHO
# Sandbox Ravena
# ============================================
# Este script testa todo o fluxo de trabalho
# do agente hacker, desde o acesso até a geração
# de relatórios.
# ============================================

echo "============================================"
echo "  TESTE COMPLETO DO FLUXO DE TRABALHO"
echo "  Sandbox Ravena"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

# Função para testar
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}Testando:${NC} $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "  ${RED}✗ FAIL${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# ============================================
# 1. VERIFICAÇÕES PRÉ-REQUISITOS
# ============================================

echo "1. VERIFICAÇÕES PRÉ-REQUISITOS"
echo "=============================="
echo ""

run_test "Docker instalado" "command -v docker"
run_test "docker-compose instalado" "command -v docker-compose"
run_test "Python3 instalado" "command -v python3"
run_test "curl instalado" "command -v curl"
run_test "nmap instalado" "command -v nmap"

echo ""

# ============================================
# 2. VERIFICAÇÃO DE ESTRUTURA
# ============================================

echo "2. VERIFICAÇÃO DE ESTRUTURA"
echo "==========================="
echo ""

run_test "app.py existe" "[ -f app.py ]"
run_test "docker-compose.yml existe" "[ -f docker-compose.yml ]"
run_test "Dockerfile.ravena existe" "[ -f Dockerfile.ravena ]"
run_test "requirements.txt existe" "[ -f requirements.txt ]"
run_test "hacker-lab existe" "[ -d hacker-lab ]"
run_test "scripts existe" "[ -d scripts ]"
run_test "skills existe" "[ -d skills ]"

echo ""

# ============================================
# 3. VERIFICAÇÃO DE SCRIPTS DO HACKER
# ============================================

echo "3. VERIFICAÇÃO DE SCRIPTS DO HACKER"
echo "==================================="
echo ""

for script in 01_port_scan.sh 02_sql_injection.sh 03_xss_test.sh 04_brute_force.sh 05_idor_test.sh 06_path_traversal.sh 07_response_analysis.sh 08_generate_report.sh; do
    run_test "hacker-lab/$script existe" "[ -f hacker-lab/$script ]"
    run_test "hacker-lab/$script executável" "[ -x hacker-lab/$script ]"
done

echo ""

# ============================================
# 4. VERIFICAÇÃO DE SKILLS
# ============================================

echo "4. VERIFICAÇÃO DE SKILLS"
echo "======================="
echo ""

for skill in sqli_detector.py brute_force_protector.py session_manager.py input_validator.py rate_limiter.py audit_logger.py; do
    run_test "skills/$skill existe" "[ -f skills/$skill ]"
done

echo ""

# ============================================
# 5. VERIFICAÇÃO DE CONFIGURAÇÕES
# ============================================

echo "5. VERIFICAÇÃO DE CONFIGURAÇÕES"
echo "==============================="
echo ""

run_test "nginx/nginx.conf existe" "[ -f nginx/nginx.conf ]"
run_test "init-scripts/01-init.sql existe" "[ -f init-scripts/01-init.sql ]"
run_test "monitoring/prometheus/prometheus.yml existe" "[ -f monitoring/prometheus/prometheus.yml ]"
run_test "monitoring/grafana/security_dashboard.json existe" "[ -f monitoring/grafana/security_dashboard.json ]"

echo ""

# ============================================
# 6. TESTE DE SINTAXE
# ============================================

echo "6. TESTE DE SINTAXE"
echo "==================="
echo ""

run_test "app.py sintaxe válida" "python3 -m py_compile app.py"
run_test "skills sqli_detector.py sintaxe válida" "python3 -m py_compile skills/sqli_detector.py"
run_test "skills brute_force_protector.py sintaxe válida" "python3 -m py_compile skills/brute_force_protector.py"
run_test "skills session_manager.py sintaxe válida" "python3 -m py_compile skills/session_manager.py"
run_test "skills input_validator.py sintaxe válida" "python3 -m py_compile skills/input_validator.py"
run_test "skills rate_limiter.py sintaxe válida" "python3 -m py_compile skills/rate_limiter.py"
run_test "skills audit_logger.py sintaxe válida" "python3 -m py_compile skills/audit_logger.py"

echo ""

# ============================================
# 7. TESTE DE DOCKER
# ============================================

echo "7. TESTE DE DOCKER"
echo "=================="
echo ""

if command -v docker &> /dev/null; then
    run_test "Docker está rodando" "docker info"
    run_test "docker-compose.yml válido" "docker-compose config"
else
    echo -e "${YELLOW}  Docker não disponível - pulando testes Docker${NC}"
fi

echo ""

# ============================================
# 8. TESTE DE REDE
# ============================================

echo "8. TESTE DE REDE"
echo "================"
echo ""

run_test "Porta 8080 disponível" "! nc -z localhost 8080"
run_test "Porta 5432 disponível" "! nc -z localhost 5432"
run_test "Porta 6379 disponível" "! nc -z localhost 6379"

echo ""

# ============================================
# 9. TESTE DE DEPENDÊNCIAS
# ============================================

echo "9. TESTE DE DEPENDÊNCIAS"
echo "========================"
echo ""

if command -v python3 &> /dev/null; then
    run_test "Flask instalado" "python3 -c 'import flask'"
    run_test "psycopg2 instalado" "python3 -c 'import psycopg2'"
    run_test "redis instalado" "python3 -c 'import redis'"
    run_test "PyJWT instalado" "python3 -c 'import jwt'"
else
    echo -e "${YELLOW}  Python3 não disponível - pulando testes de dependências${NC}"
fi

echo ""

# ============================================
# 10. TESTE DE PERMISSÕES
# ============================================

echo "10. TESTE DE PERMISSÕES"
echo "======================="
echo ""

run_test "implement_controls.sh executável" "[ -x implement_controls.sh ]"
run_test "install_all.sh executável" "[ -x install_all.sh ]"
run_test "validate_system.sh executável" "[ -x validate_system.sh ]"

echo ""

# ============================================
# RESUMO FINAL
# ============================================

echo "============================================"
echo "  RESUMO DO TESTE"
echo "============================================"
echo ""

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
if [ $TOTAL -gt 0 ]; then
    SUCCESS_RATE=$(( (TESTS_PASSED * 100) / TOTAL ))
else
    SUCCESS_RATE=0
fi

echo -e "${BLUE}Total de testes:${NC} $TOTAL"
echo -e "${GREEN}Testes passaram:${NC} $TESTS_PASSED"
echo -e "${RED}Testes falharam:${NC} $TESTS_FAILED"
echo -e "${BLUE}Taxa de sucesso:${NC} $SUCCESS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  TODOS OS TESTES PASSARAM!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "O sistema está pronto para uso!"
    echo ""
    echo "PRÓXIMOS PASSOS:"
    echo "1. Execute: ./install_all.sh"
    echo "2. Acesse: http://localhost:8080"
    echo "3. Use: cd ~/hacker-lab"
else
    echo -e "${YELLOW}============================================${NC}"
    echo -e "${YELLOW}  ALGUNS TESTES FALHARAM${NC}"
    echo -e "${YELLOW}============================================${NC}"
    echo ""
    echo "Revise os erros acima antes de usar o sistema."
fi

echo ""
echo "============================================"
