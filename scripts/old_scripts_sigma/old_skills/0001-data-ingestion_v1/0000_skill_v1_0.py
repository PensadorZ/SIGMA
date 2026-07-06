# =============================================================================
# skills/0000-system-health-check/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA v1.0.1: Reubicado desde skills/s0000_system_health_check.py (flat) a esta carpeta,
#   siguiendo la convención ya establecida en Eco MultiAgentes 3 Skills 1:
#   'skill.py files in skills/000X-name/'. La resolución de import se
#   hace por ruta de archivo (importlib.util), no por paquete Python,
#   porque '000X-nombre-con-guion' no es un identificador válido.
# Implementación Python del skill 0000-system-health-check.
# Ver skills/0000-system-health-check/SKILL.md para el contrato completo.
#
# Estados verificados: HEALTHY, DEGRADED, BLOCKED (mapeados a SkillResult):
#   HEALTHY  → status='success'
#   DEGRADED → status='success_with_warnings'
#   BLOCKED  → status='error'
# =============================================================================

from __future__ import annotations

import logging
import os
from pathlib import Path

from core.pipeline_state import PipelineState, SkillResult
from skills._common import (
    get_pg_connection,
    get_required_env,
    is_dev_mode,
    make_error,
    make_success,
    timer,
)

log = logging.getLogger("sigma.skills.0000")

SKILL_ID = "0000"

# Variables de entorno cuya ausencia bloquea el pipeline en modo Full
CRITICAL_ENV_VARS = [
    "POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD",
    "MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY",
]

# Variables cuya ausencia degrada pero no bloquea (afectan solo a 0011)
NON_CRITICAL_ENV_VARS = [
    "ROBERTA_MODEL_PATH", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY",
]


def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        if is_dev_mode(state):
            return make_success(
                SKILL_ID,
                {
                    "health_status": "HEALTHY",
                    "dev_mode": True,
                    "checks_performed": [],
                },
                t["ms"],
                warnings=["synthetic_data"],
            )

        warnings: list[str] = []

        # ── 1. Variables de entorno críticas ────────────────────────────
        missing_critical = [v for v in CRITICAL_ENV_VARS if not os.environ.get(v)]
        if missing_critical:
            return make_error(
                SKILL_ID,
                "ConfigurationError",
                f"Variables de entorno críticas faltantes: {missing_critical}. "
                f"Verifica tu archivo .env (ver .env.example).",
                t["ms"],
            )

        # ── 2. Variables no críticas (degradan, no bloquean) ────────────
        missing_non_critical = [v for v in NON_CRITICAL_ENV_VARS if not os.environ.get(v)]
        if missing_non_critical:
            warnings.append(f"missing_non_critical_env:{missing_non_critical}")

        # ── 3. Conectividad PostgreSQL ───────────────────────────────────
        try:
            conn = get_pg_connection(state)
            conn.close()
        except Exception as exc:  # noqa: BLE001
            return make_error(
                SKILL_ID,
                "ConfigurationError",
                f"No se pudo conectar a PostgreSQL: {exc}",
                t["ms"],
            )

        # ── 4. Modelo RoBERTa presente en disco ─────────────────────────
        model_path = os.environ.get("ROBERTA_MODEL_PATH")
        if model_path and not Path(model_path).exists():
            warnings.append("roberta_model_not_found_at_configured_path")

        # ── 5. Ollama disponible (solo advertencia, 0011 tiene fallback) ─
        try:
            import requests
            ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            resp = requests.get(f"{ollama_host}/api/tags", timeout=3)
            if resp.status_code != 200:
                warnings.append("ollama_not_responding")
        except Exception:  # noqa: BLE001
            warnings.append("ollama_not_reachable")

        health_status = "DEGRADED" if warnings else "HEALTHY"

        return make_success(
            SKILL_ID,
            {
                "health_status": health_status,
                "dev_mode": False,
                "checks_performed": [
                    "env_vars_critical", "env_vars_non_critical",
                    "postgres_connectivity", "roberta_model_path", "ollama_reachable",
                ],
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
