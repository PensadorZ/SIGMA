---
id: ADR-009
title: Skill Specification with Gherkin, LTL, and Granular Structure
version: 1.8
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-009 v1.7
minimum-references: ADR-002, ADR-006, ADR-011, ADR-014, ADR-016, ADR-017
approved-by: Prof. Marx A. García Delgado
---

# ADR-009: Skill Specification with Gherkin, LTL, and Granular Structure

## Executive summary of v1.8 changes

Two real corrections, verified against the project's current state
(Milestone 2, Rollout 1 close): (1) Tab. 5 still said "Orchestrator in
Architect mode" as the author of dynamically generated skills —
terminology predating the Director/Engineer/Auditor hierarchy, already
reconciled in `ADR-014` v1.2 but never propagated here; (2) Tab. 2b
incorrectly grouped `0004` within Milestone 1's original close (55
tests), when it was actually built during Milestone 2 Rollout 1 — the
65/65 count only exists after that addition. `ADR-014`, `ADR-016`, and
`ADR-017` are added to the minimum references, directly cited in the
body but missing from the list.

## Executive summary of v1.7 changes

The Context section is expanded to first explain that this ADR is the
contract ADR-002 (`parallelism` field), ADR-006 (placeholders resolved
inside `skill.py`), and ADR-011 (the per-skill span) depend on — before
getting into the detail of the seven canonical artifacts.

## Executive summary of v1.6 changes

The engineering justification for the `tests/` folder is added as a
functional decision — not merely a structural one: skills are tested
and iteratively improved, and `tests/` is the support for that cycle.
The **root-level modules of `skills/`** (`__init__.py`, `_loader.py`,
`_common.py`) are documented, verified against `sigma-hito1`'s real
structure, which allow invoking any skill as a Python module from
outside its execution context (other services, other agents, the
Orchestrator itself). No change breaks compatibility with existing
skills.

---

## Context

ADR-009 is the contract that gives physical shape to every SIGMA
skill: it is the answer to what must exist on disk for a skill to be
valid, runnable, and verifiable. Other ADRs assume this structure
already exists without redefining it — ADR-002's `parallelism` field is
declared in the frontmatter this ADR specifies, ADR-006's `${VAR}` is
resolved inside the `skill.py` this ADR locates, and ADR-011's
`skill.{skill_id}` span traces precisely the unit this ADR delimits.
Without this common specification, every skill could be organized
differently and none of those other mechanisms would have a stable
foundation to operate on.

A skill must communicate what it does, when it can run, what it
guarantees, and how it is traced. A `SKILL.md` with only prose is not
enough because it is ambiguous and cannot feed integration tests.
Furthermore, more complex skills need a predictable internal
organization for their assets, evaluations, helper scripts, and
references. This organization must be clearly distinguished from the
ecosystem's global folders to avoid operational and maintenance
confusion.

Two additional needs, verified in Milestone 1's practice, were not
formally justified in earlier versions of this ADR:

- **Why `tests/` is mandatory and not just a style convention.** A
  skill is not an artifact written once and left fixed: it is refined,
  fixed, and improved throughout its life (see ADR-012). Without a
  tests folder accompanying the skill, every improvement risks breaking
  already-validated behavior without anyone noticing until production.
- **How a skill is invoked by *something that is not its own
  Milestone's Orchestrator*.** An external dashboard, a second
  orchestrator (ADR-016), or a third-party service may need to run a
  skill's logic without going through the full DAG. Without a standard
  import mechanism, every external consumer reinvents its own wrapper.

---

## Decision

### Fig. 1 — A skill's file structure: the seven canonical artifacts

