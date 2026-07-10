# Estructura de carpetas — SIGMA Hito 1

**SIGMA v1.7 · Post-reestructuración a paquete `sigma/`, README bilingüe dividido, pruebas cross-domain**
Autor: Prof. Marx Agustín García Delgado · Versión: 3.2.0
Reemplaza la versión 3.1.0 — actualizada tras la generación de las 6
corridas de prueba (baseline + 2 datasets cross-domain), el reporte de
resultados `output_report.md`, y la reubicación de utilidades operativas
a `scripts/`.

---

## Árbol completo

```
sigma-hito1\
│
├── .env.example                  ← Plantilla pública de variables (va a Git)
├── .env                          ← Credenciales reales (NUNCA a Git)
├── .gitignore
├── LICENSE
├── README.md                     ← Punto de entrada del repo (inglés)
├── README.es.md                  ← Versión en español del README
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
├── assets\
│   └── sigma_banner.png          ← Banner del logo, usado en ambos README
│
├── Learning\                     ← Scripts personales de aprendizaje del operador
│   ├── fix_imports_temp.py          (NUNCA a Git, carpeta completa en .gitignore)
│   ├── fix_imports_temp2.py
│   └── fix_imports_temp2.txt
│
├── sigma\                        ← Paquete Python instalable — todo el código importable vive aquí
│   ├── __init__.py
│   │
│   ├── core\
│   │   ├── __init__.py
│   │   ├── config.py             ← Variables de entorno, get_sigma_variant(), get_sigma_submode()
│   │   ├── connections.py        ← check_postgresql/redis/minio/langfuse/ollama (ADR-011)
│   │   ├── tracing.py            ← emit_trace_event(), degradación Langfuse→Redis→log local
│   │   ├── checkpointer.py       ← mark_waiting/get_waiting_trace_id/clear_waiting/resume_pipeline (HITL)
│   │   └── pipeline_state.py     ← PipelineState, SkillResult, circuit breaker
│   │
│   ├── hooks\
│   │   ├── __init__.py
│   │   └── zulip_notifier.py     ← HITL vía Zulip, parse_hitl_response() (NLP)
│   │
│   └── skills\
│       ├── __init__.py
│       ├── _common.py            ← Infraestructura compartida: config, conexiones
│       │                            reales PostgreSQL/Redis, SkillResult builder
│       ├── _loader.py            ← Carga dinámica de skill.py por ruta de archivo
│       │
│       ├── 0000-system-health-check\
│       │   ├── SKILL.md
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_system_health_check.feature
│       │       ├── test_0000_system_health_check.py
│       │       └── test_system_health_check_stress.py
│       │
│       ├── 0001-data-ingestion\
│       │   ├── SKILL.md
│       │   ├── defaults.yaml         ← required_column ya usa placeholder
│       │   │                            ${SIGMA_INGESTION_REQUIRED_COLUMN:-text}
│       │   ├── skill.py              ← renombra la columna configurada a "text"
│       │   │                            justo tras validar el schema (contrato interno)
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_ingestion.feature
│       │       └── test_0001_data_ingestion.py
│       │
│       ├── 0002-data-cleanser\
│       │   ├── SKILL.md
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_cleanser.feature
│       │       └── test_0002_data_cleanser.py
│       │
│       ├── 0003-data-preprocessor\
│       │   ├── SKILL.md
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_preprocessor.feature
│       │       └── test_0003_data_preprocessor.py
│       │
│       ├── 0008-sentiment-analyzer\
│       │   ├── SKILL.md
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_skill.feature
│       │       └── test_0008_sentiment_analyzer.py
│       │
│       └── 0011-viz-reporter\
│           ├── SKILL.md
│           ├── defaults.yaml
│           ├── skill.py
│           ├── references\schemas.md
│           └── tests\
│               ├── test_skill.feature
│               └── test_0011_viz_reporter.py
│
├── db\
│   └── init_schema.sql           ← DDL de 7 tablas (incluye cleaned_rejected)
│
├── data\
│   ├── .gitkeep
│   ├── tirendaz.csv
│   └── raw\                      ← Datasets crudos, nunca a Git
│       ├── Tweets.csv
│       ├── twitter-tweets-sentiment-dataset.zip
│       ├── test_imdb\
│       │   └── IMDB_cleaned.csv           ← Prueba cross-domain (reseñas de cine)
│       └── test_social\
│           └── Social_Media_Sentiment_Analysis_AI_Trends_2026.csv  ← Prueba cross-domain (multi-plataforma)
│
├── models\
│   └── roberta-sentiment-correcto\   ← Modelo RoBERTa real (~500 MB), nunca a Git
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── tokenizer_config.json
│
├── outputs\
│   ├── .gitkeep
│   ├── output_report.md          ← Reporte de las 3 pruebas cross-domain + guía Kaggle
│   ├── dashboard_run1_failed.html
│   ├── dashboard_run2_failed.html
│   ├── dashboard_run3_ok.html
│   ├── dashboard_run4_ok.html
│   ├── dashboard_run5_imdb_ok.html
│   ├── dashboard_run6_social_ok_warnings.html
│   └── dashboards\
│       └── {trace_id}\index.html  ← Generado automáticamente SOLO en modo Dev;
│                                     en modo Full el dashboard vive únicamente
│                                     en MinIO (ver output_report.md)
│
├── logs\
│   └── .gitkeep
│
├── tests\
│   ├── test_common_connections_stress.py
│   ├── test_dashboard_fix.py
│   ├── test_dashboard_fix.html               ← Única ubicación correcta de este artefacto
│   ├── test_langfuse_connection.py
│   └── hist_diagnoses_tests_202607\
│       └── [tests de incidentes ya resueltos, no se ejecutan]
│
├── docs\
│   ├── AGENTS_CREATOR.md / .en.md
│   ├── ESTRUCTURA_PROYECTO.md / .en.md   ← Este documento
│   ├── SIGMA_v1.7.md / .en.md
│   ├── TROUBLESHOOTING.md / .en.md
│   ├── adr\
│   │   ├── adr-001-memoria-epistemica.md / .en.md
│   │   ├── ... (adr-002 a adr-016, cada uno con su .en.md)
│   │   └── adr-README-v1.5.md / .en.md
│   ├── docs_hist\
│   │   ├── SIGMA_v1.5.md
│   │   ├── SIGMA_v1.6.md
│   │   ├── Estructura_Proyecto_v1.md
│   │   └── Roadmap_Tecnico_v1.md
│   └── reportes\
│       ├── fusion_0001_0002_v2.0.0.md
│       └── verificacion_artefactos_hito1.md
│
└── scripts\
    ├── download_model.py
    ├── resume_hitl_manual.py     ← Reanuda pausas HITL manualmente sin Zulip
    │                                (ver TROUBLESHOOTING.md)
    └── old_scripts_sigma\        ← "NO TOCAR" — versiones históricas preservadas
        └── [...]
```

