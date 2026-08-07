#!/bin/bash
# ============================================
# BACKUP AUTOMÁTICO - POSTGRESQL
# Ravena Security Sandbox
# ============================================
# Este script cria backups automáticos do banco
# de dados PostgreSQL com rotação.
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

# Configurações
BACKUP_DIR="/opt/ravena/backups/postgres"
DB_HOST="ravena-db"
DB_PORT="5432"
DB_NAME="ravena_sandbox"
DB_USER="ravena_test"
DB_PASS="sandbox_password_123"
RETENTION_DAYS=7  # Manter backups por 7 dias
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ravena_backup_$TIMESTAMP.sql.gz"

# Função de log
log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1"; }

# Criar diretório de backups
mkdir -p "$BACKUP_DIR"

log "Iniciando backup do PostgreSQL..."
echo "  Database: $DB_NAME"
echo "  Host: $DB_HOST:$DB_PORT"
echo "  Arquivo: $BACKUP_FILE"
echo ""

# Verificar se o container está rodando
if ! docker ps | grep -q "$DB_HOST"; then
    error "Container $DB_HOST não está rodando!"
    exit 1
fi

# Executar backup
log "Executando pg_dump..."
docker exec -e PGPASSWORD="$DB_PASS" "$DB_HOST" \
    pg_dump -h localhost -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=custom --compress=9 > "$BACKUP_FILE" 2>/dev/null

# Verificar se o backup foi criado
if [ ! -f "$BACKUP_FILE" ]; then
    error "Falha ao criar backup!"
    exit 1
fi

# Obter tamanho do backup
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup criado com sucesso!"
echo "  Tamanho: $BACKUP_SIZE"
echo "  Arquivo: $BACKUP_FILE"

# Rotação - remover backups antigos
log "Removendo backups antigos (>${RETENTION_DAYS} dias)..."
find "$BACKUP_DIR" -name "ravena_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

# Listar backups existentes
echo ""
log "Backups disponíveis:"
ls -lh "$BACKUP_DIR"/ravena_backup_*.sql.gz 2>/dev/null | tail -5

echo ""
log "Backup concluído!"
echo ""
echo "Para restaurar:"
echo "  docker exec -i $DB_HOST pg_restore -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME < $BACKUP_FILE"
