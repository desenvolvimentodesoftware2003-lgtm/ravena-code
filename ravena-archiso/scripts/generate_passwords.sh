#!/bin/bash
# ============================================
# GENERATE_PASSWORDS.SH - Gerar Senhas Seguras
# ============================================
# Gera senhas aleatórias para todos os
# serviços da ISO Ravena
# ============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  GERANDO SENHAS SEGURAS${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Diretório de saída
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$PROJECT_DIR/.env.passwords"

# Função para gerar senha
generate_password() {
    local length=$1
    openssl rand -base64 $((length * 3 / 4)) | tr -d '/+=' | head -c $length
}

# Gerar senhas
echo -e "${BLUE}[1/5]${NC} Gerando senhas..."

DB_PASSWORD=$(generate_password 32)
REDIS_PASSWORD=$(generate_password 32)
JWT_SECRET=$(generate_password 64)
WEB_SECRET=$(generate_password 64)
GRAFANA_ADMIN_PASSWORD=$(generate_password 24)
ELASTIC_PASSWORD=$(generate_password 32)

echo -e "${GREEN}[OK]${NC} Senhas geradas"

# Criar arquivo .env
echo -e "${BLUE}[2/5]${NC} Criando arquivo .env..."

cat > "$OUTPUT_FILE" << EOF
# ============================================
# SENHAS SEGURAS - Ravena Sandbox
# Gerado em: $(date)
# ============================================
# IMPORTANTE: Não commit este arquivo!
# ============================================

# PostgreSQL
DB_PASSWORD=$DB_PASSWORD

# Redis
REDIS_PASSWORD=$REDIS_PASSWORD

# JWT
JWT_SECRET=$JWT_SECRET

# Flask
WEB_SECRET=$WEB_SECRET

# Grafana
GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD

# Elasticsearch
ELASTIC_PASSWORD=$ELASTIC_PASSWORD

# Usuário do sistema (sem senha - uso pessoal)
SYSTEM_USER=ravena
SYSTEM_PASSWORD=
EOF

echo -e "${GREEN}[OK]${NC} Arquivo criado: $OUTPUT_FILE"

# Criar arquivo SQL de inicialização
echo -e "${BLUE}[3/5]${NC} Criando script SQL de inicialização..."

SQL_FILE="$PROJECT_DIR/archiso/configs/ravena/airootfs/root/init_database.sql"

cat > "$SQL_FILE" << EOF
-- ============================================
-- INIT_DATABASE.SQL - Inicialização do Banco
-- Ravena Sandbox
-- ============================================

-- Criar banco de dados
CREATE DATABASE ravena;

-- Conectar ao banco
\\c ravena;

-- Habilitar extensões
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Criar tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Criar tabela de ataques
CREATE TABLE IF NOT EXISTS attacks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    attack_type VARCHAR(50),
    target VARCHAR(255),
    status VARCHAR(20),
    result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar tabela de logs
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    level VARCHAR(10),
    message TEXT,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar usuário admin com senha
INSERT INTO users (username, password_hash, role) VALUES
    ('admin', crypt('ravena2024', gen_salt('bf')), 'admin')
ON CONFLICT (username) DO NOTHING;

-- Criar usuário padrão
INSERT INTO users (username, password_hash, role) VALUES
    ('user', crypt('user2024', gen_salt('bf')), 'user')
ON CONFLICT (username) DO NOTHING;
EOF

echo -e "${GREEN}[OK]${NC} Script SQL criado: $SQL_FILE"

# Criar script de inicialização do banco
echo -e "${BLUE}[4/5]${NC} Criando script de inicialização do banco..."

DB_INIT_SCRIPT="$PROJECT_DIR/archiso/configs/ravena/airootfs/root/setup_database.sh"

cat > "$DB_INIT_SCRIPT" << 'DBEOF'
#!/bin/bash
# ============================================
# SETUP_DATABASE.SH - Configurar PostgreSQL
# ============================================

set -e

# Iniciar PostgreSQL
sudo -u postgres initdb -D /var/lib/postgres/data
sudo -u postgres pg_ctl -D /var/lib/postgres/data -l /var/lib/postgres/logfile start

# Criar usuário e banco
sudo -u postgres psql -c "CREATE USER ravena WITH PASSWORD '${DB_PASSWORD}';"
sudo -u postgres psql -c "CREATE DATABASE ravena OWNER ravena;"
sudo -u postgres psql -c "ALTER USER ravena WITH SUPERUSER;"

# Executar script de inicialização
sudo -u postgres psql -d ravena -f /root/init_database.sql

# Configurar para iniciar com o sistema
sudo systemctl enable postgresql

echo "[OK] Banco de dados configurado"
DBEOF

chmod +x "$DB_INIT_SCRIPT"

echo -e "${GREEN}[OK]${NC} Script de inicialização criado"

# Criar script de configuração do Redis
echo -e "${BLUE}[5/5]${NC} Criando script de configuração do Redis..."

REDIS_SCRIPT="$PROJECT_DIR/archiso/configs/ravena/airootfs/root/setup_redis.sh"

cat > "$REDIS_SCRIPT" << 'REDISEOF'
#!/bin/bash
# ============================================
# SETUP_REDIS.SH - Configurar Redis
# ============================================

set -e

# Configurar Redis
sed -i "s/# requirepass foobared/requirepass ${REDIS_PASSWORD}/" /etc/redis/redis.conf
sed -i "s/bind 127.0.0.1/bind 127.0.0.1/" /etc/redis/redis.conf

# Iniciar Redis
sudo systemctl enable redis

echo "[OK] Redis configurado"
REDISEOF

chmod +x "$REDIS_SCRIPT"

echo -e "${GREEN}[OK]${NC} Script do Redis criado"

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  SENHAS GERADAS COM SUCESSO${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Arquivo de senhas: $OUTPUT_FILE"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC}"
echo "1. Guarde este arquivo em local seguro"
echo "2. NÃO commit no Git"
echo "3. As senhas são:"
echo "   - PostgreSQL: $DB_PASSWORD"
echo "   - Redis: $REDIS_PASSWORD"
echo "   - JWT: $JWT_SECRET"
echo "   - Web: $WEB_SECRET"
echo "   - Grafana: $GRAFANA_ADMIN_PASSWORD"
echo ""
echo "============================================"
