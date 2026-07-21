---
id: ADR-002
title: Massive Intra-Skill Parallelism via MapReduce Templates
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-002 v1.4
minimum-references: ADR-001, ADR-003, ADR-009, ADR-011, ADR-017
approved-by: Prof. Marx A. García Delgado
---

# ADR-002: Massive Intra-Skill Parallelism via MapReduce Templates

## Executive summary of v1.5 changes

Three real corrections, verified against the project's current state
(Milestone 2, Rollout 1 close): (1) "worker" is renamed to **"compute
node"** throughout the document — this is the originating ADR for the
term that `ADR-003` already had to correct due to a collision with
"Worker" from `ADR-019` (a distinct concept, an ephemeral subagent);
(2) "Runtime variant"/"SIGMA Dev" are corrected to **submode** — Runtime
and Dev are cross-cutting submodes, not cost variants, per the variant
scheme migration already applied across the rest of the project; (3)
**a real numbering collision**: this document reserved "ADR-014" for a
future advanced-messaging ADR — that number is already taken by
"Dynamic Generation of New Skills" (approved later). The reference is
corrected to the next available number.

## Executive summary of v1.4 changes

The Context section is expanded to open with what this mechanism is and
why it exists in the ecosystem — as an extension of the skill
specification (ADR-009) — before getting into the technical
partitioning problem, making its connection to the traceability
requirement inherited from ADR-001 explicit.

## Executive summary of v1.3 changes

Fig. 1 is added with the flow diagram of the three strategies. Tab. 1
is added with the strategy comparison. It is specified that the reducer
must use commutative operations or an explicit `trace_id` ordering to
guarantee determinism. Version history is incorporated.

---

## Context

SIGMA runs skills on datasets that can reach volumes of over a million
records — the reference use case (WC2026-Tweets) is the concrete
example. Without a native parallelization mechanism in the skill
specification (ADR-009), every skill that needed to process that volume
would have to implement its own partitioning and coordination logic
from scratch, duplicating effort across skills and risking each
implementation solving the problem differently — or, worse, some simply
not scaling and failing in production without warning.

The design problem is twofold. On one hand, processing the entire
dataset on a single compute node is unfeasible in time and cost. On the
other, if solved manually by creating one DAG node per partition, the
skill designer is exposed to a combinatorial explosion of nodes
depending on each run's data volume, making the DAG impossible to
reason about or maintain as the dataset grows. Added to this is a
non-negotiable requirement inherited from ADR-001: traceability must be
preserved at the level of each individual compute node, not only at the
level of the whole skill, so that a partial failure allows retrying
only the affected partitions, without repeating work already completed
successfully.

---

## Decision

Extend the skill specification with a `parallelism` field in the YAML
frontmatter. When this field is present, the Orchestrator automatically
generates the compute nodes according to the declared strategy.

### Fig. 1 — Flow of the three intra-skill parallelism strategies

```
── map_reduce STRATEGY ────────────────────────────────────────────
Dataset ──→ Partitioner ──→ Node-01 (chunk 1/N) ──┐
                        ──→ Node-02 (chunk 2/N) ──┤→ Reducer ──→ Output
                        ──→ Node-0N (chunk N/N) ──┘
            [trace_id travels with each row]

── scatter_gather STRATEGY ────────────────────────────────────────
Dataset ──→ Partitioner ──→ Node-01 ──→ Result-01 (independent)
                        ──→ Node-02 ──→ Result-02 (independent)
                        ──→ Node-0N ──→ Result-0N (independent)

── chain STRATEGY ─────────────────────────────────────────────────
Dataset ──→ Node-1 ──→ Redis List (BLPOP) ──→ Node-2
                                        ──→ Redis List (BLPOP) ──→ Node-3
           [stage_1]       sigma:chain:{run_id}:{skill_id}:1
                                                               [stage_2]
```

### Tab. 1 — Parallelism strategy comparison

| Strategy | Pattern | Use case | Key consideration |
|---|---|---|---|
| **`map_reduce`** | N compute nodes in parallel + final reducer | Volumes > 100,000 records | Reducer must be idempotent; use commutative operations or order by `trace_id` |
| **`scatter_gather`** | N compute nodes in parallel, no reducer | Classifications with autonomous partitions | No coordination between nodes |
| **`chain`** | Compute nodes in a sequential chain with a Redis buffer | Transformations with dependent steps within the same skill | Uses `BLPOP`; requires confirmation in `policies.yaml` in Runtime submode |

