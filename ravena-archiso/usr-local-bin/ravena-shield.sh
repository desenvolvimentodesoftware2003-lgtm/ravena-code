#!/bin/bash
# ============================================================
# RAVENA SHIELD (NVML) - guardiao de memoria contra OOM
# Referencia: FASE0-TRIAGEM-REPOS-RAVENA.md (linha 39)
#   - check_ravena_shield_vram: NVML se GPU NVIDIA presente,
#     senao RAM+swap via /proc/meminfo (caso RV9 sem GPU)
#   - margem 10%: age quando uso >= 90%
#   - alvo: processo LLM (llama-server/llama-cli) p/ preservar
#     o trading de matar o OOM killer
#   - telemetria: /run/ravena-shield/state.json (widget bridge)
# ============================================================
set -uo pipefail

MARGIN_PCT=10
LIMIT_PCT=$((100 - MARGIN_PCT))
INTERVAL=5
STATE_DIR=/run/ravena-shield
STATE_FILE=$STATE_DIR/state.json
LOG=/var/log/ravena-shield.log
LLM_COMS="llama-server llama-cli llama-bench llama-mtmd llama-tts ravena-airllm ravena-llm"
LLM_EXE_RE='^(.*/)?(llama-server|llama-cli|llama-bench|llama-mtmd|llama-tts|ravena-airllm|ravena-llm)( |$)'

mkdir -p "$STATE_DIR"

log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }

total_bytes=0
used_bytes=0
mem_source=""

get_mem_usage() {
  # 1) NVIDIA GPU presente?
  if command -v nvidia-smi >/dev/null 2>&1; then
    local vmem_total vmem_used
    vmem_total=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
    vmem_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    if [ -n "$vmem_total" ] && [ -n "$vmem_used" ]; then
      total_bytes=$((vmem_total * 1024 * 1024))
      used_bytes=$((vmem_used * 1024 * 1024))
      mem_source="nvml"
      return 0
    fi
  fi

  # 2) fallback: RAM + swap (caso RV9, sem GPU)
  local mt mu st su
  mt=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
  mu=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  st=$(awk '/^SwapTotal:/{print $2}' /proc/meminfo)
  su=$(awk '/^SwapFree:/{print $2}' /proc/meminfo)
  [ -z "$mt" ] && mt=0
  [ -z "$mu" ] && mu=0
  [ -z "$st" ] && st=0
  [ -z "$su" ] && su=0
  total_bytes=$(( (mt + st) * 1024 ))
  used_bytes=$(( ((mt - mu) + (st - su)) * 1024 ))
  mem_source="ram_swap"
}

first_action_done=0

# evita pgrep -f (casa com qualquer linha contendo o nome, inclusive
# o proprio shell que invoca o script) - usa /proc/*/comm + cmdline
find_llm_pids() {
  local pid comm
  for d in /proc/[0-9]*; do
    pid=${d##*/}
    [ "$pid" = "$$" ] && continue
    comm=$(cat "$d/comm" 2>/dev/null) || continue
    case " $LLM_COMS " in
      *" $comm "*) echo "$pid"; continue ;;
    esac
    if tr '\0' ' ' < "$d/cmdline" 2>/dev/null | grep -qE "$LLM_EXE_RE"; then
      echo "$pid"
    fi
  done
}

act_on_llm() {
  local pids p
  pids=$(find_llm_pids)
  if [ -z "$pids" ]; then
    log "shield: sem processo LLM consumindo (nada a fazer)"
    return 0
  fi
  log "shield: CRITICO - matando LLM (pids: $pids) preservando trading"
  # SIGTERM gracioso primeiro
  for p in $pids; do
    kill -TERM "$p" 2>/dev/null || true
  done
  sleep 2
  # depois SIGKILL se ainda vivo
  for p in $pids; do
    kill -KILL "$p" 2>/dev/null || true
  done
  log "shield: LLM terminado (evitou OOM killer)"
}

write_state() {
  local pct status action
  pct=0
  [ "$total_bytes" -gt 0 ] && pct=$(( used_bytes * 100 / total_bytes ))
  status="$1"
  action="$2"
  cat > "$STATE_FILE" <<EOF
{"timestamp":"$(date -Iseconds)","status":"$status","source":"$mem_source","mem_used":$used_bytes,"mem_total":$total_bytes,"usage_pct":$pct,"margin_pct":$MARGIN_PCT,"action":"$action"}
EOF
}

run_once() {
  get_mem_usage
  local pct=0
  [ "$total_bytes" -gt 0 ] && pct=$(( used_bytes * 100 / total_bytes ))

  if [ "$pct" -ge "$LIMIT_PCT" ]; then
    write_state "critical" "kill-llm"
    log "shield: uso ${pct}% >= limite ${LIMIT_PCT}% (margem $MARGIN_PCT%)"
    act_on_llm
    return
  fi

  local warn=$(( LIMIT_PCT - 10 ))
  if [ "$pct" -ge "$warn" ]; then
    write_state "warning" "monitor"
    log "shield: uso ${pct}% (aviso, limiar $warn%)"
  else
    write_state "ok" "monitor"
  fi
}

run_loop() {
  while true; do
    run_once
    sleep "$INTERVAL"
  done
}

main() {
  case "${1:-}" in
    check)
      run_once
      cat "$STATE_FILE"
      ;;
    once)
      run_once
      ;;
    *)
      echo "RAVENA SHIELD (NVML) guardando ${mem_source} margem $MARGIN_PCT%"
      echo "uso: $0 check | once | (daemon sem args)"
      run_loop
      ;;
  esac
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
fi