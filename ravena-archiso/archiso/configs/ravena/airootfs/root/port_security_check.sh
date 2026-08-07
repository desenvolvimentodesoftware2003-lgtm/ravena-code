#!/bin/bash
# ============================================
# PORT_SECURITY_CHECK.SH - Verificação de Segurança
# Ravena Security Sandbox
# ============================================
# Verifica a segurança de todas as portas
# e recomenda ações.
# ============================================

echo "============================================"
echo "  VERIFICAÇÃO DE SEGURANÇA DAS PORTAS"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
SECURE=0
INSECURE=0
WARNING=0

# Função para verificar porta
check_port() {
    local port=$1
    local service=$2
    local encrypted=$3
    
    # Verificar se a porta está aberta
    if nc -z -w1 localhost $port 2>/dev/null; then
        if [ "$encrypted" = "YES" ]; then
            echo -e "  ${GREEN}✅ $port ($service) - CRIPTOGRAFADO${NC}"
            SECURE=$((SECURE + 1))
        else
            echo -e "  ${RED}❌ $port ($service) - NÃO CRIPTOGRAFADO${NC}"
            INSECURE=$((INSECURE + 1))
        fi
    else
        echo -e "  ${YELLOW}⚠️  $port ($service) - FECHADA${NC}"
        WARNING=$((WARNING + 1))
    fi
}

# ============================================
# VERIFICAR PORTAS
# ============================================

echo -e "${BLUE}Verificando portas...${NC}"
echo ""

# Portas abertas
check_port 22 "SSH" "YES"
check_port 80 "HTTP" "NO"
check_port 443 "HTTPS" "YES"
check_port 3000 "Grafana" "NO"
check_port 5432 "PostgreSQL" "YES"
check_port 5601 "Kibana" "NO"
check_port 6379 "Redis" "YES"
check_port 8080 "Ravena App" "NO"
check_port 9090 "Prometheus" "NO"
check_port 9200 "Elasticsearch" "YES"

echo ""

# ============================================
# VERIFICAR CERTIFICADOS
# ============================================

echo -e "${BLUE}Verificando certificados...${NC}"
echo ""

# Verificar SSL/TLS
if command -v openssl &> /dev/null; then
    echo -e "  ${GREEN}✅ OpenSSL instalado${NC}"
    
    # Verificar certificado SSL
    if [ -f "/etc/ssl/certs/ca-certificates.crt" ]; then
        echo -e "  ${GREEN}✅ Certificados CA instalados${NC}"
    else
        echo -e "  ${RED}❌ Certificados CA não encontrados${NC}"
    fi
else
    echo -e "  ${RED}❌ OpenSSL não instalado${NC}"
fi

echo ""

# ============================================
# VERIFICAR FIREWALL
# ============================================

echo -e "${BLUE}Verificando firewall...${NC}"
echo ""

# Verificar iptables
if command -v iptables &> /dev/null; then
    echo -e "  ${GREEN}✅ iptables instalado${NC}"
    
    # Verificar regras
    RULES=$(iptables -L -n 2>/dev/null | wc -l)
    if [ "$RULES" -gt 8 ]; then
        echo -e "  ${GREEN}✅ Regras de firewall configuradas${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Poucas regras de firewall${NC}"
    fi
else
    echo -e "  ${RED}❌ iptables não instalado${NC}"
fi

echo ""

# ============================================
# VERIFICAR SERVIÇOS
# ============================================

echo -e "${BLUE}Verificando serviços...${NC}"
echo ""

# Verificar serviços críticos
services=("ssh" "docker" "postgresql" "redis" "tor")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo -e "  ${GREEN}✅ $service - ATIVO${NC}"
    else
        echo -e "  ${YELLOW}⚠️  $service - INATIVO${NC}"
    fi
done

echo ""

# ============================================
# RESUMO
# ============================================

echo "============================================"
echo "  RESUMO DA VERIFICAÇÃO"
echo "============================================"
echo ""

TOTAL=$((SECURE + INSECURE + WARNING))

echo -e "Portas verificadas: ${BLUE}$TOTAL${NC}"
echo -e "Seguras: ${GREEN}$SECURE${NC}"
echo -e "Inseguras: ${RED}$INSECURE${NC}"
echo -e "Avisos: ${YELLOW}$WARNING${NC}"

echo ""

if [ $INSECURE -gt 0 ]; then
    echo -e "${RED}⚠️  ATENÇÃO: Existem portas inseguras!${NC}"
    echo ""
    echo "Recomendações:"
    echo "  1. Configurar TLS/SSL para portas HTTP"
    echo "  2. Usar VPN ou Tor para acesso externo"
    echo "  3. Configurar firewall"
    echo "  4. Usar ProxyChains para acesso anônimo"
else
    echo -e "${GREEN}✅ Todas as portas estão seguras!${NC}"
fi

echo ""
echo "============================================"
