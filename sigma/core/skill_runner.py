# =============================================================================
# sigma/core/skill_runner.py
# SIGMA v1.5 · Hito 2, Rollout 1 (cerrado)
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.2.0
# =============================================================================
# NOTA v1.2.0 — FIX de duration_ms (detectado al cerrar Rollout 1):
# run_skill() confiaba ciegamente en el duration_ms autorreportado por
# cada skill.py. Se detectó que 0003 y 0011 reportaban 0ms pese a que el
# reloj real (timestamps del log) mostraba 7s y 52s respectivamente — no
# se confirmó la causa exacta dentro de esos dos archivos, pero el
# defecto de arquitectura sí se corrige aquí: run_skill() ahora mide su
# propio tiempo real y lo usa como autoridad, con una advertencia si
# difiere mucho del autorreportado (señal de que ese skill.py específico
# tiene un bug en dónde abre/cierra su propio timer()).
# =============================================================================
# Extraído de orchestrator.py (Hito 1, v1.1.0) — _run_skill, _should_retry
# y _emit_langfuse vivían ahí sin ningún módulo compartido. Engineer
# Modelos y Engineer Auditor (Rollout 2 y 3) van a necesitar exactamente
# la misma lógica de circuit breaker — extraído aquí para no duplicarla
# tres veces.
#
# NOTA v1.1.0 — CORRECCIÓN REAL, no solo extracción (decidida en la misma
# sesión que la extracción, a petición explícita de Marx):
# La versión de orchestrator.py v1.1.0 instanciaba su propio cliente
# Langfuse con os.environ["LANGFUSE_PUBLIC_KEY"] (acceso directo, sin
# default) — si esas variables faltaban en .env, el módulo entero fallaba
# al importarse, ANTES de que el pipeline pudiera siquiera intentar
# degradar. Esto contradice la premisa central de ADR-011 (degradación
# elegante Langfuse→Redis→log local, que sigma/core/tracing.py sí
# implementa correctamente con get_optional_env, sin crashear nunca).
# Se reemplaza el cliente Langfuse directo por tracing.emit_trace_event(),
# preservando la firma externa emit_langfuse(trace_id, event_name, fields)
# para no tener que tocar engineer_datos.py ni ningún llamador existente.
# =============================================================================

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from sigma.core.pipeline_state import (
    BACKOFF_BASE_SECONDS,
    MAX_RETRIES,
    PipelineState,
    SkillResult,
    classify_error,
)
from sigma.core.tracing import emit_trace_event

log = logging.getLogger("sigma.skill_runner")


def _should_retry(state: PipelineState, skill_id: str, error_type: str) -> bool:
    """
    Determina si el circuit breaker debe reintentar el skill o fallar rápido.

    Reglas (Decisión B, aprobada 2026-06-30, sin cambios en esta extracción):
    - Error no recuperable → False inmediato (sin reintentos).
    - Error desconocido    → False (fallo rápido, se notifica a Gemini).
    - Error recuperable    → True si retries < MAX_RETRIES, False si agotó.
    """
    category = classify_error(error_type)

    if category in ("non_recoverable", "unknown"):
        log.warning(
            "[circuit_breaker] skill=%s error=%s category=%s → fallo rápido",
            skill_id, error_type, category,
        )
        return False

    retries_so_far = state["retry_counts"].get(skill_id, 0)
    if retries_so_far >= MAX_RETRIES:
        log.warning(
            "[circuit_breaker] skill=%s agotó reintentos (%d/%d) → fallo",
            skill_id, retries_so_far, MAX_RETRIES,
        )
        return False

    wait = BACKOFF_BASE_SECONDS * (retries_so_far + 1)
    log.info(
        "[circuit_breaker] skill=%s reintento %d/%d en %.0fs",
        skill_id, retries_so_far + 1, MAX_RETRIES, wait,
    )
    time.sleep(wait)
    return True


