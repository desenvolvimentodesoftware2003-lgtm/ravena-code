#!/bin/bash
# ============================================================
# RAVENA KILL-SWITCH (nftables) - v3
# Aceita qualquer tunel: wg0 (VPN propria) ou CloudflareWARP
# Seguranca: sem tunel ativo, TODO o trafego e bloqueado -
# o IP publico real NUNCA e exposto para a internet.
#
# Uso:
#   ravena-killswitch.sh up [interface]
#   ravena-killswitch.sh down
#
# Ex: ravena-killswitch.sh up CloudflareWARP
# Chamado automaticamente pelo wg-quick (PostUp/PostDown)
# ============================================================

TUN_IF="${2:-wg0}"

case "$1" in
    up)
        nft delete table inet ravena 2>/dev/null
        nft -f - <<EOF
table inet ravena {
    chain block_non_vpn {
        type filter hook output priority -200; policy drop;
        iifname "lo" accept
        oifname "$TUN_IF" accept
        ct state established,related accept
        udp dport 2408 accept
        udp dport 51820 accept
    }
    chain input {
        type filter hook input priority -200; policy drop;
        iifname "lo" accept
        ct state established,related accept
        iifname "$TUN_IF" accept
    }
    chain forward {
        type filter hook forward priority -200; policy drop;
        iifname "$TUN_IF" accept
    }
}
EOF
        echo "KILL-SWITCH ATIVO (tunel: $TUN_IF): trafego fora do tunel bloqueado"
        ;;
    down)
        nft delete table inet ravena 2>/dev/null
        echo "KILL-SWITCH REMOVIDO"
        ;;
    *)
        echo "uso: $0 up|down [interface]"
        exit 1
        ;;
esac