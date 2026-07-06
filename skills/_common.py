# =============================================================================
# skills/_common.py — Utilidades compartidas por los stubs de skills
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 / Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.1.0
# =============================================================================
# No es un skill en sí — es infraestructura compartida para que cada
# skill no repita: carga de defaults.yaml, conexión a PostgreSQL/Redis,
# construcción de SkillResult, medición de tiempo y logging homogéneo.
#
# NOTA v1.1.0 — FUSIÓN (Opción 3, decidida en Eco MultiAgentes 4 Skills 2):
# Este archivo incorpora la capa de clientes reales de infraestructura que
# se construyó originalmente en sigma/core/connections.py durante
# Eco MultiAgentes 3 Skills 1 (ServiceCheckResult, chequeo real de
# PostgreSQL y Redis con psycopg2/redis-py). Se fusiona aquí, no se deja
# como módulo separado, porque _common.py ya es el punto único de
# infraestructura compartida que todos los skill.py importan — mantener
# dos módulos de infraestructura (sigma/core/ y skills/_common.py) es
# exactamente el tipo de duplicación de namespace que esta fusión existe
# para eliminar.
#
# get_pg_connection() conserva su firma original get_pg_connection(state)
# para no romper los skill.py ni los tests ya verificados (14/14 pasan) —
# el timeout y el retry se añadieron POR DENTRO, como mejora transparente,
# no como cambio de contrato.
# =============================================================================

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

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
# Variables de entorno obligatorias (ADR-010)
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


def is_dev_mode(state: PipelineState) -> bool:
    """Determina si el skill debe operar en modo Dev (datos sintéticos)."""
    return state.get("sigma_variant", "Full") == "Dev"


# ---------------------------------------------------------------------------
# ServiceCheckResult — resultado uniforme de verificación de infraestructura
# (fusionado desde sigma/core/connections.py, Eco MultiAgentes 3 Skills 1)
# ---------------------------------------------------------------------------

@dataclass
class ServiceCheckResult:
    """
    Resultado de verificar la disponibilidad real de un servicio de
    infraestructura (PostgreSQL, Redis, MinIO, Ollama). Usado por
    0000-system-health-check y por cualquier skill que necesite degradar
    su comportamiento en lugar de fallar duro ante un servicio caído.
    """
    service: str
    available: bool
    latency_ms: int
    error: Optional[str] = None


