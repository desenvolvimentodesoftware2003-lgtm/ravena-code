#!/bin/bash
# ============================================
# WEBHOOK ALERTS - Sistema de Alertas
# Ravena Security Sandbox
# ============================================
# Envia alertas via webhook para diferentes
# plataformas (Slack, Discord, Telegram, etc.)
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

# Configurações
RAVENA_DIR="/opt/ravena"
CONFIG_FILE="$RAVENA_DIR/config/webhooks.json"
LOG_FILE="$RAVENA_DIR/logs/webhooks.log"

# Criar diretórios
mkdir -p "$(dirname "$CONFIG_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# Configuração padrão
DEFAULT_CONFIG='{
    "webhooks": {
        "slack": {
            "enabled": false,
            "url": "",
            "channel": "#ravena-alerts"
        },
        "discord": {
            "enabled": false,
            "url": ""
        },
        "telegram": {
            "enabled": false,
            "bot_token": "",
            "chat_id": ""
        },
        "webhook": {
            "enabled": false,
            "url": "",
            "method": "POST",
            "headers": {}
        }
    },
    "alerts": {
        "critical": true,
        "high": true,
        "medium": false,
        "low": false
    }
}'

# Inicializar configuração se não existir
if [ ! -f "$CONFIG_FILE" ]; then
    echo "$DEFAULT_CONFIG" > "$CONFIG_FILE"
    warn "Configuração padrão criada: $CONFIG_FILE"
fi

# ============================================
# Funções de envio
# ============================================

send_slack() {
    local message="$1"
    local level="$2"
    local config=$(cat "$CONFIG_FILE" | jq -r '.webhooks.slack')
    
    if [ "$(echo "$config" | jq -r '.enabled')" != "true" ]; then
        return 1
    fi
    
    local url=$(echo "$config" | jq -r '.url')
    local channel=$(echo "$config" | jq -r '.channel')
    
    if [ -z "$url" ]; then
        return 1
    fi
    
    # Definir cor baseado no nível
    local color
    case "$level" in
        critical) color="#FF0000" ;;
        high) color="#FF6600" ;;
        medium) color="#FFCC00" ;;
        low) color="#00CC00" ;;
        *) color="#808080" ;;
    esac
    
    # Enviar para Slack
    curl -s -X POST "$url" \
        -H 'Content-type: application/json' \
        -d "{
            \"channel\": \"$channel\",
            \"attachments\": [{
                \"color\": \"$color\",
                \"title\": \"Ravena Security Alert\",
                \"text\": \"$message\",
                \"fields\": [{
                    \"title\": \"Nível\",
                    \"value\": \"$level\",
                    \"short\": true
                }, {
                    \"title\": \"Horário\",
                    \"value\": \"$(date '+%Y-%m-%d %H:%M:%S')\",
                    \"short\": true
                }]
            }]
        }" > /dev/null 2>&1
    
    return 0
}

send_discord() {
    local message="$1"
    local level="$2"
    local config=$(cat "$CONFIG_FILE" | jq -r '.webhooks.discord')
    
    if [ "$(echo "$config" | jq -r '.enabled')" != "true" ]; then
        return 1
    fi
    
    local url=$(echo "$config" | jq -r '.url')
    
    if [ -z "$url" ]; then
        return 1
    fi
    
    # Definir cor baseado no nível
    local color
    case "$level" in
        critical) color=16711680 ;;
        high) color=16744448 ;;
        medium) color=16776960 ;;
        low) color=65280 ;;
        *) color=8421504 ;;
    esac
    
    # Enviar para Discord
    curl -s -X POST "$url" \
        -H 'Content-type: application/json' \
        -d "{
            \"embeds\": [{
                \"title\": \"Ravena Security Alert\",
                \"description\": \"$message\",
                \"color\": $color,
                \"fields\": [{
                    \"name\": \"Nível\",
                    \"value\": \"$level\",
                    \"inline\": true
                }, {
                    \"name\": \"Horário\",
                    \"value\": \"$(date '+%Y-%m-%d %H:%M:%S')\",
                    \"inline\": true
                }]
            }]
        }" > /dev/null 2>&1
    
    return 0
}

