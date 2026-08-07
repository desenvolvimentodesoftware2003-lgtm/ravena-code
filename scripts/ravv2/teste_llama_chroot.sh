#!/bin/bash
# Teste do llama-cli no chroot do rootfs (CPU do WSL host)
set -e
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true

echo '=== version ==='
chroot $ROOT /usr/bin/llama-cli --version 2>&1 | head -3

echo '=== teste inference (Qwen 0.5B, prompt curto) ==='
timeout 240 chroot $ROOT /usr/bin/llama-cli -m /root/ravv2/qwen05b.gguf -p "Diga oi em portugues:" -n 64 -t 8 -ngl 0 --no-display-prompt 2>&1 | grep -vE "load|llama_|system_info|print_info|ggml" | head -40
echo "=== exit: $? ==="

umount $ROOT/run 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
echo FIM