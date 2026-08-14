#!/bin/bash
# RAVENA REDE - painel de rede estilo "icone do Windows"
# Teclado: setas p/ navegar, Enter p/ escolher, Esc p/ sair
# Uso:  rede  (menu completo)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;36m'; CYAN='\033[0;36m'; WHITE='\033[1;37m'; NC='\033[0m'

[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"

net_status() {
    echo
    echo -e "${WHITE}=== ESTADO DA REDE ===${NC}"
    nmcli -t device status 2>/dev/null | awk -F: '{printf "  %-10s %-14s %-20s\n",$1,$2,$3}'
    echo
    conn=$(nmcli -t -f NAME,DEVICE,TYPE connection show --active 2>/dev/null | head -3)
    if [ -n "$conn" ]; then
        echo -e "${GREEN}Conectado em:${NC}"
        echo "$conn" | awk -F: '{printf "  %-25s (via %s, %s)\n",$1,$2,$3}'
    else
        echo -e "${RED}Nenhuma conexao ativa.${NC}"
    fi
    echo
    if ping -c1 -W3 1.1.1.1 > /dev/null 2>&1; then
        echo -e "  ${GREEN}INTERNET: OK${NC}"
    else
        echo -e "  ${YELLOW}INTERNET: sem resposta (verifique rede)${NC}"
    fi
    echo
}

menu_main() {
    while true; do
        clear
        net_status
        echo -e "${WHITE}==========================="
        echo -e "  RAVENA REDE${NC} (setas+Enter, Esc sai)"
        echo -e "${WHITE}===========================${NC}"
        echo "  1) Conectar WIFI (escolher rede)     <- SEM CABO LAN, e aqui"
        echo "  2) Conectar CABO (ethernet LAN)"
        echo "  3) Configuracao completa (nmtui)"
        echo "  4) Desconectar tudo"
        echo "  5) Informacoes de IP/DNS"
        echo "  0) Sair"
        echo -e "${WHITE}===========================${NC}"
        echo -e "${YELLOW}Dica: se o notebook esta sem cabo LAN, use a opcao 1 (WiFi).${NC}"
        echo -e "Atalhos no terminal: ${GREEN}wifi${NC} (listar) | ${GREEN}conectar-wifi <rede>${NC}"
        echo
        read -r -p "Escolha: " op
        case "$op" in
            1) menu_wifi ;;
            2) menu_cabo ;;
            3) nmtui ;;
            4) nmcli networking off; sleep 2; nmcli networking on; echo "Rede reiniciada."; sleep 1 ;;
            5) ip -br addr 2>/dev/null | grep -v '^lo' ; echo; nmcli -t -f IP4.ADDRESS,IP4.DNS,IP4.GATEWAY connection show --active 2>/dev/null; read -r -p "Enter p/ voltar" _ ;;
            0) clear; exit 0 ;;
        esac
    done
}

menu_wifi() {
    while true; do
        clear
        echo -e "${WHITE}=== WIFI DISPONIVEL ===${NC} (setas+Enter p/ conectar, Esc fecha)"
        echo
        nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY device wifi list 2>/dev/null | awk -F: '{
            mark=($1=="*")?"[*]":"[ ]";
            ssid=($2=="")?"(oculto)":$2;
            sec=($3~"WPA")?"senha":($3~"WEP")?"senha":"aberto";
            printf "  %-4s %-30s sinal:%-3s%% %s\n", mark, ssid, $4, sec
        }'
        echo
        read -r -p "Nome da rede (ou Enter p/ voltar): " ssid
        [ -z "$ssid" ] && return 0
        read -r -s -p "Senha (vazio = abrir): " pass; echo
        nmcli device wifi connect "$ssid" password "$pass" 2>&1 | sed 's/^/  /'
        echo
        read -r -p "Enter p/ voltar"
    done
}

menu_cabo() {
    clear
    echo -e "${WHITE}=== ETHERNET (CABO) ===${NC}"
    echo
    for dev in $(nmcli -t -f DEVICE,TYPE device status 2>/dev/null | awk -F: '$2=="ethernet"{print $1}'); do
        st=$(nmcli -t -f DEVICE,STATE device status 2>/dev/null | awk -F: -v d="$dev" '$1==d{print $2}')
        echo "  Interface: $dev  -  $st"
        nmcli device connect "$dev" 2>&1 | sed 's/^/    /'
    done
    echo
    echo "  Se a internet usa DHCP automatico, ja deve estar conectado acima."
    echo "  Para IP manual: opcao 3 (nmtui) > Editar conexao."
    echo
    read -r -p "Enter p/ voltar"
}

menu_main