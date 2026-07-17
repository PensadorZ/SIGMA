# =============================================================================
# sigma/core/engineer_datos.py
# SIGMA v1.5 · Hito 2, Rollout 1 (ADR-016 Tab. 2, Fig. 1 v1.3)
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.1.0
# =============================================================================
# Subgrafo Engineer Datos — envuelve el DAG de Hito 1 (orchestrator.py
# v1.1.0), sin cambiar su lógica interna, e inserta 0004-statistical-
# validator entre 0003 y 0008 (decisión confirmada: verificar calidad
# estadística de los datos antes del paso más caro computacionalmente,
# RoBERTa). Skills: 0000-0004, 0008, 0011 (ADR-016 v1.3).
#
# Este módulo NO se ejecuta solo (sin CLI propio) — se compila aquí y
# director_main.py lo añade como nodo del grafo padre (Rollout 1).
# También se compila independientemente en los tests (build_engineer_
# datos_graph(checkpointer=None)) para cumplir la condición de salida
# (a) de ADR-016 Tab. 2: suite pytest-bdd de Engineer Datos en verde,
# sin necesidad del Director.
#
# HITL propio de este Engineer (decisión confirmada: cada Engineer
# maneja su propio HITL como bypass si A2A falla) — node_hitl_wait se
# preserva tal cual funcionaba en orchestrator.py v1.1.0, sin cambios.
#
# NOTA v1.1.0 — CORRECCIÓN sobre el diseño original de node_0004:
# verificado contra "Eco MultiAgentes Sigma 3 (Hito 1)" que el pipeline
# real Tirendaz → RoBERTa NO tiene columna objetivo antes de 0008 (la
# etiqueta de sentimiento la genera 0008, no la trae Tirendaz
# pre-etiquetada como IMDb). El diseño original (Modo C, leakage contra
# una columna objetivo, con SIGMA_LEAKAGE_TARGET_COL) partía de una
# premisa falsa y se descartó. node_0004 corre ahora sin forzar ningún
# modo — cae a descriptive_fallback por la propia lógica estructural de
# 0004 (Tab. 1 de su SKILL.md), que sí tiene datos reales disponibles
# en este punto del pipeline.
# =============================================================================

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from sigma.core.checkpointer import mark_waiting
from sigma.core.pipeline_state import PipelineState
from sigma.core.skill_runner import run_skill, emit_langfuse
from sigma.hooks.zulip_notifier import request_hitl_confirmation
from sigma.skills._loader import load_skill

log = logging.getLogger("sigma.engineer_datos")

run_0000 = load_skill("0000-system-health-check").run
run_0001 = load_skill("0001-data-ingestion").run
run_0002 = load_skill("0002-data-cleanser").run
run_0003 = load_skill("0003-data-preprocessor").run
run_0004 = load_skill("0004-statistical-validator").run
run_0008 = load_skill("0008-sentiment-analyzer").run
run_0011 = load_skill("0011-viz-reporter").run


# ---------------------------------------------------------------------------
# Nodos — 0000, 0001, 0002, 0003 sin cambios respecto a orchestrator.py v1.1.0
# ---------------------------------------------------------------------------

def node_0000(state: PipelineState) -> PipelineState:
    """system-health-check: verifica el entorno antes de cualquier otra cosa."""
    return run_skill("0000", run_0000, state)


def node_0001(state: PipelineState) -> PipelineState:
    """data-ingestion: carga el CSV Tirendaz en processed_data."""
    return run_skill("0001", run_0001, state)


def node_0002(state: PipelineState) -> PipelineState:
    """data-cleanser: limpia y deduplica."""
    return run_skill("0002", run_0002, state)


def node_0003(state: PipelineState) -> PipelineState:
    """data-preprocessor: normaliza, escala, one-hot."""
    return run_skill("0003", run_0003, state)


def node_0004(state: PipelineState) -> PipelineState:
    """
    statistical-validator, nuevo en Rollout 1.

    CORREGIDO tras verificar "Eco MultiAgentes Sigma 3 (Hito 1)": el
    pipeline real Tirendaz → RoBERTa NO tiene columna objetivo en esta
    etapa — la etiqueta de sentimiento la genera 0008 DESPUÉS de este
    nodo, no antes (mismo motivo por el que 0003-data-preprocessor
    desactiva SMOTE/class_weight/PCA por defecto). El diseño original
    de este nodo (Modo C, leakage contra una columna objetivo) partía
    de una premisa falsa y se descarta.

    Sin hypothesis, datetime_index, live_feedback ni columna objetivo
    disponibles aquí, la única rama de la Tab. 1 (SKILL.md de 0004) con
    datos reales que la respalden es descriptive_fallback (nulos,
    duplicados) — no se fuerza ningún modo especial, se deja que
    _select_branch() de 0004 llegue ahí por su propia lógica estructural.
    """
    return run_skill("0004", run_0004, state)


def node_0008(state: PipelineState) -> PipelineState:
    """sentiment-analyzer: clasifica con RoBERTa batch=32."""
    return run_skill("0008", run_0008, state)


def node_hitl_wait(state: PipelineState) -> PipelineState:
    """
    Pausa REAL del subgrafo — idéntico a orchestrator.py v1.1.0, sin
    cambios. HITL propio de Engineer Datos (bypass si A2A falla).
    """
    pct_unclear = state["outputs"].get("0008", {}).get("output", {}).get("pct_unclear", 0)
    question = (
        f"⚠️ SIGMA — Aprobación requerida (Engineer Datos)\n"
        f"skill 0008: pct_unclear={pct_unclear:.1f}% supera el umbral del 30%.\n"
        f"trace_id={state['trace_id']}\n"
        f"¿Continuar con el pipeline? Responde sí/no."
    )
    mark_waiting(state["trace_id"])
    request_hitl_confirmation(question)
    state["hitl_question"] = question
    state["hitl_notified"] = True

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
    result_state = run_skill("0011", run_0011, state)
    if result_state["pipeline_status"] != "failed":
        result_state["dashboard_url"] = (
            result_state["outputs"].get("0011", {}).get("output", {}).get("dashboard_url")
        )
    return result_state


