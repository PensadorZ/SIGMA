# Estructura de carpetas — SIGMA Hito 1

**SIGMA v1.7 · Post-reestructuración a paquete `sigma/`**
Autor: Prof. Marx Agustín García Delgado · Versión: 3.0.0
Reemplaza la versión 2.0.0 — actualizada tras la reestructuración completa
del código dentro del paquete `sigma/` (`sigma/core/`, `sigma/hooks/`,
`sigma/skills/`), la recuperación de `config.py`/`connections.py`/
`tracing.py` en `sigma/core/`, y el cierre formal del Hito 1 (65/65 tests).

---

## Árbol completo

```
sigma-hito1\
│
├── .env.example                  ← Plantilla pública de variables (SÍ a Git)
├── .env                          ← Credenciales reales (NUNCA a Git)
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── pyproject.toml
├── policies.yaml                 ← Políticas del Policy Server (seguridad)
├── orchestrator.py               ← Grafo LangGraph, punto de entrada
├── webhook_receiver.py           ← Recibe respuestas HITL de Zulip
├── conftest.py                   ← Fixtures pytest-bdd compartidas (ctx, make_state)
├── docker-compose.yml            ← PostgreSQL, Redis, MinIO, Langfuse, Ollama
├── zuliprc                       ← Credenciales Zulip (NUNCA a Git, en .gitignore)
├── sigma_checkpoints.sqlite      ← Estado LangGraph (NUNCA a Git, en .gitignore)
│
├── Learning\                     ← Scripts personales de aprendizaje del operador
│   └── *.py                        (NUNCA a Git, carpeta completa en .gitignore)
│
├── sigma\                        ← Paquete Python instalable — todo el código importable vive aquí
│   ├── __init__.py
│   │
│   ├── core\
│   │   ├── __init__.py
│   │   ├── config.py             ← Variables de entorno, get_sigma_variant(), get_sigma_submode()
│   │   ├── connections.py        ← check_postgresql/redis/minio/langfuse/ollama (ADR-011)
│   │   ├── tracing.py            ← emit_trace_event(), degradación Langfuse→Redis→log local
│   │   ├── checkpointer.py       ← mark_waiting/get_waiting_trace_id/clear_waiting (HITL)
│   │   └── pipeline_state.py     ← PipelineState, SkillResult, circuit breaker
│   │
│   ├── hooks\
│   │   ├── __init__.py
│   │   └── zulip_notifier.py     ← HITL vía Zulip, parse_hitl_response() (NLP)
│   │
│   └── skills\
│       ├── __init__.py
│       ├── _common.py            ← Infraestructura compartida: config, conexiones
│       │                            reales PostgreSQL/Redis, constructor de SkillResult
│       ├── _loader.py            ← Carga dinámica de skill.py por ruta de archivo
│       │                            (resuelve el problema de identificador Python
│       │                            inválido en carpetas con guion — ver ADR-009)
│       │
│       ├── 0000-system-health-check\
│       │   ├── SKILL.md          ← v2.0.0 — veredicto HEALTHY/DEGRADED/BLOCKED
│       │   ├── defaults.yaml     ← timeout, clasificación crítico/opcional
│       │   ├── skill.py          ← verificación real de 5 servicios
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_system_health_check.feature
│       │       ├── test_0000_system_health_check.py
│       │       └── test_system_health_check_stress.py   ← 15 tests de resiliencia
│       │
│       ├── 0001-data-ingestion\
│       │   ├── SKILL.md          ← v2.0.0 — checksum SHA-256, chunks, run_id
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_ingestion.feature
│       │       └── test_0001_data_ingestion.py
│       │
│       ├── 0002-data-cleanser\
│       │   ├── SKILL.md          ← v2.0.0 — dedup O(n), cleaned_rejected
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_cleanser.feature
│       │       └── test_0002_data_cleanser.py
│       │
│       ├── 0003-data-preprocessor\
│       │   ├── SKILL.md          ← v2.0.0 — leakage, SMOTE/PCA condicionales
│       │   ├── defaults.yaml     ← apply_smote/apply_pca/apply_class_weight
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_preprocessor.feature
│       │       └── test_0003_data_preprocessor.py
│       │
│       ├── 0008-sentiment-analyzer\
│       │   ├── SKILL.md          ← v1.1.0 — run_id, model_name deshardcodeado
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_skill.feature
│       │       └── test_0008_sentiment_analyzer.py
│       │
│       └── 0011-viz-reporter\
│           ├── SKILL.md          ← v1.1.0 — run_id agregado
│           ├── defaults.yaml
│           ├── skill.py
│           ├── references\schemas.md
│           ├── evals\eval_adherencia.yaml
│           └── tests\
│               ├── test_skill.feature
│               └── test_0011_viz_reporter.py
│
├── db\
│   └── init_schema.sql           ← DDL de 7 tablas (incluye cleaned_rejected)
│
├── data\
│   ├── .gitkeep                  ← tirendaz.csv, nunca a Git
│   └── raw\                      ← Dataset crudo original, nunca a Git
│       ├── Tweets.csv
│       └── twitter-tweets-sentiment-dataset.zip
│
├── models\
│   └── roberta-sentiment-correcto\   ← Modelo RoBERTa real (~500 MB), nunca a Git
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── tokenizer_config.json
│
├── outputs\
│   └── .gitkeep                  ← Dashboards HTML generados en modo Dev
│
├── logs\
│   └── .gitkeep
│
├── tests\                        ← Infraestructura compartida y verificaciones puntuales
│   ├── test_common_connections_stress.py    ← 11 tests de _common.py
│   ├── test_dashboard_fix.py                ← Verificación puntual del fix de 0011
│   ├── test_dashboard_fix.html
│   ├── test_langfuse_connection.py          ← Verificación de conectividad Langfuse
│   └── hist_diagnoses_tests_202607\         ← Archivo histórico de diagnósticos reales
│       └── [tests de incidentes ya resueltos, no se ejecutan — ver TROUBLESHOOTING.md]
│
├── docs\
│   ├── AGENTS_CREATOR.md         ← Contrato global de agentes (v1.1.0)
│   ├── ESTRUCTURA_PROYECTO.md    ← Este documento
│   ├── SIGMA_v1.7.md             ← Plan Maestro vigente
│   ├── TROUBLESHOOTING.md        ← 5 incidentes reales con diagnóstico completo
│   ├── adr\
│   │   ├── adr-001-memoria-epistemica.md … adr-016-orquestacion-jerarquica.md
│   │   └── adr-README-v1.5.md    ← Índice de los 16 ADRs
│   ├── docs_hist\                ← Versiones archivadas de documentos (nunca sobrescribir)
│   │   ├── SIGMA_v1.5.md
│   │   ├── SIGMA_v1.6.md
│   │   ├── Estructura_Proyecto_v1.md
│   │   └── Roadmap_Tecnico_v1.md
│   └── reportes\                 ← Auditorías internas de proceso (no traducidas al inglés)
│       ├── fusion_0001_0002_v2.0.0.md
│       └── verificacion_artefactos_hito1.md
│
└── scripts\
    ├── download_model.py
    └── old_scripts_sigma\        ← "NO TOCAR" — versiones históricas preservadas
        ├── oldscript_README.md
        ├── init_schema_v2.sql
        ├── old_core\             ← config.py/connections.py/tracing.py viejos (ya recuperados en sigma/core/)
        ├── old_hooks\
        ├── old_main\             ← conftest_v1-4, orchestrator_v1-7, pyproject_v2-3
        └── old_skills\           ← Versiones v1-v5 de cada skill, reemplazadas
```

