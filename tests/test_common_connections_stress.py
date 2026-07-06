# =============================================================================
# tests/test_common_connections_stress.py — Tests de estrés de infraestructura
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Objetivo: garantizar que la capa de conexiones fusionada en _common.py
# (Opción 3 — sigma/core/connections.py + skills/_common.py) NO puede
# hacer fallar la ejecución del Hito 1 por:
#   - Servicios caídos o inalcanzables (Postgres/Redis apagados)
#   - Conexiones lentas que se cuelgan indefinidamente sin timeout
#   - Errores transitorios que SÍ deberían reintentarse
#   - Errores no transitorios (credenciales) que NO deberían reintentarse
#   - Llamadas concurrentes simultáneas (varios skills verificando a la vez)
#
# Ejecutar: pytest tests/test_common_connections_stress.py -v
# =============================================================================

from __future__ import annotations

import threading
import time

import pytest

from skills._common import (
    ServiceCheckResult,
    check_postgres,
    check_redis,
    get_pg_connection,
)


# ---------------------------------------------------------------------------
# Fakes controlados — simulan fallos reales sin depender de infraestructura
# ---------------------------------------------------------------------------

class _FakeSlowConnector:
    """Simula un servicio que tarda más de lo razonable en responder."""
    def __call__(self, *args, **kwargs):
        time.sleep(0.3)  # simula latencia alta, no un cuelgue infinito
        raise TimeoutError("timeout expired simulado")


class _FakeUnreachableConnector:
    """Simula 'Connection refused' — servicio apagado."""
    def __call__(self, *args, **kwargs):
        raise ConnectionRefusedError("connection refused simulado")


class _FakeAuthFailureConnector:
    """Simula error de credenciales — NO debe reintentarse."""
    call_count = 0

    def __call__(self, *args, **kwargs):
        _FakeAuthFailureConnector.call_count += 1
        raise Exception("FATAL: password authentication failed for user")


class _FakeTransientThenSuccessConnector:
    """
    Simula un servicio que falla las primeras N veces (arrancando o
    reiniciándose) y luego responde correctamente — el caso real más
    común en un docker-compose que aún no terminó su healthcheck.
    """
    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise Exception("could not connect to server: Connection refused")
        return _FakeConnection()


class _FakeConnection:
    def close(self):
        pass


# ---------------------------------------------------------------------------
# check_postgres — nunca debe propagar excepción, siempre ServiceCheckResult
# ---------------------------------------------------------------------------

def test_check_postgres_servicio_caido_no_lanza_excepcion():
    result = check_postgres(timeout_seconds=1, _connector=_FakeUnreachableConnector())
    assert isinstance(result, ServiceCheckResult)
    assert result.available is False
    assert result.service == "postgres"
    assert "refused" in result.error.lower()


def test_check_postgres_reporta_latencia_incluso_en_fallo():
    result = check_postgres(timeout_seconds=1, _connector=_FakeUnreachableConnector())
    assert result.latency_ms >= 0


def test_check_postgres_exitoso_marca_available_true():
    def _fake_ok_connector(*args, **kwargs):
        return _FakeConnection()

    result = check_postgres(timeout_seconds=1, _connector=_fake_ok_connector)
    assert result.available is True
    assert result.error is None


# ---------------------------------------------------------------------------
# check_redis — mismo contrato que check_postgres
# ---------------------------------------------------------------------------

def test_check_redis_servicio_caido_no_lanza_excepcion(monkeypatch):
    class _FakeRedisUnreachable:
        def __init__(self, *args, **kwargs):
            pass
        def ping(self):
            raise ConnectionError("Error connecting to redis")

    result = check_redis(timeout_seconds=1, _connector=_FakeRedisUnreachable)
    assert isinstance(result, ServiceCheckResult)
    assert result.available is False
    assert result.service == "redis"


def test_check_redis_exitoso():
    class _FakeRedisOK:
        def __init__(self, *args, **kwargs):
            pass
        def ping(self):
            return True

    result = check_redis(timeout_seconds=1, _connector=_FakeRedisOK)
    assert result.available is True


# ---------------------------------------------------------------------------
# get_pg_connection — retry con backoff SOLO para errores transitorios
# ---------------------------------------------------------------------------

def test_get_pg_connection_reintenta_y_logra_conectar_tras_fallos_transitorios(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "fake-host")
    monkeypatch.setenv("POSTGRES_DB", "fake-db")
    monkeypatch.setenv("POSTGRES_USER", "fake-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-pass")

    fake_connector = _FakeTransientThenSuccessConnector(fail_times=2)

    conn = get_pg_connection(
        state={},
        max_retries=3,
        backoff_seconds=0.01,  # rápido para no alargar la suite de tests
        _connector=fake_connector,
    )
    assert isinstance(conn, _FakeConnection)
    assert fake_connector.calls == 3  # 2 fallos + 1 éxito


