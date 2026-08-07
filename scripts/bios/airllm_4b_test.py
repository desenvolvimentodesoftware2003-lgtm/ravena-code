import os, time
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
t0 = time.time()
from airllm import AutoModel
print("airllm importado em", round(time.time()-t0, 1), "s")
m = AutoModel.from_pretrained("/data/qwen35-4b-txt", device="cpu", max_seq_len=64)
print("modelo airllm pronto em", round(time.time()-t0, 1), "s, tipo:", type(m).__name__)
print("layer_names:", m.layer_names if hasattr(m, "layer_names") else "n/a")
inp = "O preco da acao da Petrobras hoje"
t1 = time.time()
out = m.generate(inp, max_new_tokens=32)
print("GERADO EM", round(time.time()-t1, 1), "s")
print("saida tokens:", out.shape)
txt = m.tokenizer.decode(out[0].tolist(), skip_special_tokens=True)
print("TEXTO:", txt)