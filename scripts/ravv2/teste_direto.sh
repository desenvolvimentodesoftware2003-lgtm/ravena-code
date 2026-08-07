#!/bin/bash
# teste direto no host WSL usando binario do rootfs (Arch) com libs do rootfs
ROOT=/root/ravv2/rootfs
export LD_LIBRARY_PATH="$ROOT/usr/lib:$ROOT/usr/lib/ggml"
echo "=== inicio $(date +%T) ==="
timeout 180 $ROOT/usr/bin/llama-cli -m /root/ravv2/rootfs/tmp/qwen05b.gguf -p "Diga oi em portugues:" -n 48 -t 4 -ngl 0 --no-mmap --no-display-prompt --no-conversation 2>/tmp/llama_d.err | tail -20
echo "=== exit: $? ($(date +%T)) ==="
echo "=== stderr filtrado ==="
grep -viE "ggml|llama_|system_info|print_info|load|mmap|compute|alloc|KV|attn|rope|arch|sparsity|flash|n_threads|n_ctx|tensor|model|dev|sampl|war" /tmp/llama_d.err | head -12
echo FIM