def node_engineer_datos_end(state: PipelineState) -> PipelineState:
    """
    Fin del subgrafo Engineer Datos (equivalente a node_end de
    orchestrator.py v1.1.0, sin la notificación final a Zulip — esa
    responsabilidad sube al Director en Rollout 1, no se duplica aquí).
    """
    log.info("[engineer_datos] ✓✓ Subgrafo completado exitosamente")
    state["pipeline_status"] = "success"
    return state


def node_handle_error(state: PipelineState) -> PipelineState:
    """Manejo de errores dentro de Engineer Datos — emite a Langfuse,
    deja que el Director decida si notifica HITL global (Tab. 1 ADR-016)."""
    failed_id = state.get("failed_skill_id", "desconocido")
    failed_result = state["outputs"].get(failed_id, {})
    log.error(
        "[engineer_datos] ✗✗ Subgrafo fallido en skill %s: %s",
        failed_id, failed_result.get("error_detail", "sin detalle"),
    )
    emit_langfuse(state["trace_id"], "engineer_datos.failed", {
        "failed_skill_id": failed_id,
        "error_type": failed_result.get("error_type"),
        "error_category": failed_result.get("error_category"),
        "skills_completed": list(state["outputs"].keys()),
        "warnings_accumulated": state["warnings"],
    })
    state["pipeline_status"] = "failed"
    return state


# ---------------------------------------------------------------------------
# Bordes condicionales — circuit breaker, idéntico patrón a Hito 1
# ---------------------------------------------------------------------------

def _edge_after_skill(state: PipelineState, next_skill: str) -> str:
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
    """Nuevo en Rollout 1: 0003 → 0004 (antes iba directo a 0008)."""
    return _edge_after_skill(state, "node_0004")


def edge_after_0004(state: PipelineState) -> str:
    """Nuevo en Rollout 1: 0004 → 0008."""
    return _edge_after_skill(state, "node_0008")


def edge_after_0008(state: PipelineState) -> str:
    if state["pipeline_status"] == "failed":
        return "HANDLE_ERROR"
    pct_unclear = state["outputs"].get("0008", {}).get("output", {}).get("pct_unclear", 0)
    if pct_unclear > 30.0:
        log.info("[hitl] pct_unclear=%.1f%% > 30%% → pausando en node_hitl_wait", pct_unclear)
        return "node_hitl_wait"
    return "node_0011"


def edge_after_0011(state: PipelineState) -> str:
    return _edge_after_skill(state, "node_engineer_datos_end")


def edge_after_hitl_wait(state: PipelineState) -> str:
    if state.get("hitl_decision") is False or state["pipeline_status"] == "failed":
        return "HANDLE_ERROR"
    return "node_0011"


# ---------------------------------------------------------------------------
# Construcción del subgrafo
# ---------------------------------------------------------------------------

def build_engineer_datos_graph(checkpointer=None) -> StateGraph:
    """
    Construye y compila el subgrafo Engineer Datos.

    DAG (acíclico):
      START → 0000 → 0001 → 0002 → 0003 → 0004 → 0008
            → [0011 | node_hitl_wait] → engineer_datos_end

    Diferencia respecto al DAG de Hito 1 (orchestrator.py v1.1.0):
    se inserta 0004-statistical-validator entre 0003 y 0008 (ADR-016 v1.3).
    Todo lo demás — circuit breaker, HITL, manejo de errores — es
    idéntico, sin reescritura.

    checkpointer=None permite compilar este subgrafo de forma
    independiente para tests (condición de salida (a), ADR-016 Tab. 2) —
    director_main.py pasará el checkpointer compartido cuando lo añada
    como nodo del grafo padre.
    """
    graph = StateGraph(PipelineState)

    graph.add_node("node_0000", node_0000)
    graph.add_node("node_0001", node_0001)
    graph.add_node("node_0002", node_0002)
    graph.add_node("node_0003", node_0003)
    graph.add_node("node_0004", node_0004)
    graph.add_node("node_0008", node_0008)
    graph.add_node("node_hitl_wait", node_hitl_wait)
    graph.add_node("node_0011", node_0011)
    graph.add_node("HANDLE_ERROR", node_handle_error)
    graph.add_node("node_engineer_datos_end", node_engineer_datos_end)

    graph.add_edge(START, "node_0000")

    graph.add_conditional_edges("node_0000", edge_after_0000,
                                {"node_0001": "node_0001", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0001", edge_after_0001,
                                {"node_0002": "node_0002", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0002", edge_after_0002,
                                {"node_0003": "node_0003", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0003", edge_after_0003,
                                {"node_0004": "node_0004", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0004", edge_after_0004,
                                {"node_0008": "node_0008", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0008", edge_after_0008,
                                {"node_0011": "node_0011", "node_hitl_wait": "node_hitl_wait",
                                 "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_hitl_wait", edge_after_hitl_wait,
                                {"node_0011": "node_0011", "HANDLE_ERROR": "HANDLE_ERROR"})
    graph.add_conditional_edges("node_0011", edge_after_0011,
                                {"node_engineer_datos_end": "node_engineer_datos_end",
                                 "HANDLE_ERROR": "HANDLE_ERROR"})

    graph.add_edge("HANDLE_ERROR", END)
    graph.add_edge("node_engineer_datos_end", END)

    return graph.compile(checkpointer=checkpointer)
