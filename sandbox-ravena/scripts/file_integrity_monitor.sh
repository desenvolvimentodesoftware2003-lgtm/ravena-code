#!/bin/bash
# ============================================
# FILE INTEGRITY MONITORING (FIM)
# Ravena Security Sandbox
# ============================================
# Monitora alterações em arquivos críticos
# do sistema e alerta sobre modificações.
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

# Função de log
log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[!]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

# Configurações
RAVENA_DIR="/opt/ravena"
HASH_DIR="$RAVENA_DIR/data/integrity"
LOG_FILE="$RAVENA_DIR/logs/integrity.log"
ALERT_EMAIL=""  # Configurar se necessário

# Criar diretório de hashes
mkdir -p "$HASH_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Arquivos críticos para monitorar
CRITICAL_FILES=(
    "$RAVENA_DIR/app/app.py"
    "$RAVENA_DIR/app/requirements.txt"
    "$RAVENA_DIR/nginx/nginx.conf"
    "$RAVENA_DIR/docker-compose.yml"
    "$RAVENA_DIR/init-scripts/01-init.sql"
    "$RAVENA_DIR/scripts/backup_postgres.sh"
    "$RAVENA_DIR/scripts/ravena"
)

# Diretórios críticos para monitorar
CRITICAL_DIRS=(
    "$RAVENA_DIR/app"
    "$RAVENA_DIR/nginx"
    "$RAVENA_DIR/scripts"
    "$RAVENA_DIR/init-scripts"
)

# Função para calcular hash de arquivo
calculate_hash() {
    local file="$1"
    if [ -f "$file" ]; then
        sha256sum "$file" | awk '{print $1}'
    else
        echo "FILE_NOT_FOUND"
    fi
}

# Função para calcular hash de diretório
calculate_dir_hash() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -type f -exec sha256sum {} \; | sort | sha256sum | awk '{print $1}'
    else
        echo "DIR_NOT_FOUND"
    fi
}

# Função para registrar log
log_event() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# ============================================
# COMANDO: init - Criar baseline inicial
# ============================================

cmd_init() {
    log "Criando baseline de integridade..."
    
    # Limpar hashes antigos
    rm -rf "$HASH_DIR"/*
    
    # Calcular hashes dos arquivos críticos
    info "Calculando hashes dos arquivos críticos..."
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            hash=$(calculate_hash "$file")
            echo "$hash" > "$HASH_DIR/$(echo "$file" | md5sum | awk '{print $1}').hash"
            log "  $file"
        fi
    done
    
    # Calcular hashes dos diretórios críticos
    info "Calculando hashes dos diretórios críticos..."
    for dir in "${CRITICAL_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            hash=$(calculate_dir_hash "$dir")
            echo "$hash" > "$HASH_DIR/$(echo "$dir" | md5sum | awk '{print $1}').dirhash"
            log "  $dir"
        fi
    done
    
    # Salvar timestamp do baseline
    date '+%Y-%m-%d %H:%M:%S' > "$HASH_DIR/baseline.timestamp"
    
    log_event "INFO" "Baseline de integridade criado"
    log "Baseline criado com sucesso!"
    echo ""
    echo "Arquivos monitorados: ${#CRITICAL_FILES[@]}"
    echo "Diretórios monitorados: ${#CRITICAL_DIRS[@]}"
    echo "Local: $HASH_DIR"
}

# ============================================
# COMANDO: check - Verificar integridade
# ============================================

cmd_check() {
    if [ ! -f "$HASH_DIR/baseline.timestamp" ]; then
        error "Baseline não encontrado! Execute: ravena fim init"
        exit 1
    fi
    
    log "Verificando integridade dos arquivos..."
    echo ""
    
    local violations=0
    local checked=0
    
    # Verificar arquivos críticos
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            current_hash=$(calculate_hash "$file")
            hash_file="$HASH_DIR/$(echo "$file" | md5sum | awk '{print $1}').hash"
            
            if [ -f "$hash_file" ]; then
                stored_hash=$(cat "$hash_file")
                
                if [ "$current_hash" != "$stored_hash" ]; then
                    error "ALTERAÇÃO DETECTADA: $file"
                    echo "    Hash armazenado: $stored_hash"
                    echo "    Hash atual:      $current_hash"
                    log_event "CRITICAL" "Arquivo alterado: $file"
                    violations=$((violations + 1))
                else
                    log "  OK: $file"
                fi
            else
                warn "  NOVO: $file (não está no baseline)"
                log_event "WARNING" "Arquivo novo: $file"
            fi
            checked=$((checked + 1))
        fi
    done
    
    # Verificar diretórios críticos
    for dir in "${CRITICAL_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            current_hash=$(calculate_dir_hash "$dir")
            hash_file="$HASH_DIR/$(echo "$dir" | md5sum | awk '{print $1}').dirhash"
            
            if [ -f "$hash_file" ]; then
                stored_hash=$(cat "$hash_file")
                
                if [ "$current_hash" != "$stored_hash" ]; then
                    error "ALTERAÇÃO DETECTADA no diretório: $dir"
                    log_event "CRITICAL" "Diretório alterado: $dir"
                    violations=$((violations + 1))
                else
                    log "  OK: $dir"
                fi
            fi
        fi
    done
    
    echo ""
    if [ $violations -eq 0 ]; then
        log "Integridade verificada: $checked arquivos OK"
        log_event "INFO" "Verificação de integridade: $checked arquivos OK"
    else
        error "VIOLAÇÕES DETECTADAS: $violations alterações"
        log_event "CRITICAL" "Verificação de integridade: $violations violações"
        exit 1
    fi
}

# ============================================
# COMANDO: update - Atualizar baseline
# ============================================

cmd_update() {
    log "Atualizando baseline de integridade..."
    cmd_init
    log "Baseline atualizado!"
}

# ============================================
# COMANDO: status - Mostrar status
# ============================================

cmd_status() {
    if [ ! -f "$HASH_DIR/baseline.timestamp" ]; then
        error "Baseline não encontrado!"
        exit 1
    fi
    
    log "Status do File Integrity Monitoring:"
    echo ""
    echo "  Baseline criado em: $(cat "$HASH_DIR/baseline.timestamp")"
    echo "  Arquivos monitorados: ${#CRITICAL_FILES[@]}"
    echo "  Diretórios monitorados: ${#CRITICAL_DIRS[@]}"
    echo "  Última verificação: $(tail -1 "$LOG_FILE" 2>/dev/null | cut -d']' -f1 | tr -d '[' || echo "Nunca")"
    echo ""
    echo "Logs: $LOG_FILE"
}

# ============================================
# COMANDO: logs - Mostrar logs
# ============================================

cmd_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        warn "Nenhum log encontrado"
        exit 0
    fi
    
    log "Logs de integridade:"
    echo ""
    tail -20 "$LOG_FILE"
}

# ============================================
# Parser de argumentos
# ============================================

case "${1:-help}" in
    init)
        cmd_init
        ;;
    check)
        cmd_check
        ;;
    update)
        cmd_update
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    help|--help|-h)
        echo "Uso: $0 <comando>"
        echo ""
        echo "Comandos:"
        echo "  init    Criar baseline inicial"
        echo "  check   Verificar integridade"
        echo "  update  Atualizar baseline"
        echo "  status  Mostrar status"
        echo "  logs    Mostrar logs"
        ;;
    *)
        error "Comando inválido: $1"
        echo "Use '$0 help' para ver os comandos disponíveis"
        exit 1
        ;;
esac
