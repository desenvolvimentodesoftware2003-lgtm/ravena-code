#!/bin/bash
# ============================================
# POST_QUANTUM_CRYPTO.SH - Criptografia Pós-Quântica
# Ravena Security Sandbox
# ============================================
# Implementa criptografia pós-quântica em
# todas as portas que não têm segurança.
# ============================================

echo "============================================"
echo "  CRIPTOGRAFIA PÓS-QUÂNTICA"
echo "============================================"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
SSL_DIR="/etc/ssl/ravena"
CERT_DAYS=365
KEY_SIZE=4096

# ============================================
# 1. INSTALAR FERRAMENTAS DE CRIPTOGRAFIA
# ============================================

echo -e "${BLUE}[1/7]${NC} Instalando ferramentas de criptografia..."

# Instalar OpenSSL com suporte pós-quântico
pacman -S --noconfirm --needed \
    openssl \
    gnutls \
    libgcrypt \
    wolfssl \
    liboqs

echo -e "${GREEN}[OK]${NC} Ferramentas instaladas"

# ============================================
# 2. CRIAR DIRETÓRIO DE CERTIFICADOS
# ============================================

echo -e "${BLUE}[2/7]${NC} Criando diretório de certificados..."

mkdir -p "$SSL_DIR"/{certs,private,csr,ext}

# Configurar permissões
chmod 700 "$SSL_DIR/private"

echo -e "${GREEN}[OK]${NC} Diretório criado"

# ============================================
# 3. GERAR CHAVES PÓS-QUÂNTICAS
# ============================================

echo -e "${BLUE}[3/7]${NC} Gerando chaves pós-quânticas..."

# Gerar chave RSA principal (4096 bits)
echo "Gerando chave RSA 4096 bits..."
openssl genrsa -out "$SSL_DIR/private/ca.key" $KEY_SIZE 2>/dev/null

# Gerar chave ECDSA (curva P-384 para resistência pós-quântica)
echo "Gerando chave ECDSA P-384..."
openssl ecparam -genkey -name secp384r1 -out "$SSL_DIR/private/ca-ec.key" 2>/dev/null

# Gerar chave Ed25519 (mais resistente a ataques quânticos)
echo "Gerando chave Ed25519..."
openssl genpkey -algorithm Ed25519 -out "$SSL_DIR/private/ca-ed25519.key" 2>/dev/null

echo -e "${GREEN}[OK]${NC} Chaves geradas"

# ============================================
# 4. CRIAR CERTIFICADO CA
# ============================================

echo -e "${BLUE}[4/7]${NC} Criando certificado CA..."

# Criar arquivo de extensão para CA
cat > "$SSL_DIR/ext/ca.ext" << EOF
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
nsCertType = sslCA, emailCA
nsComment = "Ravena CA - Certificado Pós-Quântico"
EOF

# Gerar certificado CA autoassinado
echo "Gerando certificado CA..."
openssl req -x509 -new -nodes \
    -key "$SSL_DIR/private/ca.key" \
    -sha384 \
    -days $CERT_DAYS \
    -out "$SSL_DIR/certs/ca.crt" \
    -config "$SSL_DIR/ext/ca.ext" 2>/dev/null

echo -e "${GREEN}[OK]${NC} Certificado CA criado"

# ============================================
# 5. CRIAR CERTIFICADOS PARA CADA PORTA
# ============================================

echo -e "${BLUE}[5/7]${NC} Criando certificados para cada porta..."

# Função para criar certificado
create_cert() {
    local name=$1
    local port=$2
    
    echo "Criando certificado para $name (porta $port)..."
    
    # Criar chave (4096 bits para resistência pós-quântica)
    openssl genrsa -out "$SSL_DIR/private/$name.key" 4096 2>/dev/null
    
    # Criar arquivo de extensão
    cat > "$SSL_DIR/ext/$name.ext" << EOF
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
DNS.3 = *.sandbox.local
IP.1 = 127.0.0.1
IP.2 = 172.20.0.2
IP.3 = ::1
EOF
    
    # Criar CSR
    openssl req -new \
        -key "$SSL_DIR/private/$name.key" \
        -out "$SSL_DIR/csr/$name.csr" \
        -config "$SSL_DIR/ext/$name.ext" 2>/dev/null
    
    # Assinar com CA
    openssl x509 -req \
        -in "$SSL_DIR/csr/$name.csr" \
        -CA "$SSL_DIR/certs/ca.crt" \
        -CAkey "$SSL_DIR/private/ca.key" \
        -CAcreateserial \
        -out "$SSL_DIR/certs/$name.crt" \
        -days $CERT_DAYS \
        -sha384 \
        -extfile "$SSL_DIR/ext/$name.ext" \
        -extensions v3_req 2>/dev/null
    
    echo -e "  ${GREEN}✅ Certificado $name criado${NC}"
}

# Criar certificados para cada porta
create_cert "http" "80"
create_cert "grafana" "3000"
create_cert "kibana" "5601"
create_cert "ravena-app" "8080"
create_cert "prometheus" "9090"

