# =============================================================================
# skills/0004-statistical-validator/tests/test_0004_statistical_validator.py
# Step definitions pytest-bdd para 0004
# SIGMA v1.5 · Hito 2, Engineer Datos
# Autor: Prof. Marx Agustin Garcia Delgado
# Version: 1.0.0
# =============================================================================
# Carga el skill via _loader.load_skill() -- import por puntos es
# SyntaxError con carpetas "0004-..." (ver _loader.py). policies.yaml se
# mockea via monkeypatch sobre mod._load_policies, unico punto de
# inyeccion posible dado que skill.py lo lee de disco por diseno.
# =============================================================================

"""
Steps pytest-bdd para 0004-statistical-validator.

CORREGIDO: la carpeta del skill empieza con dígito y tiene guiones
('0004-statistical-validator'), que NO es un identificador Python
válido — _loader.py existe precisamente porque
`from sigma.skills.0004-statistical-validator.skill import run` es un
SyntaxError. Se usa `load_skill()` por ruta de archivo, como documenta
_loader.py, no un import con puntos (mi primera versión de este archivo
tenía ese error).

Usa las fixtures compartidas `ctx` y `make_state` del conftest.py raíz
del repo (AGENTS_CREATOR.md §5).

NOTA DE VERIFICACIÓN: `make_state` se asume capaz de recibir kwargs
arbitrarios y completar los campos obligatorios de PipelineState
(trace_id, pipeline_run_id, sigma_variant, etc.) con valores por
defecto — no vi el conftest.py real. Si su firma difiere, ajusta los
`given` de abajo.

`policies.yaml` se mockea vía monkeypatch sobre `mod._load_policies`
directamente en el módulo cargado, ya que no hay forma de inyectarlo
como parámetro (skill.py lo lee de disco por diseño — ver skill.py).
"""
import numpy as np
import pandas as pd
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from sigma.skills._common import is_dev_mode
from sigma.skills._loader import load_skill

scenarios("test_statistical_validator.feature")

mod = load_skill("0004-statistical-validator")

_DEFAULT_POLICIES = {
    "statistical_validator": {
        "drift_method": "ks_test",
        "drift_threshold": 0.05,
        "leakage_correlation_threshold": 0.95,
        "leakage_temporal_threshold": 0.85,
        "bayes_factor_min": 3.0,
        "permutation_ci_width_max": 0.5,
        "bayesian_ab_min_samples": 30,
    }
}


@pytest.fixture(autouse=True)
def _default_policies(monkeypatch):
    monkeypatch.setattr(mod, "_load_policies", lambda: _DEFAULT_POLICIES)


@pytest.fixture(autouse=True)
def _no_real_postgres(monkeypatch):
    """
    CORRECCIÓN: sin esto, los tests de Modo A (significancia) y de error
    intentaban conectar a PostgreSQL real, porque make_state() no fija
    sigma_variant='Dev' por defecto (queda en 'Full', igual que en los
    escenarios reales de este pipeline). Los escenarios que sí necesitan
    un DataFrame específico (drift, leakage) inyectan su propio 'df' en
    el estado vía make_state(df=...) — este mock genérico solo cubre los
    casos donde _read_processed_data() se llamaría de otro modo.
    """
    original = mod._read_processed_data

    def _fake_read_processed_data(state):
        if "df" in state:
            # df=None explícito simula ausencia real de datos (dispara
            # InputSchemaError vía el chequeo df.empty en skill.py) —
            # un DataFrame real se usa tal cual (escenarios drift/leakage).
            return pd.DataFrame() if state["df"] is None else state["df"]
        if is_dev_mode(state):
            return original(state)
        return pd.DataFrame({
            "row_id": [f"t-{i}" for i in range(20)],
            "engagement_score": np.random.default_rng(1).uniform(0, 1, 20),
        })

    monkeypatch.setattr(mod, "_read_processed_data", _fake_read_processed_data)


# ── Contexto (Background) ──

@given("que el input fue validado por 0002-data-cleanser")
def _():
    pass  # cada escenario construye su propio DataFrame ya "validado" en su Given específico


@given("que policies.yaml está disponible")
def _():
    pass  # cubierto por el fixture autouse _default_policies


# ── Given ──

@given("un DataFrame validado con dos grupos y una hipótesis explícita declarada", target_fixture="state")
def _(make_state):
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "group": ["a"] * 20 + ["b"] * 20,
        "metric": list(rng.normal(0, 1, 20)) + list(rng.normal(0.1, 1, 20)),
    })
    hypothesis = {"group_col": "group", "group_a": "a", "group_b": "b", "metric_col": "metric"}
    return make_state(df=df, hypothesis=hypothesis)


@given("policies.yaml define un bayes_factor_min alto")
def _(monkeypatch):
    policies = {**_DEFAULT_POLICIES, "statistical_validator": {**_DEFAULT_POLICIES["statistical_validator"], "bayes_factor_min": 1e6}}
    monkeypatch.setattr(mod, "_load_policies", lambda: policies)


