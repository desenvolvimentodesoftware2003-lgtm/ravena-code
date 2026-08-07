#!/bin/bash
set -e
cd /root/ravv2
NAME=ravena-remaster-RV9
echo "=== limpeza cache pacman ==="
rm -f rootfs/var/cache/pacman/pkg/*.pkg.tar.zst
rm -f rootfs/tmp/ks_test*.nft
echo "=== mksquashfs RV9 ==="
rm -f $NAME.sfs $NAME.sfs.sha512
mksquashfs rootfs $NAME.sfs -noappend -comp zstd -processors 4 2>&1 | tail -2
printf '%s  airootfs.sfs\n' "$(sha512sum $NAME.sfs | awk '{print $1}')" > $NAME.sfs.sha512
cat $NAME.sfs.sha512

echo "=== xorriso remaster (base RV5b) ==="
rm -f $NAME.iso
xorriso -indev ravena-remaster-RV5b.iso -outdev $NAME.iso \
  -map $NAME.sfs /arch/x86_64/airootfs.sfs \
  -map $NAME.sfs.sha512 /arch/x86_64/airootfs.sha512 \
  -boot_image any replay -commit 2>&1 | tail -3
ls -la $NAME.iso
sha512sum $NAME.iso | tee $NAME.iso.sha512
echo DONE