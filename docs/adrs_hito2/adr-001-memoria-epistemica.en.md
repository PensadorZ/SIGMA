---
id: ADR-001
title: Epistemic Memory based on Feature Store and Assumption Graph
version: 1.6
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-001 v1.5
minimum-references: ADR-002, ADR-008, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-001: Epistemic Memory based on Feature Store and Assumption Graph

## Executive summary of v1.6 changes

Two real corrections (Milestone 2, Rollout 1 close): "worker" is
renamed to "compute node" in Fig. 1 and in the text (consistent with
the originating ADR-002, already corrected) — this document was one of
those still using the old term. Tab. 1 corrected to the real cost
variant scheme (SIGMA-FE/LE/ME/HE) separated from submode
(Dev/Runtime).

## Executive summary of v1.5 changes

The Context section is expanded to explicitly establish what Epistemic
Memory is and why it exists within the broader SIGMA ecosystem —
specifically, its role as the operational foundation of Epistemic
Containment K ⊆ X (ADR-008) — instead of opening directly with the
technical problem. A conceptual cross-reference note is added at the
end of the Decision section, pointing to a parallel personal
theoretical framework the author is developing (Epistemological
Zeugmatization), explicitly delimited as outside this ADR's technical
scope.

## Executive summary of v1.4 changes

KS-test is declared the **sole authorized method** for drift detection,
documenting the formal rejection of PSI (Population Stability Index)
following the evaluation carried out during Milestone 1. Minor change
with no compatibility impact.

---

## Context

SIGMA operates as an ecosystem of autonomous agents that run pipelines
recurrently, not as a single-run script. For that autonomy to be
trustworthy — and not a source of accumulated hallucination — the
system needs persistent memory across executions: without it, every
run would relearn from scratch what is already known about an entity,
and there would be no way to detect when its behavior changes over
time. This memory is, moreover, the operational foundation of Epistemic
Containment K ⊆ X (ADR-008): an agent can only assert what it can trace
back to an observed data point, and that requires a real mechanism
where that observed data point is stored and queryable.

The central design problem is that two fundamentally distinct
categories of knowledge exist, and treating them as one introduces real
semantic ambiguity:

- **Verified facts:** user profiles, historical metrics, stable entity
  characteristics. Monotonic knowledge — once confirmed, it is only
  updated, never refuted.
- **Business assumptions:** behavioral hypotheses, model inferences.
  Non-monotonic knowledge — they can be refuted by new evidence without
  that invalidating the record of why they were believed at the time.

A single, homogeneous store cannot serve both categories well at once:
forcing refutable assumptions into the same structure as verified
facts, or vice versa, produces either loss of historical traceability
or unnecessary over-engineering for data that never changes. A flat
JSON file per run, the simplest alternative, also fails to solve the
underlying problem: it doesn't scale beyond a million entities, doesn't
allow automatic re-evaluation of old assumptions, and offers no
temporal traceability of changes of belief.

---

## Decision

### Fig. 1 — Epistemic Memory architecture

```
External entities
        │
        ├─ Verified facts ──────→ Feature Store (PostgreSQL)
        │                              └─ entity_features
        │                                 (entity_id, feature_key,
        │                                  value, valid_from, valid_to)
        │
        └─ Inferred beliefs ─────→ Assumption Graph
                                       └─ Versioned JSON + NetworkX
                                          States: PROPOSED → ACTIVE
                                                   → CONFLICT → KNOWN
                                                   → REFUTED

During a parallel pipeline (MapReduce):
  Node-N ──→ Redis List (sigma:graph:updates:{run_id})
                    │
                    ▼
              Serializer Node (Orchestrator)
                    │
                    ▼
              Assumption Graph (serialized FIFO write)
                    │
                    ▼
              Versioned JSON (persisted when the pipeline ends)

Read mode: compute nodes access the graph directly (no queue)
```

### Tab. 1 — Feature Store implementation by variant

**Corrected (Milestone 2):** the original table mixed cost and submode
in the same rows. It is separated into two real axes, consistent with
the rest of the project.

| Cost variant | Backend | Extra cost | Configuration requirement |
|---|---|---|---|
| **SIGMA-FE** | PostgreSQL with temporal partitioning | No license cost | Manual temporal index |
| **SIGMA-LE** | PostgreSQL with temporal partitioning | No license cost | Manual temporal index |
| **SIGMA-ME** | Bigtable or DynamoDB (`FeatureStoreClient` adapter) | Per-operation cost | Cloud credentials |
| **SIGMA-HE** | Bigtable or DynamoDB, larger reserved capacity | Per-operation cost, scaled | Cloud credentials |

**Dev submode (any variant):** PostgreSQL with synthetic data,
identical to the backend of the variant active in Runtime, no extra
cost. **Runtime submode:** the real backend per the table above.

