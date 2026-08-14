#!/bin/bash
# RAVENA OOBE - primeira configuracao (estilo Windows/MEC)
# 1o boot sem internet -> tela de boas-vindas + painel de rede p/ conectar
# So roda enquanto nao houver marcador de conclusao persistido.
[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"

DONE_DATA="/mnt/ravena-data/ravena/config/oobe-done"
DONE_LOCAL="/etc/ravena/oobe-done"

for f in "$DONE_DATA" "$DONE_LOCAL"; do
    [ -f "$f" ] && exit 0
done

# ja tem internet? nao precisa de wizard
if ping -c1 -W3 1.1.1.1 >/dev/null 2>&1; then
    mkdir -p /etc/ravena
    touch "$DONE_LOCAL" 2>/dev/null || true
    [ -d /mnt/ravena-data/ravena/config ] && touch "$DONE_DATA" 2>/dev/null || true
    exit 0
fi

clear
echo -e "\033[1;36m"
echo "  =================================================="
echo "        BEM-VINDO AO RAVENA OS"
echo "        primeira configuracao (semelhante ao Windows)"
echo "  =================================================="
echo -e "\033[0m"
echo "  Nao detectamos conexao com a internet."
echo "  Vamos configurar sua rede agora."
echo
echo "  No painel a seguir (RAVENA REDE):"
echo "    opcao 1 = Conectar WIFI   (escolha a rede + senha)"
echo "    opcao 2 = Conectar CABO   (ethernet/LAN)"
echo "    opcao 3 = Config completo (nmtui - IP manual, etc)"
echo
echo "  DICA: use as SETAS do teclado p/ escolher, ENTER p/ confirmar."
echo
echo -e "\033[1;33m  Aperte ENTER para abrir as configs de rede...\033[0m"
read -r _

# abre o painel de rede interativo
/usr/local/bin/ravena-rede.sh 2>/dev/null

# teste apos o painel
echo
if ping -c1 -W3 1.1.1.1 >/dev/null 2>&1; then
    echo -e "\033[1;32m  INTERNET CONECTADA! Configuracao concluida. :) \033[0m"
    # sincroniza o perfil WiFi na RAVENA-DATA p/ nao somar no proximo boot
    /usr/local/bin/ravena-sync-rede.sh >/dev/null 2>&1 || true
else
    echo -e "\033[1;33m  Ainda sem internet. Rode 'rede' quando quiser tentar de novo.\033[0m"
    echo -e "\033[1;33m  (este assistente voltara no proximo boot enquanto nao conectar)\033[0m"
fi
sleep 2

# marcador: local (some no reboot) => so persiste quando a RAVENA-DATA existir
mkdir -p /etc/ravena
touch "$DONE_LOCAL" 2>/dev/null || true
if [ -d /mnt/ravena-data/ravena/config ]; then
    touch "$DONE_DATA" 2>/dev/null || true
fi
exit 0