#!/bin/bash
# ============================================================================
# SISTEMA DE CHECKPOINT PARA FINE-TUNING DO RAVENA AIM
# Salva progresso automaticamente e antes de desligamento
# ============================================================================

set -euo pipefail

# --- CONFIGURACAO ---
PROJETO_DIR="${PROJETO_DIR:-$(cd "$(dirname "$0")" && pwd)}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-${PROJETO_DIR}/checkpoints}"
CHECKPOINT_INTERVAL="${CHECKPOINT_INTERVAL:-5400}"  # 90 minutos entre checkpoints automaticos
MAX_CHECKPOINTS="${MAX_CHECKPOINTS:-3}"              # manter apenas os N ultimos
TRAINING_SCRIPT="${TRAINING_SCRIPT:-python ${PROJETO_DIR}/scripts/finetune_ravena.py}"
LOG_FILE="${CHECKPOINT_DIR}/checkpoint.log"

# --- VARIAVEIS DE ESTADO ---
LAST_CHECKPOINT=""
START_TIME=$(date +%s)
CHECKPOINT_COUNT=0

# --- FUNCOES ---

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

mkdir -p "$CHECKPOINT_DIR"

# --- VARIAVEIS DE ESTADO ---
LAST_CHECKPOINT=""
START_TIME=$(date +%s)
CHECKPOINT_COUNT=0

# --- FUNCOES ---

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

mkdir -p "$CHECKPOINT_DIR"

# Salvar checkpoint completo
save_checkpoint() {
    local reason="${1:-auto}"
    local checkpoint_id="ckpt_$(date +%Y%m%d_%H%M%S)_$$"
    local ckpt_path="${CHECKPOINT_DIR}/${checkpoint_id}"
    
    mkdir -p "$ckpt_path"
    
    log "SALVANDO CHECKPOINT: $checkpoint_id (motivo: $reason)"
    
    # 1. Salvar estado do treinamento
    cat > "$ckpt_path/training_state.json" <<EOF
{
    "checkpoint_id": "$checkpoint_id",
    "timestamp": "$(date -Iseconds)",
    "epoch": ${EPOCH:-0},
    "batch": ${BATCH:-0},
    "global_step": ${GLOBAL_STEP:-0},
    "total_samples_processed": ${TOTAL_SAMPLES:-0},
    "processed_files": "${PROCESSED_FILES:-}",
    "last_loss": ${LAST_LOSS:-0},
    "best_loss": ${BEST_LOSS:-999999},
    "learning_rate": ${LEARNING_RATE:-0.001},
    "training_time_seconds": $(($(date +%s) - START_TIME)),
    "pid": $$,
    "hostname": "$(hostname)"
}
EOF

    # 2. Salvar lista de arquivos processados
    if [[ -f "${CHECKPOINT_DIR}/processed_files.txt" ]]; then
        cp "${CHECKPOINT_DIR}/processed_files.txt" "$ckpt_path/processed_files.txt"
    fi
    
    # 3. Salvar dados parciais (ex: metricas)
    if [[ -f "${CHECKPOINT_DIR}/metrics_history.csv" ]]; then
        cp "${CHECKPOINT_DIR}/metrics_history.csv" "$ckpt_path/metrics_history.csv"
    fi

    # 4. Sinalizar ao script de treinamento para salvar modelo
    # (o script de treinamento deve escutar este sinal)
    if [[ -n "${TRAINING_PID:-}" ]] && kill -0 "$TRAINING_PID" 2>/dev/null; then
        kill -USR1 "$TRAINING_PID" 2>/dev/null || true
        sleep 2  # aguardar salvar
    fi

    # 5. Salvar variaveis de ambiente criticas
    env | grep -E "^(EPOCH|BATCH|GLOBAL_STEP|TOTAL_SAMPLES|LAST_LOSS|BEST_LOSS|LEARNING_RATE)=" \
        > "$ckpt_path/env_vars.txt" 2>/dev/null || true

    # 6. Criar link para ultimo checkpoint
    ln -sfn "$ckpt_path" "${CHECKPOINT_DIR}/latest"
    
    LAST_CHECKPOINT="$ckpt_path"
    CHECKPOINT_COUNT=$((CHECKPOINT_COUNT + 1))
    
    log "CHECKPOINT SALVO: $ckpt_path"
    
    # Limpar checkpoints antigos
    cleanup_old_checkpoints
}

# Limpar checkpoints antigos (manter apenas MAX_CHECKPOINTS)
cleanup_old_checkpoints() {
    local count=$(ls -1d "${CHECKPOINT_DIR}"/ckpt_* 2>/dev/null | wc -l)
    
    if [[ $count -gt $MAX_CHECKPOINTS ]]; then
        local to_remove=$((count - MAX_CHECKPOINTS))
        ls -1d "${CHECKPOINT_DIR}"/ckpt_* | head -n "$to_remove" | while read dir; do
            log "REMOVENDO CHECKPOINT ANTIGO: $dir"
            rm -rf "$dir"
        done
    fi
}

# Trap para sinais de desligamento
emergency_save() {
    log "=== SINAL DE DESLIGAMENTO DETECTADO ==="
    log "Motivo: $1"
    save_checkpoint "emergency_$1"
    log "CHECKPOINT DE EMERGENCIA SALVO - processo pode ser encerrado com seguranca"
    exit 0
}

# Configurar traps para todos os sinais de desligamento
trap 'emergency_save SIGTERM' SIGTERM
trap 'emergency_save SIGINT' SIGINT
trap 'emergency_save SIGHUP' SIGHUP
trap 'emergency_save SIGQUIT' SIGQUIT

