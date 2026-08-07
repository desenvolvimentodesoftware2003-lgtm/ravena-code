import os, time
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
from airllm import AutoModel
m = AutoModel.from_pretrained("/data/qwen35-4b-txt", device="cpu", max_seq_len=32)
print("modelo pronto:", type(m).__name__)
inp = "O preco da acao da Petrobras hoje"
ids = m.tokenizer.encode(inp, return_tensors="pt")[:, :31]
print("input:", ids.shape)
t1 = time.time()
out = m.generate(ids, max_new_tokens=16, do_sample=False)
print("GERADO EM", round(time.time()-t1, 1), "s")
txt = m.tokenizer.decode(out[0].tolist(), skip_special_tokens=True)
print("TEXTO:", txt)