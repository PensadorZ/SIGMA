---
skill_id: "0008"
name: sentiment-analyzer
version: "1.1.0"
sigma_variant: "Full"
status: active
description: |
  Clasifica cada texto limpio en POSITIVE, NEGATIVE, NEUTRAL o UNCLEAR
  utilizando el modelo cardiffnlp/twitter-roberta-base-sentiment-latest
  cargado localmente vía HuggingFace Transformers (~500 MB en disco).
  No realiza llamadas a APIs externas; el costo de inferencia es
  exclusivamente cómputo local. Opera en modo batch configurable.
  La etiqueta UNCLEAR se asigna cuando el confidence_score del modelo
  no supera el umbral configurado, preservando el contrato K ⊆ X:
  el skill nunca fuerza una clase cuando el modelo no está seguro.
activation_keywords:
  - "analizar sentimiento"
  - "clasificar polaridad"
  - "sentiment"
  - "polaridad"
  - "positivo negativo"
excluded_from:
  - "limpieza de datos"
  - "preprocesado"
  - "clustering"
  - "generación de reportes"
  - "ingesta"
  - "análisis en tiempo real"
scope_note: |
  Este skill procesa datasets completos en modo batch. El análisis en
  tiempo real (streaming) está fuera del alcance del Hito 1 y del Hito 2
  tal como están definidos. Requeriría un ADR específico y skills distintos.
allowed_tools:
  - Read
  - Write
  - Bash
max_budget_usd: 0.00
parallelism: none
privacy_mode: relaxed
preconditions:
  - "La tabla processed_data debe estar poblada (salida de 0003-data-preprocessor)"
  - "La columna clean_text debe existir en processed_data"
  - "El modelo cardiffnlp/twitter-roberta-base-sentiment-latest debe estar\
     \ descargado en la ruta configurada (ROBERTA_MODEL_PATH)"
input_table: "processed_data"
output_table: "sentiment_results"
langfuse_trace_prefix: "sentiment-analyzer"
adr_references:
  - ADR-005
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
---

# Skill 0008 — sentiment-analyzer

## 1. Propósito

`sentiment-analyzer` clasifica cada texto limpio del corpus en una de cuatro
etiquetas: `POSITIVE`, `NEGATIVE`, `NEUTRAL` o `UNCLEAR`. Utiliza el modelo
`cardiffnlp/twitter-roberta-base-sentiment-latest`, entrenado específicamente
sobre texto de Twitter en los idiomas más frecuentes del corpus World Cup
(español, inglés, portugués). El modelo corre completamente en local — sin
llamadas externas, sin costo de API — y escribe sus resultados en la tabla
`sentiment_results` de PostgreSQL junto con el `confidence_score` individual
de cada predicción.

La etiqueta `UNCLEAR` preserva el contrato epistémico K ⊆ X: cuando el
modelo no supera el umbral de confianza configurado, el skill registra la
incertidumbre en lugar de imponer una clase. El conocimiento generado (K)
nunca excede lo que el clasificador realmente observó (X).

---

## 2. Pipeline de inferencia

```
processed_data (PostgreSQL)
        ↓
Carga en batches de 32 filas
        ↓
Tokenización (RoBERTa tokenizer, max_length=128)
        ↓
Forward pass → logits → softmax → (label, confidence_score)
        ↓
Si confidence_score < confidence_threshold → label = UNCLEAR
        ↓
Escritura batch en sentiment_results (PostgreSQL)
        ↓
Evento Langfuse por batch completado
```

---

## 3. Comportamiento — Gherkin

