#!/bin/bash
# provision_bios.sh - Provisiona o penrive SanDisk real (Disco 1) com Ravena RV9 + RAVENA-DATA
# e prepara o alvo real (Qwen 3.6-27B text-only p/ airLLM) ANTES de aplicar na BIOS.
#
# USO (no Windows, WSL como host):
#   Apagar pendrive no Windows (rmdisk, GPT/MBR) primeiro.
#   wsl -e bash /mnt/c/Users/DELL/AppData/Local/Temp/opencode/ravena_ops/provision_bios.sh
#
# O script escreve direto em /dev/sdX escolhido (BBBRIEFO) e valida com lsblk.
set -uo pipefail

# ---- Parametros (edite aqui) ----
ISO=/mnt/c/Users/DELL/OneDrive/Documentos/RAVENA-RV7/ravena-remaster-RV9.iso
DEV=/dev/sde                 # verificar com lsblk: deve ser o SanDisk 114GB
DATA_LABEL=RAVENA-DATA
SWAP_SIZE_MB=8192
LLM_SRC="DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP"
# pasta local (chroot) onde ficará o modelo convertido text-only
LLM_DIR=/root/ravv2/rootfs/data/qwen27b-txt

log()  { echo -e "\n[provision] $*"; }
die()  { echo -e "\n[ERRO] $*"; exit 1; }

# ---- 0. Sanidade ----
[ -f "$ISO" ] || die "ISO nao encontrado: $ISO"
[ -b "$DEV" ] || die "Dispositivo nao encontrado ou nao confirma: $DEV (ajuste DEV=)"
lsblk -o NAME,SIZE,FSTYPE,LABEL,MODEL "$DEV" || die "sem lsblk"

df -h / | tail -1
free -h | head -2

# ---- 1. Aviso e confirmação (por fdisk: wipe completo do pendrive) ----
echo "ATENCAO: $DEV sera completamente apagado!"
echo "Tem certeza? (digite: PROVISIONAR)"
read -r conf
[ "$conf" = "PROVISIONAR" ] || die "cancelado"

umount "$DEV"?* 2>/dev/null || true

# ---- 2. DD do ISO (isohybrid) + append partinso de dados ----
log "Gravando ISO com dd (pode demorar ~un10 min)..."
dd if="$ISO" of="$DEV" bs=4M status=progress conv=fsync || die "dd falhou"
partprobe "$DEV" || true

log "Criando partição RAVENA-DATA (restante)..."
# localizar fim do disco
END_SECT=$(( $(blockdev --getsize64 "$DEV") / 512 - 1 ))
# incluir partição logo apia imagem ISO: iniciar em +1 setor do ISO (na prática: fim do iso)
START_SECT=$(( 2500000000 / 512 ))   # ~2.5GB offset obtido do GetPartition do ISO RV9
# partição MBR extendida não-necessária: append direto
sfdisk --append "$DEV" <<EOF
$START_SECT,$END_SECT,L,*
EOF
partprobe "$DEV"
sleep 2
lsblk -o NAME,SIZE,FSTYPE,LABEL "$DEV"

# ---- 3. mkfs da partição de dados ----
# obter a p última do pendrive (a recém-criada)
PART_FULL=$(lsblk -p -l -o NAME,TYPE "$DEV" | awk '$2=="part" {n=$1} END{print n}')
[ -n "$PART_FULL" ] || die "partição não encontrada"
log "Partição de dados: $PART_FULL"
mkfs.ext4 -L "$DATA" -F "$PART_FULL" || die "mkfs falhou"

# ---- 4. Swap: arquivo dentro de RAVENA-DATA (sem repartição extra) ----
log "Montando RAVENA-DATA p/ criar swapfile..."
mkdir -p /mnt/rvdata
mount "$PART_FULL" /mnt/rvdata || die "mount falhou"
[ -f /mnt/rvdata/swapfile ] || {
    fallocate -l ${SWAP_SIZE_MB}M /mnt/rvdata/swapfile || trunr
    chmod 600 /mnt/rvdata/swapfile
    mkswap /mnt/rvdata/swapfile || die "mkswap"
}
sync

# ---- 5. Destino do modelo IRAL ao target real ----
# Baixar e converter o 27B text-only DENTRO do rootfs (preparado p/ o airLLM), e mover p/ RAVENA-DATA?
# No fluxo real: o boot do Ravena monta RAVENA-DATA em /mnt/ravena-data; o AIRL VM-bun pip ele lê de lá.
# Aqui (pré-BOS) baixamos na partição montada:
MODEL_DST=/mnt/rvdata/qwen27b-txt
log "Destino do modelo no pendrive: $MODEL_DST"

# swapfile: sem ativar aqui (será ativo no boot pelo ravena-swap.service)

rmdir /mnt/rvdata
umount "$PART_FULL" 2>/dev/null || true
log "PRONTO! Provioner criado. Shon a nova distribuição/análise."