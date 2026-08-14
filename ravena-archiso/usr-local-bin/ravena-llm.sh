#!/bin/bash
# RAVENA LLM provider - prioriza GGUF L3-Dark-Planet-8B Q4_K_M (llama-server);
# airLLM text-only fica como fallback futuro (quando houver rede p/ safetensors).
set -e
CONF=/etc/ravena/llm.conf
LLM_QUANT=Q4_k_m
LLM_PORT=8080
SERVE=/usr/local/bin/ravena-airllm-server.py
[ -f "$CONF" ] && . "$CONF"

MODELOS="/mnt/ravena-data/modelos"
[ -d "$MODELOS" ] || MODELOS="/home/ravena/modelos"
TXT_DIR="/mnt/ravena-data/modelos/qwen27b-txt"

# --- 1. prioridade: GGUF L3-Dark-Planet-8B via llama-server (MHA puro,
#    3.78 tok/s medido em i7-8665U 7.7GB; ~3.9GB de RAM total) ---
F=""
for q in "$LLM_QUANT" "Q4_k_s" "Q5_k_s"; do
  f="$MODELOS/L3-Dark-Planet-8B-D_AU-${q}.gguf"
  [ -f "$f" ] && { F="$f"; break; }
done
[ -z "$F" ] && F=$(ls "$MODELOS"/L3-Dark-Planet*gguf 2>/dev/null | head -1)
if [ -n "$F" ] && [ -f "$F" ]; then
  echo "ravena-llm: provendo GGUF em $(basename "$F") na :$LLM_PORT"
  exec llama-server -m "$F" -c 4096 --port "$LLM_PORT" -fit off --load-mode mmap \
    --threads "$(nproc)" --host 0.0.0.0
fi

# --- 2. fallback: airLLM text-only (safetensors convertido) ---
if [ -f "$TXT_DIR/model.safetensors.index.json" ]; then
  echo "ravena-llm: provendo AirLLM text-only de $TXT_DIR na :$LLM_PORT"
  export LLM_PORT
  exec python3 "$SERVE" "$TXT_DIR"
fi

echo "ravena-llm: nenhum modelo disponivel. Rodar: llm baixar-dark-planet Q4_k_m"
exit 0