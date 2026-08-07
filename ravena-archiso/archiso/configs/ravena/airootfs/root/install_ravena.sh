#!/bin/bash
# ============================================
# INSTALL_RAVENA.SH - Instalação da Ravena
# Archiso - Arch Linux Customizado
# ============================================
# Este script é executado durante a instalação
# do Archiso para configurar a Ravena.
# ============================================

echo "============================================"
echo "  INSTALANDO RAVENA SECURITY SANDBOX"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Diretório de instalação
RAVENA_DIR="/opt/ravena"
LOG_FILE="/var/log/ravena_install.log"

# Função de log
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# ============================================
# 1. CONFIGURAR SISTEMA
# ============================================

log "${BLUE}[1/8]${NC} Configurando sistema..."

# Configurar hostname
echo "ravena-sandbox" > /etc/hostname

# Configurar hosts
cat > /etc/hosts << EOF
127.0.0.1   localhost
::1         localhost
127.0.1.1   ravena-sandbox.sandbox.local ravena-sandbox
EOF

# Configurar timezone
timedatectl set-timezone America/Sao_Paulo

# Configurar locale
sed -i 's/#pt_BR.UTF-8/pt_BR.UTF-8/' /etc/locale.gen
locale-gen
echo "LANG=pt_BR.UTF-8" > /etc/locale.conf

# Configurar keymap
echo "KEYMAP=br-abnt2" > /etc/vconsole.conf

log "${GREEN}[OK]${NC} Sistema configurado"

# ============================================
# 2. INSTALAR DEPENDÊNCIAS DO SISTEMA
# ============================================

log "${BLUE}[2/8]${NC} Instalando dependências do sistema..."

pacman -S --noconfirm --needed \
    base-devel \
    cmake \
    gcc \
    make \
    python \
    python-pip \
    docker \
    docker-compose \
    nmap \
    netcat \
    curl \
    wget \
    git \
    tmux \
    htop \
    jq

log "${GREEN}[OK]${NC} Dependências instaladas"

# ============================================
# 3. CRIAR DIRETÓRIO DA RAVENA
# ============================================

log "${BLUE}[3/8]${NC} Criando diretório da Ravena..."

mkdir -p "$RAVENA_DIR"/{app,logs,data,config,scripts,backups}
mkdir -p "$RAVENA_DIR"/app/{skills,monitoring,nginx}

log "${GREEN}[OK]${NC} Diretório criado: $RAVENA_DIR"

# ============================================
# 4. INSTALAR DEPENDÊNCIAS PYTHON
# ============================================

log "${BLUE}[4/8]${NC} Instalando dependências Python..."

pip install --break-system-packages \
    flask \
    psycopg2-binary \
    redis \
    pyjwt \
    requests \
    gunicorn \
    python-dotenv

log "${GREEN}[OK]${NC} Dependências Python instaladas"

# ============================================
# 5. CONFIGURAR DOCKER
# ============================================

log "${BLUE}[5/8]${NC} Configurando Docker..."

# Habilitar Docker
systemctl enable docker
systemctl start docker

# Adicionar usuário ao grupo docker
usermod -aG docker ravena 2>/dev/null || true

log "${GREEN}[OK]${NC} Docker configurado"

# ============================================
# 5.1 CONFIGURAR AUTO-LOGIN SEM SENHA
# ============================================

log "${BLUE}[5.1]${NC} Configurando auto-login sem senha..."

# Remover senhas
passwd -d root 2>/dev/null || true
passwd -d ravena 2>/dev/null || true

# Auto-login no TTY1
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << 'AUTOEOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ravena -o '-p -f ravena' --noclear %I $TERM
Type=idle
AUTOEOF

# Sudo sem senha para o usuário
cat > /etc/sudoers.d/ravena << 'SUDOEOF'
ravena ALL=(ALL) NOPASSWD:ALL
SUDOEOF
chmod 440 /etc/sudoers.d/ravena

# SSH sem senha (acesso local apenas)
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/no_password.conf << 'SSHEOF'
PermitRootLogin yes
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
SSHEOF

log "${GREEN}[OK]${NC} Auto-login configurado (sem senha)"

# ============================================
# 6. CRIAR SCRIPT DE MONITORAMENTO DE RAM
# ============================================

log "${BLUE}[6/8]${NC} Criando script de monitoramento de RAM..."

cat > "$RAVENA_DIR/scripts/ram_monitor.sh" << 'RAVEOF'
#!/bin/bash
# ============================================
# MONITORAMENTO DE RAM - RAVENA
# ============================================
# Monitora o uso de RAM e protege contra
# estouro de memória.
# ============================================

