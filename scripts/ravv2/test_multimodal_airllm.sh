#!/bin/bash
# Valida se o airLLM/transformers 5.12.1 suporta o Qwen3_5ForConditionalGeneration (multimodal)
set -e
cd /root/ravv2
mount -o bind /dev rootfs/dev 2>/dev/null || true
mount -o bind /sys rootfs/sys 2>/dev/null || true
mount -o bind /proc rootfs/proc 2>/dev/null || true
chroot rootfs /bin/bash -lc '
export HF_HUB_DISABLE_PROGRESS_BARS=1
echo "=== 1. transformers tem Qwen3_5? ==="
python3 -c "from transformers.models.qwen3_5 import modeling_qwen3_5; print(\"qwen3_5 module OK\")" 2>&1 | tail -2
echo "=== 2. arquitetura registrada? ==="
python3 -c "
from transformers import AutoConfig, AutoModelForCausalLM, AutoModel
cfg = AutoConfig.from_pretrained(\"DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP\", trust_remote_code=True)
print(\"arch:\", cfg.architectures)
try:
    AutoModelForCausalLM.from_config(cfg)
    print(\"AutoModelForCausalLM.from_config: OK (consegue instanciar)\")
except Exception as e:
    print(\"AutoModelForCausalLM.from_config: FALHOU ->\", type(e).__name__, str(e)[:200])
" 2>&1 | tail -6
'
