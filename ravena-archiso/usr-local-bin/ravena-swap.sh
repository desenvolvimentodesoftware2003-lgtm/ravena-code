#!/bin/bash
# RAVENA - ativa swapfile no pendrive (RAVENA-DATA/swapfile) no boot.
# Unificacao de memoria: swap ativo antes do login.
set -e

MP="/mnt/ravena-data"
SWF="$MP/swapfile"
SIZE_MB=8192

# ja tem swap? nada a fazer
if swapon --show | grep -q swap; then
  exit 0
fi

# espera a particao montar (ravena-data.service roda no sysinit em paralelo)
for i in $(seq 1 30); do
  mountpoint -q "$MP" 2>/dev/null && break
  sleep 1
done

if ! mountpoint -q "$MP" 2>/dev/null; then
  echo "RAVENA-SWAP: RAVENA-DATA nao montada, sem swap"
  exit 0
fi

if [ ! -f "$SWF" ]; then
  echo "RAVENA-SWAP: criando swapfile ${SIZE_MB}MB em $SWF..."
  fallocate -l ${SIZE_MB}M "$SWF" 2>/dev/null || dd if=/dev/zero of="$SWF" bs=1M count=$SIZE_MB
  chmod 600 "$SWF"
  mkswap "$SWF" >/dev/null
fi

swapon "$SWF" && echo "RAVENA-SWAP: swap ativo ($SWF)"
exit 0