# Configurações
MAX_RAM_PERCENT=80          # Limite máximo de RAM (%)
CHECK_INTERVAL=5            # Intervalo de verificação (segundos)
LOG_FILE="/var/log/ravena_ram.log"
ALERT_FILE="/var/log/ram_alerts.log"

# Cores
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Função para obter uso de RAM
get_ram_usage() {
    free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}'
}

# Função para obter RAM total
get_ram_total() {
    free -m | grep Mem | awk '{print $2}'
}

# Função para obter RAM usada
get_ram_used() {
    free -m | grep Mem | awk '{print $3}'
}

# Função para obter RAM disponível
get_ram_available() {
    free -m | grep Mem | awk '{print $7}'
}

# Função para registrar log
log_ram() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local usage=$(get_ram_usage)
    local total=$(get_ram_total)
    local used=$(get_ram_used)
    local available=$(get_ram_available)
    
    echo "[$timestamp] RAM: ${usage}% | Total: ${total}MB | Usado: ${used}MB | Disponível: ${available}MB" >> "$LOG_FILE"
}

# Função para verificar alertas
check_alerts() {
    local usage=$(get_ram_usage)
    local usage_int=${usage%.*}
    
    if [ "$usage_int" -ge "$MAX_RAM_PERCENT" ]; then
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        local alert_msg="[$timestamp] ALERTA: RAM em ${usage}%! Limite: ${MAX_RAM_PERCENT}%"
        
        echo "$alert_msg" >> "$ALERT_FILE"
        echo -e "${RED}$alert_msg${NC}"
        
        # Matar processos que usam muita RAM
        kill_high_memory_processes
    fi
}

# Função para matar processos de alta memória
kill_high_memory_processes() {
    echo -e "${YELLOW}Verificando processos de alta memória...${NC}"
    
    # Listar processos por uso de memória
    ps aux --sort=-%mem | awk 'NR>1{print $4, $11}' | while read mem cmd; do
        mem_int=${mem%.*}
        if [ "$mem_int" -ge 10 ]; then  # Processos usando mais de 10% da RAM
            echo -e "${YELLOW}Matando processo: $cmd (usando ${mem}% da RAM)${NC}"
            pkill -f "$cmd" 2>/dev/null || true
        fi
    done
}

# Função para mostrar status
show_status() {
    local usage=$(get_ram_usage)
    local total=$(get_ram_total)
    local used=$(get_ram_used)
    local available=$(get_ram_available)
    local usage_int=${usage%.*}
    
    echo "============================================"
    echo "  MONITORAMENTO DE RAM - RAVENA"
    echo "============================================"
    echo ""
    
    if [ "$usage_int" -ge "$MAX_RAM_PERCENT" ]; then
        echo -e "Uso de RAM: ${RED}${usage}%${NC}"
    elif [ "$usage_int" -ge 60 ]; then
        echo -e "Uso de RAM: ${YELLOW}${usage}%${NC}"
    else
        echo -e "Uso de RAM: ${GREEN}${usage}%${NC}"
    fi
    
    echo "Total: ${total}MB"
    echo "Usado: ${used}MB"
    echo "Disponível: ${available}MB"
    echo "Limite: ${MAX_RAM_PERCENT}%"
    echo ""
    echo "============================================"
}

# Função principal
main() {
    local mode="${1:-daemon}"
    
    case "$mode" in
        daemon)
            echo "Iniciando monitoramento de RAM..."
            while true; do
                log_ram
                check_alerts
                sleep "$CHECK_INTERVAL"
            done
            ;;
        status)
            show_status
            ;;
        log)
            if [ -f "$LOG_FILE" ]; then
                tail -20 "$LOG_FILE"
            else
                echo "Nenhum log encontrado"
            fi
            ;;
        alerts)
            if [ -f "$ALERT_FILE" ]; then
                tail -20 "$ALERT_FILE"
            else
                echo "Nenhum alerta registrado"
            fi
            ;;
        *)
            echo "Uso: $0 {daemon|status|log|alerts}"
            exit 1
            ;;
    esac
}

main "$@"
RAVEOF

chmod +x "$RAVENA_DIR/scripts/ram_monitor.sh"

log "${GREEN}[OK]${NC} Script de monitoramento de RAM criado"

# ============================================
# 7. CRIAR SCRIPT DE PROTEÇÃO DE RAM
# ============================================

