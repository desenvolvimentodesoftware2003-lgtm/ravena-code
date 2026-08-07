#!/bin/bash
# ============================================
# PROFILEDEF.SH - Definição do Perfil Ravena
# Archiso - Arch Linux Customizado
# ============================================

# Informações da ISO
iso_name="ravena-archlinux"
iso_label="RAVENA_$(date +%Y%m)"
iso_publisher="Ravena Security Lab"
iso_application="Ravena Security Sandbox"
iso_version="$(date +%Y.%m.%d)"

# Configurações de boot (BIOS + UEFI)
bootmodes=('bios/grub' 'uefi/x64')
bootloader="grub"

# Configurações do sistema
timezone="America/Sao_Paulo"
locale="pt_BR.UTF-8"
keymap="br-abnt2"

# Configurações de rede
hostname="ravena-sandbox"
domain="sandbox.local"

# Configurações de usuário (SEM SENHA - uso pessoal)
user_name="ravena"
user_password=""
user_shell="/bin/bash"

# Configurações de ISO
image_type="iso"
iso_checksum="sha256"

# Configurações de squashfs
airootfs_image_type="squashfs"
airootfs_tar_options=('--zstd' '--acls' '--xattrs' '--numeric-owner')
airootfs_mksquashfs_options=('-comp' 'zstd' '-Xcompression-level' '19')

# Configurações de compressão
squashfs_compression="zstd"
squashfs_level=19
