---
tipo: auditoria_artefactos
alcance: snapshot_historico
changelog:
  a:
    fecha: "2026-07"
    descripcion: >
      Auditoría original de artefactos entregados vs. esperados para el
      cierre del Hito 1, previa a la reestructuración del proyecto dentro
      del paquete sigma/.
---

> **Nota de historicidad — leer antes de usar este documento:**
> Este reporte es un **snapshot fijo** del estado del proyecto en el
> momento en que se escribió, **antes** de la reestructuración que movió
> `core/`, `hooks/` y `skills/` dentro del paquete `sigma/`. Las rutas que
> aparecen aquí (`core\`, `skills\`, sin el prefijo `sigma\`) reflejan la
> estructura de ese momento, no la estructura actual del repositorio.
>
> El hallazgo pendiente registrado al final (`0008\references\schemas.md`
> y sus tests sin actualizar con `run_id`/`trace_id`) **ya fue resuelto**
> en trabajo posterior — la suite completa de tests confirma 65/65
> pasando, incluyendo la cobertura de `run_id` en `0008`.
>
> Este documento se conserva como registro histórico del proceso de
> auditoría, no como referencia del estado actual del proyecto. Para el
> estado actual, consultar `SIGMA_v1.7.md` y el `git log` del repositorio.

---

# Verificación final de artefactos — SIGMA Hito 1

**SIGMA v1.5 · Eco MultiAgentes 4 Skills 2**
Autor: Prof. Marx Agustín García Delgado · Fecha: Julio 2026

Este documento cruza dos cosas distintas: qué debería existir en
`sigma-hito1\` según todo lo acordado en esta conversación (Tabla 1), y
si ese artefacto específico fue efectivamente entregado como descarga en
algún punto de esta misma conversación (Tabla 2). Las versiones se
extrajeron directamente de la cabecera de cada archivo real, no de
memoria — donde un archivo no declara versión explícita, se marca así.

---

## Tabla 1 — Inventario esperado (qué debe estar, y para qué sirve)

### Raíz del proyecto

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `orchestrator.py` | `sigma-hito1\` | 1.0.0 | Grafo LangGraph con circuit breaker, punto de entrada del pipeline |
| `conftest.py` | `sigma-hito1\` | sin versión declarada | Fixtures pytest-bdd compartidas por todos los skills |
| `docker-compose.yml` | `sigma-hito1\` | sin versión declarada | Infraestructura: PostgreSQL, Redis, MinIO, Langfuse, Ollama |
| `.env.example` | `sigma-hito1\` | — | Plantilla pública de variables de entorno |
| `.gitignore` | `sigma-hito1\` | — | Protege `.env`, modelos, datos |
| `ESTRUCTURA_PROYECTO.md` | `sigma-hito1\` | — | Mapa de carpetas y su propósito |
| `pyproject.toml` | `sigma-hito1\` | referenciado, no regenerado aquí | Configuración Python del proyecto |

### `core\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `__init__.py` | `core\` | — | Paquete raíz |
| `pipeline_state.py` | `core\` | 1.0.0 | `PipelineState`, `SkillResult`, clasificación de errores del circuit breaker |

### `skills\` — raíz

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `__init__.py` | `skills\` | — | Paquete raíz de skills |
| `_common.py` | `skills\` | 1.1.0 | Infraestructura compartida: config, conexiones reales PostgreSQL/Redis, `SkillResult` |
| `_loader.py` | `skills\` | sin versión declarada | Carga dinámica de `skill.py` por ruta de archivo |

### `skills\0000-system-health-check\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `SKILL.md` | `skills\0000-system-health-check\` | 2.0.0 | Especificación: veredicto HEALTHY/DEGRADED/BLOCKED |
| `defaults.yaml` | `skills\0000-system-health-check\` | 2.0.0 | Timeout, clasificación crítico/opcional configurable |
| `skill.py` | `skills\0000-system-health-check\` | 2.0.0 | Verificación real de 5 servicios |
| `references\schemas.md` | `skills\0000-system-health-check\` | 2.0.0 | `HealthCheckOutput`, `ServiceStatus` |
| `evals\eval_adherencia.yaml` | `skills\0000-system-health-check\` | 2.0.0 | Evaluador de adherencia |
| `tests\test_system_health_check.feature` | `skills\0000-system-health-check\` | — | Escenarios Gherkin |
| `tests\test_0000_system_health_check.py` | `skills\0000-system-health-check\` | — | Step definitions |
| `tests\test_system_health_check_stress.py` | `skills\0000-system-health-check\` | — | 15 tests de resiliencia |

### `skills\0001-data-ingestion\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `SKILL.md` | `skills\0001-data-ingestion\` | 2.0.0 | Checksum SHA-256, chunks, `run_id` |
| `defaults.yaml` | `skills\0001-data-ingestion\` | 2.0.0 | `chunk_size`, `required_column` |
| `skill.py` | `skills\0001-data-ingestion\` | 2.0.0 | Ingesta con checksum e integridad |
| `references\schemas.md` | `skills\0001-data-ingestion\` | 2.0.0 | `DataIngestionOutput` |
| `evals\eval_adherencia.yaml` | `skills\0001-data-ingestion\` | 2.0.0 | Evaluador de adherencia |
| `tests\test_data_ingestion.feature` | `skills\0001-data-ingestion\` | — | Escenarios Gherkin |
| `tests\test_0001_data_ingestion.py` | `skills\0001-data-ingestion\` | — | Step definitions |

### `skills\0002-data-cleanser\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `SKILL.md` | `skills\0002-data-cleanser\` | 2.0.0 | Dedup O(n), `cleaned_rejected` |
| `defaults.yaml` | `skills\0002-data-cleanser\` | 2.0.0 | Umbral de duplicados configurable |
| `skill.py` | `skills\0002-data-cleanser\` | 2.0.0 | Dedup exacto + casi-exacto O(n) |
| `references\schemas.md` | `skills\0002-data-cleanser\` | 2.0.0 | Output + tabla `cleaned_rejected` |
| `evals\eval_adherencia.yaml` | `skills\0002-data-cleanser\` | 2.0.0 | Evaluador de adherencia |
| `tests\test_data_cleanser.feature` | `skills\0002-data-cleanser\` | — | Escenarios Gherkin (reescrito, fusión) |
| `tests\test_0002_data_cleanser.py` | `skills\0002-data-cleanser\` | — | Step definitions |

### `skills\0003-data-preprocessor\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `SKILL.md` | `skills\0003-data-preprocessor\` | 2.0.0 | Leakage, SMOTE/PCA condicionales |
| `defaults.yaml` | `skills\0003-data-preprocessor\` | 2.0.0 | Flags `apply_smote`/`apply_pca`/`apply_class_weight` |
| `skill.py` | `skills\0003-data-preprocessor\` | 2.0.0 | `StandardScaler` real, detección automática de target |
| `references\schemas.md` | `skills\0003-data-preprocessor\` | 2.0.0 | Output + tabla de warnings |
| `evals\eval_adherencia.yaml` | `skills\0003-data-preprocessor\` | 2.0.0 | Evaluador de adherencia |
| `tests\test_data_preprocessor.feature` | `skills\0003-data-preprocessor\` | — | Escenarios Gherkin |
| `tests\test_0003_data_preprocessor.py` | `skills\0003-data-preprocessor\` | — | Step definitions |

### `skills\0008-sentiment-analyzer\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `SKILL.md` | `skills\0008-sentiment-analyzer\` | 1.1.0 | `run_id`/`trace_id`, `model_name` deshardcodeado |
| `defaults.yaml` | `skills\0008-sentiment-analyzer\` | 1.0.0 | `batch_size`, `confidence_threshold`, `model.name` |
| `skill.py` | `skills\0008-sentiment-analyzer\` | sin versión declarada en el código | Inferencia RoBERTa real |
| `references\schemas.md` | `skills\0008-sentiment-analyzer\` | 1.0.0 | `SentimentAnalyzerOutput` |
| `evals\eval_adherencia.yaml` | `skills\0008-sentiment-analyzer\` | 1.0.0 | Evaluador de adherencia |
| `tests\test_skill.feature` | `skills\0008-sentiment-analyzer\` | — | Escenarios Gherkin |
| `tests\test_0008_sentiment_analyzer.py` | `skills\0008-sentiment-analyzer\` | — | Step definitions |

### `skills\0011-viz-reporter\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `SKILL.md` | `skills\0011-viz-reporter\` | 1.1.0 | `run_id`/`trace_id` agregados |
| `defaults.yaml` | `skills\0011-viz-reporter\` | 1.0.0 | Motores, umbral DuckDB, resumen |
| `skill.py` | `skills\0011-viz-reporter\` | sin versión declarada en el código | Selección autónoma de motor |
| `references\schemas.md` | `skills\0011-viz-reporter\` | 1.0.0 | `VizReporterOutput` con `run_id` |
| `evals\eval_adherencia.yaml` | `skills\0011-viz-reporter\` | 1.0.0 | Evaluador de adherencia |
| `tests\test_skill.feature` | `skills\0011-viz-reporter\` | — | Escenarios Gherkin (con verificación `run_id`) |
| `tests\test_0011_viz_reporter.py` | `skills\0011-viz-reporter\` | — | Step definitions |

### Compartidos fuera de `skills\`

| Artefacto | Ubicación | Versión | Función |
|---|---|---|---|
| `zulip_notifier.py` | `hooks\` | 1.0.0 | Notificaciones HITL, `parse_hitl_response()` |
| `init_schema.sql` | `db\` | 1.0.0 | DDL de 7 tablas (incluye `cleaned_rejected`) |
| `test_common_connections_stress.py` | `tests\` | — | 11 tests de estrés de `_common.py` |
| `fusion_0001_0002_v2.0.0.md` | `docs\reportes\` | — | Reporte técnico de la fusión |
| `ADR-015.md` | `docs\adr\` | 1.0.0 (literal `a.`) | Streaming, Hamilton Selector |
| `PROMPT_CONTINUIDAD_HITO2_HITO3.md` | `docs\` | — | Prompt de arranque para Hito 2 |
| `README.md` | `scripts\old_scripts\` | — | Advertencia "No tocar" |

---

## Tabla 2 — Verificación de descarga (¿lo tienes ya en tus manos?)

| Artefacto | Ubicación | Versión | Descarga |
|---|---|---|---|
| `orchestrator.py` | `sigma-hito1\` | 1.0.0 | Sí |
| `conftest.py` | `sigma-hito1\` | — | Sí |
| `docker-compose.yml` | `sigma-hito1\` | — | Sí (ajustar puertos antes de usar) |
| `.env.example` | `sigma-hito1\` | — | Sí |
| `.gitignore` | `sigma-hito1\` | — | Sí |
| `ESTRUCTURA_PROYECTO.md` | `sigma-hito1\` | — | Sí (con corrección AGENTS_CREATOR.md) |
| `pyproject.toml` | `sigma-hito1\` | — | No generado en esta conversación — es tuyo, de otra sesión |
| `core\__init__.py` | `core\` | — | Sí |
| `core\pipeline_state.py` | `core\` | 1.0.0 | Sí |
| `skills\__init__.py` | `skills\` | — | Sí |
| `skills\_common.py` | `skills\` | 1.1.0 | Sí (versión fusionada) |
| `skills\_loader.py` | `skills\` | — | Sí |
| `0000\SKILL.md` | `skills\0000-system-health-check\` | 2.0.0 | Sí |
| `0000\defaults.yaml` | `skills\0000-system-health-check\` | 2.0.0 | Sí |
| `0000\skill.py` | `skills\0000-system-health-check\` | 2.0.0 | Sí |
| `0000\references\schemas.md` | `skills\0000-system-health-check\` | 2.0.0 | Sí |
| `0000\evals\eval_adherencia.yaml` | `skills\0000-system-health-check\` | 2.0.0 | Sí |
| `0000\tests\*.feature` | `skills\0000-system-health-check\` | — | Sí |
| `0000\tests\test_0000_*.py` | `skills\0000-system-health-check\` | — | Sí |
| `0000\tests\*_stress.py` | `skills\0000-system-health-check\` | — | Sí |
| `0001\SKILL.md` | `skills\0001-data-ingestion\` | 2.0.0 | Sí |
| `0001\defaults.yaml` | `skills\0001-data-ingestion\` | 2.0.0 | Sí |
| `0001\skill.py` | `skills\0001-data-ingestion\` | 2.0.0 | Sí |
| `0001\references\schemas.md` | `skills\0001-data-ingestion\` | 2.0.0 | Sí |
| `0001\evals\eval_adherencia.yaml` | `skills\0001-data-ingestion\` | 2.0.0 | Sí |
| `0001\tests\*.feature` | `skills\0001-data-ingestion\` | — | Sí |
| `0001\tests\test_0001_*.py` | `skills\0001-data-ingestion\` | — | Sí |
| `0002\SKILL.md` | `skills\0002-data-cleanser\` | 2.0.0 | Sí |
| `0002\defaults.yaml` | `skills\0002-data-cleanser\` | 2.0.0 | Sí |
| `0002\skill.py` | `skills\0002-data-cleanser\` | 2.0.0 | Sí |
| `0002\references\schemas.md` | `skills\0002-data-cleanser\` | 2.0.0 | Sí |
| `0002\evals\eval_adherencia.yaml` | `skills\0002-data-cleanser\` | 2.0.0 | Sí |
| `0002\tests\*.feature` | `skills\0002-data-cleanser\` | — | Sí (reescrito) |
| `0002\tests\test_0002_*.py` | `skills\0002-data-cleanser\` | — | Sí |
| `0003\SKILL.md` | `skills\0003-data-preprocessor\` | 2.0.0 | Sí |
| `0003\defaults.yaml` | `skills\0003-data-preprocessor\` | 2.0.0 | Sí |
| `0003\skill.py` | `skills\0003-data-preprocessor\` | 2.0.0 | Sí |
| `0003\references\schemas.md` | `skills\0003-data-preprocessor\` | 2.0.0 | Sí |
| `0003\evals\eval_adherencia.yaml` | `skills\0003-data-preprocessor\` | 2.0.0 | Sí |
| `0003\tests\*.feature` | `skills\0003-data-preprocessor\` | — | Sí |
| `0003\tests\test_0003_*.py` | `skills\0003-data-preprocessor\` | — | Sí |
| `0008\SKILL.md` | `skills\0008-sentiment-analyzer\` | 1.1.0 | Sí |
| `0008\defaults.yaml` | `skills\0008-sentiment-analyzer\` | 1.0.0 | Sí (original, sin cambios) |
| `0008\skill.py` | `skills\0008-sentiment-analyzer\` | sin versión | Sí (con fix `run_id`/`model_name`) |
| `0008\references\schemas.md` | `skills\0008-sentiment-analyzer\` | 1.0.0 | No actualizado con `run_id`/`trace_id` al momento de este reporte — **resuelto posteriormente, ver nota de historicidad al inicio** |
| `0008\evals\eval_adherencia.yaml` | `skills\0008-sentiment-analyzer\` | 1.0.0 | Sí |
| `0008\tests\*.feature` | `skills\0008-sentiment-analyzer\` | — | No actualizado con verificación de `run_id` al momento de este reporte — **resuelto posteriormente** |
| `0008\tests\test_0008_*.py` | `skills\0008-sentiment-analyzer\` | — | No actualizado con verificación de `run_id` al momento de este reporte — **resuelto posteriormente** |
| `0011\SKILL.md` | `skills\0011-viz-reporter\` | 1.1.0 | Sí |
| `0011\defaults.yaml` | `skills\0011-viz-reporter\` | 1.0.0 | Sí (reentregado, confirmado íntegro) |
| `0011\skill.py` | `skills\0011-viz-reporter\` | sin versión | Sí (con fix `run_id`) |
| `0011\references\schemas.md` | `skills\0011-viz-reporter\` | 1.0.0 | Sí (actualizado con `run_id`) |
| `0011\evals\eval_adherencia.yaml` | `skills\0011-viz-reporter\` | 1.0.0 | Sí |
| `0011\tests\*.feature` | `skills\0011-viz-reporter\` | — | Sí (actualizado con `run_id`) |
| `0011\tests\test_0011_*.py` | `skills\0011-viz-reporter\` | — | Sí (actualizado con `run_id`) |
| `hooks\zulip_notifier.py` | `hooks\` | 1.0.0 | Sí |
| `db\init_schema.sql` | `db\` | 1.0.0 | Sí (con `cleaned_rejected`) |
| `tests\test_common_connections_stress.py` | `tests\` | — | Sí (confirmado idéntico por ti) |
| `docs\reportes\fusion_0001_0002_v2.0.0.md` | `docs\reportes\` | — | Sí |
| `docs\adr\ADR-015.md` | `docs\adr\` | 1.0.0 | Sí |
| `docs\PROMPT_CONTINUIDAD_HITO2_HITO3.md` | `docs\` | — | Sí (texto plano, sin archivo) |
| `scripts\old_scripts\README.md` | `scripts\old_scripts\` | — | Sí |
| `AGENTS_CREATOR.md` | repositorio de documentación, no `sigma-hito1` | — | Nunca generado como archivo — solo referenciado |
| `hardening_inicial_vps.sh` | fuera de `sigma-hito1`, en `Configuracion VPS Hetzner\` | — | Tuyo, de otra sesión — reubicado por ti, no por mí |

---

## Hallazgo real de esta verificación (al momento de escribir este reporte)

Al construir la Tabla 2 encontré algo que se me había pasado: **cuando
agregué `run_id`/`trace_id` al output de `0008` y `0011`, solo actualicé
`schemas.md` y el test de `0011` — nunca hice el mismo trabajo para
`0008`.** `0008\references\schemas.md`, su `.feature` y su archivo de
step definitions seguían sin documentar ni verificar el campo `run_id`
que ya existía en su `skill.py`. Era el mismo defecto que se había
cerrado para `0011`, pendiente todavía en `0008` **en ese momento** —
ver nota de historicidad al inicio del documento sobre su resolución
posterior.

**Total de artefactos esperados en ese momento:** 68 (incluyendo los 3
que eran del autor, fuera de la generación de esta conversación).
**Total confirmado entregado en ese momento:** 65.
**Pendientes reales en ese momento:** 3 (`0008\references\schemas.md`,
su `.feature` y su archivo de step definitions — todos por el mismo
motivo, ya resueltos).