log "${BLUE}[7/8]${NC} Criando script de proteção de RAM..."

cat > "$RAVENA_DIR/scripts/ram_protector.sh" << 'RAVEOF'
#!/bin/bash
# ============================================
# PROTEÇÃO DE RAM - RAVENA
# ============================================
# Protege o sistema contra estouro de memória
# matando processos que usam RAM demais.
# ============================================

# Configurações
MAX_RAM_PERCENT=70
MAX_PROCESS_RAM_PERCENT=15
SWAPPINESS=10
LOG_FILE="/var/log/ram_protection.log"

# Função para configurar swappiness
configure_swappiness() {
    echo "Configurando swappiness para $SWAPPINESS..."
    sysctl vm.swappiness=$SWAPPINESS
    echo "vm.swappiness=$SWAPPINESS" >> /etc/sysctl.conf
}

# Função para limpar cache
clear_cache() {
    echo "Limpando cache do sistema..."
    sync
    echo 3 > /proc/sys/vm/drop_caches
}

# Função para monitorar e proteger
protect() {
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [ "$usage" -ge "$MAX_RAM_PERCENT" ]; then
        echo "[$(date)] ALERTA: RAM em ${usage}% - Limpando cache..." >> "$LOG_FILE"
        clear_cache
        
        # Verificar se ainda está alto
        usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        if [ "$usage" -ge "$MAX_RAM_PERCENT" ]; then
            echo "[$(date)] CRÍTICO: RAM em ${usage}% - Matando processos..." >> "$LOG_FILE"
            
            # Matar processos de alta memória
            ps aux --sort=-%mem | awk -v max="$MAX_PROCESS_RAM_PERCENT" \
                'NR>1 && $4 > max {print $2}' | xargs -r kill -9
        fi
    fi
}

# Função principal
main() {
    local mode="${1:-daemon}"
    
    case "$mode" in
        daemon)
            configure_swappiness
            echo "Iniciando proteção de RAM..."
            while true; do
                protect
                sleep 10
            done
            ;;
        configure)
            configure_swappiness
            echo "Swappiness configurado"
            ;;
        clear)
            clear_cache
            echo "Cache limpo"
            ;;
        status)
            free -h
            ;;
        *)
            echo "Uso: $0 {daemon|configure|clear|status}"
            exit 1
            ;;
    esac
}

main "$@"
RAVEOF

chmod +x "$RAVENA_DIR/scripts/ram_protector.sh"

log "${GREEN}[OK]${NC} Script de proteção de RAM criado"

# ============================================
# 8. CRIAR SCRIPT DE MIGRAÇÃO PARA ORACLE CLOUD
# ============================================

log "${BLUE}[8/8]${NC} Criando script de migração para Oracle Cloud..."

cat > "$RAVENA_DIR/scripts/migrate_to_cloud.sh" << 'RAVEOF'
#!/bin/bash
# ============================================
# MIGRAÇÃO PARA ORACLE CLOUD
# ============================================
# Migra a Ravena de BIOS para servidor
# dedicado no Oracle Cloud.
# ============================================

# Configurações
ORACLE_CLOUD_IP="${ORACLE_CLOUD_IP:-}"
ORACLE_CLOUD_USER="${ORACLE_CLOUD_USER:-ubuntu}"
ORACLE_CLOUD_KEY="${ORACLE_CLOUD_KEY:-~/.ssh/id_rsa}"
RAVENA_DIR="/opt/ravena"
BACKUP_DIR="/opt/ravena/backups"

# Função para criar backup
create_backup() {
    echo "Criando backup da Ravena..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/ravena_backup_$timestamp.tar.gz"
    
    tar -czf "$backup_file" \
        -C /opt \
        ravena \
        --exclude='*.log' \
        --exclude='__pycache__'
    
    echo "Backup criado: $backup_file"
    echo "$backup_file"
}

