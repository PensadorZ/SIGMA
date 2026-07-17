"""
sigma/core/tracing.py

Trazabilidad de eventos según ADR-011 (Trazabilidad de Pipelines en
Langfuse V2). Implementa la política de último recurso: si Langfuse no
está disponible, los eventos se encolan en Redis; si Redis tampoco
está disponible, se escriben en archivos de log local con rotación
diaria. El pipeline nunca falla por indisponibilidad de Langfuse.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from sigma.core.config import get_optional_env

logger = logging.getLogger("sigma.core.tracing")

FALLBACK_LOG_DIR = Path(get_optional_env("SIGMA_FALLBACK_LOG_DIR", "sigma_fallback_logs"))


class TraceBackend:
    """
    Backend de trazabilidad con degradación elegante en tres niveles:
    Langfuse -> Redis -> archivo local. Cada nivel se intenta una sola
    vez por evento; si falla, cae al siguiente sin reintentos bloqueantes,
    para no introducir latencia en el pipeline principal.
    """

    def __init__(self) -> None:
        self._langfuse_client: Optional[Any] = None
        self._redis_client: Optional[Any] = None
        self._langfuse_available = self._try_init_langfuse()
        self._redis_available = self._try_init_redis()

    def _try_init_langfuse(self) -> bool:
        try:
            from langfuse import Langfuse  # type: ignore

            public_key = get_optional_env("LANGFUSE_PUBLIC_KEY")
            secret_key = get_optional_env("LANGFUSE_SECRET_KEY")
            host = get_optional_env("LANGFUSE_HOST", "http://localhost:3000")
            if not public_key or not secret_key:
                logger.warning(
                    "LANGFUSE_PUBLIC_KEY/SECRET_KEY no definidas. "
                    "Trazabilidad degradará a Redis o logs locales."
                )
                return False
            self._langfuse_client = Langfuse(
                public_key=public_key, secret_key=secret_key, host=host
            )
            return True
        except Exception as exc:  # noqa: BLE001 - degradación intencional
            logger.warning("Langfuse no disponible (%s). Degradando a Redis.", exc)
            return False

    def _try_init_redis(self) -> bool:
        try:
            import redis  # type: ignore

            host = get_optional_env("REDIS_HOST", "localhost")
            port = int(get_optional_env("REDIS_PORT", "6379"))
            self._redis_client = redis.Redis(host=host, port=port, db=0, socket_timeout=2)
            self._redis_client.ping()
            return True
        except Exception as exc:  # noqa: BLE001 - degradación intencional
            logger.warning("Redis no disponible (%s). Degradando a logs locales.", exc)
            return False

    def emit(self, event_name: str, payload: dict[str, Any], trace_id: str) -> str:
        """
        Emite un evento de trazabilidad. Devuelve el nivel de backend
        que efectivamente lo procesó: "langfuse" | "redis" | "local_log".
        """
        enriched = {
            "event": event_name,
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }

        if self._langfuse_available and self._langfuse_client is not None:
            try:
                self._langfuse_client.event(
                    name=event_name,
                    metadata=enriched,
                    trace_id=trace_id,
                )
                return "langfuse"
            except Exception as exc:  # noqa: BLE001
                logger.warning("Fallo al emitir a Langfuse (%s). Probando Redis.", exc)

        if self._redis_available and self._redis_client is not None:
            try:
                key = f"sigma:fallback_events:{trace_id}"
                self._redis_client.rpush(key, json.dumps(enriched))
                return "redis"
            except Exception as exc:  # noqa: BLE001
                logger.warning("Fallo al emitir a Redis (%s). Usando log local.", exc)

        self._emit_local(enriched)
        return "local_log"

    def _emit_local(self, enriched: dict[str, Any]) -> None:
        FALLBACK_LOG_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = FALLBACK_LOG_DIR / f"sigma_events_{date_str}.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(enriched) + "\n")


_backend: Optional[TraceBackend] = None


def _get_backend() -> TraceBackend:
    global _backend
    if _backend is None:
        _backend = TraceBackend()
    return _backend


def emit_trace_event(event_name: str, trace_id: str, **payload: Any) -> str:
    """
    Punto de entrada único usado por todos los skills para emitir
    eventos de trazabilidad. Ejemplo:

        emit_trace_event(
            "health_check.completed",
            trace_id="tr-001",
            run_id="hc-001",
            verdict="HEALTHY",
        )

    Devuelve el backend que procesó el evento, útil para tests.
    """
    return _get_backend().emit(event_name, payload, trace_id)
