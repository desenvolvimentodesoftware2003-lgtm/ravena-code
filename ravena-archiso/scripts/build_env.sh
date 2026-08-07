#!/bin/bash
# ============================================
# BUILD_ENV.SH - Preparar Ambiente de Build
# ============================================
# Instala dependências e prepara o ambiente
# para compilar a ISO Ravena
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  PREPARANDO AMBIENTE DE BUILD RAVENA${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERRO]${NC} Execute como root: sudo ./build_env.sh"
    exit 1
fi

# Verificar Arch Linux
if ! grep -q "Arch Linux" /etc/os-release 2>/dev/null; then
    echo -e "${RED}[ERRO]${NC} Este script deve ser executado no Arch Linux"
    echo "Use uma VM com Arch Linux ou instale Arch primeiro"
    exit 1
fi

echo -e "${BLUE}[1/6]${NC} Atualizando sistema..."
pacman -Syu --noconfirm
echo -e "${GREEN}[OK]${NC} Sistema atualizado"

echo -e "${BLUE}[2/6]${NC} Instalando pacotes básicos..."
pacman -S --noconfirm \
    base-devel \
    git \
    curl \
    wget \
    archiso \
    mkinitcpio \
    squashfs-tools \
    dosfstools \
    e2fsprogs \
    libisoburn \
    mtools \
    parted
echo -e "${GREEN}[OK]${NC} Pacotes básicos instalados"

echo -e "${BLUE}[3/6]${NC} Instalando ferramentas Python..."
pacman -S --noconfirm \
    python \
    python-pip \
    python-setuptools
echo -e "${GREEN}[OK]${NC} Python instalado"

echo -e "${BLUE}[4/6]${NC} Verificando archiso..."
if ! command -v mkarchiso &> /dev/null; then
    echo -e "${YELLOW}[AVISO]${NC} mkarchiso não encontrado, instalando archiso..."
    pacman -S --noconfirm archiso
fi
echo -e "${GREEN}[OK]${NC} archiso verificado"

echo -e "${BLUE}[5/6]${NC} Criando diretório de trabalho..."
WORK_DIR="/tmp/ravena-build"
mkdir -p "$WORK_DIR"
echo -e "${GREEN}[OK]${NC} Diretório criado: $WORK_DIR"

echo -e "${BLUE}[6/6]${NC} Verificando estrutura do projeto..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -d "$PROJECT_DIR/archiso/configs/ravena" ]; then
    echo -e "${RED}[ERRO]${NC} Estrutura do projeto não encontrada"
    echo "Execute este script do diretório ravena-archiso/scripts/"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Estrutura do projeto verificada"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  AMBIENTE PREPARADO COM SUCESSO${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Próximo passo: Execute ./build_iso.sh para compilar a ISO"
echo ""
