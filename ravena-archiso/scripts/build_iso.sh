#!/bin/bash
# ============================================
# BUILD_ISO.SH - Compilar ISO Ravena
# ============================================
# Compila a ISO personalizada do Arch Linux
# com a Ravena pré-instalada.
#
# Uso: ./build_iso.sh [--clean] [--fast]
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROFILE_DIR="$PROJECT_DIR/archiso/configs/ravena"
WORK_DIR="/tmp/ravena-build"
OUTPUT_DIR="$PROJECT_DIR/output"

# Flags
CLEAN_BUILD=false
FAST_BUILD=false

# Parse argumentos
for arg in "$@"; do
    case $arg in
        --clean) CLEAN_BUILD=true ;;
        --fast) FAST_BUILD=true ;;
        --help|-h)
            echo "Uso: ./build_iso.sh [opções]"
            echo ""
            echo "Opções:"
            echo "  --clean  Limpar diretório de trabalho antes de compilar"
            echo "  --fast   Compilação rápida (compressão mínima)"
            echo "  --help   Mostrar esta ajuda"
            exit 0
            ;;
    esac
done

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  COMPILANDO ISO RAVENA SECURITY SANDBOX${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Verificar se está no Arch Linux
if ! grep -q "Arch Linux" /etc/os-release 2>/dev/null; then
    echo -e "${RED}[ERRO]${NC} Este script deve ser executado no Arch Linux"
    echo "Execute em uma VM com Arch Linux"
    echo ""
    echo "Alternativa: Use o Docker"
    echo "  docker run -it archlinux:latest /bin/bash"
    echo " 然后 monte o projeto e execute o build"
    exit 1
fi

# Verificar se é root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[AVISO]${NC} Recomenda-se executar como root"
    echo "Alguns passos podem falhar sem permissões de root"
    echo ""
fi

# Verificar dependências
echo -e "${BLUE}[1/8]${NC} Verificando dependências..."

DEPS_OK=true

for cmd in mkarchiso pacman mkinitcpio; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}[ERRO]${NC} Comando não encontrado: $cmd"
        DEPS_OK=false
    fi
done

if [ "$DEPS_OK" = false ]; then
    echo ""
    echo "Execute primeiro: ./build_env.sh"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Dependências verificadas"

# Verificar estrutura do projeto
echo -e "${BLUE}[2/8]${NC} Verificando estrutura do projeto..."

if [ ! -d "$PROFILE_DIR" ]; then
    echo -e "${RED}[ERRO]${NC} Diretório do perfil não encontrado: $PROFILE_DIR"
    exit 1
fi

if [ ! -f "$PROFILE_DIR/profiledef.sh" ]; then
    echo -e "${RED}[ERRO]${NC} profiledef.sh não encontrado"
    exit 1
fi

if [ ! -f "$PROFILE_DIR/packages.x86_64" ]; then
    echo -e "${RED}[ERRO]${NC} packages.x86_64 não encontrado"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Estrutura verificada"

# Gerar senhas se não existirem
echo -e "${BLUE}[3/8]${NC} Verificando senhas..."

if [ ! -f "$PROJECT_DIR/.env.passwords" ]; then
    echo -e "${YELLOW}[AVISO]${NC} Senhas não encontradas, gerando..."
    bash "$SCRIPT_DIR/generate_passwords.sh"
else
    echo -e "${GREEN}[OK]${NC} Senhas encontradas"
fi

# Limpar diretório de trabalho se solicitado
echo -e "${BLUE}[4/8]${NC} Preparando diretório de trabalho..."

if [ "$CLEAN_BUILD" = true ] || [ ! -d "$WORK_DIR" ]; then
    echo -e "${YELLOW}[LIMPANDO]${NC} Removendo diretório de trabalho anterior..."
    sudo rm -rf "$WORK_DIR"
fi

mkdir -p "$WORK_DIR"
mkdir -p "$OUTPUT_DIR"

echo -e "${GREEN}[OK]${NC} Diretório preparado"

# Copiar perfil
echo -e "${BLUE}[5/8]${NC} Copiando perfil..."

rm -rf "$WORK_DIR/ravena"
cp -r "$PROFILE_DIR" "$WORK_DIR/ravena"

