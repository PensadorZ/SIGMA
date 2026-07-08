# =============================================================================
# webhook_receiver.py — Servidor FastAPI para HITL vía Zulip
# SIGMA v1.6 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# ---------------------------------------------------------------------------
# changelog:
#   - version: 2.2.0
#     fecha: 2026-07-06
#     cambio: >
#       Detección de saludos casuales ampliada a español e inglés
#       (hola/hi, buenos días/good morning, etc.). El bot responde en el
#       mismo idioma detectado, con la fecha del día, sin intentar
#       interpretar el saludo como respuesta HITL.
#     razon: >
#       Antes de este cambio, cualquier saludo caía en "respuesta ambigua"
#       sin ninguna reacción visible — daba la impresión de que el bot no
#       funcionaba. Se limitó deliberadamente a un diccionario de palabras
#       clave (sin LLM) para no sobre-construir en el cierre del Hito 1;
#       la conversación libre bilingüe vía Ollama queda pospuesta para el
#       Director del Hito 2, donde pertenece ese tipo de razonamiento abierto.
#   - version: 2.1.1
#     fecha: 2026-07-06
#     cambio: >
#       Validación de remitente cambiada de sender_email a sender_id.
#     razon: >
#       Zulip entrega sender_email enmascarado (formato userNNNNN@dominio)
#       según su configuración de privacidad (email_address_visibility),
#       sin relación con el correo real configurado en ZULIP_EMAIL.
#       sender_id es estable y siempre visible en el payload — confirmado
#       con una prueba real de DM en esta sesión.
#   - version: 2.1.0
#     fecha: 2026-07-06
#     cambio: >
#       Validación cambiada de stream/topic a type="private" (DM).
#     razon: >
#       Documentación oficial de Zulip confirma que un Outgoing webhook
#       solo se dispara por @-mención o mensaje directo — nunca por un
#       mensaje plano en un stream/topic, aunque el bot esté suscrito.
#   - version: 2.0.0
#     fecha: 2026-07-05
#     cambio: >
#       Reemplazo de clave global de Redis por get_waiting_trace_id()
#       aislado por corrida, vía core.checkpointer.
#     razon: >
#       La v1.0.0 usaba una clave "hitl_decision" global sin trace_id,
#       nunca limpiada tras leerla — una corrida futura podía leer la
#       aprobación de una corrida anterior sin haber esperado nada.
# ---------------------------------------------------------------------------
# Canal: Sigma-Approval
# Bot: chismosito2 (Outgoing webhook)
# =============================================================================

from __future__ import annotations

import logging
import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from sigma.hooks.zulip_notifier import parse_hitl_response
from sigma.core.checkpointer import get_waiting_trace_id, resume_pipeline


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
# Saludos casuales bilingües — respuesta amistosa, sin tocar el pipeline
# ---------------------------------------------------------------------------

GREETING_KEYWORDS_ES = [
    "hola", "cómo estás", "como estas", "cómo esta", "como esta",
    "buen dia", "buen día", "buenos dias", "buenos días",
    "buenas tardes", "buenas noches", "buenas",
    "epa", "saludos", "que tal", "qué tal",
]

GREETING_KEYWORDS_EN = [
    "hi", "hello", "hey", "how are you", "how's it going",
    "good morning", "good afternoon", "good evening",
    "greetings", "what's up", "whats up",
]

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _es_saludo(text: str) -> bool:
    normalized = text.strip().lower()
    return any(kw in normalized for kw in GREETING_KEYWORDS_ES + GREETING_KEYWORDS_EN)


def _es_ingles(text: str) -> bool:
    normalized = text.strip().lower()
    return any(kw in normalized for kw in GREETING_KEYWORDS_EN)


def _fecha_hoy_es() -> str:
    now = datetime.now()
    return f"{now.day} de {MESES_ES[now.month]} de {now.year}"


def _respuesta_saludo(en_ingles: bool) -> str:
    fecha = _fecha_hoy_es()
    if en_ingles:
        return f"Hi, how's it going? Today is a beautiful day, {fecha}."
    return f"Hola, ¿Qué tal? Hoy es un lindo día {fecha}."


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
        msg_type = message.get("type", "")

        # ── Validación de canal: solo DM dispara el flujo HITL ──────────
        if msg_type != "private":
            logger.warning(
                f"Mensaje ignorado: type='{msg_type}' (se esperaba 'private', "
                f"la respuesta HITL debe llegar por DM al bot)"
            )
            return JSONResponse({"status": "ignored", "reason": "not_a_direct_message"})

        # ── Validación de remitente: solo el operador autorizado ────────
        # sender_id es estable; sender_email puede llegar enmascarado
        # por Zulip según su configuración de privacidad.
        sender_id = message.get("sender_id")
        expected_owner_id = os.getenv("ZULIP_OWNER_USER_ID", "")

        if expected_owner_id and str(sender_id) != str(expected_owner_id):
            logger.warning(
                f"DM ignorado: sender_id '{sender_id}' no coincide con "
                f"ZULIP_OWNER_USER_ID configurado ('{expected_owner_id}')."
            )
            return JSONResponse({"status": "ignored", "reason": "sender_not_authorized"})

        # ── Saludo casual (ES/EN): respuesta amistosa, no se toca el pipeline
        if _es_saludo(content):
            respuesta = _respuesta_saludo(en_ingles=_es_ingles(content))
            logger.info(f"[saludo] '{content}' → respondiendo saludo")
            return JSONResponse({"content": respuesta})

        # ── Interpretación como respuesta HITL (sí/no) ──────────────────
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


# ---------------------------------------------------------------------------
# Healthcheck (para ngrok o servicios de monitoreo)
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "service": "sigma-hito1-webhook", "version": "2.2.0"}