#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"
echo "### llama-simple-chat $(date +%T)"
timeout 150 chroot $ROOT /usr/bin/llama-simple-chat -m /tmp/qwen05b.gguf -c 4096 -ngl 0 < /dev/null 2>&1 | grep -viE "ggml|llama_|system_info|print_info|loading|load|mmap|warmup|^warning" | tail -15
echo "### exit: $? ($(date +%T))"
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
echo FIM