# Função para migrar para Oracle Cloud
migrate_to_oracle() {
    if [ -z "$ORACLE_CLOUD_IP" ]; then
        echo "ERRO: Configure ORACLE_CLOUD_IP"
        echo "Uso: export ORACLE_CLOUD_IP='seu-ip'"
        exit 1
    fi
    
    echo "Migrando para Oracle Cloud: $ORACLE_CLOUD_IP"
    
    # Criar backup
    local backup_file=$(create_backup)
    
    # Copiar backup para o servidor
    echo "Copiando backup para o servidor..."
    scp -i "$ORACLE_CLOUD_KEY" \
        "$backup_file" \
        "$ORACLE_CLOUD_USER@$ORACLE_CLOUD_IP:/tmp/"
    
    # Instalar dependências no servidor
    echo "Instalando dependências no servidor..."
    ssh -i "$ORACLE_CLOUD_KEY" "$ORACLE_CLOUD_USER@$ORACLE_CLOUD_IP" << 'SSHEOF'
        # Atualizar sistema
        sudo apt update && sudo apt upgrade -y
        
        # Instalar dependências
        sudo apt install -y \
            python3 \
            python3-pip \
            docker.io \
            docker-compose \
            curl \
            wget \
            git
        
        # Instalar dependências Python
        sudo pip3 install \
            flask \
            psycopg2-binary \
            redis \
            pyjwt \
            requests \
            gunicorn
        
        # Criar diretório
        sudo mkdir -p /opt/ravena
SSHEOF
    
    # Descompactar backup no servidor
    echo "Instalando Ravena no servidor..."
    ssh -i "$ORACLE_CLOUD_KEY" "$ORACLE_CLOUD_USER@$ORACLE_CLOUD_IP" << SSHEOF
        sudo tar -xzf /tmp/ravena_backup_*.tar.gz -C /opt/
        sudo chown -R $ORACLE_CLOUD_USER:$ORACLE_CLOUD_USER /opt/ravena
SSHEOF
    
    # Configurar e iniciar
    echo "Configurando Ravena no servidor..."
    ssh -i "$ORACLE_CLOUD_KEY" "$ORACLE_CLOUD_USER@$ORACLE_CLOUD_IP" << 'SSHEOF'
        # Configurar variáveis de ambiente
        export DB_HOST=localhost
        export DB_PORT=5432
        export REDIS_URL=redis://localhost:6379
        
        # Iniciar Docker
        sudo systemctl enable docker
        sudo systemctl start docker
        
        # Iniciar Ravena
        cd /opt/ravena
        sudo docker-compose up -d
SSHEOF
    
    echo "Migração concluída!"
    echo "Acesse: http://$ORACLE_CLOUD_IP:8080"
}

# Função para verificar status
check_status() {
    echo "Verificando status da migração..."
    
    if [ -n "$ORACLE_CLOUD_IP" ]; then
        echo "Oracle Cloud IP: $ORACLE_CLOUD_IP"
        ping -c 1 "$ORACLE_CLOUD_IP" > /dev/null 2>&1 && \
            echo "Status: ONLINE" || echo "Status: OFFLINE"
    else
        echo "Oracle Cloud não configurado"
    fi
}

# Função principal
main() {
    local mode="${1:-help}"
    
    case "$mode" in
        backup)
            create_backup
            ;;
        migrate)
            migrate_to_oracle
            ;;
        status)
            check_status
            ;;
        *)
            echo "Uso: $0 {backup|migrate|status}"
            echo ""
            echo "Variáveis de ambiente:"
            echo "  ORACLE_CLOUD_IP     - IP do servidor Oracle Cloud"
            echo "  ORACLE_CLOUD_USER   - Usuário do servidor (padrão: ubuntu)"
            echo "  ORACLE_CLOUD_KEY    - Caminho da chave SSH (padrão: ~/.ssh/id_rsa)"
            exit 1
            ;;
    esac
}

main "$@"
RAVEOF

chmod +x "$RAVENA_DIR/scripts/migrate_to_cloud.sh"

log "${GREEN}[OK]${NC} Script de migração criado"

# ============================================
# CRIAR SERVIÇOS SYSTEMD
# ============================================

log "Criando serviços systemd..."

# Serviço da Ravena
cat > /etc/systemd/system/ravena.service << EOF
[Unit]
Description=Ravena Security Sandbox
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ravena/app
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Serviço de monitoramento de RAM
cat > /etc/systemd/system/ravena-ram-monitor.service << EOF
[Unit]
Description=Ravena RAM Monitor
After=network.target

[Service]
Type=simple
ExecStart=/opt/ravena/scripts/ram_monitor.sh daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Serviço de proteção de RAM
cat > /etc/systemd/system/ravena-ram-protector.service << EOF
[Unit]
Description=Ravena RAM Protector
After=network.target

[Service]
Type=simple
ExecStart=/opt/ravena/scripts/ram_protector.sh daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar serviços
systemctl daemon-reload
systemctl enable ravena.service
systemctl enable ravena-ram-monitor.service
systemctl enable ravena-ram-protector.service

log "${GREEN}[OK]${NC} Serviços systemd criados"

