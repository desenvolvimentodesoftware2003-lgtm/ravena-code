import json, urllib.request

def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if raw else json.load(r)

for repo in ["Qwen/Qwen3.6-27B", "DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-MTP"]:
    try:
        d = get("https://huggingface.co/api/models/" + repo)
        print(repo, "| pipeline:", d.get("pipeline_tag", "?"), "| lib:", d.get("library_name", "?"), "| downloads:", d.get("downloads"))
        cfg = get("https://huggingface.co/" + repo + "/raw/main/config.json")
        print("   arch:", cfg.get("architectures"), "| model_type:", cfg.get("model_type"), "| language_model_only:", cfg.get("language_model_only"))
    except Exception as e:
        print(repo, "ERRO:", e)
