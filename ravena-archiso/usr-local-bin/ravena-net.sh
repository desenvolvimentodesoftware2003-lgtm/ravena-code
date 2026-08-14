#!/bin/bash
# RAVENA - rede no boot: DHCP caboada + WiFi disponivel + mensagem clara
rfkill unblock all 2>/dev/null || true
sleep 1
systemctl start NetworkManager 2>/dev/null || true

# aguarda o NetworkManager estar pronto
for i in $(seq 1 20); do
  nmcli -t general status 2>/dev/null | grep -q running && break
  sleep 1
done

# ativa DHCP em qualquer interface caboada (eth*/en*/wired)
for dev in $(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1}'); do
  nmcli device connect "$dev" 2>/dev/null || true
done

# conecta a primeira rede WiFi salva (se houver)
CONN=$(nmcli -t -f NAME,DEVICE connection show 2>/dev/null | grep -v '^:' | head -1 | cut -d: -f1)
[ -n "$CONN" ] && nmcli connection up "$CONN" 2>/dev/null || true

# mostra estado final da rede
sleep 2
echo
echo "=== REDE ==="
nmcli device status 2>/dev/null | awk '{print "  "$0}'
echo "=== INTERNET ==="
if ping -c1 -W3 1.1.1.1 >/dev/null 2>&1; then echo "  CONECTADO (internet OK)"; else echo "  SEM INTERNET - rode: wifi (listar) / conectar-wifi (conectar)"; fi
