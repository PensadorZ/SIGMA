# =============================================================================
# director_main.py
# SIGMA v1.5 · Hito 2, Rollout 1
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.0.0
# =============================================================================
# Punto de entrada delgado — reemplaza a orchestrator.py (Hito 1,
# archivado como scripts/old_scripts_sigma/orchestrator_hito1_v1.0.py,
# nombre confirmado). Nombre confirmado tras descartar director_h2,
# director_upstream y director_p1 — "director_main" no requiere
# renombrarse en cada Rollout futuro.
#
# Toda la lógica real vive en sigma/core/director.py — este archivo solo
# resuelve CLI, IDs de trazabilidad, y el ciclo de vida del checkpointer.
# =============================================================================

from __future__ import annotations

import argparse
import logging
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.environ.get("SIGMA_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("sigma.director_main")

from sigma.core.checkpointer import get_checkpointer
from sigma.core.director import build_director_graph, build_initial_director_state
from sigma.core.tracing import _get_backend, emit_trace_event


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SIGMA Director — Rollout 1 (Engineer Datos)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python director_main.py --variant Full --data-path ./data/tirendaz.csv\n"
            "  python director_main.py --variant Dev  --data-path ./data/tirendaz.csv\n"
        ),
    )
    # NOTA: se mantiene el esquema --variant {Full,Lite,Dev,Runtime} tal
    # cual, sin migrar a SIGMA-FE/LE/ME/HE + --submode todavía — esa
    # migración quedó agendada explícitamente para el cierre de Rollout 1,
    # en el mismo commit que el fix de pipeline_state.py (ver Plan
    # Operativo). Este archivo hereda la decisión de orchestrator.py
    # v1.1.0 sin cambiarla por su cuenta.
    parser.add_argument(
        "--variant",
        choices=["Full", "Lite", "Dev", "Runtime"],
        default="Full",
        help="Variante SIGMA a usar (default: Full) — esquema pendiente de migrar, ver nota arriba",
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="Ruta al dataset CSV de entrada (ej. ./data/tirendaz.csv)",
    )
    args = parser.parse_args()

    run_uuid = uuid.uuid4().hex[:8]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    trace_id = f"sigma-{ts}-{run_uuid}"
    pipeline_run_id = f"run-{ts}-{run_uuid}"

    log.info("=" * 60)
    log.info("SIGMA Director — Rollout 1 (Engineer Datos)")
    log.info("trace_id       : %s", trace_id)
    log.info("pipeline_run_id: %s", pipeline_run_id)
    log.info("sigma_variant  : %s", args.variant)
    log.info("data_path      : %s", args.data_path)
    log.info("=" * 60)

    director_state = build_initial_director_state(
        trace_id=trace_id,
        pipeline_run_id=pipeline_run_id,
        sigma_variant=args.variant,
        data_path=args.data_path,
    )

    emit_trace_event("director.start", trace_id, sigma_variant=args.variant, data_path=args.data_path)

    with get_checkpointer() as checkpointer:
        compiled_director = build_director_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": trace_id}}
        final_state = compiled_director.invoke(director_state, config=config)

        if "__interrupt__" in final_state:
            log.info("=" * 60)
            log.info("[resultado] ⏸  Pipeline PAUSADO — esperando decisión humana en Zulip")
            log.info("[resultado]    trace_id: %s", trace_id)
            log.info("[resultado]    Responde en Zulip (canal Sigma-Approval) para reanudar.")
            log.info("[resultado]    Este proceso puede terminar con seguridad — el estado")
            log.info("[resultado]    ya está persistido en sigma_checkpoints.sqlite.")
            log.info("=" * 60)
            return

    if final_state["director_status"] == "success":
        log.info("[resultado] ✓ Director completado exitosamente")
        log.info("[resultado]   dashboard_url : %s", final_state.get("dashboard_url"))
        log.info("[resultado]   warnings      : %s", final_state["warnings"])
    else:
        failed = final_state.get("failed_engineer_id", "desconocido")
        log.error("[resultado] ✗ Director fallido en Engineer %s", failed)
        raise SystemExit(1)
    from sigma.core.tracing import _get_backend
    _get_backend()._langfuse_client.flush()


if __name__ == "__main__":
    main()