# Trap para checkpoint periodico (via SIGUSR1)
handle_checkpoint_signal() {
    log "Sinal SIGUSR1 recebido - salvando checkpoint manual"
    save_checkpoint "manual_signal"
}
trap 'handle_checkpoint_signal' USR1

# Verificar se existe checkpoint para restaurar
find_latest_checkpoint() {
    if [[ -L "${CHECKPOINT_DIR}/latest" ]]; then
        local latest=$(readlink -f "${CHECKPOINT_DIR}/latest")
        if [[ -d "$latest" ]] && [[ -f "$latest/training_state.json" ]]; then
            echo "$latest"
            return 0
        fi
    fi
    return 1
}

# Restaurar checkpoint
restore_checkpoint() {
    local ckpt_path="${1:-$(find_latest_checkpoint)}"
    
    if [[ -z "$ckpt_path" ]] || [[ ! -d "$ckpt_path" ]]; then
        log "NENHUM CHECKPOINT ENCONTRADO - iniciando do zero"
        return 1
    fi
    
    log "RESTAURANDO CHECKPOINT: $ckpt_path"
    
    # Ler estado
    if [[ -f "$ckpt_path/training_state.json" ]]; then
        # Extrair valores do JSON (sem jq, usando grep/sed)
        EPOCH=$(grep '"epoch"' "$ckpt_path/training_state.json" | sed 's/[^0-9]//g')
        BATCH=$(grep '"batch"' "$ckpt_path/training_state.json" | sed 's/[^0-9]//g')
        GLOBAL_STEP=$(grep '"global_step"' "$ckpt_path/training_state.json" | sed 's/[^0-9]//g')
        TOTAL_SAMPLES=$(grep '"total_samples_processed"' "$ckpt_path/training_state.json" | sed 's/[^0-9]//g')
        LAST_LOSS=$(grep '"last_loss"' "$ckpt_path/training_state.json" | sed 's/[^0-9.]//g')
        BEST_LOSS=$(grep '"best_loss"' "$ckpt_path/training_state.json" | sed 's/[^0-9.]//g')
        LEARNING_RATE=$(grep '"learning_rate"' "$ckpt_path/training_state.json" | sed 's/[^0-9.]//g')
        
        log "Estado restaurado: Epoch=$EPOCH Batch=$BATCH Step=$GLOBAL_STEP Loss=$LAST_LOSS"
    fi
    
    # Restaurar lista de arquivos processados
    if [[ -f "$ckpt_path/processed_files.txt" ]]; then
        cp "$ckpt_path/processed_files.txt" "${CHECKPOINT_DIR}/processed_files.txt"
        log "Lista de arquivos processados restaurada"
    fi
    
    # Restaurar metricas
    if [[ -f "$ckpt_path/metrics_history.csv" ]]; then
        cp "$ckpt_path/metrics_history.csv" "${CHECKPOINT_DIR}/metrics_history.csv"
        log "Historico de metricas restaurado"
    fi
    
    log "CHECKPOINT RESTAURADO COM SUCESSO"
    return 0
}

# Monitor de desligamento do sistema
watch_for_shutdown() {
    # Verificar se o sistema esta desligando
    if [[ -d "/run/systemd/shutdown" ]] || [[ -f "/var/run/shutdown.pid" ]]; then
        log "SISTEMA EM PROCESSO DE DESLIGAMENTO DETECTADO"
        save_checkpoint "system_shutdown_detected"
    fi
    
    # Verificar bateria (se laptop)
    if [[ -f "/sys/class/power_supply/BAT0/status" ]]; then
        local bat_status=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)
        local bat_level=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null)
        
        if [[ "$bat_status" == "Discharging" ]] && [[ "$bat_level" -lt 15 ]]; then
            log "BATERIA CRITICA ($bat_level%) - salvando checkpoint"
            save_checkpoint "low_battery"
        fi
    fi
}

# Loop de checkpoint automatico
checkpoint_loop() {
    while true; do
        sleep "$CHECKPOINT_INTERVAL"
        save_checkpoint "periodic"
        watch_for_shutdown
    done
}

# --- PONTO DE ENTRADA ---
echo "
============================================
  SISTEMA DE CHECKPOINT ATIVADO
  Diretorio: $CHECKPOINT_DIR
  Intervalo: ${CHECKPOINT_INTERVAL}s
  Max checkpoints: $MAX_CHECKPOINTS
  PID: $$
============================================
"

# Iniciar loop de checkpoint em background
checkpoint_loop &
CHECKPOINT_LOOP_PID=$!
log "Loop de checkpoint iniciado (PID: $CHECKPOINT_LOOP_PID)"

# Restaurar checkpoint se existir
restore_checkpoint || true

# Executar script de treinamento
log "Iniciando treinamento: $TRAINING_SCRIPT"
python "$TRAINING_SCRIPT" \
    --resume-from "${LAST_CHECKPOINT:-}" \
    --checkpoint-dir "$CHECKPOINT_DIR" &
    
TRAINING_PID=$!
log "Treinamento iniciado (PID: $TRAINING_PID)"

# Aguardar treinamento
wait $TRAINING_PID
TRAINING_EXIT=$?

# Parar loop de checkpoint
kill $CHECKPOINT_LOOP_PID 2>/dev/null || true

# Checkpoint final
save_checkpoint "training_complete"

log "Treinamento finalizado com codigo: $TRAINING_EXIT"
exit $TRAINING_EXIT
