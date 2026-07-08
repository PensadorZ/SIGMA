---
id: ADR-014
title: Dynamic Generation of New Skills on Demand
version: 1.1
status: Proposed
original-date: 2026-06
revision-date: 2026-07
supersedes: None
minimum-references: ADR-003, ADR-004, ADR-009, ADR-012
approved-by: Pending approval from Prof. Marx A. García Delgado
---

# ADR-014: Dynamic Generation of New Skills on Demand

## Executive summary of changes in v1.1

The Context section is expanded to first explain that this ADR is the
ecosystem's highest-risk scenario — the only one where the system writes
its own code — and that it introduces no new mechanisms, but instead
orchestrates the ones from ADR-003, ADR-004, ADR-005, ADR-009, and
ADR-012 together at their point of highest demand.

## Executive summary

This ADR defines the process by which the SIGMA ecosystem can
autonomously generate new skills when the existing catalog doesn't cover
a detected functional need. The Orchestrator in **Architect** mode
detects the gap and generates the new skill. The Auditor Agent acts as
**reviewer** (not author). The new skill goes through the standard
validation cycle of the Policy Server, the Green Team, the Approval
Endpoint, and versioning per ADR-012. This ADR applies to every variant
except SIGMA Dev.

---

## Context

Dynamic Skill Generation is the ecosystem's highest-risk scenario
governed by the whole system: it's the only point where the system
itself writes new code that will later run with real authority. That's
why this ADR introduces no new mechanisms — it orchestrates, at its
point of highest demand, all the ones that already exist: ADR-009's
specification, the Policy Server's validation (ADR-005), the Green
Team's tests (ADR-003), ADR-004's approval, and ADR-012's versioning. If
any of those mechanisms had a flaw, this is the place where that flaw
would have the greatest possible impact.

SIGMA's skill catalog is initially finite. In an ecosystem operating
across domains as diverse as data science, engineering, physics,
mathematics, or philosophy, uncovered functional needs will inevitably
arise. Without a formal mechanism, the system stays limited to its
initial catalog, losing its character as an autonomous, adaptable
ecosystem.

---

## Decision

### Fig. 1 — Flow for dynamically generating a new skill

```
STEP 1 — Need detection
─────────────────────────────────────
Detection sources:
  A. A user query no skill can resolve
     └─ The Orchestrator logs the failure in Langfuse
  B. A recurring failure pattern detected in Langfuse
  C. An explicit operator request via the Approval Endpoint
        │
        ▼
Orchestrator generates a creation mandate:
  {functional description, domain constraints,
   estimated impact level, ADRs governing the new skill}

STEP 2 — Generation by the Orchestrator (Architect mode)
─────────────────────────────────────
The Orchestrator generates:
  ├─ A full SKILL.md (ADR-009 format)
  │    ├─ YAML frontmatter (version: gia_0.1.0)
  │    ├─ Gherkin scenarios (≥1 positive, ≥1 negative)
  │    ├─ LTL properties (≥1 safety, ≥1 liveness)
  │    └─ Traceability specification
  └─ skill.py (initial implementation)
Temporary storage: skills/generated/{skill_id}/

STEP 3 — Review by the Auditor Agent
─────────────────────────────────────
The Auditor verifies:
  ├─ Coherence of expected_trajectory with existing skills
  ├─ Formal correctness of the LTL properties
  └─ The OutputSchema doesn't violate K⊆X (ADR-008)

STEP 4 — Validation by the Policy Server (ADR-005)
─────────────────────────────────────
  ├─ Structural layer: authorized tools, allowed dependencies
  └─ Semantic layer: PII, credentials, intent deviation

STEP 5 — Testing by the Green Team (ADR-003)
─────────────────────────────────────
  ├─ Runs the skill in an isolated environment
  ├─ Verifies the Gherkin scenarios
  ├─ Verifies the LTL properties at runtime
  └─ Static analysis with the code-reviewer skill

STEP 6 — Approval (ADR-004)
─────────────────────────────────────
  ├─ LOW impact  → Vibe Diff generated, no approval required
  └─ MEDIUM/HIGH impact → Vibe Diff + operator approval

STEP 7 — Versioning and promotion (ADR-012)
─────────────────────────────────────
  Initial version: gia_0.1.0
  Cycle: Dev → Staging → Production
  (the same criteria as any other skill)
```

### Table 1 — Roles and responsibilities in dynamic generation

| Agent | Role | Responsibility |
|---|---|---|
| **Orchestrator (Architect mode)** | Author | Detects the need, generates the mandate, drafts `SKILL.md` and `skill.py`, oversees the cycle |
| **Auditor Agent** | Reviewer | Verifies trajectory, LTL, and K⊆X coherence |
| **Policy Server** | Structural/semantic validator | Validates the generated skill's tools and dependencies |
| **Green Team** | Functional validator | Runs Gherkin/LTL tests, reviews code with `code-reviewer`, manages the Vibe Diff |
| **Blue Team** | Recorder | Updates the AgBOM when the skill is promoted to production |

### Table 2 — Behavior by cost variant

| Variant | Status | Approval level |
|---|---|---|
| **SIGMA-FE** | Active | LOW impact with no human approval; MEDIUM/HIGH with approval |
| **SIGMA-LE** | Active | Same levels as FE |
| **SIGMA-ME** | Active | Same levels as FE |
| **SIGMA-HE** | Active | Same levels as FE |

**Transversal submodes** (apply to any of the four cost variants):

| Submode | Status | Approval level |
|---|---|---|
| **Dev** | **Disabled** | Not applicable; prevents proliferation of unvalidated skills during debugging |
| **Runtime** | Active | **Any generation** requires operator approval, regardless of the level |

---

## Positive consequences

- The system can adapt to new needs with no human intervention for
  low-impact cases.
- The validation cycle guarantees generated skills meet the same
  standards as manually designed ones.
- The role separation between the Orchestrator as author and the
  Auditor as reviewer follows ADR-003's separation-of-concerns principle.
- The `gia_` mark in the version (ADR-009) permanently identifies the
  skill's origin for security audits.

## Negative consequences

- The process adds computational and time overhead before a new skill
  is available in production.
- The generated skill's quality depends on the Architect-mode
  Orchestrator's ability to correctly interpret the mandate.
- The `skills/generated/` directory requires cleanup policies for
  obsolete, unpromoted skills.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Manual generation by a developer | Introduces latency and human-resource dependency |
| Generation by the Auditor | Mixes governance responsibilities with code generation, violating ADR-003 |
| Validation by the Policy Server only | Doesn't verify functionality or code quality |
| No research repository | Prevents traceability, versioning, and rollback |

---

## Version history

This is the first record of this ADR. There are no prior versions.

**Changes in v1.1:**
- **a** Expanded Context to explain that this ADR is the ecosystem's
  highest-risk scenario — the only one where the system writes its own
  code — and that it introduces no new mechanisms, but orchestrates
  ADR-003, ADR-004, ADR-005, ADR-009, and ADR-012 together at their
  point of highest demand.
