#!/bin/bash
# ============================================
# TEST_ISO.SH - Testar ISO em VM
# ============================================
# Testa a ISO compilada em uma máquina virtual
# usando QEMU/KVM.
# ============================================

echo "============================================"
echo "  TESTANDO ISO RAVENA EM VM"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
VM_NAME="ravena-test"
VM_RAM="2048"
VM_DISK="20G"
VM_CPUS="2"

# Verificar dependências
echo -e "${BLUE}[1/4]${NC} Verificando dependências..."

if ! command -v qemu-system-x86_64 &> /dev/null; then
    echo -e "${YELLOW}[AVISO]${NC} QEMU não encontrado - instalando..."
    sudo pacman -S --noconfirm qemu-full virt-manager
fi

echo -e "${GREEN}[OK]${NC} Dependências verificadas"

# Encontrar ISO
echo -e "${BLUE}[2/4]${NC} Procurando ISO..."

ISO_FILE=$(find "$HOME/Desktop" -name "ravena-archlinux*.iso" -type f | head -1)

if [ -z "$ISO_FILE" ]; then
    echo -e "${RED}[ERRO]${NC} ISO não encontrada no Desktop"
    echo "Execute build_iso.sh primeiro"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} ISO encontrada: $ISO_FILE"

# Criar VM
echo -e "${BLUE}[3/4]${NC} Criando VM..."

# Verificar se VM já existe
if virsh dominfo "$VM_NAME" &> /dev/null; then
    echo -e "${YELLOW}[AVISO]${NC} VM já existe - removendo..."
    virsh destroy "$VM_NAME" 2>/dev/null || true
    virsh undefine "$VM_NAME" --remove-all-storage 2>/dev/null || true
fi

# Criar disco virtual
qemu-img create -f qcow2 "/tmp/${VM_NAME}.qcow2" "$VM_DISK"

# Iniciar VM
echo -e "${BLUE}[4/4]${NC} Iniciando VM..."

echo ""
echo "============================================"
echo "  VM INICIADA"
echo "============================================"
echo ""
echo "A VM está iniciando com a ISO Ravena."
echo ""
echo "Para acessar a VM:"
echo "  - Use o console do QEMU"
echo "  - Ou acesse via VNC: localhost:5900"
echo ""
echo "Para parar a VM:"
echo "  virsh destroy $VM_NAME"
echo ""
echo "============================================"

qemu-system-x86_64 \
    -name "$VM_NAME" \
    -m "$VM_RAM" \
    -smp "$VM_CPUS" \
    -cpu host \
    -enable-kvm \
    -drive file="/tmp/${VM_NAME}.qcow2",format=qcow2 \
    -cdrom "$ISO_FILE" \
    -boot d \
    -vnc :0 \
    -net nic \
    -net user,hostfwd=tcp::8080-:8080
