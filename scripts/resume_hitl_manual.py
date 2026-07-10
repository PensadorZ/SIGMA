"""
resume_hitl.py — Reanuda manualmente una corrida pausada en HITL,
sin depender de Zulip. Uso de un solo caso: mientras el bot de Zulip
esté desactivado (ver Known limitations), este script cumple la misma
función que webhook_receiver.py cumpliría automáticamente.
"""
from sigma.core.checkpointer import resume_pipeline
from orchestrator import build_graph

TRACE_ID = "sigma-20260710-1ea00c31"
DECISION = True  # True = aprobar, False = rechazar

result = resume_pipeline(build_graph, TRACE_ID, DECISION)
print(result)