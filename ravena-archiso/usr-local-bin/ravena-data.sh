#!/bin/bash
# RAVENA - monta particao de dados persistente RAVENA-DATA no boot
# USO: com LUKS2 (criptografia em repouso):
#   - Primeiro boot (particao sem filesystem): cria LUKS2 com chave em
#     /etc/ravena/data.key + passphrase de recuperacao mostrada na tela,
#     formata ext4 e monta.
#   - Boots seguintes: abre LUKS com a chave salva e monta.
# Sem chave (perdeu /etc/ravena): recupera com a passphrase de recuperacao
# impressa/guardada pelo usuario (cryptsetup open --type luks2).
set -e

LABEL="RAVENA-DATA"
MP="/mnt/ravena-data"
KEYFILE="/etc/ravena/data.key"
MAPPER="ravena-data"
# PENDDRIVE: chaves persistem na particao de boot (FAT/bootmnt) porque /etc
# num live ISO (archiso tmpfs) se perde no reboot. OPCAO 1 do usuario.
BOOTMNT="/run/archiso/bootmnt/ravena-keys"
KEYCOPY="$BOOTMNT/data.key"
RECCOPY="$BOOTMNT/recovery.key"

mkdir -p /etc/ravena

# ============================================================
# 0. RESTAURA AS CHAVES DO PENDRIVE (se o tmpfs as perdeu)
# ============================================================

