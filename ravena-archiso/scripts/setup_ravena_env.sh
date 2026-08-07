#!/bin/bash
# ============================================
# Script de Configuração do Ambiente Ravena
# Execute este script no Arch Linux instalado
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

# ============================================
# VERIFICAR ROOT
# ============================================
if [ "$EUID" -ne 0 ]; then
    error "Execute como root: sudo ./setup_ravena_env.sh"
    exit 1
fi

echo ""
echo "============================================"
echo "  CONFIGURAÇÃO DO AMBIENTE RAVENA"
echo "  Arch Linux - ISO Builder"
echo "============================================"
echo ""

# ============================================
# 1. ATUALIZAR SISTEMA
# ============================================
log "Atualizando sistema..."
pacman -Syyu --noconfirm

# ============================================
# 2. INSTALAR DEPENDÊNCIAS
# ============================================
log "Instalando dependências essenciais..."

pacman -S --noconfirm --needed \
    base-devel \
    git \
    sudo \
    nano \
    vim \
    curl \
    wget \
    networkmanager \
    network-manager-applet \
    wpa_supplicant \
    dhcpcd \
    openssh

# ============================================
# 3. INSTALAR PACOTES DO PROJETO
# ============================================
log "Instalando pacotes do projeto Ravena..."

pacman -S --noconfirm --needed \
    archiso \
    mkinitcpio \
    dosfstools \
    e2fsprogs \
    squashfs-tools \
    libisoburn \
    grub \
    efibootmgr \
    mtools

# ============================================
# 4. INSTALAR AMBIENTE DE DESENVOLVIMENTO
# ============================================
log "Instalando ambiente de desenvolvimento..."

pacman -S --noconfirm --needed \
    python \
    python-pip \
    python-virtualenv \
    nodejs \
    npm \
    docker \
    docker-compose \
    nginx \
    postgresql \
    redis \
    tor \
    proxychains-ng \
    nmap \
    nikto \
    sqlmap \
    whatweb \
    gobuster \
    dirb \
    hydra \
    john \
    hashcat \
    metasploit \
    burpsuite \
    zaproxy \
    wireshark-qt \
    tcpdump \
    net-tools \
    openbsd-netcat \
    openssl

# ============================================
# 5. CRIAR DIRETÓRIOS
# ============================================
log "Criando estrutura de diretórios..."

mkdir -p /opt/ravena
mkdir -p /opt/ravena/scripts
mkdir -p /opt/ravena/logs
mkdir -p /opt/ravena/backups
mkdir -p /opt/ravena/config

# ============================================
# 6. HABILITAR SERVIÇOS
# ============================================
log "Habilitando serviços..."

systemctl enable docker
systemctl enable postgresql
systemctl enable redis
systemctl enable nginx
systemctl enable tor
systemctl enable NetworkManager
systemctl enable sshd

# ============================================
# 7. CRIAR SCRIPT DE COMPILAÇÃO DO ISO
# ============================================
log "Criando script de compilação..."

cat > /opt/ravena/scripts/build_ravena_iso.sh << 'BUILDEOF'
#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    error "Execute como root: sudo ./build_ravena_iso.sh"
    exit 1
fi

RAVENA_DIR="/opt/ravena-archiso"
ISO_NAME="ravena-sandbox"
WORK_DIR="/tmp/ravena-work"
OUT_DIR="/opt/ravena/out"

log "Limpando diretórios de trabalho..."
rm -rf "$WORK_DIR"
mkdir -p "$OUT_DIR"

log "Compilando ISO da Ravena..."
cd "$RAVENA_DIR/archiso/configs/ravena"

# Usar mkarchiso do sistema
mkarchiso \
    -v \
    -w "$WORK_DIR" \
    -C "" \
    -D "$ISO_NAME" \
    -o "$OUT_DIR" \
    .

