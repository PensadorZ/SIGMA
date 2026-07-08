# Project Folder Structure — SIGMA Milestone 1

**SIGMA v1.7 · Post-restructuring into the `sigma/` package**
Author: Prof. Marx Agustín García Delgado · Version: 3.0.0
Replaces version 2.0.0 — updated after the full restructuring of the
code into the `sigma/` package (`sigma/core/`, `sigma/hooks/`,
`sigma/skills/`), the recovery of `config.py`/`connections.py`/
`tracing.py` inside `sigma/core/`, and the formal close of Milestone 1
(65/65 tests).

---

## Full tree

```
sigma-hito1\
│
├── .env.example                  ← Public variable template (goes to Git)
├── .env                          ← Real credentials (NEVER to Git)
├── .gitignore
├── LICENSE
├── README.md
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
├── Learning\                     ← Operator's personal learning scripts
│   └── *.py                        (NEVER to Git, whole folder in .gitignore)
│
├── sigma\                        ← Installable Python package — all importable code lives here
│   ├── __init__.py
│   │
│   ├── core\
│   │   ├── __init__.py
│   │   ├── config.py             ← Environment variables, get_sigma_variant(), get_sigma_submode()
│   │   ├── connections.py        ← check_postgresql/redis/minio/langfuse/ollama (ADR-011)
│   │   ├── tracing.py            ← emit_trace_event(), Langfuse→Redis→local-log degradation
│   │   ├── checkpointer.py       ← mark_waiting/get_waiting_trace_id/clear_waiting (HITL)
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
│       │                            (solves the invalid-Python-identifier
│       │                            problem in hyphenated folders — see ADR-009)
│       │
│       ├── 0000-system-health-check\
│       │   ├── SKILL.md          ← v2.0.0 — HEALTHY/DEGRADED/BLOCKED verdict
│       │   ├── defaults.yaml     ← timeout, critical/optional classification
│       │   ├── skill.py          ← real check of 5 services
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_system_health_check.feature
│       │       ├── test_0000_system_health_check.py
│       │       └── test_system_health_check_stress.py   ← 15 resilience tests
│       │
│       ├── 0001-data-ingestion\
│       │   ├── SKILL.md          ← v2.0.0 — SHA-256 checksum, chunks, run_id
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_ingestion.feature
│       │       └── test_0001_data_ingestion.py
│       │
│       ├── 0002-data-cleanser\
│       │   ├── SKILL.md          ← v2.0.0 — O(n) dedup, cleaned_rejected
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_cleanser.feature
│       │       └── test_0002_data_cleanser.py
│       │
│       ├── 0003-data-preprocessor\
│       │   ├── SKILL.md          ← v2.0.0 — leakage, conditional SMOTE/PCA
│       │   ├── defaults.yaml     ← apply_smote/apply_pca/apply_class_weight flags
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_data_preprocessor.feature
│       │       └── test_0003_data_preprocessor.py
│       │
│       ├── 0008-sentiment-analyzer\
│       │   ├── SKILL.md          ← v1.1.0 — run_id, model_name un-hardcoded
│       │   ├── defaults.yaml
│       │   ├── skill.py
│       │   ├── references\schemas.md
│       │   ├── evals\eval_adherencia.yaml
│       │   └── tests\
│       │       ├── test_skill.feature
│       │       └── test_0008_sentiment_analyzer.py
│       │
│       └── 0011-viz-reporter\
│           ├── SKILL.md          ← v1.1.0 — run_id added
│           ├── defaults.yaml
│           ├── skill.py
│           ├── references\schemas.md
│           ├── evals\eval_adherencia.yaml
│           └── tests\
│               ├── test_skill.feature
│               └── test_0011_viz_reporter.py
│
├── db\
│   └── init_schema.sql           ← DDL for 7 tables (includes cleaned_rejected)
│
├── data\
│   ├── .gitkeep                  ← tirendaz.csv goes here, never to Git
│   └── raw\                      ← Original raw dataset, never to Git
│       ├── Tweets.csv
│       └── twitter-tweets-sentiment-dataset.zip
│
├── models\
│   └── roberta-sentiment-correcto\   ← Real RoBERTa model (~500 MB), never to Git
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── tokenizer_config.json
│
├── outputs\
│   └── .gitkeep                  ← HTML dashboards generated in Dev mode
│
├── logs\
│   └── .gitkeep
│
├── tests\                        ← Shared infrastructure and one-off checks
│   ├── test_common_connections_stress.py    ← 11 tests for _common.py
│   ├── test_dashboard_fix.py                ← One-off verification of the 0011 fix
│   ├── test_dashboard_fix.html
│   ├── test_langfuse_connection.py          ← Langfuse connectivity check
│   └── hist_diagnoses_tests_202607\         ← Archived real-incident diagnostics
│       └── [tests for already-resolved incidents, not run — see TROUBLESHOOTING.md]
│
├── docs\
│   ├── AGENTS_CREATOR.md         ← Global agent contract (v1.1.0)
│   ├── ESTRUCTURA_PROYECTO.md    ← This document
│   ├── SIGMA_v1.7.md             ← Current Master Plan
│   ├── TROUBLESHOOTING.md        ← 5 real incidents with full diagnosis
│   ├── adr\
│   │   ├── adr-001-memoria-epistemica.md … adr-016-orquestacion-jerarquica.md
│   │   └── adr-README-v1.5.md    ← Index of the 16 ADRs
│   ├── docs_hist\                ← Archived document versions (never overwrite)
│   │   ├── SIGMA_v1.5.md
│   │   ├── SIGMA_v1.6.md
│   │   ├── Estructura_Proyecto_v1.md
│   │   └── Roadmap_Tecnico_v1.md
│   └── reportes\                 ← Internal process audits (not translated to English)
│       ├── fusion_0001_0002_v2.0.0.md
│       └── verificacion_artefactos_hito1.md
│
└── scripts\
    ├── download_model.py
    └── old_scripts_sigma\        ← "DO NOT TOUCH" — preserved historical versions
        ├── oldscript_README.md
        ├── init_schema_v2.sql
        ├── old_core\             ← old config.py/connections.py/tracing.py (already recovered into sigma/core/)
        ├── old_hooks\
        ├── old_main\             ← conftest_v1-4, orchestrator_v1-7, pyproject_v2-3
        └── old_skills\           ← v1-v5 versions of each skill, replaced
```

