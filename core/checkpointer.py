# =============================================================================
# core/checkpointer.py — Checkpointer compartido para HITL real
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Resuelve el problema real encontrado en la propuesta del Asistente
# Secundario: un `while True: time.sleep(5)` bloquea el proceso completo
# de Python durante la espera HITL, y no sobrevive si el proceso muere.
#
# Este módulo usa el mecanismo NATIVO de LangGraph: interrupt() + un
# checkpointer persistente (SQLite). Verificado en este sandbox con dos
# procesos Python separados: el proceso que pausa el grafo puede morir
# por completo, y un proceso nuevo (webhook_receiver.py) reanuda desde
# el archivo .sqlite en disco sin ninguna memoria compartida en RAM.
#
# orchestrator.py y webhook_receiver.py DEBEN usar exactamente el mismo
# archivo de checkpoint y la misma función build_graph() — por eso viven
# aquí, en un módulo compartido, no duplicados en cada script.
# =============================================================================

from __future__ import annotations

import logging
import os
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

log = logging.getLogger("sigma.checkpointer")

# Ruta del archivo de checkpoint — un solo archivo, compartido entre
# el proceso que arranca el pipeline y el proceso que lo reanuda.
CHECKPOINT_DB_PATH = os.environ.get(
    "SIGMA_CHECKPOINT_DB", str(Path(__file__).parent.parent / "sigma_checkpoints.sqlite")
)

# Redis: puntero al trace_id que está actualmente en pausa esperando
# respuesta humana. NOTA DE ALCANCE: SIGMA opera con un único operador
# y una corrida a la vez en el Hito 1 — este puntero simple es correcto
# para ese caso. Si en el futuro corren varias pipelines HITL en
# paralelo, esto debe evolucionar a una cola o a extraer el trace_id
# directamente del mensaje de Zulip (ya viaja en el texto de la
# pregunta, ver zulip_notifier.request_hitl_confirmation).
REDIS_HITL_WAITING_KEY = "sigma:hitl:waiting_trace_id"


def get_checkpointer():
    """
    Devuelve el checkpointer SQLite compartido. Usar dentro de un
    context manager (`with get_checkpointer() as cp:`) tanto en
    orchestrator.py como en webhook_receiver.py.
    """
    return SqliteSaver.from_conn_string(CHECKPOINT_DB_PATH)


def mark_waiting(trace_id: str) -> None:
    """
    Registra en Redis que trace_id es la corrida actualmente pausada
    esperando decisión humana. Llamado por orchestrator.py justo antes
    de que el grafo se pause en node_hitl_wait.
    """
    from skills._common import get_redis_connection

    try:
        r = get_redis_connection()
        r.set(REDIS_HITL_WAITING_KEY, trace_id)
        log.info("[checkpointer] Marcado trace_id=%s como en espera HITL", trace_id)
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "[checkpointer] No se pudo marcar en Redis (trace_id=%s): %s. "
            "El webhook no podrá auto-descubrir qué corrida reanudar.",
            trace_id, exc,
        )


def get_waiting_trace_id() -> str | None:
    """
    Lee de Redis cuál trace_id está actualmente en pausa. Usado por
    webhook_receiver.py al recibir una respuesta de Zulip, para saber
    qué corrida reanudar.
    """
    from skills._common import get_redis_connection

    r = get_redis_connection()
    value = r.get(REDIS_HITL_WAITING_KEY)
    if value is None:
        return None
    return value.decode() if isinstance(value, bytes) else value


def clear_waiting(trace_id: str) -> None:
    """
    Limpia el puntero de Redis tras reanudar — evita el bug real
    encontrado en la propuesta original, donde la clave nunca se
    borraba y contaminaba la siguiente corrida.
    """
    from skills._common import get_redis_connection

    r = get_redis_connection()
    current = get_waiting_trace_id()
    if current == trace_id:
        r.delete(REDIS_HITL_WAITING_KEY)
        log.info("[checkpointer] Puntero de espera HITL limpiado para trace_id=%s", trace_id)


def resume_pipeline(build_graph_fn, trace_id: str, decision: bool) -> dict:
    """
    Reanuda una corrida pausada. Diseñada para ser llamada desde un
    proceso completamente distinto al que la pausó (webhook_receiver.py).

    Args:
        build_graph_fn: la función build_graph() de orchestrator.py,
                         pasada como parámetro para evitar import circular
                         (orchestrator.py importa este módulo; este módulo
                         no debe importar orchestrator.py de vuelta).
        trace_id:        identifica qué corrida reanudar (= thread_id).
        decision:        True (aprobar) / False (rechazar), ya parseado
                          por parse_hitl_response() antes de llegar aquí.

    Returns:
        El estado final del grafo tras reanudar (puede incluir un nuevo
        __interrupt__ si hubiera más de una pausa HITL en el pipeline).
    """
    with get_checkpointer() as checkpointer:
        graph = build_graph_fn(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": trace_id}}
        log.info("[checkpointer] Reanudando trace_id=%s con decision=%s", trace_id, decision)

        # Guarda defensiva: decision debe ser un bool ya parseado.
        # Pasar None a Command(resume=...) rompe LangGraph internamente
        # con un error confuso (UnboundLocalError) — se detecta aquí
        # con un mensaje claro antes de llegar a ese punto.
        if decision is None:
            raise ValueError(
                "resume_pipeline() recibió decision=None. El llamador debe "
                "filtrar respuestas ambiguas de parse_hitl_response() ANTES "
                "de llamar aquí — ver webhook_receiver.py, que ya hace esa "
                "verificación correctamente."
            )

        result = graph.invoke(Command(resume=decision), config=config)
        clear_waiting(trace_id)
        return result
