#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
echo '=== pacman -Q llm ==='
chroot $ROOT pacman --query 2>/dev/null | grep -i llama
chroot $ROOT pacman --query 2>/dev/null | grep -i ggml
echo '=== binarios ==='
chroot $ROOT ls /usr/bin 2>/dev/null | grep -i llama
echo '=== version ==='
chroot $ROOT /usr/bin/llama-cli --version 2>&1 | head -2
echo FIM