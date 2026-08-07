#!/bin/bash
# TESTE FIM-A-FIM: baixa Qwen3.5-4B, converte text-only, roda airLLM (1 resposta)
cd /root/ravv2
mount -o bind /dev rootfs/dev 2>/dev/null || true
mount -o bind /sys rootfs/sys 2>/dev/null || true
mount -o bind /proc rootfs/proc 2>/dev/null || true
cp convert_qwen35_textonly.py rootfs/root/convert_qwen35_textonly.py
timeout 3000 chroot rootfs /bin/bash -lc '
set -e
export HF_HUB_DISABLE_PROGRESS_BARS=1
cd /root
echo "=== 1. baixa o checkpoint safetensors do Qwen3.5-4B ==="
mkdir -p /data/qwen35-4b-src
python3 - <<'"'"'PYEOF'"'"'
from huggingface_hub import snapshot_download
p = snapshot_download("Qwen/Qwen3.5-4B", local_dir="/data/qwen35-4b-src")
print("baixado em:", p)
PYEOF
ls -la /data/qwen35-4b-src/ | head -8
du -sh /data/qwen35-4b-src
echo "=== 2. converte para text-only ==="
python3 /root/convert_qwen35_textonly.py /data/qwen35-4b-src /data/qwen35-4b-txt 2>&1 | tail -5
ls -la /data/qwen35-4b-txt/ | head -8
du -sh /data/qwen35-4b-txt
echo "=== 3. valida conversao: chaves e shapes ==="
python3 - <<'"'"'PYEOF'"'"'
from safetensors import safe_open
import json
idx = json.load(open("/data/qwen35-4b-txt/model.safetensors.index.json"))
ks = list(idx["weight_map"].keys())
print("tensores apos conversao:", len(ks))
print("  ex: embed_tokens", "model.embed_tokens.weight" in ks, "| layers.0:", any(k.startswith("model.layers.0.") for k in ks), "| lm_head:", "lm_head.weight" in ks)
print("  sobrou language_model?", any("language_model" in k for k in ks))
print("  sobrou visual?", any("visual" in k for k in ks))
import os
cfg = json.load(open("/data/qwen35-4b-txt/config.json"))
print("  architectures:", cfg["architectures"])
PYEOF
echo "=== 4. airLLM no checkpoint convertido (streaming) ==="
python3 - <<'"'"'PYEOF'"'"'
import time
from airllm import AutoModel
t0 = time.time()
m = AutoModel.from_pretrained("/data/qwen35-4b-txt", device="cpu", max_seq_len=64)
print("carregado em %.0fs" % (time.time()-t0))
tk = m.tokenizer("The capital of France is", return_tensors="pt")
t1 = time.time()
out = m.generate(tk["input_ids"], max_new_tokens=24, do_sample=False)
txt = m.tokenizer.decode(out[0].cpu().tolist(), skip_special_tokens=True)
print("GERADO:", txt)
print("gen em %.1fs" % (time.time()-t1))
PYEOF
echo "=== FIM TESTE ==="
'
