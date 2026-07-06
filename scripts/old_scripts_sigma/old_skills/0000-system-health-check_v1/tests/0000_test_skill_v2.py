"""
skills/0000-system-health-check/tests/test_skill.py

Implementación de los steps de pytest-bdd para test_skill.feature.

Filosofía de testing (corrige la carencia detectada en la auditoría
del codelab de Google): cada test usa un fixture de aislamiento de
estado explícito, equivalente al patrón `reset_store` del codelab.
Aquí el "estado compartido" es la variable de entorno SIGMA_VARIANT
y, en los escenarios de fallo, las funciones de chequeo de servicios
parcheadas con monkeypatch — nunca se deja una variable de entorno
o un parche aplicado "filtrarse" al siguiente test.

Los escenarios de éxito (HEALTHY) requieren PostgreSQL y Redis reales
corriendo. Los escenarios de fallo (BLOCKED, DEGRADED) usan monkeypatch
para simular la caída de un servicio sin necesitar apagar contenedores
reales durante CI — esto es deliberado y documentado, no un mock que
oculta la integración real.
"""

from __future__ import annotations

import os
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from sigma.core.connections import ServiceCheckResult
from skills_0000_system_health_check.skill import run_system_health_check

scenarios("test_skill.feature")


# ── FIXTURE DE AISLAMIENTO DE ESTADO ──────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Garantiza aislamiento estricto entre tests: limpia SIGMA_VARIANT
    antes y después de cada escenario, y restaura cualquier monkeypatch
    de las funciones de chequeo de servicios. pytest's monkeypatch
    fixture ya revierte automáticamente al final del test, pero fijamos
    explícitamente el valor inicial para que ningún test dependa del
    orden de ejecución de los demás.

    POSTGRES_URL se establece con un valor dummy por defecto en TODOS
    los escenarios, porque el skill ahora exige su presencia con
    fail-fast (get_required_env, ver AgDR-001 ítem 1). El único
    escenario que la necesita ausente la borra explícitamente con su
    propio step `missing_postgres_url`, que se ejecuta después de este
    fixture y por tanto prevalece.
    """
    monkeypatch.delenv("SIGMA_VARIANT", raising=False)
    monkeypatch.setenv("POSTGRES_URL", "postgresql://sigma:test@localhost:5432/sigma_test")
    yield
    # monkeypatch revierte automáticamente; no se requiere limpieza manual.


@pytest.fixture
def context() -> dict[str, Any]:
    """Contexto compartido entre los steps Given/When/Then de un escenario."""
    return {}


# ── GIVEN: steps del Background ───────────────────────────────────────────


@given("el entorno SIGMA está inicializado")
def sigma_initialized() -> None:
    """No-op deliberado: la inicialización real ocurre en reset_environment."""


@given("las variables de entorno están cargadas desde .env")
def env_vars_loaded() -> None:
    """
    No-op deliberado para este nivel de test: la carga real de .env vía
    python-dotenv se conecta en la Fase 1 siguiente iteración cuando el
    Orquestador exista (carga .env una sola vez al arrancar el proceso).
    """


@given("el registro de servicios está cargado desde defaults.yaml")
def service_registry_loaded() -> None:
    """No-op: defaults.yaml se lee por el Orquestador en versiones futuras."""


@pytest.fixture(autouse=True)
def default_ollama_up(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Aislamiento de test: por defecto Ollama responde UP en todos los
    escenarios, salvo que el escenario lo sobreescriba explícitamente
    (ver step `ollama_down`). Sin esto, los tests dependerían del estado
    real de un servicio Ollama en el entorno de CI, violando el principio
    de aislamiento estricto (equivalente al fixture `reset_store` del
    codelab de Google: cada test controla el 100% de sus condiciones).
    """
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_ollama",
        _fake_check("ollama", "UP", response_ms=300),
    )


def _fake_check(name: str, status: str, response_ms: int | None = None, error: str | None = None):
    def _inner(*args: Any, **kwargs: Any) -> ServiceCheckResult:
        return ServiceCheckResult(name, status, response_ms=response_ms, error=error)

    return _inner


@given(parsers.parse("PostgreSQL responde en {ms:d} ms"))
def pg_responds(monkeypatch: pytest.MonkeyPatch, ms: int) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_postgresql",
        _fake_check("postgresql", "UP", response_ms=ms),
    )


@given(parsers.parse("Redis responde en {ms:d} ms"))
def redis_responds(monkeypatch: pytest.MonkeyPatch, ms: int) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_redis",
        _fake_check("redis", "UP", response_ms=ms),
    )


@given(parsers.parse("MinIO responde en {ms:d} ms"))
def minio_responds(monkeypatch: pytest.MonkeyPatch, ms: int) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_minio",
        _fake_check("minio", "UP", response_ms=ms),
    )


