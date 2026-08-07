#!/bin/bash
# Teste barato: AutoModelForCausalLM.from_config com config multimodal patcheado
# (Qwen3_5ForConditionalGeneration -> Qwen3_5ForCausalLM), sem baixar pesos.
cd /root/ravv2
mount -o bind /dev rootfs/dev 2>/dev/null || true
mount -o bind /sys rootfs/sys 2>/dev/null || true
mount -o bind /proc rootfs/proc 2>/dev/null || true
timeout 120 chroot rootfs /bin/bash -lc '
set -e
export HF_HUB_DISABLE_PROGRESS_BARS=1
python3 - <<'"'"'PYEOF'"'"'
from transformers import AutoConfig, AutoModelForCausalLM
from accelerate import init_empty_weights

cfg = AutoConfig.from_pretrained("Qwen/Qwen3.5-4B", trust_remote_code=False)
print("arch original:", cfg.architectures)
cfg.architectures = ["Qwen3_5ForCausalLM"]
print("arch patcheado:", cfg.architectures)

with init_empty_weights(include_buffers=False):
    model = AutoModelForCausalLM.from_config(cfg, trust_remote_code=False)
print("MODELO CRIADO:", type(model).__name__)
print("atributos do topo:", [n for n, _ in model.named_children()])
print("model.model:", type(model.model).__name__)
print("layer0:", type(model.model.layers[0]).__name__ if hasattr(model.model, "layers") else "SEM .layers")
PYEOF
'
