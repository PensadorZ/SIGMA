"""
sigma/core/connections.py

Clientes de conexión a infraestructura base de SIGMA: PostgreSQL y
Redis. Usados por system-health-check para verificar disponibilidad,
y por el resto de los skills para leer/escribir datos reales.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator, Optional

from sigma.core.config import get_optional_env


class ServiceCheckResult:
    """Resultado de verificar la disponibilidad de un servicio."""

    def __init__(
        self,
        name: str,
        status: str,
        response_ms: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        self.name = name
        self.status = status  # "UP" | "DOWN"
        self.response_ms = response_ms
        self.error = error

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "response_ms": self.response_ms,
            "error": self.error,
        }


def check_postgresql(timeout_ms: int = 3000) -> ServiceCheckResult:
    """
    Verifica disponibilidad de PostgreSQL mediante una conexión TCP
    real y un SELECT 1. Usa psycopg2 si está disponible.
    """
    start = time.monotonic()
    try:
        import psycopg2  # type: ignore

        host = get_optional_env("POSTGRES_HOST", "localhost")
        port = get_optional_env("POSTGRES_PORT", "5432")
        user = get_optional_env("POSTGRES_USER", "sigma")
        password = get_optional_env("POSTGRES_PASSWORD", "")
        dbname = get_optional_env("POSTGRES_DB", "sigma")

        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=max(1, timeout_ms // 1000),
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        finally:
            conn.close()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult("postgresql", "UP", response_ms=elapsed_ms)

    except Exception as exc:  # noqa: BLE001 - cualquier fallo de conexión es "DOWN"
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult(
            "postgresql", "DOWN", response_ms=elapsed_ms, error=str(exc)
        )


def check_redis(timeout_ms: int = 1000) -> ServiceCheckResult:
    """Verifica disponibilidad de Redis mediante PING real."""
    start = time.monotonic()
    try:
        import redis  # type: ignore

        host = get_optional_env("REDIS_HOST", "localhost")
        port = int(get_optional_env("REDIS_PORT", "6379"))

        client = redis.Redis(
            host=host, port=port, db=0, socket_timeout=max(1, timeout_ms / 1000)
        )
        client.ping()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult("redis", "UP", response_ms=elapsed_ms)

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult("redis", "DOWN", response_ms=elapsed_ms, error=str(exc))


def check_minio(timeout_ms: int = 2000) -> ServiceCheckResult:
    """Verifica disponibilidad de MinIO vía su endpoint de health."""
    start = time.monotonic()
    try:
        import urllib.request

        endpoint = get_optional_env("MINIO_ENDPOINT", "localhost:9000")
        url = f"http://{endpoint}/minio/health/live"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=max(1, timeout_ms / 1000)) as resp:
            ok = 200 <= resp.status < 300

        elapsed_ms = int((time.monotonic() - start) * 1000)
        if ok:
            return ServiceCheckResult("minio", "UP", response_ms=elapsed_ms)
        return ServiceCheckResult(
            "minio", "DOWN", response_ms=elapsed_ms, error=f"HTTP status {resp.status}"
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult("minio", "DOWN", response_ms=elapsed_ms, error=str(exc))


def check_langfuse(timeout_ms: int = 3000) -> ServiceCheckResult:
    """Verifica disponibilidad de Langfuse vía su endpoint de health público."""
    start = time.monotonic()
    try:
        import urllib.request

        host = get_optional_env("LANGFUSE_HOST", "http://localhost:3000")
        url = f"{host.rstrip('/')}/api/public/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=max(1, timeout_ms / 1000)) as resp:
            ok = 200 <= resp.status < 300

        elapsed_ms = int((time.monotonic() - start) * 1000)
        if ok:
            return ServiceCheckResult("langfuse", "UP", response_ms=elapsed_ms)
        return ServiceCheckResult(
            "langfuse", "DOWN", response_ms=elapsed_ms, error=f"HTTP status {resp.status}"
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult(
            "langfuse", "DOWN", response_ms=elapsed_ms, error=str(exc)
        )


def check_ollama(timeout_ms: int = 5000) -> ServiceCheckResult:
    """Verifica disponibilidad de Ollama vía su endpoint /api/tags."""
    start = time.monotonic()
    try:
        import urllib.request

        host = get_optional_env("OLLAMA_HOST", "http://localhost:11434")
        url = f"{host.rstrip('/')}/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=max(1, timeout_ms / 1000)) as resp:
            ok = 200 <= resp.status < 300

        elapsed_ms = int((time.monotonic() - start) * 1000)
        if ok:
            return ServiceCheckResult("ollama", "UP", response_ms=elapsed_ms)
        return ServiceCheckResult(
            "ollama", "DOWN", response_ms=elapsed_ms, error=f"HTTP status {resp.status}"
        )

    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.monotonic() - start) * 1000)
        return ServiceCheckResult("ollama", "DOWN", response_ms=elapsed_ms, error=str(exc))
