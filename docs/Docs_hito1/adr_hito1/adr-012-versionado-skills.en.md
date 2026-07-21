---
id: ADR-012
title: Skill Version Management and Promotion
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-012 v1.3
minimum-references: ADR-009, ADR-010, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-012: Skill Version Management and Promotion

## Executive summary of changes in v1.4

The Context section is expanded to first explain that this ADR is the
operational process that gives real consequence to ADR-009's `tests/`
mandate, using ADR-011's Langfuse metrics as the promotion criterion —
before descending into the detail of the Dev → Staging → Production cycle.

## Executive summary of changes in v1.3

Added Fig. 1 with the promotion flow between environments. Added Table 1
with the SemVer meaning for each type of versioned artifact.
Incorporated the version history.

---

## Context

ADR-012 is the mechanism that turns ADR-009's mandate into an actual
operational process: `tests/` being mandatory for every skill only has
real meaning if a formal cycle exists that decides, based on those tests
and on Langfuse's metrics (ADR-011), whether a skill is ready to move
from Dev to Staging and finally to Production. Without this ADR, the
`tests/` mandate would be a requirement with no practical consequence —
tests would get written, but nothing would dictate when a skill can be
trusted to production, or how to roll back if something goes wrong.

Skills evolve. Without a formal versioning protocol, silent regressions
occur when an update breaks production pipelines, and rollback is
impossible when there's no structured prior version.

---

## Decision

Skills follow **Semantic Versioning (SemVer)**:
- **MAJOR:** a change that breaks schema compatibility.
- **MINOR:** new backward-compatible functionality.
- **PATCH:** bug fix with no behavior change.

### Fig. 1 — A skill's promotion flow across environments

```
Branch feature/skill-{name}-v{version}
        │
        ▼
DEV ENVIRONMENT
  ├─ Unit tests (pytest)
  ├─ Behavior tests (pytest-bdd, Gherkin scenarios)
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
  Non-regression check against existing pipelines
        │
        ▼
Version pinned in production (e.g. sentiment-analyzer:1.2.0)
```

### Table 1 — SemVer meaning by type of versioned artifact

| Artifact | MAJOR | MINOR | PATCH |
|---|---|---|---|
| **Skills** (`SKILL.md` + `skill.py`) | Input or output schema changes and breaks consumers | New backward-compatible functionality | Bug fix with no behavior impact |
| **`policies.yaml`** | A tool currently in use is restricted | Only additions to the allowlist | Detection regex fix |
| **`allowed_packages.yaml`** | A package currently in use is removed | A new package is added | Hash update for an existing package |
| **Pipeline YAMLs** | Change in pinned versions that affects behavior | Addition of optional steps | Typo or metadata fix |

### Extending the scope of versioning

`policies.yaml` and `allowed_packages.yaml` also follow SemVer under the
same promotion cycle as skills. The Dev → Staging → Production cycle
applies to these artifacts the same way it applies to skills.

### Pinned versions in pipelines

Pipeline YAML files must reference explicit versions of the skills they
use. A pipeline that references a skill with no explicit version is
invalid, and the Orchestrator rejects it at load time with an
`UNPINNED_SKILL_VERSION` error.

---

## Positive consequences

- The promotion process guarantees only validated skills reach production.
- Pipelines with pinned versions are reproducible regardless of the
  versions available on the system.
- Coexistence of up to 3 versions allows A/B comparisons in staging.

## Negative consequences

- The promotion process adds formal steps to the development cycle.
- Maintaining up to 3 simultaneous versions increases management
  overhead for small teams.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Git-branch versions without SemVer | Makes it hard to know which version is in production |
| Direct deployment with no staging | No safety net; regressions reach production |
| Numeric versions without SemVer | Don't communicate the change's impact to consumers |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Extended SemVer versioning's scope to `policies.yaml` and
  `allowed_packages.yaml` under the same promotion cycle as skills.
- **b.1.2** Added that pipelines must reference pinned skill versions, or
  be rejected by the Orchestrator.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the promotion flow across environments and
  the test datasets at each stage.
- **b.1.3** Added Table 1 with the meaning of each SemVer level for each
  type of versioned artifact.

**Changes in v1.4:**
- **a** Expanded Context to explain that this ADR is the operational
  process giving real consequence to ADR-009's `tests/` mandate, using
  ADR-011's Langfuse metrics as the promotion criterion, before
  descending into the detail of the Dev → Staging → Production cycle.
