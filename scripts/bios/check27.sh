#!/bin/bash
curl -s 'https://huggingface.co/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP/resolve/main/model.safetensors.index.json' -o /root/ravv2/index27.json
curl -s 'https://huggingface.co/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP/resolve/main/config.json' -o /root/ravv2/cfg27.json
python3 - <<'PYEOF'
import json
idx=json.load(open('/root/ravv2/index27.json'))
wm=idx['weight_map']
ks=list(wm.keys())
print('total tensores:', len(ks))
def classify(k):
    if k.startswith('model.language_model.'): return 'language_model'
    if k.startswith('model.visual.'): return 'visual'
    if k.startswith('model.mtp'): return 'mtp'
    if k=='lm_head.weight': return 'lm_head'
    return 'outros_'+k.split('.')[0]
from collections import Counter
print('classes:', dict(Counter(classify(k) for k in ks)))
print('files:', sorted(set(wm.values())))
print('exemplos:', ks[:3], '...', ks[-3:])
cfg=json.load(open('/root/ravv2/cfg27.json'))
print('arch:', cfg.get('architectures'))
print('text_config arch:', cfg.get('text_config',{}).get('model_type'))
print('layers:', cfg.get('text_config',{}).get('num_hidden_layers'))
PYEOF