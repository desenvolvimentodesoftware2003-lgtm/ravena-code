#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
nohup chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Diga oi em portugues:" -n 64 -t 8 -ngl 0 --no-display-prompt --no-conversation > /tmp/llama_out.txt 2>&1 &
echo "PID: $!" > /tmp/llama_pid.txt
echo "iniciado $(date +%T)"
sleep 1
cat /tmp/llama_pid.txt