```
skills/
├── __init__.py                   ← Root module (see Fig. 2)
├── _loader.py                    ← Dynamic skill loader (see Fig. 2)
├── _common.py                    ← Shared utilities (see Fig. 2)
│
└── 0001-data-ingestion/          ← Skill folder (00xx-name format)
    │
    │  ═══ SEVEN MANDATORY ARTIFACTS (v1.5) ═══
    ├── SKILL.md                  ← 1. Full specification (≤ 500 lines)
    ├── skill.py                  ← 2. Python implementation
    ├── defaults.yaml             ← 3. Non-sensitive default values
    ├── tests/
    │   ├── test_skill.feature    ← 4. Gherkin scenarios
    │   └── test_skill.py         ← 5. Runnable steps (pytest-bdd)
    ├── references/
    │   └── schemas.md            ← 6. Pydantic output contract (D2, ADR-007)
    ├── evals/
    │   └── eval_adherencia.yaml  ← 7. Adherence evaluation (D6, ADR-013)
    │
    │  ═══ OPTIONAL for complex skills ═══
    ├── tests/conftest.py         ← Skill-specific fixtures if needed
    ├── assets/                   ← Skill assets
    └── scripts/                  ← Skill helper utilities
```

Real-world verification: Milestone 1's 6 skills (0000, 0001, 0002,
0003, 0008, 0011) follow this protocol with 65/65 tests passing. The
protocol is not theoretical: it is validated against real, runnable
code, including `0000-system-health-check`'s confirmed structure with
its eight entries (seven artifacts + a runtime-generated `__pycache__`,
which is not versioned).

### Engineering justification for `tests/` (not just a convention)

`tests/` is not a folder that exists for documentary tidiness. It is
the answer to a concrete engineering problem: **skills change, and
every change can break something that already worked.**

- A skill is defined once in `SKILL.md` but is **fixed and improved
  many times** in `skill.py` throughout its lifecycle (bugs found in
  production, new input data formats, threshold adjustments).
  `tests/test_skill.feature` freezes the expected behavior;
  `tests/test_skill.py` verifies it automatically and repeatably on
  every change.
- Without this folder, the only way to know whether a change broke
  something would be to manually run the full pipeline against real
  data — slow, costly, and not reproducible in CI.
- The mandatory nature of `tests/` is what makes ADR-012's Dev →
  Staging → Production promotion cycle possible: without tests that can
  be run automatically, there is no objective criterion for deciding
  whether a skill is ready to advance environments.

In short: `tests/` is an **engineering decision about how a skill's
quality is sustained over time**, not a folder-organization preference.

### Fig. 2 — Root-level modules of `skills/`: skills as Python modules

Besides each skill's internal structure, the `skills/` folder has three
files of its own at its root, verified against `sigma-hito1`'s real
structure:

```
skills/
├── __init__.py     ← Turns skills/ into an importable Python package
├── _loader.py      ← Discovers and dynamically loads skills by their ID (00xx)
├── _common.py      ← Utilities shared across skills (not specific
│                      to any individual skill)
├── 0000-system-health-check/
├── 0001-data-ingestion/
└── ...
```

**Purpose of each file:**

| File | Role |
|---|---|
| `__init__.py` | Declares `skills/` as a Python package. Without this file, no external consumer can do `import skills` or `from skills import ...` |
| `_loader.py` | Dynamic loader: given a skill ID (`"0008"`), locates the `00xx-name/` folder, imports its `skill.py`, and exposes its entry function without the consumer needing to know the physical path or full folder name |
| `_common.py` | Utilities genuinely shared across skills (e.g. structured-logging helpers, `get_required_env()` wrappers from ADR-010) that don't belong to any particular skill's business logic |

**Why this is necessary — the problem it solves:**

A skill was originally designed to run as a node of a LangGraph DAG
within *its own* Milestone. But in practice, other consumers need its
logic without going through that full DAG:

- A second orchestrator in the Director/Engineer hierarchy (ADR-016)
  may need to invoke another Engineer's skill under the Director's
  authorization, without instantiating that Engineer's full subgraph.
- A Milestone 3 reactive dashboard (ADR-015) may need to run
  `0008-sentiment-analyzer`'s classification logic on a single isolated
  message, outside any batch pipeline.
