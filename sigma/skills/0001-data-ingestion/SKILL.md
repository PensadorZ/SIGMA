---
skill_id: "0001"
name: data-ingestion
version: "2.0.0"
sigma_variant: "Full"
status: active
description: |
  Carga el dataset de entrada (CSV Tirendaz u otro) hacia la tabla
  raw_data de PostgreSQL. Valida el schema mínimo, calcula un checksum
  SHA-256 del archivo fuente para trazabilidad de integridad, y procesa
  la carga en chunks para estar preparado ante datasets más grandes que
  los 22.500 registros del Hito 1 sin cambiar de arquitectura.
  K ⊆ X: copia el contenido observado exactamente como viene, sin
  inferir ni completar columnas ausentes.
activation_keywords:
  - "ingesta"
  - "cargar datos"
  - "importar csv"
  - "data ingestion"
excluded_from:
  - "limpieza de datos"
  - "preprocesado"
  - "análisis de sentimiento"
allowed_tools:
  - Read
  - Write
  - Bash
max_budget_usd: 0.00
parallelism: chunked
privacy_mode: relaxed
preconditions:
  - "El archivo fuente debe existir en la ruta indicada por --data-path"
  - "El archivo debe tener al menos la columna 'text'"
  - "PostgreSQL debe estar disponible con la tabla raw_data creada"
input_table: null
output_table: "raw_data"
langfuse_trace_prefix: "data-ingestion"
adr_references:
  - ADR-002
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
---

# Skill 0001 — data-ingestion

## 1. Propósito

`data-ingestion` es el primer skill del pipeline funcional del Hito 1
(después de `0000-system-health-check`). Carga el dataset de entrada desde
un archivo CSV hacia la tabla `raw_data` de PostgreSQL, validando el schema
mínimo antes de escribir una sola fila.

**Versión 2.0.0 — Fusión (Opción C):** incorpora dos capacidades de la línea
de trabajo "Eco MultiAgentes 3 Skills 1" sobre la base ya verificada de esta
conversación (25/25 tests antes de esta fusión):

- **Checksum SHA-256** del archivo fuente completo, registrado en el output,
  para poder auditar más adelante si el archivo cargado cambió entre
  ejecuciones del pipeline.
- **`run_id`** junto a `trace_id` en el output, igual que `0000`.
- **Lectura en chunks** (vía `pandas.read_csv(chunksize=...)`), con métrica
  `chunks_processed` en el output. Para el Hito 1 (22.500 filas) el número
  de workers efectivos es 1 — secuencial — pero la arquitectura de chunks ya
  queda lista para el Hito 2 sin rediseño. **Decisión explícita de alcance:**
  no se implementa paralelismo real con multiprocessing en esta fusión —
  eso se evaluará cuando el volumen de datos lo justifique (Hito 2, 130K+
  filas), para no introducir la complejidad de sincronización entre procesos
  sin necesidad actual comprobada.

## 2. Comportamiento — Gherkin

Ver `tests/test_data_ingestion.feature` para los escenarios completos.
Resumen: carga exitosa con checksum, dataset dividido en varios chunks,
schema incompatible (columna requerida ausente), archivo fuente no
encontrado, archivo vacío (solo cabecera), y modo Dev con datos sintéticos.

## 3. Propiedades LTL

```text
-- [Safety-1] No escribir en raw_data si el archivo fuente no existe.
G (archivo_no_existe → ¬escribir_raw_data)

-- [Safety-2] No escribir en raw_data si el schema no cumple el mínimo.
G (schema_invalido → ¬escribir_raw_data)

-- [Safety-3] No escribir en raw_data si el archivo está vacío.
G (archivo_vacio → ¬escribir_raw_data)

-- [Integrity] El checksum se calcula ANTES de cualquier escritura,
--             sobre el archivo exactamente como se leyó.
G (checksum_calculado → checksum_corresponde_al_archivo_leido)

-- [Liveness-1] Siempre que se invoque el skill, eventualmente terminará.
G (invocacion → F (status_success ∨ status_error))

-- [Progress] num_records en el output == filas escritas en raw_data.
G (status_success → num_records = COUNT(raw_data WHERE trace_id))
```

## 4. Restricciones epistémicas (K ⊆ X)

El skill copia el contenido del archivo fuente exactamente como viene.
No infiere columnas ausentes, no completa valores nulos, no traduce ni
normaliza el texto — esa responsabilidad es de `0002-data-cleanser`.
Si el archivo trae columnas adicionales no esperadas, se preservan como
`metadata` JSONB sin descartarlas ni interpretarlas.

## 5. Trazabilidad Langfuse

| Evento | Momento | Campos obligatorios |
|---|---|---|
| `data-ingestion.start` | Inicio | trace_id, run_id, sigma_variant, data_path |
| `data-ingestion.chunk_complete` | Cada chunk procesado | chunk_num, chunk_size, duration_ms |
| `data-ingestion.success` | Cierre exitoso | num_records, checksum_sha256, chunks_processed, duration_ms |
| `data-ingestion.error` | Cierre con error | error_type, error_detail |

## 6. ADRs aplicables

| ADR | Aplicación |
|---|---|
| ADR-002 | La lectura en chunks es la base del futuro paralelismo MapReduce del Hito 2 |
| ADR-006 | `trace_id` y `run_id` resueltos por ContextResolver, nunca hardcodeados |
| ADR-007 | `checksum_sha256` y `chunks_processed` son métricas de Dimensión 1 |
| ADR-008 | K ⊆ X: copia exacta del contenido observado, sin inferencia |
| ADR-009 | Este archivo sigue el formato canónico de 5+ archivos |
| ADR-010 | Rutas y credenciales de PostgreSQL vía `get_required_env()` |
