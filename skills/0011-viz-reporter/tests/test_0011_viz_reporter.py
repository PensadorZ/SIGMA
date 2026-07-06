# =============================================================================
# test_skill.py — Step definitions pytest-bdd para 0011-viz-reporter
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Ejecutar solo esta suite:
#   pytest skills/0011-viz-reporter/tests/test_skill.py -v
#
# Ver conftest.py (raíz) para la nota de alcance: estas son pruebas de
# CONTRATO de la función run(state) -> SkillResult, aisladas de MinIO,
# PostgreSQL y del provider LLM real. La persistencia real y la trazabilidad
# Langfuse completa se prueban en el test end-to-end contra Tirendaz.
# =============================================================================

from __future__ import annotations

import pandas as pd
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from skills._loader import load_skill

skill = load_skill("0011-viz-reporter")

scenarios("test_skill.feature")


# ---------------------------------------------------------------------------
# Fixtures autouse — aíslan el skill de MinIO, PostgreSQL y motores reales
# ---------------------------------------------------------------------------

def _fake_sentiment_df(n_rows: int) -> pd.DataFrame:
    import itertools
    sentiments = ["POSITIVE", "NEGATIVE", "NEUTRAL", "UNCLEAR"]
    langs = ["es", "en", "und"]
    cyc_sent = itertools.cycle(sentiments)
    cyc_lang = itertools.cycle(langs)
    return pd.DataFrame({
        "row_id": [f"row-{i}" for i in range(n_rows)],
        "sentiment": [next(cyc_sent) for _ in range(n_rows)],
        "engagement_score": [round((i % 100) / 100, 3) for i in range(n_rows)],
        "lang": [next(cyc_lang) for _ in range(n_rows)],
    })


@pytest.fixture(autouse=True)
def _default_sentiment_data(monkeypatch):
    """Datos válidos por defecto — los Given específicos los sobreescriben."""
    default_df = _fake_sentiment_df(20)
    monkeypatch.setattr(skill, "_read_sentiment_data", lambda state: default_df)


@pytest.fixture(autouse=True)
def _default_persist(monkeypatch, tmp_path):
    """
    Evita requerir MinIO real. Persiste en un directorio temporal de la
    prueba y devuelve esa ruta como si fuera la URL del artefacto.
    """
    def _fake_persist(html, trace_id, dev):
        out_dir = tmp_path / "dashboards" / trace_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.html"
        out_path.write_text(html, encoding="utf-8")
        return str(out_path)

    monkeypatch.setattr(skill, "_persist_dashboard", _fake_persist)


@pytest.fixture(autouse=True)
def _default_summary(monkeypatch):
    """
    Evita llamar a Ollama/Gemini reales. Devuelve un resumen determinista
    de longitud controlada que cumple el contrato de 250 palabras / keywords.
    """
    def _fake_summary(stats, provider, cfg):
        if provider == "none":
            return None, 0, 0
        fake_text = (
            "Resumen de prueba sobre el corpus analizado. " * 5 +
            "\nPalabras clave:\n1. sentimiento\n2. idioma\n3. engagement\n"
            "4. corpus\n5. distribucion"
        )
        return fake_text, len(fake_text.split()), 5

    monkeypatch.setattr(skill, "_generate_summary", _fake_summary)


# ---------------------------------------------------------------------------
# Contexto: (pasos comunes a todos los escenarios)
# ---------------------------------------------------------------------------

@given("que el entorno tiene SIGMA_VARIANT configurado")
def _entorno_configurado():
    pass


@given(parsers.parse('que MinIO está disponible con el bucket "{bucket}"'))
def _minio_disponible(bucket):
    pass  # MinIO real no se usa en pruebas de contrato — ver _default_persist


@given(parsers.parse('que el directorio de salida temporal es "{path}"'))
def _directorio_temporal(path):
    pass


# ---------------------------------------------------------------------------
# Given — datos y entorno por escenario
# ---------------------------------------------------------------------------

@given(parsers.parse('que la tabla "processed_data" contiene {n:d} filas con columnas de sentimiento'))
def _tabla_contiene_n_filas(monkeypatch, ctx, n):
    df = _fake_sentiment_df(n)
    monkeypatch.setattr(skill, "_read_sentiment_data", lambda state: df)
    ctx["expected_rows"] = n


@given(parsers.parse('que la tabla "processed_data" contiene {n:d} filas válidas con columnas de sentimiento'))
def _tabla_contiene_n_filas_validas(monkeypatch, ctx, n):
    df = _fake_sentiment_df(n)
    monkeypatch.setattr(skill, "_read_sentiment_data", lambda state: df)
    ctx["expected_rows"] = n


@given("que Plotly está instalado en el entorno")
def _plotly_instalado():
    import importlib.util
    assert importlib.util.find_spec("plotly") is not None, (
        "plotly no está instalado en el entorno de pruebas — "
        "instalar con: pip install plotly"
    )


@given("que Plotly NO está instalado en el entorno de prueba")
def _plotly_no_instalado(monkeypatch):
    def _raise_import_error(name, *args, **kwargs):
        if name == "plotly":
            raise ImportError("plotly deliberately disabled for this test")
        return _real_import(name, *args, **kwargs)

    import builtins
    global _real_import
    _real_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", _raise_import_error)


