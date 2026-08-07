#!/bin/bash
# Rebuild RV9 com lock anti-reexecução (WSL instável duplica comandos)
LOCK=/tmp/build_rv9.lock
exec 9>"$LOCK"
flock -n 9 || { echo "JA-RODANDO, abortando"; exit 0; }

set -e
cd /root/ravv2
NAME=ravena-remaster-RV9

# remove restos de builds órfãos
rm -f $NAME.sfs $NAME.sfs.sha512 $NAME.iso $NAME.iso.sha512
pkill -9 mksquashfs 2>/dev/null || true
pkill -9 xorriso 2>/dev/null || true
sleep 1

echo "=== mksquashfs RV9 ==="
mksquashfs rootfs $NAME.sfs -noappend -comp zstd -processors 4 2>&1 | tail -2
printf '%s  airootfs.sfs\n' "$(sha512sum $NAME.sfs | awk '{print $1}')" > $NAME.sfs.sha512
cat $NAME.sfs.sha512

echo "=== xorriso remaster (base RV5b) ==="
xorriso -indev ravena-remaster-RV5b.iso -outdev $NAME.iso \
  -map $NAME.sfs /arch/x86_64/airootfs.sfs \
  -map $NAME.sfs.sha512 /arch/x86_64/airootfs.sha512 \
  -boot_image any replay -commit 2>&1 | tail -3
ls -la $NAME.iso
sha512sum $NAME.iso | tee $NAME.iso.sha512
echo DONE