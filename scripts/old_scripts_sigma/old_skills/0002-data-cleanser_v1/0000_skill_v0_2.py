"""
skills/0000-system-health-check/skill.py

Implementación real del skill 0000-system-health-check.
Ver SKILL.md para la especificación completa (Gherkin, LTL, trazabilidad).

Verifica la disponibilidad de los servicios críticos y opcionales del
ecosistema SIGMA antes de que cualquier pipeline de datos arranque.
Emite uno de tres veredicts formales: HEALTHY, DEGRADED, BLOCKED.

Este es el primer skill.py ejecutable del catálogo SIGMA. Su simplicidad
es deliberada: no toca datos, solo verifica conectividad, lo que lo
convierte en el candidato correcto para ser el primer código real del
sistema (Fase 1.2 del Roadmap Técnico).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Literal

from sigma.core import (
    ContextResolutionError,
    check_langfuse,
    check_minio,
    check_ollama,
    check_postgresql,
    check_redis,
    emit_trace_event,
    get_required_env,
    get_sigma_variant,
    is_dev_mode,
)

Verdict = Literal["HEALTHY", "DEGRADED", "BLOCKED"]


class MissingConfigurationError(RuntimeError):
    """
    Se lanza cuando una variable de entorno crítica para identificar
    el servicio a verificar no está definida. Cierra el gap dejado
    abierto con pytest.skip() en la primera versión de este skill
    (ver AgDR-001, ítem 1 de ejecución confirmada).
    """


@dataclass
class ServiceStatusRecord:
    name: str
    category: Literal["critical", "conditional_critical", "optional"]
    status: Literal["UP", "DOWN", "SKIPPED"]
    response_ms: int | None = None
    error: str | None = None
    affected_skills: list[str] = field(default_factory=list)
    remediation_step: str | None = None


@dataclass
class HealthCheckResult:
    trace_id: str
    run_id: str
    sigma_variant: str
    verdict: Verdict
    verdict_reason: str
    services: list[ServiceStatusRecord]
    critical_services_up: list[str]
    critical_services_down: list[str]
    optional_services_down: list[str]
    affected_skills: list[str]
    duration_ms: int

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "sigma_variant": self.sigma_variant,
            "verdict": self.verdict,
            "verdict_reason": self.verdict_reason,
            "services": [
                {
                    "name": s.name,
                    "category": s.category,
                    "status": s.status,
                    "response_ms": s.response_ms,
                    "error": s.error,
                    "affected_skills": s.affected_skills,
                    "remediation_step": s.remediation_step,
                }
                for s in self.services
            ],
            "critical_services_up": self.critical_services_up,
            "critical_services_down": self.critical_services_down,
            "optional_services_down": self.optional_services_down,
            "affected_skills": self.affected_skills,
            "duration_ms": self.duration_ms,
        }


_REMEDIATION_STEPS = {
    "postgresql": (
        "Verifica que el contenedor de PostgreSQL esté corriendo: "
        "`docker compose ps postgresql`. Revisa POSTGRES_HOST/PORT en .env."
    ),
    "redis": (
        "Verifica que el contenedor de Redis esté corriendo: "
        "`docker compose ps redis`. Revisa REDIS_HOST/PORT en .env."
    ),
    "minio": (
        "Verifica que el contenedor de MinIO esté corriendo: "
        "`docker compose ps minio`. Revisa MINIO_ENDPOINT en .env."
    ),
    "langfuse": (
        "Verifica que Langfuse esté desplegado y accesible. "
        "Revisa LANGFUSE_HOST en .env. En SIGMA Dev este servicio es opcional."
    ),
    "ollama": (
        "Verifica que Ollama esté corriendo: `ollama serve`. "
        "Revisa OLLAMA_HOST en .env. Si no usas modelos locales, ignora esta alerta."
    ),
}


def _critical_services_for_variant(variant: str) -> set[str]:
    """
    Determina qué servicios son críticos según la variante activa
    (ADR-009 SIGMA_variants, defaults.yaml variant_overrides).

    En SIGMA Dev, MinIO y Langfuse se degradan a opcionales para no
    bloquear el desarrollo local (ver defaults.yaml: variant_overrides.Dev).
    """
    base_critical = {"postgresql", "redis", "minio"}
    if variant == "Dev":
        return {"postgresql", "redis"}
    return base_critical | {"langfuse"} if variant in ("Full", "Runtime") else base_critical


def _dev_demoted_services(variant: str) -> set[str]:
    """
    Servicios que en SIGMA Dev pasan de críticos a opcionales SIN que
    su caída produzca veredicto DEGRADED — son irrelevantes para el
    flujo de desarrollo local (ver SKILL.md, escenario "Modo Dev").
    Esto es distinto de un servicio "opcional universal" como Ollama,
    cuya caída SÍ debe reflejarse como DEGRADED en cualquier variante
    porque puede afectar skills que dependen de modelos locales.
    """
    if variant == "Dev":
        return {"minio", "langfuse"}
    return set()


def run_system_health_check(
    run_id: str | None = None,
    trace_id: str | None = None,
    db_timeout_ms: int = 3000,
    redis_timeout_ms: int = 1000,
    minio_timeout_ms: int = 2000,
    langfuse_timeout_ms: int = 3000,
    ollama_timeout_ms: int = 5000,
) -> HealthCheckResult:
    """
    Punto de entrada del skill. Ejecuta las verificaciones de todos los
    servicios y emite el veredicto formal.

    Implementa la trayectoria esperada declarada en SKILL.md:
        load_service_registry -> ping_critical_services ->
        ping_optional_services -> evaluate_verdict -> write_health_report
    """
    start = time.monotonic()
    run_id = run_id or f"hc-{uuid.uuid4().hex[:8]}"
    trace_id = trace_id or f"tr-{uuid.uuid4().hex[:8]}"

    # ── Validación de configuración requerida (fail-fast, ADR-006) ───────
    # Antes de verificar ningún servicio, confirma que las variables de
    # conexión mínimas existen. POSTGRES_URL es la variable canónica
    # esperada por el escenario "Variable de entorno faltante" del .feature.
    # Si no está, get_required_env lanza ContextResolutionError, que aquí
    # se traduce a MissingConfigurationError con el contrato exacto que
    # el .feature exige: mensaje indicando la variable faltante, sin
    # ejecutar ninguna verificación de servicio.
    try:
        get_required_env("POSTGRES_URL")
    except ContextResolutionError as exc:
        emit_trace_event(
            "health_check.configuration_error",
            trace_id=trace_id,
            run_id=run_id,
            missing_variable="POSTGRES_URL",
        )
        raise MissingConfigurationError(
            f"No se puede ejecutar system-health-check: falta configuración "
            f"requerida. {exc}"
        ) from exc

    variant = get_sigma_variant()

    emit_trace_event(
        "health_check.started",
        trace_id=trace_id,
        run_id=run_id,
        sigma_variant=variant,
    )

    # ── load_service_registry ────────────────────────────────────────────
    critical_set = _critical_services_for_variant(variant)

    # ── ping_critical_services + ping_optional_services ──────────────────
    services: list[ServiceStatusRecord] = []

    pg_result = check_postgresql(timeout_ms=db_timeout_ms)
    services.append(
        ServiceStatusRecord(
            name="postgresql",
            category="critical" if "postgresql" in critical_set else "optional",
            status=pg_result.status,
            response_ms=pg_result.response_ms,
            error=pg_result.error,
            remediation_step=_REMEDIATION_STEPS["postgresql"] if pg_result.status == "DOWN" else None,
        )
    )

    redis_result = check_redis(timeout_ms=redis_timeout_ms)
    services.append(
        ServiceStatusRecord(
            name="redis",
            category="critical" if "redis" in critical_set else "optional",
            status=redis_result.status,
            response_ms=redis_result.response_ms,
            error=redis_result.error,
            remediation_step=_REMEDIATION_STEPS["redis"] if redis_result.status == "DOWN" else None,
        )
    )

    minio_result = check_minio(timeout_ms=minio_timeout_ms)
    services.append(
        ServiceStatusRecord(
            name="minio",
            category="critical" if "minio" in critical_set else "optional",
            status=minio_result.status,
            response_ms=minio_result.response_ms,
            error=minio_result.error,
            remediation_step=_REMEDIATION_STEPS["minio"] if minio_result.status == "DOWN" else None,
        )
    )

    langfuse_result = check_langfuse(timeout_ms=langfuse_timeout_ms)
    services.append(
        ServiceStatusRecord(
            name="langfuse",
            category="critical" if "langfuse" in critical_set else "optional",
            status=langfuse_result.status,
            response_ms=langfuse_result.response_ms,
            error=langfuse_result.error,
            remediation_step=_REMEDIATION_STEPS["langfuse"] if langfuse_result.status == "DOWN" else None,
        )
    )

    ollama_result = check_ollama(timeout_ms=ollama_timeout_ms)
    services.append(
        ServiceStatusRecord(
            name="ollama",
            category="optional",  # Ollama nunca es crítico, ver defaults.yaml
            status=ollama_result.status,
            response_ms=ollama_result.response_ms,
            error=ollama_result.error,
            remediation_step=_REMEDIATION_STEPS["ollama"] if ollama_result.status == "DOWN" else None,
        )
    )

    for s in services:
        emit_trace_event(
            "health_check.service_up" if s.status == "UP" else "health_check.service_degraded",
            trace_id=trace_id,
            run_id=run_id,
            service_name=s.name,
            category=s.category,
            response_ms=s.response_ms,
            error=s.error,
        )

    # ── evaluate_verdict ──────────────────────────────────────────────────
    critical_down = [s.name for s in services if s.category == "critical" and s.status == "DOWN"]
    critical_up = [s.name for s in services if s.category == "critical" and s.status == "UP"]

    dev_demoted = _dev_demoted_services(variant)
    optional_down_all = [s.name for s in services if s.category == "optional" and s.status == "DOWN"]
    # Los servicios degradados a opcional en Dev (MinIO, Langfuse) se
    # reportan en el informe pero NO disparan veredicto DEGRADED: son
    # irrelevantes para el flujo de desarrollo local por diseño.
    optional_down = [name for name in optional_down_all if name not in dev_demoted]

    if critical_down:
        verdict: Verdict = "BLOCKED"
        verdict_reason = (
            f"Servicio(s) crítico(s) no disponible(s): {', '.join(critical_down)}. "
            f"El pipeline no puede arrancar."
        )
        emit_trace_event(
            "health_check.blocked",
            trace_id=trace_id,
            run_id=run_id,
            failed_critical_services=critical_down,
            remediation_steps=[
                _REMEDIATION_STEPS.get(name, "Sin remediación documentada.")
                for name in critical_down
            ],
        )
    elif optional_down:
        verdict = "DEGRADED"
        verdict_reason = (
            f"Servicios no críticos no disponibles: {', '.join(optional_down)}. "
            f"El pipeline continúa con funcionalidad reducida."
        )
        emit_trace_event(
            "health_check.degraded_with_impact",
            trace_id=trace_id,
            run_id=run_id,
            degraded_services=optional_down,
        )
    else:
        verdict = "HEALTHY"
        verdict_reason = "Todos los servicios verificados están disponibles."

    duration_ms = int((time.monotonic() - start) * 1000)

    result = HealthCheckResult(
        trace_id=trace_id,
        run_id=run_id,
        sigma_variant=variant,
        verdict=verdict,
        verdict_reason=verdict_reason,
        services=services,
        critical_services_up=critical_up,
        critical_services_down=critical_down,
        optional_services_down=optional_down_all,
        affected_skills=[],  # se completa en versiones futuras con mapeo skill->servicio
        duration_ms=duration_ms,
    )

    # ── write_health_report (evento final) ───────────────────────────────
    emit_trace_event(
        "health_check.completed",
        trace_id=trace_id,
        run_id=run_id,
        verdict=verdict,
        services_up=critical_up + [s.name for s in services if s.status == "UP" and s.category != "critical"],
        services_down=critical_down + optional_down,
        duration_ms=duration_ms,
    )

    return result


if __name__ == "__main__":
    # Ejecución manual directa: python skill.py
    # Útil para verificar el skill contra infraestructura real sin
    # pasar por el Orquestador todavía.
    import json
    import sys

    result = run_system_health_check()
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    if result.verdict == "BLOCKED":
        sys.exit(1)
    sys.exit(0)
