---
id: ADR-016
title: Three-Orchestrator Hierarchical Orchestration (Director/Engineer/Auditor)
version: 1.1
status: Proposed
original-date: 2026-07
revision-date: 2026-07
supersedes: None
minimum-references: ADR-002, ADR-003, ADR-009, ADR-011, ADR-013
applicable-milestone: Milestone 2
approved-by: Pending approval from Prof. Marx A. García Delgado
file-name: adr-016-orquestacion-jerarquica.md
---

# ADR-016: Three-Orchestrator Hierarchical Orchestration (Director/Engineer/Auditor)

## Executive summary of changes in v1.1

The Context section is expanded to first explain that this ADR serves a
dual purpose — retroactively formalizing LangGraph as the engine and
defining Milestone 2's governance — before descending into the detail
of the three-orchestrator hierarchy.

## Executive summary

This ADR formalizes the design decision already approved (in the "Eco
MultiAgentes Sigma 3 (Hito 1)" conversation) that Milestone 2 adopts a
**hierarchical three-orchestrator architecture** via LangGraph
subgraphs, under the Director/Engineer/Auditor pattern. Writing it up
was left as documentation debt; this ADR settles it. It also takes the
opportunity to formally register the decision no prior ADR backed:
**LangGraph as the ecosystem's orchestration engine** — resolving the
pending reference flagged in ADR-015's audit.

---

## Context

This ADR serves an unusually dual purpose: it retroactively resolves a
technical decision that had already been in de facto use since
Milestone 1 (LangGraph as the engine), while also defining the
governance architecture for Milestone 2. In that sense, it's the ADR
that stabilizes the ground under the rest of the ecosystem — without
formalizing LangGraph here, every ADR that mentions `interrupt()`,
checkpointers, or subgraphs (ADR-004, ADR-002, ADR-015) would rest on a
technology choice never justified in writing.

Milestone 1 runs with a single orchestrator (a SupervisorAgent in
LangGraph) that manages a linear pipeline of 6 skills. Milestone 2 adds
9 more skills (0005–0007, 0009–0010, 0012–0015) covering ML/DL training,
explainability, advanced HITL, and inspection — domains with radically
different trajectories, execution times, and supervision needs.

A single flat orchestrator would have to know the details of all 15
skills, their cross-dependencies, and their retry policies — a decision
monolith that grows quadratically in complexity with every new skill.

Additionally, ADR-015's audit found that no formal decision backed the
choice of LangGraph: it had been used de facto since Milestone 1 with no
ADR justifying it. This document registers it.

---

## Decision

### 2.1 — Foundational decision: LangGraph as the orchestration engine

LangGraph (MIT license, LangChain ecosystem) is formalized as SIGMA's
orchestration engine for all Milestones, based on Milestone 1's evidence:

- A typed state graph (`PipelineState`) with validation at every transition.
- Native checkpointing (`SqliteSaver`) enabling the `interrupt()`-based
  HITL verified in ADR-004 v1.5.
- Conditional edges implementing the fast-fail circuit breaker: the DAG
  short-circuits as soon as `pipeline_status == 'failed'`.
- Subgraphs as the composition mechanism — the technical foundation of
  this ADR.

### 2.2 — The three orchestrators

**Fig. 1 — Milestone 2's orchestration hierarchy**

```
                DIRECTOR ORCHESTRATOR (level 0)
                ├─ Receives the user's intent
                ├─ Breaks it into phases and assigns them to Engineers
                ├─ Sole point of contact with global HITL (ADR-004)
                └─ Consolidates results and evaluates 7D (ADR-007)
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
DATA ENGINEER    MODEL ENGINEER     AUDITOR ENGINEER
(subgraph 1)     (subgraph 2)       (subgraph 3)
skills:          skills:            skills:
0000-0004        0005-0007,         0012-0015
(core batch      0009-0010          (inspector,
 pipeline)       (ML/DL trainers,    explainability,
                  advanced HITL)     auditing)
```

Each Engineer is a **full LangGraph subgraph** with its own
checkpointer, its own error nodes, and its own retry policy. The
Director only knows each Engineer's input/output contract, not its
internal skills.

### 2.3 — Rules of the hierarchy

**Table 1 — Division of responsibilities**

| Responsibility | Director | Engineer |
|---|---|---|
| Interpret the user's intent | ✅ | ⛔ |
| Know the individual skills | ⛔ | ✅ (only its own) |
| Escalate to global HITL | ✅ | ⛔ (escalates to the Director) |
| Intra-phase retries | ⛔ | ✅ |
| Final 7D evaluation | ✅ | ⛔ (emits partial metrics) |
| Langfuse traceability | Parent trace | Child span per subgraph (ADR-011) |

Non-negotiable rules:

1. An Engineer **never** invokes another Engineer's skills. If it needs
   that output, it requests it from the Director.
2. One Engineer's failure doesn't bring down the others: the Director
   decides whether to continue in degraded mode or abort (consistent
   with the circuit breaker).
3. The Red/Blue/Green team (ADR-003) operates at the Director's level;
   Engineers emit AgBOM events like any other worker.
4. The K ⊆ X constraint (ADR-008) and the seven-artifact protocol
   (ADR-009 v1.5) apply with no exceptions inside every subgraph.

---

## Consequences

### Benefits

- Decision complexity grows linearly per Engineer, not quadratically
  per skill.
- Subgraphs are testable in isolation — each Engineer has its own
  pytest-bdd suite.
- The pattern enables Milestone 3: the streaming graph (ADR-015)
  integrates as a fourth peer subgraph, with no changes to the other three.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Extra latency from the coordination layer | Director↔Engineer contracts are synchronous and lightweight; the measured overhead must be reported in D4 (ADR-007) |
| The Director becomes a decision bottleneck | The Director doesn't process data, only coordinates; its load is proportional to phases, not rows |
| Configuration duplication across subgraphs | Per-skill `defaults.yaml` (ADR-006) + a single root-level `policies.yaml` |

### Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-002 | Intra-skill MapReduce operates unchanged inside each Engineer |
| ADR-003 | Red/Blue/Green operates at the Director level; Engineers emit AgBOM |
| ADR-009 | Milestone 2's 9 new skills follow the seven-artifact protocol |
| ADR-011 | Parent trace at the Director; one child span per Engineer subgraph |
| ADR-013 | The auditable trajectory includes the Director's assignment decisions |
| ADR-015 | Milestone 3's streaming graph will integrate as a peer subgraph |

---

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| A single flat orchestrator with 15 skills | Quadratic decision complexity; a monolith impossible to test piece by piece |
| Independent microservices per domain | Unjustified network and deployment overhead in local SIGMA Full |
| A two-level hierarchy with a single Engineer | Doesn't separate data/models/quality, which have mutually incompatible retry and HITL policies |
| CrewAI or another hierarchical framework | Would introduce a second orchestration framework; LangGraph already provides native subgraphs |

---

## Version history

This is the first record of this ADR. The design decision was verbally
approved in "Eco MultiAgentes 5 Skills 3" and remained pending
documentary formalization until this version.

**Changes in v1.1:**
- **a** Expanded Context to explain that this ADR serves a dual purpose
  — retroactively formalizing LangGraph as the engine and defining
  Milestone 2's governance — before descending into the detail of the
  three-orchestrator hierarchy.
