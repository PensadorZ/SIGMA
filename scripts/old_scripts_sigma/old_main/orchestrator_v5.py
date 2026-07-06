# =============================================================================
# orchestrator.py — Orquestador principal SIGMA Hito 1
# SIGMA v1.6 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.1.0
# =============================================================================
# NOTA v1.1.0: agrega node_hitl_wait con interrupt() + checkpointer SQLite
# real (core/checkpointer.py). Reemplaza un diseño propuesto por el
# Asistente Secundario que bloqueaba el proceso completo con
# `while True: time.sleep(5)` y perdía el estado si el proceso moría
# durante la espera. Verificado con dos procesos Python separados antes
# de integrar — ver conversación para la prueba de concepto completa.
# Implementa el grafo LangGraph que encadena los 6 skills del Hito 1:
#
#   0000-system-health-check  →  0001-data-ingestion
#   →  0002-data-cleanser     →  0003-data-preprocessor
#   →  0008-sentiment-analyzer →  0011-viz-reporter
#
# Circuit breaker con fallo rápido (Decisión B, aprobada 2026-06-30):
#   - Errores no recuperables: fallo inmediato, sin reintentos.
#   - Errores recuperables:    máximo 2 reintentos con backoff 5s.
#   - success_with_warnings:   continúa, acumula warning en estado.
#
# Gemini (supervisor LLM) solo se invoca para errores desconocidos.
# En el flujo normal su consumo de tokens es cero.
#
# Uso:
#   python orchestrator.py --variant Full --data-path ./data/tirendaz.csv
#   python orchestrator.py --variant Dev  --data-path ./data/tirendaz.csv
# =============================================================================

from __future__ import annotations

import argparse
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# LangGraph
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

# Checkpointer compartido para HITL real (interrupt + SQLite) — permite
# que orchestrator.py (quien pausa) y webhook_receiver.py (quien reanuda,
# proceso completamente separado) coordinen sin memoria compartida en RAM.
from core.checkpointer import mark_waiting

# Langfuse
from langfuse import Langfuse

# Skills — cada skill expone una función run(state) → SkillResult
# Los imports reales apuntarán a la implementación Python de cada skill.
# Durante desarrollo, se usan stubs que leen desde defaults.yaml.
# Skills — cada skill.py vive en skills/{skill_dir}/skill.py y expone
# una función run(state) → SkillResult. Como los nombres de carpeta tienen
# guion y prefijo numérico ('0008-sentiment-analyzer'), no son identificadores
# Python válidos y no se pueden importar con sintaxis de puntos. Se cargan
# dinámicamente por ruta de archivo — ver skills/_loader.py para el detalle
# técnico completo.
from skills._loader import load_skill

run_0000 = load_skill("0000-system-health-check").run
run_0001 = load_skill("0001-data-ingestion").run
run_0002 = load_skill("0002-data-cleanser").run
run_0003 = load_skill("0003-data-preprocessor").run
run_0008 = load_skill("0008-sentiment-analyzer").run
run_0011 = load_skill("0011-viz-reporter").run

# Estado y circuit breaker
from core.pipeline_state import (
    BACKOFF_BASE_SECONDS,
    MAX_RETRIES,
    NON_RECOVERABLE_ERRORS,
    PipelineState,
    SkillResult,
    classify_error,
    initial_state,
)

# Notificaciones HITL (Zulip)
from hooks.zulip_notifier import notify_hitl, notify_pipeline_end

# Credenciales — ADR-010: nunca hardcodeadas, siempre desde .env
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sigma.orchestrator")


# ---------------------------------------------------------------------------
# Langfuse — cliente de trazabilidad
# ---------------------------------------------------------------------------

langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "http://localhost:3000"),
)


# ---------------------------------------------------------------------------
# Circuit breaker — lógica de reintento y fallo rápido
# ---------------------------------------------------------------------------

