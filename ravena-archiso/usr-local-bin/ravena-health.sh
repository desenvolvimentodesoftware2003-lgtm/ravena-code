#!/bin/bash
# RAVENA HEALTH - daemon de saude dos servicos criticos
# Roda em loop (180s). Se um servico ficar fora >30s consecutivos,
# grava alerta em /tmp/ravena-health.alert + log no journald + beep visual.
# Servicos monitorados: ravena-llm (IA :8080), ravena-net (internet),
# ravena-ntp (hora sincronizada), ravena-data (particao), disco, VPN.

STATE_FILE="/tmp/ravena-health.state"
ALERT_FILE="/tmp/ravena-health.alert"
LOG_TAG="ravena-health"
CHECK_INTERVAL=10   # checa a cada 10s
FAIL_THRESHOLD=3    # 30s consecutivos de falha = alerta

log() { timeout 2 logger -t "$LOG_TAG" "$1" 2>/dev/null; echo "$(date '+%F %T') $1" >> /var/log/ravena-health.log 2>/dev/null; }

beep() {
    # aviso visual no terminal do eDEX-UI (tty1) +/ ou console
    for tty in /dev/tty1 /dev/console; do
        [ -w "$tty" ] && printf '\a' > "$tty" 2>/dev/null
        [ -w "$tty" ] && echo -e "\n\033[1;31m[RAVENA HEALTH]\033[0m $1" > "$tty" 2>/dev/null
    done
}

declare -A fails    # nome -> n de rodadas consecutivas falhando
declare -A alertado # nome -> 1 se ja alertou (nao repetir a cada 10s)

check_llm() {
    # IA: porta 8080 responde? (nao falha se o modelo ainda esta carregando > 60s)
    if timeout 5 bash -c 'exec 3<>/dev/tcp/127.0.0.1/8080' 2>/dev/null; then
        echo "OK"
    else
        # modelo pode estar carregando nos primeiros 15min - nao eh falha ainda
        if [ -n "$(systemctl is-active ravena-llm 2>/dev/null | grep -E '^(active|activating)')" ]; then
            echo "LOADING"
        else
            echo "DOWN"
        fi
    fi
}

check_net() {
    timeout 5 curl -s -o /dev/null -w '%{http_code}' --connect-timeout 4 https://1.1.1.1 2>/dev/null | grep -q 200 && echo "OK" || echo "DOWN"
}

check_ntp() {
    # synced se chronyd ativo E nao em "*" unsynced
    chronyc tracking 2>/dev/null | grep -q '^Leap status\s*:.*OK' && echo "OK" || echo "DOWN"
}

check_data() {
    mountpoint -q /mnt/ravena-data 2>/dev/null && echo "OK" || echo "DOWN"
}

check_disco() {
    # mais de 90% em / = alerta
    pct=$(df -P / | awk 'NR==2{print $5}' | tr -d '%')
    [ "$pct" -lt 90 ] && echo "OK" || echo "CHEIO($pct%)"
}

check_vpn() {
    # qualquer tunnel ativo? (wg0/wg1, tun, nft rules)
    (ip link show 2>/dev/null | grep -qE 'wg[0-9]+|tun[0-9]+') && echo "OK" || echo "SEM_VPN"
}

# ===== LOOP PRINCIPAL =====
log "ravena-health iniciado (intervalo ${CHECK_INTERVAL}s, limiar ${FAIL_THRESHOLD}x)"
echo "OK" > "$STATE_FILE"

while true; do
    alert_now=""

    # --- IA :8080 ---
    st=$(check_llm)
    case "$st" in
        "OK")      fails[llm]=0; alertado[llm]="";;
        "LOADING") fails[llm]=0;;   # carregando nao conta como falha
        "DOWN")    fails[llm]=$(( ${fails[llm]:-0} + 1 ))
                   if [ ${fails[llm]} -ge $FAIL_THRESHOLD ] && [ -z "${alertado[llm]}" ]; then
                       alert_now="$alert_now IA (8080) fora ha $(( FAIL_THRESHOLD * CHECK_INTERVAL ))s"
                       alertado[llm]=1
                   fi;;
    esac

    # --- Internet ---
    st=$(check_net)
    if [ "$st" = "OK" ]; then fails[net]=0; alertado[net]="";
    else
        fails[net]=$(( ${fails[net]:-0} + 1 ))
        if [ ${fails[net]} -ge $FAIL_THRESHOLD ] && [ -z "${alertado[net]}" ]; then
            alert_now="$alert_now SEM INTERNET ha $(( FAIL_THRESHOLD * CHECK_INTERVAL ))s"
            alertado[net]=1
        fi
    fi

    # --- NTP ---
    st=$(check_ntp)
    if [ "$st" = "OK" ]; then fails[ntp]=0; alertado[ntp]="";
    else
        fails[ntp]=$(( ${fails[ntp]:-0} + 1 ))
        if [ ${fails[ntp]} -ge $FAIL_THRESHOLD ] && [ -z "${alertado[ntp]}" ]; then
            alert_now="$alert_now RELOGIO sem sincronizar ha $(( FAIL_THRESHOLD * CHECK_INTERVAL ))s"
            alertado[ntp]=1
        fi
    fi

    # --- Particao dados ---
    st=$(check_data)
    if [ "$st" = "OK" ]; then fails[data]=0; alertado[data]="";
    else
        fails[data]=$(( ${fails[data]:-0} + 1 ))
        if [ ${fails[data]} -ge $FAIL_THRESHOLD ] && [ -z "${alertado[data]}" ]; then
            alert_now="$alert_now PARTICAO DE DADOS desmontada"
            alertado[data]=1
        fi
    fi

    # --- Disco ---
    st=$(check_disco)
    if [ "$st" = "OK" ]; then fails[disco]=0; alertado[disco]="";
    else
        fails[disco]=$(( ${fails[disco]:-0} + 1 ))
        if [ ${fails[disco]} -ge $FAIL_THRESHOLD ] && [ -z "${alertado[disco]}" ]; then
            alert_now="$alert_now DISCO $st (??%%)"
            alertado[disco]=1
        fi
    fi

    # --- VPN (aviso informativo, so 1x por mudanca) ---
    st=$(check_vpn)
    vpn_state="ON"
    [ "$st" = "OK" ] || vpn_state="OFF"
    prev_vpn=$(cat "$STATE_FILE" 2>/dev/null)
    if [ "$prev_vpn" != "$vpn_state" ]; then
        echo "$vpn_state" > "$STATE_FILE"
        log "VPN $vpn_state (informativo)"
    fi

    # --- grava alerta se houver; mantem ENQUANTO houver servico em falha ---
    if [ -n "$alert_now" ]; then
        echo "$alert_now" > "$ALERT_FILE"
        log "ALERTA:$alert_now"
        logger -t "$LOG_TAG" -p daemon.err "ALERTA:$alert_now" 2>/dev/null
        beep "ALERTA:$alert_now"
    elif [ -f "$ALERT_FILE" ]; then
        # remove so quando NENHUM servico tem flag de alerta pendente
        any=0
        for k in "${alertado[@]}"; do [ "$k" = "1" ] && any=1; done
        [ "$any" = "0" ] && rm -f "$ALERT_FILE"
    fi

    sleep "$CHECK_INTERVAL"
done