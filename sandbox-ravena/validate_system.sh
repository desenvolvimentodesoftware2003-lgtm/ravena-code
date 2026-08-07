#!/bin/bash
# ============================================
# SCRIPT: Validação Completa do Sistema
# Sandbox Ravena
# ============================================
# Este script verifica se tudo está funcionando
# corretamente, identificando bugs, falhas e erros.
# ============================================

echo "============================================"
echo "  VALIDAÇÃO COMPLETA DO SISTEMA"
echo "  Sandbox Ravena"
echo "============================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNING_TESTS=0

# Função para registrar teste
test_pass() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "${GREEN}  ✓ PASS${NC}: $1"
}

test_fail() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}  ✗ FAIL${NC}: $1"
}

test_warning() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    WARNING_TESTS=$((WARNING_TESTS + 1))
    echo -e "${YELLOW}  ⚠ WARN${NC}: $1"
}

test_info() {
    echo -e "${BLUE}  ℹ INFO${NC}: $1"
}

# ============================================
# 1. VERIFICAÇÃO DE ARQUIVOS
# ============================================

echo "1. VERIFICAÇÃO DE ARQUIVOS"
echo "=========================="
echo ""

# Arquivos principais
echo "Arquivos principais:"

if [ -f "app.py" ]; then
    test_pass "app.py existe"
else
    test_fail "app.py não encontrado"
fi

if [ -f "docker-compose.yml" ]; then
    test_pass "docker-compose.yml existe"
else
    test_fail "docker-compose.yml não encontrado"
fi

if [ -f "Dockerfile.ravena" ]; then
    test_pass "Dockerfile.ravena existe"
else
    test_fail "Dockerfile.ravena não encontrado"
fi

if [ -f "requirements.txt" ]; then
    test_pass "requirements.txt existe"
else
    test_fail "requirements.txt não encontrado"
fi

if [ -f "implement_controls.sh" ]; then
    test_pass "implement_controls.sh existe"
else
    test_fail "implement_controls.sh não encontrado"
fi

if [ -f "CONTROLES_ACESSO.md" ]; then
    test_pass "CONTROLES_ACESSO.md existe"
else
    test_fail "CONTROLES_ACESSO.md não encontrado"
fi

if [ -f "RESUMO_IMPLEMENTACAO.md" ]; then
    test_pass "RESUMO_IMPLEMENTACAO.md existe"
else
    test_fail "RESUMO_IMPLEMENTACAO.md não encontrado"
fi

if [ -f "RESUMO_TRANSICAO.md" ]; then
    test_pass "RESUMO_TRANSICAO.md existe"
else
    test_fail "RESUMO_TRANSICAO.md não encontrado"
fi

echo ""

# ============================================
# 2. VERIFICAÇÃO DE DIRETÓRIOS
# ============================================

echo "2. VERIFICAÇÃO DE DIRETÓRIOS"
echo "============================"
echo ""

if [ -d "hacker-lab" ]; then
    test_pass "Diretório hacker-lab existe"
else
    test_fail "Diretório hacker-lab não encontrado"
fi

if [ -d "scripts" ]; then
    test_pass "Diretório scripts existe"
else
    test_fail "Diretório scripts não encontrado"
fi

if [ -d "skills" ]; then
    test_pass "Diretório skills existe"
else
    test_fail "Diretório skills não encontrado"
fi

if [ -d "monitoring" ]; then
    test_pass "Diretório monitoring existe"
else
    test_fail "Diretório monitoring não encontrado"
fi

if [ -d "config" ]; then
    test_pass "Diretório config existe"
else
    test_fail "Diretório config não encontrado"
fi

if [ -d "nginx" ]; then
    test_pass "Diretório nginx existe"
else
    test_fail "Diretório nginx não encontrado"
fi

if [ -d "init-scripts" ]; then
    test_pass "Diretório init-scripts existe"
else
    test_fail "Diretório init-scripts não encontrado"
fi

echo ""

# ============================================
# 3. VERIFICAÇÃO DE SCRIPTS DO HACKER-LAB
# ============================================

echo "3. VERIFICAÇÃO DE SCRIPTS DO HACKER-LAB"
echo "======================================="
echo ""

if [ -f "hacker-lab/setup_lab.sh" ]; then
    test_pass "hacker-lab/setup_lab.sh existe"
    if [ -x "hacker-lab/setup_lab.sh" ]; then
        test_pass "hacker-lab/setup_lab.sh é executável"
    else
        test_warning "hacker-lab/setup_lab.sh não é executável"
    fi
else
    test_fail "hacker-lab/setup_lab.sh não encontrado"
fi

