#!/bin/bash
# RAVENA INSTALLER - instala o Ravena em um disco (ex: NVMe interno).
# Transforma o live ISO (RAM) em instalacao permanente no disco.
#
#   ESQUEMA GPT criado:
#     p1  ESP       512M   vfat   (efi + chaves ravena)
#     p2  RAVENA    20G+   ext4   (sistema raiz)
#     p3  RAVENA-DATA  resto (vazio -> LUKS criado no 1o boot)
#
# USO:  ravena-instalar /dev/nvme0n1   (REESCREVE O DISCO - pede confirmacao)
#       ravena-instalar                (detecta o maior disco interno)
[ "$(id -u)" -eq 0 ] || exec sudo "$0" "$@"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# segurança: nunca instalar no mesmo disco do pendrive de boot
BOOTDISK=$(lsblk -no PKNAME "$(findmnt -no SOURCE /run/archiso/bootmnt 2>/dev/null)" 2>/dev/null)

pick_disk() {
    local d
    if [ -n "$1" ]; then
        [ -b "$1" ] || { echo "ERRO: $1 nao existe"; exit 1; }
        echo "$1"; return
    fi
    # maior disco nao particionado como / do sistema atual (live=ram, qualquer serve)
    for d in $(lsblk -dnpo NAME,TYPE | awk '$2=="disk"{print $1}'); do
        [ "$d" = "$BOOTDISK" ] && continue
        local sz=$(lsblk -dnbo SIZE "$d")
        echo "$d $sz"
    done | sort -k2 -nr | head -1 | awk '{print $1}'
}

# ---- escolhe o disco ----
TARGET=$(pick_disk "$1")
[ -n "$TARGET" ] || { echo "ERRO: nenhum disco interno encontrado"; exit 1; }
TSZ=$(lsblk -dnbo SIZE "$TARGET" | awk '{printf "%.1fGB", $1/1073741824}')
TMOD=$(lsblk -dno MODEL "$TARGET")

echo -e "${RED}==========================================================${NC}"
echo -e "${RED}  INSTALACAO RAVENA - TODO O CONTEUDO SERA APAGADO!${NC}"
echo -e "${RED}==========================================================${NC}"
echo "  Disco alvo : $TARGET  ($TMOD, $TSZ)"
echo "  Esquema    : ESP(512M) + RAVENA(root 20G+) + RAVENA-DATA(resto)"
echo
echo -e "${YELLOW}  Digite EXATAMENTE  instalar  para confirmar: ${NC}"
read -r c
[ "$c" = "instalar" ] || { echo "Cancelado."; exit 1; }

# ---- particiona (GPT) ----
echo "=== Particionando $TARGET (GPT) ==="
wipefs -a "$TARGET"
parted -s "$TARGET" mklabel gpt
parted -s "$TARGET" mkpart ESP fat32 1MiB 513MiB
parted -s "$TARGET" set 1 esp on
parted -s "$TARGET" mkpart RAVENA ext4 513MiB 21441MiB
parted -s "$TARGET" mkpart RAVENA-DATA 21441MiB 100%
sleep 2
partprobe "$TARGET" 2>/dev/null || true
sleep 2

# nomes de particao (nvme0n1p vs sda)
case "$TARGET" in
    *nvme*|*mmc*|*loop*) P1="${TARGET}p1"; P2="${TARGET}p2"; P3="${TARGET}p3" ;;
    *) P1="${TARGET}1";  P2="${TARGET}2";  P3="${TARGET}3" ;;
esac

echo "=== Formatando ==="
mkfs.vfat -F32 -n ESP "$P1" 2>&1 | tail -1
mkfs.ext4 -F -L RAVENA "$P2" 2>&1 | tail -1
# P3 fica SEM filesystem de proposito: ravena-data.sh cria o LUKS no 1o boot

# ---- copia o sistema (live -> disco) ----
echo "=== Copiando o sistema (isso demora) ==="
mkdir -p /mnt/rav-inst /mnt/rav-esp
mount "$P2" /mnt/rav-inst
mount "$P1" /mnt/rav-esp
rsync -aHAXx --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/run \
    --exclude=/tmp --exclude=/mnt --exclude=/media --exclude=/lost+found \
    / /mnt/rav-inst/ 2>&1 | tail -1
mkdir -p /mnt/rav-inst/{proc,sys,dev,run,tmp,mnt,media}

# ---- marca como instalado (ESP interna pode guardar chaves) ----
mkdir -p /mnt/rav-inst/etc/ravena
touch /mnt/rav-inst/etc/ravena/instalado

# ---- fstab (UUIDs reais) ----
U2=$(blkid -s UUID -o value "$P2")
U3=$(blkid -s UUID -o value "$P3")
{
  printf 'UUID=%s  /        ext4    rw,relatime  0 1\n' "$U2"
  printf '# RAVENA-DATA (LUKS criado no 1o boot pelo ravena-data.sh)\n'
  printf 'UUID=%s  /mnt/ravena-data  ext4  noauto,user 0 2\n' "$U3"
} > /mnt/rav-inst/etc/fstab
echo "fstab: root=UUID $U2"

# ---- GRUB EFI ----
echo "=== Instalando GRUB (UEFI) ==="
grub-install --target=x86_64-efi --efi-directory=/mnt/rav-esp \
    --boot-directory=/mnt/rav-inst/boot --removable --recheck 2>&1 | tail -3
BKUUID=$(blkid -s UUID -o value "$P2")
mkdir -p /mnt/rav-inst/etc/default
cat > /mnt/rav-inst/etc/default/grub <<EOF
GRUB_DEFAULT=0
GRUB_TIMEOUT=3
GRUB_DISTRIBUTOR="Ravena"
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"
GRUB_CMDLINE_LINUX="root=UUID=$BKUUID rw"
GRUB_PRELOAD_MODULES="part_gpt ext2"
EOF
# grub.cfg com entrada raiz simples (sem depender de os-prober/chroot)
cat > /mnt/rav-esp/EFI/BOOT/grub.cfg <<EOF
set timeout=3
set default=0
menuentry "Ravena OS" {
    search --no-floppy --fs-uuid --set=root $BKUUID
    linux /boot/vmlinuz-linux root=UUID=$BKUUID rw quiet
    initrd /boot/initramfs-linux.img
}
EOF

sync
umount /mnt/rav-esp /mnt/rav-inst

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  INSTALACAO CONCLUIDA EM $TARGET${NC}"
echo -e "${GREEN}  Remova o pendrive e religue.${NC}"
echo -e "${GREEN}  O 1o boot cria o LUKS da RAVENA-DATA${NC}"
echo -e "${GREEN}  e mostra a chave de recuperacao.${NC}"
echo -e "${GREEN}========================================${NC}"
exit 0