---
id: ADR-013
title: Agent Trajectory Auditing
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-013 v1.4
minimum-references: ADR-003, ADR-005, ADR-008, ADR-011, ADR-016, ADR-018
approved-by: Prof. Marx A. García Delgado
---

# ADR-013: Agent Trajectory Auditing

## Executive summary of v1.5 changes

Real correction: the document body still cited the broken "ADR-00"
reference even though v1.4's own changelog claimed to have corrected it
to ADR-016 — it is now actually applied, along with incomplete text
("such as...") left unfinished in an earlier edit. A link to ADR-018 is
added: the Ag-DR uses exactly the same fields this ADR already defined
(`run_id`, `skill_id`, `verdict`) — they are not independent
mechanisms.

## Executive summary of v1.4 changes

The Context section is expanded to first explain that this ADR
implements the real measurement of D6 (ADR-007) and complements K⊆X
(ADR-008) as the other half of an agent's auditability. The broken
"ADR-00" reference for the Auditor Agent is corrected to **ADR-016**,
where it is formally defined as the third orchestrator in the
Director/Engineer/Auditor pattern.

## Executive summary of v1.3 changes

Fig. 1 is added with the diagram of the four components of a full
auditable trajectory. Tab. 1 is added with the adherence thresholds
and their operational consequences. Version history is incorporated.

---

## Context

Trajectory Auditing is the mechanism that makes it possible to measure
D6 (trajectory quality) in ADR-007's Multidimensional Evaluation —
without it, that dimension would be an intent with no real
implementation. It uses Langfuse traces (ADR-011) as its source of
truth, and its findings feed directly into the Blue Team (ADR-003) when
it detects severe deviations. Together with K⊆X (ADR-008), it is the
other half of what makes a SIGMA agent auditable: K⊆X guarantees what
the agent asserts is honest, while this ADR guarantees the path it took
to get there is also verifiable.

An agent can produce the correct output by taking the wrong path. It
can call tools in the wrong order, access tables it shouldn't, or
consume ten times more resources and still produce a result that
passes the unit tests. Trajectory is the sequence of tools, models, and
decisions the agent took to reach the output. Auditing the trajectory,
not just the output, allows detecting unexpected behavior, verifying
the agent operated within K⊆X's bounds (ADR-008), and identifying
inefficiencies.

---

## Decision

The Auditor agent (formally defined in ADR-016 as the third
orchestrator in the Director/Engineer/Auditor pattern) verifies each
run's real trajectory against the expected trajectory declared in
ADR-009's `SKILL.md`, using Langfuse V2 traces from ADR-011 as the
source of truth.

### Fig. 1 — Components of a full auditable trajectory

```
A PIPELINE'S FULL TRAJECTORY
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

COMPONENT 3 — Generated Vibe Diffs and their outcome
  vibe_diff_id: sigma-20260601-143022  → APPROVED  (operator: marxiano)
  → included in the audit report

COMPONENT 4 — Red Team sub-graph (excluded from the main score)
  red_team_probe: 3 vulnerabilities found, 0 critical
  → recorded as a separate component, does not affect the main
  DAG's adherence_score because it uses different policies by design
```

### Main verifications

The Auditor performs four verifications on the real trajectory:

1. **Adherence to the expected trajectory:** comparison against
   `SKILL.md`'s `expected_trajectory`. Score from 0 to 1.
2. **Unauthorized tools:** verification against `SKILL.md`'s
   `allowed-tools`.
3. **K⊆X violation in trajectory:** verification that every tool
   operated on data within X (ADR-008).
4. **Trajectory efficiency:** penalizing redundant steps.

### Tab. 1 — Adherence thresholds and consequences

| Score | Status | Action |
|---|---|---|
| ≥ 0.95 | Normal | Log in Langfuse only |
| 0.80 – 0.94 | Minor deviation | Log in Langfuse + alert to the Orchestrator |
| < 0.80 | Major deviation | Log + alert to the Blue Team + HITL notification to the operator |
| Unauthorized tool | Independent of score | Immediate alert to the Blue Team + the Policy Server |
| K⊆X violation in trajectory | Independent of score | Immediate alert + possible pipeline termination |

The audit report is stored in Langfuse with the fields: `run_id`,
`skill_id`, `skill_version`, `adherence_score`, `unauthorized_tools`,
`epistemic_violations`, `efficiency_score`, `policy_decisions_audited`,
`vibe_diffs_audited`, and `verdict`.

---

## Positive consequences

- Agents are explainable: it is always possible to reconstruct what
  they did and why.
- Incorporating Policy Server decisions and Vibe Diffs gives a full
  view of the governance flow.
- Scores accumulated in Langfuse allow detecting behavioral
  degradation over time.

## Negative consequences

- The Auditor adds overhead proportional to the number of steps in the
  trajectory.
- `SKILL.md`'s `expected_trajectory` must be kept up to date or it
  generates false negatives.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Post-mortem auditing only | Real-time K⊆X violations can cause irreversible damage |
| Sampling-based auditing | Security violations must be audited 100% |
| Periodic manual auditing | Doesn't scale; Langfuse traces are the automated substitute |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Incorporated Policy Server decisions as part of the
  auditable trajectory.
- **b.1.2** Connected auditing to the Red Team sub-graph, excluding it
  from the main DAG's score.
- **c.1.2** Added the Vibe Diff trajectory as an auditable component.

**Changes in v1.3:**
- **a** Added Fig. 1 with the diagram of the four components of a full
  auditable trajectory.
- **b** Added Tab. 1 with the adherence thresholds, their ranges, and
  their operational consequences.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** Actually applied the "ADR-00" → "ADR-016" correction v1.4's
  changelog already claimed to have made, which the document body
  never reflected.
- **b** Fixed incomplete text ("such as...") about the origin of
  traces — it is now fixed at Langfuse V2 (ADR-011), with no
  unspecified alternatives.
- **c** Added a link to ADR-018 (Ag-DR) — they share fields (`run_id`,
  `skill_id`, `verdict`), they are not redundant mechanisms.
