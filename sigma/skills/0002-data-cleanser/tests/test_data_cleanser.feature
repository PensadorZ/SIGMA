# tests/test_data_cleanser.feature — 0002-data-cleanser v2.0.0
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2 — fusión Opción C
# Sintaxis Gherkin estricta: una línea por step (gherkin-official)
# Usa SIGMA_VARIANT (no SIGMA_ENV) — ver SKILL.md sección 1 para el porqué

# language: es

Característica: Limpieza, deduplicación y separación de filas inválidas
  Como Orquestador de SIGMA
  Quiero que data-cleanser deduplique exactos y casi-exactos, y separe filas inválidas
  Para que 0003-data-preprocessor reciba solo datos limpios y trazables

  Contexto:
    Dado que el entorno tiene SIGMA_VARIANT configurado
    Y que raw_data está disponible con datos para el trace_id de la prueba

  @happy_path @hito1
  Escenario: Limpieza completa con exactos, casi-exactos y fila inválida
    Dado que raw_data contiene 10 filas
    Y de esas filas, 2 son duplicados exactos de texto
    Y 2 son casi-exactos entre sí (mismo texto en distinta capitalización y puntuación)
    Y 1 fila tiene row_id nulo
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-cleanser con trace_id "wc-clean-001"
    Entonces el output indica num_exact_duplicates_removed igual a 2
    Y el output indica num_near_duplicates_removed igual a 1
    Y el output indica num_rejected_schema igual a 1
    Y se cumple el invariante de conteo entre input, output, duplicados y rechazados
    Y retorna status "success_with_warnings"

  @rejected_rows
  Escenario: Filas con row_id inválido van a cleaned_rejected
    Dado que raw_data contiene 5 filas
    Y de esas filas, 2 tienen row_id vacío
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-cleanser con trace_id "wc-clean-002"
    Entonces el output indica num_rejected_schema igual a 2
    Y ninguna fila rechazada aparece en cleaned_data

  @error @empty_source
  Escenario: raw_data vacía
    Dado que raw_data no contiene ninguna fila
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-cleanser con trace_id "wc-clean-003"
    Entonces el skill lanza NoDataToCleanError
    Y NO se escribe ninguna fila en cleaned_data

  @dev_mode
  Escenario: Modo Dev con datos sintéticos
    Dado que SIGMA_VARIANT es "Dev"
    Cuando el Orquestador invoca data-cleanser con trace_id "wc-clean-004"
    Entonces el output indica dev_mode True
    Y retorna status success o success_with_warnings