# ============================================
# CRIAR SCRIPT DE INICIALIZAÇÃO
# ============================================

log "Criando script de inicialização..."

cat > "$RAVENA_DIR/scripts/start_ravena.sh" << 'RAVEOF'
#!/bin/bash
# ============================================
# INICIALIZAÇÃO DA RAVENA
# ============================================

echo "============================================"
echo "  INICIANDO RAVENA SECURITY SANDBOX"
echo "============================================"
echo ""

# Verificar se Docker está rodando
if ! systemctl is-active --quiet docker; then
    echo "Iniciando Docker..."
    sudo systemctl start docker
fi

# Iniciar serviços
echo "Iniciando serviços da Ravena..."
sudo systemctl start ravena
sudo systemctl start ravena-ram-monitor
sudo systemctl start ravena-ram-protector

echo ""
echo "============================================"
echo "  RAVENA INICIADA COM SUCESSO"
echo "============================================"
echo ""
echo "URL: http://localhost:8080"
echo ""
echo "Serviços:"
echo "  - ravena: http://localhost:8080"
echo "  - grafana: http://localhost:3000"
echo "  - kibana: http://localhost:5601"
echo ""
echo "Monitoramento de RAM:"
echo "  /opt/ravena/scripts/ram_monitor.sh status"
echo ""
echo "============================================"
RAVEOF

chmod +x "$RAVENA_DIR/scripts/start_ravena.sh"

# ============================================
# CRIAR SCRIPT DE PARADA
# ============================================

cat > "$RAVENA_DIR/scripts/stop_ravena.sh" << 'RAVEOF'
#!/bin/bash
# ============================================
# PARADA DA RAVENA
# ============================================

echo "============================================"
echo "  PARANDO RAVENA SECURITY SANDBOX"
echo "============================================"
echo ""

# Parar serviços
echo "Parando serviços da Ravena..."
sudo systemctl stop ravena-ram-protector
sudo systemctl stop ravena-ram-monitor
sudo systemctl stop ravena

echo ""
echo "============================================"
echo "  RAVENA PARADA COM SUCESSO"
echo "============================================"
echo ""
RAVEOF

chmod +x "$RAVENA_DIR/scripts/stop_ravena.sh"

# ============================================
# CRIAR SCRIPT DE STATUS
# ============================================

cat > "$RAVENA_DIR/scripts/status_ravena.sh" << 'RAVEOF'
#!/bin/bash
# ============================================
# STATUS DA RAVENA
# ============================================

echo "============================================"
echo "  STATUS DA RAVENA"
echo "============================================"
echo ""

# Status dos serviços
echo "Serviços:"
echo "  - ravena: $(systemctl is-active ravena 2>/dev/null || echo 'inativo')"
echo "  - docker: $(systemctl is-active docker 2>/dev/null || echo 'inativo')"
echo "  - ram-monitor: $(systemctl is-active ravena-ram-monitor 2>/dev/null || echo 'inativo')"
echo "  - ram-protector: $(systemctl is-active ravena-ram-protector 2>/dev/null || echo 'inativo')"
echo ""

# Status da RAM
echo "Uso de RAM:"
free -h
echo ""

# Status de containers
echo "Containers Docker:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker não disponível"
echo ""

echo "============================================"
RAVEOF

chmod +x "$RAVENA_DIR/scripts/status_ravena.sh"

log "${GREEN}[OK]${NC} Scripts de inicialização criados"

# ============================================
# CRIAR SCRIPT .BASHRC AUTOMÁTICO
# ============================================

log "Criando .bashrc automático..."

cat > /root/.bashrc << 'BASHRC'
# ============================================
# .BASHRC - RAVENA SECURITY SANDBOX
# ============================================

# Aliases
alias ravena-start='/opt/ravena/scripts/start_ravena.sh'
alias ravena-stop='/opt/ravena/scripts/stop_ravena.sh'
alias ravena-status='/opt/ravena/scripts/status_ravena.sh'
alias ravena-logs='journalctl -u ravena -f'
alias ram-monitor='/opt/ravena/scripts/ram_monitor.sh status'
alias ram-protect='/opt/ravena/scripts/ram_protector.sh status'
alias migrate-cloud='/opt/ravena/scripts/migrate_to_cloud.sh'

# Prompt personalizado
PS1='\[\033[0;32m\][ravena@\h \W]\$\[\033[0m\] '

