#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
echo "=== inicio $(date +%T) ==="
chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Diga oi em portugues:" -n 64 -t 8 -ngl 0 --no-display-prompt 2>/tmp/llama_err.txt | tail -25
echo "=== stderr (filtrado) ==="
grep -vE "ggml|llama_|system_info|print_info|load|mmap|compute|alloc|KV|attn|rope|arch|sparsity|flash|n_threads|n_ctx|tensor" /tmp/llama_err.txt | head -15
echo "=== fim $(date +%T) ==="
rm -f $ROOT/tmp/qwen05b.gguf
umount $ROOT/run 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
echo FIM