---
skill_id: "0003"
name: data-preprocessor
version: "2.0.0"
sigma_variant: "Full"
status: active
description: |
  Preprocesa los datos limpios: detecta idioma, calcula engagement_score,
  detecta y excluye columnas de leakage, y escala features numéricas con
  StandardScaler real. SMOTE, class_weight y PCA están disponibles pero
  desactivados por defecto — se activan por configuración y solo actúan
  si se detecta automáticamente una target_column en los datos, lo cual
  no ocurre en el pipeline actual (Tirendaz → RoBERTa), donde la etiqueta
  de sentimiento la genera 0008-sentiment-analyzer DESPUÉS de este skill.
activation_keywords:
  - "preprocesado"
  - "escalado"
  - "feature engineering"
  - "data preprocessor"
excluded_from:
  - "limpieza"
  - "ingesta"
  - "análisis de sentimiento"
allowed_tools:
  - Read
  - Write
max_budget_usd: 0.00
parallelism: none
privacy_mode: relaxed
preconditions:
  - "cleaned_data debe contener al menos una fila para el trace_id dado"
input_table: "cleaned_data"
output_table: "processed_data"
langfuse_trace_prefix: "data-preprocessor"
adr_references:
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
---

# Skill 0003 — data-preprocessor

## 1. Propósito

`data-preprocessor` recibe los datos limpios de `0002-data-cleanser` y
produce `processed_data`, lista para que `0008-sentiment-analyzer` la
consuma. Detecta idioma, calcula `engagement_score`, y escala features
numéricas con `StandardScaler` real (antes v1.0.0 usaba una fórmula
simplificada sin escalado estadístico verdadero).

## 2. El fork arquitectónico de esta fusión — por qué SMOTE/PCA están condicionados

La versión original de "Eco MultiAgentes 3 Skills 1" asumía un flujo de
**entrenamiento supervisado**: un dataset ya etiquetado (`sentiment_label`
presente desde el origen), donde tiene sentido directo aplicar SMOTE para
balancear clases y excluir columnas de *leakage* del target.

**Este pipeline es distinto.** El orden real es
`0000→0001→0002→0003→0008→0011`. `0003` corre **antes** que
`0008-sentiment-analyzer`, que es quien **genera** la etiqueta de
sentimiento con RoBERTa. En el punto donde corre `0003`, no existe
ninguna `target_column` de la cual balancear clases — ese dato
simplemente no existe todavía en esta etapa.

**Resolución (decisión de Marx García):** en vez de eliminar SMOTE,
`class_weight` y PCA, se implementaron **condicionados por configuración
y por detección automática de `target_column`**:

- Si `target_column` no se detecta en los datos (caso del pipeline
  Tirendaz actual), `apply_smote` y `apply_class_weight` se **ignoran
  automáticamente**, sin importar su valor en `defaults.yaml`, sin error.
- El mismo `skill.py`, sin cambiar una línea de código, sirve para un
  futuro pipeline tipo Kaggle (dataset ya etiquetado) con solo cambiar
  `apply_smote: true` / `apply_class_weight: true` en `defaults.yaml`.

## 3. Límite arquitectónico explícito — SMOTE y filas sintéticas

SMOTE genera **vectores numéricos sintéticos** que no corresponden a
ningún tweet real — no tienen texto. `processed_data.clean_text` es
obligatorio porque `0008` necesita texto real para clasificar con
RoBERTa. Escribir una fila sintética con texto inventado violaría K ⊆ X.

**Resolución:** las filas **reales** se escriben en `processed_data`
normalmente, balanceadas o no. Las filas **sintéticas** de SMOTE se
reportan solo como métrica (`num_smote_synthetic_rows`,
`class_distribution_before/after`) — **su persistencia física para un
futuro entrenador queda como hueco explícito, no resuelto en esta
entrega**, porque requiere una convención de artefacto (parquet, `.npz`)
que este proyecto todavía no tiene definida. Cuando llegue el momento de
resolverlo, debe decidirse dónde y en qué formato viven esos vectores
sintéticos — no es una omisión accidental, es una decisión diferida
conscientemente.

`class_weight`, en cambio, no tiene este problema — es solo una métrica
de ponderación (`{"POSITIVE": 0.8, "NEGATIVE": 1.5}`), nunca genera
filas. Se implementa sin restricciones cuando `target_column` existe.

`PCA` tampoco tiene este problema — transforma features **por fila
existente**, sin generar filas nuevas. Los componentes se escriben en
`processed_data.features` (JSONB) para cada fila real sin conflicto.

## 4. Comportamiento — Gherkin

Ver `tests/test_data_preprocessor.feature`. Cubre: preprocesado estándar
sin target (caso Tirendaz), detección automática de `target_column`,
SMOTE omitido sin target, SMOTE aplicado con target y ratio de
desbalance superado, `class_weight` calculado, PCA aplicado y omitido
por features insuficientes, exclusión de leakage, y modo Dev.

## 5. Propiedades LTL

```text
-- [Safety-1] No escribir en processed_data si cleaned_data está vacía.
G (cleaned_data_vacia → ¬escribir_processed_data)

-- [Safety-2] Ninguna fila sintética de SMOTE se escribe en processed_data.
G (fila_sintetica_smote → ¬escribir_en_processed_data)

-- [Config] SMOTE/class_weight solo actúan si target_column fue detectada,
--          sin importar el valor de apply_smote/apply_class_weight.
G ((apply_smote ∨ apply_class_weight) ∧ ¬target_detectada →
   ¬aplicar_smote ∧ ¬aplicar_class_weight)

-- [Liveness-1] Siempre que se invoque el skill, eventualmente terminará.
G (invocacion → F (status_success ∨ status_error))
```

## 6. Restricciones epistémicas (K ⊆ X)

`engagement_score` se calcula con fórmula determinista sobre features
observadas (longitud, signos de énfasis) — no se infiere. La detección
de `target_column` es puramente estructural (¿existe la clave en
`metadata`?), nunca semántica — no se interpreta el significado de una
columna, solo se verifica su presencia.

## 7. Trazabilidad Langfuse

| Evento | Momento | Campos obligatorios |
|---|---|---|
| `data-preprocessor.start` | Inicio | trace_id, run_id, num_input_rows |
| `data-preprocessor.success` | Cierre exitoso | num_processed, target_column_detected, pca_applied, num_smote_synthetic_rows |
| `data-preprocessor.error` | Cierre con error | error_type, error_detail |

## 8. ADRs aplicables

| ADR | Aplicación |
|---|---|
| ADR-006 | `trace_id` y `run_id` resueltos por ContextResolver |
| ADR-007 | Métricas de preprocesado (distribución de clases, PCA) son Dimensión 1 |
| ADR-008 | K ⊆ X: detección de target_column es estructural, nunca semántica |
| ADR-009 | Este archivo sigue el formato canónico de 5+ archivos |
| ADR-010 | Credenciales de PostgreSQL vía `get_required_env()` |

## 9. Pendiente explícito

Persistencia física de vectores sintéticos de SMOTE (formato y ubicación
de artefacto todavía sin definir en el proyecto). Detección de idioma
sigue siendo heurística simple, no un modelo real — mejora futura
señalada desde v1.0.0, sin cambios en esta fusión.
