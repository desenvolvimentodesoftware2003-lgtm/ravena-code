#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc "$ROOT/proc" 2>/dev/null || true
mount -o bind /sys "$ROOT/sys" 2>/dev/null || true
mount -o bind /dev "$ROOT/dev" 2>/dev/null || true
mount -o bind /run "$ROOT/run" 2>/dev/null || true
cp "$ROOT/etc/resolv.conf" "$ROOT/etc/resolv.conf.bak" 2>/dev/null
printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > "$ROOT/etc/resolv.conf"
echo "=== arch ==="
chroot "$ROOT" uname -m
echo "=== pacman -Sy ==="
chroot "$ROOT" pacman -Sy --noconfirm >/tmp/pac_sy.log 2>&1 || { echo ERRO-SY; tail -30 /tmp/pac_sy.log; }
echo "=== info llama.cpp ==="
chroot "$ROOT" pacman -Si llama.cpp 2>/dev/null | head -14
echo "=== install llama.cpp ==="
chroot "$ROOT" pacman -S --noconfirm --needed llama.cpp >/tmp/pac_ll.log 2>&1 || { echo FAIL-LL; tail -30 /tmp/pac_ll.log; }
echo "=== binarios ==="
chroot "$ROOT" ls /usr/bin/llama-* 2>/dev/null | head -20
mv "$ROOT/etc/resolv.conf.bak" "$ROOT/etc/resolv.conf" 2>/dev/null
umount "$ROOT/run" 2>/dev/null
umount "$ROOT/dev" 2>/dev/null
umount "$ROOT/sys" 2>/dev/null
umount "$ROOT/proc" 2>/dev/null
echo "=== FIM ==="