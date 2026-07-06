---
id: data-cleanser
version: "1.0.0"
description: >
  Limpia, deduplica y normaliza la tabla *_raw produciendo una tabla *_cleaned
  apta para preprocesamiento estadístico. Elimina duplicados exactos y casi-
  exactos, estandariza formatos de fecha y texto, detecta y marca nulos,
  valida el schema Pydantic de cada fila y registra en el informe cada
  transformación aplicada. Propaga el trace_id en cada fila. Nunca elimina
  filas sin registrar la razón. Nunca imputa valores con modelos externos.
domain: data-engineering
input_table_pattern: "*_raw"
output_table_pattern: "*_cleaned"
max_budget_usd: 0.00
parallelism:
  strategy: map_reduce
  partition_by: row_index
  workers: ${CLEANSER_WORKERS:-8}
  reducer: concat_parquet
  retry_failed_only: true
  checkpoint_interval: 10000
output_schema: CleanserOutput
expected_trajectory:
  - tool: read_raw_table
  - tool: remove_exact_duplicates
  - tool: remove_near_duplicates
  - tool: standardize_formats
  - tool: flag_nulls
  - tool: validate_row_schema
  - tool: write_cleaned_table
  - tool: write_cleanser_report
sigma_variants: [Full, Lite, Dev, Runtime]
referencias:
  - ADR-002   # MapReduce para limpieza de datasets grandes
  - ADR-006   # Placeholders ${VAR} para umbrales y configuración
  - ADR-008   # K⊆X — nunca imputa con modelos externos
  - ADR-009   # Formato canónico
  - ADR-011   # Langfuse — trazabilidad de cada transformación
---

# Skill 0002: data-cleanser

## Qué hace este skill

`data-cleanser` recibe la tabla `*_raw` y produce la tabla `*_cleaned`.
Su principio rector es la trazabilidad de cada decisión: cada fila eliminada,
cada valor normalizado y cada nulo marcado queda registrado en el informe con
su razón. El skill no toma decisiones silenciosas.

### Operaciones en orden fijo

Primero elimina duplicados exactos. Dos filas son duplicados exactos si todos
sus campos no-ID son idénticos. Se conserva la primera ocurrencia.

Segundo elimina duplicados casi-exactos. Usa similitud de Jaccard sobre el
campo de texto principal. Si la similitud supera ${NEAR_DUP_THRESHOLD:-0.95},
las filas se consideran duplicados. Se conserva la más reciente si hay timestamp,
la primera en caso contrario.

Tercero estandariza formatos. Fechas a ISO 8601, texto a Unicode NFC, URLs a
minúsculas, números con separador decimal punto.

Cuarto marca nulos. Los nulos no se imputan. Se marcan con el flag
`__NULL__` en el campo y se registran en el informe. La decisión de qué
hacer con ellos es del 0003-data-preprocessor.

Quinto valida el schema de cada fila contra el schema Pydantic declarado.
Las filas que no pasan la validación se mueven a la tabla `*_rejected` con
el mensaje de error. Nunca se descartan silenciosamente.

---

## Comportamiento (Gherkin)

