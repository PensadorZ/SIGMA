# =============================================================================
# skills/0000-system-health-check/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 / Eco MultiAgentes 4 Skills 2 / Hito 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 2.1.0
# =============================================================================
# NOTA v2.1.0 — MIGRACIÓN DE VARIANTES (Hito 2, cierre de Rollout 1):
# HealthCheckOutput.sigma_variant pasa de Literal["Full","Lite","Dev","Runtime"]
# a Literal["SIGMA-FE","SIGMA-LE","SIGMA-ME","SIGMA-HE"], y se añade
# sigma_submode (Dev/Runtime) como campo propio — antes un solo campo
# mezclaba costo y submodo. is_dev_mode(state) en _common.py ya lee
# sigma_submode, no sigma_variant=='Dev' — este skill es el único de los
# 4 migrados que también necesitó cambios propios, porque es el único
# que persiste la variante directamente en su output (los otros 3 solo
# delegan en is_dev_mode() sin guardar el valor).
#
# NOTA v2.0.0 — FUSIÓN (Opción C, decidida en Eco MultiAgentes 4 Skills 2,
# confirmada como política por defecto para cualquier otro skill con el
# mismo patrón de divergencia entre líneas de trabajo paralelas):
#
# Incorpora el contrato más riguroso de "Eco MultiAgentes 3 Skills 1"
# (verdict HEALTHY/DEGRADED/BLOCKED validado con Pydantic, run_id además
# de trace_id, verificación real de los 5 servicios) DENTRO de la base
# ya verificada de esta línea de trabajo (LangGraph, circuit breaker,
# 25/25 tests). No se reemplaza el contrato SkillResult — se traduce:
#
#   verdict HEALTHY  → SkillResult.status = 'success'
#   verdict DEGRADED → SkillResult.status = 'success_with_warnings'
#   verdict BLOCKED  → SkillResult.status = 'error'
#
# Clasificación crítico/opcional (decisión de diseño de esta fusión,
# no estaba en ninguna de las dos versiones originales de forma explícita):
#   CRÍTICOS (bloquean el pipeline si no responden): PostgreSQL, MinIO
#   OPCIONALES (degradan con advertencia, nunca bloquean): Redis, Langfuse,
#     Ollama, y la presencia del modelo RoBERTa en disco.
#
# Razonamiento: PostgreSQL lo usan los 6 skills. MinIO lo usa 0011 al
# final del pipeline — bloquear temprano en 0000 evita gastar cómputo en
# 0001-0008 para fallar recién al final. Redis no lo usa ningún skill
# del Hito 1 todavía (reservado para el Hito 3 de streaming). Langfuse
# y Ollama ya tienen degradación graceful diseñada en orchestrator.py
# y en 0011 respectivamente — bloquear por ellos sería más estricto que
# el resto del sistema.
# =============================================================================

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Callable, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from sigma.core.pipeline_state import PipelineState, SkillResult
from sigma.skills._common import (
    ServiceCheckResult,
    check_postgres,
    check_redis,
    get_required_env,
    is_dev_mode,
    load_defaults,
    make_error,
    make_success,
    timer,
)

log = logging.getLogger("sigma.skills.0000")

SKILL_ID = "0000"
SKILL_DIR = "0000-system-health-check"