```gherkin
# language: es
Característica: Clasificación de sentimiento con RoBERTa local
  Como Orquestador de SIGMA
  Quiero que sentiment-analyzer clasifique el sentimiento de cada texto limpio
  Para que viz-reporter pueda generar la distribución de polaridad del corpus

  Contexto:
    Dado que el modelo "cardiffnlp/twitter-roberta-base-sentiment-latest"
          está descargado en la ruta configurada por ROBERTA_MODEL_PATH
    Y que PostgreSQL está disponible con las tablas processed_data
          y sentiment_results accesibles

  # ── SENT-001: Happy path ──────────────────────────────────────────────
  @happy_path @hito1
  Escenario: SENT-001 Clasificación completa del corpus Tirendaz
    Dado que la tabla "processed_data" contiene 22500 filas
    Y que cada fila tiene la columna "clean_text" con texto no vacío
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-001"
    Entonces el skill procesa todas las filas en batches de 32
    Y escribe 22500 registros en "sentiment_results" con columnas
          row_id, clean_text, sentiment, confidence_score, model_name,
          trace_id y extra_metadata
    Y cada fila tiene sentiment en {POSITIVE, NEGATIVE, NEUTRAL, UNCLEAR}
    Y cada fila tiene confidence_score entre 0.0 y 1.0
    Y retorna SentimentAnalyzerOutput con status "success"
    Y emite "sentiment-analyzer.success" en Langfuse con campos
          num_classified, num_unclear, avg_confidence, duration_ms,
          batches_processed y model_name

  # ── SENT-002: Baja confianza → UNCLEAR ───────────────────────────────
  @low_confidence @epistemic
  Escenario: SENT-002 Filas con baja confianza se marcan como UNCLEAR
    Dado que la tabla "processed_data" contiene 1000 filas
    Y que al menos 50 filas producen confidence_score menor a 0.65
          con el modelo RoBERTa
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-002"
    Entonces las filas con confidence_score menor al umbral configurado
          reciben sentiment "UNCLEAR"
    Y las demás filas reciben su etiqueta correspondiente normalmente
    Y el SentimentAnalyzerOutput incluye campo "num_unclear" mayor a 0
    Y el evento Langfuse "sentiment-analyzer.success" registra el
          porcentaje de UNCLEAR sobre el total clasificado

  # ── SENT-003: Modelo no encontrado ───────────────────────────────────
  @error @model_not_found
  Escenario: SENT-003 Error cuando el modelo RoBERTa no está en la ruta configurada
    Dado que ROBERTA_MODEL_PATH apunta a una ruta que no existe en disco
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-003"
    Entonces el skill lanza ModelNotFoundError con detalle de la ruta buscada
    Y NO escribe ninguna fila en sentiment_results
    Y retorna SentimentAnalyzerOutput con status "error"
          y error_type "ModelNotFoundError"
    Y emite "sentiment-analyzer.error" en Langfuse con reason "model_not_found"

  # ── SENT-004: Datos de entrada vacíos ────────────────────────────────
  @error @empty_data
  Escenario: SENT-004 Error cuando processed_data está vacía
    Dado que la tabla "processed_data" está vacía
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-004"
    Entonces el skill lanza NoDataToAnalyzeError
    Y NO escribe ninguna fila en sentiment_results
    Y retorna SentimentAnalyzerOutput con status "error"
          y error_type "NoDataToAnalyzeError"
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
    Y NO escribe ninguna fila en sentiment_results
    Y retorna SentimentAnalyzerOutput con status "error"
          y error_type "SchemaValidationError"
    Y emite "sentiment-analyzer.error" en Langfuse con reason "schema_drift"

  # ── SENT-006: Modo Dev con datos sintéticos ───────────────────────────
  @dev_mode @synthetic
  Escenario: SENT-006 Ejecución en modo Dev con dataset sintético interno
    Dado que SIGMA_VARIANT es "Dev"
    Y que no hay conexión a PostgreSQL disponible en el entorno de prueba
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-006"
    Entonces el skill genera internamente 500 textos sintéticos en español
    Y los clasifica con el modelo RoBERTa local
    Y escribe los resultados en una tabla en memoria
    Y retorna SentimentAnalyzerOutput con dev_mode True y status "success"
    Y emite "sentiment-analyzer.success" en Langfuse
          con advertencia "synthetic_data" en warnings

  # ── SENT-007: Métricas agregadas completas en Langfuse ────────────────
  @metrics @observability
  Escenario: SENT-007 El evento de cierre registra métricas agregadas completas
    Dado que la tabla "processed_data" contiene 500 filas válidas
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca sentiment-analyzer con trace_id "wc-sent-007"
    Y el skill completa la clasificación sin errores
    Entonces el evento "sentiment-analyzer.success" en Langfuse contiene
          los campos num_classified, num_unclear, pct_unclear,
          avg_confidence, min_confidence, max_confidence,
          batches_processed, duration_ms y model_name
    Y los campos numéricos son consistentes entre sí
          (num_classified == filas en sentiment_results con ese trace_id)
```

---

## 4. Propiedades LTL (Lógica Temporal Lineal)

