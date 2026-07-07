# =============================================================================
# test_skill.feature — Skill 0008: sentiment-analyzer
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Framework: pytest-bdd (gherkin-official, sintaxis estricta — sin wrapping)
# Ejecutar: pytest skills/0008-sentiment-analyzer/tests/test_skill.py -v
# =============================================================================
# Convención de nomenclatura:
#   SENT-001 a SENT-007: escenarios funcionales principales
# NOTA: El análisis en tiempo real (streaming) está fuera del alcance
#   de este skill. Ver scope_note en SKILL.md para justificación.
# NOTA v1.0.1: Reescrito con una línea por step (sin continuaciones
#   multilínea) tras detectar que el parser oficial de Gherkin las rechaza.
# =============================================================================

# language: es

Característica: Clasificación de sentimiento con RoBERTa local
  Como Orquestador de SIGMA
  Quiero que sentiment-analyzer clasifique el sentimiento de cada texto limpio
  Para que viz-reporter pueda generar la distribución de polaridad del corpus

  Contexto:
    Dado que el entorno tiene SIGMA_VARIANT configurado
    Y que el modelo "cardiffnlp/twitter-roberta-base-sentiment-latest" está disponible en ROBERTA_MODEL_PATH
    Y que PostgreSQL está disponible con las tablas "processed_data" y "sentiment_results"

  # ── SENT-001: Happy path ──────────────────────────────────────────────
  @happy_path @hito1
  Escenario: SENT-001 Clasificación completa del corpus Tirendaz en Full
    Dado que la tabla "processed_data" contiene 22500 filas
    Y que cada fila tiene la columna "clean_text" con texto no vacío
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-001"
    Entonces el skill procesa todas las filas en batches de tamaño configurado
    Y escribe 22500 registros en "sentiment_results"
    Y cada registro tiene las columnas row_id, clean_text, sentiment, confidence_score, model_name, trace_id y extra_metadata
    Y cada valor de sentiment pertenece al conjunto POSITIVE, NEGATIVE, NEUTRAL, UNCLEAR
    Y cada confidence_score está entre 0.0 y 1.0
    Y extra_metadata es null en todos los registros
    Y retorna SentimentAnalyzerOutput con status "success"
    Y emite "sentiment-analyzer.success" en Langfuse con los campos de metricas agregadas

  # ── SENT-002: Baja confianza → UNCLEAR ───────────────────────────────
  @low_confidence @epistemic
  Escenario: SENT-002 Filas con baja confianza se marcan como UNCLEAR
    Dado que la tabla "processed_data" contiene 1000 filas
    Y que al menos 50 filas producen confidence_score menor a 0.65
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-002"
    Entonces las filas con confidence_score menor al umbral configurado tienen sentiment igual a "UNCLEAR"
    Y las demás filas tienen su etiqueta de clase correspondiente
    Y el SentimentAnalyzerOutput tiene num_unclear mayor a 0
    Y el evento "sentiment-analyzer.success" en Langfuse registra pct_unclear como porcentaje sobre el total clasificado

  # ── SENT-003: Modelo no encontrado ───────────────────────────────────
  @error @model_not_found
  Escenario: SENT-003 Error cuando el modelo RoBERTa no está en la ruta configurada
    Dado que ROBERTA_MODEL_PATH apunta a "/ruta/que/no/existe"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-003"
    Entonces el skill lanza ModelNotFoundError
    Y el mensaje de error incluye la ruta buscada
    Y NO se escribe ninguna fila en "sentiment_results"
    Y retorna SentimentAnalyzerOutput con status de error y tipo "ModelNotFoundError"
    Y emite "sentiment-analyzer.error" en Langfuse con reason "model_not_found"

  # ── SENT-004: Datos de entrada vacíos ────────────────────────────────
  @error @empty_data
  Escenario: SENT-004 Error cuando processed_data está vacía
    Dado que la tabla "processed_data" está vacía
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-004"
    Entonces el skill lanza NoDataToAnalyzeError
    Y NO se escribe ninguna fila en "sentiment_results"
    Y retorna SentimentAnalyzerOutput con status de error y tipo "NoDataToAnalyzeError"
    Y emite "sentiment-analyzer.error" en Langfuse con reason "empty_dataset"

  # ── SENT-005: Schema drift ────────────────────────────────────────────
  @error @schema_drift
  Escenario: SENT-005 Error cuando la columna clean_text no existe en processed_data
    Dado que la tabla "processed_data" existe con 5000 filas
    Pero la tabla NO contiene la columna "clean_text"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-005"
    Entonces el skill lanza SchemaValidationError
    Y el mensaje de error lista las columnas esperadas y las encontradas
    Y NO se escribe ninguna fila en "sentiment_results"
    Y retorna SentimentAnalyzerOutput con status de error y tipo "SchemaValidationError"
    Y emite "sentiment-analyzer.error" en Langfuse con reason "schema_drift"

  # ── SENT-006: Modo Dev con datos sintéticos ───────────────────────────
  @dev_mode @synthetic
  Escenario: SENT-006 Ejecución en modo Dev sin conexión a PostgreSQL real
    Dado que SIGMA_VARIANT es "Dev"
    Y que no hay conexión a PostgreSQL disponible en el entorno de prueba
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-006"
    Entonces el skill genera internamente 500 textos sintéticos en español
    Y los clasifica con el modelo RoBERTa local
    Y escribe los resultados en una estructura en memoria
    Y retorna SentimentAnalyzerOutput con dev_mode True y status "success"
    Y el SentimentAnalyzerOutput tiene warnings con "synthetic_data"
    Y emite "sentiment-analyzer.success" en Langfuse con advertencia "synthetic_data" en el campo warnings

  # ── SENT-007: Métricas agregadas completas ────────────────────────────
  @metrics @observability
  Escenario: SENT-007 El evento de cierre registra métricas agregadas completas
    Dado que la tabla "processed_data" contiene 500 filas válidas
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-007"
    Y el skill completa la clasificación sin errores
    Entonces el evento "sentiment-analyzer.success" en Langfuse contiene todos los campos obligatorios de metricas
    Y num_classified es igual al número de filas en "sentiment_results" con trace_id "wc-sent-007"
    Y pct_unclear es igual a num_unclear dividido entre num_classified multiplicado por 100, redondeado a dos decimales
