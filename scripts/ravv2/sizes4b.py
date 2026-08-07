import json, urllib.request
req = urllib.request.Request("https://huggingface.co/api/models/Qwen/Qwen3.5-4B/tree/main?recursive=true", headers={"User-Agent":"Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    d = json.load(r)
for e in d:
    if "safetensors-000" in e.get("path",""):
        print(e["path"], "%.2f GB" % (e.get("size",0)/1e9))