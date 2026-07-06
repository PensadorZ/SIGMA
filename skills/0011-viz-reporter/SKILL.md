---
skill_id: "0011"
name: viz-reporter
version: "1.1.0"
sigma_variant: "Full"
status: active
description: |
  Genera dashboards interactivos y resúmenes ejecutivos en lenguaje natural
  a partir de los resultados del pipeline (sentimiento, engagement, preprocesado).
  Opera en modo completamente autónomo: selecciona el motor de visualización
  adecuado según el volumen y tipo de datos, genera el artefacto, lo persiste
  en MinIO y retorna la URL/ruta sin intervención adicional del orquestador.
  El resumen textual se produce bajo contrato epistémico estricto (K ⊆ X):
  solo describe datos observados, jamás infiere causas ni recomienda acciones
  no respaldadas por X.
activation_keywords:
  - "dashboard"
  - "reporte"
  - "visualizar"
  - "resumen"
  - "informe"
  - "viz"
excluded_from:
  - "limpieza de datos"
  - "análisis de sentimiento"
  - "preprocesado"
  - "ingesta"
allowed_tools:
  - Read
  - Write
  - Bash
max_budget_usd: 0.20
parallelism: none
privacy_mode: relaxed
preconditions:
  - "La tabla processed_data o sentiment_results debe estar poblada en PostgreSQL"
  - "MinIO debe estar disponible y el bucket 'dashboards' debe existir"
  - "Al menos un motor de visualización debe estar instalado (plotly o matplotlib)"
output_destination: "minio://dashboards/{trace_id}/index.html"
langfuse_trace_prefix: "viz-reporter"
adr_references:
  - ADR-002
  - ADR-004
  - ADR-005
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
---

# Skill 0011 — viz-reporter

## 1. Propósito

`viz-reporter` es el skill de cierre del pipeline del Hito 1. Toma los
resultados producidos por los skills anteriores y los convierte en un
artefacto visual autocontenido (HTML interactivo) acompañado de un resumen
ejecutivo generado por un modelo de lenguaje local o externo bajo contrato
epistémico K ⊆ X. El skill decide de forma autónoma qué motor usar, genera
el artefacto, lo persiste en MinIO y retorna un objeto estructurado con todos
los metadatos necesarios. No requiere intervención del orquestador más allá
de la invocación inicial.

---

## 2. Motor de visualización — selección autónoma

El skill evalúa en tiempo de ejecución las condiciones del entorno y el
volumen de los datos de entrada para elegir entre tres motores. La selección
sigue orden de prioridad estricto: `plotly` → `duckdb+plotly` → `matplotlib`.

| Motor | Condición de activación | Output |
|---|---|---|
| `plotly` | Disponible en entorno + dataset ≤ 500 000 filas | HTML interactivo con gráficos Plotly |
| `duckdb+plotly` | Dataset > 500 000 filas (pre-agrega antes de graficar) | HTML interactivo con datos agregados |
| `matplotlib` | Plotly no disponible en entorno (fallback garantizado) | PNG estáticos embebidos en HTML |

El motor efectivamente seleccionado se registra en el evento Langfuse
`viz-reporter.motor_selected` y en el campo `motor` del `VizReporterOutput`.

---

## 3. Comportamiento — Gherkin