---

## Cambios respecto a la versión 3.1.0 de este documento

**README dividido en dos archivos.** `README.md` es ahora la versión en
inglés (estándar de GitHub); `README.es.md` contiene la versión en
español. El orden anterior (español como `README.md`, inglés como
`README.en.md`) se invirtió.

**Nueva carpeta `assets\`** — banner visual del proyecto
(`sigma_banner.png`), referenciado desde ambos README.

**`data\raw\` incorpora dos datasets de prueba cross-domain** —
`test_imdb\` (reseñas de cine, texto largo) y `test_social\`
(multi-plataforma: Twitter/Reddit/YouTube) — usados para verificar que
el pipeline generaliza fuera del dominio original de Tirendaz. Detalle
completo de ambas corridas en `outputs\output_report.md`.

**`sigma\skills\0001-data-ingestion\defaults.yaml` corregido** — el
campo `required_column` pasó de estar hardcodeado (`"text"`) a usar el
patrón de placeholder `${VAR:-default}` que exige ADR-006
(`${SIGMA_INGESTION_REQUIRED_COLUMN:-text}`), permitiendo adaptar el
pipeline a datasets con nombres de columna distintos sin modificar
código. `skill.py` ahora renombra la columna configurada a `"text"`
inmediatamente después de validar el schema, de modo que el resto del
código (incluida la escritura a `raw_data` en PostgreSQL) no necesita
ningún cambio adicional.

**Nueva estructura en `outputs\`.** Se agregó `output_report.md`
(reporte de las 3 pruebas cross-domain con sus 6 dashboards HTML) y la
subcarpeta `dashboards\{trace_id}\`, generada automáticamente solo en
modo Dev — en modo Full, los dashboards se persisten exclusivamente en
MinIO y se descargan manualmente cuando se necesita una copia local. El
archivo `test_dashboard_fix.html` que había quedado duplicado dentro de
`outputs\` se eliminó — su única ubicación correcta es junto a su
script en `tests\`.

**Nuevo `scripts\resume_hitl_manual.py`** — utilidad para reanudar
manualmente una corrida pausada en HITL cuando el bot de Zulip está
desactivado, sin depender de `webhook_receiver.py`. Documentado en
`TROUBLESHOOTING.md`. Este archivo vivía antes en la raíz como
`test_checkpointer.py` — se renombró y reubicó porque su nombre
original coincidía con el patrón `test_*.py` que `pyproject.toml` usa
para descubrir tests automáticamente, aunque no es un test real.

**Los 16 ADRs ahora tienen su traducción `.en.md` completa** — incluido
`adr-README-v1.5.en.md`, el índice completo.

> ⚠️ **Nota de verificación pendiente:** se detectó un archivo
> `sigma\sigma_checkpoints.sqlite` duplicado dentro del paquete `sigma\`,
> distinto del que vive en la raíz del proyecto (su ubicación correcta).
> Probablemente se generó al correr un script desde dentro de esa
> carpeta por error. Pendiente de confirmar con `fc` si son idénticos
> antes de eliminar el duplicado.

---

## Orden de operaciones — primera ejecución manual

```bash
# 1. Crear base de datos (una sola vez)
createdb -U postgres sigma
psql -U postgres -d sigma -f db/init_schema.sql

