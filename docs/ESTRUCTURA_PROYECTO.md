# Estructura de carpetas — SIGMA Hito 1

**SIGMA v1.5 · Eco MultiAgentes 4 Skills 2**
Autor: Prof. Marx Agustín García Delgado · Versión: 2.0.0
Reemplaza la versión 1.0.0 — actualizada tras la fusión completa de los
6 skills y el cierre del ciclo de convenciones (`run_id`, deshardcodeo,
`_loader.py`).

---

## Árbol completo

```
sigma-hito1\
│
├── .env.example                  ← Plantilla pública de variables (SÍ a Git)
├── .env                          ← Credenciales reales (NUNCA a Git)
├── .gitignore
├── README.md
├── pyproject.toml
├── orchestrator.py               ← Grafo LangGraph, punto de entrada
├── conftest.py                   ← Fixtures pytest-bdd compartidas
├── docker-compose.yml            ← PostgreSQL, Redis, MinIO, Langfuse, Ollama
│
├── core\
│   ├── __init__.py
│   └── pipeline_state.py         ← PipelineState, SkillResult, circuit breaker
│
├── skills\
│   ├── __init__.py
│   ├── _common.py                ← Infraestructura compartida (fusionada v1.1.0):
│   │                                config, conexiones reales PostgreSQL/Redis,
│   │                                constructor de SkillResult
│   ├── _loader.py                ← Carga dinámica de skill.py por ruta de archivo
│   │                                (resuelve el problema de identificador Python
│   │                                inválido en carpetas con guion — ver ADR-009)
│   │
│   ├── 0000-system-health-check\
│   │   ├── SKILL.md              ← v2.0.0 — veredicto HEALTHY/DEGRADED/BLOCKED
│   │   ├── defaults.yaml         ← timeout, clasificación crítico/opcional
│   │   ├── skill.py              ← verificación real de 5 servicios
│   │   ├── references\schemas.md
│   │   ├── evals\eval_adherencia.yaml
│   │   └── tests\
│   │       ├── test_system_health_check.feature
│   │       ├── test_0000_system_health_check.py
│   │       └── test_system_health_check_stress.py   ← 15 tests de resiliencia
│   │
│   ├── 0001-data-ingestion\
│   │   ├── SKILL.md              ← v2.0.0 — checksum SHA-256, chunks, run_id
│   │   ├── defaults.yaml
│   │   ├── skill.py
│   │   ├── references\schemas.md
│   │   ├── evals\eval_adherencia.yaml
│   │   └── tests\
│   │       ├── test_data_ingestion.feature
│   │       └── test_0001_data_ingestion.py
│   │
│   ├── 0002-data-cleanser\
│   │   ├── SKILL.md              ← v2.0.0 — dedup O(n), cleaned_rejected
│   │   ├── defaults.yaml
│   │   ├── skill.py
│   │   ├── references\schemas.md
│   │   ├── evals\eval_adherencia.yaml
│   │   └── tests\
│   │       ├── test_data_cleanser.feature
│   │       └── test_0002_data_cleanser.py
│   │
│   ├── 0003-data-preprocessor\
│   │   ├── SKILL.md              ← v2.0.0 — leakage, SMOTE/PCA condicionales
│   │   ├── defaults.yaml         ← apply_smote/apply_pca/apply_class_weight
│   │   ├── skill.py
│   │   ├── references\schemas.md
│   │   ├── evals\eval_adherencia.yaml
│   │   └── tests\
│   │       ├── test_data_preprocessor.feature
│   │       └── test_0003_data_preprocessor.py
│   │
│   ├── 0008-sentiment-analyzer\
│   │   ├── SKILL.md              ← v1.1.0 — run_id, model_name deshardcodeado
│   │   ├── defaults.yaml
│   │   ├── skill.py
│   │   ├── references\schemas.md
│   │   ├── evals\eval_adherencia.yaml
│   │   └── tests\
│   │       ├── test_skill.feature
│   │       └── test_0008_sentiment_analyzer.py
│   │
│   └── 0011-viz-reporter\
│       ├── SKILL.md              ← v1.1.0 — run_id agregado
│       ├── defaults.yaml
│       ├── skill.py
│       ├── references\schemas.md
│       ├── evals\eval_adherencia.yaml
│       └── tests\
│           ├── test_skill.feature
│           └── test_0011_viz_reporter.py
│
├── hooks\
│   └── zulip_notifier.py         ← HITL vía Zulip, parse_hitl_response() (NLP)
│
├── db\
│   └── init_schema.sql           ← DDL de 7 tablas (incluye cleaned_rejected)
│
├── data\
│   └── .gitkeep                  ← tirendaz.csv va aquí, nunca a Git
│
├── models\
│   └── .gitkeep                  ← Modelo RoBERTa (~500 MB), nunca a Git
│
├── outputs\
│   └── dashboards\                ← Dashboards HTML generados en modo Dev
│
├── evals\
│   └── results\                   ← JSONs de resultados del evaluador
│
├── logs\
│
├── tests\                         ← Solo infraestructura COMPARTIDA entre skills
│   └── test_common_connections_stress.py   ← 11 tests de _common.py
│
├── docs\
│   ├── AGENTS_CREATOR.md         ← Contrato global de agentes (v1.0.0)
│   ├── adr\
│   │   ├── ADR-001.md a ADR-008.md
│   │   ├── ADR-009.md            ← v2.0.0 — RECTIFICADO, estructura real de skills
│   │   ├── ADR-010.md a ADR-014.md
│   │   └── ADR-015.md            ← Streaming, Hamilton Selector (Hito 3)
│   ├── reportes\
│   │   ├── fusion_0001_0002_v2.0.0.md
│   │   └── verificacion_artefactos_hito1.md
│   └── PROMPT_CONTINUIDAD_HITO2_HITO3.md
│
└── scripts\
    └── old_scripts\
        ├── README.md              ← "NO TOCAR" — versiones históricas preservadas
        ├── conftest_v1.py a conftest_v4.py
        ├── pyproject_v2.toml
        ├── 0000_skill_v2.py
        └── [otros scripts de skills reemplazados durante la fusión]
```