def check_postgres(
    timeout_seconds: float = 3.0,
    _connector: Optional[Callable[..., Any]] = None,
) -> ServiceCheckResult:
    """
    Verifica disponibilidad real de PostgreSQL sin lanzar excepción —
    a diferencia de get_pg_connection(), esta función SIEMPRE devuelve
    un ServiceCheckResult, nunca propaga la excepción del driver.
    Pensada para 0000-system-health-check y para decisiones de
    degradación (DEGRADED vs BLOCKED), no para obtener una conexión
    usable — para eso usa get_pg_connection().

    Args:
        timeout_seconds: tiempo máximo de espera de conexión.
        _connector: solo para pruebas — permite inyectar un conector falso
                    sin monkeypatchear psycopg2 globalmente.
    """
    import psycopg2

    connector = _connector or psycopg2.connect
    t0 = time.monotonic()
    try:
        # DATABASE_URL es el nombre real usado en el .env de Marx.
        # POSTGRES_DSN se mantiene como alias de compatibilidad.
        dsn = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_DSN")
        if dsn:
            conn = connector(dsn, connect_timeout=int(timeout_seconds))
        else:
            conn = connector(
                host=os.environ.get("POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                dbname=os.environ.get("POSTGRES_DB", ""),
                user=os.environ.get("POSTGRES_USER", ""),
                password=os.environ.get("POSTGRES_PASSWORD", ""),
                connect_timeout=int(timeout_seconds),
            )
        conn.close()
        return ServiceCheckResult(
            service="postgres", available=True,
            latency_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:  # noqa: BLE001
        return ServiceCheckResult(
            service="postgres", available=False,
            latency_ms=int((time.monotonic() - t0) * 1000),
            error=str(exc),
        )


def check_redis(
    timeout_seconds: float = 3.0,
    _connector: Optional[Callable[..., Any]] = None,
) -> ServiceCheckResult:
    """
    Verifica disponibilidad real de Redis sin lanzar excepción.
    Mismo contrato que check_postgres(): siempre devuelve
    ServiceCheckResult, nunca propaga.
    """
    import redis as redis_lib

    connector = _connector or redis_lib.Redis
    t0 = time.monotonic()
    try:
        # REDIS_URL es el nombre real usado en el .env de Marx.
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            client = connector.from_url(
                redis_url, socket_connect_timeout=timeout_seconds, socket_timeout=timeout_seconds,
            )
        else:
            client = connector(
                host=os.environ.get("REDIS_HOST", "localhost"),
                port=int(os.environ.get("REDIS_PORT", "6379")),
                password=os.environ.get("REDIS_PASSWORD") or None,
                db=int(os.environ.get("REDIS_DB", "0")),
                socket_connect_timeout=timeout_seconds,
                socket_timeout=timeout_seconds,
            )
        client.ping()
        return ServiceCheckResult(
            service="redis", available=True,
            latency_ms=int((time.monotonic() - t0) * 1000),
        )
    except Exception as exc:  # noqa: BLE001
        return ServiceCheckResult(
            service="redis", available=False,
            latency_ms=int((time.monotonic() - t0) * 1000),
            error=str(exc),
        )


def get_redis_connection(_connector: Optional[Callable[..., Any]] = None):
    """
    Devuelve un cliente Redis real y usable (a diferencia de check_redis,
    que solo verifica y nunca propaga). Lanza la excepción del driver si
    la conexión falla — el llamador decide cómo manejarla.
    """
    import redis as redis_lib

    connector = _connector or redis_lib.Redis
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        return connector.from_url(redis_url, socket_connect_timeout=5, socket_timeout=5)
    return connector(
        host=get_required_env("REDIS_HOST") if os.environ.get("REDIS_HOST") is None
        else os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        password=os.environ.get("REDIS_PASSWORD") or None,
        db=int(os.environ.get("REDIS_DB", "0")),
        socket_connect_timeout=5,
        socket_timeout=5,
    )


# ---------------------------------------------------------------------------
# Conexión a PostgreSQL — respeta modo Dev (sin conexión real)
# Mejorada con timeout + retry con backoff, firma sin cambios (state) → conn
# ---------------------------------------------------------------------------

# Errores de conexión considerados transitorios — dignos de reintento.
# Un error de autenticación o de base de datos inexistente NO se reintenta,
# porque reintentar no lo va a arreglar (mismo principio que el circuit
# breaker del orquestador: fallo rápido para errores no recuperables).
_TRANSIENT_PG_ERROR_MARKERS = (
    "could not connect",
    "connection refused",
    "timeout expired",
    "server closed the connection",
    "could not translate host name",
)


def _is_transient_pg_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(marker in msg for marker in _TRANSIENT_PG_ERROR_MARKERS)


def get_pg_connection(
    state: PipelineState,
    *,
    max_retries: int = 2,
    backoff_seconds: float = 2.0,
    connect_timeout: int = 5,
    _connector: Optional[Callable[..., Any]] = None,
):
    """
    Devuelve una conexión psycopg2 a PostgreSQL, con timeout de conexión
    y reintento con backoff ante errores transitorios (servicio caído
    momentáneamente, red lenta). Errores no transitorios (credenciales
    inválidas, base de datos inexistente) fallan de inmediato sin
    reintentar — mismo principio de fallo rápido que el circuit breaker
    de orchestrator.py.

    Firma compatible con el uso existente get_pg_connection(state) —
    los parámetros nuevos son keyword-only con default, así que ningún
    skill.py ni test existente necesita cambiar una sola línea.

    Solo debe llamarse cuando sigma_variant != 'Dev'.
    """
    import psycopg2

    connector = _connector or psycopg2.connect
    # DATABASE_URL es el nombre real usado en el .env de Marx.
    # POSTGRES_DSN se mantiene como alias de compatibilidad.
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_DSN")

    last_exc: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            if dsn:
                return connector(dsn, connect_timeout=connect_timeout)
            return connector(
                host=get_required_env("POSTGRES_HOST"),
                port=int(os.environ.get("POSTGRES_PORT", "5432")),
                dbname=get_required_env("POSTGRES_DB"),
                user=get_required_env("POSTGRES_USER"),
                password=get_required_env("POSTGRES_PASSWORD"),
                connect_timeout=connect_timeout,
            )
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if not _is_transient_pg_error(exc) or attempt >= max_retries:
                break
            wait = backoff_seconds * (attempt + 1)
            log.warning(
                "[get_pg_connection] intento %d/%d falló (%s) — "
                "reintentando en %.1fs",
                attempt + 1, max_retries + 1, exc, wait,
            )
            time.sleep(wait)

    raise ConnectionError(
        f"No se pudo conectar a PostgreSQL tras {max_retries + 1} intento(s): "
        f"{last_exc}"
    ) from last_exc
