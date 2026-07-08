---
id: ADR-015
title: Real-Time Analysis Architecture with Hamilton Selector
version: 1.2
status: Proposed
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-015 v1.1
minimum-references: ADR-002, ADR-008, ADR-009, ADR-010, ADR-012
applicable-milestone: Milestone 3
approved-by: Pending approval from Prof. Marx A. García Delgado
file-name: adr-015-hamilton-selector-streaming.md
---

# ADR-015: Real-Time Analysis Architecture with Hamilton Selector

## Executive summary of changes in v1.2

The Context section is expanded to first explain that this streaming
architecture is reserved since ADR-009 (skills 0016-0019) and coexists
as a peer subgraph to the batch orchestrator ADR-016 formalizes — before
descending into the detail of the resource-constrained prioritization problem.

## Executive summary of changes in v1.1

Migrated the ADR (originated in the "Eco MultiAgentes 3 (Hito 1)"
conversation) to the ADR repository's approved canonical format: full
YAML frontmatter, titled and numbered figures and tables, and a
literal-based version history. The prior audit's correction is kept: the
relationship that incorrectly cited "ADR-011: LangGraph" was removed —
the real ADR-011 covers traceability in Langfuse V2, not the choice of
LangGraph. The formal decision backing LangGraph as the orchestration
engine is logged as pending documentary audit.

---

## Context

The Hamilton Selector and the streaming architecture this ADR defines
are the ecosystem's natural extension toward real time — reserved since
ADR-009 in the `0016`-`0019` skill range, and designed to **coexist,
not compete**, with Milestone 1's batch orchestrator: the same LangGraph
ADR-016 formalizes as the ecosystem's single engine keeps running the
batch pipeline while this streaming graph operates in parallel, as a
fourth peer subgraph.

SIGMA's Milestones 1 and 2 operate in **batch** mode: the pipeline
processes complete datasets (Tirendaz 22.5K → Zenodo 130K → Mendeley
28M+) in discrete runs. However, the WC2026-Tweets use case has a
real-time dimension: during matches, the message flow is continuous and
the value of the analysis decays within minutes.

Without a streaming architecture, SIGMA can't: detect sentiment spikes
during live events, feed reactive dashboards, or prioritize which
messages to analyze when the flow exceeds local compute capacity.

The prioritization problem is central: with limited resources (SIGMA
Full, local compute), not every message can be analyzed in real time. A
**selector** is needed to decide what to process first.

---

## Decision

### 2.1 — Hamilton Selector: prioritization via a Hamiltonian matrix

The **Hamilton Selector** is introduced (skill `0016`): a prioritization
component that assigns each incoming message a composite score computed
as a weighted linear combination of signals, inspired by the structure
of a Hamiltonian matrix where diagonal elements represent each signal's
"self-energy" and the weighted sum determines processing priority.

**Table 1 — Signals and weights in the prioritization matrix**

| Signal | Weight | Description |
|---|---|---|
| Potential engagement | 0.30 | Followers, the author's historical retweets |
| Lexical novelty | 0.25 | Distance from already-known topic clusters |
| Thread velocity | 0.25 | Rate of replies/mentions per minute |
| Entity relevance | 0.20 | Presence of domain entities (teams, players) |

The weights sum to 1.0 and are configurable in `policies.yaml`. The
K ⊆ X constraint (ADR-008) applies: the selector only uses signals
present in the message and its observable metadata, never inferences
from the model's training.

### 2.2 — Streaming stack: Kafka + Faust

| Component | Role |
|---|---|
| **Apache Kafka** | Event broker; topics per match/event |
| **Faust** | Python stream-processing layer on top of Kafka |
| **Skills 0017–0019** | Specialized Faust consumers (RT analysis, aggregation, reactive dashboard) |

Broker credentials (if any) are managed with `get_required_env()` per
ADR-010. Skill `0019` uses Netlify as a deployment option for the
reactive dashboard, per ADR-012's deployment hook.

### 2.3 — Batch/streaming coexistence

The batch architecture from Milestones 1 and 2 **is not modified**:

