import json, urllib.request

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

repo = "DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP"
url = "https://huggingface.co/api/models/" + repo + "/tree/main?recursive=true&expand=false"
d = get(url)
tot = 0
big = []
for e in d:
    sz = e.get("size", 0) or 0
    tot += sz
    if sz > 5e8:
        big.append((e.get("path"), sz))
print("arquivos:", len(d))
print("tamanho total: %.1f GB" % (tot / 1e9))
for p, sz in sorted(big, key=lambda x: -x[1])[:15]:
    print(" ", p, "%.2f GB" % (sz / 1e9))