for script in 01_port_scan.sh 02_sql_injection.sh 03_xss_test.sh 04_brute_force.sh 05_idor_test.sh 06_path_traversal.sh 07_response_analysis.sh 08_generate_report.sh; do
    if [ -f "hacker-lab/$script" ]; then
        test_pass "hacker-lab/$script existe"
        if [ -x "hacker-lab/$script" ]; then
            test_pass "hacker-lab/$script é executável"
        else
            test_warning "hacker-lab/$script não é executável"
        fi
    else
        test_fail "hacker-lab/$script não encontrado"
    fi
done

if [ -f "hacker-lab/README.md" ]; then
    test_pass "hacker-lab/README.md existe"
else
    test_fail "hacker-lab/README.md não encontrado"
fi

echo ""

# ============================================
# 4. VERIFICAÇÃO DE SCRIPTS DE MONITORAMENTO
# ============================================

echo "4. VERIFICAÇÃO DE SCRIPTS DE MONITORAMENTO"
echo "=========================================="
echo ""

for script in setup_monitoring.sh setup_audit.sh setup_isolation.sh verify_isolation.sh monitor_traffic.sh audit_daily.sh audit_weekly.sh audit_monthly.sh; do
    if [ -f "scripts/$script" ]; then
        test_pass "scripts/$script existe"
        if [ -x "scripts/$script" ]; then
            test_pass "scripts/$script é executável"
        else
            test_warning "scripts/$script não é executável"
        fi
    else
        test_fail "scripts/$script não encontrado"
    fi
done

echo ""

# ============================================
# 5. VERIFICAÇÃO DE SKILLS
# ============================================

echo "5. VERIFICAÇÃO DE SKILLS"
echo "========================"
echo ""

for skill in sqli_detector.py brute_force_protector.py session_manager.py input_validator.py rate_limiter.py audit_logger.py; do
    if [ -f "skills/$skill" ]; then
        test_pass "skills/$skill existe"
    else
        test_fail "skills/$skill não encontrado"
    fi
done

echo ""

# ============================================
# 6. VERIFICAÇÃO DE CONFIGURAÇÕES
# ============================================

echo "6. VERIFICAÇÃO DE CONFIGURAÇÕES"
echo "==============================="
echo ""

if [ -f "nginx/nginx.conf" ]; then
    test_pass "nginx/nginx.conf existe"
else
    test_fail "nginx/nginx.conf não encontrado"
fi

if [ -f "init-scripts/01-init.sql" ]; then
    test_pass "init-scripts/01-init.sql existe"
else
    test_fail "init-scripts/01-init.sql não encontrado"
fi

if [ -f "monitoring/prometheus/prometheus.yml" ]; then
    test_pass "monitoring/prometheus/prometheus.yml existe"
else
    test_fail "monitoring/prometheus/prometheus.yml não encontrado"
fi

if [ -f "monitoring/prometheus/alert_rules.yml" ]; then
    test_pass "monitoring/prometheus/alert_rules.yml existe"
else
    test_fail "monitoring/prometheus/alert_rules.yml não encontrado"
fi

if [ -f "monitoring/grafana/security_dashboard.json" ]; then
    test_pass "monitoring/grafana/security_dashboard.json existe"
else
    test_fail "monitoring/grafana/security_dashboard.json não encontrado"
fi

echo ""

# ============================================
# 7. VERIFICAÇÃO DE SINTAXE DO APP.PY
# ============================================

echo "7. VERIFICAÇÃO DE SINTAXE DO APP.PY"
echo "===================================="
echo ""

if command -v python3 &> /dev/null; then
    if python3 -m py_compile app.py 2>/dev/null; then
        test_pass "app.py tem sintaxe válida"
    else
        test_fail "app.py tem erro de sintaxe"
    fi
    
    # Verificar se há importações que podem dar erro
    if python3 -c "import flask" 2>/dev/null; then
        test_pass "Flask está instalado"
    else
        test_warning "Flask não está instalado (será necessário instalar)"
    fi
    
    if python3 -c "import jwt" 2>/dev/null; then
        test_pass "PyJWT está instalado"
    else
        test_warning "PyJWT não está instalado (será necessário instalar)"
    fi
    
    if python3 -c "import psycopg2" 2>/dev/null; then
        test_pass "psycopg2 está instalado"
    else
        test_warning "psycopg2 não está instalado (será necessário instalar)"
    fi
    
    if python3 -c "import redis" 2>/dev/null; then
        test_pass "redis está instalado"
    else
        test_warning "redis não está instalado (será necessário instalar)"
    fi
else
    test_warning "Python3 não encontrado - não foi possível verificar sintaxe"
fi

echo ""

# ============================================
# 8. VERIFICAÇÃO DE DOCKER-COMPOSE
# ============================================

