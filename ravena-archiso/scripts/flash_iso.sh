#!/bin/bash
# ============================================
# FLASH_ISO.SH - Gravar ISO no Pendrive
# ============================================
# Grava a ISO compilada em um pendrive
# para boot via BIOS/UEFI.
# ============================================

echo "============================================"
echo "  GRAVANDO ISO NO PENDRIVE"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERRO]${NC} Execute como root: sudo ./flash_iso.sh"
    exit 1
fi

# Listar dispositivos
echo -e "${BLUE}[1/5]${NC} Listando dispositivos..."

echo "Dispositivos disponíveis:"
lsblk -d -o NAME,SIZE,MODEL | grep -v loop

echo ""
read -p "Digite o nome do pendrive (ex: sdb): " DEVICE

if [ ! -b "/dev/$DEVICE" ]; then
    echo -e "${RED}[ERRO]${NC} Dispositivo não encontrado: /dev/$DEVICE"
    exit 1
fi

# Encontrar ISO
echo -e "${BLUE}[2/5]${NC} Procurando ISO..."

ISO_FILE=$(find "$HOME/Desktop" -name "ravena-archlinux*.iso" -type f | head -1)

if [ -z "$ISO_FILE" ]; then
    echo -e "${RED}[ERRO]${NC} ISO não encontrada no Desktop"
    echo "Execute build_iso.sh primeiro"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} ISO encontrada: $ISO_FILE"

# Confirmar
echo -e "${YELLOW}[AVISO]${NC} ATENÇÃO: Todos os dados em /dev/$DEVICE serão apagados!"
echo "ISO: $ISO_FILE"
echo "Dispositivo: /dev/$DEVICE"
echo ""
read -p "Continuar? (s/N): " CONFIRM

if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    echo "Operação cancelada"
    exit 0
fi

# Desmontar partitions
echo -e "${BLUE}[3/5]${NC} Desmontando partitions..."

umount /dev/${DEVICE}* 2>/dev/null || true

# Gravar ISO
echo -e "${BLUE}[4/5]${NC} Gravando ISO..."

dd if="$ISO_FILE" of="/dev/$DEVICE" bs=4M status=progress conv=fsync

echo -e "${GREEN}[OK]${NC} ISO gravada"

# Sincronizar
echo -e "${BLUE}[5/5]${NC} Sincronizando..."

sync

echo ""
echo "============================================"
echo -e "${GREEN}  ISO GRAVADA COM SUCESSO${NC}"
echo "============================================"
echo ""
echo "Pendrive pronto: /dev/$DEVICE"
echo ""
echo "Para usar:"
echo "1. Insira o pendrive no PC"
echo "2. Reinicie o PC"
echo "3. Aperte F12 para selecionar boot"
echo "4. Selecione o pendrive"
echo "5. A Ravena já estará rodando!"
echo ""
echo "============================================"
