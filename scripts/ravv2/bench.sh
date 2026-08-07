#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"
echo "### bench 100 tokens (release? debug?) $(date +%T)"
timeout 180 chroot $ROOT /usr/bin/llama-bench -m /tmp/qwen05b.gguf -t 4 -p 32 -n 64 -ngl 0 2>&1 | grep -viE "ggml|llama_|system_info|print_info|warning|loading" | tail -8
echo "### exit: $? ($(date +%T))"
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
echo FIM