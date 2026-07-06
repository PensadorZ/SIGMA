# =============================================================================
# webhook_receiver.py — Servidor FastAPI para HITL vía Zulip
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.0.0

# Canal: Sigma-Approval
# Topic: hitl-approvals
# Bot: sigma-hito1-bot
# =============================================================================

import os
import logging
import redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from hooks.zulip_notifier import parse_hitl_response

load_dotenv()

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sigma.webhook")

# Conexión a Redis (para comunicarle la decisión al orquestador)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
r = redis.Redis.from_url(REDIS_URL)

app = FastAPI(title="SIGMA HITL Webhook")

# ---------------------------------------------------------------------------
# Endpoint principal: Zulip Outgoing Webhook (POST)
# ---------------------------------------------------------------------------
@app.post("/webhook/zulip")
async def handle_zulip_webhook(request: Request):
    payload = await request.json()
    logger.info(f"📩 Webhook recibido: {payload}")

    try:
        message = payload.get("message", {})
        content = message.get("content", "").strip()
        stream = message.get("stream", "").strip()
        topic = message.get("topic", "").strip()
        sender = message.get("sender_email", "")

        # Filtramos solo mensajes del stream y topic correctos
        expected_stream = os.getenv("ZULIP_STREAM", "Sigma-Approval")
        expected_topic = os.getenv("ZULIP_TOPIC", "hitl-approvals")

        if stream != expected_stream:
            logger.warning(f"Stream ignorado: '{stream}' (esperaba '{expected_stream}')")
            return JSONResponse({"status": "ignored", "reason": "stream mismatch"})

        # 🧠 Interpretamos la respuesta con lenguaje natural
        decision = parse_hitl_response(content)

        if decision is True:
            logger.info(f"✅ Decisión AFIRMATIVA detectada: '{content}'")
            r.set("hitl_decision", "approve")   # Señal para el orquestador
            return JSONResponse({"status": "approved", "parsed": True})

        elif decision is False:
            logger.info(f"❌ Decisión NEGATIVA detectada: '{content}'")
            r.set("hitl_decision", "reject")    # Señal para el orquestador
            return JSONResponse({"status": "rejected", "parsed": False})

        else:
            logger.warning(f"⚠️ Respuesta AMBIGUA: '{content}'. No se toma acción.")
            return JSONResponse({"status": "ambiguous", "parsed": None})

    except Exception as e:
        logger.error(f"🔥 Error procesando webhook: {e}")
        return JSONResponse({"status": "error", "details": str(e)})

# ---------------------------------------------------------------------------
# Healthcheck (para Expose o Ngrok)
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "sigma-hito1-webhook"}