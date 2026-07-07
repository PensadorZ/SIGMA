# =============================================================================
# test_0000_system_health_check.py — Step definitions pytest-bdd para 0000
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# =============================================================================

from __future__ import annotations

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from sigma.skills._common import ServiceCheckResult
from sigma.skills._loader import load_skill

skill = load_skill("0000-system-health-check")

scenarios("test_system_health_check.feature")


def _ok(service: str) -> ServiceCheckResult:
    return ServiceCheckResult(service=service, available=True, latency_ms=5)


def _down(service: str) -> ServiceCheckResult:
    return ServiceCheckResult(service=service, available=False, latency_ms=10, error="connection refused")


@pytest.fixture(autouse=True)
def _full_env(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "fake-host")
    monkeypatch.setenv("POSTGRES_DB", "fake-db")
    monkeypatch.setenv("POSTGRES_USER", "fake-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-pass")
    monkeypatch.setenv("MINIO_ENDPOINT", "fake-minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "fake-access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "fake-secret")


@pytest.fixture(autouse=True)
def _default_all_up(monkeypatch):
    """Todos los servicios arriba por defecto — los Given los sobreescriben."""
    monkeypatch.setattr(skill, "check_postgres", lambda **kw: _ok("postgres"))
    monkeypatch.setattr(skill, "check_redis", lambda **kw: _ok("redis"))
    monkeypatch.setattr(skill, "_check_minio", lambda **kw: _ok("minio"))
    monkeypatch.setattr(skill, "_check_langfuse", lambda **kw: _ok("langfuse"))
    monkeypatch.setattr(skill, "_check_ollama", lambda **kw: _ok("ollama"))


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------

@given("que el entorno tiene SIGMA_VARIANT configurado")
def _entorno_configurado():
    pass


@given("que las variables de entorno críticas están presentes")
def _env_criticas_presentes():
    pass  # ya garantizado por el fixture autouse _full_env


# ---------------------------------------------------------------------------
# Given — estado de servicios por escenario
# ---------------------------------------------------------------------------

@given("que los 5 servicios responden correctamente")
def _todos_arriba():
    pass  # ya es el default del fixture autouse


@given("que los demás servicios responden correctamente")
def _demas_arriba():
    pass


@given("que PostgreSQL y MinIO responden correctamente")
def _pg_minio_arriba():
    pass


@given("que PostgreSQL no responde")
def _pg_caido(monkeypatch):
    monkeypatch.setattr(skill, "check_postgres", lambda **kw: _down("postgres"))


@given("que MinIO no responde")
def _minio_caido(monkeypatch):
    monkeypatch.setattr(skill, "_check_minio", lambda **kw: _down("minio"))


@given("que Redis no responde")
def _redis_caido(monkeypatch):
    monkeypatch.setattr(skill, "check_redis", lambda **kw: _down("redis"))


@given("que Langfuse no responde")
def _langfuse_caido(monkeypatch):
    monkeypatch.setattr(skill, "_check_langfuse", lambda **kw: _down("langfuse"))


@given("que Ollama no responde")
def _ollama_caido(monkeypatch):
    monkeypatch.setattr(skill, "_check_ollama", lambda **kw: _down("ollama"))


@given(parsers.parse('que SIGMA_VARIANT es "{variant}"'))
def _sigma_variant(monkeypatch, ctx, variant):
    monkeypatch.setenv("SIGMA_VARIANT", variant)
    ctx["sigma_variant"] = variant


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse('el Orquestador invoca system-health-check con trace_id "{trace_id}"'))
def _invoca_skill(monkeypatch, make_state, ctx, trace_id):
    if ctx.get("sigma_variant") == "Dev":
        def _fail_if_called(**kwargs):
            raise AssertionError("check real invocado en modo Dev — no debería pasar nunca")
        monkeypatch.setattr(skill, "check_postgres", _fail_if_called)
        monkeypatch.setattr(skill, "check_redis", _fail_if_called)
        monkeypatch.setattr(skill, "_check_minio", _fail_if_called)
        monkeypatch.setattr(skill, "_check_langfuse", _fail_if_called)
        monkeypatch.setattr(skill, "_check_ollama", _fail_if_called)

    state = make_state(trace_id=trace_id, sigma_variant=ctx.get("sigma_variant", "Full"))
    ctx["result"] = skill.run(state)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then(parsers.parse('el veredicto es "{verdict}"'))
def _veredicto_es(ctx, verdict):
    result = ctx["result"]
    if result["status"] == "error":
        # BLOCKED vacía output por contrato de make_error() — el veredicto
        # se confirma indirectamente vía error_type, no vía output.
        assert verdict == "BLOCKED"
        assert result["error_type"] == "InfrastructureBlockedError"
    else:
        assert result["output"]["verdict"] == verdict


@then(parsers.parse('retorna status "{status}"'))
def _retorna_status(ctx, status):
    assert ctx["result"]["status"] == status


@then("el output incluye run_id y trace_id")
def _incluye_run_id_trace_id(ctx):
    out = ctx["result"]["output"]
    assert out["run_id"] is not None
    assert out["trace_id"] is not None


@then(parsers.parse('el error menciona "{service}"'))
def _error_menciona(ctx, service):
    assert service in ctx["result"]["error_detail"]


@then("el output indica dev_mode True")
def _dev_mode_true(ctx):
    assert ctx["result"]["output"]["dev_mode"] is True


@then("ningún chequeo real de infraestructura fue invocado")
def _ningun_check_real():
    pass  # verificado por el AssertionError que _fail_if_called dispararía
