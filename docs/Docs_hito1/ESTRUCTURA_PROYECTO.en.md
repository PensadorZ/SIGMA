# Project Folder Structure — SIGMA Milestone 1

**SIGMA v1.7 · Post-restructuring into the `sigma/` package, bilingual README split, cross-domain tests**
Author: Prof. Marx Agustín García Delgado · Version: 3.2.0
Replaces version 3.1.0 — updated after generating 6 test runs (baseline
+ 2 cross-domain datasets), the `output_report.md` results report, and
relocating operational utilities to `scripts/`.

---

## Full tree

```
sigma-hito1\
│
├── .env.example                  ← Public variable template (goes to Git)
├── .env                          ← Real credentials (NEVER to Git)
├── .gitignore
├── LICENSE
├── README.md                     ← Repo entry point (English)
├── README.es.md                  ← Spanish version of the README
├── requirements.txt
├── pyproject.toml
├── policies.yaml                 ← Policy Server policies (security)
├── orchestrator.py               ← LangGraph graph, entry point
├── webhook_receiver.py           ← Receives HITL responses from Zulip
├── conftest.py                   ← Shared pytest-bdd fixtures (ctx, make_state)
├── docker-compose.yml            ← PostgreSQL, Redis, MinIO, Langfuse, Ollama
├── zuliprc                       ← Zulip credentials (NEVER to Git, in .gitignore)
├── sigma_checkpoints.sqlite      ← LangGraph state (NEVER to Git, in .gitignore)
│
├── assets\
│   └── sigma_banner.png          ← Logo banner, used in both READMEs
│
├── Learning\                     ← Operator's personal learning scripts
│   ├── fix_imports_temp.py          (NEVER to Git, whole folder in .gitignore)
│   ├── fix_imports_temp2.py
│   └── fix_imports_temp2.txt
│
├── sigma\                        ← Installable Python package — all importable code lives here
│   ├── __init__.py
│   │
│   ├── core\
│   │   ├── __init__.py
│   │   ├── config.py             ← Environment variables, get_sigma_variant(), get_sigma_submode()
│   │   ├── connections.py        ← check_postgresql/redis/minio/langfuse/ollama (ADR-011)
│   │   ├── tracing.py            ← emit_trace_event(), Langfuse→Redis→local-log degradation
│   │   ├── checkpointer.py       ← mark_waiting/get_waiting_trace_id/clear_waiting/resume_pipeline (HITL)
│   │   └── pipeline_state.py     ← PipelineState, SkillResult, circuit breaker
│   │
│   ├── hooks\
│   │   ├── __init__.py
│   │   └── zulip_notifier.py     ← Zulip HITL, parse_hitl_response() (NLP)
│   │
│   └── skills\
│       ├── __init__.py
│       ├── _common.py            ← Shared infrastructure: config, real
│       │                            PostgreSQL/Redis connections, SkillResult builder
│       ├── _loader.py            ← Dynamic loading of skill.py by file path
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
│       │   ├── defaults.yaml         ← required_column now uses the
│       │   │                            ${SIGMA_INGESTION_REQUIRED_COLUMN:-text} placeholder
│       │   ├── skill.py              ← renames the configured column to "text"
│       │   │                            right after schema validation (internal contract)
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
│   └── init_schema.sql           ← DDL for 7 tables (includes cleaned_rejected)
│
├── data\
│   ├── .gitkeep
│   ├── tirendaz.csv
│   └── raw\                      ← Raw datasets, never to Git
│       ├── Tweets.csv
│       ├── twitter-tweets-sentiment-dataset.zip
│       ├── test_imdb\
│       │   └── IMDB_cleaned.csv           ← Cross-domain test (movie reviews)
│       └── test_social\
│           └── Social_Media_Sentiment_Analysis_AI_Trends_2026.csv  ← Cross-domain test (multi-platform)
│
├── models\
│   └── roberta-sentiment-correcto\   ← Real RoBERTa model (~500 MB), never to Git
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── tokenizer_config.json
│
├── outputs\
│   ├── .gitkeep
│   ├── output_report.md          ← Report of the 3 cross-domain tests + Kaggle guide
│   ├── dashboard_run1_failed.html
│   ├── dashboard_run2_failed.html
│   ├── dashboard_run3_ok.html
│   ├── dashboard_run4_ok.html
│   ├── dashboard_run5_imdb_ok.html
│   ├── dashboard_run6_social_ok_warnings.html
│   └── dashboards\
│       └── {trace_id}\index.html  ← Auto-generated ONLY in Dev mode;
│                                     in Full mode the dashboard lives only
│                                     in MinIO (see output_report.md)
│
├── logs\
│   └── .gitkeep
│
├── tests\
│   ├── test_common_connections_stress.py
│   ├── test_dashboard_fix.py
│   ├── test_dashboard_fix.html               ← This artifact's only correct location
│   ├── test_langfuse_connection.py
│   └── hist_diagnoses_tests_202607\
│       └── [tests for already-resolved incidents, not run]
│
├── docs\
│   ├── AGENTS_CREATOR.md / .en.md
│   ├── ESTRUCTURA_PROYECTO.md / .en.md   ← This document
│   ├── SIGMA_v1.7.md / .en.md
│   ├── TROUBLESHOOTING.md / .en.md
│   ├── adr\
│   │   ├── adr-001-memoria-epistemica.md / .en.md
│   │   ├── ... (adr-002 through adr-016, each with its .en.md)
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
    ├── resume_hitl_manual.py     ← Manually resumes HITL pauses without Zulip
    │                                (see TROUBLESHOOTING.md)
    └── old_scripts_sigma\        ← "DO NOT TOUCH" — preserved historical versions
        └── [...]
```

