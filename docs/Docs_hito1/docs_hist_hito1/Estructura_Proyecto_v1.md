# Estructura de carpetas — SIGMA Hito 1
**SIGMA v1.5 · Eco MultiAgentes 3 Skills 1**
Autor: Prof. Marx Agustín García Delgado · Versión: 1.0.0

---

## Árbol completo

```
sigma-hito1/
│
├── .env.example                  ← Plantilla pública de variables de entorno (SÍ a Git)
├── .env                          ← Credenciales reales (NUNCA a Git — en .gitignore)
├── .gitignore                    ← Protege credenciales, modelos y datos de Git
├── README.md                     ← Descripción del proyecto y guía de inicio
├── AGENTS_CREATOR.md              ← Contrato global que todos los agentes leen
│
├── orchestrator.py               ← Grafo LangGraph del pipeline Hito 1 (punto de entrada)
│
├── core/
│   └── pipeline_state.py         ← PipelineState TypedDict + clasificación de errores
│
├── skills/
│   ├── 0000-system-health-check/
│   │   ├── SKILL.md              ← Especificación Gherkin + LTL + trazabilidad
│   │   ├── defaults.yaml         ← Configuración declarativa del skill
│   │   ├── tests/
│   │   │   └── test_skill.feature ← Suite BDD ejecutable con pytest-bdd
│   │   ├── references/
│   │   │   └── schemas.md        ← Schema Pydantic del output
│   │   └── evals/
│   │       └── eval_adherencia.yaml ← Evaluador de adherencia ADR-007
│   │
│   ├── 0001-data-ingestion/      ← [misma estructura de 5 archivos]
│   ├── 0002-data-cleanser/       ← [misma estructura de 5 archivos]
│   ├── 0003-data-preprocessor/   ← [misma estructura de 5 archivos]
│   ├── 0004-statistical-validator/ ← [entregado, Hito 2 — no entra en el pipeline Hito 1]
│   ├── 0008-sentiment-analyzer/  ← [misma estructura de 5 archivos]
│   └── 0011-viz-reporter/        ← [misma estructura de 5 archivos]
│
├── hooks/
│   └── zulip_notifier.py         ← Notificaciones HITL vía Zulip (importado por orchestrator)
│
├── db/
│   └── init_schema.sql           ← DDL de las 6 tablas PostgreSQL del Hito 1
│                                   Ejecutar antes del primer run:
│                                   psql -U postgres -d sigma -f db/init_schema.sql
│
├── data/
│   └── .gitkeep                  ← Carpeta versionada pero vacía en Git
│                                   Aquí va tirendaz.csv (descarga manual, ~22 500 tweets)
│
├── models/
│   └── .gitkeep                  ← Aquí va el modelo RoBERTa (~500 MB, descarga manual)
│                                   Ruta configurada en .env → ROBERTA_MODEL_PATH
│
├── outputs/
│   └── dashboards/               ← Dashboards HTML generados por 0011-viz-reporter
│       └── .gitkeep              ← En producción se persisten en MinIO; aquí solo en Dev
│
├── evals/
│   └── results/                  ← JSONs de resultados del evaluador de adherencia
│       └── .gitkeep
│
├── logs/
│   └── .gitkeep                  ← Logs locales del orquestador (rotación automática)
│
├── docs/
│   └── adr/
│       ├── ADR-001.md            ← Memoria Epistémica Híbrida
│       ├── ADR-002.md            ← Paralelismo MapReduce
│       ├── ADR-003.md            ← Equipo Red/Blue/Green
│       ├── ADR-004.md            ← Vibe Diff + HITL
│       ├── ADR-005.md            ← Policy Server Híbrido (rectificado v1.1)
│       ├── ADR-006.md            ← Placeholders + ContextResolver (rectificado v1.1)
│       ├── ADR-007.md            ← Evaluación 7 Dimensiones (rectificado)
│       ├── ADR-008.md            ← Restricción Epistémica K ⊆ X
│       ├── ADR-009.md            ← Especificación de Skills Gherkin + LTL
│       ├── ADR-010.md            ← Gestión de Secretos 12-Factor
│       ├── ADR-011.md            ← Framework de Orquestación LangGraph
│       ├── ADR-012.md            ← Despliegue de Dashboards con Netlify
│       ├── ADR-013.md            ← Pipelines como Secuencias de Skills
│       ├── ADR-014.md            ← [reservado]
│       └── ADR-015.md            ← Streaming con Hamilton Selector (Hito 3)
│
└── .github/
    └── workflows/
        └── ci.yml                ← GitHub Actions: ejecuta pytest-bdd en cada push
```

---

## Descripción por carpeta

### Raíz del proyecto

