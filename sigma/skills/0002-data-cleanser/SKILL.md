---
skill_id: "0002"
name: data-cleanser
version: "2.0.0"
sigma_variant: "Full"
status: active
description: |
  Limpia y normaliza los datos crudos de raw_data: elimina duplicados
  exactos y casi-exactos, marca filas con texto nulo, limpia URLs y
  menciones, y separa filas con schema inválido hacia cleaned_rejected
  en vez de descartarlas silenciosamente. Escribe el resultado en
  cleaned_data. K ⊆ X: transforma deterministamente, nunca imputa
  valores ni infiere contenido.
activation_keywords:
  - "limpieza"
  - "deduplicación"
  - "data cleanser"
  - "normalización de texto"
excluded_from:
  - "ingesta"
  - "preprocesado"
  - "análisis de sentimiento"
allowed_tools:
  - Read
  - Write
max_budget_usd: 0.00
parallelism: none
privacy_mode: relaxed
preconditions:
  - "raw_data debe contener al menos una fila para el trace_id dado"
input_table: "raw_data"
output_table: "cleaned_data"
langfuse_trace_prefix: "data-cleanser"
adr_references:
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
---

# Skill 0002 — data-cleanser

## 1. Propósito

`data-cleanser` recibe los datos crudos de `0001-data-ingestion` y produce
una versión limpia y deduplicada en `cleaned_data`, lista para que
`0003-data-preprocessor` la consuma.

**Versión 2.0.0 — Fusión (Opción C):** incorpora sobre la base ya verificada
(25/25 tests antes de esta fusión) dos capacidades de "Eco MultiAgentes 3
Skills 1":

- **Deduplicación de casi-exactos**, además de los exactos que ya existían.
  Implementada en **O(n)** por agrupación con clave normalizada (minúsculas,
  sin puntuación, sin URLs/menciones) — deliberadamente **no** por
  comparación por pares O(n²), que fue exactamente el error de rendimiento
  que la otra línea de trabajo encontró y corrigió (290 segundos para
  22.500 filas con el algoritmo ingenuo). Se evita ese error desde el
  diseño de esta fusión, no se repite.
- **Tabla `cleaned_rejected`**, separada de `cleaned_data`, para filas con
  schema inválido — en vez de descartarlas sin dejar rastro.

**Adaptación explícita:** la versión original definía "schema inválido"
como `tweet_id` no convertible a entero. En este proyecto `row_id` es un
string libre (`row-42`, `dev-a1b2c3d4`), no necesariamente numérico —
esa regla no aplicaría tal cual. Se adapta el criterio de rechazo a lo
que sí es estructuralmente inválido aquí: `row_id` nulo o vacío, que
impide cualquier trazabilidad hacia adelante en el pipeline.

**`SIGMA_VARIANT` se mantiene** (no se renombra a `SIGMA_ENV`) — el costo
de propagar un renombrado de variable de entorno por todo el proyecto no
se justifica frente al beneficio cosmético de adoptar el nombre de la
otra línea de trabajo.

## 2. Comportamiento — Gherkin

Ver `tests/test_data_cleanser.feature`. Cubre: limpieza completa con
ambos tipos de duplicado, filas con `row_id` inválido separadas a
`cleaned_rejected`, modo Dev, y `raw_data` vacía.

## 3. Propiedades LTL

```text
-- [Safety-1] No escribir en cleaned_data si raw_data está vacía.
G (raw_data_vacia → ¬escribir_cleaned_data)

-- [Safety-2] Una fila con row_id inválido nunca llega a cleaned_data.
G (row_id_invalido → fila_va_a_cleaned_rejected ∧ ¬fila_en_cleaned_data)

-- [Integrity] La deduplicación de casi-exactos es O(n) — nunca se
--             implementa como comparación por pares.
G (dedup_near_duplicates → complejidad_algoritmica = O(n))

-- [Liveness-1] Siempre que se invoque el skill, eventualmente terminará.
G (invocacion → F (status_success ∨ status_error))

-- [Progress] num_records_output + duplicados + rechazados = num_records_input
G (status_success →
   num_records_output + num_exact_duplicates_removed +
   num_near_duplicates_removed + num_rejected_schema = num_records_input)
```

## 4. Restricciones epistémicas (K ⊆ X)

El skill nunca infiere el contenido de una fila con texto nulo — la marca
con `had_nulls=True` y la conserva tal cual, no la completa ni la descarta
por ese motivo. Una fila solo se excluye de `cleaned_data` por ser
duplicado (exacto o casi-exacto) o por tener `row_id` inválido — nunca por
juicio de calidad del contenido del texto en sí.

## 5. Trazabilidad Langfuse

| Evento | Momento | Campos obligatorios |
|---|---|---|
| `data-cleanser.start` | Inicio | trace_id, run_id, num_records_input |
| `data-cleanser.success` | Cierre exitoso | num_records_output, num_exact_duplicates_removed, num_near_duplicates_removed, num_rejected_schema, num_nulls_flagged |
| `data-cleanser.error` | Cierre con error | error_type, error_detail |

## 6. ADRs aplicables

| ADR | Aplicación |
|---|---|
| ADR-006 | `trace_id` y `run_id` resueltos por ContextResolver |
| ADR-007 | Métricas de deduplicación son indicadores de Dimensión 1 y de calidad del corpus |
| ADR-008 | K ⊆ X: nunca se infiere contenido de texto nulo |
| ADR-009 | Este archivo sigue el formato canónico de 5+ archivos |
| ADR-010 | Credenciales de PostgreSQL vía `get_required_env()` |
