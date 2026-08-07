#!/bin/bash
# ============================================
# GERAR CERTIFICADOS SSL AUTOASSINADOS
# Ravena Security Sandbox
# ============================================
# Gera certificados SSL autoassinados para
# uso no Nginx durante desenvolvimento.
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Função de log
log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# Configurações
SSL_DIR="/opt/ravena/ssl"
DAYS=365
KEY_SIZE=2048

# Criar diretório SSL
mkdir -p "$SSL_DIR"

log "Gerando certificados SSL autoassinados..."
echo "  Diretório: $SSL_DIR"
echo "  Validade: $DAYS dias"
echo "  Tamanho da chave: $KEY_SIZE bits"
echo ""

# Gerar chave privada
log "Gerando chave privada..."
openssl genrsa -out "$SSL_DIR/server.key" $KEY_SIZE 2>/dev/null

# Gerar certificado autoassinado
log "Gerando certificado autoassinado..."
openssl req -x509 -new -nodes \
    -key "$SSL_DIR/server.key" \
    -sha256 \
    -days $DAYS \
    -out "$SSL_DIR/server.crt" \
    -subj "/C=BR/ST=Sao Paulo/L=Sao Paulo/O=Ravena Security Lab/OU=Sandbox/CN=localhost" \
    2>/dev/null

# Gerar arquivo de parâmetros DH
log "Gerando parâmetros DH (pode demorar)..."
openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048 2>/dev/null

# Verificar se os arquivos foram criados
if [ -f "$SSL_DIR/server.key" ] && [ -f "$SSL_DIR/server.crt" ]; then
    log "Certificados gerados com sucesso!"
    echo ""
    echo "Arquivos:"
    echo "  - Chave:     $SSL_DIR/server.key"
    echo "  - Certificado: $SSL_DIR/server.crt"
    echo "  - DH Param:  $SSL_DIR/dhparam.pem"
    echo ""
    
    # Mostrar informações do certificado
    log "Informações do certificado:"
    openssl x509 -in "$SSL_DIR/server.crt" -noout -subject -issuer -dates 2>/dev/null
else
    echo -e "${RED}[!] Erro ao gerar certificados!${NC}"
    exit 1
fi

echo ""
log "Certificados prontos para uso no Nginx!"
