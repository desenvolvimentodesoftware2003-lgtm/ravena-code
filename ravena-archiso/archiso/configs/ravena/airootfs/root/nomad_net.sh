#!/bin/bash
# ============================================
# NOMAD_NET.SH - Configuração de Rede Nomad
# Ravena Security Sandbox
# ============================================
# Configura acesso à internet via Nomad
# usando proxy/VPN para ambientes isolados.
# ============================================

echo "============================================"
echo "  CONFIGURAÇÃO NOMAD - REDE"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
NOMAD_DIR="/opt/nomad"
LOG_FILE="/var/log/nomad.log"

# ============================================
# 1. INSTALAR DEPENDÊNCIAS
# ============================================

echo -e "${BLUE}[1/6]${NC} Instalando dependências..."

# Verificar e instalar pacotes necessários
pacman -S --noconfirm --needed \
    tor \
    proxychains-ng \
    openvpn \
    wireguard-tools \
    curl \
    wget

echo -e "${GREEN}[OK]${NC} Dependências instaladas"

# ============================================
# 2. CONFIGURAR TOR
# ============================================

echo -e "${BLUE}[2/6]${NC} Configurando Tor..."

# Criar diretório do Tor
mkdir -p /etc/tor

# Configurar Tor
cat > /etc/tor/torrc << 'EOF'
# Configuração Tor para Ravena
SocksPort 9050
SocksPolicy 127.0.0.0/8
Log notice file /var/log/tor/notices.log
DataDirectory /var/lib/tor
ControlPort 9051
HashedControlPassword
ExitNodes {br},{us},{de},{fr},{nl}
StrictNodes 0
EOF

# Criar diretório de dados
mkdir -p /var/lib/tor
chmod 700 /var/lib/tor

echo -e "${GREEN}[OK]${NC} Tor configurado"

# ============================================
# 3. CONFIGURAR PROXYCHAINS
# ============================================

echo -e "${BLUE}[3/6]${NC} Configurando ProxyChains..."

# Configurar ProxyChains
cat > /etc/proxychains.conf << 'EOF'
# Configuração ProxyChains para Ravena
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
# Tor
socks5 127.0.0.1 9050
EOF

echo -e "${GREEN}[OK]${NC} ProxyChains configurado"

# ============================================
# 4. CONFIGURAR WARP (CLOUDFLARE)
# ============================================

echo -e "${BLUE}[4/6]${NC} Configurando Cloudflare WARP..."

# Criar script de instalação do WARP
cat > "$NOMAD_DIR/install_warp.sh" << 'WARPEOF'
#!/bin/bash
# Instalar Cloudflare WARP

# Adicionar repositório
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo pacman-key --add -
sudo pacman-key --lsign-key 6D97D6F90B7F4250

# Instalar WARP
sudo pacman -S --noconfirm cloudflare-warp

# Iniciar serviço
sudo systemctl enable warp-svc
sudo systemctl start warp-svc

# Registrar
sudo warp-cli registration new

# Conectar
sudo warp-cli connect

echo "WARP configurado com sucesso!"
WARPEOF

chmod +x "$NOMAD_DIR/install_warp.sh"

echo -e "${GREEN}[OK]${NC} Script WARP criado"

# ============================================
# 5. CONFIGURAR VPN (OPCIONAL)
# ============================================

echo -e "${BLUE}[5/6]${NC} Configurando VPN..."

# Criar script de configuração VPN
cat > "$NOMAD_DIR/setup_vpn.sh" << 'VPNEOF'
#!/bin/bash
# Configuração VPN para Ravena

echo "Configurando VPN..."

# Verificar se há configuração VPN
if [ -f "/etc/openvpn/client.conf" ]; then
    echo "Configuração VPN encontrada"
    sudo systemctl enable openvpn-client@client
    sudo systemctl start openvpn-client@client
else
    echo "Nenhuma configuração VPN encontrada"
    echo "Coloque seu arquivo .ovpn em /etc/openvpn/client.conf"
fi
VPNEOF

chmod +x "$NOMAD_DIR/setup_vpn.sh"

echo -e "${GREEN}[OK]${NC} Script VPN criado"

# ============================================
# 6. CRIAR SCRIPT PRINCIPAL NOMAD
# ============================================

echo -e "${BLUE}[6/6]${NC} Criando script principal Nomad..."