```gherkin
# language: es
Característica: Generación autónoma de dashboards y resúmenes ejecutivos
  Como Orquestador de SIGMA
  Quiero que viz-reporter genere un dashboard y un resumen de forma autónoma
  Para cerrar el pipeline del Hito 1 sin intervención adicional del orquestador

  # ── Escenario 1: Happy path ────────────────────────────────────────────
  Escenario: Dashboard completo con datos de sentimiento y engagement
    Dado que la tabla "processed_data" contiene 22500 filas con columnas
          "sentiment", "engagement_score" y "lang"
    Y que Plotly está instalado en el entorno
    Y que MinIO está disponible con el bucket "dashboards"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca viz-reporter con trace_id "wc-001"
    Entonces el skill selecciona el motor "plotly"
    Y genera un archivo HTML con al menos 3 gráficos
          (distribución de sentimiento, top engagement, distribución por idioma)
    Y persiste el HTML en "minio://dashboards/wc-001/index.html"
    Y genera un resumen textual de máximo 250 palabras bajo contrato K ⊆ X
          usando el provider configurado en defaults.yaml
    Y el resumen incluye entre 5 y 8 palabras clave numeradas
    Y retorna un VizReporterOutput con status "success"
    Y emite el evento "viz-reporter.success" en Langfuse con los campos
          motor, num_graficos, dashboard_url, summary_length_chars, duration_ms

  # ── Escenario 2: Dataset grande — pre-agregación DuckDB ────────────────
  Escenario: Dataset grande activa pre-agregación con DuckDB antes de graficar
    Dado que la tabla "processed_data" contiene 800000 filas
    Y que Plotly está instalado en el entorno
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca viz-reporter
    Entonces el skill selecciona el motor "duckdb+plotly"
    Y ejecuta consultas de agregación sobre DuckDB antes de construir los gráficos
    Y genera el HTML con los datos ya agregados
    Y el VizReporterOutput incluye el campo "pre_aggregated: true"
    Y emite "viz-reporter.success" en Langfuse

  # ── Escenario 3: Fallback a matplotlib ────────────────────────────────
  Escenario: Plotly no disponible activa fallback a matplotlib
    Dado que Plotly NO está instalado en el entorno
    Y que matplotlib está disponible
    Y que la tabla "processed_data" contiene datos válidos
    Cuando el Orquestador invoca viz-reporter
    Entonces el skill selecciona el motor "matplotlib"
    Y genera imágenes PNG embebidas en un archivo HTML estático
    Y el VizReporterOutput incluye "motor: matplotlib"
    Y emite "viz-reporter.success" con advertencia "plotly_not_available"
          en el campo warnings

  # ── Escenario 4: Datos de entrada vacíos ─────────────────────────────
  Escenario: Error por datos de entrada vacíos
    Dado que la tabla "processed_data" está vacía
    Cuando el Orquestador invoca viz-reporter
    Entonces el skill lanza NoDataForVizError
    Y NO genera ningún artefacto en MinIO
    Y emite "viz-reporter.error" en Langfuse con reason "empty_dataset"
    Y retorna VizReporterOutput con status "error"
          y error_type "NoDataForVizError"

  # ── Escenario 5: Schema drift — columnas inesperadas ──────────────────
  Escenario: Error por columnas faltantes en los datos de entrada
    Dado que la tabla "processed_data" existe
    Pero no contiene la columna "sentiment" que el skill espera
    Cuando el Orquestador invoca viz-reporter
    Entonces el skill lanza SchemaValidationError
    Y el mensaje de error lista las columnas esperadas y las encontradas
    Y NO genera ningún artefacto en MinIO
    Y emite "viz-reporter.error" en Langfuse con reason "schema_drift"

  # ── Escenario 6: Modo Dev con datos sintéticos ────────────────────────
  Escenario: Ejecución en modo Dev con dataset sintético interno
    Dado que SIGMA_VARIANT es "Dev"
    Y que no hay conexión a PostgreSQL real disponible
    Cuando el Orquestador invoca viz-reporter
    Entonces el skill genera un dataset sintético de 500 filas internamente
    Y produce un dashboard HTML con esos datos sintéticos
    Y el VizReporterOutput incluye "dev_mode: true"
    Y emite "viz-reporter.success" en Langfuse con advertencia "synthetic_data"
```

---

## 4. Propiedades LTL (Lógica Temporal Lineal)

