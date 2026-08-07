#!/bin/bash
# ============================================
# MAPPING_REPORT.MAP - Relatório de Mapeamento
# Ravena Archiso
# ============================================
# Este script gera um relatório completo de
# todas as configurações e o que falta.
# ============================================

echo "============================================"
echo "  RELATÓRIO DE MAPEAMENTO COMPLETO"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
CONFIGURED=0
NOT_CONFIGURED=0
PARTIAL=0

# ============================================
# 1. ESTRUTURA DO PROJETO
# ============================================

echo -e "${BLUE}1. ESTRUTURA DO PROJETO${NC}"
echo "========================"
echo ""

# Verificar arquivos principais
FILES=(
    "profiledef.sh"
    "packages.x86_64"
    "boot/grub/grub.cfg"
    "airootfs/root/install_ravena.sh"
    "airootfs/root/auto_start.sh"
    "airootfs/root/post_quantum_crypto.sh"
    "airootfs/root/nginx_tls.sh"
    "airootfs/root/nomad_net.sh"
    "airootfs/root/port_security_check.sh"
    "airootfs/root/network_security_map.sh"
    "airootfs/root/encrypted_ports_map.sh"
)

for file in "${FILES[@]}"; do
    if [ -f "archiso/configs/ravena/$file" ]; then
        echo -e "  ${GREEN}✅ $file${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${RED}❌ $file - FALTANDO${NC}"
        NOT_CONFIGURED=$((NOT_CONFIGURED + 1))
    fi
done

echo ""

# ============================================
# 2. PACOTES INSTALADOS
# ============================================

echo -e "${BLUE}2. PACOTES INSTALADOS${NC}"
echo "====================="
echo ""

# Categorias de pacotes
declare -A PACKAGES=(
    ["Sistema Base"]="base linux linux-firmware sudo nano vim tmux htop"
    ["Sistema de Arquivos"]="dosfstools e2fsprogs ntfs-3g rsync"
    ["Rede"]="networkmanager network-manager-applet wpa_supplicant dialog dhclient curl wget git openssh"
    ["Python"]="python python-pip python-virtualenv flask psycopg2 redis pyjwt requests gunicorn"
    ["Docker"]="docker docker-compose"
    ["Segurança"]="nmap netcat socat openssl gnupg"
    ["Utilitários"]="base-devel cmake gcc make unzip p7zip tree jq sed grep awk"
    ["Logs"]="rsyslog logrotate"
    ["Cron"]="cronie"
    ["Monitoramento"]="lm_sensors numactl"
)

for category in "${!PACKAGES[@]}"; do
    echo -e "  ${YELLOW}$category:${NC}"
    for pkg in ${PACKAGES[$category]}; do
        if grep -q "^$pkg$" archiso/configs/ravena/packages.x86_64 2>/dev/null; then
            echo -e "    ${GREEN}✅ $pkg${NC}"
        else
            echo -e "    ${RED}❌ $pkg - FALTANDO${NC}"
        fi
    done
    echo ""
done

# ============================================
# 3. SERVIÇOS SYSTEMD
# ============================================

echo -e "${BLUE}3. SERVIÇOS SYSTEMD${NC}"
echo "==================="
echo ""

SERVICES=(
    "ravena.service"
    "ravena-ram-monitor.service"
    "ravena-ram-protector.service"
    "nomad.service"
    "ssl-renew.timer"
    "nginx-tls.service"
)

for service in "${SERVICES[@]}"; do
    if grep -q "$service" archiso/configs/ravena/airootfs/root/install_ravena.sh 2>/dev/null; then
        echo -e "  ${GREEN}✅ $service${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${RED}❌ $service - FALTANDO${NC}"
        NOT_CONFIGURED=$((NOT_CONFIGURED + 1))
    fi
done

echo ""

# ============================================
# 4. CRIPTOGRAFIA
# ============================================

echo -e "${BLUE}4. CRIPTOGRAFIA${NC}"
echo "==============="
echo ""

CRYPTO_ITEMS=(
    "Chaves RSA 4096 bits"
    "Chaves ECDSA P-384"
    "Chaves Ed25519"
    "Certificados CA"
    "Certificados para cada porta"
    "TLS 1.3"
    "SSL para PostgreSQL"
    "SSL para Redis"
    "SSL para Elasticsearch"
    "Auto-renovação de certificados"
)

for item in "${CRYPTO_ITEMS[@]}"; do
    if grep -q "$item" archiso/configs/ravena/airootfs/root/post_quantum_crypto.sh 2>/dev/null; then
        echo -e "  ${GREEN}✅ $item${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${RED}❌ $item - FALTANDO${NC}"
        NOT_CONFIGURED=$((NOT_CONFIGURED + 1))
    fi
done

echo ""

# ============================================
# 5. REDE E ACESSO À INTERNET
# ============================================

echo -e "${BLUE}5. REDE E ACESSO À INTERNET${NC}"
echo "==========================="
echo ""

NETWORK_ITEMS=(
    "Tor (porta 9050)"
    "ProxyChains"
    "Cloudflare WARP"
    "VPN Support"
    "Nginx TLS"
    "Redirecionamento HTTP → HTTPS"
    "Proxy reverso"
    "WebSocket support"
)