---

## Cambios respecto a la versión 1.0.0 de este documento

Esta versión reemplaza a la anterior, que describía un estado intermedio
del proyecto antes de que se resolvieran varios problemas reales
encontrados durante la auditoría completa. Los cambios más importantes:

**`skill.py` vive dentro de la carpeta con guion de cada skill**, no
suelto en `skills\` como se documentó en un momento intermedio del
proyecto. El problema de que `000X-nombre` no es un identificador Python
válido se resuelve con `skills\_loader.py` (carga por ruta de archivo),
no moviendo el código fuera de su carpeta natural. Ver ADR-009 v2.0.0
para el detalle completo de esta decisión.

**`core\` tiene 2 archivos, no 5.** Los otros 3 que existieron en una
línea de trabajo paralela (`config.py`, `connections.py`, `tracing.py`)
fueron evaluados y descartados: su funcionalidad ya vive, fusionada,
dentro de `skills\_common.py` (conexiones reales con retry) y
`orchestrator.py` (trazabilidad Langfuse directa). Se recomienda
moverlos a `scripts\old_scripts\` como referencia histórica.

**`db\init_schema.sql` tiene 7 tablas, no 6** — se agregó
`cleaned_rejected` durante la fusión de `0002` para las filas con
`row_id` inválido.

**`tests\` (raíz) contiene solo lo que es genuinamente compartido**
entre los 6 skills — `test_common_connections_stress.py`, que prueba
`_common.py`. Cualquier test específico de un skill (incluidos los de
estrés) vive dentro de la carpeta de ese skill, no en la raíz.

**`docs\adr\ADR-009.md` fue rectificado** — la versión original describía
`scripts\`/`assets\`/`references\` sin `tests\` separado; no correspondía
a la convención real ya en uso. `assets\` se retiró de la estructura
obligatoria.

**`docs\AGENTS_CREATOR.md` existe ahora como archivo real** — antes solo
se referenciaba en la documentación sin haberse materializado nunca.

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

# 4. Colocar dataset Tirendaz en data/tirendaz.csv

# 5. Levantar infraestructura
docker compose up -d

# 6. Ejecutar en modo Dev primero (sin infraestructura real)
python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv

# 7. Ejecutar en modo Full (pipeline real completo)
python orchestrator.py --variant Full --data-path ./data/tirendaz.csv
```

---

## Lo que NO está en esta estructura (fuera del Hito 1)

| Carpeta/archivo | Hito | Motivo |
|---|---|---|
| `skills\0005` a `0007`, `0009`, `0010`, `0012`-`0015` | Hito 2 | Arquitectura de 3 orquestadores |
| `skills\0016`-`0019` | Hito 3 | Streaming — solo `0016` se especifica primero |
| `hooks\deploy_to_netlify.py` | Hito 2+ | No se necesita en Hito 1 |
| VPS / `hardening_inicial_vps.sh` | Hito 2 | Vive fuera de este repo, en `Configuracion VPS Hetzner\` |
