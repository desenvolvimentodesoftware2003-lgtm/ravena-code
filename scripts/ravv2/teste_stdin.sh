#!/bin/bash
ROOT=/root/ravv2/rootfs
mount -o bind /proc $ROOT/proc 2>/dev/null || true
mount -o bind /dev $ROOT/dev 2>/dev/null || true
mount -o bind /run $ROOT/run 2>/dev/null || true
[ -f "$ROOT/tmp/qwen05b.gguf" ] || cp /root/ravv2/qwen05b.gguf "$ROOT/tmp/qwen05b.gguf"
echo "### inicio $(date +%T)"
timeout 120 chroot $ROOT /usr/bin/llama-cli -m /tmp/qwen05b.gguf -p "Diga oi em portugues:" -n 48 -t 4 -ngl 0 --no-mmap --no-display-prompt --no-conversation < /dev/null 2>/tmp/llm_e2.txt
echo "### exit: $? ($(date +%T))"
echo "### saida:"
cat /tmp/llm_e2.txt | grep -viE "ggml|llama_|system_info|print_info|load|mmap|compute|alloc|KV|attn|rope|arch|sparsity|flash|n_threads|n_ctx|tensor|model|dev|sampl|war|main:|sampling" | head -15
rm -f "$ROOT/tmp/qwen05b.gguf"
umount $ROOT/run 2>/dev/null || true
umount $ROOT/dev 2>/dev/null || true
umount $ROOT/proc 2>/dev/null || true
echo FIM