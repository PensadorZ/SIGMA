# =============================================================================
# sigma/core/director.py
# SIGMA v1.5 · Hito 2, Rollout 1 (ADR-016 v1.3, Tab. 2)
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.0.0
# =============================================================================
# Director mínimo viable — Rollout 1. Conoce únicamente Engineer Datos
# (ADR-016 §2.4: "el Director nunca conoce Engineers que aún no
# existen"). Engineer Modelos y Engineer Auditor se añaden en Rollout 2
# y 3 respectivamente, cuando existan.
#
# DirectorState es un estado PROPIO, no PipelineState reutilizado
# (Decisión confirmada por Marx — Ruta Dura, punto 1: "Confirmo el
# anidamiento"). La traducción entre DirectorState y el PipelineState
# que Engineer Datos espera es EXPLÍCITA (Ruta Dura, punto 2: función de
# traducción, no mapeo automático de LangGraph por nombre de clave) —
# confirmado como "más seguro, verificar en la práctica si hay que
# cambiarlo".
#
# ⚠️ ÁREA SIN VERIFICAR EMPÍRICAMENTE — no inventado, señalado con
# honestidad: la propagación de interrupt() de Engineer Datos hacia
# arriba, a través de una función de nodo que invoca el subgrafo
# manualmente (en vez de que LangGraph lo trate como nodo-subgrafo
# nativo), depende de que el mismo checkpointer y el mismo thread_id
# (trace_id) se usen en ambos niveles. El patrón de abajo sigue la
# documentación de LangGraph para este caso, pero la condición de salida
# (d) de ADR-016 Tab. 2 (traza Langfuse completa verificada end-to-end)
# es precisamente la prueba real que confirma si esto funciona como se
# espera — no se puede dar por sentado sin esa corrida real.
# =============================================================================

from __future__ import annotations

import logging
from typing import Any, Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from sigma.core.engineer_datos import build_engineer_datos_graph
from sigma.core.pipeline_state import PipelineState, initial_state
from sigma.core.tracing import emit_trace_event

log = logging.getLogger("sigma.director")


# ---------------------------------------------------------------------------
# DirectorState — propio, anida PipelineState de cada Engineer
# ---------------------------------------------------------------------------

class DirectorState(TypedDict):
    """
    Estado del Director. No reutiliza PipelineState — lo anida, uno por
    Engineer invocado, dentro de `engineer_results`. El Director necesita
    metadata que ningún Engineer necesita conocer (a qué Engineer
    enrutar, qué falló a nivel de todo el sistema); los Engineers no
    necesitan saber que existe un Director por encima.
    """

    trace_id: str
    pipeline_run_id: str
    sigma_variant: str
    sigma_submode: str
    data_path: str

    director_status: Literal["running", "success", "failed"]

    # Resultado completo (PipelineState) de cada Engineer que ya corrió,
    # indexado por nombre. En Rollout 1 solo existirá "engineer_datos".
    engineer_results: dict[str, PipelineState]

    # Extraídos del Engineer relevante para acceso rápido sin recorrer
    # engineer_results — mismo patrón que dashboard_url en PipelineState.
    dashboard_url: Optional[str]
    warnings: list[str]
    failed_engineer_id: Optional[str]


def build_initial_director_state(
    trace_id: str,
    pipeline_run_id: str,
    sigma_variant: str,
    sigma_submode: str,
    data_path: str,
) -> DirectorState:
    return DirectorState(
        trace_id=trace_id,
        pipeline_run_id=pipeline_run_id,
        sigma_variant=sigma_variant,
        sigma_submode=sigma_submode,
        data_path=data_path,
        director_status="running",
        engineer_results={},
        dashboard_url=None,
        warnings=[],
        failed_engineer_id=None,
    )


# ---------------------------------------------------------------------------
# Función de traducción DirectorState -> PipelineState (Engineer Datos)
# ---------------------------------------------------------------------------

def _translate_to_engineer_datos_input(director_state: DirectorState) -> PipelineState:
    """
    Traduce DirectorState al PipelineState que Engineer Datos espera.
    Explícita, no automática — decisión confirmada (Ruta Dura, punto 2).
    """
    return initial_state(
        trace_id=director_state["trace_id"],
        pipeline_run_id=director_state["pipeline_run_id"],
        sigma_variant=director_state["sigma_variant"],
        sigma_submode=director_state["sigma_submode"],
        data_path=director_state["data_path"],
    )