def _should_retry(state: PipelineState, skill_id: str, error_type: str) -> bool:
    """
    Determina si el circuit breaker debe reintentar el skill o fallar rápido.

    Reglas (Decisión B, aprobada 2026-06-30):
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


def _emit_langfuse(
    trace_id: str,
    event_name: str,
    fields: dict[str, Any],
) -> None:
    """
    Emite un evento a Langfuse. Falla silenciosamente para no romper el pipeline.

    NOTA v1.1.1 (corrección real, encontrada en la primera corrida de Marx
    contra su entorno real): la versión anterior de este fix usaba
    langfuse.create_trace_id(seed=...), que asumía que ese método existe
    en el SDK instalado. No existe en langfuse 4.10.0 (la versión real
    de Marx) — solo se verificó contra 4.13.0 en el sandbox, sin
    comprobar compatibilidad entre versiones. Corregido: el trace_id de
    32 caracteres hex se calcula con hashlib directamente, sin depender
    de ningún método específico del SDK. sha256(...).hexdigest()[:32]
    siempre produce hex minúsculas válidas, determinístico igual que
    antes (mismo trace_id de SIGMA → mismo trace_id de Langfuse siempre).
    """
    try:
        import hashlib
        langfuse_trace_id = hashlib.sha256(trace_id.encode()).hexdigest()[:32]
        langfuse.create_event(
            trace_context={"trace_id": langfuse_trace_id},
            name=event_name,
            metadata={**fields, "sigma_trace_id": trace_id},
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("[langfuse] No se pudo emitir evento '%s': %s", event_name, exc)


# ---------------------------------------------------------------------------
# Nodos del grafo — uno por skill
# ---------------------------------------------------------------------------

def _run_skill(
    skill_id: str,
    skill_fn: Any,
    state: PipelineState,
) -> PipelineState:
    """
    Ejecutor genérico de skills con circuit breaker integrado.
    Cada nodo del grafo llama a esta función pasando su skill_fn.

    Flujo:
    1. Marca current_skill en el estado.
    2. Llama a skill_fn(state) → SkillResult.
    3. Si success / success_with_warnings → actualiza outputs y continúa.
    4. Si error → evalúa circuit breaker:
       - Recuperable + reintentos disponibles → reintenta.
       - No recuperable o reintentos agotados → marca failed_skill_id.
    """
    log.info("[pipeline] ▶ Iniciando skill %s", skill_id)
    _emit_langfuse(state["trace_id"], f"{skill_id}.node_start", {
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
            # Excepción no capturada por el skill → error desconocido
            error_type = type(exc).__name__
            result = SkillResult(
                skill_id=skill_id,
                status="error",
                output={},
                error_type=error_type,
                error_detail=str(exc),
                error_category="unknown",
                duration_ms=int((time.monotonic() - t0) * 1000),
                retries_attempted=attempt - 1,
            )
            log.exception("[pipeline] Excepción inesperada en skill %s", skill_id)

        if result["status"] in ("success", "success_with_warnings"):
            # ── Éxito ────────────────────────────────────────────────────
            log.info(
                "[pipeline] ✓ Skill %s completado en %dms (status=%s)",
                skill_id, result["duration_ms"], result["status"],
            )
            if result["status"] == "success_with_warnings":
                for w in result["output"].get("warnings", []):
                    state["warnings"].append(f"{skill_id}:{w}")

            # NOTA: la alerta HITL de pct_unclear > 30% en 0008 ya NO se
            # dispara aquí. Se movió a node_hitl_wait, que además PAUSA
            # el grafo de verdad con interrupt() en vez de solo notificar
            # y seguir — ver edge_after_0008 para el ruteo condicional.

            state["outputs"][skill_id] = result
            state["current_skill"] = skill_id
            _emit_langfuse(state["trace_id"], f"{skill_id}.node_end", {
                "status": result["status"],
                "duration_ms": result["duration_ms"],
            })
            return state

        # ── Error ─────────────────────────────────────────────────────────
        error_type = result.get("error_type", "UnknownError")
        log.error(
            "[pipeline] ✗ Skill %s falló: %s — %s",
            skill_id, error_type, result.get("error_detail", ""),
        )

        if _should_retry(state, skill_id, error_type):
            state["retry_counts"][skill_id] = attempt
            continue  # reintenta el while

        # Reintentos agotados o error no recuperable → circuit breaker abierto
        result["retries_attempted"] = attempt - 1
        result["error_category"] = classify_error(error_type)
        state["outputs"][skill_id] = result
        state["failed_skill_id"] = skill_id
        state["pipeline_status"] = "failed"
        _emit_langfuse(state["trace_id"], f"{skill_id}.node_error", {
            "error_type": error_type,
            "error_category": result["error_category"],
            "retries_attempted": result["retries_attempted"],
        })
        return state


# ---------------------------------------------------------------------------
# Funciones de nodo para LangGraph
# ---------------------------------------------------------------------------

def node_0000(state: PipelineState) -> PipelineState:
    """system-health-check: verifica el entorno antes de cualquier otra cosa."""
    return _run_skill("0000", run_0000, state)


def node_0001(state: PipelineState) -> PipelineState:
    """data-ingestion: carga el CSV Tirendaz en processed_data."""
    return _run_skill("0001", run_0001, state)


def node_0002(state: PipelineState) -> PipelineState:
    """data-cleanser: limpia y deduplica."""
    return _run_skill("0002", run_0002, state)


def node_0003(state: PipelineState) -> PipelineState:
    """data-preprocessor: normaliza, escala, one-hot."""
    return _run_skill("0003", run_0003, state)


def node_0008(state: PipelineState) -> PipelineState:
    """sentiment-analyzer: clasifica con RoBERTa batch=32."""
    return _run_skill("0008", run_0008, state)


def node_hitl_wait(state: PipelineState) -> PipelineState:
    """
    Pausa REAL del grafo — no bloquea el proceso de Python. Usa
    interrupt() nativo de LangGraph: el checkpointer guarda el estado
    completo en disco (sigma_checkpoints.sqlite) y graph.invoke() retorna
    de inmediato con '__interrupt__' en el resultado. El proceso queda
    libre — puede terminar, y otro proceso (webhook_receiver.py) reanuda
    después con Command(resume=...), sin ninguna memoria compartida.

    Esto corrige el problema real de la propuesta original (Asistente
    Secundario): un `while True: time.sleep(5)` bloqueaba el proceso
    completo y perdía todo el estado si el proceso moría durante la
    espera. Verificado en sandbox con dos procesos Python separados
    antes de integrar esto — ver conversación.
    """
    pct_unclear = state["outputs"].get("0008", {}).get("output", {}).get("pct_unclear", 0)
    question = (
        f"⚠️ SIGMA — Aprobación requerida\n"
        f"skill 0008: pct_unclear={pct_unclear:.1f}% supera el umbral del 30%.\n"
        f"trace_id={state['trace_id']}\n"
        f"¿Continuar con el pipeline? Responde sí/no."
    )

    # Marca en Redis ANTES de pausar — así webhook_receiver.py sabe qué
    # trace_id reanudar en cuanto llegue la respuesta de Zulip.
    mark_waiting(state["trace_id"])

    from hooks.zulip_notifier import request_hitl_confirmation
    request_hitl_confirmation(question)

    state["hitl_question"] = question
    state["hitl_notified"] = True

    # interrupt() pausa aquí. Cuando webhook_receiver.py llame a
    # graph.invoke(Command(resume=True/False), config), esta línea
    # "retorna" ese valor y el nodo continúa normalmente.
    decision: bool = interrupt({"question": question, "trace_id": state["trace_id"]})

    state["hitl_decision"] = decision
    if not decision:
        log.warning("[hitl] Decisión NEGATIVA recibida para trace_id=%s", state["trace_id"])
        state["failed_skill_id"] = "hitl_rejected"
        state["pipeline_status"] = "failed"
    else:
        log.info("[hitl] Decisión AFIRMATIVA recibida para trace_id=%s", state["trace_id"])

    return state


def node_0011(state: PipelineState) -> PipelineState:
    """viz-reporter: genera dashboard y resumen, persiste en MinIO."""
    result_state = _run_skill("0011", run_0011, state)
    # Extrae dashboard_url al nivel de estado para acceso rápido
    if result_state["pipeline_status"] != "failed":
        result_state["dashboard_url"] = (
            result_state["outputs"]
            .get("0011", {})
            .get("output", {})
            .get("dashboard_url")
        )
    return result_state


def node_handle_error(state: PipelineState) -> PipelineState:
    """
    Nodo de manejo de errores. Se activa cuando cualquier skill
    escribe pipeline_status='failed'.

    Responsabilidades:
    1. Loguear el error con contexto completo.
    2. Emitir evento pipeline.failed a Langfuse.
    3. Notificar a Zulip con el detalle del fallo.
    4. Marcar el estado como 'failed' y devolver.
    """
    failed_id = state.get("failed_skill_id", "desconocido")
    failed_result = state["outputs"].get(failed_id, {})

    log.error(
        "[pipeline] ✗✗ Pipeline fallido en skill %s: %s",
        failed_id,
        failed_result.get("error_detail", "sin detalle"),
    )

    _emit_langfuse(state["trace_id"], "pipeline.failed", {
        "failed_skill_id": failed_id,
        "error_type": failed_result.get("error_type"),
        "error_category": failed_result.get("error_category"),
        "error_detail": failed_result.get("error_detail"),
        "skills_completed": list(state["outputs"].keys()),
        "warnings_accumulated": state["warnings"],
    })

    notify_hitl(
        message=(
            f"🔴 SIGMA Hito 1 — Pipeline FALLIDO\n"
            f"Skill: {failed_id}\n"
            f"Error: {failed_result.get('error_type', 'Unknown')}\n"
            f"Detalle: {failed_result.get('error_detail', 'sin detalle')}\n"
            f"trace_id: {state['trace_id']}"
        )
    )
    state["hitl_notified"] = True
    state["pipeline_status"] = "failed"
    return state


def node_end(state: PipelineState) -> PipelineState:
    """
    Nodo final del pipeline exitoso.
    Emite pipeline.success a Langfuse y notifica a Zulip con el resumen.
    """
    log.info("[pipeline] ✓✓ Pipeline completado exitosamente")
    log.info("[pipeline]    dashboard_url=%s", state.get("dashboard_url"))
    log.info("[pipeline]    warnings=%s", state["warnings"])

    _emit_langfuse(state["trace_id"], "pipeline.success", {
        "dashboard_url": state.get("dashboard_url"),
        "warnings": state["warnings"],
        "hitl_notified": state["hitl_notified"],
        "skills_completed": list(state["outputs"].keys()),
    })

    notify_pipeline_end(
        success=True,
        dashboard_url=state.get("dashboard_url"),
        warnings=state["warnings"],
        trace_id=state["trace_id"],
    )

    state["pipeline_status"] = "success"
    return state


# ---------------------------------------------------------------------------
# Bordes condicionales — circuit breaker en el grafo
# ---------------------------------------------------------------------------

def _edge_after_skill(state: PipelineState, next_skill: str) -> str:
    """
    Borde condicional genérico. Después de cada skill evalúa:
    - Si pipeline_status == 'failed' → salta a HANDLE_ERROR.
    - Si no → avanza al siguiente skill.

    Esto implementa el circuit breaker a nivel de grafo: una vez que
    un skill marca el pipeline como fallido, ningún nodo posterior
    se ejecuta.
    """
    if state["pipeline_status"] == "failed":
        return "HANDLE_ERROR"
    return next_skill


def edge_after_0000(state: PipelineState) -> str:
    return _edge_after_skill(state, "node_0001")


def edge_after_0001(state: PipelineState) -> str:
    return _edge_after_skill(state, "node_0002")


def edge_after_0002(state: PipelineState) -> str:
    return _edge_after_skill(state, "node_0003")


def edge_after_0003(state: PipelineState) -> str:
    return _edge_after_skill(state, "node_0008")


def edge_after_0008(state: PipelineState) -> str:
    if state["pipeline_status"] == "failed":
        return "HANDLE_ERROR"

    pct_unclear = state["outputs"].get("0008", {}).get("output", {}).get("pct_unclear", 0)
    if pct_unclear > 30.0:
        log.info(
            "[hitl] pct_unclear=%.1f%% > 30%% → pausando en node_hitl_wait",
            pct_unclear,
        )
        return "node_hitl_wait"

    return "node_0011"


def edge_after_0011(state: PipelineState) -> str:
    return _edge_after_skill(state, "node_end")


def edge_after_hitl_wait(state: PipelineState) -> str:
    """
    Tras reanudar de la pausa HITL: decision True → continúa a 0011,
    decision False → HANDLE_ERROR (rechazo humano explícito).
    """
    if state.get("hitl_decision") is False or state["pipeline_status"] == "failed":
        return "HANDLE_ERROR"
    return "node_0011"


# ---------------------------------------------------------------------------
# Construcción del grafo LangGraph
# ---------------------------------------------------------------------------

def build_graph(checkpointer=None) -> StateGraph:
    """
    Construye y compila el grafo LangGraph del pipeline Hito 1.

    DAG principal (acíclico):
      START → 0000 → 0001 → 0002 → 0003 → 0008 → [0011 | node_hitl_wait] → END

    node_hitl_wait pausa el grafo de verdad con interrupt() nativo de
    LangGraph cuando pct_unclear > 30% en 0008. Requiere un checkpointer
    persistente (SQLite) para sobrevivir entre el proceso que pausa
    (orchestrator.py) y el proceso que reanuda (webhook_receiver.py) —
    ver core/checkpointer.py para el detalle completo y la prueba de
    dos-procesos-separados que confirma que esto funciona de verdad.

    Bordes de error (ciclicidad controlada dentro del DAG acíclico):
      Cualquier nodo → HANDLE_ERROR → END
      (El borde al error nunca crea un ciclo porque HANDLE_ERROR
       no tiene borde de vuelta a ningún nodo de procesamiento.
       Cumple la sección de ciclicidad/aciclicidad del Plan Maestro.)

    ADR-009: Nodos configurados desde SKILL.md de cada skill.
    """
    graph = StateGraph(PipelineState)

    # Nodos
    graph.add_node("node_0000", node_0000)
    graph.add_node("node_0001", node_0001)
    graph.add_node("node_0002", node_0002)
    graph.add_node("node_0003", node_0003)
    graph.add_node("node_0008", node_0008)
    graph.add_node("node_hitl_wait", node_hitl_wait)
    graph.add_node("node_0011", node_0011)
    graph.add_node("HANDLE_ERROR", node_handle_error)
    graph.add_node("node_end", node_end)

    # Borde de entrada
    graph.add_edge(START, "node_0000")

    # Bordes condicionales con circuit breaker
    graph.add_conditional_edges("node_0000", edge_after_0000,
                                {"node_0001": "node_0001", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0001", edge_after_0001,
                                {"node_0002": "node_0002", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0002", edge_after_0002,
                                {"node_0003": "node_0003", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0003", edge_after_0003,
                                {"node_0008": "node_0008", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0008", edge_after_0008,
                                {"node_0011": "node_0011", "node_hitl_wait": "node_hitl_wait",
                                 "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_hitl_wait", edge_after_hitl_wait,
                                {"node_0011": "node_0011", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0011", edge_after_0011,
                                {"node_end": "node_end", "HANDLE_ERROR": "HANDLE_ERROR"})

    # Desde HANDLE_ERROR siempre termina (sin ciclos de vuelta)
    graph.add_edge("HANDLE_ERROR", END)
    graph.add_edge("node_end", END)

    return graph.compile(checkpointer=checkpointer)


# ---------------------------------------------------------------------------
# Punto de entrada — CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SIGMA Orquestador — Hito 1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python orchestrator.py --variant Full --data-path ./data/tirendaz.csv\n"
            "  python orchestrator.py --variant Dev  --data-path ./data/tirendaz.csv\n"
        ),
    )
    parser.add_argument(
        "--variant",
        choices=["Full", "Lite", "Dev", "Runtime"],
        default="Full",
        help="Variante SIGMA a usar (default: Full)",
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="Ruta al dataset CSV de entrada (ej. ./data/tirendaz.csv)",
    )
    args = parser.parse_args()

    # Generar IDs de trazabilidad
    run_uuid = uuid.uuid4().hex[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    trace_id = f"sigma-{ts}-{run_uuid}"
    pipeline_run_id = f"run-{ts}-{run_uuid}"

    log.info("=" * 60)
    log.info("SIGMA Orquestador — Hito 1")
    log.info("trace_id       : %s", trace_id)
    log.info("pipeline_run_id: %s", pipeline_run_id)
    log.info("sigma_variant  : %s", args.variant)
    log.info("data_path      : %s", args.data_path)
    log.info("=" * 60)

    # Estado inicial
    state = initial_state(
        trace_id=trace_id,
        pipeline_run_id=pipeline_run_id,
        sigma_variant=args.variant,
        data_path=args.data_path,
    )

    # Emitir evento de inicio del pipeline
    _emit_langfuse(trace_id, "pipeline.start", {
        "sigma_variant": args.variant,
        "data_path": args.data_path,
        "pipeline_run_id": pipeline_run_id,
    })

    # Compilar y ejecutar el grafo — con checkpointer persistente para
    # que node_hitl_wait pueda pausar de verdad (interrupt()) y sobrevivir
    # a que este proceso termine. webhook_receiver.py reanuda después
    # como proceso separado, usando el mismo archivo sigma_checkpoints.sqlite.
    from core.checkpointer import get_checkpointer

    with get_checkpointer() as checkpointer:
        compiled_graph = build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": trace_id}}
        final_state: PipelineState = compiled_graph.invoke(state, config=config)

        # ── El grafo se pausó en node_hitl_wait — esto NO es éxito ni
        #    fallo, es una tercera categoría: "esperando decisión humana".
        if "__interrupt__" in final_state:
            log.info("=" * 60)
            log.info("[resultado] ⏸  Pipeline PAUSADO — esperando decisión humana en Zulip")
            log.info("[resultado]    trace_id: %s", trace_id)
            log.info("[resultado]    Responde en Zulip (canal Sigma-Approval) para reanudar.")
            log.info("[resultado]    Este proceso puede terminar con seguridad — el estado")
            log.info("[resultado]    ya está persistido en sigma_checkpoints.sqlite.")
            log.info("=" * 60)
            return

    # Resultado final (solo se alcanza si NO se pausó en HITL)
    if final_state["pipeline_status"] == "success":
        log.info("[resultado] ✓ Pipeline exitoso")
        log.info("[resultado]   dashboard_url : %s", final_state.get("dashboard_url"))
        log.info("[resultado]   warnings      : %s", final_state["warnings"])
    else:
        failed = final_state.get("failed_skill_id", "desconocido")
        log.error("[resultado] ✗ Pipeline fallido en skill %s", failed)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
