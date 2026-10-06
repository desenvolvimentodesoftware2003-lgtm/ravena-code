#!/bin/bash
# RAVENA OS - inicializacao do X (eDEX-UI)
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/bin

# Fuso local - o init do archiso pode remover /etc/localtime no boot
sudo ln -sf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime 2>/dev/null || true

# eDEX-UI (leaunty)
# mkarchiso reseta permissoes do airootfs para 644 - garantir execucao
sudo chmod +x /opt/edex-ui/node_modules/electron/dist/electron /opt/edex-ui/node_modules/electron/cli.js /opt/edex-ui/node_modules/.bin/electron 2>/dev/null

echo;echo "+++++ RAVENA OS +++++";/usr/local/bin/horas;echo "+++++++++++++++++++++";echo

# Teclado ABNT2 (Ponto 4: "c" virava "~" sem esta config)
setxkbmap -model abnt2 -layout br 2>/dev/null || true

launch_edex() {
    cd /opt/edex-ui
    # setsid isola de tty/controlling-terminal: o xinit roda o .xinitrc sob
    # job control e uma arvore em background no vt recebe SIGTTOU/SIGTTIN
    # (estado T) ao tocar no console. stdio desacoplado evita a parada.
    setsid ./node_modules/.bin/electron . --no-sandbox --disable-gpu </dev/null >/tmp/edex.log 2>&1 &
    EDEX_PID=$!
}

if [ -x /opt/edex-ui/node_modules/.bin/electron ]; then
    launch_edex
    # garantia extra: retoma a arvore se por qualquer motivo tiver parado
    sleep 8
    pkill -CONT -f 'edex-ui/node_modules/electr' 2>/dev/null || true
    kill -CONT $EDEX_PID 2>/dev/null || true
    # self-heal: se o renderer nao subir apos ~25s (crash unico possivel),
    # relanca uma vez
    sleep 15
    if ! pgrep -f 'type=renderer' >/dev/null 2>&1; then
        launch_edex
        sleep 8
        pkill -CONT -f 'edex-ui/node_modules/electr' 2>/dev/null || true
        kill -CONT $EDEX_PID 2>/dev/null || true
    fi
    wait $EDEX_PID
fi

exec /bin/bash
