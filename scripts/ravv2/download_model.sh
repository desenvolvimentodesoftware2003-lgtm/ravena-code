#!/bin/bash
set -e
cd /root/ravv2
URL="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
OUT="/root/ravv2/qwen05b.gguf"
if [ -f "$OUT" ] && [ $(stat -c%s "$OUT") -gt 400000000 ]; then
  echo "ja baixado: $(stat -c%s "$OUT") bytes"
else
  echo "baixando modelo 0.5B..."
  curl -sL --retry 3 --max-time 300 -o "$OUT" "$URL"
fi
echo "==="
ls -la "$OUT"
sha256sum "$OUT"