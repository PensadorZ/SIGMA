# =============================================================================
# skills/_common.py — Utilidades compartidas por los stubs de skills
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.0.0
# =============================================================================
# No es un skill en sí — es infraestructura compartida para que cada
# skill no repita: carga de defaults.yaml, conexión a PostgreSQL,
# construcción de SkillResult, medición de tiempo y logging homogéneo.
# =============================================================================

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

import yaml

from core.pipeline_state import PipelineState, SkillResult

log = logging.getLogger("sigma.skills")


# ---------------------------------------------------------------------------
# Carga de defaults.yaml
# ---------------------------------------------------------------------------

_SKILLS_ROOT = Path(__file__).parent.parent / "skills"


def load_defaults(skill_dir: str) -> dict[str, Any]:
    """
    Carga defaults.yaml del skill indicado, expandiendo variables de
    entorno con sintaxis ${VAR:-default}.

    Args:
        skill_dir: nombre exacto de la carpeta, ej. '0008-sentiment-analyzer'.
    """
    path = _SKILLS_ROOT / skill_dir / "defaults.yaml"
    raw_text = path.read_text(encoding="utf-8")
    expanded = _expand_env_vars(raw_text)
    return yaml.safe_load(expanded)


def _expand_env_vars(text: str) -> str:
    """
    Expande ${VAR:-default} y ${VAR} en texto YAML crudo, similar a bash.
    No usa os.path.expandvars porque este no soporta la sintaxis :-default.
    """
    import re

    pattern = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(:-([^}]*))?\}")

    def _replace(match: "re.Match[str]") -> str:
        var_name = match.group(1)
        default = match.group(3) or ""
        return os.environ.get(var_name, default)

    return pattern.sub(_replace, text)


# ---------------------------------------------------------------------------
# Timer — medición de duración
# ---------------------------------------------------------------------------

@contextmanager
def timer() -> Iterator[dict[str, int]]:
    """
    Context manager que mide duración en milisegundos.
    Uso:
        with timer() as t:
            ... trabajo ...
        duration = t["ms"]
    """
    box = {"ms": 0}
    t0 = time.monotonic()
    try:
        yield box
    finally:
        box["ms"] = int((time.monotonic() - t0) * 1000)


# ---------------------------------------------------------------------------
# Constructor de SkillResult
# ---------------------------------------------------------------------------

def make_success(
    skill_id: str,
    output: dict[str, Any],
    duration_ms: int,
    warnings: Optional[list[str]] = None,
) -> SkillResult:
    status = "success_with_warnings" if warnings else "success"
    if warnings:
        output = {**output, "warnings": warnings}
    return SkillResult(
        skill_id=skill_id,
        status=status,
        output=output,
        error_type=None,
        error_detail=None,
        error_category=None,
        duration_ms=duration_ms,
        retries_attempted=0,
    )


def make_error(
    skill_id: str,
    error_type: str,
    error_detail: str,
    duration_ms: int,
) -> SkillResult:
    return SkillResult(
        skill_id=skill_id,
        status="error",
        output={},
        error_type=error_type,
        error_detail=error_detail,
        error_category=None,  # el orquestador lo clasifica con classify_error()
        duration_ms=duration_ms,
        retries_attempted=0,
    )


# ---------------------------------------------------------------------------
# Conexión a PostgreSQL — respeta modo Dev (sin conexión real)
# ---------------------------------------------------------------------------

def get_required_env(key: str) -> str:
    """
    Obtiene una variable de entorno obligatoria (ADR-010).
    Lanza ValueError inmediato si falta — principio de fallo rápido.
    """
    value = os.environ.get(key)
    if not value:
        raise ValueError(
            f"Falta variable de entorno requerida: '{key}'. "
            f"Verifica tu archivo .env (ver .env.example)."
        )
    return value


def get_pg_connection(state: PipelineState):
    """
    Devuelve una conexión psycopg2 a PostgreSQL.
    Solo debe llamarse cuando sigma_variant != 'Dev'.
    """
    import psycopg2

    dsn = os.environ.get("POSTGRES_DSN")
    if dsn:
        return psycopg2.connect(dsn)

    return psycopg2.connect(
        host=get_required_env("POSTGRES_HOST"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=get_required_env("POSTGRES_DB"),
        user=get_required_env("POSTGRES_USER"),
        password=get_required_env("POSTGRES_PASSWORD"),
    )


def is_dev_mode(state: PipelineState) -> bool:
    """Determina si el skill debe operar en modo Dev (datos sintéticos)."""
    return state.get("sigma_variant", "Full") == "Dev"
