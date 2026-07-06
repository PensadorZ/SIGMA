"""
sigma.core — Módulo base del ecosistema SIGMA.

Provee las primitivas que todos los skills usan: gestión de secretos
(ADR-010), trazabilidad con degradación elegante (ADR-011), y
verificación de conectividad a infraestructura real.
"""

from sigma.core.config import (
    ContextResolutionError,
    get_optional_env,
    get_required_env,
    get_sigma_variant,
    is_dev_mode,
)
from sigma.core.connections import (
    ServiceCheckResult,
    check_langfuse,
    check_minio,
    check_ollama,
    check_postgresql,
    check_redis,
)
from sigma.core.tracing import emit_trace_event

__all__ = [
    "ContextResolutionError",
    "get_optional_env",
    "get_required_env",
    "get_sigma_variant",
    "is_dev_mode",
    "ServiceCheckResult",
    "check_langfuse",
    "check_minio",
    "check_ollama",
    "check_postgresql",
    "check_redis",
    "emit_trace_event",
]
