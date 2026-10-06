# RAVENA OS - .bashrc (ravena)
PS1='[\033[0;36mravena\033[0m@\h \W]\$ '

alias ll='ls -la'
alias edex='cd /opt/edex-ui && ./node_modules/.bin/electron . --no-sandbox'

# RAVENA - extras
alias horas='horas'
alias net='nmcli device status; nmcli connection show --active'
alias wifi='nmcli device wifi list'
alias conectar-wifi='nmcli device wifi connect'
alias rede-diag='sudo /usr/local/bin/ravena-rede-diag.sh'
alias navega='w3m'
alias navegador='links'
alias youtube='yt-dlp'
alias video='mpv'
alias arquivos='ranger'
export EDITOR=nano

# RAVENA - tmux automatico (scrollback 50k)
if [[ $- != *i* ]]; then return; fi
if command -v tmux >/dev/null 2>&1 && [[ -z "$TMUX" ]] && [[ "$TERM" != "dumb" ]]; then
    tmux attach >/dev/null 2>&1 || tmux new -As ravena
fi

# RAVENA LLM
alias llm="/usr/local/bin/llm"
alias specs="/usr/local/bin/llm specs"
alias modelos="llm lista"

# RAVENA INTEL - WarWatch (geopolitica p/ mercado)
alias intel="/usr/local/bin/intel"
alias intel-top="intel top"
alias intel-mercado="intel mercado"
alias intel-ao-vivo="intel ao vivo"
alias guerra="intel"

# RAVENA - REDE (painel estilo icone do Windows)
alias rede="sudo /usr/local/bin/ravena-rede.sh"
alias oobe="sudo /usr/local/bin/ravena-oobe.sh"
alias rede-sync="sudo /usr/local/bin/ravena-sync-rede.sh"
alias hardware="sudo /usr/local/bin/ravena-hardware.sh"
alias instalar="sudo /usr/local/bin/ravena-instalar.sh"
alias wifi="nmcli device wifi list"
alias conectar-wifi="nmcli device wifi connect"
alias cabo="nmcli device connect"
alias status-rede="nmcli -t device status"
alias status-ativo="nmcli -t connection show --active"

# RAVENA - USB (pendrive plug-and-play)
alias usb="/usr/local/bin/ravena-usb.sh listar"
alias usb-montar="sudo /usr/local/bin/ravena-usb.sh montar"
alias usb-ejetar="sudo /usr/local/bin/ravena-usb.sh desmontar"
alias pendrives="ls /mnt/usb"
# RAVENA - SAUDE DOS SERVICOS
alias saude="/usr/local/bin/ravena-health.sh status"
alias alertas="cat /tmp/ravena-health.alert 2>/dev/null || echo 'sem alertas'"

# RAVENA - BACKUP E SESSAO
alias backup="sudo /usr/local/bin/ravena-backup.sh"
alias salvar-sessao="/usr/local/bin/ravena-salvar-sessao"
alias restaurar-sessao="/usr/local/bin/ravena-restaurar-sessao"
# RAVENA RV9b - acoes do sistema
alias reiniciar='sudo systemctl reboot'
alias desligar='sudo systemctl poweroff'
alias cancelar-reinicio='sudo systemctl cancel-reboot'
alias intel-24h="/usr/local/bin/intel 24h"