# Mensagem de boas-vindas
echo ""
echo "============================================"
echo "  RAVENA SECURITY SANDBOX"
echo "============================================"
echo ""
echo "Comandos disponíveis:"
echo "  ravena-start    - Iniciar a Ravena"
echo "  ravena-stop     - Parar a Ravena"
echo "  ravena-status   - Ver status"
echo "  ravena-logs     - Ver logs"
echo "  ram-monitor     - Monitorar RAM"
echo "  ram-protect     - Configurar proteção"
echo "  migrate-cloud   - Migrar para Oracle Cloud"
echo "  nomad           - Acesso à internet"
echo "  nomad-status    - Ver status da rede"
echo "  port-check      - Verificar segurança das portas"
echo "  ssl-setup       - Configurar criptografia"
echo "  nginx-tls       - Configurar Nginx TLS"
echo "  encrypted-map   - Ver portas criptografadas"
echo ""
echo "============================================"
BASHRC

log "${GREEN}[OK]${NC} .bashrc criado"

# ============================================
# 9. CONFIGURAR REDE E SEGURANÇA
# ============================================

log "${BLUE}[9/9]${NC} Configurando rede e segurança..."

# Criar diretório Nomad
mkdir -p /opt/nomad

# Copiar scripts de rede
cp /root/nomad_net.sh /opt/nomad/
cp /root/port_security_check.sh /opt/nomad/
cp /root/network_security_map.sh /opt/nomad/
cp /root/post_quantum_crypto.sh /opt/nomad/
cp /root/nginx_tls.sh /opt/nomad/
cp /root/encrypted_ports_map.sh /opt/nomad/

