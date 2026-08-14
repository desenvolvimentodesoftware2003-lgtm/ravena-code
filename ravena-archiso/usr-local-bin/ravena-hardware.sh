#!/bin/bash
# RAVENA HARDWARE - painel de drivers e diagnosticos (equivalente ao
# Gerenciador de Dispositivos do Windows). Usa lspci/lsmod/sensors.
# USO: hardware  (menu completo)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;36m'; CYAN='\033[0;36m'; WHITE='\033[1;37m'; NC='\033[0m'

erat=0
check() {
    local nome="$1" cond="$2"
    if eval "$cond" 2>/dev/null; then
        echo -e "  ${GREEN}[OK]${NC} $nome"
    else
        echo -e "  ${RED}[FALTA]${NC} $nome"
        erat=1
    fi
}

sec_video() {
    echo -e "${WHITE}=== VIDEO (Intel iGPU) ===${NC}"
    check "driver i915 carregado" "lsmod | grep -q '^i915 '"
    check "modo grafico funcional" "ls /dev/dri/card0 >/dev/null 2>&1"
    echo
}

sec_wifi() {
    echo -e "${WHITE}=== WIFI (Intel Wireless) ===${NC}"
    check "driver iwlwifi carregado" "lsmod | grep -q '^iwlwifi '"
    check "radio desbloqueado (rfkill)" "[ -z \\\"\\\$(rfkill list wifi 2>/dev/null | grep -i blocked | grep -v 'no')\\\" ] || rfkill list wifi | grep -q 'Soft blocked: no'"
    check "interface de rede presente" "ls /sys/class/net/ | grep -qE 'wlan|wlp'"
    echo
}

sec_audio() {
    echo -e "${WHITE}=== AUDIO (Intel SOF/HD-Audio) ===${NC}"
    check "controlador de som no PCI" "lspci -d ::0403 2>/dev/null | grep -qi intel"
    check "modulos de audio carregados" "lsmod | grep -qE 'snd_hda_intel|snd_sof_pci'"
    check "placa de som reconhecida" "aplay -l 2>/dev/null | grep -q 'card 0'"
    echo
}

sec_armaz() {
    echo -e "${WHITE}=== ARMAZENAMENTO (NVMe/SSD) ===${NC}"
    check "NVMe detectado" "lsblk -d 2>/dev/null | grep -qi nvme"
    check "particao de dados montada" "mountpoint -q /mnt/ravena-data 2>/dev/null"
    echo -e "  Espaco livre: $(df -h / /mnt/ravena-data 2>/dev/null | awk 'NR>1{print "    "$6": "$4}')"
    echo
}

sec_termicas() {
    echo -e "${WHITE}=== TEMPERATURAS (sensores) ===${NC}"
    if command -v sensors >/dev/null 2>&1 && sensors 2>/dev/null | grep -qE '°|C'; then
        sensors 2>/dev/null | grep -E 'Core|Package|temp1|fan' | sed 's/^/  /' | head -8
    else
        echo -e "  ${YELLOW}[aviso]${NC} lm_sensors nao instalado - run: sudo pacman -S lm_sensors"
    fi
    echo
}

sec_bateria() {
    echo -e "${WHITE}=== BATERIA (portatil) ===${NC}"
    if [ -d /sys/class/power_supply/BAT0 ]; then
        cap=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null)
        st=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)
        echo -e "  Carga: ${GREEN}${cap}%${NC}  ($st)"
    else
        echo -e "  ${YELLOW}[aviso]${NC} sem bateria detectada (desktop?)"
    fi
    echo
}

sec_ia() {
    echo -e "${WHITE}=== IA LOCAL (llama.cpp) ===${NC}"
    if systemctl is-active ravena-llm.service >/dev/null 2>&1; then
        echo -e "  ${GREEN}[OK]${NC} servico ravena-llm ativo"
        curl -s http://localhost:8080/health 2>/dev/null | head -c 120; echo
    else
        echo -e "  ${YELLOW}[aviso]${NC} ravena-llm inativo (roda sob demanda via 'llm')"
    fi
    echo
}

main() {
    clear
    echo -e "${WHITE}======================================"
    echo -e "   RAVENA HARDWARE - diagnostico${NC}"
    echo -e "${WHITE}======================================${NC}"
    echo -e "  Modelo: $(cat /sys/class/dmi/id/product_name 2>/dev/null)"
    echo -e "  CPU:    $(lscpu 2>/dev/null | grep 'Model name' | cut -d: -f2 | xargs)"
    echo -e "  Kernel: $(uname -r)"
    echo -e "  Uptime: $(uptime -p 2>/dev/null | sed 's/up //')"
    echo
    sec_video
    sec_wifi
    sec_audio
    sec_armaz
    sec_termicas
    sec_bateria
    sec_ia
    if [ "$erat" = "1" ]; then
        echo -e "  ${RED}Algum item FALTA do sistema.${NC}"
        echo -e "  Rode ${CYAN}dmesg | grep -iE 'error|fail'${NC} ou peca suporte."
    else
        echo -e "  ${GREEN}Registro completo, nada faltando.${NC}"
    fi
    echo
    read -r -p "Enter p/ sair" _
}

[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"
main