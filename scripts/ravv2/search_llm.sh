#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc/sys $ROOT/proc/sys 2>/dev/null || true
mount -o bind /proc/sys $ROOT/proc 2>/dev/null || true
mount -o bind /sys $ROOT/sys 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
cp $ROOT/etc/resolv.conf $ROOT/etc/resolv.conf.bak 2>/dev/null
printf 'nameserver 1.1.1.1\n' > $ROOT/etc/resolv.conf
echo '=== search llama ==='
chroot $ROOT pacman -Ss llama 2>/dev/null | head -20
echo '=== search ollama ==='
chroot $ROOT pacman -Ss ollama 2>/dev/null | head -10
echo '=== search ggml ==='
chroot $ROOT pacman -Ss ggml 2>/dev/null | head
echo '=== search small models/tools ==='
chroot $ROOT pacman -Ss llm 2>/dev/null | head -15
mv $ROOT/etc/resolv.conf.bak $ROOT/etc/resolv.conf 2>/dev/null
umount $ROOT/run 2>/dev/null
umount $ROOT/dev 2>/dev/null
umount $ROOT/sys 2>/dev/null
umount $ROOT/proc 2>/dev/null
echo FIM