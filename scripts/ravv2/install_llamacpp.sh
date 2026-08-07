#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc/sys $ROOT/proc 2>/dev/null || true
mount -o bind /sys $ROOT/sys 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
cp $ROOT/etc/resolv.conf $ROOT/etc/resolv.conf.bak 2>/dev/null
printf 'nameserver 1.1.1.1\n' > $ROOT/etc/resolv.conf
echo '=== info llama-cpp ==='
chroot $ROOT pacman -Si llama-cpp 2>/dev/null | head -20
echo '=== info ollama ==='
chroot $ROOT pacman -Si ollama 2>/dev/null | grep -E '^Name|^Version|^Depends|^Conflicts|^Provides|^Size|^Installed' | head -20
echo '=== install llama-cpp ==='
chroot $ROOT pacman -S --noconfirm --needed llama-cpp >/tmp/pac_llc.log 2>&1 || { echo FAIL-LLC; tail -40 /tmp/pac_llc.log; }
echo '=== binarios llama ==='
chroot $ROOT ls /usr/bin/llama-* 2>/dev/null | head -30
echo '=== versao ==='
chroot $ROOT bash -c 'llama-cli --version 2>/dev/null | head -3 || llama-server --version 2>/dev/null | head -3'
mv $ROOT/etc/resolv.conf.bak $ROOT/etc/resolv.conf 2>/dev/null
umount $ROOT/run 2>/dev/null
umount $ROOT/dev 2>/dev/null
umount $ROOT/sys 2>/dev/null
umount $ROOT/proc 2>/dev/null
echo FIM