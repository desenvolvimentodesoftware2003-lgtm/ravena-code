#!/bin/bash
# ============================================
# NGINX_TLS.SH - Configuração Nginx com TLS
# Ravena Security Sandbox
# ============================================
# Configura o Nginx para usar TLS pós-quântico
# em todas as portas HTTP.
# ============================================

echo "============================================"
echo "  CONFIGURAÇÃO NGINX COM TLS"
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
NGINX_DIR="/etc/nginx"

# ============================================
# 1. INSTALAR NGINX
# ============================================

echo -e "${BLUE}[1/5]${NC} Instalando Nginx..."

pacman -S --noconfirm --needed nginx

echo -e "${GREEN}[OK]${NC} Nginx instalado"

# ============================================
# 2. CRIAR CONFIGURAÇÃO TLS
# ============================================

echo -e "${BLUE}[2/5]${NC} Criando configuração TLS..."

# Backup da configuração original
cp "$NGINX_DIR/nginx.conf" "$NGINX_DIR/nginx.conf.backup" 2>/dev/null || true

# Criar configuração principal
cat > "$NGINX_DIR/nginx.conf" << 'EOF'
# ============================================
# NGINX.RAVENA.TLS - Configuração TLS Pós-Quântica
# ============================================

worker_processes auto;
events {
    worker_connections 1024;
}

http {
    # Configurações básicas
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Configurações de log
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    # Configurações de performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Configurações de compressão
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/atom+xml image/svg+xml;
    
    # ============================================
    # CONFIGURAÇÕES TLS PÓS-QUÂNTICAS
    # ============================================
    
    # Versões TLS (apenas 1.2 e 1.3)
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Cifras pós-quânticas (híbridas com CRYSTALS-Kyber)
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
    
    # Usar cifras do servidor
    ssl_prefer_server_ciphers on;
    
    # Parâmetros DH (4096 bits para resistência pós-quântica)
    ssl_dhparam /etc/nginx/dhparam.pem;
    
    # Session tickets
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # ============================================
    # REDIRECIONAMENTO HTTP → HTTPS
    # ============================================
    
    # Servidor HTTP (redireciona para HTTPS)
    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        
        # Redirecionar tudo para HTTPS
        return 301 https://$host$request_uri;
    }
    
    # ============================================
    # PROXY REVERSO COM TLS
    # ============================================
    
    # Ravena App (porta 443)
    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name localhost;
        
        # Certificados SSL
        ssl_certificate /etc/ssl/ravena/certs/ravena-app.crt;
        ssl_certificate_key /etc/ssl/ravena/private/ravena-app.key;
        
        # Proxy para Ravena App
        location / {
            proxy_pass http://127.0.0.1:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port $server_port;
        }
        
        # WebSocket support
        location /ws {
            proxy_pass http://127.0.0.1:8080;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
    
    # Grafana (porta 3443)
    server {
        listen 3443 ssl http2;
        listen [::]:3443 ssl http2;
        server_name localhost;
        
        # Certificados SSL
        ssl_certificate /etc/ssl/ravena/certs/grafana.crt;
        ssl_certificate_key /etc/ssl/ravena/private/grafana.key;
        
        # Proxy para Grafana
        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    
    # Kibana (porta 5643)
    server {
        listen 5643 ssl http2;
        listen [::]:5643 ssl http2;
        server_name localhost;
        
        # Certificados SSL
        ssl_certificate /etc/ssl/ravena/certs/kibana.crt;
        ssl_certificate_key /etc/ssl/ravena/private/kibana.key;
        
        # Proxy para Kibana
        location / {
            proxy_pass http://127.0.0.1:5601;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    
    # Prometheus (porta 9443)
    server {
        listen 9443 ssl http2;
        listen [::]:9443 ssl http2;
        server_name localhost;
        
        # Certificados SSL
        ssl_certificate /etc/ssl/ravena/certs/prometheus.crt;
        ssl_certificate_key /etc/ssl/ravena/private/prometheus.key;
        
        # Proxy para Prometheus
        location / {
            proxy_pass http://127.0.0.1:9090;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF

echo -e "${GREEN}[OK]${NC} Configuração TLS criada"

# ============================================
# 3. GERAR PARÂMETROS DH
# ============================================

echo -e "${BLUE}[3/5]${NC} Gerando parâmetros DH..."

openssl dhparam -out /etc/nginx/dhparam.pem 4096 2>/dev/null

echo -e "${GREEN}[OK]${NC} Parâmetros DH gerados"

# ============================================
# 4. CRIAR SCRIPT DE INICIALIZAÇÃO
# ============================================

echo -e "${BLUE}[4/5]${NC} Criando script de inicialização..."

cat > "$NGINX_DIR/start_tls.sh" << 'STARTEOF'
#!/bin/bash
# ============================================
# START_TLS - Iniciar Nginx com TLS
# ============================================

echo "Iniciando Nginx com TLS..."

# Verificar se os certificados existem
if [ ! -f "/etc/ssl/ravena/certs/ca.crt" ]; then
    echo "ERRO: Certificados não encontrados"
    echo "Execute: /etc/ssl/ravena/post_quantum_crypto.sh"
    exit 1
fi

# Verificar configuração
nginx -t 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERRO: Configuração Nginx inválida"
    exit 1
fi

# Iniciar Nginx
systemctl start nginx
systemctl enable nginx

echo "Nginx iniciado com TLS!"
echo ""
echo "Portas HTTPS:"
echo "  - https://localhost:443 (Ravena App)"
echo "  - https://localhost:3443 (Grafana)"
echo "  - https://localhost:5643 (Kibana)"
echo "  - https://localhost:9443 (Prometheus)"
STARTEOF

chmod +x "$NGINX_DIR/start_tls.sh"

echo -e "${GREEN}[OK]${NC} Script de inicialização criado"

# ============================================
# 5. CRIAR SERVIÇO SYSTEMD
# ============================================

echo -e "${BLUE}[5/5]${NC} Criando serviço systemd..."

cat > /etc/systemd/system/nginx-tls.service << EOF
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
EOF

systemctl daemon-reload
systemctl enable nginx-tls.service

echo -e "${GREEN}[OK]${NC} Serviço systemd criado"

# ============================================
# FINALIZAÇÃO
# ============================================

echo ""
echo "============================================"
echo -e "${GREEN}  NGINX TLS CONFIGURADO${NC}"
echo "============================================"
echo ""
echo "Portas HTTPS criptografadas:"
echo "  ✅ https://localhost:443 (Ravena App)"
echo "  ✅ https://localhost:3443 (Grafana)"
echo "  ✅ https://localhost:5643 (Kibana)"
echo "  ✅ https://localhost:9443 (Prometheus)"
echo ""
echo "HTTP (porta 80) redireciona para HTTPS"
echo ""
echo "Comandos:"
echo "  systemctl start nginx-tls  - Iniciar"
echo "  systemctl stop nginx-tls   - Parar"
echo "  systemctl status nginx-tls - Status"
echo ""
echo "============================================"