# 2. Configurar variables de entorno (una sola vez)
cp .env.example .env

# 3. Descargar modelo RoBERTa (una sola vez, ~500 MB)
python scripts/download_model.py

# 4. Colocar dataset Tirendaz en data/tirendaz.csv

# 5. Levantar infraestructura
docker compose up -d

# 6. Ejecutar en modo Dev primero (sin infraestructura real)
python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv

# 7. Ejecutar en modo Full (pipeline real completo)
python orchestrator.py --variant Full --data-path ./data/tirendaz.csv

# 8. Para usar un dataset propio con nombre de columna distinto a "text":
set SIGMA_INGESTION_REQUIRED_COLUMN=nombre_real_de_tu_columna
python orchestrator.py --variant Full --data-path ./data/tu_dataset.csv

# 9. Si el bot de Zulip está desactivado y el pipeline queda pausado en HITL:
python scripts/resume_hitl_manual.py
```

> **Nota:** el paso 7 usa el esquema de variantes real que
> `orchestrator.py` acepta hoy (`--variant Full`), no el esquema
> objetivo documentado (`SIGMA-FE` + `--submode`) — esa migración a
> nivel de código se pospuso deliberadamente al Hito 2.

---

## Lo que NO está en esta estructura (fuera del Hito 1)

| Carpeta/archivo | Hito | Motivo |
|---|---|---|
| `sigma\skills\0005` a `0007`, `0009`, `0010`, `0012`-`0015` | Hito 2 | Arquitectura de 3 orquestadores |
| `sigma\skills\0016`-`0019` | Hito 3 | Streaming — solo `0016` se especifica primero |
| `sigma\hooks\deploy_to_netlify.py` | Hito 2+ | No se necesita en Hito 1 |
| VPS / `hardening_inicial_vps.sh` | Hito 2 | Vive fuera de este repo |