### `trace_id` propagation

Every partition carries a `trace_id` on each row throughout the entire
transformation chain. The reducer consolidates the `trace_id`s of the
partitions it unifies. This guarantees the data lineage ADR-001 and
ADR-008 require.

### `chain` strategy — Redis implementation

Compute node N writes its output to a Redis List with key
`sigma:chain:{run_id}:{skill_id}:{stage}`. Compute node N+1 runs
`BLPOP` on that key and activates when the data arrives, with no CPU
spent on active waiting. In Runtime submode, the `chain` strategy
requires the operator's explicit confirmation in `policies.yaml` since
it involves long-lived compute nodes. If volume exceeds Redis's
capacity or stronger delivery guarantees are needed, a **future
advanced-messaging ADR** will be created — **corrected**: the
originally reserved number (`ADR-014`) is already taken by "Dynamic
Generation of New Skills" (approved after this document); the next
available ADR at the time of this revision is `ADR-020`, but the final
number is assigned when that ADR is actually drafted — no more
reserving numbers in advance — we already saw, with this very mistake,
the consequences of reserving numbers without building them.

**Link to ADR-003 (AgBOM):** every compute node, under any of the three
strategies, emits the AgBOM event on startup (`{model_hash,
dependency_hashes, compute_node_id}`) — the same mechanism the Blue
Team already verifies, with no distinction by parallelism strategy.

### Behavior in Dev submode

The `parallelism.compute_nodes` field (renamed from
`parallelism.workers` — no Rollout 1 skill used it yet, a safe change)
is automatically overridden to `1` to simplify debugging. The rest of
the specification stays unchanged.

---

## Positive consequences

- The designer writes a single definition and the Orchestrator manages
  parallelization.
- Granular traceability allows surgical retries of only the failed
  partitions.
- The `parallelism` field is optional: skills without it work exactly
  as before.
- The `chain` strategy adds no new dependencies to the stack because
  Redis already exists.

## Negative consequences

- The Orchestrator takes on additional responsibility for managing
  compute nodes' lifecycle.
- The reducer must be deterministic and idempotent.
- Skills with `parallelism` are harder to debug without Langfuse
  active.

**Link to ADR-017 (sandboxing):** this ADR's compute nodes **do not**
fall within the scope of mandatory sandboxing — they are part of
human-authored skills (Rollout 1/2), not dynamically generated code nor
ephemeral Workers (`ADR-019`). Same criterion `ADR-017` §2.1 already
states explicitly.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| A single compute node per skill | Unfeasible for large datasets |
| Manual nodes per partition | Combinatorial explosion; unmaintainable skills |
| Celery or Ray as scheduler | Unjustified infrastructure dependencies |
| Kafka for the `chain` strategy | Reserved for a future ADR if volume demands it |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Renamed the `pipeline` strategy to `chain` to avoid
  ambiguity with the Data Science pipeline concept.
- **b.1.2** Specified the `chain` implementation with Redis `BLPOP` as
  a buffer between chained workers.
- **c.1.2** Added per-row `trace_id` propagation for data lineage.
- **d.1.2** Established that the `chain` strategy in the Runtime
  variant requires the operator's explicit confirmation.

**Changes in v1.3:**
- **a** Added Fig. 1 with the flow diagram of the three strategies.
- **b** Added Tab. 1 with the strategy comparison.
- **c** Specified that the reducer must use commutative operations or
  an explicit `trace_id` ordering to guarantee determinism.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** "worker" renamed to "compute node" throughout the document —
  this is the originating ADR for the term, corrected so it does not
  collide with "Worker" from `ADR-019` (a distinct concept, an
  ephemeral subagent). `parallelism.workers` field renamed to
  `parallelism.compute_nodes`.
- **b** "Runtime variant"/"SIGMA Dev" corrected to Runtime/Dev submode,
  consistent with the variant-scheme migration already applied across
  the rest of the project.
- **c** Fixed the numbering collision: the "ADR-014 for advanced
  messaging" this document reserved is already taken by "Dynamic
  Generation of New Skills" — a number is no longer reserved in
  advance, it will be assigned once that ADR is actually drafted.
- **d** Added formal links to ADR-003 (AgBOM, emitted by every compute
  node) and ADR-017 (compute nodes are explicitly out of scope for
  mandatory sandboxing, being part of human-authored skills).