```text
-- [Safety-1] No ejecutar si processed_data está vacía.
G (dataset_vacio → ¬ejecutar_clasificacion)

-- [Safety-2] No ejecutar si clean_text no existe en el schema de entrada.
G (schema_invalido → ¬ejecutar_clasificacion)

-- [Safety-3] No ejecutar si el modelo no está disponible en disco.
G (¬modelo_disponible → ¬ejecutar_clasificacion)

-- [Safety-4] El texto original nunca se modifica durante la clasificación.
G (ejecutar_clasificacion → ¬modificar_processed_data)

-- [Safety-5] No escribir en sentiment_results si el batch falló.
G (batch_fallido → ¬escribir_batch_en_db)

-- [Epistemic] La etiqueta asignada proviene exclusivamente del modelo;
--             nunca de reglas manuales o inferencia adicional.
G (clasificacion → etiqueta ∈ output_modelo ∨ etiqueta = UNCLEAR)

-- [Epistemic] UNCLEAR se asigna si y solo si confidence < umbral.
G (confidence < umbral → etiqueta = UNCLEAR)
G (etiqueta = UNCLEAR → confidence < umbral)

-- [Liveness-1] Siempre que se invoque el skill, eventualmente terminará.
G (invocacion → F (status_success ∨ status_error))

-- [Liveness-2] Cada batch se procesa antes de pasar al siguiente.
G (batch_iniciado → F (batch_completado ∨ batch_fallido))

-- [Progress] num_classified en el output == filas escritas en sentiment_results.
G (status_success → num_classified = COUNT(sentiment_results WHERE trace_id))
```

---

## 5. Restricciones epistémicas (K ⊆ X) — ADR-008

Este skill utiliza un clasificador determinista (RoBERTa) como subagente
mecánico. Su salida se considera observación del sistema, no inferencia del
agente. Las restricciones son:

El skill **no infiere** causas del sentimiento detectado.
El skill **no genera** explicaciones subjetivas de por qué un texto es positivo.
El skill **no imputa** sentimiento a filas vacías o nulas.
El skill **no fuerza** una etiqueta cuando la confianza no supera el umbral;
usa `UNCLEAR` en su lugar.

Si una fila tiene `clean_text` nulo o vacío, se registra en `sentiment_results`
con `sentiment = NULL` y `confidence_score = NULL`. No se asume ningún valor.

---

## 6. Nota sobre análisis en tiempo real

El análisis en tiempo real (streaming tweet-by-tweet) está **explícitamente
fuera del alcance** de este skill, del Hito 1 y del Hito 2 tal como están
definidos en el Plan Maestro de SIGMA v1.5. Esta arquitectura procesa
datasets completos en modo batch. Una capacidad de streaming requeriría un
ADR específico (decisión sobre Kafka, Redis Streams o Faust), skills de
ingesta distintos, y un modelo de consistencia diferente. Se documenta aquí
para evitar ambigüedad futura.

---

## 7. Trazabilidad Langfuse

| Evento | Momento | Campos obligatorios |
|---|---|---|
| `sentiment-analyzer.start` | Inicio del skill | trace_id, sigma_variant, input_rows, model_name |
| `sentiment-analyzer.batch_complete` | Al completar cada batch | batch_num, batch_size, duration_ms |
| `sentiment-analyzer.success` | Cierre exitoso | num_classified, num_unclear, pct_unclear, avg_confidence, min_confidence, max_confidence, batches_processed, duration_ms, model_name |
| `sentiment-analyzer.error` | Cierre con error | error_type, error_detail, trace_id, batches_completed_before_error |

---

## 8. ADRs aplicables

| ADR | Aplicación concreta en este skill |
|---|---|
| ADR-005 | Policy Server valida que Write solo ocurra en `sentiment_results`, nunca en `processed_data` |
| ADR-006 | `{trace_id}` y `{workflow_id}` son placeholders resueltos por ContextResolver |
| ADR-007 | `avg_confidence` y distribución de etiquetas son métricas de Dimensión 1. El porcentaje de UNCLEAR es indicador de calidad del corpus |
| ADR-008 | La etiqueta `UNCLEAR` es la implementación directa del contrato K ⊆ X para baja confianza |
| ADR-009 | Este archivo sigue el formato canónico de 5 archivos |
| ADR-010 | `ROBERTA_MODEL_PATH` y credenciales de PostgreSQL se obtienen exclusivamente vía `get_required_env()` |

---

## 9. Historial de resolución

**v1.1.0 (auditoría de cierre de ciclo, Eco MultiAgentes 4 Skills 2):**
`run_id` y `trace_id` faltaban explícitamente en el output — se usaban
internamente para las consultas SQL, pero nunca se exponían en el
`SkillResult`, a diferencia de `0000`/`0001`/`0002`/`0003`. Corregido.
`model_name` estaba hardcodeado como constante `MODEL_NAME` pese a que
`defaults.yaml` ya lo declaraba en `model.name` — mismo patrón de
desincronización encontrado antes en `0001` (`REQUIRED_COLUMN`) y `0002`
(umbral de duplicados). Ahora se lee realmente desde `cfg`.
