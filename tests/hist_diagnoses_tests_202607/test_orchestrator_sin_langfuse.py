"""
Prueba definitiva - corre el orquestador REAL, pero con TODAS las
llamadas a Langfuse convertidas en no-operacion (ni siquiera se
inicializa el cliente). Si postgres/redis se vuelven instantaneos
AQUI, confirma que el hilo de fondo de Langfuse es la causa real de
la contencion. Si siguen lentos, Langfuse queda descartado tambien,
y hay que seguir buscando en otra direccion.

Uso: python test_orchestrator_sin_langfuse.py
"""
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

# Neutraliza _emit_langfuse ANTES de que se llame nunca, para que
# el hilo de fondo de Langfuse nunca haga ninguna peticion.
import orchestrator

def _no_op_langfuse(trace_id, event_name, fields):
    pass

orchestrator._emit_langfuse = _no_op_langfuse
print("_emit_langfuse neutralizada -- Langfuse NUNCA se llama en esta prueba.")
print()

from sigma.core.pipeline_state import initial_state
from sigma.core.checkpointer import get_checkpointer

state = initial_state(
    trace_id="test-sin-langfuse",
    pipeline_run_id="run-test-sin-langfuse",
    sigma_variant="Full",
    data_path="./data/tirendaz.csv",
)

with get_checkpointer() as checkpointer:
    graph = orchestrator.build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "test-sin-langfuse"}}
    t0 = time.monotonic()
    result = graph.invoke(state, config=config)
    print(f"\nTiempo total del nodo 0000: {time.monotonic() - t0:.2f}s")
    print(f"pipeline_status: {result.get('pipeline_status')}")