# acha a particao EFI (FAT32) do pendrive - gravavel mesmo no modo DD
# (no modo DD o bootmnt e ISO9660 ro; as chaves vao para a particao EFI)
# IMPORTANTE: prefere discos REMOVIVEIS (USB). Nunca deve gravar chaves na
# ESP do Windows (disco interno) - regressao evitada por ordem de busca.
find_esp_partition() {
    local disk
    # passo 1: discos removiveis (pendrive) - prioridade maxima
    for disk in $(lsblk -n -d -o NAME -r 2>/dev/null); do
        case "$disk" in
            sd[a-z]|vd[a-z]|hd[a-z]|nvme[0-9]*n[0-9]) : ;;
            *) continue ;;
        esac
        # /sys/class/block/<disk>/removable == 1 => USB/pendrive
        if [ "$(cat /sys/class/block/$disk/removable 2>/dev/null)" != "1" ]; then
            continue
        fi
        for dev in $(lsblk -n -o NAME -r "/dev/$disk" 2>/dev/null); do
            case "$dev" in
                $disk[0-9]*)
                    local fst fsz fsz_bytes
                    fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                    [ "$fst" = "vfat" ] || [ "$fst" = "msdos" ] || continue
                    fsz=$(blkid -p -o value -s SIZE "/dev/$dev" 2>/dev/null)
                    if [ -n "$fsz" ]; then
                        fsz_bytes=$(numfmt --from=iec "$fsz" 2>/dev/null || echo 0)
                        if [ "${fsz_bytes:-0}" -le 1073741824 ] && [ "${fsz_bytes:-0}" -gt 0 ]; then
                            echo "/dev/$dev"; return 0
                        fi
                    else
                        echo "/dev/$dev"; return 0
                    fi
                    ;;
            esac
        done
    done
    # passo 1b: ESP marcada EXPLICITAMENTE (PARTLABEL ou LABEL = ESP) em qualquer
    # disco - e o que o ravena-instalar cria; na VM/QEMU os discos nao reportam
    # removable=1 (sysfs), entao este passo e necessario p/ persistir as chaves
    # mesmo sem disco removivel reportado. Windows usa LABEL=SYSTEM, nunca ESP.
    for dev in $(lsblk -n -o NAME -r 2>/dev/null); do
        case "$dev" in
            sd[a-z][0-9]*|vd[a-z][0-9]*|hd[a-z][0-9]*|nvme[0-9]*n[0-9]*p[0-9]*)
                fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                [ "$fst" = "vfat" ] || continue
                plab=$(blkid -p -o value -s PARTLABEL "/dev/$dev" 2>/dev/null)
                lab=$(blkid -p -o value -s LABEL "/dev/$dev" 2>/dev/null)
                if [ "$plab" = "ESP" ] || [ "$lab" = "ESP" ]; then
                    fsz=$(blkid -p -o value -s SIZE "/dev/$dev" 2>/dev/null)
                    if [ -n "$fsz" ]; then
                        fsz_bytes=$(numfmt --from=iec "$fsz" 2>/dev/null || echo 0)
                        if [ "${fsz_bytes:-0}" -gt 1073741824 ]; then
                            echo "RAVENA-DATA: ESP marcada porem grande demais ($dev) - ignorada" >&2
                            continue
                        fi
                    fi
                    echo "RAVENA-DATA: ESP marcada (PARTLABEL/LABEL=ESP) == /dev/$dev" >&2
                    echo "/dev/$dev"; return 0
                fi
                ;;
        esac
    done
    if [ -f /etc/ravena/instalado ]; then
        echo "RAVENA-DATA: modo instalado - procurando ESP vfat em qualquer disco" >&2
        for dev in $(lsblk -n -o NAME -r 2>/dev/null); do
            case "$dev" in
                sd[a-z][0-9]*|vd[a-z][0-9]*|hd[a-z][0-9]*|nvme[0-9]*n[0-9]*p[0-9]*)
                    fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                    if [ "$fst" = "vfat" ] || [ "$fst" = "msdos" ]; then
                        echo "RAVENA-DATA: ESP instalada == /dev/$dev" >&2
                        echo "/dev/$dev"; return 0
                    fi
                    ;;
            esac
        done
    fi
    # MODO INSTALADO: se o pacote ravena-instalar rodou, /etc/ravena/instalado
    # existe => aceita a ESP do proprio disco interno (nao so removiveis)
    if [ -f /etc/ravena/instalado ]; then
        echo "RAVENA-DATA: modo instalado - procurando ESP vfat em qualquer disco" >&2
        for dev in $(lsblk -n -o NAME -r 2>/dev/null); do
            case "$dev" in
                sd[a-z][0-9]*|vd[a-z][0-9]*|hd[a-z][0-9]*|nvme[0-9]*n[0-9]*p[0-9]*)
                    fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                    if [ "$fst" = "vfat" ] || [ "$fst" = "msdos" ]; then
                        echo "RAVENA-DATA: ESP instalada == /dev/$dev" >&2
                        echo "/dev/$dev"; return 0
                    fi
                    ;;
            esac
        done
    fi
    # passo 2: fallback seguro - apenas discos removiveis sem filtro de tamanho
    echo "RAVENA-DATA: aviso - procurando ESP vfat extra em discos removiveis" >&2
    for disk in $(lsblk -n -d -o NAME -r 2>/dev/null); do
        case "$disk" in
            sd[a-z]|vd[a-z]|hd[a-z]|nvme[0-9]*n[0-9]) : ;;
            *) continue ;;
        esac
        if [ "$(cat /sys/class/block/$disk/removable 2>/dev/null)" != "1" ]; then
            continue
        fi
        for dev in $(lsblk -n -o NAME -r "/dev/$disk" 2>/dev/null); do
            case "$dev" in
                $disk[0-9]*)
                    fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                    if [ "$fst" = "vfat" ] || [ "$fst" = "msdos" ]; then
                        echo "RAVENA-DATA: ESP removivel == /dev/$dev (sem filtro de tamanho)" >&2
                        echo "/dev/$dev"; return 0
                    fi
                    ;;
            esac
        done
    done
    # passo 3: NUNCA disco interno - sem ESP removivel, avisa e retorna falha
    echo "RAVENA-DATA: ERRO - nenhuma ESP em disco removivel; chaves NAO persistidas" >&2
    return 1
}

# monta a particao EFI e devolve o ponto de montagem em $1
mount_esp() {
    local part
    part=$(find_esp_partition) || return 1
    mkdir -p /mnt/ravena-esp
    if ! mountpoint -q /mnt/ravena-esp 2>/dev/null; then
        mount -o rw "$part" /mnt/ravena-esp 2>/dev/null || return 1
    fi
    echo "$part"
}

umount_esp() {
    umount /mnt/ravena-esp 2>/dev/null || true
}

