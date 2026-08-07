#!/bin/bash
# Instala llama.cpp + ferramentas de LLM no rootfs Ravena (chroot)
set -e
ROOTFS=/root/ravv2/rootfs

mount -t proc proc "$ROOT/proc" 2>/dev/null || true
mount -t sysfs sys "$ROOT/sys" 2>/dev/null || true
mount -o bind /dev "$ROOT/dev" 2>/dev/null || true
mount -o bind /run "$ROOT/run" 2>/dev/null || true

# DNS utilizavel dentro do chroot (pacman precisa)
cp "$ROOT/etc/resolv.conf" "$ROOT/etc/resolv.conf.bak.wsl" 2>/dev/null
printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' > "$ROOT/etc/resolv.conf"

echo "=== ARCH ===" 
chroot "$ROOT" uname -m 2>/dev/null || echo "falha-chroot"

echo "=== PACMAN -Sy ==="
chroot "$ROOT" pacman -Sy --noconfirm >/tmp/pacman_sy.log 2>&1 || { echo "ERRO pacman -Sy:"; tail -30 /tmp/pacman_sy.log; }

echo "=== pacman -Si llama.cpp ==="
chroot "$ROOT" pacman -Si llama.cpp 2>/dev/null | head -12 || echo "llama.cpp nao encontrado no repo"

echo "=== INSTALL llama.cpp ==="
chroot "$ROOT" pacman -S --noconfirm --needed llama.cpp >/tmp/pacman_llama.log 2>&1 || { echo "ERRO install"; tail -30 /tmp/pacman_llama.log; }

echo "=== binarios ==="
chroot "$ROOT" bash -c 'ls /usr/bin/llama-* 2>/dev/null | head -20'

echo "=== restaurar resolv ==="
mv "$ROOT/etc/resolv.conf.bak.wsl" "$ROOT/etc/resolv.conf" 2>/dev/null || true

umount "$ROOT/run" 2>/dev/null || true
umount "$ROOT/dev" 2>/dev/null || true
umount "$ROOT/sys" 2>/dev/null || true
umount "$ROOT/proc" 2>/dev/null || true
echo "=== FIM ==="