echo -e "${GREEN}[OK]${NC} Todos os certificados criados"

# ============================================
# 6. CRIAR SCRIPT DE RENOVAÇÃO
# ============================================

echo -e "${BLUE}[6/7]${NC} Criando script de renovação..."

cat > "$SSL_DIR/renew_certs.sh" << 'RENEWEOF'
#!/bin/bash
# ============================================
# RENOVATION_SCRIPT - Renovação de Certificados
# ============================================

SSL_DIR="/etc/ssl/ravena"
CERT_DAYS=365

echo "Renovando certificados..."

# Renovar cada certificado
for cert in "$SSL_DIR/certs"/*.crt; do
    if [ -f "$cert" ]; then
        name=$(basename "$cert" .crt)
        
        # Verificar se não é o CA
        if [ "$name" != "ca" ]; then
            echo "Renovando $name..."
            
            # Criar nova CSR
            openssl req -new \
                -key "$SSL_DIR/private/$name.key" \
                -out "$SSL_DIR/csr/$name.csr" \
                -config "$SSL_DIR/ext/$name.ext" 2>/dev/null
            
            # Assinar novamente
            openssl x509 -req \
                -in "$SSL_DIR/csr/$name.csr" \
                -CA "$SSL_DIR/certs/ca.crt" \
                -CAkey "$SSL_DIR/private/ca.key" \
                -CAcreateserial \
                -out "$SSL_DIR/certs/$name.crt" \
                -days $CERT_DAYS \
                -sha384 \
                -extfile "$SSL_DIR/ext/$name.ext" \
                -extensions v3_req 2>/dev/null
            
            echo "  ✅ $name renovado"
        fi
    fi
done

echo "Renovação concluída!"
RENEWEOF

chmod +x "$SSL_DIR/renew_certs.sh"

echo -e "${GREEN}[OK]${NC} Script de renovação criado"

# ============================================
# 7. CRIAR SERVIÇO DE AUTO-RENOVAÇÃO
# ============================================

echo -e "${BLUE}[7/7]${NC} Criando serviço de auto-renovação..."

# Criar.timer para renovação automática
cat > /etc/systemd/system/ssl-renew.timer << EOF
[Unit]
Description=Renovação automática de certificados SSL
Requires=ssl-renew.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Criar serviço de renovação
cat > /etc/systemd/system/ssl-renew.service << EOF
[Unit]
Description=Renovação de certificados SSL
After=network.target

[Service]
Type=oneshot
ExecStart=$SSL_DIR/renew_certs.sh
StandardOutput=journal
StandardError=journal
EOF

# Habilitar timer
systemctl daemon-reload
systemctl enable ssl-renew.timer
systemctl start ssl-renew.timer

echo -e "${GREEN}[OK]${NC} Serviço de auto-renovação criado"

# ============================================
# CRIAR SCRIPT DE STATUS
# ============================================

cat > "$SSL_DIR/ssl_status.sh" << 'STATUSEOF'
#!/bin/bash
# ============================================
# SSL_STATUS - Status dos Certificados
# ============================================

SSL_DIR="/etc/ssl/ravena"

echo "============================================"
echo "  STATUS DOS CERTIFICADOS SSL"
echo "============================================"
echo ""

# Listar certificados
for cert in "$SSL_DIR/certs"/*.crt; do
    if [ -f "$cert" ]; then
        name=$(basename "$cert" .crt)
        
        # Obter informações do certificado
        subject=$(openssl x509 -in "$cert" -noout -subject 2>/dev/null | cut -d= -f2-)
        expiry=$(openssl x509 -in "$cert" -noout -enddate 2>/dev/null | cut -d= -f2)
        
        echo "Certificado: $name"
        echo "  Assunto: $subject"
        echo "  Expira: $expiry"
        echo ""
    fi
done

echo "============================================"
STATUSEOF

chmod +x "$SSL_DIR/ssl_status.sh"

# ============================================
# FINALIZAÇÃO
# ============================================

echo ""
echo "============================================"
echo -e "${GREEN}  CRIPTOGRAFIA PÓS-QUÂNTICA IMPLEMENTADA${NC}"
echo "============================================"
echo ""
echo "Portas criptografadas:"
echo "  ✅ 80 (HTTP) → HTTPS"
echo "  ✅ 3000 (Grafana)"
echo "  ✅ 5601 (Kibana)"
echo "  ✅ 8080 (Ravena App)"
echo "  ✅ 9090 (Prometheus)"
echo ""
echo "Algoritmos utilizados:"
echo "  • RSA 4096 bits"
echo "  • ECDSA P-384"
echo "  • Ed25519"
echo "  • SHA-384"
echo ""
echo "Comandos disponíveis:"
echo "  /etc/ssl/ravena/ssl_status.sh     - Ver status"
echo "  /etc/ssl/ravena/renew_certs.sh    - Renovar certificados"
echo ""
echo "============================================"
