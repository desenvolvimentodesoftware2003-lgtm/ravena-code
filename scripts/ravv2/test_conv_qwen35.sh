#!/bin/bash
# FIM-A-FIM: converte Qwen3.5-4B para text-only e roda airLLM (1 geracao)
set -uo pipefail
cd /root/ravv2
mount -o bind /dev rootfs/dev 2>/dev/null || true
mount -o bind /sys rootfs/sys 2>/dev/null || true

SRC=rootfs/data/qwen35-4b-src
# copia os pesos baixados no host p/ dentro do rootfs
cp qwen35_4b_shard01.safetensors "$SRC/model.safetensors-00001-of-00002.safetensors"
cp qwen35_4b_shard02.safetensors "$SRC/model.safetensors-00002-of-00002.safetensors"
cp convert_qwen35_textonly.py rootfs/root/convert_qwen35_textonly.py

timeout 1200 chroot rootfs /bin/bash -lc '
set -e
export HF_HUB_DISABLE_PROGRESS_BARS=1
cd /root
du -sh /data/qwen35-4b-src
echo "=== 1. converte para text-only ==="
python3 /root/convert_qwen35_textonly.py /data/qwen35-4b-src /data/qwen35-4b-txt > /root/conv.log 2>&1
echo "CONV_EXIT=$?"
tail -6 /root/conv.log
du -sh /data/qwen35-4b-txt
echo "=== 2. valida index convertido ==="
python3 - <<PYEOF
from safetensors import safe_open
import json
idx = json.load(open("/data/qwen35-4b-txt/model.safetensors.index.json"))
ks = list(idx["weight_map"].keys())
print("tensores:", len(ks))
print("embed:", any(k=="model.embed_tokens.weight" for k in ks))
print("layers.0:", any(k.startswith("model.layers.0.") for k in ks))
print("lm_head:", "lm_head.weight" in ks)
print("sobrou language_model:", any("language_model" in k for k in ks))
print("sobrou visual:", any("visual" in k for k in ks))
# fila por arquivo
from collections import Counter
cnt = Counter(idx["weight_map"].values())
print("por arquivo:", dict(cnt))
PYEOF"
' 2>&1 | tail -20