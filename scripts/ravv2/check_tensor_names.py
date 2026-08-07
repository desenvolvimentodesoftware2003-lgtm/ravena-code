import json, urllib.request

def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read() if raw else json.load(r)

idx = get("https://huggingface.co/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP/raw/main/model.safetensors.index.json")
wm = idx["weight_map"]
ks = list(wm.keys())
print("total tensores:", len(ks))
for k in ks[:12]:
    print(" ", k)
print(" ...")
emb = [k for k in ks if k.endswith("embed_tokens.weight") or k.endswith("lm_head.weight")]
for k in emb:
    print(" ", k, "->", wm[k])
# checa se ha prefixo language_model
lm = [k for k in ks if k.startswith("model.language_model")]
vl = [k for k in ks if "visual" in k.lower() or "vision" in k.lower()]
print("tensores com language_model:", len(lm))
print("tensores com visual/vision:", len(vl))
top = sorted(set(k.split(".")[1] if k.startswith("model.") else k.split(".")[0] for k in ks))
print("prefixos de 1o nivel:", top)
