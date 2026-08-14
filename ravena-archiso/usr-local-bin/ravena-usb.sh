#!/bin/bash
# RAVENA USB - automount de pendrive/USB
# Uso (chamado pelo udev):
#   ravena-usb.sh add   sdb1
#   ravena-usb.sh remove sdb1
# Uso manual:
#   ravena-usb.sh listar        -> lista pendrives montados
#   ravena-usb.sh montar sdb1   -> monta manualmente
#   ravena-usb.sh desmontar sdb1-> desmonta (ejetar seguro)
# Monta em /mnt/usb/<label> (ou /mnt/usb/sdX1 se nao tiver label).
# Suporte: ext4, vfat/FAT32, exfat, ntfs-3g, auto.

BASE="/mnt/usb"
LOG="/tmp/ravena-usb.log"
MOUNT_TIMEOUT=8

log() { echo "$(date '+%F %T') [$1] $2" >> "$LOG"; }

notify() {
    # aviso visual: tenta o eDEX via wall e echo no tty ativo
    echo -e "\n\033[1;33m[RAVENA USB]\033[0m $1" > /dev/console 2>/dev/null
    logger -t ravena-usb "$1" 2>/dev/null
    log "msg" "$1"
}

safe_label() {
    # converte label do disco em nome de pasta seguro (sem espaco/barra)
    echo "$1" | tr -c 'A-Za-z0-9._-' '_' | sed 's/^_*//;s/_*$//'
}

guess_fstype() {
    local dev="$1"
    blkid -o value -s TYPE "/dev/$dev" 2>/dev/null | head -1
}

is_boot_disk() {
    # ignora particoes do proprio pendrive de boot (o sistema roda DE um USB)
    local dev="$1" rootdev rootdisk disk
    rootdev=$(findmnt -n -o SOURCE / 2>/dev/null)
    [ -n "$rootdev" ] || return 1
    rootdisk=$(lsblk -no PKNAME "$rootdev" 2>/dev/null)
    disk=$(lsblk -no PKNAME "/dev/$dev" 2>/dev/null)
    [ -n "$rootdisk" ] && [ "$disk" = "$rootdisk" ]
}

mount_disk() {
    local dev="$1"
    [ -e "/dev/$dev" ] || { log "erro" "dispositivo /dev/$dev nao existe"; exit 1; }
    mountpoint -q "/dev/$dev" 2>/dev/null && { log "msg" "$dev ja montado"; exit 0; }
    if is_boot_disk "$dev"; then
        log "msg" "$dev e particao do pendrive de boot - ignorada"
        exit 0
    fi

    # se ja esta montado em algum lugar (ex: RAVENA-DATA), nao duplica
    local cur
    cur=$(findmnt -n -o TARGET "/dev/$dev" 2>/dev/null)
    if [ -n "$cur" ]; then
        log "msg" "$dev ja montado em $cur"
        echo "$cur"
        return 0
    fi

    local label fstype name mp
    label=$(blkid -o value -s LABEL "/dev/$dev" 2>/dev/null | head -1)
    fstype=$(guess_fstype "$dev")
    [ -z "$fstype" ] && fstype="auto"
    name=$(safe_label "${label:-${dev}}")
    [ -z "$name" ] && name="$dev"
    mp="$BASE/$name"
    mkdir -p "$mp"

    local opts="rw,nosuid,nodev"
    if [ "$fstype" = "ntfs" ] || [ "$fstype" = "ntfs3" ]; then
        opts="$opts,uid=1000,gid=1000"
        fstype="ntfs-3g"
    elif [ "$fstype" = "vfat" ] || [ "$fstype" = "exfat" ]; then
        opts="$opts,uid=1000,gid=1000"
    fi

    for i in $(seq 1 $MOUNT_TIMEOUT); do
        if mount -t "$fstype" -o "$opts" "/dev/$dev" "$mp" 2>/dev/null; then
            log "montado" "/dev/$dev ($fstype) em $mp"
            notify "Pendrive montado em $mp (conteudo em /mnt/usb)"
            echo "$mp"
            return 0
        fi
        sleep 1
    done
    log "erro" "falha ao montar /dev/$dev ($fstype)"
    notify "FALHA ao montar /dev/$dev ($fstype) - veja /tmp/ravena-usb.log"
    return 1
}

umount_disk() {
    local dev="$1"
    sync
    local cur
    cur=$(findmnt -n -o TARGET "/dev/$dev" 2>/dev/null)
    if [ -n "$cur" ]; then
        if umount "$cur" 2>/dev/null; then
            rmdir "$cur" 2>/dev/null
            log "desmontado" "/dev/$dev de $cur"
            notify "Pendrive /dev/$dev ejetado com seguranca"
            return 0
        else
            log "erro" "falha ao desmontar /dev/$dev (em uso?)"
            notify "Pendrive EM USO - nao ejetado. Feche os arquivos abertos e tente de novo."
            return 1
        fi
    fi
    log "msg" "/dev/$dev nao estava montado"
    return 0
}

case "${1:-listar}" in
    add)        mount_disk "$2" ;;
    remove)     umount_disk "$2" ;;
    montar)     mount_disk "$2" ;;
    desmontar)  umount_disk "$2" ;;
    listar)
        echo "=== PENDRIVES MONTADOS (RAVENA USB) ==="
        findmnt -rno TARGET,SOURCE,FSTYPE,SIZE "$BASE" 2>/dev/null | awk '{printf "  %-30s %-10s %-8s %s\n",$1,$2,$3,$4}'
        echo
        echo "=== DISCOS REMOVIVEIS DISPONIVEIS ==="
        for dev in /sys/block/sd*; do
            [ -e "$dev/removable" ] || continue
            rem=$(cat "$dev/removable" 2>/dev/null)
            [ "$rem" = "1" ] || continue
            base=$(basename "$dev")
            echo "  /dev/$base - $(cat $dev/device/model 2>/dev/null)"
        done
        ;;
    *)
        echo "Uso: ravena-usb.sh {listar|montar <dev>|desmontar <dev>}"
        ;;
esac
exit 0