---

## Changes from version 3.1.0 of this document

**README split into two files.** `README.md` is now the English
version (GitHub's standard); `README.es.md` holds the Spanish version.
The previous order (Spanish as `README.md`, English as `README.en.md`)
was reversed.

**New `assets\` folder** — the project's visual banner
(`sigma_banner.png`), referenced from both READMEs.

**`data\raw\` now includes two cross-domain test datasets** —
`test_imdb\` (movie reviews, long-form text) and `test_social\`
(multi-platform: Twitter/Reddit/YouTube) — used to verify the pipeline
generalizes beyond Tirendaz's original domain. Full detail on both runs
in `outputs\output_report.md`.

**`sigma\skills\0001-data-ingestion\defaults.yaml` fixed** — the
`required_column` field went from being hardcoded (`"text"`) to using
the `${VAR:-default}` placeholder pattern ADR-006 requires
(`${SIGMA_INGESTION_REQUIRED_COLUMN:-text}`), allowing the pipeline to
adapt to datasets with different column names without modifying code.
`skill.py` now renames the configured column to `"text"` immediately
after schema validation, so the rest of the code (including the write
to `raw_data` in PostgreSQL) needs no further changes.

**New structure inside `outputs\`.** Added `output_report.md` (results
report for the 3 cross-domain tests with their 6 HTML dashboards) and
the `dashboards\{trace_id}\` subfolder, auto-generated only in Dev
mode — in Full mode, dashboards are persisted exclusively to MinIO and
downloaded manually when a local copy is needed. The duplicate
`test_dashboard_fix.html` inside `outputs\` was removed — its only
correct location is alongside its script in `tests\`.

**New `scripts\resume_hitl_manual.py`** — utility to manually resume a
run paused in HITL when the Zulip bot is deactivated, without relying
on `webhook_receiver.py`. Documented in `TROUBLESHOOTING.md`. This file
previously lived at the root as `test_checkpointer.py` — it was renamed
and relocated because its original name matched the `test_*.py` pattern
`pyproject.toml` uses for automatic test discovery, even though it
isn't a real test.

**All 16 ADRs now have their complete `.en.md` translation** — including
`adr-README-v1.5.en.md`, the full index.

> ⚠️ **Pending verification note:** a duplicate
> `sigma\sigma_checkpoints.sqlite` file was found inside the `sigma\`
> package, distinct from the one at the project root (its correct
> location). It was likely generated by running a script from inside
> that folder by mistake. Pending confirmation via `fc` on whether they
> are identical before removing the duplicate.

---

## Operations sequence — first manual run

```bash
# 1. Create the database (one time only)
createdb -U postgres sigma
psql -U postgres -d sigma -f db/init_schema.sql

# 2. Configure environment variables (one time only)
cp .env.example .env

# 3. Download the RoBERTa model (one time only, ~500 MB)
python scripts/download_model.py

# 4. Place the Tirendaz dataset at data/tirendaz.csv

# 5. Bring up infrastructure
docker compose up -d

# 6. Run in Dev mode first (no real infrastructure)
python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv

# 7. Run in Full mode (full real pipeline)
python orchestrator.py --variant Full --data-path ./data/tirendaz.csv

# 8. To use your own dataset with a column name other than "text":
set SIGMA_INGESTION_REQUIRED_COLUMN=your_real_column_name
python orchestrator.py --variant Full --data-path ./data/your_dataset.csv

# 9. If the Zulip bot is deactivated and the pipeline is paused in HITL:
python scripts/resume_hitl_manual.py
```

> **Note:** step 7 uses the real variant scheme `orchestrator.py`
> accepts today (`--variant Full`), not the documented target scheme
> (`SIGMA-FE` + `--submode`) — that code-level migration was
> deliberately postponed to Milestone 2.

---

## What's NOT in this structure (outside Milestone 1)

| Folder/file | Milestone | Reason |
|---|---|---|
| `sigma\skills\0005` through `0007`, `0009`, `0010`, `0012`-`0015` | Milestone 2 | Three-orchestrator architecture |
| `sigma\skills\0016`-`0019` | Milestone 3 | Streaming — only `0016` is specified first |
| `sigma\hooks\deploy_to_netlify.py` | Milestone 2+ | Not needed in Milestone 1 |
| VPS / `hardening_inicial_vps.sh` | Milestone 2 | Lives outside this repo |
