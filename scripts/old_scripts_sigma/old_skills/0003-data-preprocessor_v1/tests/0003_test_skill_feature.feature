# tests/test_skill.feature — 0003-data-preprocessor v1.2.0
# Tests ejecutables con pytest-bdd
# Ejecutar: pytest tests/test_skill.py -v

Feature: Preprocesamiento estadístico de datos para modelado

  Background:
    Given el entorno SIGMA está inicializado
    And las variables de entorno están cargadas desde .env
    And la conexión a PostgreSQL está disponible

  # ─── ESCENARIOS POSITIVOS ─────────────────────────────────────────────

  Scenario: Preprocesamiento completo de dataset de clasificación binaria
    Given una tabla "test_tweets_cleaned" con 1.000 filas de prueba
    And la tabla tiene columnas ["tweet_id", "text", "lang", "likes", "retweets", "sentiment_label"]
    And la columna "sentiment_label" tiene distribución [800 POSITIVE, 200 NEGATIVE]
    And defaults.yaml declara task: "classification" y target_column: "sentiment_label"
    When el skill data-preprocessor se ejecuta con run_id "test-001" y trace_id "trace-abc"
    Then existe la tabla "test_tweets_processed" en la base de datos
    And cada fila de "test_tweets_processed" contiene trace_id = "trace-abc"
    And todas las columnas numéricas tienen media entre -0.1 y 0.1
    And todas las columnas numéricas tienen std entre 0.9 y 1.1
    And la columna "sentiment_label" tiene ratio de clases ≤ 3:1
    And existe "preprocessing_report.json" en ${OUTPUT_DIR}
    And el informe contiene trace_id_propagated: true
    And el evento "data_preprocessor.completed" fue emitido en Langfuse
    And el payload del evento contiene trace_id: "trace-abc"
    And la tabla "test_tweets_cleaned" original no fue modificada

  Scenario: PCA se activa automáticamente con alta dimensionalidad
    Given una tabla "test_highdim_cleaned" con 500 filas y 600 columnas numéricas
    And MAX_FEATURES está configurado en 500
    When el skill data-preprocessor se ejecuta con run_id "test-002" y trace_id "trace-def"
    Then la tabla "test_highdim_processed" tiene ≤ 500 columnas
    And las columnas se llaman "pc_001", "pc_002", ... hasta "pc_N"
    And cada fila contiene trace_id = "trace-def"
    And el preprocessing_report.json contiene "pca_components_selected"
    And el preprocessing_report.json contiene "variance_explained" ≥ 0.95
    And el evento "data_preprocessor.pca_applied" fue emitido en Langfuse

  Scenario: Modo Dev fuerza workers=1 y class_weight en lugar de SMOTE
    Given el entorno es SIGMA_ENV=Dev
    And una tabla "test_dev_cleaned" con 500 filas
    And la columna target tiene ratio de clases 10:1
    When el skill data-preprocessor se ejecuta con run_id "test-003" y trace_id "trace-ghi"
    Then el preprocessing_report.json indica workers_used: 1
    And el preprocessing_report.json indica balance_strategy: "class_weight"
    And NO existen filas sintéticas en la tabla output
    And cada fila contiene trace_id = "trace-ghi"
    And el evento "data_preprocessor.completed" fue emitido

  # ─── ESCENARIOS DE ERROR ──────────────────────────────────────────────

  Scenario: Error si la tabla de entrada no existe
    Given que la tabla "nonexistent_cleaned" no existe en la base de datos
    When el skill data-preprocessor se ejecuta con run_id "test-004" y trace_id "trace-jkl"
    Then el skill termina con error "InputTableNotFoundError"
    And NO existe ninguna tabla con sufijo "_processed" creada en este run
    And el evento "data_preprocessor.failed" fue emitido en Langfuse
    And el payload contiene error_type: "InputTableNotFoundError" y trace_id: "trace-jkl"

  Scenario: Pausa HITL si nulos superan el umbral
    Given una tabla "test_nulls_cleaned" donde "engagement_score" tiene 35% nulos
    And null_threshold está configurado en 0.30
    When el skill data-preprocessor se ejecuta con run_id "test-005" y trace_id "trace-mno"
    Then el evento "data_preprocessor.decision_required" fue emitido en Langfuse
    And el payload contiene column: "engagement_score", null_ratio: 0.35, trace_id: "trace-mno"
    And NO existe la tabla "test_nulls_processed"
    And el workflow permanece en estado "waiting_hitl"

  Scenario: Notificación webhook en decision_required si está configurado
    Given una tabla "test_nulls_cleaned" donde "engagement_score" tiene 35% nulos
    And policies.yaml tiene webhook_url configurado
    When el skill data-preprocessor se ejecuta con run_id "test-005b" y trace_id "trace-pqr"
    Then se invoca el webhook con el payload de "data_preprocessor.decision_required"
    And el payload del webhook contiene trace_id: "trace-pqr"

  Scenario: Columna sospechosa de fuga se excluye y registra
    Given una tabla "test_leak_cleaned" con columna "future_engagement"
    And leakage_action está configurado en "exclude_and_warn"
    When el skill data-preprocessor se ejecuta con run_id "test-006" y trace_id "trace-stu"
    Then la tabla "test_leak_processed" NO contiene la columna "future_engagement"
    And el preprocessing_report.json lista "future_engagement" en "excluded_columns"
    And el preprocessing_report.json indica reason: "leakage_pattern_match"
    And el evento "data_preprocessor.leakage_warning" fue emitido con trace_id: "trace-stu"

  Scenario: Columna target declarada no existe
    Given una tabla "test_notarget_cleaned" con columnas ["tweet_id", "text"]
    And el pipeline declara target_column: "sentiment_label"
    When el skill data-preprocessor se ejecuta con run_id "test-007" y trace_id "trace-vwx"
    Then el skill termina con error "TargetColumnNotFoundError"
    And el mensaje de error incluye las columnas disponibles: ["tweet_id", "text"]
    And el evento "data_preprocessor.failed" fue emitido con trace_id: "trace-vwx"