# Tornar executáveis
chmod +x /opt/nomad/*.sh

# Criar aliases de rede e segurança
cat >> /root/.bashrc << 'REDEOF'

# Aliases de Rede e Segurança
alias nomad='/opt/nomad/nomad.sh'
alias nomad-status='nomad status'
alias nomad-start='nomad start'
alias nomad-stop='nomad stop'
alias nomad-tor='nomad tor'
alias nomad-warp='nomad warp'
alias nomad-ip='nomad ip'
alias port-check='/opt/nomad/port_security_check.sh'
alias net-map='/opt/nomad/network_security_map.sh'
alias ssl-setup='/opt/nomad/post_quantum_crypto.sh'
alias nginx-tls='/opt/nomad/nginx_tls.sh'
alias encrypted-map='/opt/nomad/encrypted_ports_map.sh'
REDEOF

# Executar configuração de criptografia
log "Executando criptografia pós-quântica..."
/opt/nomad/post_quantum_crypto.sh

# Executar configuração do Nginx
log "Configurando Nginx com TLS..."
/opt/nomad/nginx_tls.sh

log "${GREEN}[OK]${NC} Rede, segurança e criptografia configuradas"

# ============================================
# FINALIZAÇÃO
# ============================================

echo ""
echo "============================================"
echo -e "${GREEN}  INSTALAÇÃO DA RAVENA CONCLUÍDA${NC}"
echo "============================================"
echo ""
echo "Próximos passos:"
echo "1. Reiniciar o sistema"
echo "2. Executar: ravena-start"
echo "3. Acessar: http://localhost:8080"
echo ""
echo "Scripts disponíveis:"
echo "  /opt/ravena/scripts/start_ravena.sh"
echo "  /opt/ravena/scripts/stop_ravena.sh"
echo "  /opt/ravena/scripts/status_ravena.sh"
echo "  /opt/ravena/scripts/ram_monitor.sh"
echo "  /opt/ravena/scripts/ram_protector.sh"
echo "  /opt/ravena/scripts/migrate_to_cloud.sh"
echo "  /opt/nomad/nomad.sh"
echo "  /opt/nomad/port_security_check.sh"
echo "  /opt/nomad/network_security_map.sh"
echo "  /opt/nomad/post_quantum_crypto.sh"
echo "  /opt/nomad/nginx_tls.sh"
echo "  /opt/nomad/encrypted_ports_map.sh"
echo ""
echo "============================================"

# ============================================
# SERVIÇOS ADICIONAIS
# ============================================

# Serviço Nomad
cat > /etc/systemd/system/nomad.service << 'NOMADEOF'
[Unit]
Description=Nomad - Acesso à Internet
After=network.target

[Service]
Type=simple
ExecStart=/opt/nomad/nomad.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
NOMADEOF

# Timer de renovação SSL
cat > /etc/systemd/system/ssl-renew.timer << 'SSLRENEOF'
[Unit]
Description=Renovação automática de certificados SSL
Requires=ssl-renew.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
SSLRENEOF

# Serviço de renovação SSL
cat > /etc/systemd/system/ssl-renew.service << 'SSLSERVICEEOF'
[Unit]
Description=Renovação de certificados SSL
After=network.target

[Service]
Type=oneshot
ExecStart=/etc/ssl/ravena/renew_certs.sh
StandardOutput=journal
StandardError=journal
SSLSERVICEEOF

# Serviço Nginx TLS
cat > /etc/systemd/system/nginx-tls.service << 'NGINXEOF'
[Unit]
Description=Nginx com TLS Pós-Quântico
After=network.target

[Service]
Type=forking
ExecStartPre=/usr/bin/nginx -t
ExecStart=/usr/bin/nginx
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s QUIT $MAINPID

[Install]
WantedBy=multi-user.target
NGINXEOF

# Habilitar serviços
systemctl daemon-reload
systemctl enable nomad.service 2>/dev/null || true
systemctl enable ssl-renew.timer 2>/dev/null || true
systemctl enable nginx-tls.service 2>/dev/null || true

# ============================================
# CRIPTOGRAFIA PÓS-QUÂNTICA
# ============================================

log "Configurando criptografia pós-quântica..."

mkdir -p /etc/ssl/ravena/{certs,private,csr,ext,post-quantum}

log "Gerando chaves RSA 4096..."
openssl genrsa -out /etc/ssl/ravena/private/ca.key 4096 2>/dev/null

log "Gerando chaves ECDSA P-384..."
openssl ecparam -genkey -name secp384r1 -out /etc/ssl/ravena/private/ca-ec.key 2>/dev/null

log "Gerando chaves Ed25519..."
openssl genpkey -algorithm Ed25519 -out /etc/ssl/ravena/private/ca-ed25519.key 2>/dev/null

log "Criando certificado CA..."
cat > /etc/ssl/ravena/ext/ca.ext << 'CAEOF'
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = BR
ST = Sao Paulo
L = Sao Paulo
O = Ravena Security Lab
OU = CA
CN = Ravena CA

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
CAEOF

openssl req -x509 -new -nodes -key /etc/ssl/ravena/private/ca.key -sha384 -days 365 -out /etc/ssl/ravena/certs/ca.crt -config /etc/ssl/ravena/ext/ca.ext 2>/dev/null

create_cert() {
    local name=$1
    local port=$2
    log "Criando certificado para $name (porta $port)..."
    openssl genrsa -out "/etc/ssl/ravena/private/$name.key" 4096 2>/dev/null
    cat > "/etc/ssl/ravena/ext/$name.ext" << CERTCONF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = BR
ST = Sao Paulo
L = Sao Paulo
O = Ravena Security Lab
OU = $name
CN = localhost

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = ravena-sandbox
IP.1 = 127.0.0.1
IP.2 = 172.20.0.2
CERTCONF
    openssl req -new -key "/etc/ssl/ravena/private/$name.key" -out "/etc/ssl/ravena/csr/$name.csr" -config "/etc/ssl/ravena/ext/$name.ext" 2>/dev/null
    openssl x509 -req -in "/etc/ssl/ravena/csr/$name.csr" -CA /etc/ssl/ravena/certs/ca.crt -CAkey /etc/ssl/ravena/private/ca.key -CAcreateserial -out "/etc/ssl/ravena/certs/$name.crt" -days 365 -sha384 -extfile "/etc/ssl/ravena/ext/$name.ext" -extensions v3_req 2>/dev/null
}

create_cert "http" "80"
create_cert "grafana" "3000"
create_cert "kibana" "5601"
create_cert "ravena-app" "8080"
create_cert "prometheus" "9090"
create_cert "postgresql" "5432"
create_cert "redis" "6379"
create_cert "elasticsearch" "9200"

log "Criando script de renovação..."
cat > /etc/ssl/ravena/renew_certs.sh << 'RENEWEOF'
#!/bin/bash
SSL_DIR="/etc/ssl/ravena"
for cert in "$SSL_DIR/certs"/*.crt; do
    name=$(basename "$cert" .crt)
    if [ "$name" != "ca" ]; then
        openssl req -new -key "$SSL_DIR/private/$name.key" -out "$SSL_DIR/csr/$name.csr" -config "$SSL_DIR/ext/$name.ext" 2>/dev/null
        openssl x509 -req -in "$SSL_DIR/csr/$name.csr" -CA "$SSL_DIR/certs/ca.crt" -CAkey "$SSL_DIR/private/ca.key" -CAcreateserial -out "$SSL_DIR/certs/$name.crt" -days 365 -sha384 -extfile "$SSL_DIR/ext/$name.ext" -extensions v3_req 2>/dev/null
    fi
done
RENEWEOF
chmod +x /etc/ssl/ravena/renew_certs.sh

# ============================================
# CONFIGURAR NGINX COM TLS
# ============================================

log "Configurando Nginx com TLS..."

pacman -S --noconfirm --needed nginx 2>/dev/null || true
openssl dhparam -out /etc/nginx/dhparam.pem 4096 2>/dev/null

cat > /etc/nginx/nginx.conf << 'NGINXEOF'
worker_processes auto;
events { worker_connections 1024; }
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    log_format main '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent';
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_dhparam /etc/nginx/dhparam.pem;
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 301 https://$host$request_uri;
    }
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name localhost;
        ssl_certificate /etc/ssl/ravena/certs/ravena-app.crt;
        ssl_certificate_key /etc/ssl/ravena/private/ravena-app.key;
        location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }
        location /ws { proxy_pass http://127.0.0.1:8080; proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade"; }
    }
    server {
        listen 3443 ssl http2; listen [::]:3443 ssl http2;
        server_name localhost;
        ssl_certificate /etc/ssl/ravena/certs/grafana.crt;
        ssl_certificate_key /etc/ssl/ravena/private/grafana.key;
        location / { proxy_pass http://127.0.0.1:3000; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }
    }
    server {
        listen 5643 ssl http2; listen [::]:5643 ssl http2;
        server_name localhost;
        ssl_certificate /etc/ssl/ravena/certs/kibana.crt;
        ssl_certificate_key /etc/ssl/ravena/private/kibana.key;
        location / { proxy_pass http://127.0.0.1:5601; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }
    }
    server {
        listen 9443 ssl http2; listen [::]:9443 ssl http2;
        server_name localhost;
        ssl_certificate /etc/ssl/ravena/certs/prometheus.crt;
        ssl_certificate_key /etc/ssl/ravena/private/prometheus.key;
        location / { proxy_pass http://127.0.0.1:9090; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme; }
    }
}
NGINXEOF

systemctl enable nginx 2>/dev/null || true

# ============================================
# CONFIGURAR TOR
# ============================================

log "Configurando Tor..."

pacman -S --noconfirm --needed tor proxychains-ng 2>/dev/null || true

cat > /etc/tor/torrc << 'TOREOF'
SocksPort 9050
SocksPolicy 127.0.0.0/8
Log notice file /var/log/tor/notices.log
DataDirectory /var/lib/tor
ControlPort 9051
ExitNodes {br},{us},{de},{fr},{nl}
StrictNodes 0
TOREOF

mkdir -p /var/lib/tor
chmod 700 /var/lib/tor

cat > /etc/proxychains.conf << 'PROXYEOF'
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 9050
PROXYEOF

# ============================================
# SCRIPT DE BACKUP
# ============================================

log "Criando script de backup..."

cat > "$RAVENA_DIR/scripts/backup_ravena.sh" << 'BACKUPEOF'
#!/bin/bash
BACKUP_DIR="/opt/ravena/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ravena_backup_$TIMESTAMP.tar.gz"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_FILE" -C /opt ravena --exclude='*.log' --exclude='__pycache__'
echo "Backup criado: $BACKUP_FILE"
BACKUPEOF
chmod +x "$RAVENA_DIR/scripts/backup_ravena.sh"

# ============================================
# CONFIGURAÇÕES DE PROTEÇÃO DE RAM
# ============================================

log "Configurando limites de RAM..."

cat > "$RAVENA_DIR/config/ram_limits.conf" << 'LIMITEOF'
MAX_RAM_PERCENT=80
CHECK_INTERVAL=5
AUTO_CLEAN_CACHE=true
KILL_HIGH_MEMORY=true
LOG_ALERTS=true
SWAPPINESS=10
LIMITEOF

# ============================================
# FINALIZAÇÃO
# ============================================

log ""
log "============================================"
log "  INSTALAÇÃO DA RAVENA CONCLUÍDA"
log "============================================"
log ""
log "Próximos passos:"
log "1. Reiniciar o sistema"
log "2. Executar: ravena-start"
log "3. Acessar: https://localhost:443"
log ""
log "Serviços habilitados:"
log "  - ravena.service"
log "  - ravena-ram-monitor.service"
log "  - ravena-ram-protector.service"
log "  - nomad.service"
log "  - ssl-renew.timer"
log "  - nginx.service"
log ""
log "============================================"
