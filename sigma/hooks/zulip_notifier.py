# =============================================================================
# hooks/zulip_notifier.py — Notificaciones HITL vía Zulip
# SIGMA v1.6 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# ---------------------------------------------------------------------------
# changelog:
#   - version: 1.1.0
#     fecha: 2026-07-06
#     cambio: >
#       request_hitl_confirmation() ahora instruye responder por mensaje
#       directo (DM) al bot, no en el topic del stream.
#     razon: >
#       La documentación oficial de Zulip confirma que un Outgoing webhook
#       solo se dispara con @-mención al bot o mensaje directo — nunca con
#       un mensaje plano en el topic, aunque el bot esté suscrito al stream.
#       Responder en el topic simplemente no activaba nada.
#   - version: 1.0.0
#     fecha: 2026-07-04
#     cambio: "Versión inicial. parse_hitl_response() con soporte ES/EN."
# =============================================================================
# Implementa las dos funciones que el orquestador importa:
#   notify_hitl()        → alerta puntual durante el pipeline
#   notify_pipeline_end() → resumen al cierre del pipeline
#
# Las credenciales se obtienen exclusivamente de variables de entorno (ADR-010).
# Si Zulip no está configurado, las notificaciones se degradan a log local
# sin interrumpir el pipeline (modo silencioso).
# =============================================================================

from __future__ import annotations

import logging
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("sigma.zulip_notifier")

ZULIP_BOT_EMAIL: Optional[str] = os.getenv("ZULIP_BOT_EMAIL")
ZULIP_BOT_API_KEY: Optional[str] = os.getenv("ZULIP_BOT_API_KEY")
ZULIP_SITE: Optional[str] = os.getenv("ZULIP_SITE")
ZULIP_STREAM: str = os.getenv("ZULIP_STREAM", "sigma-hito1")
ZULIP_TOPIC: str = os.getenv("ZULIP_TOPIC", "pipeline-events")

_ZULIP_ENABLED: bool = all([ZULIP_BOT_EMAIL, ZULIP_BOT_API_KEY, ZULIP_SITE])

if not _ZULIP_ENABLED:
    log.warning(
        "[zulip] Variables ZULIP_BOT_EMAIL / ZULIP_BOT_API_KEY / ZULIP_SITE "
        "no configuradas. Las notificaciones se registrarán solo en log local."
    )


def _send(message: str) -> bool:
    """
    Envía un mensaje al stream y topic configurados en Zulip.

    Returns:
        True si el envío fue exitoso, False si falló (no relanza excepción).
    """
    if not _ZULIP_ENABLED:
        log.info("[zulip:silencioso] %s", message)
        return False

    url = f"https://{ZULIP_SITE}/api/v1/messages"
    payload = {
        "type": "stream",
        "to": ZULIP_STREAM,
        "topic": ZULIP_TOPIC,
        "content": message,
    }

    try:
        response = requests.post(
            url,
            auth=(ZULIP_BOT_EMAIL, ZULIP_BOT_API_KEY),
            data=payload,
            timeout=10,
        )
        if response.status_code == 200:
            log.info("[zulip] Mensaje enviado OK → stream=%s topic=%s",
                     ZULIP_STREAM, ZULIP_TOPIC)
            return True
        else:
            log.warning("[zulip] Respuesta inesperada: %d — %s",
                        response.status_code, response.text[:200])
            return False

    except requests.exceptions.Timeout:
        log.warning("[zulip] Timeout al enviar notificación. Pipeline continúa.")
        return False
    except requests.exceptions.ConnectionError as exc:
        log.warning("[zulip] Error de conexión: %s. Pipeline continúa.", exc)
        return False
    except Exception as exc:  # noqa: BLE001
        log.warning("[zulip] Error inesperado: %s. Pipeline continúa.", exc)
        return False


def notify_hitl(message: str) -> None:
    """
    Envía una alerta puntual de Human-in-the-Loop a Zulip.

    Usada por el orquestador en dos casos:
    - pct_unclear > 30% en skill 0008-sentiment-analyzer.
    - Pipeline fallido (HANDLE_ERROR node).

    No lanza excepciones. Si Zulip no está disponible, el mensaje
    queda registrado en el log local y el pipeline continúa.

    Args:
        message: Texto de la alerta. Puede incluir emojis y saltos de línea.
    """
    log.info("[hitl] Enviando alerta HITL a Zulip")
    _send(message)