echo -e "${GREEN}[OK]${NC} Perfil copiado"

# Preparar airootfs
echo -e "${BLUE}[6/8]${NC} Preparando sistema de arquivos..."

# Tornar scripts executáveis
find "$WORK_DIR/ravena/airootfs" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Copiar arquivos do sandbox-ravena para a ISO
SANDBOX_DIR="$PROJECT_DIR/../sandbox-ravena"
if [ -d "$SANDBOX_DIR" ]; then
    echo -e "${YELLOW}[INFO]${NC} Copiando sandbox-ravena para a ISO..."
    mkdir -p "$WORK_DIR/ravena/airootfs/opt/ravena"
    cp -r "$SANDBOX_DIR"/* "$WORK_DIR/ravena/airootfs/opt/ravena/" 2>/dev/null || true
    echo -e "${GREEN}[OK]${NC} Sandbox copiado"
else
    echo -e "${YELLOW}[AVISO]${NC} Diretório sandbox-ravena não encontrado"
    echo "O sandbox será instalado depois via script de instalação"
fi

echo -e "${GREEN}[OK]${NC} Sistema de arquivos preparado"

# Compilar ISO
echo -e "${BLUE}[7/8]${NC} Compilando ISO..."
echo -e "${CYAN}Isso pode levar 15-30 minutos...${NC}"
echo ""

# Configurar opções de compressão
if [ "$FAST_BUILD" = true ]; then
    COMPRESSION="-comp gzip"
    echo -e "${YELLOW}[MODO RÁPIDO]${NC} Compressão gzip (mais rápido, ISO maior)"
else
    COMPRESSION="-comp zstd -Xcompression-level 19"
    echo -e "${GREEN}[MODO NORMAL]${NC} Compressão zstd (mais lento, ISO menor)"
fi

# Compilar com mkarchiso
cd /usr/share/archiso/archiso
sudo mkarchiso -v \
    -w "$WORK_DIR" \
    -o "$OUTPUT_DIR" \
    "$WORK_DIR/ravena"

echo -e "${GREEN}[OK]${NC} ISO compilada"

# Verificar ISO
echo -e "${BLUE}[8/8]${NC} Verificando ISO..."

ISO_FILE=$(find "$OUTPUT_DIR" -name "*.iso" -type f | head -1)

if [ -f "$ISO_FILE" ]; then
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    ISO_NAME=$(basename "$ISO_FILE")
    
    echo -e "${GREEN}[OK]${NC} ISO encontrada!"
    echo ""
    echo -e "  Arquivo: ${CYAN}$ISO_NAME${NC}"
    echo -e "  Tamanho: ${CYAN}$ISO_SIZE${NC}"
    echo -e "  Local:   ${CYAN}$ISO_FILE${NC}"
else
    echo -e "${RED}[ERRO]${NC} ISO não encontrada após compilação"
    echo "Verifique os logs de erro acima"
    exit 1
fi

# Gerar checksum
echo -e "${BLUE}[BÔNUS]${NC} Gerando checksum..."
sha256sum "$ISO_FILE" > "$ISO_FILE.sha256"
echo -e "${GREEN}[OK]${NC} Checksum gerado"

# Resumo final
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  ISO COMPILADA COM SUCESSO!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "  Arquivo: ${CYAN}$ISO_NAME${NC}"
echo -e "  Tamanho: ${CYAN}$ISO_SIZE${NC}"
echo -e "  Local:   ${CYAN}$OUTPUT_DIR/${NC}"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo ""
echo "  1. Copiar ISO para pendrive:"
echo "     ${CYAN}sudo dd if=$ISO_FILE of=/dev/sdX bs=4M status=progress${NC}"
echo ""
echo "     Ou use Etcher/Rufus (Windows)"
echo ""
echo "  2. Bootar pelo pendrive:"
echo "     - Reiniciar computador"
echo "     - Pressionar F12 (ou F2/Del) para boot menu"
echo "     - Selecionar pendrive"
echo ""
echo "  3. A Ravena já estará rodando!"
echo ""
echo -e "${GREEN}============================================${NC}"
echo ""
