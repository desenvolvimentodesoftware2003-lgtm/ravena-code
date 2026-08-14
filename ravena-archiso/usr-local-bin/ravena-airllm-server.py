#!/usr/bin/env python3
"""RAVENA airLLM provider - API OpenAI-compativel em :8080 (stdlib/gunicorn).

Serve /v1/chat/completions usando AirLLM com o checkpoint Qwen text-only
convertido (sem visual/mtp). Sem dependencias extras (wsgiref).
"""
import os, sys, json, threading, time

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

MODEL_DIR = sys.argv[1] if len(sys.argv) > 1 else "/mnt/ravena-data/modelos/qwen27b-txt"
PORT = int(os.environ.get("LLM_PORT", "8080"))
MAX_NEW = int(os.environ.get("LLM_MAX_NEW_TOKENS", "512"))

print(f"ravena-airllm: carregando {MODEL_DIR} ...", flush=True)
t0 = time.time()
from airllm import AutoModel
model = AutoModel.from_pretrained(MODEL_DIR, device="cpu", max_seq_len=8192)
print(f"ravena-airllm: carregado em {time.time()-t0:.0f}s", flush=True)
print("ravena-airllm: pronto em :%d" % PORT, flush=True)

from wsgiref.simple_server import make_server

LOCK = threading.Lock()

def chat_completion(messages):
    with LOCK:
        prompt = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                prompt += content + "\n"
            elif role == "user":
                prompt += content + "\n"
            elif role == "assistant":
                prompt += content + "\n"
        prompt = prompt.strip()
        if not prompt:
            prompt = "oi"
        ids = model.tokenizer(prompt, return_tensors="pt")["input_ids"]
        ids = ids[:, -8191:]
        t1 = time.time()
        out = model.generate(ids, max_new_tokens=MAX_NEW, do_sample=True, temperature=0.7, top_p=0.95)
        gen = time.time() - t1
        text = model.tokenizer.decode(out[0].tolist(), skip_special_tokens=True)
        return text, gen

def application(environ, start_response):
    if environ.get("PATH_INFO") == "/v1/chat/completions" and environ["REQUEST_METHOD"] == "POST":
        try:
            length = int(environ.get("CONTENT_LENGTH", 0))
            body = json.loads(environ["wsgi.input"].read(length) or b"{}")
            messages = body.get("messages", [])
            max_tokens = int(body.get("max_tokens", MAX_NEW))
            global MAX_NEW
            MAX_NEW = max(1, min(max_tokens, 4096))
            text, gen = chat_completion(messages)
            resp = {
                "id": "ravena-airllm",
                "object": "chat.completion",
                "model": "qwen",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": text},
                             "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "gen_seconds": round(gen, 2),
            }
            payload = json.dumps(resp).encode()
            start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(payload)))])
            return [payload]
        except Exception as e:
            err = json.dumps({"error": {"message": str(e)}}).encode()
            start_response("500 Internal Server Error", [("Content-Type", "application/json")])
            return [err]
    if environ.get("PATH_INFO") == "/" :
        payload = b"RAVENA airLLM provider :8080"
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [payload]
    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"not found"]

if __name__ == "__main__":
    server = make_server("0.0.0.0", PORT, application)
    print("ravena-airllm: servindo em http://0.0.0.0:%d/v1/chat/completions" % PORT, flush=True)
    server.serve_forever()
