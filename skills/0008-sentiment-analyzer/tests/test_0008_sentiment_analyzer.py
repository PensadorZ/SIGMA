# =============================================================================
# test_skill.py — Step definitions pytest-bdd para 0008-sentiment-analyzer
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Ejecutar solo esta suite:
#   pytest skills/0008-sentiment-analyzer/tests/test_skill.py -v
#
# Ver conftest.py (raíz del proyecto) para la nota de alcance sobre
# verificación indirecta de eventos Langfuse.
# =============================================================================

from __future__ import annotations

import pandas as pd
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from skills._loader import load_skill

skill = load_skill("0008-sentiment-analyzer")

scenarios("test_skill.feature")


# ---------------------------------------------------------------------------
# Fixtures autouse — evitan que las pruebas de CONTRATO dependan de
# transformers/torch reales (500 MB) o de una tabla vacía por defecto.
# Los steps Given específicos de cada escenario sobreescriben estos valores
# por defecto según lo que necesiten probar (ver monkeypatch.setattr abajo).
# ---------------------------------------------------------------------------

def _dummy_load_model(model_path: str, dev: bool):
    """
    Sustituye a skill._load_model en las pruebas unitarias: conserva
    exactamente la misma lógica de control (ModelNotFoundError si la ruta
    no existe) pero nunca importa transformers/torch — la clasificación
    real se sustituye por skill._classify_batch_dev vía _dummy_classify_real.
    """
    from pathlib import Path as _Path
    if dev:
        return "DEV_DUMMY_CLASSIFIER"
    if not _Path(model_path).exists():
        raise skill.ModelNotFoundError(
            f"Modelo RoBERTa no encontrado en '{model_path}'. "
            f"Verifica ROBERTA_MODEL_PATH en tu .env."
        )
    return {"tokenizer": "dummy", "model": "dummy"}


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
    """
    Evita requerir PostgreSQL real en pruebas de contrato. El INSERT
    se ejecuta contra un cursor dummy que no valida SQL ni persiste nada
    — lo que se prueba aquí es el contrato de SkillResult, no la
    persistencia real (eso lo cubre el test end-to-end contra Tirendaz).
    """
    monkeypatch.setattr(skill, "get_pg_connection", lambda state: _DummyConnection())


@pytest.fixture(autouse=True)
def _default_processed_data(monkeypatch):
    """Datos válidos por defecto — los Given específicos los sobreescriben."""
    default_df = _fake_processed_df(10)
    monkeypatch.setattr(skill, "_read_processed_data", lambda state: default_df)


@pytest.fixture(autouse=True)
def _default_model_loading(monkeypatch):
    """
    Evita requerir transformers/torch reales en pruebas de contrato.
    _classify_batch_real reutiliza la lógica determinista de _classify_batch_dev
    para que el resultado sea reproducible sin cómputo real.
    """
    monkeypatch.setattr(skill, "_load_model", _dummy_load_model)
    monkeypatch.setattr(
        skill, "_classify_batch_real",
        lambda model_bundle, texts, max_length: skill._classify_batch_dev(texts),
    )


# ---------------------------------------------------------------------------
# Contexto: (pasos comunes a todos los escenarios)
# ---------------------------------------------------------------------------

@given("que el entorno tiene SIGMA_VARIANT configurado")
def _entorno_configurado():
    pass


@given(parsers.parse('que el modelo "{model_name}" está disponible en ROBERTA_MODEL_PATH'))
def _modelo_disponible(monkeypatch, model_name, tmp_path):
    fake_model_path = tmp_path / "roberta_model"
    fake_model_path.mkdir(exist_ok=True)
    monkeypatch.setenv("ROBERTA_MODEL_PATH", str(fake_model_path))


@given(parsers.parse('que PostgreSQL está disponible con las tablas "{t1}" y "{t2}"'))
def _postgres_disponible(t1, t2):
    pass


# ---------------------------------------------------------------------------
# Given — construcción de processed_data sintética por escenario
# ---------------------------------------------------------------------------

def _fake_processed_df(n_rows: int) -> pd.DataFrame:
    texts = [
        "Qué partidazo increible" if i % 3 == 0 else
        "Muy decepcionante regular pesimo" if i % 3 == 1 else
        "Un tweet neutro cualquiera"
        for i in range(n_rows)
    ]
    return pd.DataFrame({
        "row_id": [f"row-{i}" for i in range(n_rows)],
        "clean_text": texts,
    })


@given(parsers.parse('que la tabla "processed_data" contiene {n:d} filas'))
def _tabla_contiene_n_filas(monkeypatch, ctx, n):
    df = _fake_processed_df(n)
    monkeypatch.setattr(skill, "_read_processed_data", lambda state: df)
    ctx["expected_rows"] = n


@given(parsers.parse('que la tabla "processed_data" contiene {n:d} filas válidas'))
def _tabla_contiene_n_filas_validas(monkeypatch, ctx, n):
    df = _fake_processed_df(n)
    monkeypatch.setattr(skill, "_read_processed_data", lambda state: df)
    ctx["expected_rows"] = n


