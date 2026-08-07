import json, urllib.request

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

for repo in ["Qwen/Qwen3.5-8B", "Qwen/Qwen3.5-4B", "Qwen/Qwen3.5-1.7B", "Qwen/Qwen3.5-14B"]:
    try:
        d = get("https://huggingface.co/api/models/" + repo)
        cfg = get("https://huggingface.co/" + repo + "/raw/main/config.json")
        arch = cfg.get("architectures")
        print(repo, "| pipe:", d.get("pipeline_tag", "?"), "| arch:", arch, "| dl:", d.get("downloads", 0))
    except Exception as e:
        print(repo, "ERRO:", e)