- An external service or a maintenance script may need to run
  `0004-statistical-validator` on an ad-hoc dataset without mounting
  the full Orchestrator.

Without `__init__.py` + `_loader.py`, each of these consumers would
have to reinvent its own way of locating and importing the skill —
duplicating logic and risking breaking the encapsulation ADR-002 and
ADR-008 require. With this mechanism, any authorized consumer does:

```python
from skills._loader import load_skill

sentiment = load_skill("0008")
result = sentiment.run(isolated_text, context=override_state)
```

**Usage rules for this mechanism:**

1. `_loader.py` **does not**, by itself, grant authorization to run a
   skill outside its Milestone — authorization still goes through the
   Policy Server (ADR-005) and, if the impact level requires it, the
   Vibe Diff (ADR-004). The loader is a technical access mechanism, not
   a governance bypass.
2. `_common.py` only contains utilities **with no business state**.
   Domain-specific logic (sentiment, drift, etc.) lives inside the
   corresponding skill, never in `_common.py`.
3. These three files are a transversal responsibility of the skill
   catalog, not of any individual skill: they are versioned alongside
   `AGENTS_CREATOR.md`, not with a particular skill's SemVer cycle.

### Tab. 1 — The four mandatory sections of SKILL.md

| Section | Content | Purpose |
|---|---|---|
| **YAML frontmatter** | id, version, description, domain, model, input/output patterns, parallelism, output_schema, expected_trajectory, sigma_variants, ADR references | Automatically processed by the Orchestrator |
| **Gherkin scenarios** | At least one positive and one negative case | Runnable with `pytest-bdd`; readable by stakeholders |
| **LTL properties** | At least one safety property and one liveness property | Verified at design, CI, and runtime by the Blue Team (ADR-003) |
| **Traceability specification** | Exact events the skill will emit to Langfuse with minimum payload | Uniformity in ecosystem observability |

### Tab. 2 — Skill subfolders: mandatory and optional

| Folder | Status | Purpose | Minimum content |
|---|---|---|---|
| `tests/` | **Mandatory** | Sustains the skill's test-and-improve cycle (see engineering justification above) | `test_skill.feature` + `test_skill.py` |
| `references/` | **Mandatory** | Data contract | `schemas.md` (Pydantic output) |
| `evals/` | **Mandatory** | Adherence evaluation | `eval_adherencia.yaml` |
| `assets/` | Optional | Visual assets, test data | `sample_data.parquet`, `custom_theme.yaml` |
| `scripts/` | Optional | Skill helper utilities | `migrate_schema.py`, `pre_clean.sh` |

### Tab. 2b — Official skill catalog by Milestone (0000–0019)

**Corrected:** the previous version grouped `0004` inside "Milestone 1,
65/65 tests" — but `0004-statistical-validator` was built during
Milestone 2 Rollout 1, not in Milestone 1's original close (which
closed with 6 skills and 55 tests). The 65/65 count only exists
*after* Milestone 2's Rollout 1 added `0004`. It is correctly split
below, and Milestone 2's Rollouts are broken out per `ADR-016` instead
of a flat "Specification" block.

