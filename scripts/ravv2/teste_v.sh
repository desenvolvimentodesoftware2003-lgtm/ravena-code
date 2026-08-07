#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"

echo "=== validar modelo ==="
timeout 30 chroot $ROOT /usr/bin/llama-gguf-hash /tmp/qwen05b.gguf 2>&1 | tail -3
echo "gguf-hash exit: $?"

echo "=== teste 1 token com verboso (max 60s) ==="
setsid timeout --foreground -k 5 60 chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Oi:" -n 1 -t 4 -ngl 0 --no-conversation --verbose < /dev/null > /tmp/llm_v.log 2>&1
echo "llama exit: $?"
echo "--- ultimas 25 linhas ---"
tail -25 /tmp/llm_v.log
echo "--- greps uteis ---"
grep -iE "error|fail|abort|segv|assert" /tmp/llm_v.log | head -10
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
echo FIM