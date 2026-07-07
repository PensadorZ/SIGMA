# =============================================================================
# webhook_receiver.py — Servidor FastAPI para HITL vía Zulip
# SIGMA v1.6 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 2.1.0
#
# Canal: Sigma-Approval
# Topic: hitl-approvals (ZULIP_TOPIC_HITL)
# Bot: sigma-hito1-bot
# =============================================================================
# NOTA v2.1.0 — CORRECCIÓN de un supuesto incorrecto de la v2.0.0:
#
# Se verificó contra la documentación oficial de Zulip que un Outgoing
# Webhook NUNCA se dispara por el simple hecho de escribir en un stream
# o topic, sin importar cuál. Solo se dispara en dos casos:
#   1. @-mención del bot dentro de un canal.
#   2. Mensaje directo (DM) enviado al bot.
#
# La v2.0.0 validaba `stream == expected_stream`, lo cual habría
# funcionado SOLO si además se mencionaba al bot — pero el flujo real
# probado (escribir "sí" en el topic hitl-approvals) nunca habría
# disparado el webhook en absoluto.
#
# Se decide usar DM como canal de respuesta (más simple, sin necesidad
# de recordar la sintaxis @mención cada vez). Se valida el remitente
# contra ZULIP_EMAIL para que solo el operador autorizado pueda
# aprobar/rechazar — cualquier otro DM al bot se ignora.
# =============================================================================

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from hooks.zulip_notifier import parse_hitl_response
from core.checkpointer import get_waiting_trace_id, resume_pipeline


def _get_build_graph_fn():
    from orchestrator import build_graph
    return build_graph


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sigma.webhook")

app = FastAPI(title="SIGMA HITL Webhook")


@app.post("/webhook/zulip")
async def handle_zulip_webhook(request: Request):
    payload = await request.json()
    logger.info(f"📩 Webhook recibido: {payload}")

    try:
        message = payload.get("message", {})
        content = message.get("content", "").strip()
        message_type = message.get("type", "")

        # ── Validación de canal: solo DM al bot dispara HITL ────────────
        if message_type != "private":
            logger.info(
                f"Mensaje ignorado (type='{message_type}', no es DM). "
                f"Las respuestas HITL deben enviarse como mensaje directo al bot."
            )
            return JSONResponse({"status": "ignored", "reason": "not_a_direct_message"})

        # ── Validación de remitente: solo el operador autorizado ────────
        sender_email = message.get("sender_email", "")
        expected_sender = os.getenv("ZULIP_EMAIL", "")

        if expected_sender and sender_email != expected_sender:
            logger.warning(
                f"DM ignorado: remitente '{sender_email}' no coincide con "
                f"ZULIP_EMAIL configurado ('{expected_sender}')."
            )
            return JSONResponse({"status": "ignored", "reason": "sender_not_authorized"})

        # Interpretamos la respuesta en lenguaje natural — sin cambios
        # respecto a versiones anteriores, esta parte ya funcionaba correctamente.
        decision = parse_hitl_response(content)

        if decision is None:
            logger.warning(f"⚠️ Respuesta AMBIGUA: '{content}'. No se toma acción.")
            return JSONResponse({"status": "ambiguous", "parsed": None})

        # ── Identificar QUÉ corrida está esperando ──────────────────────
        trace_id = get_waiting_trace_id()
        if trace_id is None:
            logger.warning(
                "No hay ninguna corrida marcada como en espera HITL. "
                "¿Respondiste dos veces, o la corrida ya se resolvió?"
            )
            return JSONResponse({
                "status": "no_pending_run",
                "detail": "No hay ninguna pausa HITL activa para reanudar.",
            })

        # ── Reanudar el grafo específico de ese trace_id ────────────────
        build_graph_fn = _get_build_graph_fn()
        result = resume_pipeline(build_graph_fn, trace_id, decision)

        if "__interrupt__" in result:
            logger.info(f"Pipeline {trace_id} reanudado, pero pausado de nuevo (otra pausa HITL).")
            return JSONResponse({
                "status": "resumed_but_paused_again",
                "trace_id": trace_id,
                "parsed": decision,
            })

        logger.info(
            f"{'✅' if decision else '❌'} trace_id={trace_id} reanudado con decision={decision}"
        )
        return JSONResponse({
            "status": "approved" if decision else "rejected",
            "trace_id": trace_id,
            "parsed": decision,
        })

    except Exception as e:  # noqa: BLE001
        logger.error(f"🔥 Error procesando webhook: {e}")
        return JSONResponse({"status": "error", "details": str(e)})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sigma-hito1-webhook", "version": "2.1.0"}