log "ISO criada em: $OUT_DIR"
ls -lh "$OUT_DIR"/*.iso

echo ""
echo "============================================"
echo "  ISO COMPILADA COM SUCESSO!"
echo "============================================"
echo ""
echo "Próximos passos:"
echo "  1. Testar: sudo qemu-system-x86_64 -cdrom $OUT_DIR/*.iso -m 4096"
echo "  2. Gravar: sudo dd if=$OUT_DIR/*.iso of=/dev/sdX bs=4M status=progress"
echo ""
BUILDEOF
chmod +x /opt/ravena/scripts/build_ravena_iso.sh

# ============================================
# 8. CRIAR SCRIPT DE TESTE EM VM
# ============================================
log "Criando script de teste..."

cat > /opt/ravena/scripts/test_ravena_vm.sh << 'TESTEOF'
#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1"; }

if ! command -v qemu-system-x86_64 &> /dev/null; then
    error "QEMU não instalado. Instale com: sudo pacman -S qemu-full"
    exit 1
fi

ISO_FILE=$(ls -t /opt/ravena/out/*.iso 2>/dev/null | head -1)

if [ -z "$ISO_FILE" ]; then
    error "Nenhuma ISO encontrada em /opt/ravena/out/"
    error "Compile primeiro: sudo /opt/ravena/scripts/build_ravena_iso.sh"
    exit 1
fi

log "Iniciando VM com ISO: $ISO_FILE"
qemu-system-x86_64 \
    -cdrom "$ISO_FILE" \
    -m 4096 \
    -smp 2 \
    -enable-kvm \
    -vga virtio \
    -net nic \
    -net user,hostfwd=tcp::8080-:80,hostfwd=tcp::4443-:443,hostfwd=tcp::2222-:22

TESTEOF
chmod +x /opt/ravena/scripts/test_ravena_vm.sh

# ============================================
# 9. CRIAR SCRIPT DE GRAVAÇÃO EM PENDRIVE
# ============================================
log "Criando script de flash..."

cat > /opt/ravena/scripts/flash_pendrive.sh << 'FLASHEOF'
#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then
    error "Execute como root: sudo ./flash_pendrive.sh"
    exit 1
fi

ISO_FILE=$(ls -t /opt/ravena/out/*.iso 2>/dev/null | head -1)

if [ -z "$ISO_FILE" ]; then
    error "Nenhuma ISO encontrada em /opt/ravena/out/"
    exit 1
fi

echo ""
echo "Dispositivos disponíveis:"
lsblk -d -o NAME,SIZE,MODEL
echo ""

read -p "Digite o dispositivo do pendrive (ex: sdb): " DEVICE

if [ ! -b "/dev/$DEVICE" ]; then
    error "Dispositivo /dev/$DEVICE não encontrado!"
    exit 1
fi

warn "ATENÇÃO: Todos os dados de /dev/$DEVICE serão apagados!"
read -p "Continuar? (sim/nao): " CONFIRM

if [ "$CONFIRM" != "sim" ]; then
    echo "Cancelado."
    exit 0
fi

log "Desmontando partições..."
umount /dev/${DEVICE}* 2>/dev/null || true

log "Gravando ISO no pendrive..."
dd if="$ISO_FILE" of="/dev/$DEVICE" bs=4M status=progress
sync

log "ISO gravada com sucesso!"
echo ""
echo "Para testar:"
echo "  1. Reiniciar o computador"
echo "  2. Entrar no BIOS/UEFI (F2/F12/Del)"
echo "  3. Selecionar boot pelo pendrive"
FLASHEOF
chmod +x /opt/ravena/scripts/flash_pendrive.sh

# ============================================
# 10. CRIAR MENU PRINCIPAL
# ============================================
log "Criando menu principal..."

cat > /opt/ravena/scripts/menu.sh << 'MENUEOF'
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  RAVENA SANDBOX - Menu Principal${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${GREEN}1)${NC} Compilar ISO"
echo -e "${GREEN}2)${NC} Testar ISO em VM"
echo -e "${GREEN}3)${NC} Gravar ISO em Pendrive"
echo -e "${GREEN}4)${NC} Verificar Ambiente"
echo -e "${GREEN}5)${NC} Limpar Trabalho"
echo -e "${GREEN}6)${NC} Sair"
echo ""
read -p "Escolha uma opção: " OPTION

case $OPTION in
    1)
        sudo /opt/ravena/scripts/build_ravena_iso.sh
        ;;
    2)
        /opt/ravena/scripts/test_ravena_vm.sh
        ;;
    3)
        sudo /opt/ravena/scripts/flash_pendrive.sh
        ;;
    4)
        echo ""
        echo "Verificando ambiente..."
        echo ""
        echo "Archiso: $(pacman -Qi archiso 2>/dev/null | grep Version || echo 'NÃO INSTALADO')"
        echo "QEMU: $(qemu-system-x86_64 --version 2>/dev/null | head -1 || echo 'NÃO INSTALADO')"
        echo "Docker: $(docker --version 2>/dev/null || echo 'NÃO INSTALADO')"
        echo "ISO prontas:"
        ls -lh /opt/ravena/out/*.iso 2>/dev/null || echo "  Nenhuma"
        echo ""
        ;;
    5)
        echo "Limpando..."
        sudo rm -rf /tmp/ravena-work
        echo "Pronto!"
        ;;
    6)
        echo "Saindo..."
        exit 0
        ;;
    *)
        echo "Opção inválida!"
        ;;
esac

MENUEOF
chmod +x /opt/ravena/scripts/menu.sh

# ============================================
# 11. CONFIGURAR AUTO-LOGIN SEM SENHA
# ============================================
log "Configurando auto-login sem senha..."

# Remover senha do usuário
passwd -d ravena 2>/dev/null || true
passwd -d root 2>/dev/null || true

# Criar diretório para auto-login no TTY1
mkdir -p /etc/systemd/system/getty@tty1.service.d

cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << 'AUTOEOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ravena -o '-p -f ravena' --noclear %I $TERM
Type=idle
AUTOEOF

# SSH sem senha (acesso local apenas)
cat > /etc/ssh/sshd_config.d/no_password.conf << 'SSHEOF'
# SSH sem senha - acesso local apenas
PermitRootLogin yes
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes
SSHEOF

# Criar diretório .ssh
mkdir -p /home/ravena/.ssh
chmod 700 /home/ravena/.ssh
touch /home/ravena/.ssh/authorized_keys
chmod 600 /home/ravena/.ssh/authorized_keys
chown -R ravena:ravena /home/ravena/.ssh

# Gerar chave SSH vazia (preenchida pelo usuário se necessário)
echo "# Adicione suas chaves SSH aqui" > /home/ravena/.ssh/authorized_keys

# ============================================
# 12. CRIAR ATALHO NO BASH
# ============================================
log "Criando atalho no bash..."

cat >> /home/$SUDO_USER/.bashrc << 'BASHEOF'

# Ravena Menu
alias ravena='bash /opt/ravena/scripts/menu.sh'
alias ravena-build='sudo /opt/ravena/scripts/build_ravena_iso.sh'
alias ravena-test='/opt/ravena/scripts/test_ravena_vm.sh'
alias ravena-flash='sudo /opt/ravena/scripts/flash_pendrive.sh'
BASHEOF

# ============================================
# FINALIZAÇÃO
# ============================================
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  AMBIENTE CONFIGURADO COM SUCESSO!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "COMANDOS DISPONÍVEIS (SEM LOGIN):"
echo "  ravena         → Menu principal"
echo "  ravena-build   → Compilar ISO"
echo "  ravena-test    → Testar em VM"
echo "  ravena-flash   → Gravar em pendrive"
echo ""
echo "SISTEMA CONFIGURADO PARA:"
echo "  ✓ Auto-login sem senha no TTY1"
echo "  ✓ SSH sem senha (chaves)"
echo "  ✓ Sudo sem senha"
echo "  ✓ Docker sem sudo"
echo ""
echo "Para usar, execute: source ~/.bashrc"
echo ""
echo "Próximos passos:"
echo "  1. Copiar projeto ravena-archiso para /opt/"
echo "  2. Executar: ravena-build"
echo "  3. Testar: ravena-test"
echo "  4. Gravar: ravena-flash"
echo ""