@given("un DataFrame validado con índice temporal", target_fixture="state")
def _(make_state):
    rng = np.random.default_rng(1)
    df = pd.DataFrame({
        "ts": pd.date_range("2026-01-01", periods=50, freq="D"),
        "value": rng.normal(0, 1, 50),
    })
    return make_state(df=df, datetime_index="ts")


@given("un DataFrame validado sin hipótesis y distribución desconocida", target_fixture="state")
def _(make_state):
    rng = np.random.default_rng(2)
    df = pd.DataFrame({"value": rng.uniform(0, 100, 30)})
    return make_state(df=df, no_hypothesis_distribution_unknown=True)


@given("policies.yaml define un permutation_ci_width_max bajo")
def _(monkeypatch):
    policies = {**_DEFAULT_POLICIES, "statistical_validator": {**_DEFAULT_POLICIES["statistical_validator"], "permutation_ci_width_max": 1e-6}}
    monkeypatch.setattr(mod, "_load_policies", lambda: policies)


@given("un DataFrame con feedback en vivo con menos muestras que el mínimo configurado", target_fixture="state")
def _(make_state):
    feedback = {"arms": [{"samples": [1, 2]}, {"samples": [1]}]}
    df = pd.DataFrame({"value": [1, 2, 3]})
    return make_state(df=df, live_feedback=feedback)


@given("policies.yaml define un bayesian_ab_min_samples")
def _():
    pass  # ya cubierto por _default_policies (autouse)


@given("un DataFrame validado sin hipótesis, sin índice temporal y sin feedback en vivo", target_fixture="state")
def _(make_state):
    df = pd.DataFrame({"a": [1, 2, None, 4], "b": [1, 1, 2, 2]})
    return make_state(df=df)


@given("policies.yaml no define bayes_factor_min")
def _(monkeypatch):
    policies = {"statistical_validator": {k: v for k, v in _DEFAULT_POLICIES["statistical_validator"].items() if k != "bayes_factor_min"}}
    monkeypatch.setattr(mod, "_load_policies", lambda: policies)


@given("un DataFrame actual y un DataFrame baseline con distribuciones distintas", target_fixture="state")
def _(make_state):
    rng = np.random.default_rng(3)
    current = pd.DataFrame({"value": rng.normal(5, 1, 40)})
    baseline = pd.DataFrame({"value": rng.normal(0, 1, 40)})
    return make_state(df=current, baseline_df=baseline)


@given("un DataFrame con una columna casi idéntica a la columna objetivo", target_fixture="state")
def _(make_state):
    rng = np.random.default_rng(4)
    target = rng.normal(0, 1, 40)
    df = pd.DataFrame({"target": target, "leaky_feature": target + rng.normal(0, 0.001, 40)})
    return make_state(df=df, leakage_target_col="target")


@given('un estado sin la clave "df" validada por 0002-data-cleanser', target_fixture="state")
def _(make_state):
    return make_state(df=None)


@given("un DataFrame validado con hipótesis explícita pero menos de 2 filas por grupo", target_fixture="state")
def _(make_state):
    df = pd.DataFrame({"group": ["a", "b"], "metric": [1.0, 2.0]})
    hypothesis = {"group_col": "group", "group_a": "a", "group_b": "b", "metric_col": "metric"}
    return make_state(df=df, hypothesis=hypothesis)


@given(parsers.parse('un estado con sigma_variant en "{variant}"'), target_fixture="state")
def _(make_state, variant):
    return make_state(sigma_variant=variant)


@given("un DataFrame sintético generado localmente sin infraestructura real", target_fixture="state")
def _(state):
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    state["df"] = df
    return state


# ── When ──

@when(parsers.parse('se ejecuta statistical-validator con trace_id "{trace_id}" en modo significancia'), target_fixture="result")
def _(state, trace_id):
    state["trace_id"] = trace_id
    return mod.run(state)


@when(parsers.parse('se ejecuta statistical-validator con trace_id "{trace_id}" en modo drift'), target_fixture="result")
def _(state, trace_id):
    state["trace_id"] = trace_id
    return mod.run(state)


@when(parsers.parse('se ejecuta statistical-validator con trace_id "{trace_id}" en modo leakage'), target_fixture="result")
def _(state, trace_id):
    state["trace_id"] = trace_id
    return mod.run(state)


# ── Then ──

@then(parsers.parse('la rama seleccionada es "{branch}"'))
def _(result, branch):
    assert result["output"]["branch"] == branch


@then(parsers.parse('el veredicto es "{verdict}"'))
def _(result, verdict):
    assert result["output"]["verdict"] == verdict


@then(parsers.parse('el método usado es "{method}"'))
def _(result, method):
    assert result["output"]["detail"]["method"] == method


@then(parsers.parse('retorna status "{status}"'))
def _(result, status):
    assert result["status"] == status


@then(parsers.parse('el error menciona "{needle}"'))
def _(result, needle):
    assert needle in (result["error_type"] or "") or needle.lower() in (result["error_detail"] or "").lower()


@then("el output indica dev_mode True")
def _(result):
    assert result["output"]["dev_mode"] is True
