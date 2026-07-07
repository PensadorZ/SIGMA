# =============================================================================
# test_0001_data_ingestion.py — Step definitions pytest-bdd para 0001
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# =============================================================================

from __future__ import annotations

import pandas as pd
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from sigma.skills._loader import load_skill

skill = load_skill("0001-data-ingestion")

scenarios("test_data_ingestion.feature")


class _DummyCursor:
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return False
    def execute(self, *args, **kwargs):
        pass


class _DummyConnection:
    def cursor(self):
        return _DummyCursor()
    def commit(self):
        pass
    def rollback(self):
        pass
    def close(self):
        pass


@pytest.fixture(autouse=True)
def _default_pg_connection(monkeypatch):
    monkeypatch.setattr(skill, "get_pg_connection", lambda state: _DummyConnection())


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------

@given("que el entorno tiene SIGMA_VARIANT configurado")
def _entorno_configurado():
    pass


@given(parsers.parse('que PostgreSQL está disponible con la tabla "{table}"'))
def _postgres_disponible(table):
    pass


# ---------------------------------------------------------------------------
# Given — archivos sintéticos vía tmp_path
# ---------------------------------------------------------------------------

@given(parsers.parse('que el archivo "{filename}" existe con {n:d} filas y columna "{col}"'))
def _archivo_existe(monkeypatch, ctx, tmp_path, filename, n, col):
    path = tmp_path / filename
    if n > 0:
        df = pd.DataFrame({col: [f"texto {i}" for i in range(n)]})
        df.to_csv(path, index=False)
    else:
        # Solo cabecera — archivo "vacío" en el sentido de 0 filas de datos
        path.write_text(f"{col}\n", encoding="utf-8")
    ctx["data_path"] = str(path)
    ctx["expected_rows"] = n


@given(parsers.parse('que el archivo "{filename}" existe con {n:d} filas sin columna "{col}"'))
def _archivo_sin_columna(ctx, tmp_path, filename, n, col):
    path = tmp_path / filename
    df = pd.DataFrame({"otra_columna": [f"valor {i}" for i in range(n)]})
    df.to_csv(path, index=False)
    ctx["data_path"] = str(path)


@given(parsers.parse('que el archivo "{filename}" no existe en el sistema'))
def _archivo_no_existe(ctx, tmp_path, filename):
    ctx["data_path"] = str(tmp_path / filename)  # nunca se crea


@given(parsers.parse("que el tamaño de chunk configurado es {size:d}"))
def _tamano_chunk(monkeypatch, size):
    original_load = skill.load_defaults

    def _patched(skill_dir):
        cfg = original_load(skill_dir)
        cfg.setdefault("ingestion", {})["chunk_size"] = size
        return cfg

    monkeypatch.setattr(skill, "load_defaults", _patched)


@given(parsers.parse('que SIGMA_VARIANT es "{variant}"'))
def _sigma_variant(monkeypatch, ctx, variant):
    monkeypatch.setenv("SIGMA_VARIANT", variant)
    ctx["sigma_variant"] = variant


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse('el Orquestador invoca data-ingestion con trace_id "{trace_id}"'))
def _invoca_skill(make_state, ctx, trace_id):
    state = make_state(
        trace_id=trace_id,
        sigma_variant=ctx.get("sigma_variant", "Full"),
        data_path=ctx.get("data_path", "./data/default.csv"),
    )
    ctx["expected_run_id"] = state["pipeline_run_id"]
    ctx["result"] = skill.run(state)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then(parsers.parse('se escriben {n:d} registros en "{table}"'))
def _se_escriben_n_registros(ctx, n, table):
    assert ctx["result"]["output"]["num_records"] == n


@then("el output incluye un checksum_sha256 no nulo")
def _checksum_no_nulo(ctx):
    assert ctx["result"]["output"]["checksum_sha256"] is not None
    assert len(ctx["result"]["output"]["checksum_sha256"]) == 64  # SHA-256 hex


@then("el output incluye run_id igual al run_id del estado del pipeline")
def _run_id_igual(ctx):
    assert ctx["result"]["output"]["run_id"] == ctx["expected_run_id"]


@then(parsers.parse('retorna DataIngestionOutput con status "{status}"'))
def _retorna_status(ctx, status):
    assert ctx["result"]["status"] == status


@then("el output indica chunks_processed mayor a 1")
def _chunks_mayor_a_1(ctx):
    assert ctx["result"]["output"]["chunks_processed"] > 1


@then("el skill lanza SchemaValidationError")
def _lanza_schema_error(ctx):
    assert ctx["result"]["error_type"] == "SchemaValidationError"


@then(parsers.parse('NO se escribe ninguna fila en "{table}"'))
def _no_se_escribe_fila(ctx, table):
    assert ctx["result"]["status"] == "error"
    assert ctx["result"]["output"] == {}


@then("el skill lanza SourceNotFoundError")
def _lanza_source_not_found(ctx):
    assert ctx["result"]["error_type"] == "SourceNotFoundError"


@then("el skill lanza EmptySourceError")
def _lanza_empty_source(ctx):
    assert ctx["result"]["error_type"] == "EmptySourceError"


@then("el output indica dev_mode True")
def _dev_mode_true(ctx):
    assert ctx["result"]["output"]["dev_mode"] is True


@then("el output tiene checksum_sha256 nulo")
def _checksum_nulo(ctx):
    assert ctx["result"]["output"]["checksum_sha256"] is None


@then("retorna DataIngestionOutput con status success o success_with_warnings")
def _status_success_o_warnings(ctx):
    assert ctx["result"]["status"] in ("success", "success_with_warnings")