def emit_langfuse(trace_id: str, event_name: str, fields: dict[str, Any]) -> None:
    """
    Emite un evento de trazabilidad con degradación elegante real
    (Langfuse → Redis → log local, ADR-011) vía sigma.core.tracing.
    Nunca lanza excepción — tracing.py ya garantiza eso internamente.

    Firma preservada idéntica a la versión anterior (trace_id, event_name,
    fields) para no romper a ningún llamador existente (engineer_datos.py).
    """
    backend_used = emit_trace_event(event_name, trace_id, **fields)
    log.debug("[tracing] evento '%s' procesado por backend=%s", event_name, backend_used)




def run_skill(skill_id: str, skill_fn: Any, state: PipelineState) -> PipelineState:
    """
    Ejecutor genérico de skills con circuit breaker integrado.
    Cada nodo del grafo (de cualquier Engineer) llama a esta función
    pasando su skill_fn.

    CORREGIDO (Hito 2): antes confiaba ciegamente en el duration_ms que
    cada skill.py autorreportaba desde su propio timer() — se detectó
    que ese valor venía sistemáticamente en 0ms para 0003 y 0011 pese a
    que el reloj real (comparando timestamps del log) mostraba 7s y 52s
    respectivamente. No se pudo confirmar la causa exacta dentro de esos
    dos skill.py sin verlos de nuevo, pero el defecto de arquitectura sí
    es corregible aquí: skill_runner.py ahora mide su PROPIO tiempo real
    alrededor de la llamada, y ese valor sobrescribe el autorreportado —
    nunca se vuelve a confiar en una medición que otro componente puede
    haber calculado mal, cuando este módulo puede medirla directamente.
    """
    log.info("[pipeline] ▶ Iniciando skill %s", skill_id)
    emit_langfuse(state["trace_id"], f"{skill_id}.node_start", {
        "skill_id": skill_id,
        "sigma_variant": state["sigma_variant"],
    })

    attempt = 0
    result: Optional[SkillResult] = None

    while True:
        attempt += 1
        t0 = time.monotonic()

        try:
            result = skill_fn(state)
        except Exception as exc:  # noqa: BLE001
            error_type = type(exc).__name__
            result = SkillResult(
                skill_id=skill_id,
                status="error",
                output={},
                error_type=error_type,
                error_detail=str(exc),
                error_category="unknown",
                duration_ms=0,  # se sobrescribe abajo con la medición real
                retries_attempted=attempt - 1,
            )
            log.exception("[pipeline] Excepción inesperada en skill %s", skill_id)

        real_duration_ms = int((time.monotonic() - t0) * 1000)
        self_reported_ms = result.get("duration_ms", 0)
        if abs(real_duration_ms - self_reported_ms) > 500:
            log.warning(
                "[skill_runner] skill=%s duration_ms autorreportado (%dms) "
                "difiere del reloj real (%dms) — usando el real. Revisar "
                "dónde empieza/termina timer() dentro de ese skill.py.",
                skill_id, self_reported_ms, real_duration_ms,
            )
        result["duration_ms"] = real_duration_ms

        if result["status"] in ("success", "success_with_warnings"):
            log.info(
                "[pipeline] ✓ Skill %s completado en %dms (status=%s)",
                skill_id, result["duration_ms"], result["status"],
            )
            if result["status"] == "success_with_warnings":
                for w in result["output"].get("warnings", []):
                    state["warnings"].append(f"{skill_id}:{w}")

            state["outputs"][skill_id] = result
            state["current_skill"] = skill_id
            emit_langfuse(state["trace_id"], f"{skill_id}.node_end", {
                "status": result["status"],
                "duration_ms": result["duration_ms"],
            })
            return state

        error_type = result.get("error_type", "UnknownError")
        log.error(
            "[pipeline] ✗ Skill %s falló: %s — %s",
            skill_id, error_type, result.get("error_detail", ""),
        )

        if _should_retry(state, skill_id, error_type):
            state["retry_counts"][skill_id] = attempt
            continue

        result["retries_attempted"] = attempt - 1
        result["error_category"] = classify_error(error_type)
        state["outputs"][skill_id] = result
        state["failed_skill_id"] = skill_id
        state["pipeline_status"] = "failed"
        emit_langfuse(state["trace_id"], f"{skill_id}.node_error", {
            "error_type": error_type,
            "error_category": result["error_category"],
            "retries_attempted": result["retries_attempted"],
        })
        return state