restore_keys_from_pendrive() {
    local tries=0 found=0
    while [ $tries -lt 20 ]; do
        # aguarda o bootmnt (pendrive) aparecer
        if [ -d /run/archiso/bootmnt ]; then
            if [ -f "$KEYCOPY" ] && [ ! -f "$KEYFILE" ]; then
                cp "$KEYCOPY" "$KEYFILE" 2>/dev/null && chmod 400 "$KEYFILE" 2>/dev/null
                echo "RAVENA-DATA: chave restaurada do pendrive (data.key)"
                found=1
            fi
            if [ -f "$RECCOPY" ] && [ ! -f /etc/ravena/recovery.key ]; then
                cp "$RECCOPY" /etc/ravena/recovery.key 2>/dev/null && chmod 400 /etc/ravena/recovery.key 2>/dev/null
                echo "RAVENA-DATA: recovery.key restaurado do pendrive (bootmnt)"
            fi
            break
        fi
        sleep 1
        tries=$((tries+1))
    done
    # SEMPRE tenta tambem a particao EFI do pendrive (modo DD: bootmnt e ISO9660 ro,
    # e mesmo em modo normal as chaves podem estar la do 1o boot em DD).
    # O bootmnt pode existir (ISO ro) sem ter as chaves -> precisa do fallback.
    if mount_esp >/dev/null 2>&1; then
        if [ -f /mnt/ravena-esp/ravena-keys/data.key ] && [ ! -f "$KEYFILE" ]; then
            cp /mnt/ravena-esp/ravena-keys/data.key "$KEYFILE" 2>/dev/null && chmod 400 "$KEYFILE" 2>/dev/null
            echo "RAVENA-DATA: chave restaurada da particao EFI (data.key)"
            found=1
        fi
        if [ -f /mnt/ravena-esp/ravena-keys/recovery.key ] && [ ! -f /etc/ravena/recovery.key ]; then
            cp /mnt/ravena-esp/ravena-keys/recovery.key /etc/ravena/recovery.key 2>/dev/null && chmod 400 /etc/ravena/recovery.key 2>/dev/null
            echo "RAVENA-DATA: recovery.key restaurado da particao EFI"
        fi
        umount_esp
    fi
    if [ "$found" = "0" ]; then
        echo "RAVENA-DATA: nenhuma chave persistida encontrada (bootmnt/EFI) - segue sem"
    fi
    return 0
}

