# RAVENA OS - perfil de login (ravena)
# 1o boot: assistente OOBE (rede/config) antes da interface grafica.
# Boots seguintes: pula direto para o OS (eDEX-UI) quando ja configurado.


# Iniciar interface grafica (eDEX-UI) no TTY1 (testar SEM travar/caem no tmux)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    # OOBE: roda so sem marcador de conclusao e sem internet
    command -v ravena-oobe.sh >/dev/null 2>&1 && ravena-oobe.sh
    startx
    # se o X nao subir ou encerrar, cai no tmux (fallback terminal)
    [ -f ~/.bashrc ] && . ~/.bashrc
    exit 0
fi

# Demais sessoes (serial/pts/ssh): bashrc normal (inclui tmux automatico)
[ -f ~/.bashrc ] && . ~/.bashrc