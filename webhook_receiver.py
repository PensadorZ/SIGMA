# =============================================================================
# webhook_receiver.py — Servidor FastAPI para HITL vía Zulip
# SIGMA v1.6 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 2.0.0
#
# Canal: Sigma-Approval
# Topic: hitl-approvals (ZULIP_TOPIC_HITL)
# Bot: sigma-hito1-bot
# =============================================================================
# NOTA v2.0.0 — CORRECCIÓN de un bug real de la versión 1.0.0 original:
#
# La v1.0.0 escribía `r.set("hitl_decision", "approve")` con una clave
# GLOBAL, sin trace_id, y nunca la borraba tras leerla. Eso significa
# que si alguna vez quedaba un "approve" de una corrida anterior, la
# SIGUIENTE corrida lo leería de inmediato como respuesta a su propia
# pregunta, sin haber esperado nada — y el problema se repetía en cada
# corrida futura una vez que ocurría una vez.
#
# Esta versión usa core.checkpointer.resume_pipeline(), que:
#   1. Identifica QUÉ trace_id está esperando (Redis, puntero aislado,
#      limpiado automáticamente tras reanudar — ver core/checkpointer.py).
#   2. Reanuda ESE grafo específico vía interrupt() + Command(resume=...),
#      no un flag global que cualquier corrida podría leer por error.
#
# parse_hitl_response() se sigue usando exactamente igual que en v1.0.0
# — eso ya estaba bien, no se tocó esa parte.
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
    """
    Import diferido — orchestrator.py importa módulos de skills pesados
    (transformers, sklearn) que no tiene sentido cargar solo para
    levantar el servidor; se importa recién cuando llega un webhook
    real que necesita reanudar.
    """
    from orchestrator import build_graph
    return build_graph


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sigma.webhook")

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

        # Nombres reconciliados con el .env real — ver reconciliación
        # de nombres de variable hecha en esta sesión.
        expected_stream = os.getenv("ZULIP_STREAM", "Sigma-Approval")

        if stream != expected_stream:
            logger.warning(f"Stream ignorado: '{stream}' (esperaba '{expected_stream}')")
            return JSONResponse({"status": "ignored", "reason": "stream mismatch"})

        # Interpretamos la respuesta en lenguaje natural — sin cambios
        # respecto a v1.0.0, esta parte ya funcionaba correctamente.
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
            # El pipeline tenía más de una pausa HITL — quedó pausado
            # de nuevo en el siguiente punto. No es un error.
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


# ---------------------------------------------------------------------------
# Healthcheck (para Expose o Ngrok)
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "sigma-hito1-webhook", "version": "2.0.0"}
