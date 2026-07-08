---
id: ADR-002
title: Massive Intra-Skill Parallelism via MapReduce Templates
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-002 v1.3
minimum-references: ADR-001, ADR-009, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-002: Massive Intra-Skill Parallelism via MapReduce Templates

## Executive summary of changes in v1.4

The Context section is expanded to open with what this mechanism is and
why it exists in the broader ecosystem — as an extension of the skill
specification (ADR-009) — before descending into the technical
partitioning problem, and to make explicit its connection to the
traceability requirement inherited from ADR-001.

## Executive summary of changes in v1.3

Added Fig. 1 with the flow diagram of the three strategies. Added
Table 1 with the strategy comparison. Specified that the reducer must
use commutative operations or an explicit order by `trace_id` to
guarantee determinism. Incorporated the version history.

---

## Context

SIGMA runs skills over datasets that can reach volumes beyond a million
records — the reference use case (WC2026-Tweets) is the concrete
example. Without a native parallelization mechanism built into the skill
specification (ADR-009), every skill that needed to process that volume
would have to implement its own partitioning and coordination logic from
scratch, duplicating effort across skills and risking that each
implementation solves the problem differently — or, worse, that some
simply don't scale and fail in production without warning.

The design problem is twofold. On one hand, processing the full dataset
in a single worker is infeasible in time and cost. On the other, if this
is solved manually by hand-creating a DAG node per partition, the skill
designer is exposed to a combinatorial explosion of nodes depending on
each run's data volume, making the DAG impossible to reason about or
maintain as the dataset grows. On top of this sits a non-negotiable
requirement inherited from ADR-001: traceability must be preserved at
the level of each individual worker, not just at the level of the whole
skill, so that a partial failure allows retrying only the affected
partitions, without repeating work that already completed successfully.

---

## Decision

Extend the skill specification with a `parallelism` field in the YAML
frontmatter. When this field is present, the Orchestrator automatically
generates workers according to the declared strategy.

### Fig. 1 — Flow of the three intra-skill parallelism strategies

```
── map_reduce STRATEGY ────────────────────────────────────────────
Dataset ──→ Partitioner ──→ Worker-01 (chunk 1/N) ──┐
                         ──→ Worker-02 (chunk 2/N) ──┤→ Reducer ──→ Output
                         ──→ Worker-0N (chunk N/N) ──┘
            [trace_id travels with every row]

── scatter_gather STRATEGY ─────────────────────────────────────────
Dataset ──→ Partitioner ──→ Worker-01 ──→ Result-01 (independent)
                         ──→ Worker-02 ──→ Result-02 (independent)
                         ──→ Worker-0N ──→ Result-0N (independent)

── chain STRATEGY ──────────────────────────────────────────────────
Dataset ──→ Worker-1 ──→ Redis List (BLPOP) ──→ Worker-2
                                           ──→ Redis List (BLPOP) ──→ Worker-3
           [stage_1]       sigma:chain:{run_id}:{skill_id}:1
                                                               [stage_2]
```

### Table 1 — Parallelism strategy comparison

| Strategy | Pattern | Use case | Key consideration |
|---|---|---|---|
| **`map_reduce`** | N parallel workers + final reducer | Volumes > 100,000 records | Reducer must be idempotent; use commutative operations or order by `trace_id` |
| **`scatter_gather`** | N parallel workers, no reducer | Classifications with autonomous partitions | No coordination between workers |
| **`chain`** | Sequential worker chain with a Redis buffer | Transformations with dependent steps within the same skill | Uses `BLPOP`; in Runtime requires confirmation in `policies.yaml` |

### `trace_id` propagation

Each partition carries a `trace_id` on every row across the entire
transformation chain. The reducer consolidates the `trace_id`s of the
partitions it merges. This guarantees the data lineage required by
ADR-001 and ADR-008.

### `chain` strategy — Redis implementation

Worker N writes its output to a Redis List keyed
`sigma:chain:{run_id}:{skill_id}:{stage}`. Worker N+1 runs `BLPOP` on
that key and activates when data arrives, without consuming CPU on
active waiting. In the Runtime variant, the `chain` strategy requires
explicit operator confirmation in `policies.yaml` because it implies
long-lived workers. If volume exceeds Redis's capacity or stronger
delivery guarantees are needed, an ADR-014-style advanced messaging
record will be created.

### Behavior in SIGMA Dev

The `parallelism.workers` field is automatically overridden to `1` to
simplify debugging. The rest of the specification remains intact.

---

## Positive consequences

- The designer writes a single definition and the Orchestrator manages
  parallelization.
- Granular traceability allows surgical retries of only the failed
  partitions.
- The `parallelism` field is optional: skills without it work exactly as
  before.
- The `chain` strategy adds no new dependencies to the stack, since
  Redis already exists.

## Negative consequences

- The Orchestrator takes on extra responsibility for managing the
  workers' lifecycle.
- The reducer must be deterministic and idempotent.
- Skills with `parallelism` are harder to debug without Langfuse active.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Single worker per skill | Infeasible for large datasets |
| Manual nodes per partition | Combinatorial explosion; unmaintainable skills |
| Celery or Ray as a scheduler | Unjustified infrastructure dependencies |
| Kafka for the `chain` strategy | Reserved for a future ADR if volume demands it |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Renamed the `pipeline` strategy to `chain` to avoid ambiguity
  with the Data Science pipeline concept.
- **b.1.2** Specified the `chain` implementation using Redis `BLPOP` as
  the buffer between chained workers.
- **c.1.2** Added per-row `trace_id` propagation for data lineage.
- **d.1.2** Established that the `chain` strategy in the Runtime variant
  requires explicit operator confirmation.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the flow diagram of the three strategies.
- **b.1.3** Added Table 1 with the strategy comparison.
- **c.1.3** Specified that the reducer must use commutative operations
  or an explicit order by `trace_id` to guarantee determinism.

**Changes in v1.4:**
- **a** Expanded Context to open with what this mechanism is and why it
  exists in the ecosystem, before descending into the technical
  partitioning problem.
