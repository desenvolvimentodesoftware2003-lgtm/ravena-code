import sys, json, urllib.request
url = "https://huggingface.co/api/models/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP"
with urllib.request.urlopen(url, timeout=60) as r:
    d = json.load(r)
sibs = d.get("siblings", [])
tot = sum(s.get("size", 0) for s in sibs) / 1e9
print("arquivos:", len(sibs))
print("tamanho total: %.1f GB" % tot)
for s in sibs:
    sz = s.get("size", 0)
    if sz > 1e9:
        print(" ", s["rfilename"], "%.2f GB" % (sz / 1e9))
