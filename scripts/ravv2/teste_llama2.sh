#!/bin/bash
set -e
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true

# copia o modelo para dentro do chroot (roota tmp)
if [ ! -f "$ROOT/tmp/qwen05b.gguf" ]; then
  cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"
fi
echo '=== teste inference (Qwen 0.5B) ==='
timeout 300 chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Diga oi em portugues:" -n 64 -t 8 -ngl 0 2>&1 | grep -vE "ggml|llama_|system_info|print_info|load_backend|load_model|(ggml_tensor|n_threads|sparsity|flash_attn|group-attn|rope|kv_cell|kv_self|gqa|no KV|compute|alloc|mmap|LLM)" | tail -30
echo "=== exit: $? ==="

rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
echo FIM