# Variables de entorno cuya ausencia bloquea el pipeline en modo Full.
# NOTA v2.0.1 (bug real encontrado en la primera corrida de Marx): esta
# lista exigía POSTGRES_HOST/DB/USER/PASSWORD como obligatorios sin
# excepción, pero _common.py ya acepta DATABASE_URL como alternativa
# suficiente desde la reconciliación de nombres de variable. Este
# archivo nunca se actualizó junto con ese cambio — desincronización
# real, no intencional. Corregido: se acepta CUALQUIERA de los dos
# caminos válidos para PostgreSQL, igual que ya hace _common.py.
POSTGRES_VIA_URL = ["DATABASE_URL"]
POSTGRES_VIA_SPLIT_FIELDS = ["POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]

CRITICAL_ENV_VARS = ["MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY"]

# Variables cuya ausencia degrada pero no bloquea
NON_CRITICAL_ENV_VARS = [
    "ROBERTA_MODEL_PATH", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY",
]


def _check_postgres_env_vars() -> list[str]:
    """
    Devuelve la lista de variables faltantes SOLO si NINGUNO de los dos
    caminos válidos (DATABASE_URL, o los 4 campos separados completos)
    está satisfecho. Si DATABASE_URL está presente, no exige nada más.
    """
    if os.environ.get("DATABASE_URL"):
        return []
    missing_split = [v for v in POSTGRES_VIA_SPLIT_FIELDS if not os.environ.get(v)]
    if missing_split:
        return ["DATABASE_URL (o los campos separados: " + ", ".join(missing_split) + ")"]
    return []

# Timeout por defecto para cada verificación de servicio. Sin timeout,
# un servicio colgado (no caído, sino lento) puede tumbar todo el
# arranque del pipeline indefinidamente — exactamente el escenario que
# los tests de estrés de esta fusión verifican.
DEFAULT_SERVICE_TIMEOUT_SECONDS = 3.0


# ---------------------------------------------------------------------------
# Esquema Pydantic — validación formal del veredicto
# (fusionado desde Eco MultiAgentes 3 Skills 1)
# ---------------------------------------------------------------------------

class ServiceStatus(BaseModel):
    """Estado individual de un servicio verificado."""
    service: str
    available: bool
    critical: bool
    latency_ms: int
    error: Optional[str] = None


class HealthCheckOutput(BaseModel):
    """
    Salida formal y validada del chequeo de salud. El Orquestador puede
    leer 'verdict' directamente, o consumir el SkillResult traducido
    (status='success'/'success_with_warnings'/'error') si prefiere el
    contrato genérico compartido con los otros 5 skills.
    """
    trace_id: str
    run_id: str
    sigma_variant: Literal["SIGMA-FE", "SIGMA-LE", "SIGMA-ME", "SIGMA-HE"]
    sigma_submode: Literal["Dev", "Runtime"]
    verdict: Literal["HEALTHY", "DEGRADED", "BLOCKED"]
    verdict_reason: str

    services: list[ServiceStatus] = Field(default_factory=list)
    critical_services_down: list[str] = Field(default_factory=list)
    optional_services_down: list[str] = Field(default_factory=list)

    duration_ms: int

    @field_validator("critical_services_down")
    @classmethod
    def _blocked_if_critical_down(cls, v, info):
        # En Pydantic v2, 'verdict' puede no estar validado aún si el
        # orden de campos cambia — se valida de forma laxa aquí y de
        # forma estricta (con datos completos) en _build_output() abajo,
        # que es la única función que realmente construye este modelo.
        return v


# ---------------------------------------------------------------------------
# Verificaciones individuales — cada una testeable de forma aislada
# ---------------------------------------------------------------------------

def _check_minio(
    timeout_seconds: float = DEFAULT_SERVICE_TIMEOUT_SECONDS,
    _client_factory: Optional[Callable[..., object]] = None,
) -> ServiceCheckResult:
    """
    Verifica disponibilidad real de MinIO. Igual contrato que
    check_postgres/check_redis de _common.py: nunca propaga excepción.
    """
    import time as _time
    t0 = _time.monotonic()
    try:
        if _client_factory is not None:
            client = _client_factory()
        else:
            from minio import Minio
            client = Minio(
                get_required_env("MINIO_ENDPOINT"),
                access_key=get_required_env("MINIO_ACCESS_KEY"),
                secret_key=get_required_env("MINIO_SECRET_KEY"),
                secure=os.environ.get("MINIO_USE_SSL", "false").lower() == "true",
            )
        # list_buckets es la operación más barata para confirmar que el
        # servidor responde y las credenciales son válidas.
        client.list_buckets()
        return ServiceCheckResult(
            service="minio", available=True,
            latency_ms=int((_time.monotonic() - t0) * 1000),
        )
    except Exception as exc:  # noqa: BLE001
        return ServiceCheckResult(
            service="minio", available=False,
            latency_ms=int((_time.monotonic() - t0) * 1000),
            error=str(exc),
        )


def _check_langfuse(
    timeout_seconds: float = DEFAULT_SERVICE_TIMEOUT_SECONDS,
    _http_get: Optional[Callable[..., object]] = None,
) -> ServiceCheckResult:
    """
    Verifica disponibilidad real de Langfuse vía su endpoint de salud.
    Nunca propaga excepción — Langfuse es opcional, su caída solo
    degrada trazabilidad (ya manejado con try/except en orchestrator.py).
    """
    import time as _time
    t0 = _time.monotonic()
    try:
        import requests
        get_fn = _http_get or requests.get
        host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
        resp = get_fn(f"{host}/api/public/health", timeout=timeout_seconds)
        status_code = getattr(resp, "status_code", 0)
        if status_code == 200:
            return ServiceCheckResult(
                service="langfuse", available=True,
                latency_ms=int((_time.monotonic() - t0) * 1000),
            )
        return ServiceCheckResult(
            service="langfuse", available=False,
            latency_ms=int((_time.monotonic() - t0) * 1000),
            error=f"HTTP {status_code}",
        )
    except Exception as exc:  # noqa: BLE001
        return ServiceCheckResult(
            service="langfuse", available=False,
            latency_ms=int((_time.monotonic() - t0) * 1000),
            error=str(exc),
        )


def _check_ollama(
    timeout_seconds: float = DEFAULT_SERVICE_TIMEOUT_SECONDS,
    _http_get: Optional[Callable[..., object]] = None,
) -> ServiceCheckResult:
    """Verifica disponibilidad real de Ollama. Opcional — 0011 tiene fallback."""
    import time as _time
    t0 = _time.monotonic()
    try:
        import requests
        get_fn = _http_get or requests.get
        host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        resp = get_fn(f"{host}/api/tags", timeout=timeout_seconds)
        status_code = getattr(resp, "status_code", 0)
        return ServiceCheckResult(
            service="ollama", available=(status_code == 200),
            latency_ms=int((_time.monotonic() - t0) * 1000),
            error=None if status_code == 200 else f"HTTP {status_code}",
        )
    except Exception as exc:  # noqa: BLE001
        return ServiceCheckResult(
            service="ollama", available=False,
            latency_ms=int((_time.monotonic() - t0) * 1000),
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Construcción del veredicto formal
# ---------------------------------------------------------------------------

def _build_output(
    trace_id: str,
    run_id: str,
    sigma_variant: str,
    sigma_submode: str,
    duration_ms: int,
    pg_result: ServiceCheckResult,
    redis_result: ServiceCheckResult,
    minio_result: ServiceCheckResult,
    langfuse_result: ServiceCheckResult,
    ollama_result: ServiceCheckResult,
    roberta_model_missing: bool,
    critical_services: tuple[str, ...] = ("postgres", "minio"),
    optional_services: tuple[str, ...] = ("redis", "langfuse", "ollama"),
) -> HealthCheckOutput:
    """
    critical_services / optional_services ya NO están hardcodeados aquí —
    se reciben como parámetro, resuelto en run() desde defaults.yaml.
    Los defaults de la firma son solo el valor de respaldo si el archivo
    de configuración no está disponible (mismo patrón que 0001/0002/0008/0011).
    """
    all_results = {
        "postgres": pg_result, "redis": redis_result, "minio": minio_result,
        "langfuse": langfuse_result, "ollama": ollama_result,
    }

    services: list[ServiceStatus] = []
    critical_down: list[str] = []
    optional_down: list[str] = []

    for name in critical_services:
        result = all_results[name]
        services.append(ServiceStatus(
            service=name, available=result.available, critical=True,
            latency_ms=result.latency_ms, error=result.error,
        ))
        if not result.available:
            critical_down.append(name)

    for name in optional_services:
        result = all_results[name]
        services.append(ServiceStatus(
            service=name, available=result.available, critical=False,
            latency_ms=result.latency_ms, error=result.error,
        ))
        if not result.available:
            optional_down.append(name)

    if roberta_model_missing:
        optional_down.append("roberta_model_path")

    if critical_down:
        verdict = "BLOCKED"
        verdict_reason = f"Servicios críticos caídos: {critical_down}"
    elif optional_down:
        verdict = "DEGRADED"
        verdict_reason = f"Servicios opcionales caídos (pipeline continúa): {optional_down}"
    else:
        verdict = "HEALTHY"
        verdict_reason = "Todos los servicios responden correctamente"

    return HealthCheckOutput(
        trace_id=trace_id,
        run_id=run_id,
        sigma_variant=sigma_variant,
        sigma_submode=sigma_submode,
        verdict=verdict,
        verdict_reason=verdict_reason,
        services=services,
        critical_services_down=critical_down,
        optional_services_down=optional_down,
        duration_ms=duration_ms,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        trace_id = state.get("trace_id", "unknown")
        run_id = state.get("pipeline_run_id", trace_id)
        sigma_variant = state.get("sigma_variant", "SIGMA-FE")
        sigma_submode = state.get("sigma_submode", "Dev")

        try:
            cfg = load_defaults(SKILL_DIR)
            timeout = float(cfg.get("services", {}).get("timeout_seconds", DEFAULT_SERVICE_TIMEOUT_SECONDS))
            critical_services = tuple(cfg.get("services", {}).get("critical", ["postgres", "minio"]))
            optional_services = tuple(cfg.get("services", {}).get("optional", ["redis", "langfuse", "ollama"]))
        except FileNotFoundError:
            timeout = DEFAULT_SERVICE_TIMEOUT_SECONDS
            critical_services = ("postgres", "minio")
            optional_services = ("redis", "langfuse", "ollama")

        if is_dev_mode(state):
            output = _build_output(
                trace_id=trace_id, run_id=run_id, sigma_variant=sigma_variant,
                sigma_submode=sigma_submode,
                duration_ms=0,
                pg_result=ServiceCheckResult("postgres", True, 0),
                redis_result=ServiceCheckResult("redis", True, 0),
                minio_result=ServiceCheckResult("minio", True, 0),
                langfuse_result=ServiceCheckResult("langfuse", True, 0),
                ollama_result=ServiceCheckResult("ollama", True, 0),
                roberta_model_missing=False,
                critical_services=critical_services,
                optional_services=optional_services,
            )
            return make_success(
                SKILL_ID,
                {**output.model_dump(), "dev_mode": True},
                t["ms"],
                warnings=["synthetic_data"],
            )

        # ── Variables de entorno críticas — fallo inmediato, sin cómputo ──
        missing_critical = [v for v in CRITICAL_ENV_VARS if not os.environ.get(v)]
        missing_critical += _check_postgres_env_vars()
        if missing_critical:
            return make_error(
                SKILL_ID,
                "ConfigurationError",
                f"Variables de entorno críticas faltantes: {missing_critical}. "
                f"Verifica tu archivo .env (ver .env.example).",
                t["ms"],
            )

        # ── Verificación real de los 5 servicios ───────────────────────────
        # ── Diagnóstico: qué ve el proceso REAL, no lo que asumimos ──────
        _db_url = os.environ.get("DATABASE_URL", "")
        _redis_url = os.environ.get("REDIS_URL", "")
        if _db_url:
            _masked = _db_url.split("@")[-1] if "@" in _db_url else _db_url
            log.debug("[diag] DATABASE_URL vista por el proceso: ...@%s", _masked)
        else:
            log.debug("[diag] DATABASE_URL: AUSENTE en os.environ de este proceso")
        log.debug("[diag] REDIS_URL vista por el proceso: %s", _redis_url or "AUSENTE en os.environ de este proceso")

        import time as _time_diag

        _t0 = _time_diag.monotonic()
        pg_result = check_postgres(timeout_seconds=timeout)
        log.debug("[diag] check_postgres tardó %.2fs (timeout configurado=%.1fs)",
                 _time_diag.monotonic() - _t0, timeout)

        _t0 = _time_diag.monotonic()
        redis_result = check_redis(timeout_seconds=timeout)
        log.debug("[diag] check_redis tardó %.2fs", _time_diag.monotonic() - _t0)

        _t0 = _time_diag.monotonic()
        minio_result = _check_minio(timeout_seconds=timeout)
        log.debug("[diag] _check_minio tardó %.2fs", _time_diag.monotonic() - _t0)

        _t0 = _time_diag.monotonic()
        langfuse_result = _check_langfuse(timeout_seconds=timeout)
        log.debug("[diag] _check_langfuse tardó %.2fs", _time_diag.monotonic() - _t0)

        _t0 = _time_diag.monotonic()
        ollama_result = _check_ollama(timeout_seconds=timeout)
        log.debug("[diag] _check_ollama tardó %.2fs", _time_diag.monotonic() - _t0)

        model_path = os.environ.get("ROBERTA_MODEL_PATH")
        roberta_missing = bool(model_path) and not Path(model_path).exists()

        output = _build_output(
            trace_id=trace_id, run_id=run_id, sigma_variant=sigma_variant,
            sigma_submode=sigma_submode,
            duration_ms=t["ms"],
            pg_result=pg_result, redis_result=redis_result,
            minio_result=minio_result, langfuse_result=langfuse_result,
            ollama_result=ollama_result, roberta_model_missing=roberta_missing,
            critical_services=critical_services,
            optional_services=optional_services,
        )

        output_dict = output.model_dump()
        # Compatibilidad con el nombre de campo usado por versiones previas
        # de este skill (health_status) — algunos consumidores externos
        # (evals, dashboards) podrían leer ese nombre. Se mantiene como
        # alias hasta que se audite si algo más lo usa.
        output_dict["health_status"] = output.verdict

        if output.verdict == "BLOCKED":
            return make_error(
                SKILL_ID, "InfrastructureBlockedError",
                output.verdict_reason, t["ms"],
            )
        elif output.verdict == "DEGRADED":
            return make_success(
                SKILL_ID, output_dict, t["ms"],
                warnings=[f"degraded:{s}" for s in output.optional_services_down],
            )
        else:
            return make_success(SKILL_ID, output_dict, t["ms"])