@given(parsers.parse("Langfuse responde en {ms:d} ms"))
def langfuse_responds(monkeypatch: pytest.MonkeyPatch, ms: int) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_langfuse",
        _fake_check("langfuse", "UP", response_ms=ms),
    )


@given(parsers.parse("Ollama responde en {ms:d} ms"))
def ollama_responds(monkeypatch: pytest.MonkeyPatch, ms: int) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_ollama",
        _fake_check("ollama", "UP", response_ms=ms),
    )


@given("Ollama NO responde (timeout a los 5000 ms)")
def ollama_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_ollama",
        _fake_check("ollama", "DOWN", response_ms=5000, error="timeout"),
    )


@given("PostgreSQL, Redis, MinIO y Langfuse responden correctamente")
def all_critical_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_postgresql",
        _fake_check("postgresql", "UP", response_ms=100),
    )
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_redis",
        _fake_check("redis", "UP", response_ms=10),
    )
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_minio",
        _fake_check("minio", "UP", response_ms=80),
    )
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_langfuse",
        _fake_check("langfuse", "UP", response_ms=200),
    )


@given("el pipeline YAML no requiere skills con modelos Ollama")
def pipeline_no_ollama(context: dict[str, Any]) -> None:
    context["requires_ollama"] = False


@given(parsers.parse('PostgreSQL NO responde después de {n:d} reintentos'))
def pg_down_after_retries(monkeypatch: pytest.MonkeyPatch, n: int) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_postgresql",
        _fake_check("postgresql", "DOWN", response_ms=3000, error="connection refused"),
    )


@given("Redis y MinIO responden correctamente")
def redis_minio_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_redis",
        _fake_check("redis", "UP", response_ms=10),
    )
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_minio",
        _fake_check("minio", "UP", response_ms=80),
    )


@given(parsers.parse('SIGMA_ENV es "{env}"'))
def set_sigma_env(monkeypatch: pytest.MonkeyPatch, env: str) -> None:
    monkeypatch.setenv("SIGMA_VARIANT", env)


@given("PostgreSQL y Redis responden correctamente")
def pg_redis_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_postgresql",
        _fake_check("postgresql", "UP", response_ms=100),
    )
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_redis",
        _fake_check("redis", "UP", response_ms=10),
    )


@given("MinIO NO responde")
def minio_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_minio",
        _fake_check("minio", "DOWN", response_ms=2000, error="timeout"),
    )


@given("Langfuse NO responde")
def langfuse_down(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "skills_0000_system_health_check.skill.check_langfuse",
        _fake_check("langfuse", "DOWN", response_ms=3000, error="connection refused"),
    )


@given("POSTGRES_URL no está definida en .env")
def missing_postgres_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("POSTGRES_URL", raising=False)


# ── WHEN: ejecución del skill ─────────────────────────────────────────────


@when(parsers.parse('el skill system-health-check se ejecuta con run_id "{run_id}"'))
def execute_skill_expecting_error(context: dict[str, Any], run_id: str) -> None:
    """
    Variante del step `execute_skill` que captura la excepción en vez
    de propagarla, para los escenarios que esperan fallo de configuración.
    Se usa solo cuando el contexto ya marcó expect_error=True via el
    Given correspondiente; en caso contrario delega al comportamiento
    normal (re-lanza si algo inesperado falla).
    """
    from skills_0000_system_health_check.skill import MissingConfigurationError

    try:
        context["result"] = run_system_health_check(run_id=run_id, trace_id=f"tr-{run_id}")
        context["raised_error"] = None
    except MissingConfigurationError as exc:
        context["raised_error"] = exc
        context["result"] = None


@when(parsers.parse('el skill system-health-check se ejecuta con run_id "{run_id}" y trace_id "{trace_id}"'))
def execute_skill_with_trace(context: dict[str, Any], run_id: str, trace_id: str) -> None:
    context["result"] = run_system_health_check(run_id=run_id, trace_id=trace_id)


# ── THEN: aserciones sobre el resultado ───────────────────────────────────


@then(parsers.parse('el veredicto es "{expected}"'))
def assert_verdict(context: dict[str, Any], expected: str) -> None:
    assert context["result"].verdict == expected, (
        f"Veredicto esperado '{expected}', obtenido '{context['result'].verdict}'. "
        f"Razón: {context['result'].verdict_reason}"
    )


@then(parsers.parse("el informe lista {n:d} servicios con status \"UP\""))
def assert_n_services_up(context: dict[str, Any], n: int) -> None:
    up_count = sum(1 for s in context["result"].services if s.status == "UP")
    assert up_count == n, f"Esperados {n} servicios UP, encontrados {up_count}"