```text
-- [Safety-1] No generar artefactos si el dataset de entrada está vacío.
G (dataset_vacio → ¬generar_dashboard)

-- [Safety-2] No generar artefactos si el schema de entrada no es válido.
G (schema_invalido → ¬generar_dashboard)

-- [Safety-3] El resumen textual solo puede contener contenido observable en X.
G (generar_resumen → contenido_resumen ⊆ X)

-- [Safety-4] No persistir en MinIO si la generación del HTML falló.
G (¬html_generado → ¬escribir_minio)

-- [Safety-5] El presupuesto del provider LLM se verifica antes de invocar.
G (costo_estimado_llm > max_budget_usd → solicitar_aprobacion_hitl)

-- [Liveness-1] Siempre que se invoque el skill, eventualmente terminará.
G (invocacion → F (status_success ∨ status_error))

-- [Liveness-2] Si el motor primario falla, el fallback se activa antes
--              de declarar error total.
G (plotly_falla → X (intentar_matplotlib))

-- [Progress] El motor seleccionado siempre queda registrado en el output.
G (status_success → motor_registrado_en_output)
```

---

## 5. Restricciones epistémicas (K ⊆ X) — ADR-008

El skill opera exclusivamente sobre datos observados presentes en la tabla de
entrada. El contrato para el LLM que genera el resumen textual se inyecta
como system prompt en cada invocación:

```
CONTRATO EPISTÉMICO ESTRICTO — viz-reporter (K ⊆ X)

Eres un reportero de datos. Tienes acceso ÚNICAMENTE a los siguientes datos
observados: [STATS_JSON].

REGLAS ABSOLUTAS:
1. Solo puedes afirmar hechos directamente presentes en STATS_JSON.
2. Tienes prohibido inferir causas, motivaciones o intenciones de usuarios.
3. Tienes prohibido hacer recomendaciones no respaldadas por los datos.
4. Si un dato no está en STATS_JSON, responde: "DATOS_INSUFICIENTES".
5. Extensión máxima: 250 palabras en prosa descriptiva sin bullets.
6. Al final del resumen incluye entre 5 y 8 palabras clave numeradas
   bajo el encabezado "Palabras clave:" que capturen los temas principales
   del corpus analizado. Ejemplo de formato:
   Palabras clave:
   1. sentimiento positivo
   2. idioma español
   3. engagement alto
   4. distribución bimodal
   5. cluster temático principal
```

---

## 6. Gestión del provider LLM

El provider se declara en `defaults.yaml` y puede sobrescribirse mediante
variable de entorno `SIGMA_SUMMARY_PROVIDER`. El skill instancia el proveedor
correcto en tiempo de ejecución sin modificar código:

| Provider | Modelo por defecto | Requisito |
|---|---|---|
| `ollama` | `llama3.2:3b` | Ollama corriendo localmente |
| `gemini` | `gemini-1.5-flash` | `GEMINI_API_KEY` en `.env` vía `get_required_env()` |
| `none` | — | Sin resumen textual; `summary_text: null` en output |

Si `summary_provider: none`, el campo `summary_text` queda en `null` en el
`VizReporterOutput`. Esto no es un error ni genera advertencia.

---

## 7. Trazabilidad Langfuse

| Evento | Momento de emisión | Campos obligatorios |
|---|---|---|
| `viz-reporter.start` | Inicio del skill | trace_id, sigma_variant, input_rows |
| `viz-reporter.motor_selected` | Tras elección del motor | motor, reason, input_rows |
| `viz-reporter.html_generated` | Tras generar el HTML | num_graficos, duration_ms |
| `viz-reporter.summary_generated` | Tras generar el resumen | provider, length_chars, keywords_count |
| `viz-reporter.minio_persisted` | Tras escritura exitosa en MinIO | dashboard_url |
| `viz-reporter.success` | Cierre exitoso | todos los campos de VizReporterOutput |
| `viz-reporter.error` | Cierre con error | error_type, error_detail, trace_id |

---

## 8. Integración opcional: Netlify + Observable Framework

