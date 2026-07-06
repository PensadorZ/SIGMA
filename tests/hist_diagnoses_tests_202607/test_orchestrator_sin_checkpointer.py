"""
Prueba definitiva #2 - mismo pipeline real, pero esta vez SIN
checkpointer (SqliteSaver) en absoluto. Si postgres/redis se vuelven
instantaneos AQUI, confirma que el hilo de fondo de aiosqlite (usado
por SqliteSaver) es la causa real de la contencion - no Langfuse.

NOTA: sin checkpointer, node_hitl_wait (interrupt()) no podria pausar
correctamente en un pipeline real - esto es SOLO para diagnostico,
no para uso normal.

Uso: python test_orchestrator_sin_checkpointer.py
"""
import time

from dotenv import load_dotenv
load_dotenv()

import orchestrator

# Neutraliza tambien Langfuse, para aislar UNA sola variable a la vez
# (ya sabemos que Langfuse no es la causa, pero lo dejamos fuera para
# no mezclar dos posibles causas en la misma prueba).
def _no_op_langfuse(trace_id, event_name, fields):
    pass

orchestrator._emit_langfuse = _no_op_langfuse
print("_emit_langfuse neutralizada.")

from core.pipeline_state import initial_state

state = initial_state(
    trace_id="test-sin-checkpointer",
    pipeline_run_id="run-test-sin-checkpointer",
    sigma_variant="Full",
    data_path="./data/tirendaz.csv",
)

print("Compilando el grafo SIN checkpointer (checkpointer=None)...")
print()

# Sin 'with get_checkpointer()' -- checkpointer=None directo.
graph = orchestrator.build_graph(checkpointer=None)

t0 = time.monotonic()
result = graph.invoke(state)
print(f"\nTiempo total del nodo 0000: {time.monotonic() - t0:.2f}s")
print(f"pipeline_status: {result.get('pipeline_status')}")
