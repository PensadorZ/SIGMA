---
id: ADR-001
title: Epistemic Memory Based on a Feature Store and an Assumption Graph
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-001 v1.4
minimum-references: ADR-002, ADR-008, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-001: Epistemic Memory Based on a Feature Store and an Assumption Graph

## Executive summary of changes in v1.5

The Context section is expanded to explicitly state what Epistemic Memory
is and why it exists within the broader SIGMA ecosystem — specifically,
its role as the operational foundation for Epistemic Containment K ⊆ X
(ADR-008) — rather than opening directly on the technical problem. A
conceptual cross-reference note is added at the end of the Decision
section, pointing to a parallel personal theoretical framework the
author is developing (epistemological Zeugmatization), explicitly scoped
as outside this ADR's technical requirements.

## Executive summary of changes in v1.4

The KS-test is declared the **sole authorized method** for drift
detection, documenting the formal rejection of PSI (Population Stability
Index) following the evaluation carried out during Milestone 1. Minor
change, no compatibility impact.

---

## Context

SIGMA operates as an ecosystem of autonomous agents that run pipelines
recurrently, not as a single one-off script. For that autonomy to be
trustworthy — rather than a source of accumulating hallucination — the
system needs memory that persists across runs: without it, every run
would relearn from scratch what's already known about an entity, and
there would be no way to detect when its behavior changes over time.
This memory is, moreover, the operational foundation of Epistemic
Containment K ⊆ X (ADR-008): an agent can only assert what it can trace
back to an observed data point, and that requires a real mechanism where
that observed data point is actually stored and queryable.

The central design problem is that two fundamentally distinct categories
of knowledge exist, and treating them as a single one introduces real
semantic ambiguity:

- **Verified facts:** user profiles, historical metrics, stable entity
  characteristics. Monotonic knowledge — once confirmed, it's only
  updated, never refuted.
- **Business assumptions:** hypotheses about behavior, model inferences.
  Non-monotonic knowledge — they can be refuted by new evidence without
  that invalidating the history of why they were believed at the time.

A single, homogeneous storage layer can't serve both categories well:
forcing refutable assumptions into the same structure as verified facts,
or vice versa, produces either loss of historical traceability or
unnecessary over-engineering for data that never changes. A flat JSON
file per run — the simplest alternative — doesn't solve the underlying
problem either: it doesn't scale past roughly a million entities, it
doesn't allow automatic re-evaluation of old assumptions, and it offers
no temporal traceability of changes of belief.

---

## Decision

### Fig. 1 — Epistemic Memory architecture

```
External entities
        │
        ├─ Verified facts ───────────→ Feature Store (PostgreSQL)
        │                              └─ entity_features
        │                                 (entity_id, feature_key,
        │                                  value, valid_from, valid_to)
        │
        └─ Inferred beliefs ────────→ Assumption Graph
                                       └─ Versioned JSON + NetworkX
                                          States: PROPOSED → ACTIVE
                                                   → CONFLICT → KNOWN
                                                   → REFUTED

During a parallel pipeline (MapReduce):
  Worker-N ──→ Redis List (sigma:graph:updates:{run_id})
                    │
                    ▼
              Serializer node (Orchestrator)
                    │
                    ▼
              Assumption Graph (FIFO serialized write)
                    │
                    ▼
              Versioned JSON (persisted when the pipeline ends)

Read mode: workers access the graph directly (no queue)
```

### Table 1 — Feature Store implementation by variant

| Variant | Backend | Extra cost | Configuration requirement |
|---|---|---|---|
| **SIGMA Full** | PostgreSQL with temporal partitioning | No license cost | Manual temporal index |
| **SIGMA Lite** | Bigtable or DynamoDB (`FeatureStoreClient` adapter) | Per-operation cost | Cloud credentials |
| **SIGMA Dev** | PostgreSQL with synthetic data | No license cost | Identical to Full |
| **SIGMA Runtime** | PostgreSQL or Bigtable depending on the deployed environment | Variable | Depends on choice |

### Component 1 — Temporal Feature Store

Stores verified facts with historical versioning. In SIGMA Full it uses
PostgreSQL with an `entity_features` table with fields `entity_id`,
`feature_key`, `value`, `valid_from`, `valid_to`. The `FeatureStoreClient`
interface abstracts the backend, which allows migrating from SIGMA Full
to SIGMA Lite without modifying the skills.

### Component 2 — Assumption Graph

Stores inferred beliefs with explicit state transitions.

### Fig. 2 — Lifecycle of an assumption

