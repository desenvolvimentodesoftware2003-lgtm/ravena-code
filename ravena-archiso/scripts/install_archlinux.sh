#!/bin/bash
# ============================================
# Script de Instalação Automatizada do Arch Linux
# Para VirtualBox/QEMU - Modo TTY
# ============================================

set -e

echo "============================================"
echo "  INSTALAÇÃO AUTOMÁTICA - ARCH LINUX"
echo "  Para Ambiente Ravena"
echo "============================================"
echo ""
echo "AVISO: Isso vai instalar Arch Linux no disco!"
echo "Para VM: Certifique-se de que está no instalador do Arch Linux"
echo ""

# ============================================
# CONFIGURAÇÕES (edite conforme necessário)
# ============================================
DISCO="/dev/sda"
TIMEZONE="America/Sao_Paulo"
LOCALE="pt_BR.UTF-8"
HOSTNAME="ravena-sandbox"
USERNAME="ravena"
PASSWORD=""
ROOT_PASSWORD=""

# ============================================
# FUNÇÕES
# ============================================
log() { echo "[+] $1"; }
error() { echo "[!] ERRO: $1"; exit 1; }

# ============================================
# 1. VERIFICAR SE ESTÁ NO INSTALADOR
# ============================================
if [ ! -f /arch/setup ]; then
    error "Execute este script no instalador do Arch Linux!"
fi

log "Iniciando instalação automatizada..."

# ============================================
# 2. CONFIGURAR REDE
# ============================================
log "Configurando rede..."
dhcpcd
ping -c 3 archlinux.org || error "Sem internet!"

# ============================================
# 3. SINCRONIZAR RELÓGIO
# ============================================
log "Sincronizando relógio..."
timedatectl set-ntp true

# ============================================
# 4. PARTICIONAR DISCO
# ============================================
log "Particionando disco $DISCO..."

# Limpar disco
wipefs -af "$DISCO"
sgdisk --zap-all "$DISCO"

# Criar partições
sgdisk -n 1:0:+512M -t 1:ef00 -c 1:"EFI" "$DISCO"
sgdisk -n 2:0:0 -t 2:8300 -c 2:"Root" "$DISCO"

# Formatando
log "Formatando partições..."
mkfs.fat -F32 ${DISCO}1
mkfs.ext4 -F ${DISCO}2

# Montando
log "Montando partições..."
mount ${DISCO}2 /mnt
mkdir -p /mnt/boot
mount ${DISCO}1 /mnt/boot

# ============================================
# 5. INSTALAR SISTEMA BASE
# ============================================
log "Instalando sistema base..."

pacstrap /mnt \
    base \
    linux \
    linux-firmware \
    nano \
    sudo \
    git \
    base-devel \
    python \
    python-pip \
    nodejs \
    npm \
    docker \
    docker-compose \
    nginx \
    postgresql \
    redis \
    tor \
    proxychains-ng \
    networkmanager \
    openssh \
    efibootmgr \
    grub \
    dosfstools \
    e2fsprogs

# ============================================
# 6. GERAR FSTAB
# ============================================
log "Gerando fstab..."
genfstab -U /mnt >> /mnt/etc/fstab

# ============================================
# 7. CHROOT E CONFIGURAÇÕES
# ============================================
log "Configurando sistema..."

arch-chroot /mnt /bin/bash << 'CHROOTEOF'

# Timezone
ln -sf /usr/share/timezone/America/Sao_Paulo /etc/localtime
hwclock --systohc

# Locale
echo "pt_BR.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen
echo "LANG=pt_BR.UTF-8" > /etc/locale.conf

# Hostname
echo "ravena-sandbox" > /etc/hostname

# Usuário SEM SENHA
useradd -m -G wheel -s /bin/bash ravena

# Root sem senha
passwd -d root

# Usuário sem senha
passwd -d ravena

# Sudo sem senha
cat > /etc/sudoers.d/ravena << 'SUDOEOF'
ravena ALL=(ALL) NOPASSWD:ALL
SUDOEOF
chmod 440 /etc/sudoers.d/ravena

# Auto-login sem senha no TTY1
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/autologin.conf << 'AUTOEOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ravena -o '-p -f ravena' --noclear %I $TERM
Type=idle
AUTOEOF

# Docker sem sudo
gpasswd -a ravena docker

# Habilitar serviços
systemctl enable docker
systemctl enable postgresql
systemctl enable redis
systemctl enable nginx
systemctl enable tor
systemctl enable NetworkManager
systemctl enable sshd

# Bootloader
bootctl --path=/boot install

echo "title Arch Linux" > /boot/loader/entries/arch.conf
echo "linux /vmlinuz-linux" >> /boot/loader/entries/arch.conf
echo "initrd /initramfs-linux.img" >> /boot/loader/entries/arch.conf
echo "options root=UUID=$(blkid -s UUID -o value /dev/sda2) rw" >> /boot/loader/entries/arch.conf

CHROOTEOF

# ============================================
# 8. FINALIZAR
# ============================================
log "Instalação concluída!"

echo ""
echo "============================================"
echo "  INSTALAÇÃO CONCLUÍDA!"
echo "============================================"
echo ""
echo "Próximos passos:"
echo "  1. Exit do chroot"
echo "  2. umount -R /mnt"
echo "  3. reboot"
echo "  4. Login: ravena / ravena123"
echo "  5. Configurar ambiente: sudo /opt/ravena/scripts/setup_ravena_env.sh"
echo ""