---

## Cambios respecto a la versión 2.0.0 de este documento

**Corrección importante — `core\` no se redujo a 2 archivos, se recuperó a 5.**
La versión 2.0.0 de este documento afirmaba que `config.py`, `connections.py`
y `tracing.py` habían sido "evaluados y descartados" en favor de fusionar
esa funcionalidad en `skills\_common.py`. Esa afirmación resultó incorrecta:
los tres archivos existían en `scripts\old_scripts_sigma\old_core\` pero
**nunca llegaron a la carpeta activa** — un `__init__.py` los importaba
(`from sigma.core.config import ...`) sin que el archivo existiera
realmente. Se recuperaron, se actualizó `config.py` al esquema de variantes
vigente (`SIGMA-FE/LE/ME/HE` + submodos `Dev`/`Runtime`), y ahora los 5
archivos conviven en `sigma\core\`.

**Todo el código se movió dentro del paquete `sigma\`.** `core\`, `hooks\`
y `skills\` ya no viven sueltos en la raíz — ahora son subpaquetes de
`sigma\`, porque prácticamente todo el código ya usaba internamente el
patrón de import `from sigma.core...` / `from sigma.skills...`, y la
estructura física debía coincidir con eso.

**`scripts\old_scripts\` se corrige a `scripts\old_scripts_sigma\`** —
nombre real de la carpeta, no coincidía con el documento anterior.

**`tests\` (raíz) ya no contiene solo lo compartido entre skills.** Se
agregaron `test_dashboard_fix.py`/`.html` (verificación puntual del fix de
`0011-viz-reporter`) y `test_langfuse_connection.py` (verificación de
conectividad), además de la carpeta `hist_diagnoses_tests_202607\` con
tests de incidentes ya resueltos y archivados (no se ejecutan — excluidos
vía `pyproject.toml`).

**`docs\adr\` pasó de 15 a 16 ADRs**, con nombres de archivo descriptivos
en minúscula (`adr-016-orquestacion-jerarquica.md`, etc.) en vez del
formato `ADR-00X.md` de la versión anterior.

**Se agregó `docs\docs_hist\`** para versiones archivadas de documentos
completos (`SIGMA_v1.5.md`, `SIGMA_v1.6.md`, etc.), y `docs\reportes\`
para auditorías internas de proceso (`fusion_0001_0002_v2.0.0.md`,
`verificacion_artefactos_hito1.md`).

**Nueva carpeta `Learning\`** — scripts personales de aprendizaje del
operador, ignorados por Git en su totalidad.

**Se retiran de este documento** `evals\results\` y
`docs\PROMPT_CONTINUIDAD_HITO2_HITO3.md` — no existen en el árbol real
actual; probablemente nunca se materializaron o se referenciaron
prematuramente en una versión anterior.

**`data\` y `models\` ahora muestran contenido real**, no solo `.gitkeep`
— `data\raw\` con el dataset crudo y `models\roberta-sentiment-correcto\`
con los archivos reales del modelo (ambos siguen sin subirse a Git).

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
python orchestrator.py --variant SIGMA-FE --submode Dev --data-path ./data/tirendaz.csv

# 7. Ejecutar en modo Runtime (pipeline real completo)
python orchestrator.py --variant SIGMA-FE --submode Runtime --data-path ./data/tirendaz.csv
```

---

## Lo que NO está en esta estructura (fuera del Hito 1)

| Carpeta/archivo | Hito | Motivo |
|---|---|---|
| `sigma\skills\0005` a `0007`, `0009`, `0010`, `0012`-`0015` | Hito 2 | Arquitectura de 3 orquestadores |
| `sigma\skills\0016`-`0019` | Hito 3 | Streaming — solo `0016` se especifica primero |
| `sigma\hooks\deploy_to_netlify.py` | Hito 2+ | No se necesita en Hito 1 |
| VPS / `hardening_inicial_vps.sh` | Hito 2 | Vive fuera de este repo, en `Configuracion VPS Hetzner\` |