### Component 1 — Temporal Feature Store

Stores verified facts with historical versioning. On SIGMA-FE/LE it
uses PostgreSQL with an `entity_features` table with fields
`entity_id`, `feature_key`, `value`, `valid_from`, `valid_to`. The
`FeatureStoreClient` interface abstracts the backend, allowing
migration from SIGMA-FE/LE to SIGMA-ME/HE without modifying the skills.

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
                            REFUTED (terminal — kept for
                                     audit with a refutation
                                     date)
```

**On SIGMA-FE/LE:** versioned JSON per entity plus NetworkX in memory.
**On SIGMA-ME/HE:** Neo4j AuraDB via the `GraphClient` adapter.

### Serialized writes during parallel pipelines

During an active run with MapReduce compute nodes (ADR-002), the nodes
enqueue requests on a Redis List with key
`sigma:graph:updates:{run_id}`. A single serializer node on the
Orchestrator consumes the queue in FIFO order and applies the updates.
On completion, the graph is persisted as versioned JSON. This resolves
the race condition between ADR-001 and ADR-002.

### Data lineage

Every processed row carries a `trace_id` that allows tracing its origin
and transformations. Without lineage, `K ⊆ X` is only verifiable at the
schema level, not at the level of an individual data point. See
ADR-008.

### Statistical drift

When the Feature Store detects a distribution deviation in an incoming
batch, the pipeline generates a `MEDIUM`-level alert to the Approval
Endpoint and logs the event in Langfuse (see ADR-011). The operator
decides whether to continue or pause. The `statistical-validator` skill
(0004) implements the detection algorithm using **KS-test as the sole
authorized method**, with a threshold configurable in `policies.yaml`
(not in `defaults.yaml`). PSI (Population Stability Index) was
evaluated during Milestone 1 and **formally rejected**: it requires
arbitrary binning that introduces sensitivity to the choice of
intervals, whereas the KS-test operates on the full empirical
distribution with no discretization parameters.

---

> **Conceptual note (outside this ADR's technical scope):** the
> separation between verified facts (Component 1) and business
> assumptions (Component 2) bears a parallel to a personal theoretical
> framework the author is developing — Epistemological Zeugmatization —
> where the What-How plane (Platonic) corresponds to concrete facts and
> the What-Why plane (Socratic) corresponds to handling uncertainty and
> hypotheses. This note is a cross-reference, not a requirement: the
> ADR is complete and verifiable without knowledge of that framework,
> and its formal development lives outside SIGMA's technical
> documentation.

## Positive consequences

- Separating facts and assumptions removes semantic ambiguity.
- Temporal versioning enables detecting behavioral drift.
- The Assumption Graph preserves the system's historical reasoning.
- The abstract interface allows migrating between variants without
  modifying skills.
- The Redis queue resolves concurrency without adding new dependencies
  to the stack.

## Negative consequences

- Two storage systems increase operational complexity, regardless of
  the active cost variant.
- Queries that cross facts and assumptions require an additional
  orchestration layer (`EpistemicQueryRouter`).
- JSON versioning has scaling limits beyond 100,000 entities.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| A single JSON per workflow | Doesn't scale; doesn't allow automatic re-evaluation |
| Document database (MongoDB) | No native graph semantics |
| Memory only in the LLM's context | Volatile; limited by context window |
| Redis as the sole memory | Inadequate for complex temporal queries |
| PSI (Population Stability Index) for drift | Requires arbitrary binning; sensitive to interval choice. KS-test operates on the full empirical distribution. Rejected in Milestone 1 |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added a serialized-write mode via Redis during parallel
  pipelines to resolve the race condition with ADR-002.
- **b.1.2** Incorporated data lineage as an implementation requirement
  of K ⊆ X.
- **c.1.2** Added the trigger mechanism for detected statistical drift.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the memory architecture diagram.
- **b.1.3** Added Fig. 2 with an assumption's lifecycle.
- **c.1.3** Added Tab. 1 with the Feature Store's implementation by
  variant.
- **d.1.3** Added a concrete reference to the `statistical-validator`
  skill for the KS-test implementation.

**Changes in v1.4:**
- **a** Declared KS-test as the sole authorized drift-detection method,
  with a threshold in `policies.yaml`.
- **b** Documented PSI's formal rejection in Alternatives Considered,
  with the technical justification verified during Milestone 1.

**Changes in v1.6 (Milestone 2, Rollout 1 close):**
- **a** "worker" renamed to "compute node" in Fig. 1 and in the text —
  consistent with ADR-002 (already corrected in this session).
- **b** Tab. 1 corrected to the 4 real cost-variant levels, separated
  from Dev/Runtime submode.