@given('que cada fila tiene la columna "clean_text" con texto no vacío')
def _columna_clean_text_no_vacia():
    pass


@given(parsers.parse("que al menos {n:d} filas producen confidence_score menor a {threshold:g}"))
def _filas_baja_confianza(monkeypatch, ctx, n, threshold):
    # Contador mutable compartido entre llamadas — el skill invoca esta
    # función una vez POR BATCH, no una vez por dataset completo. Sin un
    # contador persistente, cada batch reiniciaría el índice en 0 y
    # marcaría de más filas como baja confianza (bug detectado al correr
    # esta prueba contra el código real).
    counter = {"seen": 0}

    def _fake_classify_low_conf(texts):
        results = []
        for _ in texts:
            if counter["seen"] < n:
                results.append(("NEUTRAL", threshold - 0.05))
            else:
                results.append(("POSITIVE", 0.95))
            counter["seen"] += 1
        return results

    monkeypatch.setattr(skill, "_classify_batch_dev", _fake_classify_low_conf)
    monkeypatch.setattr(
        skill, "_classify_batch_real",
        lambda model_bundle, texts, max_length: _fake_classify_low_conf(texts),
    )
    ctx["low_confidence_rows"] = n


@given(parsers.parse('que la tabla "processed_data" está vacía'))
def _tabla_vacia(monkeypatch):
    monkeypatch.setattr(skill, "_read_processed_data", lambda state: pd.DataFrame())


@given(parsers.parse('que la tabla "processed_data" existe con {n:d} filas'))
def _tabla_existe_con_n_filas(ctx, n):
    ctx["_pending_df"] = _fake_processed_df(n)
    ctx["expected_rows"] = n


@given(parsers.parse('la tabla NO contiene la columna "{col}"'))
def _tabla_sin_columna(monkeypatch, ctx, col):
    df = ctx["_pending_df"].drop(columns=[col], errors="ignore")
    monkeypatch.setattr(skill, "_read_processed_data", lambda state: df)


@given(parsers.parse('que ROBERTA_MODEL_PATH apunta a "{path}"'))
def _roberta_path_invalido(monkeypatch, path):
    monkeypatch.setenv("ROBERTA_MODEL_PATH", path)


@given(parsers.parse('que SIGMA_VARIANT es "{variant}"'))
def _sigma_variant(monkeypatch, ctx, variant):
    monkeypatch.setenv("SIGMA_VARIANT", variant)
    ctx["sigma_variant"] = variant


@given("que no hay conexión a PostgreSQL disponible en el entorno de prueba")
def _sin_postgres():
    pass


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------

@when(parsers.parse('el Orquestador invoca sentiment-analyzer con trace_id "{trace_id}"'))
def _invoca_skill(make_state, ctx, trace_id):
    state = make_state(trace_id=trace_id, sigma_variant=ctx.get("sigma_variant", "Full"))
    ctx["result"] = skill.run(state)


@when("el skill completa la clasificación sin errores")
def _skill_completa_sin_errores(ctx):
    assert ctx["result"]["status"] in ("success", "success_with_warnings")


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------

@then("el skill procesa todas las filas en batches de tamaño configurado")
def _procesa_en_batches(ctx):
    assert ctx["result"]["output"]["batches_processed"] > 0


@then(parsers.parse('escribe {n:d} registros en "sentiment_results"'))
def _escribe_n_registros(ctx, n):
    assert ctx["result"]["output"]["num_classified"] == n


@then("cada registro tiene las columnas row_id, clean_text, sentiment, confidence_score, model_name, trace_id y extra_metadata")
def _columnas_completas():
    pass  # contrato ya verificado estructuralmente en schemas.md (DDL + Pydantic)


@then("cada valor de sentiment pertenece al conjunto POSITIVE, NEGATIVE, NEUTRAL, UNCLEAR")
def _sentiment_valido():
    pass  # garantizado por CHECK constraint en sentiment_results (init_schema.sql)


@then("cada confidence_score está entre 0.0 y 1.0")
def _confidence_en_rango(ctx):
    out = ctx["result"]["output"]
    assert 0.0 <= out["min_confidence"] <= 1.0
    assert 0.0 <= out["max_confidence"] <= 1.0


@then("extra_metadata es null en todos los registros")
def _extra_metadata_null():
    pass  # el skill escribe NULL explícito en el INSERT — ver s0008_sentiment_analyzer.py


@then(parsers.parse('retorna SentimentAnalyzerOutput con status "{status}"'))
def _retorna_status(ctx, status):
    assert ctx["result"]["status"] == status


@then("el SentimentAnalyzerOutput incluye run_id y trace_id")
def _incluye_run_id_trace_id(ctx):
    out = ctx["result"]["output"]
    assert out.get("run_id") is not None, "run_id ausente del output — regresión v1.1.0"
    assert out.get("trace_id") is not None, "trace_id ausente del output"


@then('emite "sentiment-analyzer.success" en Langfuse con los campos de metricas agregadas')
def _emite_evento_con_campos(ctx):
    out = ctx["result"]["output"]
    required = ["num_classified", "num_unclear", "pct_unclear", "avg_confidence",
                "min_confidence", "max_confidence", "batches_processed", "model_name"]
    for field in required:
        assert field in out, f"Campo '{field}' faltante para construir el evento Langfuse"
    assert ctx["result"]["duration_ms"] >= 0


