#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
echo "=== /dev dentro do chroot ==="
ls $ROOT/dev/ | head -15
echo "=== urandom existe? ==="
ls -la $ROOT/dev/urandom $ROOT/dev/random 2>/dev/null || echo "FALTA urandom/random"
echo "=== teste simples: cat /dev/urandom no chroot ==="
timeout 5 chroot $ROOT head -c 32 /dev/urandom | xxd | head -2
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"
echo "=== teste llama -t 1, 8 tokens ==="
timeout 90 chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Oi:" -n 8 -t 1 -ngl 0 --no-conversation < /dev/null 2>&1 | tail -12
echo "### exit: $?"
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
echo FIM