cat > "$NOMAD_DIR/nomad.sh" << 'NOMADEOF'
#!/bin/bash
# ============================================
# NOMAD - ACESSO À INTERNET
# ============================================
# Gerencia acesso à internet via Tor,
# VPN, WARP ou ProxyChains.
# ============================================

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Função para mostrar status
show_status() {
    echo "============================================"
    echo "  STATUS NOMAD"
    echo "============================================"
    echo ""
    
    # Verificar Tor
    if systemctl is-active --quiet tor; then
        echo -e "Tor: ${GREEN}ATIVO${NC}"
    else
        echo -e "Tor: ${RED}INATIVO${NC}"
    fi
    
    # Verificar WARP
    if systemctl is-active --quiet warp-svc; then
        echo -e "WARP: ${GREEN}ATIVO${NC}"
    else
        echo -e "WARP: ${RED}INATIVO${NC}"
    fi
    
    # Verificar VPN
    if systemctl is-active --quiet openvpn-client@client; then
        echo -e "VPN: ${GREEN}ATIVO${NC}"
    else
        echo -e "VPN: ${RED}INATIVO${NC}"
    fi
    
    # Verificar conectividade
    echo ""
    echo "Conectividade:"
    if ping -c 1 8.8.8.8 &> /dev/null; then
        echo -e "  Internet: ${GREEN}CONECTADO${NC}"
    else
        echo -e "  Internet: ${RED}DESCONECTADO${NC}"
    fi
    
    echo ""
    echo "============================================"
}

# Função para iniciar Tor
start_tor() {
    echo "Iniciando Tor..."
    sudo systemctl start tor
    echo -e "${GREEN}Tor iniciado${NC}"
}

# Função para parar Tor
stop_tor() {
    echo "Parando Tor..."
    sudo systemctl stop tor
    echo -e "${YELLOW}Tor parado${NC}"
}

# Função para iniciar WARP
start_warp() {
    echo "Iniciando WARP..."
    sudo systemctl start warp-svc
    sudo warp-cli connect
    echo -e "${GREEN}WARP iniciado${NC}"
}

# Função para parar WARP
stop_warp() {
    echo "Parando WARP..."
    sudo warp-cli disconnect
    sudo systemctl stop warp-svc
    echo -e "${YELLOW}WARP parado${NC}"
}

# Função para usar ProxyChains
use_proxy() {
    local cmd="$1"
    echo "Executando via ProxyChains..."
    proxychains4 "$cmd"
}

# Função para mostrar IP
show_ip() {
    echo "IP Atual:"
    echo "  Direto: $(curl -s ifconfig.me)"
    echo "  Via Tor: $(proxychains4 curl -s ifconfig.me 2>/dev/null || echo 'N/A')"
}

# Função principal
main() {
    local mode="${1:-help}"
    
    case "$mode" in
        status)
            show_status
            ;;
        start)
            start_tor
            start_warp
            ;;
        stop)
            stop_tor
            stop_warp
            ;;
        tor)
            start_tor
            ;;
        warp)
            start_warp
            ;;
        proxy)
            use_proxy "$2"
            ;;
        ip)
            show_ip
            ;;
        help|*)
            echo "Uso: $0 {status|start|stop|tor|warp|proxy <cmd>|ip}"
            echo ""
            echo "Comandos:"
            echo "  status        - Ver status"
            echo "  start         - Iniciar tudo"
            echo "  stop          - Parar tudo"
            echo "  tor           - Iniciar apenas Tor"
            echo "  warp          - Iniciar apenas WARP"
            echo "  proxy <cmd>   - Executar comando via proxy"
            echo "  ip            - Mostrar IP"
            exit 1
            ;;
    esac
}

main "$@"
NOMADEOF

chmod +x "$NOMAD_DIR/nomad.sh"

echo -e "${GREEN}[OK]${NC} Script principal criado"

# ============================================
# CRIAR SERVIÇO SYSTEMD
# ============================================

echo "Criando serviço systemd..."

cat > /etc/systemd/system/nomad.service << EOF
[Unit]
Description=Nomad - Acesso à Internet
After=network.target

[Service]
Type=simple
ExecStart=$NOMAD_DIR/nomad.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable nomad.service

echo -e "${GREEN}[OK]${NC} Serviço systemd criado"

# ============================================
# CRIAR ALIASES
# ============================================

echo "Criando aliases..."

cat >> /root/.bashrc << 'EOF'

# Aliases Nomad
alias nomad='$NOMAD_DIR/nomad.sh'
alias nomad-status='nomad status'
alias nomad-start='nomad start'
alias nomad-stop='nomad stop'
alias nomad-tor='nomad tor'
alias nomad-warp='nomad warp'
alias nomad-ip='nomad ip'
EOF

echo -e "${GREEN}[OK]${NC} Aliases criados"

# ============================================
# FINALIZAÇÃO
# ============================================

echo ""
echo "============================================"
echo -e "${GREEN}  NOMAD CONFIGURADO COM SUCESSO${NC}"
echo "============================================"
echo ""
echo "Comandos disponíveis:"
echo "  nomad status    - Ver status"
echo "  nomad start     - Iniciar tudo"
echo "  nomad stop      - Parar tudo"
echo "  nomad tor       - Iniciar Tor"
echo "  nomad warp      - Iniciar WARP"
echo "  nomad ip        - Ver IP"
echo ""
echo "============================================"