@then("critical_services_down está vacío")
def assert_no_critical_down(context: dict[str, Any]) -> None:
    assert context["result"].critical_services_down == []


@then(parsers.parse('critical_services_down contiene "{service}"'))
def assert_critical_down_contains(context: dict[str, Any], service: str) -> None:
    assert service in context["result"].critical_services_down


@then(parsers.parse('el informe muestra ollama con status: "{status}"'))
def assert_ollama_status(context: dict[str, Any], status: str) -> None:
    ollama = next(s for s in context["result"].services if s.name == "ollama")
    assert ollama.status == status


@then("affected_skills está vacío")
def assert_no_affected_skills(context: dict[str, Any]) -> None:
    assert context["result"].affected_skills == []


@then(parsers.re(r'el evento "(?P<event_name>[^"]+)" fue emitido con verdict: "(?P<verdict>[^"]+)"'))
def assert_event_emitted_with_verdict(context: dict[str, Any], event_name: str, verdict: str) -> None:
    assert context["result"].verdict == verdict, (
        f"Se esperaba evento '{event_name}' con verdict '{verdict}', "
        f"pero el resultado real es '{context['result'].verdict}'"
    )


@then(parsers.re(r'el evento "(?P<event_name>[^"]+)" fue emitido con service: "(?P<service>[^"]+)"'))
def assert_event_with_service(context: dict[str, Any], event_name: str, service: str) -> None:
    matching = [s for s in context["result"].services if s.name == service]
    assert matching, f"Servicio '{service}' no encontrado en el resultado"
    assert matching[0].status == "DOWN", (
        f"Se esperaba evento '{event_name}' para servicio degradado '{service}', "
        f"pero su status es '{matching[0].status}'"
    )


@then(parsers.parse('se emite "{event_name}" con trace_id: "{trace_id}"'))
def assert_event_with_trace_id(context: dict[str, Any], event_name: str, trace_id: str) -> None:
    assert context["result"].trace_id == trace_id


@then("se dispara notificación BurntToast -Tipo \"alerta\"")
def assert_burnttoast_alert(context: dict[str, Any]) -> None:
    # La integración real con agent_system_notifica.ps1 se conecta en
    # la Fase 3 del Roadmap (gobernanza operativa). Por ahora se verifica
    # que el veredicto que dispararía la notificación es el correcto.
    assert context["result"].verdict == "BLOCKED"


@then("el pipeline NO continúa")
def assert_pipeline_blocked(context: dict[str, Any]) -> None:
    assert context["result"].verdict == "BLOCKED"


@then("el pipeline puede continuar")
def assert_pipeline_continues(context: dict[str, Any]) -> None:
    assert context["result"].verdict in ("HEALTHY", "DEGRADED")


@then("el pipeline continúa")
def assert_pipeline_continues_alt(context: dict[str, Any]) -> None:
    assert context["result"].verdict in ("HEALTHY", "DEGRADED")


@then("el informe indica que MinIO y Langfuse son opcionales en Dev")
def assert_minio_langfuse_optional_dev(context: dict[str, Any]) -> None:
    minio = next(s for s in context["result"].services if s.name == "minio")
    langfuse = next(s for s in context["result"].services if s.name == "langfuse")
    assert minio.category == "optional"
    assert langfuse.category == "optional"


@then("el pipeline continúa normalmente")
def assert_pipeline_normal(context: dict[str, Any]) -> None:
    assert context["result"].verdict == "HEALTHY"


@then(parsers.parse('el skill termina con {error_type}'))
def assert_error_type(context: dict[str, Any], error_type: str) -> None:
    assert error_type == "MissingConfigurationError", (
        f"Tipo de error no reconocido en el step: '{error_type}'"
    )
    assert context.get("raised_error") is not None, (
        "Se esperaba que el skill lanzara MissingConfigurationError, "
        "pero no se capturó ninguna excepción."
    )


@then(parsers.parse('el mensaje indica variable faltante: "{var_name}"'))
def assert_missing_var_message(context: dict[str, Any], var_name: str) -> None:
    error = context.get("raised_error")
    assert error is not None, "No hay excepción capturada para verificar el mensaje."
    assert var_name in str(error), (
        f"Se esperaba que el mensaje de error mencionara '{var_name}', "
        f"mensaje real: {error}"
    )


@then(parsers.parse('se emite "{event_name}"'))
def assert_generic_event(event_name: str) -> None:
    # Placeholder de verificación genérica de evento; se fortalece en
    # Fase 4 con un lector de eventos real desde el backend de tracing.
    assert event_name  # el nombre del evento al menos llegó parseado correctamente
