# =============================================================================
# skills/0000-system-health-check/tests/test_system_health_check_stress.py
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA: reubicado desde tests/test_0000_health_check_stress.py (raíz del
# proyecto) a esta carpeta, consistente con el patrón ya establecido para
# 0001 y 0002 — todo el testing específico de un skill vive dentro de su
# propia carpeta, no disperso en la raíz.
#
# Objetivo: garantizar que la fusión (Opción C) de 0000-system-health-check
# — verdict HEALTHY/DEGRADED/BLOCKED + run_id + verificación real de 5
# servicios — no puede hacer fallar la ejecución del Hito 1 por:
#   - Un servicio crítico caído (debe BLOQUEAR, no colgarse)
#   - Un servicio opcional caído (debe DEGRADAR, nunca bloquear)
#   - Todos los servicios caídos a la vez (peor caso realista)
#   - Servicios lentos que casi alcanzan el timeout
#   - El veredicto Pydantic siendo internamente consistente siempre
#   - Llamadas concurrentes (varios health-checks en paralelo)
#
# Ejecutar: pytest skills/0000-system-health-check/tests/test_system_health_check_stress.py -v
# =============================================================================

from __future__ import annotations

import threading
import time

import pytest

from sigma.core.pipeline_state import initial_state
from sigma.skills._common import ServiceCheckResult
from sigma.skills._loader import load_skill

skill = load_skill("0000-system-health-check")


# ---------------------------------------------------------------------------
# Fixtures — entorno Full mínimo válido, y helpers de estado
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _full_env(monkeypatch):
    """Variables de entorno críticas presentes — sin esto ni siquiera arranca."""
    monkeypatch.setenv("SIGMA_VARIANT", "Full")
    monkeypatch.setenv("POSTGRES_HOST", "fake-host")
    monkeypatch.setenv("POSTGRES_DB", "fake-db")
    monkeypatch.setenv("POSTGRES_USER", "fake-user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "fake-pass")
    monkeypatch.setenv("MINIO_ENDPOINT", "fake-minio:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY", "fake-access")
    monkeypatch.setenv("MINIO_SECRET_KEY", "fake-secret")


def _make_state(trace_id="test-0000") -> dict:
    return initial_state(
        trace_id=trace_id, pipeline_run_id=f"run-{trace_id}",
        sigma_variant="Full", data_path="./data/test.csv",
    )


def _ok(service: str) -> ServiceCheckResult:
    return ServiceCheckResult(service=service, available=True, latency_ms=5)


def _down(service: str, error: str = "connection refused") -> ServiceCheckResult:
    return ServiceCheckResult(service=service, available=False, latency_ms=10, error=error)


def _patch_all_services(monkeypatch, *, pg=True, redis=True, minio=True, langfuse=True, ollama=True):
    monkeypatch.setattr(skill, "check_postgres", lambda **kw: (_ok if pg else _down)("postgres"))
    monkeypatch.setattr(skill, "check_redis", lambda **kw: (_ok if redis else _down)("redis"))
    monkeypatch.setattr(skill, "_check_minio", lambda **kw: (_ok if minio else _down)("minio"))
    monkeypatch.setattr(skill, "_check_langfuse", lambda **kw: (_ok if langfuse else _down)("langfuse"))
    monkeypatch.setattr(skill, "_check_ollama", lambda **kw: (_ok if ollama else _down)("ollama"))


# ---------------------------------------------------------------------------
# Veredicto HEALTHY — todo arriba
# ---------------------------------------------------------------------------

def test_todos_los_servicios_arriba_veredicto_healthy(monkeypatch):
    _patch_all_services(monkeypatch)
    result = skill.run(_make_state())
    assert result["status"] == "success"
    assert result["output"]["verdict"] == "HEALTHY"
    assert result["output"]["critical_services_down"] == []
    assert result["output"]["optional_services_down"] == []


def test_healthy_incluye_run_id_y_trace_id(monkeypatch):
    _patch_all_services(monkeypatch)
    result = skill.run(_make_state(trace_id="wc-0000-001"))
    assert result["output"]["trace_id"] == "wc-0000-001"
    assert result["output"]["run_id"] == "run-wc-0000-001"


# ---------------------------------------------------------------------------
# Veredicto BLOCKED — servicio crítico caído
# ---------------------------------------------------------------------------

def test_postgres_caido_bloquea_el_pipeline(monkeypatch):
    _patch_all_services(monkeypatch, pg=False)
    result = skill.run(_make_state())
    assert result["status"] == "error"
    assert result["error_type"] == "InfrastructureBlockedError"
    assert "postgres" in result["error_detail"]


def test_minio_caido_bloquea_el_pipeline(monkeypatch):
    _patch_all_services(monkeypatch, minio=False)
    result = skill.run(_make_state())
    assert result["status"] == "error"
    assert result["error_type"] == "InfrastructureBlockedError"
    assert "minio" in result["error_detail"]


def test_ambos_criticos_caidos_bloquea_con_ambos_en_el_detalle(monkeypatch):
    _patch_all_services(monkeypatch, pg=False, minio=False)
    result = skill.run(_make_state())
    assert result["status"] == "error"
    assert "postgres" in result["error_detail"]
    assert "minio" in result["error_detail"]


# ---------------------------------------------------------------------------
# Veredicto DEGRADED — solo servicios opcionales caídos, NUNCA bloquea
# ---------------------------------------------------------------------------

def test_redis_caido_solo_degrada_no_bloquea(monkeypatch):
    _patch_all_services(monkeypatch, redis=False)
    result = skill.run(_make_state())
    assert result["status"] == "success_with_warnings"
    assert result["output"]["verdict"] == "DEGRADED"
    assert "redis" in result["output"]["optional_services_down"]


def test_langfuse_caido_solo_degrada(monkeypatch):
    _patch_all_services(monkeypatch, langfuse=False)
    result = skill.run(_make_state())
    assert result["status"] == "success_with_warnings"
    assert result["output"]["verdict"] == "DEGRADED"


def test_ollama_caido_solo_degrada(monkeypatch):
    _patch_all_services(monkeypatch, ollama=False)
    result = skill.run(_make_state())
    assert result["status"] == "success_with_warnings"
    assert result["output"]["verdict"] == "DEGRADED"


def test_todos_los_opcionales_caidos_a_la_vez_sigue_sin_bloquear(monkeypatch):
    """
    Peor caso realista para servicios opcionales: Redis, Langfuse y
    Ollama caídos simultáneamente (ej. VPS recién reiniciado, esos tres
    contenedores tardan más en levantar que PostgreSQL/MinIO). El
    pipeline DEBE poder continuar — es exactamente el escenario que
    esta fusión existe para blindar.
    """
    _patch_all_services(monkeypatch, redis=False, langfuse=False, ollama=False)
    result = skill.run(_make_state())
    assert result["status"] == "success_with_warnings"
    assert result["output"]["verdict"] == "DEGRADED"
    assert set(result["output"]["optional_services_down"]) == {"redis", "langfuse", "ollama"}
    assert result["output"]["critical_services_down"] == []


# ---------------------------------------------------------------------------
# Consistencia interna del veredicto — nunca debe contradecirse
# ---------------------------------------------------------------------------

def test_veredicto_nunca_es_healthy_si_hay_algo_caido(monkeypatch):
    _patch_all_services(monkeypatch, redis=False)
    result = skill.run(_make_state())
    assert result["output"]["verdict"] != "HEALTHY"


def test_veredicto_nunca_es_blocked_si_solo_hay_opcionales_caidos(monkeypatch):
    _patch_all_services(monkeypatch, redis=False, langfuse=False, ollama=False)
    result = skill.run(_make_state())
    assert result["output"]["verdict"] != "BLOCKED"


def test_veredicto_es_blocked_si_hay_al_menos_un_critico_caido_sin_importar_opcionales(monkeypatch):
    _patch_all_services(monkeypatch, pg=False, redis=False, langfuse=False, ollama=False)
    result = skill.run(_make_state())
    # make_error() vacía 'output' por contrato de todo el proyecto (ver
    # _common.py) — el detalle del veredicto BLOCKED va en error_detail,
    # no en output. Consistente con cómo se prueban los demás errores
    # en 0008/0011 (SENT-003, VIZ-004, etc.)
    assert result["status"] == "error"
    assert result["error_type"] == "InfrastructureBlockedError"
    assert "postgres" in result["error_detail"]


# ---------------------------------------------------------------------------
# Servicios lentos — no deben colgar el arranque del pipeline
# ---------------------------------------------------------------------------

def test_servicio_lento_no_cuelga_indefinidamente(monkeypatch):
    """
    Simula PostgreSQL respondiendo justo antes del timeout — el chequeo
    debe completarse en un tiempo acotado, no esperar para siempre.
    Este es el escenario más peligroso para una corrida real: un
    servicio que ni cae limpiamente ni responde rápido.
    """
    def _slow_check_postgres(**kwargs):
        time.sleep(0.2)
        return _ok("postgres")

    monkeypatch.setattr(skill, "check_postgres", _slow_check_postgres)
    monkeypatch.setattr(skill, "check_redis", lambda **kw: _ok("redis"))
    monkeypatch.setattr(skill, "_check_minio", lambda **kw: _ok("minio"))
    monkeypatch.setattr(skill, "_check_langfuse", lambda **kw: _ok("langfuse"))
    monkeypatch.setattr(skill, "_check_ollama", lambda **kw: _ok("ollama"))

    t0 = time.monotonic()
    result = skill.run(_make_state())
    elapsed = time.monotonic() - t0

    assert result["status"] == "success"
    assert elapsed < 2.0, f"El chequeo tardó {elapsed:.2f}s — riesgo de cuelgue en producción"


# ---------------------------------------------------------------------------
# Modo Dev — nunca debe intentar tocar infraestructura real
# ---------------------------------------------------------------------------

def test_modo_dev_no_llama_a_ningun_check_real(monkeypatch):
    """
    Si algún check real se invoca en modo Dev, algo está mal — Dev existe
    precisamente para no depender de infraestructura. Este test falla
    fuerte (con AssertionError explícito) si eso ocurre.
    """
    def _fail_if_called(**kwargs):
        raise AssertionError("check real invocado en modo Dev — no debería pasar nunca")

    monkeypatch.setattr(skill, "check_postgres", _fail_if_called)
    monkeypatch.setattr(skill, "check_redis", _fail_if_called)
    monkeypatch.setattr(skill, "_check_minio", _fail_if_called)
    monkeypatch.setattr(skill, "_check_langfuse", _fail_if_called)
    monkeypatch.setattr(skill, "_check_ollama", _fail_if_called)

    state = _make_state()
    state["sigma_variant"] = "Dev"
    result = skill.run(state)

    # El modo Dev siempre marca warnings=['synthetic_data'], igual que
    # 0008 y 0011 — status correcto es success_with_warnings, no 'success'
    # puro. Mismo patrón ya establecido para esos dos skills.
    assert result["status"] in ("success", "success_with_warnings")
    assert result["output"]["verdict"] == "HEALTHY"
    assert result["output"]["dev_mode"] is True


# ---------------------------------------------------------------------------
# Concurrencia — varios arranques de pipeline verificando salud a la vez
# ---------------------------------------------------------------------------

def test_health_check_concurrente_no_falla_ni_da_veredictos_cruzados(monkeypatch):
    """
    Simula el caso de que decidas correr más de un pipeline en paralelo
    (ej. Tirendaz + un dataset de prueba al mismo tiempo). Cada
    ejecución debe llegar a su propio veredicto sin interferencia.
    """
    _patch_all_services(monkeypatch, redis=False)  # DEGRADED esperado en todos

    results: list[dict] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def _worker(idx: int):
        try:
            r = skill.run(_make_state(trace_id=f"concurrent-{idx}"))
            with lock:
                results.append(r)
        except Exception as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(15)]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=5)

    assert len(errors) == 0, f"run() lanzó excepciones bajo concurrencia: {errors}"
    assert len(results) == 15
    assert all(r["output"]["verdict"] == "DEGRADED" for r in results)
    # Cada resultado debe llevar su propio trace_id, sin mezclarse entre hilos
    trace_ids = {r["output"]["trace_id"] for r in results}
    assert trace_ids == {f"concurrent-{i}" for i in range(15)}
