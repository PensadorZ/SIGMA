# =============================================================================
# test_skill.feature — Skill 0011: viz-reporter
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Framework: pytest-bdd (gherkin-official, sintaxis estricta — sin wrapping)
# Ejecutar: pytest skills/0011-viz-reporter/tests/test_skill.py -v
# =============================================================================
# NOTA v1.0.1: Reescrito con una línea por step (sin continuaciones
#   multilínea) tras detectar que el parser oficial de Gherkin las rechaza.
# =============================================================================

# language: es

Característica: Generación autónoma de dashboards y resúmenes ejecutivos
  Como Orquestador de SIGMA
  Quiero que viz-reporter genere dashboards y resúmenes de forma autónoma
  Para cerrar el pipeline del Hito 1 sin intervención adicional del orquestador

  Contexto:
    Dado que el entorno tiene SIGMA_VARIANT configurado
    Y que MinIO está disponible con el bucket "dashboards"
    Y que el directorio de salida temporal es "/tmp/sigma_viz_test"

  # ── VIZ-001: Happy path ───────────────────────────────────────────────
  @happy_path @plotly @hito1
  Escenario: VIZ-001 Dashboard completo con sentimiento y engagement usando Plotly
    Dado que la tabla "processed_data" contiene 22500 filas con columnas de sentimiento
    Y que Plotly está instalado en el entorno
    Y que SIGMA_VARIANT es "Full"
    Y que el provider LLM es "ollama" con modelo "llama3.2:3b" disponible
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-001"
    Entonces el skill selecciona el motor "plotly"
    Y genera un archivo HTML con al menos 3 gráficos
    Y persiste el artefacto en el destino configurado
    Y el VizReporterOutput tiene status "success"
    Y el VizReporterOutput tiene campo "motor" igual a "plotly"
    Y el VizReporterOutput tiene campo "pre_aggregated" igual a False
    Y el VizReporterOutput tiene campo "dev_mode" igual a False
    Y el VizReporterOutput incluye run_id y trace_id

  # ── VIZ-002: Dataset grande — DuckDB ─────────────────────────────────
  @large_dataset @duckdb @plotly
  Escenario: VIZ-002 Dataset grande activa pre-agregación con DuckDB
    Dado que la tabla "processed_data" contiene 800000 filas con columnas de sentimiento
    Y que Plotly está instalado en el entorno
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-002"
    Entonces el skill selecciona el motor "duckdb+plotly"
    Y el VizReporterOutput tiene campo "pre_aggregated" igual a True
    Y el VizReporterOutput tiene status "success"

  # ── VIZ-003: Fallback a matplotlib ───────────────────────────────────
  @fallback @matplotlib
  Escenario: VIZ-003 Plotly no disponible activa fallback a matplotlib
    Dado que Plotly NO está instalado en el entorno de prueba
    Y que matplotlib está disponible
    Y que la tabla "processed_data" contiene 500 filas válidas con columnas de sentimiento
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-003"
    Entonces el skill selecciona el motor "matplotlib"
    Y el VizReporterOutput tiene campo "motor" igual a "matplotlib"
    Y el VizReporterOutput tiene status "success"
    Y el VizReporterOutput tiene warnings con "plotly_not_available"

  # ── VIZ-004: Datos vacíos ─────────────────────────────────────────────
  @error @empty_data
  Escenario: VIZ-004 Error por datos de entrada vacíos
    Dado que la tabla "processed_data" está vacía
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-004"
    Entonces el skill lanza la excepción "NoDataForVizError"
    Y el VizReporterOutput tiene status "error"
    Y el VizReporterOutput tiene campo "error_type" igual a "NoDataForVizError"

  # ── VIZ-005: Schema drift ─────────────────────────────────────────────
  @error @schema_drift
  Escenario: VIZ-005 Error por columna esperada ausente en los datos de entrada
    Dado que la tabla "processed_data" existe con 1000 filas
    Pero la tabla NO contiene la columna "sentiment"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-005"
    Entonces el skill lanza la excepción "SchemaValidationError"
    Y el VizReporterOutput tiene status "error"
    Y el VizReporterOutput tiene campo "error_type" igual a "SchemaValidationError"

  # ── VIZ-006: Modo Dev ─────────────────────────────────────────────────
  @dev_mode @synthetic
  Escenario: VIZ-006 Ejecución en modo Dev con dataset sintético interno
    Dado que SIGMA_VARIANT es "Dev"
    Y que no hay conexión a PostgreSQL disponible en el entorno de prueba
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-006"
    Entonces el skill genera internamente un dataset sintético de 500 filas
    Y el VizReporterOutput tiene campo "dev_mode" igual a True
    Y el VizReporterOutput tiene status "success"

  # ── VIZ-007: Provider LLM "none" — sin resumen textual ───────────────
  @summary @provider_none
  Escenario: VIZ-007 Provider LLM configurado como none omite el resumen sin error
    Dado que la tabla "processed_data" contiene 5000 filas válidas con columnas de sentimiento
    Y que SIGMA_VARIANT es "Full"
    Y que el provider LLM en defaults.yaml es "none"
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-test-007"
    Entonces el skill genera el dashboard HTML normalmente
    Y el VizReporterOutput tiene campo "summary_text" igual a None
    Y el VizReporterOutput tiene campo "summary_provider" igual a "none"
    Y el VizReporterOutput tiene status "success"
