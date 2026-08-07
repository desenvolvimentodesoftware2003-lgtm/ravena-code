#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"
echo "### llama-simple-chat (batch, sai sozinho) $(date +%T)"
timeout 120 chroot $ROOT /usr/bin/llama-simple-chat -m /tmp/qwen05b.gguf -p "Diga oi em portugues em uma frase." -n 64 -t 4 -ngl 0 --no-warmup 2>/tmp/ls_err.log | grep -viE "ggml|llama_|system_info|print_info|loading|load|mmap|warmup" | tail -12
echo "### exit: $?"
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
echo FIM