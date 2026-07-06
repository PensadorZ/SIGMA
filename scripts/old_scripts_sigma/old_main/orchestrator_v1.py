"""
orchestrator.py

Orquestador mínimo de SIGMA. Implementa el ítem 2 de AgDR-001:
"orchestrator.py mínimo — UN solo flujo lineal, sin sub-grafos".

Deliberadamente NO implementa la arquitectura de 3 Orquestadores
(Gerente/Ingeniero/Director) propuesta para una fase posterior. Esa
arquitectura queda formalmente aprobada en AgDR-001 Parte B, pero
secuenciada después de validar el flujo más simple posible con datos
reales — invertir ese orden repetiría el patrón de riesgo que el
propio diagnóstico de probabilidad de éxito del proyecto identificó
como causa raíz: complejidad de integración antes de validación.

Este Orquestador hace exactamente una cosa por ahora: construye un
grafo LangGraph de un solo nodo (system-health-check) y lo ejecuta.
Cada skill nuevo que se implemente (0001, 0002...) se añade como un
nodo adicional en una cadena lineal, sin ramificaciones ni paralelismo
de control hasta que ADR-002/ADR-009 lo requieran explícitamente para
un skill concreto (el paralelismo intra-skill de MapReduce es asunto
del propio skill, no del grafo del Orquestador).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

# Permite ejecutar este archivo directamente (`python orchestrator.py`)
# sin depender de que el proyecto esté instalado como paquete.
sys.path.insert(0, str(Path(__file__).parent))

import conftest  # noqa: E402  - registra los skill.py de carpetas 00xx- como módulos importables

from sigma.core import emit_trace_event, get_sigma_variant  # noqa: E402


class OrchestratorState(TypedDict, total=False):
    """
    Estado compartido del grafo. Crece conforme se añaden nodos nuevos
    (0001-data-ingestion añadirá `raw_table`, 0002 añadirá `cleaned_table`,
    etc.) Por ahora solo necesita lo que system-health-check produce.
    """

    run_id: str
    trace_id: str
    health_check_verdict: str
    health_check_reason: str
    pipeline_status: str  # "running" | "blocked" | "completed"


def node_system_health_check(state: OrchestratorState) -> OrchestratorState:
    """
    Nodo único del grafo mínimo. Invoca 0000-system-health-check y
    traduce su veredicto al estado del Orquestador.
    """
    from skills_0000_system_health_check.skill import (
        MissingConfigurationError,
        run_system_health_check,
    )

    run_id = state.get("run_id", "orch-run")
    trace_id = state.get("trace_id", f"tr-{run_id}")

    try:
        result = run_system_health_check(run_id=run_id, trace_id=trace_id)
    except MissingConfigurationError as exc:
        emit_trace_event(
            "orchestrator.node_failed",
            trace_id=trace_id,
            run_id=run_id,
            node="system-health-check",
            error=str(exc),
        )
        return {
            **state,
            "health_check_verdict": "BLOCKED",
            "health_check_reason": str(exc),
            "pipeline_status": "blocked",
        }

    new_status = "blocked" if result.verdict == "BLOCKED" else "running"

    emit_trace_event(
        "orchestrator.node_completed",
        trace_id=trace_id,
        run_id=run_id,
        node="system-health-check",
        verdict=result.verdict,
    )

    return {
        **state,
        "health_check_verdict": result.verdict,
        "health_check_reason": result.verdict_reason,
        "pipeline_status": new_status,
    }


def route_after_health_check(state: OrchestratorState) -> str:
    """
    Decide si el grafo continúa o se detiene tras system-health-check.
    Esta es la única bifurcación del Orquestador mínimo: BLOCKED termina
    el pipeline inmediatamente (ADR-004), cualquier otro veredicto
    continúa. Cuando se añada 0001-data-ingestion, esta función crecerá
    para apuntar al siguiente nodo en vez de a END.
    """
    if state.get("health_check_verdict") == "BLOCKED":
        return "blocked_end"
    return "continue"


def build_graph() -> StateGraph:
    """
    Construye el grafo mínimo de un solo nodo. La función existe
    separada de `run_pipeline` para que los tests de integración
    (Fase 2.7 del Roadmap Técnico) puedan inspeccionar la estructura
    del grafo sin ejecutarlo.
    """
    graph = StateGraph(OrchestratorState)
    graph.add_node("system_health_check", node_system_health_check)
    graph.set_entry_point("system_health_check")
    graph.add_conditional_edges(
        "system_health_check",
        route_after_health_check,
        {
            "blocked_end": END,
            "continue": END,  # hasta que exista 0001, "continue" también termina aquí
        },
    )
    return graph


def run_pipeline(run_id: str | None = None, trace_id: str | None = None) -> OrchestratorState:
    """
    Punto de entrada del Orquestador. Ejecuta el grafo mínimo de
    extremo a extremo y devuelve el estado final.
    """
    import uuid

    run_id = run_id or f"orch-{uuid.uuid4().hex[:8]}"
    trace_id = trace_id or f"tr-{run_id}"

    variant = get_sigma_variant()
    emit_trace_event(
        "orchestrator.pipeline_started",
        trace_id=trace_id,
        run_id=run_id,
        sigma_variant=variant,
    )

    compiled = build_graph().compile()
    final_state: OrchestratorState = compiled.invoke(
        {"run_id": run_id, "trace_id": trace_id, "pipeline_status": "running"}
    )

    emit_trace_event(
        "orchestrator.pipeline_completed",
        trace_id=trace_id,
        run_id=run_id,
        final_status=final_state.get("pipeline_status"),
        health_check_verdict=final_state.get("health_check_verdict"),
    )

    return final_state


if __name__ == "__main__":
    import json

    state = run_pipeline()
    print(json.dumps(dict(state), indent=2, ensure_ascii=False))

    if state.get("pipeline_status") == "blocked":
        print(
            f"\nPIPELINE BLOQUEADO: {state.get('health_check_reason')}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nPIPELINE COMPLETADO (nodo único: system-health-check).")
    sys.exit(0)