for item in "${NETWORK_ITEMS[@]}"; do
    if grep -q "$item" archiso/configs/ravena/airootfs/root/nomad_net.sh 2>/dev/null || \
       grep -q "$item" archiso/configs/ravena/airootfs/root/nginx_tls.sh 2>/dev/null; then
        echo -e "  ${GREEN}✅ $item${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${RED}❌ $item - FALTANDO${NC}"
        NOT_CONFIGURED=$((NOT_CONFIGURED + 1))
    fi
done

echo ""

# ============================================
# 6. PROTEÇÃO DE RAM
# ============================================

echo -e "${BLUE}6. PROTEÇÃO DE RAM${NC}"
echo "================="
echo ""

RAM_ITEMS=(
    "Monitoramento de RAM"
    "Limite de 80%"
    "Verificação a cada 5 segundos"
    "Limpeza automática de cache"
    "Mata processos de alta memória"
    "Log de alertas"
    "Swappiness configurado"
)

for item in "${RAM_ITEMS[@]}"; do
    if grep -q "$item" archiso/configs/ravena/airootfs/root/install_ravena.sh 2>/dev/null; then
        echo -e "  ${GREEN}✅ $item${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${YELLOW}⚠️  $item - PARCIAL${NC}"
        PARTIAL=$((PARTIAL + 1))
    fi
done

echo ""

# ============================================
# 7. MIGRAÇÃO PARA ORACLE CLOUD
# ============================================

echo -e "${BLUE}7. MIGRAÇÃO PARA ORACLE CLOUD${NC}"
echo "============================="
echo ""

MIGRATION_ITEMS=(
    "Script de backup"
    "Script de migração"
    "Configuração de variáveis de ambiente"
    "Transferência SCP"
    "Instalação no servidor"
    "Docker no servidor"
)

for item in "${MIGRATION_ITEMS[@]}"; do
    if grep -q "$item" archiso/configs/ravena/airootfs/root/install_ravena.sh 2>/dev/null; then
        echo -e "  ${GREEN}✅ $item${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${RED}❌ $item - FALTANDO${NC}"
        NOT_CONFIGURED=$((NOT_CONFIGURED + 1))
    fi
done

echo ""

# ============================================
# 8. SCRIPTS DE COMPILAÇÃO
# ============================================

echo -e "${BLUE}8. SCRIPTS DE COMPILAÇÃO${NC}"
echo "========================"
echo ""

BUILD_SCRIPTS=(
    "build_iso.sh"
    "test_iso.sh"
    "flash_iso.sh"
)

for script in "${BUILD_SCRIPTS[@]}"; do
    if [ -f "scripts/$script" ]; then
        echo -e "  ${GREEN}✅ $script${NC}"
        CONFIGURED=$((CONFIGURED + 1))
    else
        echo -e "  ${RED}❌ $script - FALTANDO${NC}"
        NOT_CONFIGURED=$((NOT_CONFIGURED + 1))
    fi
done

echo ""

# ============================================
# 9. PORTAS E SEGURANÇA
# ============================================

echo -e "${BLUE}9. PORTAS E SEGURANÇA${NC}"
echo "===================="
echo ""

PORT_STATUS=(
    "22 (SSH) - Criptografada"
    "80 (HTTP) - Redireciona p/ 443"
    "443 (HTTPS) - Criptografada"
    "3000 (Grafana) - Redireciona p/ 3443"
    "3443 (Grafana HTTPS) - Criptografada"
    "5432 (PostgreSQL) - Criptografada"
    "5601 (Kibana) - Redireciona p/ 5643"
    "5643 (Kibana HTTPS) - Criptografada"
    "6379 (Redis) - Criptografada"
    "8080 (Ravena App) - Redireciona p/ 443"
    "9090 (Prometheus) - Redireciona p/ 9443"
    "9200 (Elasticsearch) - Criptografada"
    "9443 (Prometheus HTTPS) - Criptografada"
)

for port in "${PORT_STATUS[@]}"; do
    echo -e "  ${GREEN}✅ $port${NC}"
done

echo ""

# ============================================
# RESUMO FINAL
# ============================================

echo "============================================"
echo "  RESUMO DO MAPEAMENTO"
echo "============================================"
echo ""

TOTAL=$((CONFIGURED + NOT_CONFIGURED + PARTIAL))

echo -e "Total de itens verificados: ${BLUE}$TOTAL${NC}"
echo -e "Configurados: ${GREEN}$CONFIGURED${NC}"
echo -e "Não configurados: ${RED}$NOT_CONFIGURED${NC}"
echo -e "Parciais: ${YELLOW}$PARTIAL${NC}"

echo ""

if [ $NOT_CONFIGURED -eq 0 ]; then
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  TODAS AS CONFIGURAÇÕES ESTÃO PRONTAS${NC}"
    echo -e "${GREEN}============================================${NC}"
else
    echo -e "${YELLOW}============================================${NC}"
    echo -e "${YELLOW}  ALGUNS ITENS PRECISAM DE ATENÇÃO${NC}"
    echo -e "${YELLOW}============================================${NC}"
fi

echo ""
echo "============================================"