```
         evidence available
PROPOSED ──────────────────→ ACTIVE ──→ KNOWN
                                │        (multiple independent
                                │         pieces of evidence)
                                ▼
                            CONFLICT ──→ ACTIVE (resolved)
                                │
                                ▼
                            REFUTED (terminal — kept for audit
                                     with the refutation date)
```

**In SIGMA Full:** versioned JSON per entity plus in-memory NetworkX.
**In SIGMA Lite:** Neo4j AuraDB via the `GraphClient` adapter.

### Serialized writes during parallel pipelines

During an active run with MapReduce workers, workers queue update
requests in a Redis List keyed `sigma:graph:updates:{run_id}`. A single
serializer node in the Orchestrator consumes the queue in FIFO order and
applies the updates. When the run ends, the graph is persisted as
versioned JSON. This resolves the race condition between ADR-001 and
ADR-002.

### Data lineage

Every processed row carries a `trace_id` that allows tracing its origin
and transformations. Without lineage, K ⊆ X is verifiable only at the
schema level, not at the individual data-point level. See ADR-008.

### Statistical drift

When the Feature Store detects deviation in an incoming batch's
distribution, the pipeline generates a `MEDIUM`-level alert to the
Approval Endpoint and logs the event in Langfuse (see ADR-011). The
operator decides whether to continue or pause. The `statistical-validator`
skill (0004) implements the detection algorithm using the **KS-test as
the sole authorized method**, with a configurable threshold in
`policies.yaml` (not in `defaults.yaml`). PSI (Population Stability
Index) was evaluated during Milestone 1 and **formally rejected**: it
requires arbitrary binning, which introduces sensitivity to interval
choice, whereas the KS-test operates on the full empirical distribution
with no discretization parameters.

> **Conceptual note (outside this ADR's technical scope):** the split
> between verified facts (Component 1) and business assumptions
> (Component 2) has a parallel with a personal theoretical framework the
> author is developing — epistemological Zeugmatization — where the
> What-How plane (Platonic) corresponds to concrete facts and the
> What-Why plane (Socratic) corresponds to handling uncertainty and
> hypotheses. This note is a cross-reference, not a requirement: this
> ADR is complete and verifiable without knowing that framework, and its
> formal development lives outside SIGMA's technical documentation.

---

## Positive consequences

- Separating facts from assumptions removes semantic ambiguity.
- Temporal versioning allows detecting behavioral drift.
- The Assumption Graph preserves the system's historical reasoning.
- The abstract interface allows migrating between variants without
  modifying the skills.
- The Redis queue resolves concurrency without adding new dependencies
  to the stack.

## Negative consequences

- Two storage systems increase operational complexity in SIGMA Full.
- Queries that cross facts and assumptions require an additional
  orchestration layer (`EpistemicQueryRouter`).
- JSON versioning has scale limits beyond roughly 100,000 entities.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| A single JSON per workflow | Doesn't scale; no automatic re-evaluation |
| Document database (MongoDB) | No native graph semantics |
| Memory only in the LLM's context | Volatile; limited by the context window |
| Redis as the sole memory store | Inadequate for complex temporal queries |
| PSI (Population Stability Index) for drift | Requires arbitrary binning; sensitive to interval choice. The KS-test operates on the full empirical distribution. Rejected in Milestone 1 |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added a serialized write mode via Redis during parallel
  pipelines to resolve the race condition with ADR-002.
- **b.1.2** Incorporated data lineage as an implementation requirement
  of K ⊆ X.
- **c.1.2** Added the trigger mechanism for statistical drift detection.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the memory architecture diagram.
- **b.1.3** Added Fig. 2 with an assumption's lifecycle.
- **c.1.3** Added Table 1 with the Feature Store implementation by variant.
- **d.1.3** Added a concrete reference to the `statistical-validator`
  skill for the KS-test implementation.

**Changes in v1.4:**
- **a.1.4** Declared the KS-test the sole authorized drift-detection
  method, with its threshold in `policies.yaml`.
- **b.1.4** Documented the formal rejection of PSI in Alternatives
  Considered, with the technical justification verified during
  Milestone 1.

**Changes in v1.5:**
- **a** Expanded Context to open with what Epistemic Memory is and why
  it exists in the ecosystem — its role as the operational foundation of
  Epistemic Containment K ⊆ X (ADR-008) — before descending into the
  technical problem.
- **b** Added a conceptual cross-reference note on epistemological
  Zeugmatization at the end of the Decision section, explicitly scoped
  outside this ADR's technical requirements.
