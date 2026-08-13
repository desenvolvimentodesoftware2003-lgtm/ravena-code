#!/bin/bash
# Rebuild RV10 (igual build_rv9b.sh, com lock anti-reexecução)
LOCK=/tmp/build_rv10.lock
exec 9>"$LOCK"
flock -n 9 || { echo "JA-RODANDO, abortando"; exit 0; }
set -e
cd /root/ravv2
NAME=ravena-remaster-RV10

rm -f $NAME.sfs $NAME.sfs.sha512 $NAME.iso $NAME.iso.sha512
pkill -9 mksquashfs 2>/dev/null || true
pkill -9 xorriso 2>/dev/null || true
sleep 1

for m in dev/pts dev proc sys run; do
    while umount "rootfs/$m" 2>/dev/null; do :; done
done

if grep -q "rootfs/\(proc\|sys\|dev\|run\|dev/pts\)" /proc/mounts 2>/dev/null; then
    echo "ERRO: ainda ha pseudo-fs montado dentro do rootfs. Abortando."
    exit 1
fi
BIG=$(find rootfs -xdev -type f -size +10G 2>/dev/null | head -3)
if [ -n "$BIG" ]; then
    echo "ERRO: arquivo anomalo (>10GB) no rootfs:"; echo "$BIG"; exit 1
fi
SIZE_TOTAL=$(du -sb rootfs 2>/dev/null | awk '{print $1}')
if [ "$SIZE_TOTAL" -gt 45000000000 ] || [ "$SIZE_TOTAL" -lt 8000000000 ]; then
    echo "ERRO: tamanho do rootfs ($SIZE_TOTAL bytes) fora da faixa (8-45GB). Abortando."
    exit 1
fi
echo "GUARDA OK: pseudo-fs desmontados, sem arquivos>10GB, rootfs=$SIZE_TOTAL bytes"

echo "=== mksquashfs RV10 (timeout 3600s) ==="
timeout 3600 mksquashfs rootfs $NAME.sfs -noappend -comp zstd -processors 4 -e rootfs/proc rootfs/sys rootfs/dev rootfs/run 2>&1 | tail -2
RC=$?
if [ "$RC" != "0" ]; then
    echo "ERRO: mksquashfs falhou (rc=$RC)."; rm -f $NAME.sfs; exit 1
fi
printf '%s  airootfs.sfs\n' "$(sha512sum $NAME.sfs | awk '{print $1}')" > $NAME.sfs.sha512
cat $NAME.sfs.sha512

echo "=== xorriso remaster (base RV5b, timeout 1200s) ==="
timeout 1200 xorriso -indev ravena-remaster-RV5b.iso -outdev $NAME.iso \
  -map $NAME.sfs /arch/x86_64/airootfs.sfs \
  -map $NAME.sfs.sha512 /arch/x86_64/airootfs.sha512 \
  -boot_image any replay -commit 2>&1 | tail -3
RC=$?
if [ "$RC" != "0" ]; then
    echo "ERRO: xorriso falhou (rc=$RC)."; exit 1
fi
ls -la $NAME.iso
sha512sum $NAME.iso | tee $NAME.iso.sha512
echo DONE_RV10