| Archivo | Propósito | ¿Va a Git? |
|---|---|---|
| `.env.example` | Plantilla pública con todas las variables necesarias. Sin valores reales | ✅ Sí |
| `.env` | Credenciales reales de Marx. **Jamás a Git** | ❌ No |
| `.gitignore` | Protege `.env`, modelos, datos y outputs de subir accidentalmente a Git | ✅ Sí |
| `README.md` | Descripción del proyecto y pasos de inicio | ✅ Sí |
| `AGENTS_CREATOR.md` | Contrato global del sistema multiagente (acta fundacional de agentes) | ✅ Sí |
| `orchestrator.py` | Punto de entrada del pipeline. Ejecutar con `python orchestrator.py --variant Full --data-path ./data/tirendaz.csv` | ✅ Sí |

### `core/`

Módulos Python compartidos entre el orquestador y los skills. No contiene lógica de negocio — solo tipos, contratos y utilidades transversales.

| Archivo | Contenido |
|---|---|
| `pipeline_state.py` | `PipelineState` TypedDict, `SkillResult`, clasificación de errores recuperables/no recuperables, constantes del circuit breaker |

### `skills/`

Un subdirectorio por skill. Cada uno contiene exactamente 5 archivos canónicos según ADR-009. Los skills del Hito 1 son: 0000, 0001, 0002, 0003, 0008 y 0011. El skill 0004 está entregado pero no forma parte del pipeline mínimo del Hito 1.

### `hooks/`

Scripts Python que el orquestador invoca en puntos específicos del pipeline. No son skills — no tienen SKILL.md ni suite Gherkin. Son acciones de infraestructura.

| Archivo | Cuándo se llama |
|---|---|
| `zulip_notifier.py` | Al detectar `pct_unclear > 30%` en 0008, al fallar el pipeline, al cerrarlo exitosamente |

### `db/`

Scripts SQL de administración de la base de datos. Ejecutar manualmente antes del primer run.

| Archivo | Propósito |
|---|---|
| `init_schema.sql` | Crea las 6 tablas: `pipeline_runs`, `raw_data`, `cleaned_data`, `processed_data`, `sentiment_results`, `pipeline_events`. Incluye verificación final automática |

### `data/`

Carpeta versionada (`.gitkeep`) pero vacía en Git. El dataset Tirendaz (~22 500 tweets) se coloca aquí manualmente tras descargarlo. No va a Git por peso y por privacidad de datos.

### `models/`

Carpeta para el modelo RoBERTa (~500 MB). No va a Git. Se descarga una vez con `python scripts/download_model.py` (script a implementar). La ruta se configura en `.env` → `ROBERTA_MODEL_PATH`.

### `outputs/`

Dashboards HTML generados por `0011-viz-reporter` en modo Dev. En modo Full se persisten en MinIO; esta carpeta es solo para inspección local rápida.

### `evals/`

Resultados JSON del evaluador de adherencia (`eval_adherencia.yaml`) de cada skill. Se generan automáticamente durante la ejecución. No van a Git (`evals/results/` está en `.gitignore`).

### `docs/adr/`

Los 14 Architecture Decision Records que justifican cada decisión arquitectónica de SIGMA. Todos van a Git. Son la memoria institucional del proyecto.

### `.github/workflows/`

GitHub Actions para CI. El workflow `ci.yml` ejecuta la suite pytest-bdd en cada push para garantizar que ningún cambio rompe los contratos Gherkin de los skills.

---

## Orden de operaciones — primera ejecución manual

```bash
# 1. Crear base de datos (una sola vez)
createdb -U postgres sigma
psql -U postgres -d sigma -f db/init_schema.sql

# 2. Configurar variables de entorno (una sola vez)
cp .env.example .env
# Editar .env con tus valores reales

# 3. Descargar modelo RoBERTa (una sola vez, ~500 MB)
python scripts/download_model.py

# 4. Colocar dataset Tirendaz
# Descargar manualmente y mover a:
# data/tirendaz.csv

# 5. Ejecutar en modo Dev (sin PostgreSQL real, con datos sintéticos)
python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv

# 6. Ejecutar en modo Full (pipeline real completo)
python orchestrator.py --variant Full --data-path ./data/tirendaz.csv
```

---

## Lo que NO está en esta estructura (fuera del Hito 1)

| Carpeta/archivo | Hito | Motivo |
|---|---|---|
| `pipelines/*.yaml` | Hito 2 | Pipelines declarativos YAML (ADR-013) |
| `hooks/deploy_to_netlify.py` | Hito 2+ | Netlify no se necesita en Hito 1 |
| `endpoints/` | Hito 2 | APIs REST del sistema |
| `skills/0005` a `0007`, `0009`, `0010`, `0012`–`0015` | Hito 2 | Skills ML/DL, HITL, explainability |
| `skills/0016`–`0019` | Hito 3 | Skills de streaming (ADR-015) |
| VPS / despliegue remoto | Hito 2 | No necesario hasta escalar a 130K+ tweets |
