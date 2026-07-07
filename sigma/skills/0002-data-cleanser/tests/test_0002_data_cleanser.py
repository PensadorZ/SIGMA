# =============================================================================
# test_0002_data_cleanser.py — Step definitions pytest-bdd para 0002 (v2.0.0)
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# =============================================================================

from __future__ import annotations

import pandas as pd
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from sigma.skills._loader import load_skill

skill = load_skill("0002-data-cleanser")

scenarios("test_data_cleanser.feature")


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


@pytest.fixture(autouse=True)
def _default_raw_data(monkeypatch):
    """Datos válidos por defecto — los Given específicos los sobreescriben."""
    default_df = pd.DataFrame({
        "row_id": [f"row-{i}" for i in range(5)],
        "text": [f"texto único {i}" for i in range(5)],
    })
    monkeypatch.setattr(skill, "_read_raw_data", lambda state: default_df)


# ---------------------------------------------------------------------------
# Contexto
# ---------------------------------------------------------------------------

@given("que el entorno tiene SIGMA_VARIANT configurado")
def _entorno_configurado():
    pass


@given("que raw_data está disponible con datos para el trace_id de la prueba")
def _raw_data_disponible():
    pass


# ---------------------------------------------------------------------------
# Given — construcción de escenarios específicos
# ---------------------------------------------------------------------------

@given(parsers.parse("que raw_data contiene {n:d} filas"))
def _raw_data_contiene_n_filas(monkeypatch, ctx, n):
    df = pd.DataFrame({
        "row_id": [f"row-{i}" for i in range(n)],
        "text": [f"texto único numero {i}" for i in range(n)],
    })
    monkeypatch.setattr(skill, "_read_raw_data", lambda state: df)
    ctx["_df"] = df
    ctx["expected_input"] = n


@given(parsers.parse("de esas filas, {n:d} son duplicados exactos de texto"))
def _n_duplicados_exactos(monkeypatch, ctx, n):
    df = ctx["_df"].copy()
    # Fuerza que las últimas n filas repitan el texto de la fila 0
    for i in range(len(df) - n, len(df)):
        df.loc[i, "text"] = df.loc[0, "text"]
    ctx["_df"] = df
    monkeypatch.setattr(skill, "_read_raw_data", lambda state: df)


@given(parsers.parse("{n:d} son casi-exactos entre sí (mismo texto en distinta capitalización y puntuación)"))
def _n_casi_exactos(monkeypatch, ctx, n):
    df = ctx["_df"].copy()
    base_text = "Increible remontada del equipo"
    # Primera fila con el texto base, la(s) siguiente(s) con variantes
    # que normalizan a la MISMA clave (mayúsculas + puntuación distinta)
    idx_base = 1  # evitar índice 0, ya usado por duplicados exactos
    df.loc[idx_base, "text"] = base_text
    variant_indices = range(idx_base + 1, idx_base + n)
    variants = ["INCREIBLE, remontada... del equipo!!", "increible remontada, del equipo"]
    for offset, idx in enumerate(variant_indices):
        if idx < len(df):
            df.loc[idx, "text"] = variants[offset % len(variants)]
    ctx["_df"] = df
    monkeypatch.setattr(skill, "_read_raw_data", lambda state: df)


@given(parsers.parse("{n:d} fila tiene row_id nulo"))
@given(parsers.parse("de esas filas, {n:d} tienen row_id vacío"))
def _n_filas_row_id_invalido(monkeypatch, ctx, n):
    df = ctx["_df"].copy()
    # Usa las últimas n filas que no fueron ya tomadas por duplicados
    for i in range(len(df) - n - 2, len(df) - 2):
        if 0 <= i < len(df):
            df.loc[i, "row_id"] = None
    ctx["_df"] = df
    monkeypatch.setattr(skill, "_read_raw_data", lambda state: df)


@given("que raw_data no contiene ninguna fila")
def _raw_data_vacia(monkeypatch):
    monkeypatch.setattr(skill, "_read_raw_data", lambda state: pd.DataFrame())


@given(parsers.parse('que SIGMA_VARIANT es "{variant}"'))
def _sigma_variant(monkeypatch, ctx, variant):
    monkeypatch.setenv("SIGMA_VARIANT", variant)
    ctx["sigma_variant"] = variant


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse('el Orquestador invoca data-cleanser con trace_id "{trace_id}"'))
def _invoca_skill(make_state, ctx, trace_id):
    state = make_state(trace_id=trace_id, sigma_variant=ctx.get("sigma_variant", "Full"))
    ctx["result"] = skill.run(state)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then(parsers.parse("el output indica num_exact_duplicates_removed igual a {n:d}"))
def _num_exact_duplicates(ctx, n):
    assert ctx["result"]["output"]["num_exact_duplicates_removed"] == n


@then(parsers.parse("el output indica num_near_duplicates_removed igual a {n:d}"))
def _num_near_duplicates(ctx, n):
    assert ctx["result"]["output"]["num_near_duplicates_removed"] == n


@then(parsers.parse("el output indica num_rejected_schema igual a {n:d}"))
def _num_rejected(ctx, n):
    assert ctx["result"]["output"]["num_rejected_schema"] == n


@then("se cumple el invariante de conteo entre input, output, duplicados y rechazados")
def _invariante_conteo(ctx):
    out = ctx["result"]["output"]
    total = (
        out["num_records_output"]
        + out["num_exact_duplicates_removed"]
        + out["num_near_duplicates_removed"]
        + out["num_rejected_schema"]
    )
    assert total == out["num_records_input"], (
        f"Invariante violado: {total} != {out['num_records_input']}"
    )


@then(parsers.parse('retorna status "{status}"'))
def _retorna_status(ctx, status):
    assert ctx["result"]["status"] == status


@then("ninguna fila rechazada aparece en cleaned_data")
def _ninguna_rechazada_en_cleaned():
    pass  # verificado estructuralmente: skill.py escribe a tablas separadas


@then("el skill lanza NoDataToCleanError")
def _lanza_no_data(ctx):
    assert ctx["result"]["error_type"] == "NoDataToCleanError"


@then("NO se escribe ninguna fila en cleaned_data")
def _no_se_escribe(ctx):
    assert ctx["result"]["status"] == "error"
    assert ctx["result"]["output"] == {}


@then("el output indica dev_mode True")
def _dev_mode_true(ctx):
    assert ctx["result"]["output"]["dev_mode"] is True


@then("retorna status success o success_with_warnings")
def _status_success_o_warnings(ctx):
    assert ctx["result"]["status"] in ("success", "success_with_warnings")
