---
skill_id: 0004-statistical-validator
name: statistical-validator
version: 1.0.0
sigma_variant: [FE, LE, ME, HE]
description: >
  Selecciona y ejecuta la prueba estadística correcta para validar una
  afirmación (insight), detecta drift entre el dataset actual y una línea
  base (Modo B), y detecta leakage/confusores por correlación (Modo C).
  No genera ni imputa ningún dato — solo emite veredicto sobre datos ya
  presentes en X (ADR-008).
activation_keywords: [validar hipótesis, prueba estadística, drift, leakage, significancia, evidencia insuficiente]
allowed_tools: [Read]
preconditions:
  - "El dataset de entrada existe y su schema fue validado por 0002-data-cleanser"
  - "Si se declara una hipótesis explícita, viene acompañada de su claim en lenguaje natural"
adr_references: [ADR-001, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010, ADR-011, ADR-016]
---

# 0004-statistical-validator

> SIGMA v1.5 · Hito 2, Engineer Datos (ADR-016 Tab. 2, Rollout 1)
> Autor: Prof. Marx Agustín García Delgado · Versión: 1.0.0

## Propósito

Reviewer & Gate puro (taxonomía de nodos, Día 3 del curso Google):
**nunca transforma datos, solo emite un veredicto**. Pertenece a Engineer
Datos (ADR-016 Tab. 2, `0000-0004, 0008, 0011`). Confirmado por
`policies.yaml` real: el rol `statistical_validator` en la capa
estructural del Policy Server (ADR-005) tiene `allowed_tables_prefix: []`
y `denied_tools: ["write_table", "modify_table"]` — es de solo lectura
por diseño, no por convención de este documento.

Tres modos, todos deterministas y de coste $0 (no invoca ningún LLM):

- **Modo A — Selección de prueba de significancia** (Tab. 1).
- **Modo B — Detección de drift.** KS-test exclusivamente
  (`policies.yaml → statistical_validator.drift_method: ks_test`) — PSI
  queda prohibido por mandato de ADR-001 v1.4.
- **Modo C — Detección de leakage por correlación**, usando
  `leakage_correlation_threshold` (0.95, → `REJECTED` directo) y
  `leakage_temporal_threshold` (0.85, → warning).

> ⚠️ **Contradicción sin resolver, señalada explícitamente:** el
> comentario junto a `leakage_temporal_threshold` en `policies.yaml`
> dice *"correlación Spearman que activa warning en pre_processing"*,
> lo que sugeriría que ese chequeo pertenece a `0003-data-preprocessor`.
> El catálogo de `SIGMA_v1.7.md` asigna "leakage y confusores" a `0004`.
> Se implementa aquí porque las claves de configuración viven bajo el
> namespace `statistical_validator`, no `data_preprocessor` — pero
> Marx debe confirmar cuál de los dos documentos es el vigente.

## Tab. 1 — Matriz de decisión (Modo A)

Verificada contra `SIGMA_v1.7.md`, sección "Pruebas avanzadas bajo
incertidumbre":

| Condición del proyecto | Método aplicado | Veredicto si evidencia débil |
|---|---|---|
| Hipótesis explícita declarada | Factor de Bayes (prior uniforme por defecto) | `INSUFFICIENT_EVIDENCE` (BF < umbral) |
| Sin hipótesis, distribución desconocida | Prueba de Permutación + Bootstrapping | `PAUSED_HITL` si el IC es demasiado ancho |
| Datos con índice temporal | Test ADF + Causalidad de Granger | `APPROVED_WITH_WARNINGS` si la serie no es estacionaria |
| Entorno vivo con feedback inmediato | A/B Testing Bayesiano (Multi-Armed Bandits) | `INSUFFICIENT_EVIDENCE` si hay pocas muestras |
| Ninguna condición anterior | Descriptivos básicos (nulos, varianza, duplicados) | `PAUSED_HITL` si superan umbrales |

> ⚠️ **Umbrales pendientes de aprobación** (no existen hoy en
> `policies.yaml`): `bayes_factor_min`, `permutation_ci_width_max`,
> `bayesian_ab_min_samples`. El skill falla rápido con
> `PolicyConfigurationError` si intentas ejecutar esas ramas sin que
> Marx los añada primero — no se asumen valores por defecto para no
> inventar un umbral estadístico sin su aprobación.

La condición se determina de forma **estructural**, nunca semántica
(ADR-008): se verifica la *forma* del input, nunca se infiere la
intención del usuario a partir del contenido.

## Restricción epistémica K ⊆ X (ADR-008)

- Nunca emite `APPROVED` puro — el veredicto más fuerte posible es
  `APPROVED_WITH_WARNINGS`, y solo en la rama `adf_granger`.
- El veredicto de drift y de leakage reporta el estadístico crudo
  (KS, correlación) y su p-valor — nunca una interpretación narrativa
  del *por qué* cambió la distribución o de *qué* columna causa el
  leakage más allá de su nombre, porque esa causa no está en X.

## Configuración (ADR-005, ADR-006, ADR-010)

- Ningún secreto — no llama APIs externas ni bases de datos con
  credenciales propias.
- Umbrales de drift y leakage: `policies.yaml → statistical_validator`
  (ya existen, verificados).
- Umbrales de Modo A: **pendientes**, ver advertencia en Tab. 1.
- No usa `get_required_env()` — no hay ninguna variable obligatoria.

## Trazabilidad (ADR-011, `sigma.core.tracing.emit_trace_event`)

`emit_trace_event(event_name, trace_id, **payload)` exige `trace_id`
explícito — se toma de `state["trace_id"]` (campo real de
`PipelineState`).

| Evento | Cuándo | Payload |
|---|---|---|
| `0004-statistical-validator.start` | Al recibir el input | `mode` (`significance`\|`drift`\|`leakage`) |
| `0004-statistical-validator.branch_selected` | Tras evaluar la Tab. 1 | `branch` |
| `0004-statistical-validator.success` | Al emitir veredicto | `verdict`, `branch`, `statistic`, `p_value`, `duration_ms` |
| `0004-statistical-validator.error` | Excepción no recuperable | `error_type`, `recoverable: false` |

## Circuit breaker (`pipeline_state.py` real)

`ModelNotFoundError`, `SchemaValidationError`, `NoDataToAnalyzeError` ya
están en `NON_RECOVERABLE_ERRORS`. Este skill añade sus propias
excepciones, clasificadas igual (no recuperables — reintentar no arregla
una muestra insuficiente ni un input sin validar):

| Excepción | Clasificación |
|---|---|
| `InputSchemaError` | No recuperable |
| `InsufficientSampleSizeError` | No recuperable |
| `PolicyConfigurationError` (umbral de Modo A ausente en policies.yaml) | No recuperable |

> ⚠️ **Pendiente de tu aprobación, fuera del alcance de este skill:**
> `pipeline_state.py` define `SkillId` como
> `Literal["0000","0001","0002","0003","0008","0011","HANDLE_ERROR"]` —
> **"0004" no está en esa lista**, ni en el diccionario `retry_counts`
> de `initial_state()`. El circuit breaker de `orchestrator.py`/
> `director.py` no puede rastrear reintentos de `0004` hasta que ese
> archivo se actualice. Propuesta exacta al final de esta entrega.

## Propiedades LTL

- **Safety:** `G (verdict = "APPROVED_WITH_WARNINGS" → branch = "adf_granger" ∧ is_stationary = true)`
- **Liveness:** `F (verdict ∨ error_no_recuperable)`
