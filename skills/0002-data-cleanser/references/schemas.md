# schemas.md — Skill 0002: data-cleanser

## Output (dentro de SkillResult.output)

| Campo | Tipo | Descripción |
|---|---|---|
| `num_records_input` | `int` | Filas leídas de `raw_data` |
| `num_records_output` | `int` | Filas finales escritas en `cleaned_data` |
| `num_exact_duplicates_removed` | `int` | Duplicados de texto idéntico |
| `num_near_duplicates_removed` | `int` | Duplicados tras normalización (minúsculas, sin puntuación) — **nuevo en v2.0.0** |
| `num_rejected_schema` | `int` | Filas con `row_id` inválido, movidas a `cleaned_rejected` — **nuevo en v2.0.0** |
| `num_nulls_flagged` | `int` | Filas con texto nulo/vacío (conservadas, solo marcadas) |
| `run_id` | `str` | ID de nivel pipeline — **nuevo en v2.0.0** |
| `trace_id` | `str` | ID de trazabilidad |
| `dev_mode` | `bool` | Modo Dev activo |

## Excepciones

```python
class NoDataToCleanError(Exception):
    """raw_data no contiene filas para el trace_id dado."""
```

## Tabla de salida: `cleaned_data`

Sin cambios respecto a v1.0.0 — ver `db/init_schema.sql`.

## Tabla de salida: `cleaned_rejected` (nueva en v2.0.0)

| Columna | Tipo | Descripción |
|---|---|---|
| `row_id` | `TEXT` | Puede ser `'unknown'` si el propio row_id era nulo |
| `raw_text` | `TEXT` | Texto original de la fila rechazada |
| `rejection_reason` | `TEXT` | Motivo — actualmente solo `'missing_row_id'` |
| `trace_id` | `TEXT` | ID de trazabilidad |
| `rejected_at` | `TIMESTAMPTZ` | Momento del rechazo |

## Invariante de conteo

```
num_records_output + num_exact_duplicates_removed +
num_near_duplicates_removed + num_rejected_schema == num_records_input
```

Esta igualdad debe cumplirse siempre en `status='success'` — cada fila
de entrada termina en exactamente una de las cuatro categorías, nunca
en más de una ni en ninguna.