- Skills 0000–0015 are independent of the streaming decision.
- Milestone 1's LangGraph orchestrator runs alongside the streaming
  graph — these are two separate, non-exclusive operating modes.
- Streaming feeds the Feature Store (ADR-001) with the same data
  contracts; batch can reprocess what streaming prioritized.

**Fig. 1 — Coexistence of the two operating modes**

```
BATCH MODE (Milestones 1-2)           STREAMING MODE (Milestone 3)
──────────────────────                ─────────────────────────
Full dataset                          Kafka topic (continuous flow)
      │                                     │
      ▼                                     ▼
LangGraph Orchestrator                Hamilton Selector (0016)
  skills 0000-0015                       │ score > threshold
      │                                     ▼
      ▼                               Faust consumers (0017-0019)
PostgreSQL / MinIO / Langfuse               │
      ▲                                     ▼
      └────── Shared Feature Store ─────────┘
              (ADR-001, same contracts)
```

---

## Consequences

### Benefits

- SIGMA gains live-analysis capability without touching Milestone 1's
  verified batch architecture.
- The Hamilton Selector makes real time viable with local compute: what
  matters gets processed, not everything.
- Skills 0016–0019 follow ADR-009's seven-artifact protocol, with
  Gherkin and LTL — no exceptions for being streaming skills.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Kafka adds significant operational complexity | Milestone 3 doesn't start until Milestones 1 and 2 are validated; Kafka is only available in SIGMA-ME/HE (sufficient compute and budget for the broker) |
| Matrix weights can skew toward viral content | Weights are configurable and auditable in `policies.yaml`; periodic review against ADR-007's D1 |
| Low classifier confidence in streaming | K ⊆ X applies the same as in batch: `UNCLEAR` for low confidence, no exceptions (ADR-008) |

### Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-002 | Kafka's per-topic partitioning is the streaming analog of batch MapReduce |
| ADR-008 | K ⊆ X applies in streaming exactly as in batch. `UNCLEAR` for low confidence, no exceptions |
| ADR-009 | Skills 0016–0019 follow the seven-artifact protocol with Gherkin and LTL |
| ADR-010 | Broker credentials (if any) are managed with `get_required_env()` |
| ADR-012 | Skill 0019 uses Netlify as a deployment option for the reactive dashboard |
| — | Milestone 1's LangGraph orchestrator coexists with Milestone 3's streaming graph as a parallel operating mode. *Audit note: this row previously incorrectly cited "ADR-011" — the real ADR-011 covers Langfuse V2 traceability, not LangGraph. The formal decision backing LangGraph is pending documentary audit (a candidate to be resolved in ADR-016)* |

---

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Process 100% of the flow with no selector | Infeasible with local compute; peak flow exceeds capacity |
| Random sampling instead of the Hamilton Selector | Systematically loses the highest analytical-value messages |
| Redis Streams instead of Kafka | Sufficient for ADR-002's `chain` buffer, but lacks the retention and partitioning guarantees a full match's event flow requires |
| Spark Structured Streaming | Unjustified infrastructure overhead for Milestone 3's initial target volume |

---

## Version history

**Changes in v1.0:**
- **a.1.0** Original draft in "Eco MultiAgentes 4 Skills 2" with the
  Status · Context · Decision (2.1–2.3) · Consequences · History structure.
- **b.1.0** Audit correction: removed the false reference to "ADR-011:
  LangGraph"; the real ADR-011 covers Langfuse V2 traceability.

**Changes in v1.1:**
- **a.1.1** Migrated to the ADR repository's canonical format: full YAML
  frontmatter with the `hito-de-aplicacion` field, titled and numbered
  Fig. 1 and Table 1, literal-based history.
- **b.1.1** Added the Alternatives Considered section, absent in v1.0.
- **c.1.1** The pending formal decision on LangGraph is marked as a
  candidate to be resolved in ADR-016.

**Changes in v1.2:**
- **a** Expanded Context to explain that this streaming architecture is
  reserved since ADR-009 (skills 0016-0019) and coexists as a peer
  subgraph to the batch orchestrator ADR-016 formalizes, before
  descending into the detail of the resource-constrained prioritization problem.
