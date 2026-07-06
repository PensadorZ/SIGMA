# tests/test_data_cleanser.feature — 0002-data-cleanser v1.0.0 (PENDIENTE fusión Opción C)

Feature: Limpieza y normalización de datos crudos

  Background:
    Given el entorno SIGMA está inicializado
    And el skill 0001-data-ingestion ha producido una tabla "*_raw"

  Scenario: Limpieza completa de tweets Tirendaz
    Given la tabla "tirendaz_tweets_raw" con 22.500 filas
    And la tabla tiene 300 duplicados exactos y 150 casi-exactos
    And 450 filas tienen el campo "text" nulo
    When el skill data-cleanser se ejecuta con run_id "dc-t001" y trace_id "tr-dc-001"
    Then existe la tabla "tirendaz_tweets_cleaned" con 22.500 filas
    And las filas con text nulo tienen el campo marcado "__NULL__"
    And cada fila contiene trace_id: "tr-dc-001"
    And el informe registra exact_duplicates_removed: 300
    And el informe registra near_duplicates_removed: 150
    And el evento "data_cleanser.completed" fue emitido

  Scenario: Filas con schema inválido van a tabla rejected
    Given la tabla "*_raw" tiene 100 filas con tweet_id no entero
    When el skill data-cleanser se ejecuta con run_id "dc-t002"
    Then esas 100 filas están en "*_rejected" con error: "invalid_tweet_id_type"
    And "*_cleaned" no las contiene
    And el informe registra rows_rejected: 100

  Scenario: Modo Dev fuerza workers=1
    Given SIGMA_ENV es "Dev"
    And una tabla "*_raw" con 5.000 filas
    When el skill data-cleanser se ejecuta con run_id "dc-t003"
    Then el informe indica workers_used: 1

  Scenario: Tabla raw no existe
    Given que "inexistente_raw" no existe
    When el skill data-cleanser se ejecuta con run_id "dc-t004"
    Then el skill termina con InputTableNotFoundError
    And el evento "data_cleanser.failed" fue emitido
