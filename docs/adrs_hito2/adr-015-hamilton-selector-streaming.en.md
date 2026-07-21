---
id: ADR-015
title: Real-Time Analysis Architecture with the Hamilton Selector
version: 1.3
status: Proposed
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-015 v1.2
minimum-references: ADR-002, ADR-008, ADR-009, ADR-010, ADR-012
milestone-of-application: Milestone 3
approved-by: Pending approval from Prof. Marx A. García Delgado
file-name: adr-015-hamilton-selector-streaming.md
---

# ADR-015: Real-Time Analysis Architecture with the Hamilton Selector

## Executive summary of v1.3 changes

Verified against Milestone 2's real state (Rollout 1 close): (1)
variant scheme corrected (`SIGMA Full` → `SIGMA-FE`); (2) the
"Milestone 1 LangGraph orchestrator" no longer exists as a monolithic
component — every reference is replaced with `ADR-016`'s Director +
Engineers hierarchy, consistent with this ADR already describing itself
as a "sibling subgraph" of that hierarchy; (3) the formal decision
about LangGraph this ADR marked as "pending documentary audit" has
already been resolved — `ADR-016` §2.1 formalizes it explicitly. The
"pending" note is removed.

## Executive summary of v1.2 changes

The Context section is expanded to first explain that this streaming
architecture has been reserved since ADR-009 (skills 0016-0019) and
coexists as a sibling subgraph to the batch orchestrator ADR-016
formalizes — before getting into the detail of the resource-constrained
prioritization problem.

## Executive summary of v1.1 changes

Migration of the ADR (originating in the "Eco MultiAgentes 3 (Hito 1)"
conversation) to the ADR repository's approved canonical format: full
YAML frontmatter, numbered figures and tables with titles, and version
history with lettered items. The previous audit correction is
preserved: the relationship that incorrectly cited "ADR-011:
LangGraph" was removed — the real ADR-011 covers Langfuse V2
traceability, not the choice of LangGraph. The formal decision backing
LangGraph as the orchestration engine is recorded as pending
documentary audit.

---

## Context

The Hamilton Selector and the streaming architecture this ADR defines
are the ecosystem's natural extension toward real time — reserved
since ADR-009 in the `0016`-`0019` skill range, and meant to
**coexist, not compete**, with Milestone 1's batch orchestrator: the
same LangGraph `ADR-016` formalizes as the ecosystem's sole engine
keeps running the batch pipeline while this streaming graph operates in
parallel, as a fourth sibling subgraph.

SIGMA's Milestones 1 and 2 operate in **batch** mode: the pipeline
processes complete datasets (Tirendaz 22.5K → Zenodo 130K → Mendeley
28M+) in discrete runs. However, the WC2026-Tweets use case has a
real-time dimension: during matches, the message flow is continuous
and the analysis's value decays within minutes.

Without a streaming architecture, SIGMA cannot: detect sentiment spikes
during live events, feed reactive dashboards, or prioritize which
messages to analyze when volume exceeds local compute capacity.

The prioritization problem is central: with limited resources
(SIGMA-FE, local compute), not every message can be analyzed in real
time. A **selector** is needed to decide what to process first.

---

## Decision

### 2.1 — Hamilton Selector: prioritization via a Hamiltonian matrix

The **Hamilton Selector** (skill `0016`) is introduced: a
prioritization component that assigns every incoming message a
composite score computed as a weighted linear combination of signals,
inspired by the structure of a Hamiltonian matrix where the diagonal
elements represent each signal's "self-energy" and the weighted sum
determines processing priority.

**Tab. 1 — Signals and weights in the prioritization matrix**

| Signal | Weight | Description |
|---|---|---|
| Potential engagement | 0.30 | Followers, the author's historical retweets |
| Lexical novelty | 0.25 | Distance to already-known topic clusters |
| Thread velocity | 0.25 | Rate of replies/mentions per minute |
| Entity relevance | 0.20 | Presence of domain entities (teams, players) |

Weights sum to 1.0 and are configurable in `policies.yaml`. The K ⊆ X
constraint (ADR-008) applies: the selector only uses signals present in
the message and its observable metadata, never inferences from the
model's training.

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

Milestones 1 and 2's batch architecture **is not modified**:

- Skills 0000–0015 are independent of the streaming decision.
- **Corrected (Milestone 2, Rollout 1):** there is no longer a
  monolithic "Milestone 1 LangGraph orchestrator" — it was replaced by
  `ADR-016`'s Director + Engineers (Data/Models/Auditor) hierarchy.
  This ADR's streaming graph coexists with that hierarchy as a
  **sibling subgraph**, as `ADR-016` already anticipates in its own
  relationship table with other ADRs — not with an orchestrator that no
  longer exists in that form.
