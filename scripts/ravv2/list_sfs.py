import json, urllib.request

repo = "Qwen/Qwen3.5-4B"
url = f"https://huggingface.co/api/models/{repo}/tree/main?recursive=true"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as r:
    d = json.load(r)
big = [e["path"] for e in d if e.get("path","").endswith(".safetensors")]
print("\n".join(big))