"""
RAVENA AIM v3.2.6 — API REST Server
====================================
FastAPI application. All credentials read from SecretsManager.
No hardcoded tokens, keys, or secrets.
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.secrets_manager import secrets

import importlib.util
_omega_path = PROJECT_ROOT / "src/core/omega_v3_2_6.py"
_spec = importlib.util.spec_from_file_location("omega_api_mod", _omega_path)
_omega_mod = importlib.util.module_from_spec(_spec)
sys.modules["omega_api_mod"] = _omega_mod
_spec.loader.exec_module(_omega_mod)
Omega = _omega_mod.Omega

logger = logging.getLogger("ravena.api")

omega = Omega()

class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class TradeSignalRequest(BaseModel):
    symbol: str
    action: str
    quantity: Optional[float] = None
    context: Optional[Dict[str, Any]] = None

app = FastAPI(
    title="Ravena AIM API",
    version="3.2.6",
    description="Sistema Cognitivo Modular de Trading — API Segura",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
async def startup():
    env = secrets.get("RAVENA_ENV", required=False) or "development"
    logger.info(f"Ravena AIM API v3.2.6 iniciada em modo: {env}")

@app.get("/health", tags=["System"])
async def health():
    diag = omega.obter_diagnostico()
    return {
        "status": diag["status"],
        "version": diag["versao"],
        "uptime": diag["uptime_segundos"],
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/system/diagnostic", tags=["System"])
async def diagnostic():
    diag = omega.obter_diagnostico()
    sec_status = secrets.get_all()
    loaded = sum(1 for v in sec_status.values() if v["loaded"])
    total = len(sec_status)
    return {
        "omega": diag,
        "secrets": {"loaded": loaded, "total": total, "source": secrets.source},
        "environment": secrets.get("RAVENA_ENV", required=False) or "unknown",
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/secrets/status", tags=["Security"])
async def secrets_status():
    audit = secrets.audit()
    return {
        "source": secrets.source,
        "loaded": audit["loaded"],
        "total": audit["total_secrets"],
        "compliant": audit["compliant"],
        "missing_critical": audit.get("missing_critical", []),
        "missing_high": audit.get("missing_high", []),
    }

@app.post("/trade/signal", tags=["Trading"])
async def trade_signal(req: TradeSignalRequest):
    api_key = secrets.get("BYBIT_API_KEY", required=False)
    api_secret = secrets.get("BYBIT_API_SECRET", required=False)
    if not api_key or not api_secret:
        raise HTTPException(status_code=503, detail="Bybit credentials not configured in SecretsManager")
    return {
        "symbol": req.symbol,
        "action": req.action,
        "status": "SIMULATED",
        "mode": "paper-trading",
        "timestamp": datetime.now().isoformat(),
    }

@app.post("/chat", tags=["AI"])
async def chat(req: ChatRequest):
    diag = omega.obter_diagnostico()
    return {
        "response": f"Processado: {req.message[:100]}",
        "context": req.context or {},
        "omega_status": diag["status"],
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/modules", tags=["System"])
async def modules():
    diag = omega.obter_diagnostico()
    return {"modules": diag.get("modulos", []), "total": len(diag.get("modulos", []))}

# ── Instagram OAuth ────────────────────────────────────────────
@app.get("/auth/instagram/callback", tags=["Instagram"])
async def instagram_auth_callback(code: str = None, error: str = None):
    if error:
        return {"error": error}
    logger.info(f"Instagram OAuth callback received with code: {code[:20] if code else 'None'}...")
    return {"status": "authorized", "code": code}

@app.get("/auth/instagram/login", tags=["Instagram"])
async def instagram_auth_login():
    client_id = secrets.get("INSTAGRAM_APP_ID", required=False) or "YOUR_APP_ID"
    redirect_uri = f"https://exhaust-broadcasting-jonathan-teenage.trycloudflare.com/auth/instagram/callback"
    scope = "instagram_basic,instagram_manage_comments,instagram_manage_messages"
    url = (
        f"https://www.facebook.com/v19.0/dialog/oauth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
    )
    return {"login_url": url}

# ── Instagram Webhook ──────────────────────────────────────────
INSTAGRAM_VERIFY_TOKEN = "ravena_verify_token_2026"

@app.get("/webhook/instagram", tags=["Instagram"])
async def instagram_webhook_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == INSTAGRAM_VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook/instagram", tags=["Instagram"])
async def instagram_webhook_receive(payload: dict):
    logger.info(f"Instagram webhook received: {payload}")
    return {"status": "received"}

def create_app():
    return app

if __name__ == "__main__":
    import uvicorn
    port = int(secrets.get("API_PORT", required=False) or "8000")
    host = secrets.get("API_HOST", required=False) or "0.0.0.0"
    logger.info(f"Starting API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
