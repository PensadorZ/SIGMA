---
id: ADR-013
title: Agent Trajectory Audit
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-013 v1.3
minimum-references: ADR-003, ADR-005, ADR-008, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-013: Agent Trajectory Audit

## Executive summary of changes in v1.4

The Context section is expanded to first explain that this ADR
implements the real measurement of D6 (ADR-007) and complements K⊆X
(ADR-008) as the other half of an agent's auditability. Fixed the broken
"ADR-00" reference for the Auditor Agent to **ADR-016**, where it's
formally defined as the third orchestrator in the Director/Engineer/Auditor
pattern.

## Executive summary of changes in v1.3

Added Fig. 1 with the diagram of the four components of the full
auditable trajectory. Added Table 1 with the adherence thresholds and
their operational consequences. Incorporated the version history.

---

## Context

Trajectory Audit is the mechanism that makes it possible to actually
measure D6 (trajectory quality) in ADR-007's Multidimensional Evaluation
— without it, that dimension would be an intention with no real
implementation. It uses Langfuse's traces (ADR-011) as its source of
truth, and its findings feed directly into the Blue Team (ADR-003) when
it detects serious deviations. Together with K⊆X (ADR-008), it's the
other half of what makes a SIGMA agent auditable: K⊆X guarantees that
what the agent claims is honest, while this ADR guarantees that the path
it took to get there is also verifiable.

An agent can produce the correct output by taking the wrong path. It can
call tools in the wrong order, access tables it shouldn't, or consume
ten times more resources and still produce a result that passes the
unit tests. The trajectory is the sequence of tools, models, and
decisions the agent used to reach the output. Auditing the trajectory,
not just the output, allows detecting unexpected behaviors, verifying
the agent operated within K⊆X's limits (ADR-008), and identifying
inefficiencies.

---

## Decision

The Auditor agent (defined in **ADR-016**) verifies the real trajectory
of every run against the expected trajectory declared in ADR-009's
`SKILL.md`, using Langfuse V2's traces (or any other traceability
service, such as...) from ADR-011 as the source of truth.

### Fig. 1 — Components of the full auditable trajectory

```
FULL TRAJECTORY OF A PIPELINE
─────────────────────────────────────────────────────────────

COMPONENT 1 — The skill's tool sequence
  read_table(tweets_cleaned)
  run_model(roberta-sentiment)
  write_table(tweets_sentiment)
  → compared against SKILL.md's expected_trajectory

COMPONENT 2 — Policy Server decisions
  tool: read_table     → ALLOWED  (structural layer, rule: allowed_tables)
  tool: write_prod     → BLOCKED  (structural layer, rule: denied_tables)
  → included in the audit report

COMPONENT 3 — Vibe Diffs generated and their outcome
  vibe_diff_id: sigma-20260601-143022  → APPROVED  (operator: marxiano)
  → included in the audit report

COMPONENT 4 — Red Team subgraph (excluded from the main score)
  red_team_probe: 3 vulnerabilities found, 0 critical
  → logged as a separate component, doesn't affect the main DAG's
  adherence_score because it uses different policies by design
```

### Main checks

The Auditor runs four checks on the real trajectory:

1. **Adherence to the expected trajectory:** comparison against
   `SKILL.md`'s `expected_trajectory`. Score from 0 to 1.
2. **Unauthorized tools:** verification against `SKILL.md`'s `allowed-tools`.
3. **K⊆X violation in the trajectory:** verification that every tool
   operated on data within X (ADR-008).
4. **Trajectory efficiency:** penalizes redundant steps.

### Table 1 — Adherence thresholds and consequences

| Score | Status | Action |
|---|---|---|
| ≥ 0.95 | Normal | Logged in Langfuse only |
| 0.80 – 0.94 | Minor deviation | Logged in Langfuse + alert to the Orchestrator |
| < 0.80 | Major deviation | Logged + alert to the Blue Team + HITL notification to the operator |
| Unauthorized tool | Independent of score | Immediate alert to the Blue Team + the Policy Server |
| K⊆X violation in the trajectory | Independent of score | Immediate alert + possible pipeline termination |

The audit report is stored in Langfuse with the fields: `run_id`,
`skill_id`, `skill_version`, `adherence_score`, `unauthorized_tools`,
`epistemic_violations`, `efficiency_score`, `policy_decisions_audited`,
`vibe_diffs_audited`, and `verdict`.

---

## Positive consequences

- Agents are explainable: what they did and why can always be reconstructed.
- Incorporating the Policy Server's decisions and the Vibe Diffs gives a
  full view of the governance flow.
- Scores accumulated in Langfuse allow detecting behavioral degradation
  over time.

## Negative consequences

- The Auditor adds overhead proportional to the number of steps in the
  trajectory.
- `SKILL.md`'s `expected_trajectory` must be kept up to date, or it
  produces false negatives.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Post-mortem audit only | Real-time K⊆X violations can cause irreversible damage |
| Sampling-based audit | Security violations must be audited 100% of the time |
| Periodic manual audit | Doesn't scale; Langfuse's traces are the automated substitute |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Incorporated the Policy Server's decisions as part of the
  auditable trajectory.
- **b.1.2** Connected the audit with the Red Team subgraph, excluding it
  from the main DAG's score.
- **c.1.2** Added the Vibe Diff's trajectory as an auditable component.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the diagram of the four components of the
  full auditable trajectory.
- **b.1.3** Added Table 1 with the adherence thresholds, their ranges,
  and their operational consequences.

**Changes in v1.4:**
- **a** Expanded Context to explain that this ADR implements the real
  measurement of D6 (ADR-007) and complements K⊆X (ADR-008), before
  descending into the detail of the four components. Fixed the broken
  "ADR-00" reference for the Auditor Agent to ADR-016.