- Streaming feeds the Feature Store (ADR-001) with the same data
  contracts; batch can re-process what streaming prioritized.

**Fig. 1 — Coexistence of the two operating modes**

```
BATCH MODE (Milestones 1-2)           STREAMING MODE (Milestone 3)
──────────────────────                ─────────────────────────
Full dataset                          Kafka topic (continuous flow)
      │                                     │
      ▼                                     ▼
Director + Engineers (ADR-016)        Hamilton Selector (0016)
  skills 0000-0015                      │ score > threshold
      │                                     ▼
      ▼                               Faust consumers (0017-0019)
PostgreSQL / MinIO / Langfuse               │
      ▲                                     ▼
      └────── Common Feature Store ─────────┘
              (ADR-001, same contracts)
```

---

## Consequences

### Benefits

- SIGMA gains live-analysis capability without touching Milestone 1's
  verified batch architecture.
- The Hamilton Selector makes real time viable with local compute: what
  matters most gets processed, not everything.
- Skills 0016–0019 follow ADR-009's seven-artifact protocol, with
  Gherkin and LTL — no exceptions for being streaming.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Kafka adds significant operational complexity | Milestone 3 doesn't start until Milestones 1 and 2 are validated; Kafka only available on SIGMA-ME/HE (enough compute and budget for the broker) |
| Matrix weights may skew toward viral content | Weights are configurable and auditable in `policies.yaml`; periodic review against ADR-007 D1 |
| Low classifier confidence in streaming | K ⊆ X applies the same as in batch: `UNCLEAR` for low confidence, no exceptions (ADR-008) |

### Relationship with other ADRs

| ADR | Relationship |
|---|---|
| ADR-002 | Kafka's per-topic partitioning is the streaming analog of batch MapReduce |
| ADR-008 | K ⊆ X applies in streaming the same as in batch. `UNCLEAR` for low confidence, no exceptions |
| ADR-009 | Skills 0016–0019 follow the seven-artifact protocol with Gherkin and LTL |
| ADR-010 | Broker credentials (if any) are managed with `get_required_env()` |
| ADR-012 | Skill 0019 uses Netlify as a deployment option for the reactive dashboard |
| ADR-016 | The batch orchestrator is no longer a monolithic Milestone-1 LangGraph — it is the Director + Engineers hierarchy `ADR-016` v1.1+ formalizes, including the base decision of LangGraph as the orchestration engine (§2.1, resolved — no longer pending). This ADR's streaming integrates as a sibling subgraph of that hierarchy |

---

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Processing 100% of the flow with no selector | Unfeasible with local compute; peak volume exceeds capacity |
| Random sampling instead of the Hamilton Selector | Systematically loses the messages of highest analytical value |
| Redis Streams instead of Kafka | Sufficient for the `chain` buffer (ADR-002) but lacks the retention and partitioning guarantees a full match's event flow requires |
| Spark Structured Streaming | Unjustified infrastructure overhead for Milestone 3's initial target volume |

---

## Version history

**Changes in v1.0:**
- **a.1.0** Original drafting in "Eco MultiAgentes 4 Skills 2" with the
  Status · Context · Decision (2.1–2.3) · Consequences · History
  structure.
- **b.1.0** Audit correction: removed the false reference to
  "ADR-011: LangGraph"; the real ADR-011 covers Langfuse V2
  traceability.

**Changes in v1.1:**
- **a** Migration to the ADR repository's canonical format: full YAML
  frontmatter with a `milestone-of-application` field, Fig. 1 and Tab.
  1 numbered with titles, history with lettered items.
- **b** Added the Alternatives Considered section, absent in v1.0.
- **c** The pending formal decision about LangGraph is marked as a
  candidate to be resolved in ADR-016.

**Changes in v1.3 (Milestone 2, Rollout 1 close):**
- **a** Variant scheme corrected: `SIGMA Full` → `SIGMA-FE`.
- **b** All references to the monolithic "Milestone 1 LangGraph
  orchestrator" updated to `ADR-016`'s real Director + Engineers
  hierarchy — Fig. 1 and section 2.3 corrected.
- **c** Resolved the "pending documentary audit" note about
  LangGraph — `ADR-016` §2.1 already formalizes that decision, the
  pending mark is removed and the real resolution is cited.