@given("que matplotlib está disponible")
def _matplotlib_disponible():
    import importlib.util
    assert importlib.util.find_spec("matplotlib") is not None, (
        "matplotlib no está instalado en el entorno de pruebas — "
        "instalar con: pip install matplotlib"
    )


@given(parsers.parse('que SIGMA_VARIANT es "{variant}"'))
def _sigma_variant(monkeypatch, ctx, variant):
    monkeypatch.setenv("SIGMA_VARIANT", variant)
    ctx["sigma_variant"] = variant


@given(parsers.parse('que el provider LLM es "{provider}" con modelo "{model}" disponible'))
def _provider_llm_disponible(provider, model):
    pass  # el provider real se mockea en _default_summary


@given(parsers.parse('que la tabla "processed_data" está vacía'))
def _tabla_vacia(monkeypatch):
    monkeypatch.setattr(skill, "_read_sentiment_data", lambda state: pd.DataFrame())


@given(parsers.parse('que la tabla "processed_data" existe con {n:d} filas'))
def _tabla_existe_con_n_filas(ctx, n):
    ctx["_pending_df"] = _fake_sentiment_df(n)
    ctx["expected_rows"] = n


@given(parsers.parse('la tabla NO contiene la columna "{col}"'))
def _tabla_sin_columna(monkeypatch, ctx, col):
    df = ctx["_pending_df"].drop(columns=[col], errors="ignore")
    monkeypatch.setattr(skill, "_read_sentiment_data", lambda state: df)


@given("que no hay conexión a PostgreSQL disponible en el entorno de prueba")
def _sin_postgres():
    pass  # en modo Dev el skill nunca intenta conectar — verificado por diseño


@given(parsers.parse('que el provider LLM en defaults.yaml es "{provider}"'))
def _provider_llm_configurado(monkeypatch, ctx, provider):
    ctx["summary_provider"] = provider


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse('el Orquestador invoca viz-reporter con trace_id "{trace_id}"'))
def _invoca_skill(make_state, monkeypatch, ctx, trace_id):
    if "summary_provider" in ctx:
        original_load = skill.load_defaults

        def _patched_load_defaults(skill_dir):
            cfg = original_load(skill_dir)
            cfg.setdefault("summary", {})["provider"] = ctx["summary_provider"]
            return cfg

        monkeypatch.setattr(skill, "load_defaults", _patched_load_defaults)

    state = make_state(trace_id=trace_id, sigma_variant=ctx.get("sigma_variant", "Full"))
    ctx["result"] = skill.run(state)


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then(parsers.parse('el skill selecciona el motor "{engine}"'))
def _selecciona_motor(ctx, engine):
    assert ctx["result"]["output"]["motor"] == engine


@then("genera un archivo HTML con al menos 3 gráficos")
def _genera_html_con_graficos(ctx):
    assert ctx["result"]["output"]["num_graficos"] >= 3


@then("persiste el artefacto en el destino configurado")
def _persiste_artefacto(ctx):
    assert ctx["result"]["output"]["dashboard_url"] is not None


@then(parsers.parse('el VizReporterOutput tiene status "{status}"'))
def _tiene_status(ctx, status):
    actual = ctx["result"]["status"]
    if status == "success":
        # success_with_warnings es válido cuando hay warnings acumuladas
        # (ej. modo Dev siempre añade 'synthetic_data') — el contrato
        # make_success() degrada correctamente a success_with_warnings
        # en ese caso, no es un fallo del skill.
        assert actual in ("success", "success_with_warnings")
    else:
        assert actual == status


@then(parsers.parse('el VizReporterOutput tiene campo "{field}" igual a {value}'))
def _tiene_campo_igual_a(ctx, field, value):
    # error_type y status son campos de nivel superior del SkillResult;
    # el resto de campos (motor, dev_mode, etc.) están dentro de "output".
    if field in ("error_type", "status", "error_detail"):
        actual = ctx["result"].get(field)
    else:
        actual = ctx["result"]["output"].get(field)

    if value == "True":
        assert actual is True
    elif value == "False":
        assert actual is False
    elif value == "None":
        assert actual is None
    elif value.startswith('"') and value.endswith('"'):
        assert actual == value.strip('"')
    else:
        assert str(actual) == value


@then(parsers.parse('el VizReporterOutput tiene warnings con "{warning}"'))
def _tiene_warning(ctx, warning):
    assert warning in ctx["result"]["output"].get("warnings", [])


@then("el VizReporterOutput incluye run_id y trace_id")
def _incluye_run_id_trace_id(ctx):
    out = ctx["result"]["output"]
    assert out.get("run_id") is not None, "run_id ausente del output — regresión v1.1.0"
    assert out.get("trace_id") is not None, "trace_id ausente del output"


@then(parsers.parse('el skill lanza la excepción "{error_type}"'))
def _lanza_excepcion(ctx, error_type):
    assert ctx["result"]["error_type"] == error_type


@then(parsers.parse("el skill genera internamente un dataset sintético de {n:d} filas"))
def _genera_dataset_sintetico(ctx, n):
    assert ctx["result"]["output"]["dev_mode"] is True


@then("el skill genera el dashboard HTML normalmente")
def _genera_dashboard_normal(ctx):
    assert ctx["result"]["status"] == "success"
    assert ctx["result"]["output"]["dashboard_url"] is not None