# ============================================================
# 4b. COPIA AS CHAVES PARA O PENDRIVE (persistencia OPCAO 1)
# ============================================================
persist_keys_to_pendrive() {
    # bootmnt do archiso normalmente RO; remonta RW p/ gravar as chaves
    if mountpoint -q /run/archiso/bootmnt 2>/dev/null; then
        mount -o remount,rw /run/archiso/bootmnt 2>/dev/null || true
        if mkdir -p "$BOOTMNT" 2>/dev/null; then
            umask 077
            cp "$KEYFILE" "$KEYCOPY" 2>/dev/null || true
            cp /etc/ravena/recovery.key "$RECCOPY" 2>/dev/null || true
            chmod 400 "$KEYCOPY" "$RECCOPY" 2>/dev/null || true
            umask 022
            # deixa o bootmnt RO de novo (estado original do archiso)
            mount -o remount,ro /run/archiso/bootmnt 2>/dev/null || true
            echo "RAVENA-DATA: chaves gravadas no pendrive (bootmnt/ravena-keys)"
            return 0
        fi
        # bootmnt nao gravavel (modo DD: ISO9660 ro) - deixa RO e cai p/ EFI
        mount -o remount,ro /run/archiso/bootmnt 2>/dev/null || true
    fi
    # fallback: particao EFI do pendrive (gravavel no modo DD)
    if mount_esp >/dev/null 2>&1; then
        mkdir -p /mnt/ravena-esp/ravena-keys 2>/dev/null || { umount_esp; echo "RAVENA-DATA: aviso - EFI nao gravavel, chaves NAO persistidas (ram)"; return 0; }
        umask 077
        cp "$KEYFILE" /mnt/ravena-esp/ravena-keys/data.key 2>/dev/null || true
        cp /etc/ravena/recovery.key /mnt/ravena-esp/ravena-keys/recovery.key 2>/dev/null || true
        chmod 400 /mnt/ravena-esp/ravena-keys/*.key 2>/dev/null || true
        umask 022
        umount_esp
        echo "RAVENA-DATA: chaves gravadas na particao EFI do pendrive (ravena-keys)"
        return 0
    fi
    echo "RAVENA-DATA: sem pendrive gravavel - chaves NAO persistidas (ram)"
    return 0
}

# ============================================================
# 1. PROCURA A PARTICAO (lsblk p/ nomes + blkid -p p/ tipo real)
# ============================================================
part_type() {
    if mountpoint -q "$MP" 2>/dev/null; then echo "mounted"; return; fi
    if [ -e "/dev/mapper/$MAPPER" ]; then echo "mapper"; return; fi

    local dev fst
    # passo 1: existe particao LUKS? (le tipo direto do superblock)
    for dev in $(lsblk -n -o NAME -r 2>/dev/null); do
        case "$dev" in
            sd[a-z][0-9]*|vd[a-z][0-9]*|hd[a-z][0-9]*|loop[0-9]*p[0-9]*|nvme[0-9]*n[0-9]*p[0-9]*)
                fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                if [ "$fst" = "crypto_LUKS" ]; then
                    echo "luks:/dev/$dev"; return
                fi
                ;;
        esac
    done

    # passo 2: nenhum LUKS -> particao SEM filesystem (primeiro boot)
    # IMPORTANTE: ignora particoes sem FS menores que 4GiB, p/ NUNCA formatar
    # a MSR/Reserved do Windows (128MB) nem outras reservadas.
    for dev in $(lsblk -n -o NAME -r 2>/dev/null); do
        case "$dev" in
            sd[a-z][0-9]*|vd[a-z][0-9]*|hd[a-z][0-9]*|loop[0-9]*p[0-9]*|nvme[0-9]*n[0-9]*p[0-9]*)
                fst=$(blkid -p -o value -s TYPE "/dev/$dev" 2>/dev/null)
                if [ -z "$fst" ]; then
                    # tamanho real em bytes (lsblk -b) - seguro contra MSR/swap vazia
                    sz=$(lsblk -n -b -o SIZE "/dev/$dev" 2>/dev/null | tr -d ' ')
                    if [ -n "$sz" ] && [ "$sz" -ge 4294967296 ]; then
                        echo "new:/dev/$dev"; return
                    fi
                    echo "RAVENA-DATA: ignorando particao sem FS pequena ($dev = $sz bytes)" >&2
                fi
                ;;
        esac
    done
    echo ""
}

# ============================================================
# 2. ABRE O LUKS COM A CHAVE (se existir)
# ============================================================
open_luks() {
    local part="$1"
    if [ -r "$KEYFILE" ]; then
        cryptsetup open --type luks2 --key-file "$KEYFILE" "$part" "$MAPPER" 2>/dev/null \
            && return 0
        if [ -r /etc/ravena/recovery.key ]; then
            cryptsetup open --type luks2 --key-file /etc/ravena/recovery.key "$part" "$MAPPER" 2>/dev/null \
                && return 0
        fi
    fi
    echo "RAVENA-DATA: ERRO - nao consegui abrir LUKS em $part sem interacao."
    echo "RAVENA-DATA: use a PASSPHRASE DE RECUPERACAO:"
    echo "RAVENA-DATA:   cryptsetup open --type luks2 $part $MAPPER"
    return 1
}

# ============================================================
# 3. PRIMEIRO BOOT: cria LUKS2 + ext4
# ============================================================
first_boot_luks() {
    local part="$1"
    echo "RAVENA-DATA: particao sem formato encontrada ($part)."
    echo "RAVENA-DATA: criando criptografia LUKS2 (AES-256-XTS + Argon2id)..."
    sleep 2

    # chave de dados (usada no boot, sem interacao)
    umask 077
    if [ ! -f "$KEYFILE" ]; then
        head -c 64 /dev/urandom > "$KEYFILE"
        chmod 400 "$KEYFILE"
    fi
    # passphrase de recuperacao (impressa/guardada pelo usuario)
    local rec
    rec=$(head -c 16 /dev/urandom | base64 | tr -d '=+/' | cut -c1-20)
    printf '%s' "$rec" > /etc/ravena/recovery.key
    chmod 400 /etc/ravena/recovery.key
    umask 022

    # slot 0 = chave de dados; slot 1 = passphrase de recuperacao
    cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 --key-size 512 \
        --pbkdf argon2id --hash sha512 --iter-time 2000 \
        --key-file "$KEYFILE" --batch-mode "$part"
    cryptsetup luksAddKey --key-file "$KEYFILE" \
        --new-keyfile /etc/ravena/recovery.key "$part" 2>/dev/null &&
        echo "(slot de recuperacao adicionado)"

    cryptsetup open --type luks2 --key-file "$KEYFILE" "$part" "$MAPPER"
    mkfs.ext4 -q -L "$LABEL" "/dev/mapper/$MAPPER"

    echo
    echo "############################################################"
    echo "#  RAVENA-DATA criptografada (LUKS2 - AES-256-XTS)          #"
    echo "#  A chave de recuperacao (IMPRIMA E GUARDE) e:            #"
    echo "#                                                          #"
    echo "#    $rec"
    echo "#                                                          #"
    echo "#  Sem ela + sem o pendrive, os dados ficam INACESSIVEIS.  #"
    echo "############################################################"
    echo

    # A chave TAMBEM vai para o console fisico (tty1) e para todos os
    # terminais (wall), pois via systemd o stdout vai so pro journald.
    for tty in /dev/tty1 /dev/console; do
        [ -w "$tty" ] && {
            echo "############################################################" > "$tty"
            echo "#  RAVENA-DATA criptografada (LUKS2 - AES-256-XTS)          #" > "$tty"
            echo "#  CHAVE DE RECUPERACAO - IMPRIMA E GUARDE:                #" > "$tty"
            echo "#                                                          #" > "$tty"
            echo "#    $rec" > "$tty"
            echo "#                                                          #" > "$tty"
            echo "#  Sem ela + sem o pendrive, os dados ficam INACESSIVEIS.  #" > "$tty"
            echo "############################################################" > "$tty"
        } 2>/dev/null
    done
    echo "CHAVE DE RECUPERACAO: $rec" | timeout 2 wall 2>/dev/null || true
    return 0
}

# ============================================================
# 4a. PERSISTENCIA da pasta unica do usuario na particao de dados
# (/home/ravena/.ravena -> /mnt/ravena-data/ravena). Config + cache + chaves
# sobrevivem ao live ISO. No live, /home/ravena vem do squashfs (ro) e o
# overlay e tmpfs -> sem isso, senhas/configs somem a cada reboot.
persist_ravena_home() {
    local base="$1/ravena"
    mkdir -p "$base/config" "$base/cache" "$base/chaves"
    # 1) pasta unica .ravena
    if [ ! -L /home/ravena/.ravena ] && [ ! -e /home/ravena/.ravena ]; then
        ln -sfn "$base" /home/ravena/.ravena 2>/dev/null || true
    fi
    # 2) config do eDEX-UI persistente (1a vez copia defaults do squashfs)
    if [ -d /home/ravena/.config/eDEX-UI ] && [ ! -e /home/ravena/.config/eDEX-UI.persistido ]; then
        mkdir -p "$base/config/eDEX-UI"
        cp -a /home/ravena/.config/eDEX-UI/. "$base/config/eDEX-UI/" 2>/dev/null || true
        rm -rf /home/ravena/.config/eDEX-UI
        ln -sfn "$base/config/eDEX-UI" /home/ravena/.config/eDEX-UI 2>/dev/null || true
        touch /home/ravena/.config/eDEX-UI.persistido 2>/dev/null || true
    elif [ ! -L /home/ravena/.config/eDEX-UI ]; then
        ln -sfn "$base/config/eDEX-UI" /home/ravena/.config/eDEX-UI 2>/dev/null || true
    fi
    # 3) chaves de acesso em pasta unica (espelho legivel)
    if [ -f /etc/ravena/data.key ] && [ ! -f "$base/chaves/data.key" ]; then
        cp /etc/ravena/data.key "$base/chaves/data.key" 2>/dev/null && chmod 600 "$base/chaves/data.key" 2>/dev/null || true
    fi
    if [ -f /etc/ravena/recovery.key ] && [ ! -f "$base/chaves/recovery.key" ]; then
        cp /etc/ravena/recovery.key "$base/chaves/recovery.key" 2>/dev/null && chmod 600 "$base/chaves/recovery.key" 2>/dev/null || true
    fi
    # 4) perfis de rede WiFi (system-connections) + dotfiles: persistencia
    # 4a. RESTAURA perfis salvos p/ o live (so se a particao tiver perfis)
    if [ -d "$base/config/system-connections" ] && \
       ls "$base/config/system-connections/"*.nmconnection >/dev/null 2>&1; then
        mkdir -p /etc/NetworkManager/system-connections
        cp -a "$base/config/system-connections/". /etc/NetworkManager/system-connections/ 2>/dev/null || true
        chmod 600 /etc/NetworkManager/system-connections/*.nmconnection 2>/dev/null || true
        echo "RAVENA-DATA: perfis WiFi restaurados da particao (system-connections)"
    fi
    # 4b. SINCRONIZA perfis novbos criados no boot atual (ex: OOBE conectou) p/ a particao
    if [ -d /etc/NetworkManager/system-connections ]; then
        mkdir -p "$base/config/system-connections"
        cp -a /etc/NetworkManager/system-connections/. "$base/config/system-connections/" 2>/dev/null || true
    fi
    # 4c. dotfiles (bashrc, bash_profile, tmux.conf, gitconfig): espelho na particao
    mkdir -p "$base/config/dotfiles"
    if ! ls "$base/config/dotfiles/".bashrc >/dev/null 2>&1; then
        cp -a /home/ravena/.bashrc "$base/config/dotfiles/.bashrc" 2>/dev/null || true
        cp -a /home/ravena/.bash_profile "$base/config/dotfiles/.bash_profile" 2>/dev/null || true
        cp -a /home/ravena/.tmux.conf "$base/config/dotfiles/.tmux.conf" 2>/dev/null || true
        cp -a /home/ravena/.gitconfig "$base/config/dotfiles/.gitconfig" 2>/dev/null || true
    else
        cp -a "$base/config/dotfiles/.bashrc" /home/ravena/.bashrc 2>/dev/null || true
        cp -a "$base/config/dotfiles/.bash_profile" /home/ravena/.bash_profile 2>/dev/null || true
        cp -a "$base/config/dotfiles/.tmux.conf" /home/ravena/.tmux.conf 2>/dev/null || true
        cp -a "$base/config/dotfiles/.gitconfig" /home/ravena/.gitconfig 2>/dev/null || true
        echo "RAVENA-DATA: dotfiles restaurados da particao (.bashrc/.bash_profile/.tmux.conf)"
    fi
    echo "RAVENA-DATA: persistencia pronta em /home/ravena/.ravena (config+cache)"
}

# sync perfis de rede p/ a particao de dados (chamado pelo ravena-sync-rede.sh)
sync_network_profiles() {
    if mountpoint -q "$MP" 2>/dev/null; then
        mkdir -p "$MP/ravena/config/system-connections"
        if [ -d /etc/NetworkManager/system-connections ]; then
            cp -a /etc/NetworkManager/system-connections/. "$MP/ravena/config/system-connections/" 2>/dev/null || true
            echo "RAVENA-REDE: perfis WiFi sincronizados p/ RAVENA-DATA"
        fi
        # recarrega caso o NM tenha começado antes da partição
        nmcli connection reload 2>/dev/null || true
    else
        echo "RAVENA-REDE: RAVENA-DATA nao montada - perfis ficam so no boot atual"
    fi
}

# 4. FLUXO PRINCIPAL
# ============================================================
# permite usar o script como biblioteca (testes): so executa main se nao-sourced
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
# no live ISO o /etc e tmpfs: tenta restaurar as chaves do pendrive
[ -f "$KEYFILE" ] || restore_keys_from_pendrive || true

RES=""
for i in $(seq 1 30); do
    RES=$(part_type)
    [ -n "$RES" ] && break
    sleep 1
done

if [ -z "$RES" ]; then
    echo "RAVENA-DATA: particao nao encontrada (sem persistencia)"
    exit 0
fi

case "$RES" in
    mounted|mapper) MP_OK=1 ;;
    new:*)
        part="${RES#new:}"
        first_boot_luks "$part" || exit 0
        MP_OK=1
        ;;
    luks:*)
        part="${RES#luks:}"
        open_luks "$part" || exit 0
        MP_OK=1
        ;;
    *) exit 0 ;;
esac

# OPCAO 1: grava as chaves no pendrive p/ persistencia entre boots
if [ -f "$KEYFILE" ]; then
    persist_keys_to_pendrive
fi

if [ "$MP_OK" = "1" ]; then
    mkdir -p "$MP"
    if ! mountpoint -q "$MP" 2>/dev/null; then
        mount -o rw "/dev/mapper/$MAPPER" "$MP" 2>/dev/null \
            || { echo "RAVENA-DATA: falha ao montar /dev/mapper/$MAPPER"; exit 0; }
    fi
    mkdir -p "$MP/modelos" "$MP/scripts"
    # guarda a chave de recuperacao TAMBEM dentro da particao (copia p/ backup)
    if [ -f /etc/ravena/recovery.key ] && [ ! -f "$MP/CHAVE_RECUPERACAO.txt" ]; then
        cp /etc/ravena/recovery.key "$MP/CHAVE_RECUPERACAO.txt" 2>/dev/null
        chmod 600 "$MP/CHAVE_RECUPERACAO.txt" 2>/dev/null
    fi
    if [ -d /home/ravena ] && [ ! -e /home/ravena/modelos ]; then
        ln -sfn "$MP/modelos" /home/ravena/modelos 2>/dev/null || true
    fi
    persist_ravena_home "$MP"
    echo "RAVENA-DATA: montada em $MP (modelos em /home/ravena/modelos)"
fi
exit 0
fi # fim do main (quando nao-sourced, vira biblioteca de funcoes)