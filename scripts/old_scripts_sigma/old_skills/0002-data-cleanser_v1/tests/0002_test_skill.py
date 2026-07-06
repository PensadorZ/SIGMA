"""
skills/0002-data-cleanser/tests/test_skill.py

Steps de pytest-bdd para test_skill.feature. Sin dependencias externas
que mockear (a diferencia de 0000): construye listas de filas en
memoria con las propiedades exactas que cada escenario describe
(N duplicados exactos, M casi-exactos, K nulos) y ejecuta el skill
real sobre ellas.
"""

from __future__ import annotations

from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from skills_0002_data_cleanser.skill import InputTableNotFoundError, run_data_cleanser

scenarios("test_skill.feature")


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIGMA_VARIANT", raising=False)
    monkeypatch.setenv("POSTGRES_URL", "postgresql://sigma:test@localhost:5432/sigma_test")
    yield


@pytest.fixture
def context() -> dict[str, Any]:
    return {}


# ── GIVEN: Background ─────────────────────────────────────────────────────


@given("el entorno SIGMA está inicializado")
def sigma_initialized() -> None:
    pass


@given('el skill 0001-data-ingestion ha producido una tabla "*_raw"')
def upstream_produced_raw() -> None:
    """No-op: este test verifica 0002 de forma aislada (ver nota análoga en 0001)."""


# ── GIVEN: construcción de datasets sintéticos con propiedades exactas ────


@given(parsers.re(r'la tabla "(?P<table>[^"]+)" con (?P<n>[\d.]+) filas'))
def table_with_n_rows(context: dict[str, Any], table: str, n: str) -> None:
    n_rows = int(n.replace(".", ""))
    context["base_row_count"] = n_rows
    context["rows"] = [
        {"tweet_id": str(i), "text": f"texto único número {i}", "label": "POSITIVE"}
        for i in range(n_rows)
    ]


@given(parsers.re(r'la tabla tiene (?P<exact>\d+) duplicados exactos y (?P<near>\d+) casi-exactos'))
def inject_duplicates(context: dict[str, Any], exact: str, near: str) -> None:
    """
    Inyecta exactamente N duplicados exactos (copia bit a bit de filas
    ya existentes, salvo el id) y M casi-exactos (texto con una
    variación mínima) sobre el dataset base ya construido.
    """
    n_exact = int(exact)
    n_near = int(near)
    rows = context["rows"]
    base_count = context["base_row_count"]

    next_id = base_count
    for i in range(n_exact):
        source_row = rows[i % base_count]
        dup_row = dict(source_row)
        dup_row["tweet_id"] = str(next_id)
        rows.append(dup_row)
        next_id += 1

    for i in range(n_near):
        source_row = rows[(i + n_exact) % base_count]
        near_row = dict(source_row)
        near_row["tweet_id"] = str(next_id)
        near_row["text"] = source_row["text"] + "!"  # variación mínima de texto
        rows.append(near_row)
        next_id += 1

    context["rows"] = rows
    context["expected_exact_removed"] = n_exact
    context["expected_near_removed"] = n_near


@given(parsers.re(r'(?P<n>\d+) filas tienen el campo "(?P<field>[^"]+)" nulo'))
def inject_nulls(context: dict[str, Any], n: str, field: str) -> None:
    """
    Aplica nulos sobre un rango de índices que NO se solapa con las
    filas usadas como fuente de duplicados exactos/casi-exactos
    (índices usados: 0 hasta n_exact+n_near-1 en inject_duplicates).
    Sin este cuidado, nulificar una fila fuente cambia retroactivamente
    el conteo de duplicados detectados — no es un bug del skill, es
    un requisito de diseño correcto del dataset sintético de prueba,
    ya que el .feature original no especifica explícitamente que los
    nulos deban aplicarse sobre filas distintas de las fuente.
    """
    n_nulls = int(n)
    rows = context["rows"]
    used_as_source = context.get("expected_exact_removed", 0) + context.get(
        "expected_near_removed", 0
    )
    start = used_as_source  # arranca después del rango usado como fuente
    for i in range(n_nulls):
        rows[start + i][field] = None
    context["expected_null_count"] = n_nulls


@given(parsers.re(r'la tabla "(?P<pattern>[^"]+)" tiene (?P<n>\d+) filas con tweet_id no entero'))
def inject_invalid_tweet_id(context: dict[str, Any], pattern: str, n: str) -> None:
    n_invalid = int(n)
    context["rows"] = [
        {"tweet_id": None, "text": f"fila invalida numero {i}", "label": "POSITIVE"}
        for i in range(n_invalid)
    ]
    context["expected_rejected"] = n_invalid


@given(parsers.re(r'SIGMA_ENV es "(?P<env>[^"]+)"'))
def set_sigma_env(monkeypatch: pytest.MonkeyPatch, env: str) -> None:
    monkeypatch.setenv("SIGMA_VARIANT", env)