> Esta sección es documentación de referencia arquitectónica.
> La integración con Netlify NO forma parte de la lógica interna de este
> skill. Es un hook externo (`hooks/deploy_to_netlify.py`) que el orquestador
> invoca opcionalmente tras recibir el `VizReporterOutput`.
>
> **Corrección (auditoría Eco MultiAgentes 4 Skills 2):** esta sección
> citaba antes "ADR-012" como respaldo formal — es incorrecto. El
> `ADR-012` real trata "Gestión de Versiones y Promoción de Skills", no
> Netlify. No existe todavía un ADR verificado que formalice esta
> integración — queda como hueco explícito de gobernanza, no como
> decisión ya respaldada.

### 8.1 Flujo básico con Plotly → Netlify

```
viz-reporter retorna dashboard_url (ruta MinIO)
        ↓
hooks/deploy_to_netlify.py lee el HTML desde MinIO
        ↓
Publica en Netlify vía API REST
(NETLIFY_AUTH_TOKEN + NETLIFY_SITE_ID desde .env via get_required_env())
        ↓
Retorna URL pública: https://{site}.netlify.app/dashboards/{trace_id}/
```

Variables de entorno requeridas (nunca hardcodeadas, ADR-010):

```
NETLIFY_AUTH_TOKEN=<token>
NETLIFY_SITE_ID=<site_id>
```

### 8.2 Ruta avanzada: Observable Framework → Netlify

Para dashboards visualmente más ricos e interactivos, la ruta recomendada
combina **Observable Framework** (observable.hq, licencia MIT) con Netlify:

```
Datos JSON exportados por viz-reporter desde MinIO
        ↓
Observable Framework compila notebooks reactivos JavaScript a HTML estático puro
(sin servidor, sin backend, sin runtime adicional)
        ↓
HTML estático con interactividad nativa, animaciones y filtros en tiempo real
        ↓
Deploy en Netlify → URL pública inmediata
```

Observable Framework produce dashboards con interactividad nativa, filtros
en tiempo real, animaciones y visualizaciones de nivel editorial sin coste
adicional de infraestructura. El HTML generado es completamente estático y
deployable directamente en Netlify sin servidor. Esta ruta está documentada
aquí como horizonte técnico del Hito 2; no es requisito del Hito 1.

---

## 9. ADRs aplicables

| ADR | Aplicación concreta en este skill |
|---|---|
| ADR-002 | Pre-agregación DuckDB activa el patrón MapReduce-lite para datasets > 500K filas |
| ADR-004 | Si el costo estimado del LLM supera `max_budget_usd`, se pausa y notifica vía Zulip |
| ADR-005 | Policy Server valida que Write solo ocurra en `dashboards/`, nunca en tablas transaccionales |
| ADR-006 | `{trace_id}` y `{workflow_id}` son placeholders resueltos por ContextResolver, nunca hardcodeados |
| ADR-007 | `num_graficos` y `summary_length_chars` se registran como métricas de Dimensión 1 (corrección funcional) |
| ADR-008 | El contrato epistémico K ⊆ X se inyecta literalmente en el system prompt del LLM |
| ADR-009 | Este archivo sigue el formato canónico de 5 archivos: SKILL.md, defaults.yaml, test_skill.feature, schemas.md, eval_adherencia.yaml |
| ADR-010 | `NETLIFY_AUTH_TOKEN`, `MINIO_ACCESS_KEY` y credenciales LLM se obtienen exclusivamente vía `get_required_env()` |
| — | La integración con Netlify NO tiene ADR formal todavía — hueco de gobernanza explícito, corregido en la auditoría de Eco MultiAgentes 4 Skills 2 (antes citaba erróneamente ADR-012, que en realidad trata versionado de skills) |

---

## Historial de resolución

**v1.1.0 (auditoría de cierre de ciclo, Eco MultiAgentes 4 Skills 2):**
`run_id` y `trace_id` faltaban explícitamente en el output, igual que en
`0008` — se usaban internamente pero nunca se exponían en el
`SkillResult`. Corregido, consistente con `0000`/`0001`/`0002`/`0003`.