---

## Changes from version 2.0.0 of this document

**Important correction — `core\` wasn't reduced to 2 files, it was recovered to 5.**
Version 2.0.0 of this document stated that `config.py`, `connections.py`,
and `tracing.py` had been "evaluated and discarded" in favor of merging
that functionality into `skills\_common.py`. That statement turned out
to be incorrect: the three files existed in
`scripts\old_scripts_sigma\old_core\`, but **never made it into the
active folder** — an `__init__.py` imported them
(`from sigma.core.config import ...`) without the file actually
existing. They were recovered, `config.py` was updated to the current
variant scheme (`SIGMA-FE/LE/ME/HE` + `Dev`/`Runtime` submodes), and now
all 5 files live together in `sigma\core\`.

**All code moved inside the `sigma\` package.** `core\`, `hooks\`, and
`skills\` no longer sit loose at the root — they're now subpackages of
`sigma\`, because virtually all the code already used the internal
import pattern `from sigma.core...` / `from sigma.skills...`, and the
physical structure had to match that.

**`scripts\old_scripts\` corrected to `scripts\old_scripts_sigma\`** —
the folder's real name, which didn't match the previous document.

**`tests\` (root) no longer contains only what's shared across skills.**
Added `test_dashboard_fix.py`/`.html` (a one-off check for the
`0011-viz-reporter` fix) and `test_langfuse_connection.py` (connectivity
check), plus the `hist_diagnoses_tests_202607\` folder with tests for
already-resolved and archived incidents (not run — excluded via
`pyproject.toml`).

**`docs\adr\` went from 15 to 16 ADRs**, with descriptive lowercase
filenames (`adr-016-orquestacion-jerarquica.md`, etc.) instead of the
previous document's `ADR-00X.md` format.

**Added `docs\docs_hist\`** for archived full-document versions
(`SIGMA_v1.5.md`, `SIGMA_v1.6.md`, etc.), and `docs\reportes\` for
internal process audits (`fusion_0001_0002_v2.0.0.md`,
`verificacion_artefactos_hito1.md`).

**New `Learning\` folder** — the operator's personal learning scripts,
fully ignored by Git.

**Removed from this document:** `evals\results\` and
`docs\PROMPT_CONTINUIDAD_HITO2_HITO3.md` — they don't exist in the
current real tree; likely never materialized or were referenced
prematurely in a previous version.

**`data\` and `models\` now show real content**, not just `.gitkeep` —
`data\raw\` with the raw dataset and `models\roberta-sentiment-correcto\`
with the real model files (both still excluded from Git).

---

## Operations sequence — first manual run

```bash
# 1. Create the database (one time only)
createdb -U postgres sigma
psql -U postgres -d sigma -f db/init_schema.sql

# 2. Configure environment variables (one time only)
cp .env.example .env
# Edit .env with your real values

# 3. Download the RoBERTa model (one time only, ~500 MB)
python scripts/download_model.py

# 4. Place the Tirendaz dataset at data/tirendaz.csv

# 5. Bring up infrastructure
docker compose up -d

# 6. Run in Dev mode first (no real infrastructure)
python orchestrator.py --variant SIGMA-FE --submode Dev --data-path ./data/tirendaz.csv

# 7. Run in Runtime mode (full real pipeline)
python orchestrator.py --variant SIGMA-FE --submode Runtime --data-path ./data/tirendaz.csv
```

> **Note:** steps 6 and 7 above use the target variant scheme
> (`--variant`/`--submode` separated). As of this writing, `orchestrator.py`'s
> actual CLI still uses the old scheme (`--variant {Full,Lite,Dev,Runtime}`,
> no `--submode` flag) — the code-level migration is deliberately postponed
> to Milestone 2 to avoid risking the verified 65-test suite. Until that
> migration lands, use `python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv`
> instead.

---

## What's NOT in this structure (outside Milestone 1)

| Folder/file | Milestone | Reason |
|---|---|---|
| `sigma\skills\0005` through `0007`, `0009`, `0010`, `0012`-`0015` | Milestone 2 | Three-orchestrator architecture |
| `sigma\skills\0016`-`0019` | Milestone 3 | Streaming — only `0016` is specified first |
| `sigma\hooks\deploy_to_netlify.py` | Milestone 2+ | Not needed in Milestone 1 |
| VPS / `hardening_inicial_vps.sh` | Milestone 2 | Lives outside this repo, in `Configuracion VPS Hetzner\` |
