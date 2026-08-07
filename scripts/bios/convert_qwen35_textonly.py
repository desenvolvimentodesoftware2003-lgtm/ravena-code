#!/usr/bin/env python3
"""Converte checkpoint Qwen3.5 multimodal para text-only (airLLM-compativel).

Renomeia model.language_model.* -> model.*, descarta model.visual.* e model.mtp.*,
e patcheia config.json para architectures=[Qwen3_5ForCausalLM].
Funciona streaming por shard (RAM baixa). Uso:
  convert_qwen35_textonly.py <dir-origem> <dir-destino>
"""
import sys, os, json, shutil
from pathlib import Path

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2])

def convert_shard(src_file, dst_file, keep_map):
    """Reescreve um safetensors renomeando chaves conforme keep_map."""
    from safetensors import safe_open
    from safetensors.torch import save_file
    out = {}
    with safe_open(str(src_file), framework="pt", device="cpu") as f:
        for k in f.keys():
            nk = keep_map.get(k)
            if nk is not None:
                out[nk] = f.get_tensor(k)
    save_file(out, str(dst_file))
    return len(out)

def main():
    os.makedirs(DST, exist_ok=True)
    idx_path = SRC / "model.safetensors.index.json"
    if not idx_path.exists():
        print("ERRO: sem model.safetensors.index.json em", SRC)
        sys.exit(1)
    idx = json.loads(idx_path.read_text())
    wm = idx["weight_map"]

    # build rename map
    keep_map = {}
    for k, f in wm.items():
        if k.startswith("model.language_model."):
            keep_map[k] = "model." + k[len("model.language_model."):]
        elif k == "lm_head.weight":
            keep_map[k] = k
        else:
            continue  # visual/mtp/outros -> descarta

    new_wm = {}
    files = sorted(set(wm.values()))
    for f in files:
        src_file = SRC / f
        if not src_file.exists():
            print("baixar faltante:", f)
            sys.exit(1)
        dst_file = DST / f
        print("convertendo", f, "...", flush=True)
        n = convert_shard(src_file, dst_file, keep_map)
        print("  ok,", n, "tensores", flush=True)

    for k, v in keep_map.items():
        new_wm[v] = wm[k]

    # remove tensores que sobraram em arquivos nao convertidos? nao: so salvamos os mantidos.
    new_idx = {"metadata": idx.get("metadata", {}), "weight_map": new_wm}
    (DST / "model.safetensors.index.json").write_text(json.dumps(new_idx))

    # config.json: patch architectures
    cfg = json.loads((SRC / "config.json").read_text())
    cfg["architectures"] = ["Qwen3_5ForCausalLM"]
    (DST / "config.json").write_text(json.dumps(cfg, indent=2))
    for f in ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt",
              "generation_config.json", "chat_template.json", "tokenizer.model",
              "special_tokens_map.json", "added_tokens.json"]:
        s = SRC / f
        if s.exists():
            shutil.copy2(s, DST / f)
    print("DONE. destino:", DST)
    total_kept = sum(1 for k in keep_map)
    print("tensores mantidos:", total_kept, "| descartados:", len(wm) - total_kept)

if __name__ == "__main__":
    main()