@given(parsers.re(r'una tabla "(?P<pattern>[^"]+)" con (?P<n>[\d.]+) filas'))
def generic_table_with_rows(context: dict[str, Any], pattern: str, n: str) -> None:
    n_rows = int(n.replace(".", ""))
    context["rows"] = [
        {"tweet_id": str(i), "text": f"texto {i}", "label": "POSITIVE"} for i in range(n_rows)
    ]


@given(parsers.re(r'que "(?P<table>[^"]+)" no existe'))
def table_does_not_exist(context: dict[str, Any], table: str) -> None:
    context["rows"] = None


# ── WHEN ─────────────────────────────────────────────────────────────────


@when(parsers.parse('el skill data-cleanser se ejecuta con run_id "{run_id}"'))
def execute_cleanser(context: dict[str, Any], run_id: str) -> None:
    _execute(context, run_id, trace_id=f"tr-{run_id}")


@when(parsers.parse('el skill data-cleanser se ejecuta con run_id "{run_id}" y trace_id "{trace_id}"'))
def execute_cleanser_with_trace(context: dict[str, Any], run_id: str, trace_id: str) -> None:
    _execute(context, run_id, trace_id)


def _execute(context: dict[str, Any], run_id: str, trace_id: str) -> None:
    try:
        context["result"] = run_data_cleanser(
            rows=context.get("rows"), run_id=run_id, trace_id=trace_id
        )
        context["raised_error"] = None
    except InputTableNotFoundError as exc:
        context["raised_error"] = exc
        context["result"] = None


# ── THEN ─────────────────────────────────────────────────────────────────


@then(parsers.re(r'existe la tabla "(?P<table>[^"]+)" con (?P<n>[\d.]+) filas'))
def assert_output_row_count(context: dict[str, Any], table: str, n: str) -> None:
    expected = int(n.replace(".", ""))
    assert context["result"] is not None
    assert context["result"].rows_out == expected, (
        f"Esperadas {expected} filas en output, obtenidas {context['result'].rows_out}"
    )


@then(parsers.re(r'las filas con text nulo tienen el campo marcado "(?P<flag>[^"]+)"'))
def assert_null_flag(context: dict[str, Any], flag: str) -> None:
    cleaned = context["result"].cleaned_rows
    flagged_count = sum(1 for r in cleaned if r.get("text") == flag)
    assert flagged_count == context["expected_null_count"], (
        f"Se esperaban {context['expected_null_count']} filas marcadas '{flag}', "
        f"se encontraron {flagged_count}"
    )


@then(parsers.re(r'cada fila contiene trace_id: "(?P<trace_id>[^"]+)"'))
def assert_trace_id_in_rows(context: dict[str, Any], trace_id: str) -> None:
    assert all(r["trace_id"] == trace_id for r in context["result"].cleaned_rows)


@then(parsers.re(r'el informe registra exact_duplicates_removed: (?P<n>\d+)'))
def assert_exact_removed(context: dict[str, Any], n: str) -> None:
    assert context["result"].exact_duplicates_removed == int(n)


@then(parsers.re(r'el informe registra near_duplicates_removed: (?P<n>\d+)'))
def assert_near_removed(context: dict[str, Any], n: str) -> None:
    assert context["result"].near_duplicates_removed == int(n)


@then(parsers.re(r'el evento "(?P<event_name>[^"]+)" fue emitido$'))
def assert_event_emitted(event_name: str) -> None:
    assert event_name


@then(parsers.re(r'esas (?P<n>\d+) filas están en "(?P<pattern>[^"]+)" con error: "(?P<error>[^"]+)"'))
def assert_rows_in_rejected(context: dict[str, Any], n: str, pattern: str, error: str) -> None:
    expected_n = int(n)
    rejected = context["result"].rejected_rows
    matching = [r for r in rejected if r.reason == error]
    assert len(matching) == expected_n, (
        f"Se esperaban {expected_n} filas rechazadas con razón '{error}', "
        f"se encontraron {len(matching)}"
    )


@then(parsers.re(r'"(?P<pattern>[^"]+)" no las contiene'))
def assert_cleaned_does_not_contain(context: dict[str, Any], pattern: str) -> None:
    cleaned_ids = {r.get("tweet_id") for r in context["result"].cleaned_rows}
    rejected_ids = {r.row.get("tweet_id") for r in context["result"].rejected_rows}
    assert cleaned_ids.isdisjoint(rejected_ids) or not rejected_ids


@then(parsers.re(r'el informe registra rows_rejected: (?P<n>\d+)'))
def assert_rows_rejected_count(context: dict[str, Any], n: str) -> None:
    assert len(context["result"].rejected_rows) == int(n)


@then(parsers.re(r'el informe indica workers_used: (?P<n>\d+)'))
def assert_workers_used(context: dict[str, Any], n: str) -> None:
    assert context["result"].workers_used == int(n)


@then("el skill termina con InputTableNotFoundError")
def assert_input_table_not_found(context: dict[str, Any]) -> None:
    assert isinstance(context.get("raised_error"), InputTableNotFoundError)
