#!/bin/bash
# RAVENA REDE-DIAG - diagnostico de rede p/ achar a causa quando
# o WiFi/ethernet nao aparece. Mostra hardware, driver, firmware,
# bloqueio (rfkill) e o estado do NetworkManager.
# Uso:  rede-diag

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;36m'; CYAN='\033[0;36m'; WHITE='\033[1;37m'; NC='\033[0m'

[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"

hr() { echo -e "${BLUE}--------------------------------------------------${NC}"; }

echo -e "${WHITE}=== RAVENA REDE-DIAG ===${NC}"
echo

hr
echo -e "${WHITE}[1] HARDWARE (placa de rede no PCI/USB)${NC}"
if command -v lspci >/dev/null 2>&1; then
    lspci -nnk 2>/dev/null | grep -iA3 -E "network|ethernet|wireless" | sed 's/^/  /'
else
    echo "  lspci indisponivel (pacote pciutils nao instalado?)"
fi
echo

hr
echo -e "${WHITE}[2] DRIVER CARREGADO (iwlwifi/rtl/etc)${NC}"
if lsmod 2>/dev/null | grep -iE "iwlwifi|rtl|ath|r8169|e1000" ; then
    lsmod 2>/dev/null | grep -iE "iwlwifi|rtl|ath|r8169|e1000" | awk '{printf "  %-16s %8s\n",$1,$3}'
else
    echo -e "  ${RED}NENHUM driver de rede carregado!${NC}"
fi
echo

hr
echo -e "${WHITE}[3] FIRMWARE (erros de firmware no kernel)${NC}"
dmesg 2>/dev/null | grep -iE "iwlwifi|firmware|microcode" | tail -15 | sed 's/^/  /'
[ -z "$(dmesg 2>/dev/null | grep -iE 'iwlwifi')" ] && echo "  (sem mensagens iwlwifi no dmesg)"
echo

hr
echo -e "${WHITE}[4] BLOQUEIO RFKILL (WiFi/Bluetooth desligados)${NC}"
rfkill list 2>/dev/null | sed 's/^/  /' || echo "  rfkill indisponivel"
echo

hr
echo -e "${WHITE}[5] DISPOSITIVOS VISTOS PELO NETWORKMANAGER${NC}"
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status 2>/dev/null | awk -F: '{printf "  %-12s %-10s %-12s %s\n",$1,$2,$3,$4}' || echo "  NetworkManager sem resposta"
echo

hr
echo -e "${WHITE}[6] RADIO WIFI (enabled/disabled)${NC}"
echo -e "  WiFi: $(nmcli -t radio wifi 2>/dev/null)"
echo

hr
echo -e "${YELLOW}COMO LER:${NC}"
echo -e "  - [1] vazio + [2] sem driver => hardware desligado no BIOS ou placa ausente"
echo -e "  - [3] 'Direct firmware load failed' => pacote linux-firmware incompleto"
echo -e "  - [4] 'hard blocked: yes' => tecla Fn/aviao ou BIOS Wireless desabilitado"
echo -e "  - [1],[2] ok mas [5] vazio => NetworkManager travado: reiniciar com 'systemctl restart NetworkManager'"
echo

read -r -p "Enter p/ sair" _ 2>/dev/null || true