echo "8. VERIFICAÇÃO DE DOCKER-COMPOSE"
echo "================================"
echo ""

if command -v docker &> /dev/null; then
    test_pass "Docker está instalado"
else
    test_fail "Docker não está instalado"
fi

if command -v docker-compose &> /dev/null; then
    test_pass "docker-compose está instalado"
else
    test_fail "docker-compose não está instalado"
fi

if [ -f "docker-compose.yml" ]; then
    # Verificar se o docker-compose.yml é válido
    if command -v docker-compose &> /dev/null; then
        if docker-compose config > /dev/null 2>&1; then
            test_pass "docker-compose.yml é válido"
        else
            test_fail "docker-compose.yml tem erro de formatação"
        fi
    else
        test_warning "Não foi possível validar docker-compose.yml (docker-compose não instalado)"
    fi
fi

echo ""

# ============================================
# 9. VERIFICAÇÃO DE SEGURANÇA
# ============================================

echo "9. VERIFICAÇÃO DE SEGURANÇA"
echo "==========================="
echo ""

# Verificar se há senhas hardcoded no app.py
if grep -q "password.*=.*['\"].*['\"]" app.py 2>/dev/null; then
    test_warning "Possíveis senhas hardcoded encontradas no app.py"
else
    test_pass "Nenhuma senha hardcoded encontrada no app.py"
fi

# Verificar se há debug=True (perigoso em produção)
if grep -q "debug=True" app.py 2>/dev/null; then
    test_warning "debug=True encontrado no app.py (perigoso em produção)"
else
    test_pass "Nenhum debug=True encontrado no app.py"
fi

# Verificar se há rotas sensíveis expostas
if grep -q "@app.route.*admin" app.py 2>/dev/null; then
    test_info "Rotas de admin encontradas (verificar autenticação)"
else
    test_pass "Nenhuma rota de admin exposta"
fi

echo ""

# ============================================
# 10. VERIFICAÇÃO DE INTEGRIDADE
# ============================================

echo "10. VERIFICAÇÃO DE INTEGRIDADE"
echo "=============================="
echo ""

# Verificar se o app.py tem as rotas esperadas
if grep -q "@app.route" app.py 2>/dev/null; then
    test_pass "Rotas encontradas no app.py"
else
    test_fail "Nenhuma rota encontrada no app.py"
fi

# Verificar se o app.py tem as configurações de banco
if grep -q "get_db()" app.py 2>/dev/null; then
    test_pass "Função de banco de dados encontrada"
else
    test_fail "Função de banco de dados não encontrada"
fi

# Verificar se o app.py tem as configurações de Redis
if grep -q "redis" app.py 2>/dev/null; then
    test_pass "Configurações de Redis encontradas"
else
    test_warning "Configurações de Redis não encontradas"
fi

# Verificar se o app.py tem as configurações de JWT
if grep -q "jwt" app.py 2>/dev/null; then
    test_pass "Configurações de JWT encontradas"
else
    test_fail "Configurações de JWT não encontradas"
fi

# Verificar se o app.py tem as rotas de autenticação
if grep -q "@app.route.*login" app.py 2>/dev/null; then
    test_pass "Rota de login encontrada"
else
    test_fail "Rota de login não encontrada"
fi

# Verificar se o app.py tem as rotas de saque
if grep -q "@app.route.*withdrawal" app.py 2>/dev/null; then
    test_pass "Rotas de saque encontradas"
else
    test_fail "Rotas de saque não encontradas"
fi

# Verificar se o app.py tem as rotas de slots
if grep -q "@app.route.*slot" app.py 2>/dev/null; then
    test_pass "Rotas de slots encontradas"
else
    test_fail "Rotas de slots não encontradas"
fi

echo ""

# ============================================
# 11. VERIFICAÇÃO DE DOCUMENTAÇÃO
# ============================================

echo "11. VERIFICAÇÃO DE DOCUMENTAÇÃO"
echo "==============================="
echo ""

# Verificar se CONTROLES_ACESSO.md tem a nova abordagem
if grep -q "ferramentas normais de sistema operacional" CONTROLES_ACESSO.md 2>/dev/null; then
    test_pass "CONTROLES_ACESSO.md atualizado com nova abordagem"
else
    test_fail "CONTROLES_ACESSO.md não está atualizado"
fi

# Verificar se RESUMO_IMPLEMENTACAO.md tem a nova abordagem
if grep -q "LABORATÓRIO DO AGENTE HACKER" RESUMO_IMPLEMENTACAO.md 2>/dev/null; then
    test_pass "RESUMO_IMPLEMENTACAO.md atualizado com nova abordagem"