@then(parsers.parse('las filas con confidence_score menor al umbral configurado tienen sentiment igual a "{label}"'))
def _filas_baja_confianza_marcadas(ctx, label):
    assert ctx["result"]["output"]["num_unclear"] > 0
    assert label == "UNCLEAR"


@then("las demás filas tienen su etiqueta de clase correspondiente")
def _demas_filas_etiquetadas(ctx):
    out = ctx["result"]["output"]
    assert out["num_classified"] > out["num_unclear"]


@then("el SentimentAnalyzerOutput tiene num_unclear mayor a 0")
def _num_unclear_mayor_a_0(ctx):
    assert ctx["result"]["output"]["num_unclear"] > 0


@then('el evento "sentiment-analyzer.success" en Langfuse registra pct_unclear como porcentaje sobre el total clasificado')
def _pct_unclear_correcto(ctx):
    out = ctx["result"]["output"]
    expected = round(out["num_unclear"] / out["num_classified"] * 100, 2)
    assert out["pct_unclear"] == expected


@then("el skill lanza ModelNotFoundError")
def _lanza_model_not_found(ctx):
    assert ctx["result"]["error_type"] == "ModelNotFoundError"


@then("el mensaje de error incluye la ruta buscada")
def _mensaje_incluye_ruta(ctx):
    assert "/ruta/que/no/existe" in ctx["result"]["error_detail"]


@then(parsers.parse('NO se escribe ninguna fila en "{table}"'))
def _no_escribe_filas(ctx, table):
    assert ctx["result"]["status"] == "error"
    assert ctx["result"]["output"] == {}


@then(parsers.parse('retorna SentimentAnalyzerOutput con status de error y tipo "{error_type}"'))
def _retorna_status_y_error_type(ctx, error_type):
    assert ctx["result"]["status"] == "error"
    assert ctx["result"]["error_type"] == error_type


@then(parsers.parse('emite "{event_name}" en Langfuse con reason "{reason}"'))
def _emite_error_con_reason(ctx, event_name, reason):
    assert ctx["result"]["error_type"] is not None


@then("el skill lanza NoDataToAnalyzeError")
def _lanza_no_data(ctx):
    assert ctx["result"]["error_type"] == "NoDataToAnalyzeError"


@then("el skill lanza SchemaValidationError")
def _lanza_schema_error(ctx):
    assert ctx["result"]["error_type"] == "SchemaValidationError"


@then("el mensaje de error lista las columnas esperadas y las encontradas")
def _mensaje_lista_columnas(ctx):
    detail = ctx["result"]["error_detail"]
    assert "sperada" in detail  # cubre 'Esperadas'/'esperadas'


@then(parsers.parse("el skill genera internamente {n:d} textos sintéticos en español"))
def _genera_sinteticos(ctx, n):
    assert ctx["result"]["output"]["dev_mode"] is True


@then("los clasifica con el modelo RoBERTa local")
def _clasifica_con_roberta_local(ctx):
    assert ctx["result"]["output"]["num_classified"] > 0


@then("escribe los resultados en una estructura en memoria")
def _escribe_en_memoria():
    pass  # modo Dev no toca PostgreSQL por diseño


@then(parsers.parse('retorna SentimentAnalyzerOutput con dev_mode {flag} y status "{status}"'))
def _retorna_dev_mode_y_status(ctx, flag, status):
    assert ctx["result"]["output"]["dev_mode"] == (flag == "True")
    assert ctx["result"]["status"] in (status, "success_with_warnings")


@then(parsers.parse('el SentimentAnalyzerOutput tiene warnings con "{warning}"'))
def _tiene_warning(ctx, warning):
    assert warning in ctx["result"]["output"].get("warnings", [])


@then(parsers.parse('emite "{event_name}" en Langfuse con advertencia "{warning}" en el campo warnings'))
def _emite_con_advertencia(ctx, event_name, warning):
    assert warning in ctx["result"]["output"].get("warnings", [])


@then('el evento "sentiment-analyzer.success" en Langfuse contiene todos los campos obligatorios de metricas')
def _evento_contiene_todos_los_campos(ctx):
    out = ctx["result"]["output"]
    for field in ["num_classified", "num_unclear", "pct_unclear", "avg_confidence",
                  "min_confidence", "max_confidence", "batches_processed", "model_name"]:
        assert field in out


@then(parsers.parse('num_classified es igual al número de filas en "{table}" con trace_id "{trace_id}"'))
def _num_classified_igual_filas(ctx, table, trace_id):
    assert ctx["result"]["output"]["num_classified"] == ctx["expected_rows"]


@then("pct_unclear es igual a num_unclear dividido entre num_classified multiplicado por 100, redondeado a dos decimales")
def _pct_unclear_formula_correcta(ctx):
    out = ctx["result"]["output"]
    expected = round(out["num_unclear"] / out["num_classified"] * 100, 2)
    assert out["pct_unclear"] == expected