def notify_pipeline_end(
    success: bool,
    trace_id: str,
    dashboard_url: Optional[str] = None,
    warnings: Optional[list[str]] = None,
) -> None:
    """
    Envía el resumen de cierre del pipeline a Zulip.

    Llamada por el nodo `node_end` (éxito) o `node_handle_error` (fallo).

    Args:
        success:       True si el pipeline cerró exitosamente.
        trace_id:      ID de trazabilidad del run.
        dashboard_url: URL del dashboard generado (solo si success=True).
        warnings:      Lista de advertencias acumuladas durante el run.
    """
    warnings = warnings or []

    if success:
        warnings_section = (
            f"\n⚠️ Advertencias acumuladas:\n" +
            "\n".join(f"  • {w}" for w in warnings)
            if warnings else "\n✅ Sin advertencias."
        )
        message = (
            f"✅ **SIGMA Hito 1 — Pipeline COMPLETADO**\n"
            f"trace_id: `{trace_id}`\n"
            f"Dashboard: {dashboard_url or 'No generado'}"
            f"{warnings_section}"
        )
    else:
        message = (
            f"🔴 **SIGMA Hito 1 — Pipeline FALLIDO**\n"
            f"trace_id: `{trace_id}`\n"
            f"Revisa los logs y Langfuse para el detalle del error."
        )

    log.info("[pipeline_end] Enviando resumen de cierre a Zulip (success=%s)", success)
    _send(message)


AFFIRMATIVE_RESPONSES: frozenset[str] = frozenset({
    "sí", "si", "s", "sip", "seee", "seeee", "seeeee",
    "claro", "dale", "va", "vale", "ok", "okay", "oki",
    "confirmo", "confirmado", "aprobado", "apruebo", "adelante",
    "correcto", "afirmativo", "procede", "procedo",
    "yes", "y", "yeah", "yep", "yup", "sure", "confirm",
    "confirmed", "approved", "go", "go ahead", "proceed",
    "+1", "1",
})

NEGATIVE_RESPONSES: frozenset[str] = frozenset({
    "no", "n", "nop", "nel", "negativo", "para", "detente",
    "cancela", "cancelar", "aborta", "abortar", "denegado",
    "rechazo", "rechazado", "incorrecto",
    "nope", "cancel", "stop", "abort", "denied", "reject", "rejected",
    "-1",
})


def parse_hitl_response(text: str) -> Optional[bool]:
    """
    Normaliza una respuesta humana en lenguaje natural a un booleano
    de aprobación HITL.

    Args:
        text: Respuesta cruda del humano tal como llega desde Zulip.

    Returns:
        True  si la respuesta es afirmativa (sí, yeah, sip, +1, etc.)
        False si la respuesta es negativa (no, nop, -1, etc.)
        None  si la respuesta es ambigua o no reconocida — el orquestador
              debe re-preguntar en lugar de asumir una interpretación.
    """
    normalized = text.strip().lower()
    normalized = normalized.strip("¡!¿?., ")

    if normalized in AFFIRMATIVE_RESPONSES:
        log.info("[hitl_parse] '%s' → True", text)
        return True

    if normalized in NEGATIVE_RESPONSES:
        log.info("[hitl_parse] '%s' → False", text)
        return False

    log.warning("[hitl_parse] Respuesta ambigua: '%s' → None (re-preguntar)", text)
    return None


def request_hitl_confirmation(question: str) -> None:
    """
    Envía una pregunta HITL a Zulip que espera respuesta por mensaje
    directo (DM) al bot — no en el topic del stream. El webhook_receiver.py
    detecta el DM entrante y lo pasa por parse_hitl_response() antes de
    reanudar el pipeline.

    Args:
        question: Pregunta a formular. Se recomienda ser explícito sobre
                  qué constituye una respuesta afirmativa o negativa,
                  aunque el parser acepta variantes coloquiales.
    """
    message = (
        f"❓ **SIGMA — Confirmación requerida**\n"
        f"{question}\n\n"
        f"_Responde por **mensaje directo (DM)** a este bot — no aquí en el topic._\n"
        f"_Lenguaje natural: sí/no, yeah/nop, sip/nel, o +1/-1 si prefieres el esquema anterior._"
    )
    log.info("[hitl] Solicitando confirmación HITL vía Zulip (respuesta esperada por DM)")
    _send(message)