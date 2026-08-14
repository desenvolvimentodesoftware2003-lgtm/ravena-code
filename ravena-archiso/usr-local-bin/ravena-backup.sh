#!/bin/bash
# RAVENA BACKUP - backup diario dos configs criticos p/ /mnt/ravena-data/backup
# Retencao: 7 dias. Manual: `ravena-backup`

BACKUP_DIR="/mnt/ravena-data/backup"
RETENTION=7
STAMP=$(date +%Y%m%d-%H%M)
DEST="$BACKUP_DIR/$STAMP"
LOG_TAG="ravena-backup"

log() { timeout 2 logger -t "$LOG_TAG" "$1" 2>/dev/null; echo "$(date '+%F %T') $1" >> /var/log/ravena-backup.log 2>/dev/null; }

# se a particao de dados nao estiver montada, tenta abrir/montar (SEGURANCA: nunca formata)
if ! mountpoint -q /mnt/ravena-data 2>/dev/null; then
    log "particao nao montada - tentando abrir com chave existente"
    PART=$(blkid -t LABEL="RAVENA-DATA" -o device 2>/dev/null | head -1)
    if [ -n "$PART" ]; then
        [ -e /dev/mapper/ravena-data ] || cryptsetup open --key-file /etc/ravena/data.key "$PART" ravena-data 2>/dev/null \
            || cryptsetup open --key-file /etc/ravena/recovery.key "$PART" ravena-data 2>/dev/null
        [ -e /dev/mapper/ravena-data ] && mount -o rw /dev/mapper/ravena-data /mnt/ravena-data 2>/dev/null
    fi
    mountpoint -q /mnt/ravena-data 2>/dev/null || { log "ERRO: nao consegui montar /mnt/ravena-data - backup cancelado"; exit 1; }
fi

mkdir -p "$DEST"

# itens criticos
cp -a /etc/systemd/system/ravena-*.service "$DEST/" 2>/dev/null
cp -a /etc/systemd/system/ravena-*.timer "$DEST/" 2>/dev/null
cp -a /etc/ravena/ "$DEST/etc-ravena/" 2>/dev/null
cp -a /usr/local/bin/ravena-* "$DEST/" 2>/dev/null
cp -a /home/ravena/.bashrc "$DEST/bashrc" 2>/dev/null || cp -a /root/.bashrc "$DEST/bashrc" 2>/dev/null
cp -a /home/ravena/.bash_profile "$DEST/" 2>/dev/null || cp -a /root/.bash_profile "$DEST/" 2>/dev/null
cp -a /home/ravena/.tmux.conf "$DEST/" 2>/dev/null || cp -a /root/.tmux.conf "$DEST/" 2>/dev/null
cp -a /home/ravena/.config/eDEX-UI/ "$DEST/eDEX-UI/" 2>/dev/null || cp -a /root/.config/eDEX-UI/ "$DEST/" 2>/dev/null
[ -d /home/ravena/projects ] && cp -a /home/ravena/projects "$DEST/projects/" 2>/dev/null

COUNT=$(find "$DEST" -type f | wc -l)
log "backup completo: $DEST ($COUNT arquivos)"

# retencao
ls -1d "$BACKUP_DIR"/20* 2>/dev/null | sort -r | tail -n +$((RETENTION+1)) | while read -r old; do
    rm -rf "$old"
    log "backup antigo removido: $old"
done

echo "Backup OK: $DEST"
exit 0