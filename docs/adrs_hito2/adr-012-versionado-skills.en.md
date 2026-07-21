---
id: ADR-012
title: Skill Version Management and Promotion
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-012 v1.4
minimum-references: ADR-009, ADR-010, ADR-011, ADR-014
approved-by: Prof. Marx A. García Delgado
---

# ADR-012: Skill Version Management and Promotion

## Executive summary of v1.5 changes

Added `ADR-014` to the minimum references — its Step 7 ("Versioning and
promotion") explicitly depends on the Dev → Staging → Production cycle
this document defines, with that relationship never formally declared
here. No other changes: the rest of the document was already free of
outdated variant schemes and worker terminology, verified against the
project's real state in this session.

## Executive summary of v1.4 changes

The Context section is expanded to first explain that this ADR is the
operational process that gives real consequence to ADR-009's `tests/`
requirement, using ADR-011's Langfuse metrics as the promotion
criterion — before getting into the detail of the Dev → Staging →
Production cycle.

## Executive summary of v1.3 changes

Fig. 1 is added with the promotion flow between environments. Tab. 1 is
added with the SemVer meaning for each versioned artifact type.
Version history is incorporated.

---

## Context

ADR-012 is the mechanism that turns what ADR-009 requires as mandatory
into an operational process: the existence of `tests/` in every skill
only makes real sense if there is a formal cycle that decides, based on
those tests and on Langfuse's metrics (ADR-011), whether a skill is
ready to advance from Dev to Staging and finally to Production. Without
this ADR, `tests/`'s mandatory nature would be a requirement with no
practical consequence — tests would get written, but nothing would
dictate when a skill can be trusted to production or how to roll back
if something goes wrong.

Skills evolve. Without a formal versioning protocol, silent regressions
occur when an update breaks production pipelines, and rollback is
impossible when there is no structured previous version.

---

## Decision

Skills follow **Semantic Versioning (SemVer)**:
- **MAJOR:** a change that breaks schema compatibility.
- **MINOR:** new, backward-compatible functionality.
- **PATCH:** bug fix with no behavior change.

### Fig. 1 — A skill's promotion flow between environments

```
Branch feature/skill-{name}-v{version}
        │
        ▼
DEV ENVIRONMENT
  ├─ Unit tests (pytest)
  ├─ Behavioral tests (pytest-bdd, Gherkin scenarios)
  └─ Static verification of LTL properties
        │ Do all tests pass?
        ▼
STAGING ENVIRONMENT
  Real test data (e.g. Tirendaz, 22.5K records)
  Metrics measured in Langfuse:
  ├─ d2_functional_score >= 1.0
  └─ d6_trajectory_adherence >= 0.9
        │ Do metrics clear the thresholds?
        ▼
PRODUCTION ENVIRONMENT
  Operator's final approval (Approval Endpoint, ADR-004)
  Non-regression verification against existing pipelines
        │
        ▼
Version pinned in production (e.g. sentiment-analyzer:1.2.0)
```

### Tab. 1 — SemVer meaning by versioned-artifact type

| Artifact | MAJOR | MINOR | PATCH |
|---|---|---|---|
| **Skills** (`SKILL.md` + `skill.py`) | Input or output schema changes and breaks consumers | New, compatible functionality | Bug fix with no behavior impact |
| **`policies.yaml`** | A tool currently in use is restricted | Only added to the allowlist | Detection-regex fix |
| **`allowed_packages.yaml`** | A package currently in use is removed | A new package is added | Update to an existing package's hash |
| **Pipeline YAML files** | Change in pinned versions that affects behavior | Addition of optional steps | Typo or metadata fix |

### Extending the versioning scope

`policies.yaml` and `allowed_packages.yaml` also follow SemVer under the
same promotion cycle as skills. The Dev → Staging → Production cycle
applies to these artifacts just as it does to skills.

### Pinned versions in pipelines

Pipeline YAML files must reference explicit versions of the skills they
use. A pipeline that references a skill with no explicit version is
invalid, and the Orchestrator rejects it at load time with an
`UNPINNED_SKILL_VERSION` error.

---

## Positive consequences

- The promotion process guarantees only validated skills reach
  production.
- Pipelines with pinned versions are reproducible regardless of which
  versions are available on the system.
- Coexistence of up to 3 versions allows A/B comparisons in staging.

## Negative consequences

- The promotion process adds formal steps to the development cycle.
- Keeping up to 3 simultaneous versions increases management overhead
  for small teams.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Versions in Git branches with no SemVer | Makes it hard to know which version is in production |
| Direct deployment with no staging | No safety net; regressions reach production |
| Numeric versions with no SemVer | Don't communicate a change's impact to consumers |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Extended SemVer versioning scope to `policies.yaml` and
  `allowed_packages.yaml` with the same promotion cycle as skills.
- **b.1.2** Added that pipelines must reference pinned skill versions,
  on pain of rejection by the Orchestrator.

**Changes in v1.3:**
- **a** Added Fig. 1 with the promotion flow between environments and
  the test datasets at each stage.
- **b** Added Tab. 1 with the meaning of each SemVer level for each
  versioned-artifact type.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** Added ADR-014 to minimum references — its promotion cycle for
  dynamically generated skills directly depends on this ADR.
