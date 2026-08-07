#!/bin/bash
# ============================================
# CONFIGURAR BACKUP AUTOMÁTICO
# Ravena Security Sandbox
# ============================================
# Configura cron para backups automáticos
# do PostgreSQL.
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_postgres.sh"

# Verificar se o script de backup existe
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo -e "${RED}[!] Script de backup não encontrado: $BACKUP_SCRIPT${NC}"
    exit 1
fi

# Tornar executável
chmod +x "$BACKUP_SCRIPT"

# Criar cron job
# Executa todos os dias às 2:00 da manhã
CRON_JOB="0 2 * * * $BACKUP_SCRIPT >> /opt/ravena/logs/backup.log 2>&1"

# Verificar se o cron job já existe
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    warn "Cron job já existe!"
else
    # Adicionar ao crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    log "Cron job configurado com sucesso!"
fi

# Mostrar crontab atual
echo ""
log "Crontab atual:"
crontab -l 2>/dev/null || echo "  Nenhum cron job configurado"

echo ""
log "Configuração concluída!"
echo ""
echo "Backups automáticos:"
echo "  - Frequência: Todos os dias às 2:00"
echo "  - Retenção: 7 dias"
echo "  - Local: /opt/ravena/backups/postgres/"
echo "  - Log: /opt/ravena/logs/backup.log"
echo ""
echo "Para testar manualmente:"
echo "  $BACKUP_SCRIPT"