```gherkin
Feature: Limpieza y normalización de datos crudos

  Background:
    Given el entorno SIGMA está inicializado
    And el skill 0001-data-ingestion ha producido una tabla "*_raw"

  Scenario: Limpieza completa de 22.500 tweets Tirendaz
    Given la tabla "tirendaz_tweets_raw" con 22.500 filas
    And la tabla tiene 300 duplicados exactos y 150 casi-exactos
    And 450 filas tienen el campo "text" nulo
    When el skill data-cleanser se ejecuta con run_id "dc-001" y trace_id "tr-dc-001"
    Then se crea la tabla "tirendaz_tweets_cleaned"
    And la tabla tiene 22.500 + 300 + 150 - 300 - 150 = 22.500 filas (los duplicados se eliminan; los nulos se marcan, no se eliminan filas — corrección v1.0.1 tras verificación con código real, ver skill.py)
    And las 450 filas con text nulo tienen el campo marcado como "__NULL__"
    And cada fila de "tirendaz_tweets_cleaned" contiene trace_id: "tr-dc-001"
    And el informe registra exact_duplicates_removed: 300
    And el informe registra near_duplicates_removed: 150
    And el informe registra null_fields_flagged: 450
    And se emite "data_cleanser.completed" en Langfuse

  Scenario: Filas con schema inválido van a tabla rejected
    Given la tabla "*_raw" tiene 100 filas donde tweet_id no es un entero
    When el skill data-cleanser se ejecuta con run_id "dc-002"
    Then esas 100 filas se mueven a la tabla "*_rejected" con error: "invalid_tweet_id_type"
    And la tabla "*_cleaned" NO las contiene
    And el informe registra rows_rejected: 100 con sus razones

  Scenario: Modo Dev fuerza workers=1
    Given SIGMA_ENV es "Dev"
    And una tabla "*_raw" con 5.000 filas
    When el skill data-cleanser se ejecuta con run_id "dc-003"
    Then el informe indica workers_used: 1
    And la ejecución termina en menos de 120 segundos

  Scenario: Tabla raw no existe
    Given que la tabla "inexistente_raw" no existe en PostgreSQL
    When el skill data-cleanser se ejecuta con run_id "dc-004"
    Then el skill termina con InputTableNotFoundError
    And se emite "data_cleanser.failed" en Langfuse
    And se dispara notificación BurntToast con -Tipo "alerta"
```

---

## Propiedades LTL — Garantías temporales

```
# ── SAFETY ──────────────────────────────────────────────────────────────

□ ¬(eliminar_fila_sin_registrar_razon)
"Ninguna fila se elimina sin que el informe registre por qué"

□ ¬(imputar_con_modelo_externo)
"Los nulos se marcan, nunca se imputan con modelos (K⊆X)"

□ ¬(modificar_tabla_raw)
"La tabla de entrada *_raw nunca se modifica"

□ (skill_ejecutando → trace_id_en_cada_fila_output)
"Cada fila de *_cleaned lleva el trace_id del workflow"


# ── LIVENESS ─────────────────────────────────────────────────────────────

skill_iniciado → ◇ (tabla_cleaned_escrita ∨ skill_fallido)
"El skill siempre produce *_cleaned o falla con error documentado"


# ── RESPONSE ─────────────────────────────────────────────────────────────

fila_rechazada → ◇ fila_en_tabla_rejected_con_razon
"Toda fila rechazada aparece en *_rejected con su razón"


# ── ABSENCE ──────────────────────────────────────────────────────────────

□ ¬(descartar_fila_silenciosamente)
"Ninguna fila desaparece sin dejar rastro en el informe o en *_rejected"
```

---

## Especificación de trazabilidad

```yaml
traces:
  langfuse_events:

    - name: "data_cleanser.started"
      when: "al inicio"
      payload: {run_id, trace_id, input_table, n_rows_raw, workers}

    - name: "data_cleanser.duplicates_removed"
      when: "tras eliminar duplicados"
      payload: {run_id, trace_id, exact_removed, near_removed,
                near_dup_threshold_used}

    - name: "data_cleanser.nulls_flagged"
      when: "tras marcar nulos"
      payload: {run_id, trace_id, fields_with_nulls, total_null_flags}

    - name: "data_cleanser.rows_rejected"
      when: "si hay filas con schema inválido"
      payload: {run_id, trace_id, rejected_count, rejection_reasons}

    - name: "data_cleanser.completed"
      when: "al finalizar exitosamente"
      payload: {run_id, trace_id, output_table, rows_in, rows_out,
                rows_rejected, duration_ms}

    - name: "data_cleanser.failed"
      when: "error no recuperable"
      payload: {run_id, trace_id, error_type, error_message, stack_trace}

  desktop_notification:
    on_failure: true
    on_completion: false
```

---

## Referencias

- [ADR-002](../docs/adr/adr-002-mapreduce-skills.md) — MapReduce
- [ADR-006](../docs/adr/adr-006-context-placeholders.md) — ${VAR}
- [ADR-008](../docs/adr/adr-008-restriccion-epistemica.md) — K⊆X
- [ADR-009](../docs/adr/adr-009-especificacion-skills.md) — Formato canónico
- [ADR-011](../docs/adr/adr-011-trazabilidad-langfuse.md) — Langfuse V2