else
    test_fail "RESUMO_IMPLEMENTACAO.md não está atualizado"
fi

# Verificar se há referências antigas
if grep -q "/api/agent/hacker" CONTROLES_ACESSO.md 2>/dev/null; then
    test_fail "Referência antiga a /api/agent/hacker encontrada em CONTROLES_ACESSO.md"
else
    test_pass "Nenhuma referência antiga a /api/agent/hacker em CONTROLES_ACESSO.md"
fi

if grep -q "/api/agent/hacker" RESUMO_IMPLEMENTACAO.md 2>/dev/null; then
    test_fail "Referência antiga a /api/agent/hacker encontrada em RESUMO_IMPLEMENTACAO.md"
else
    test_pass "Nenhuma referência antiga a /api/agent/hacker em RESUMO_IMPLEMENTACAO.md"
fi

echo ""

# ============================================
# 12. VERIFICAÇÃO DE PERMISSÕES
# ============================================

echo "12. VERIFICAÇÃO DE PERMISSÕES"
echo "============================="
echo ""

# Verificar permissões dos scripts
for script in implement_controls.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            test_pass "$script é executável"
        else
            test_warning "$script não é executável"
        fi
    fi
done

# Verificar permissões dos scripts do hacker-lab
for script in hacker-lab/*.sh; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            test_pass "$script é executável"
        else
            test_warning "$script não é executável"
        fi
    fi
done

echo ""

# ============================================
# 13. VERIFICAÇÃO DE DEPENDÊNCIAS
# ============================================

echo "13. VERIFICAÇÃO DE DEPENDÊNCIAS"
echo "==============================="
echo ""

if [ -f "requirements.txt" ]; then
    test_pass "requirements.txt existe"
    
    # Verificar dependências principais
    if grep -q "flask" requirements.txt 2>/dev/null; then
        test_pass "Flask está nas dependências"
    else
        test_fail "Flask não está nas dependências"
    fi
    
    if grep -q "psycopg2" requirements.txt 2>/dev/null; then
        test_pass "psycopg2 está nas dependências"
    else
        test_fail "psycopg2 não está nas dependências"
    fi
    
    if grep -q "redis" requirements.txt 2>/dev/null; then
        test_pass "redis está nas dependências"
    else
        test_fail "redis não está nas dependências"
    fi
    
    if grep -qi "pyjwt" requirements.txt 2>/dev/null; then
        test_pass "PyJWT está nas dependências"
    else
        test_fail "PyJWT não está nas dependências"
    fi
else
    test_fail "requirements.txt não encontrado"
fi

echo ""

# ============================================
# RESUMO FINAL
# ============================================

echo "============================================"
echo "  RESUMO DA VALIDAÇÃO"
echo "============================================"
echo ""

echo -e "${BLUE}Total de testes:${NC} $TOTAL_TESTS"
echo -e "${GREEN}Testes passaram:${NC} $PASSED_TESTS"
echo -e "${RED}Testes falharam:${NC} $FAILED_TESTS"
echo -e "${YELLOW}Avisos:${NC} $WARNING_TESTS"
echo ""

# Calcular porcentagem de sucesso
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo -e "${BLUE}Taxa de sucesso:${NC} $SUCCESS_RATE%"
else
    echo -e "${RED}Nenhum teste executado${NC}"
fi

echo ""

# Status geral
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  SISTEMA VALIDADO COM SUCESSO${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Todos os testes passaram com sucesso!"
    echo "O sistema está pronto para uso."
else
    echo -e "${RED}============================================${NC}"
    echo -e "${RED}  PROBLEMAS ENCONTRADOS${NC}"
    echo -e "${RED}============================================${NC}"
    echo ""
    echo "Foram encontrados $FAILED_TESTS problema(s) que precisam de correção."
    echo "Revise os erros acima antes de usar o sistema."
fi

echo ""

# ============================================
# RECOMENDAÇÕES
# ============================================

if [ $WARNING_TESTS -gt 0 ]; then
    echo -e "${YELLOW}RECOMENDAÇÕES:${NC}"
    echo ""
    echo "1. Revise os avisos acima"
    echo "2. Instale dependências faltantes: pip install -r requirements.txt"
    echo "3. Torne os scripts executáveis: chmod +x *.sh"
    echo "4. Valide o docker-compose.yml antes de usar"
    echo ""
fi

if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}PRÓXIMOS PASSOS:${NC}"
    echo ""
    echo "1. Corrija os erros listados acima"
    echo "2. Execute novamente: ./validate_system.sh"
    echo "3. Verifique a documentação em CONTROLES_ACESSO.md"
    echo ""
fi

echo "============================================"
echo "  FIM DA VALIDAÇÃO"
echo "============================================"
