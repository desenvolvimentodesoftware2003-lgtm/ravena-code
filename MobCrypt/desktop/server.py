import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger("mobcrypt.server")

PAGE_HTML = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MobCrypt Desktop</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family: system-ui, sans-serif; background: #111; color: #eee;
       display: flex; justify-content: center; align-items: center;
       min-height: 100vh; padding: 20px; }
.card { background: #1e1e1e; border-radius: 16px; padding: 32px;
        max-width: 480px; width: 100%; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
h1 { font-size: 1.6rem; margin-bottom: 8px; color: #7c4dff; }
p { color: #aaa; margin-bottom: 20px; font-size: 0.9rem; }
input, button { width: 100%; padding: 14px 16px; border: none; border-radius: 10px;
                font-size: 1rem; outline: none; }
input { background: #2a2a2a; color: #fff; margin-bottom: 12px; }
input::placeholder { color: #666; }
button { background: #7c4dff; color: #fff; font-weight: 600; cursor: pointer;
         transition: background 0.2s; }
button:hover { background: #651fff; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
#status { margin-top: 16px; padding: 12px; border-radius: 8px; display: none; }
.success { background: #1b5e20; color: #a5d6a7; }
.error { background: #b71c1c; color: #ef9a9a; }
.footer { margin-top: 16px; font-size: 0.75rem; color: #555; text-align: center; }
</style>
</head>
<body>
<div class="card">
  <h1>MobCrypt</h1>
  <p>Cole a URL do QR code escaneado e envie para o PC</p>
  <input type="url" id="urlInput" placeholder="https://exemplo.com/auth/qr...">
  <button id="sendBtn" onclick="send()">Enviar via Tor</button>
  <div id="status"></div>
  <div class="footer">Delay aleatório + Tor NEWNYM antes de abrir</div>
</div>
<script>
function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.textContent = msg; el.className = type; el.style.display = 'block';
}
async function send() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { showStatus('Cole uma URL primeiro', 'error'); return; }
  const btn = document.getElementById('sendBtn');
  btn.disabled = true; showStatus('Enviando...', 'success');
  try {
    const r = await fetch('/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const d = await r.json();
    if (r.ok) showStatus('Recebido! Aguardando delay aleatório...', 'success');
    else showStatus('Erro: ' + (d.error || r.status), 'error');
    document.getElementById('urlInput').value = '';
  } catch(e) {
    showStatus('Erro de conexao: ' + e.message, 'error');
  }
  btn.disabled = false;
}
</script>
</body>
</html>"""


class ScanHandler(BaseHTTPRequestHandler):
    server_ref: "MobCryptServer | None" = None

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
            url = data.get("url", "")
            if not url:
                self._respond(400, {"error": "url is required"})
                return

            logger.info("QR recebido: %s", url)
            if self.server_ref:
                self.server_ref.on_scan(url)

            self._respond(200, {"status": "received"})
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid json"})

    def do_GET(self):
        if self.path == "/":
            html = PAGE_HTML
            body = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._respond(200, {
            "status": "running",
            "message": "MobCrypt Desktop - POST /scan com {\"url\": \"...\"}",
        })

    def _respond(self, code: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        logger.debug("HTTP: %s", fmt % args)


class MobCryptServer:
    def __init__(self, host: str, port: int, callback):
        self.host = host
        self.port = port
        self.callback = callback
        ScanHandler.server_ref = self
        self.httpd = HTTPServer((host, port), ScanHandler)

    def on_scan(self, url: str):
        self.callback(url)

    def start(self):
        logger.info("Servidor HTTP em http://%s:%s", self.host, self.port)
        self.httpd.serve_forever()

    def stop(self):
        self.httpd.shutdown()