def _translate_from_engineer_datos_output(
    director_state: DirectorState,
    engineer_result: PipelineState,
) -> DirectorState:
    """Traduce el PipelineState final de Engineer Datos de vuelta a
    DirectorState. Traducción explícita, simétrica a la de arriba."""
    director_state["engineer_results"]["engineer_datos"] = engineer_result
    director_state["warnings"].extend(engineer_result.get("warnings", []))
    director_state["dashboard_url"] = engineer_result.get("dashboard_url")

    if engineer_result["pipeline_status"] == "failed":
        director_state["director_status"] = "failed"
        director_state["failed_engineer_id"] = "engineer_datos"
    else:
        director_state["director_status"] = "success"

    return director_state


# ---------------------------------------------------------------------------
# Nodo del Director — invoca Engineer Datos
# ---------------------------------------------------------------------------

def make_node_engineer_datos(checkpointer):
    """
    Factory de la función de nodo — necesita el checkpointer compartido
    para compilar el subgrafo de Engineer Datos con el mismo backend de
    persistencia que el Director, condición necesaria para que
    interrupt() se propague correctamente entre ambos niveles (ver
    advertencia al inicio del archivo).
    """
    engineer_datos_graph = build_engineer_datos_graph(checkpointer=checkpointer)

    def node_engineer_datos(director_state: DirectorState) -> DirectorState:
        log.info("[director] ▶ Delegando a Engineer Datos (trace_id=%s)", director_state["trace_id"])
        child_input = _translate_to_engineer_datos_input(director_state)
        config = {"configurable": {"thread_id": director_state["trace_id"]}}

        result = engineer_datos_graph.invoke(child_input, config=config)

        if "__interrupt__" in result:
            # HITL propio de Engineer Datos (bypass A2A) — el Director
            # no intercepta esta pausa, la deja subir tal cual. Quien
            # invoque al Director (director_main.py) es responsable de
            # detectarla, igual que orchestrator.py v1.1.0 lo hacía.
            log.info("[director] ⏸ Engineer Datos pausado en HITL — propagando interrupt")
            return {**director_state, "__interrupt__": result["__interrupt__"]}

        return _translate_from_engineer_datos_output(director_state, result)

    return node_engineer_datos


def node_director_end(director_state: DirectorState) -> DirectorState:
    log.info("[director] ✓✓ Rollout 1 completado — status=%s", director_state["director_status"])
    emit_trace_event(
        "director.success" if director_state["director_status"] == "success" else "director.failed",
        director_state["trace_id"],
        dashboard_url=director_state.get("dashboard_url"),
        warnings=director_state["warnings"],
        failed_engineer_id=director_state.get("failed_engineer_id"),
    )
    return director_state


def edge_after_engineer_datos(director_state: DirectorState) -> str:
    if "__interrupt__" in director_state:
        return END  # el interrupt ya se está propagando, no hay más nodos que correr
    return "director_end"


# ---------------------------------------------------------------------------
# Construcción del grafo del Director — Rollout 1
# ---------------------------------------------------------------------------

def build_director_graph(checkpointer=None) -> StateGraph:
    """
    Grafo del Director — Rollout 1.

    DAG (acíclico, mínimo por diseño — ADR-016 §2.4):
      START → engineer_datos → director_end

    Solo conoce Engineer Datos. Engineer Modelos y Engineer Auditor se
    añaden en Rollout 2 y 3 — este archivo se extiende entonces, no se
    reescribe (AGENTS_CREATOR.md §3, versionado).
    """
    graph = StateGraph(DirectorState)

    graph.add_node("engineer_datos", make_node_engineer_datos(checkpointer))
    graph.add_node("director_end", node_director_end)

    graph.add_edge(START, "engineer_datos")
    graph.add_conditional_edges("engineer_datos", edge_after_engineer_datos,
                                {"director_end": "director_end", END: END})
    graph.add_edge("director_end", END)

    return graph.compile(checkpointer=checkpointer)