| Range | Skills | Milestone / Rollout | Status |
|---|---|---|---|
| 0000–0003, 0008, 0011 | Batch pipeline core + sentiment + viz | Milestone 1 (original close) | ✅ Implemented (55/55 tests at close) |
| 0004 | Statistical validation (Engineer Data) | Milestone 2, Rollout 1 | ✅ Implemented — combined suite 65/65 (with Milestone 1's 6) |
| 0005–0007, 0009–0010 | ML/DL trainers, clustering, engagement (Engineer Models) | Milestone 2, Rollout 2 | Specification — no code yet |
| 0012–0015 | HITL, explainability, code-reviewer, skill-discovery (Engineer Auditor) | Milestone 2, Rollout 3 | Specification — gated by `ADR-017` (sandboxing) |
| 0016–0019 | Hamilton Selector streaming + RT skills (ADR-015) | Milestone 3 | Reserved |

Skills 0016–0019 include future lines for banking analytics,
video/image analysis, and authorized security testing, with the
non-negotiable limit that unauthorized scanning of third-party systems
is out of the ecosystem's scope, regardless of intent.

### Tab. 3 — Differentiation between global and local folders

| Purpose | Global folder (repository root) | Local folder (inside each skill) |
|---|---|---|
| Cross-cutting evaluations for all of SIGMA | `evals_SIGMA/` | `skills/00xx-name/evals/` |
| Cross-cutting hooks and scripts | `hooks_SIGMA/` | `skills/00xx-name/scripts/` |
| Shared global assets | `assets_SIGMA/` | `skills/00xx-name/assets/` |
| Global references | `references_SIGMA/` | `skills/00xx-name/references/` |
| **Catalog modules (new in v1.6)** | `skills/__init__.py`, `skills/_loader.py`, `skills/_common.py` | *(not applicable — cross-cutting by definition)* |

This convention guarantees a developer can immediately identify whether
a resource belongs to the whole ecosystem or to a particular skill, and
prevents name collisions between skills that define their own
evaluations or scripts.

### Tab. 4 — Skill naming and numbering convention

| Element | Format | Example |
|---|---|---|
| Skill folder | `00xx-skill-name` | `0001-data-ingestion`, `0012-code-reviewer` |
| Specification file | `SKILL.md` | `skills/0001-data-ingestion/SKILL.md` |
| Implementation file | `skill.py` | `skills/0001-data-ingestion/skill.py` |
| Default values | `defaults.yaml` | `skills/0001-data-ingestion/defaults.yaml` |
| Tests folder | `tests/` | `skills/0001-data-ingestion/tests/` |

Numbering follows a zero-padded four-digit format, assigned
sequentially when added to the official catalog. It is stable
throughout the skill's life and **is never reassigned** even if the
skill is deprecated.

### Tab. 5 — Authorship mark for dynamically generated skills

| Skill type | Version format | Example |
|---|---|---|
| Manually designed | Standard SemVer `MAJOR.MINOR.PATCH` | `1.2.0` |
| AI-generated (Director authorizes, domain Engineer generates) | `gia_` + SemVer | `gia_0.1.0` |

The `gia_` prefix stands for **Generated by Artificial Intelligence**
(*Generado por Inteligencia Artificial*). Skills bearing this mark were
produced by the corresponding domain Engineer (Data/Models/Auditor),
under the Director's authorization, following the dynamic generation
flow `ADR-014` v1.2 defines — **corrected**: the previous version of
this document said "Orchestrator in Architect mode," terminology
predating the real Director/Engineer/Auditor hierarchy from `ADR-016`,
already reconciled in `ADR-014` but left unupdated here. The mark is
permanent throughout the generated skill's life. If an AI-generated
skill is completely redesigned by a human, it is considered a new skill
with independent numbering and versioning.

The rule requiring at least three references to prior ADRs also applies
to `SKILL.md`'s frontmatter.

---

## Positive consequences

- Gherkin scenarios are directly runnable as integration tests.
- LTL properties make the skill's guarantees explicit.
- The granular structure makes it easy to organize complex skills
  without forcing simple ones to adopt it.
- The justified mandatory nature of `tests/` sustains ADR-012's
  promotion cycle with an objective, automatable criterion.
- The root modules (`__init__.py`, `_loader.py`, `_common.py`) allow
  any skill to be invoked as a Python module from outside its
  Milestone, without duplicating import logic in every external
  consumer.
- The global-vs-local differentiation removes ambiguity about which
  evaluations and scripts belong where.
- The `gia_` mark identifies a skill's origin for security audits and
  quality reviews.
- Sequential four-digit numbering enables unambiguous references in
  pipelines and configurations.

## Negative consequences

- Writing a complete `SKILL.md` takes more time than an
  implementation with no specification.
- LTL properties require knowledge of temporal logic.
- The granular structure can produce asset duplication if several
  skills share resources; mitigated with the global `assets_SIGMA/`
  folder.
- Numbering requires maintaining a centralized registry to avoid
  collisions.
- `_loader.py` is a single cross-cutting point of access: a bug in its
  discovery logic affects every skill simultaneously. Mitigated by the
  test coverage ADR-012 requires before promoting any change to
  `_loader.py` or `_common.py`.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Prose-only description | Ambiguous; doesn't automatically generate tests |
| OpenAPI or JSON Schema only | Suitable for HTTP APIs; doesn't capture temporal properties |
| A single mandatory structure for all | Overburdens simple skills with no benefit |
| No root modules — every external consumer imports the skill by hand | Duplicates location/import logic in every consumer; risks breaking the encapsulation ADR-002/ADR-008 require by exposing internal paths |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Confirmed the integration of the `parallelism` field with
  ADR-002's `chain` strategy.
- **b.1.2** Added the explicit mention that LTL properties are verified
  in real time by ADR-003's Blue Team.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with a skill's full file structure.
- **b.1.3** Added Tab. 1 with `SKILL.md`'s four mandatory sections.

**Changes in v1.4:**
- **a.1.4** Updated Fig. 1 to reflect the optional granular structure
  with `assets/`, `evals/`, `scripts/`, and `references/` subfolders.
- **b.1.4** Added Tab. 2 with a description of each optional subfolder.
- **c.1.4** Added Tab. 3 with the differentiation between `_SIGMA`
  -suffixed global folders and each skill's local folders.
- **d.1.4** Added Tab. 4 with four-digit numbering.
- **e.1.4** Added Tab. 5 with the `gia_` mark in coordination with
  ADR-014.
- **f.1.4** Clarified the granular structure's backward compatibility.
- **g.1.4** Framed the relationship with ADR-014 as an informational
  note to avoid circular dependency.

**Changes in v1.5:**
- **a.1.5** The packaging protocol was raised to seven mandatory
  canonical artifacts: `references/schemas.md` and
  `evals/eval_adherencia.yaml` move from optional to mandatory, and
  `tests/test_skill.py` is required alongside the `.feature`. Verified
  against Milestone 1's 6 skills with 65/65 tests.
- **b.1.5** Added the recommended 500-line limit per `SKILL.md`.
- **c.1.5** Added Tab. 2b with the official catalog of 20 skills
  (0000–0019) organized across 3 Milestones, including the reserved
  0016–0019 range and its non-negotiable ethical limit.
- **d.1.5** Fig. 1 was updated to distinguish the seven mandatory
  artifacts from the remaining optional subfolders.

**Changes in v1.6:**
- **a** Added the engineering justification for `tests/` as a
  functional decision sustaining the skill's continuous test-and-improve
  cycle, not a style convention.
- **b** Documented `skills/`'s root-level modules (`__init__.py`,
  `_loader.py`, `_common.py`), verified against `sigma-hito1`'s real
  structure, with Fig. 2, their purpose, the problem they solve, and
  usage rules (no bypassing the Policy Server or the Vibe Diff).
- **c** Updated Fig. 1 to show the root modules alongside each
  individual skill's folder.
- **d** Added a row in Tab. 3 for the catalog modules as a
  cross-cutting resource by definition.
- **e** Added a negative consequence about the single-point-of-access
  risk in `_loader.py`, with its mitigation via ADR-012.

**Changes in v1.8 (Milestone 2, Rollout 1 close):**
- **a** Tab. 5 corrected: "Orchestrator in Architect mode" → the
  Director authorizes, the corresponding domain Engineer generates —
  consistent with the reconciliation already applied in ADR-014 v1.2.
- **b** Tab. 2b corrected: `0004` separated from Milestone 1's original
  close (55 tests) — it was built in Milestone 2 Rollout 1. Milestone
  2's Rollouts 2 and 3 broken out per ADR-016 instead of a flat block.
- **c** Added ADR-014, ADR-016, ADR-017 to minimum references.