send_telegram() {
    local message="$1"
    local level="$2"
    local config=$(cat "$CONFIG_FILE" | jq -r '.webhooks.telegram')
    
    if [ "$(echo "$config" | jq -r '.enabled')" != "true" ]; then
        return 1
    fi
    
    local bot_token=$(echo "$config" | jq -r '.bot_token')
    local chat_id=$(echo "$config" | jq -r '.chat_id')
    
    if [ -z "$bot_token" ] || [ -z "$chat_id" ]; then
        return 1
    fi
    
    # Formatar mensagem
    local formatted_message="🚨 *Ravena Security Alert*

*Nível:* $level
*Mensagem:* $message
*Horário:* $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Enviar para Telegram
    curl -s -X POST "https://api.telegram.org/bot$bot_token/sendMessage" \
        -d "chat_id=$chat_id" \
        -d "text=$formatted_message" \
        -d "parse_mode=Markdown" > /dev/null 2>&1
    
    return 0
}

send_webhook() {
    local message="$1"
    local level="$2"
    local config=$(cat "$CONFIG_FILE" | jq -r '.webhooks.webhook')
    
    if [ "$(echo "$config" | jq -r '.enabled')" != "true" ]; then
        return 1
    fi
    
    local url=$(echo "$config" | jq -r '.url')
    local method=$(echo "$config" | jq -r '.method')
    
    if [ -z "$url" ]; then
        return 1
    fi
    
    # Enviar para webhook personalizado
    curl -s -X "$method" "$url" \
        -H 'Content-type: application/json' \
        -d "{
            \"source\": \"ravena-sandbox\",
            \"level\": \"$level\",
            \"message\": \"$message\",
            \"timestamp\": \"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",
            \"data\": {
                \"hostname\": \"$(hostname)\",
                \"ip\": \"$(hostname -I | awk '{print $1}')\"
            }
        }" > /dev/null 2>&1
    
    return 0
}

# ============================================
# Função principal de alerta
# ============================================

send_alert() {
    local level="$1"
    local message="$2"
    
    # Verificar se o nível deve ser enviado
    local should_send=$(jq -r ".alerts.$level" "$CONFIG_FILE" 2>/dev/null)
    if [ "$should_send" != "true" ]; then
        return 0
    fi
    
    # Registrar no log
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $message" >> "$LOG_FILE"
    
    # Enviar para cada plataforma habilitada
    send_slack "$message" "$level" && log "Alerta enviado para Slack"
    send_discord "$message" "$level" && log "Alerta enviado para Discord"
    send_telegram "$message" "$level" && log "Alerta enviado para Telegram"
    send_webhook "$message" "$level" && log "Alerta enviado para Webhook"
}

# ============================================
# Comandos
# ============================================

cmd_send() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        error "Uso: $0 send <nível> <mensagem>"
        error "Níveis: critical, high, medium, low"
        exit 1
    fi
    
    local level="$1"
    local message="$2"
    
    # Validar nível
    case "$level" in
        critical|high|medium|low) ;;
        *)
            error "Nível inválido: $level"
            exit 1
            ;;
    esac
    
    send_alert "$level" "$message"
    log "Alerta enviado: [$level] $message"
}

cmd_config() {
    log "Configuração atual:"
    echo ""
    cat "$CONFIG_FILE" | jq .
}

cmd_test() {
    log "Testando envio de alertas..."
    send_alert "medium" "Teste de alerta do Ravena Sandbox"
    log "Teste concluído!"
}

cmd_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        warn "Nenhum log encontrado"
        exit 0
    fi
    
    log "Logs de alertas:"
    echo ""
    tail -20 "$LOG_FILE"
}

# ============================================
# Parser de argumentos
# ============================================

case "${1:-help}" in
    send)
        shift
        cmd_send "$@"
        ;;
    config)
        cmd_config
        ;;
    test)
        cmd_test
        ;;
    logs)
        cmd_logs
        ;;
    help|--help|-h)
        echo "Uso: $0 <comando>"
        echo ""
        echo "Comandos:"
        echo "  send <nível> <mensagem>  Enviar alerta"
        echo "  config                  Ver configuração"
        echo "  test                    Testar envio"
        echo "  logs                    Ver logs"
        echo ""
        echo "Níveis:"
        echo "  critical  Crítico (vermelho)"
        echo "  high      Alto (laranja)"
        echo "  medium    Médio (amarelo)"
        echo "  low       Baixo (verde)"
        ;;
    *)
        error "Comando inválido: $1"
        echo "Use '$0 help' para ver os comandos disponíveis"
        exit 1
        ;;
esac