def test_get_pg_connection_agota_reintentos_y_lanza_error_claro(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "fake-host")
    monkeypatch.setenv("POSTGRES_DB", "fake-db")
    monkeypatch.setenv("POSTGRES_USER", "fake-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-pass")

    with pytest.raises(ConnectionError) as exc_info:
        get_pg_connection(
            state={},
            max_retries=2,
            backoff_seconds=0.01,
            _connector=_FakeUnreachableConnector(),
        )
    assert "3 intento" in str(exc_info.value)  # max_retries + 1 = 3 intentos


def test_get_pg_connection_no_reintenta_errores_de_credenciales(monkeypatch):
    """
    Un error de autenticación no se va a resolver reintentando —
    debe fallar en el PRIMER intento, sin backoff, mismo principio
    de fallo rápido que el circuit breaker del orquestador.
    """
    monkeypatch.setenv("POSTGRES_HOST", "fake-host")
    monkeypatch.setenv("POSTGRES_DB", "fake-db")
    monkeypatch.setenv("POSTGRES_USER", "fake-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-pass")

    fake_connector = _FakeAuthFailureConnector()
    _FakeAuthFailureConnector.call_count = 0

    with pytest.raises(ConnectionError):
        get_pg_connection(
            state={},
            max_retries=5,  # aunque se permitan 5 reintentos...
            backoff_seconds=0.01,
            _connector=fake_connector,
        )
    # ...solo debe haberse llamado UNA vez, porque el error no es transitorio
    assert _FakeAuthFailureConnector.call_count == 1


def test_get_pg_connection_respeta_timeout_no_se_cuelga(monkeypatch):
    """
    Verifica que una conexión lenta no bloquea la prueba más allá de un
    tiempo razonable — protege contra el escenario real más peligroso
    para el Hito 1: que el pipeline se quede colgado indefinidamente
    esperando a PostgreSQL sin nunca fallar ni continuar.
    """
    monkeypatch.setenv("POSTGRES_HOST", "fake-host")
    monkeypatch.setenv("POSTGRES_DB", "fake-db")
    monkeypatch.setenv("POSTGRES_USER", "fake-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-pass")

    t0 = time.monotonic()
    with pytest.raises(ConnectionError):
        get_pg_connection(
            state={},
            max_retries=1,
            backoff_seconds=0.01,
            _connector=_FakeSlowConnector(),
        )
    elapsed = time.monotonic() - t0
    # 2 intentos * ~0.3s de latencia simulada + backoff mínimo, con margen
    assert elapsed < 2.0, (
        f"get_pg_connection tardó {elapsed:.2f}s — posible cuelgue sin timeout"
    )


# ---------------------------------------------------------------------------
# Concurrencia — varios skills verificando infraestructura al mismo tiempo
# ---------------------------------------------------------------------------

def test_check_postgres_concurrente_no_falla_ni_corrompe_estado():
    """
    Simula varios nodos del orquestador (0000, 0001, etc.) llamando a
    check_postgres al mismo tiempo. No debe haber excepciones no
    capturadas ni resultados cruzados entre hilos.
    """
    results: list[ServiceCheckResult] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def _worker():
        try:
            r = check_postgres(timeout_seconds=1, _connector=_FakeUnreachableConnector())
            with lock:
                results.append(r)
        except Exception as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)

    assert len(errors) == 0, f"check_postgres lanzó excepciones bajo concurrencia: {errors}"
    assert len(results) == 20
    assert all(r.available is False for r in results)


def test_get_pg_connection_concurrente_con_reintentos_no_se_bloquea():
    """
    Peor caso realista: varios skills reintentando conexión a la vez
    mientras PostgreSQL está arrancando. Ninguno debe tardar más de
    lo esperado ni lanzar una excepción distinta a ConnectionError.
    """
    exceptions: list[Exception] = []
    lock = threading.Lock()

    def _worker():
        fake_connector = _FakeTransientThenSuccessConnector(fail_times=1)
        try:
            get_pg_connection(
                state={}, max_retries=2, backoff_seconds=0.01,
                _connector=fake_connector,
            )
        except Exception as exc:  # noqa: BLE001
            with lock:
                exceptions.append(exc)

    import os
    os.environ.setdefault("POSTGRES_HOST", "fake-host")
    os.environ.setdefault("POSTGRES_DB", "fake-db")
    os.environ.setdefault("POSTGRES_USER", "fake-user")
    os.environ.setdefault("POSTGRES_PASSWORD", "fake-pass")

    threads = [threading.Thread(target=_worker) for _ in range(10)]
    t0 = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    elapsed = time.monotonic() - t0

    assert len(exceptions) == 0, f"Excepciones inesperadas bajo concurrencia: {exceptions}"
    assert elapsed < 3.0, f"La concurrencia tardó demasiado: {elapsed:.2f}s"
