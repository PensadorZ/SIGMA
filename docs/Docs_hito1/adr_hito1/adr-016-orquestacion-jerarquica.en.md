---
id: ADR-016
title: Hierarchical Orchestration of Three Orchestrators (Director/Engineer/Auditor)
version: 1.3
status: Proposed
original-date: 2026-07
revision-date: 2026-07
supersedes: ADR-016 v1.0
minimum-references: ADR-002, ADR-003, ADR-009, ADR-011, ADR-013
milestone-of-application: Milestone 2
approved-by: Pending approval from Prof. Marx A. García Delgado
file-name: adr-016-orquestacion-jerarquica.en.md
---

# ADR-016: Hierarchical Orchestration of Three Orchestrators (Director/Engineer/Auditor)

## Executive summary of changes v1.3

Corrects a real gap detected while preparing Rollout 1 code:
`0008-sentiment-analyzer` and `0011-viz-reporter` — the two skills with
real code and passing tests since Milestone 1 — were not assigned to any
Engineer in Fig. 1 or Tab. 2. They are reassigned to Engineer Data, which
now covers `0000-0004, 0008, 0011`. Without this correction, the Rollout
1 Director would not have been able to run sentiment analysis or
generate the dashboard — the visible output of running SIGMA.

## Executive summary of changes v1.2

Adds section 2.4 with the phased implementation plan by Rollouts
(1/2/3), resolving the sequencing ambiguity that v1.1 left implicit.
Each Rollout declares a verifiable exit condition and its pending
dependencies on real code, preventing the full hierarchy from being
considered built when in fact only one subgraph exists.

## Executive summary of changes v1.1

Expands the Context section to first explain that this ADR serves a
dual purpose — retroactively formalizing LangGraph as the engine and
defining Milestone 2 governance — before detailing the three-orchestrator
hierarchy.

## Executive summary

This ADR formalizes the decision already approved at design level
(conversation "Eco MultiAgentes Sigma 3 (Hito 1)") that Milestone 2
adopts a **hierarchical three-orchestrator architecture** via LangGraph
subgraphs, under the Director/Engineer/Auditor pattern. Its write-up was
pending as documentation debt; this ADR settles it. It also formally
registers a decision no prior ADR backed: **LangGraph as the
orchestration engine of the ecosystem** — resolving the pending
reference flagged during the ADR-015 audit.

---

## Context

This ADR serves an unusually dual purpose: it retroactively resolves a
technical decision already in de facto use since Milestone 1 (LangGraph
as the engine), while simultaneously defining the governance
architecture for Milestone 2. In that sense, it is the ADR that
stabilizes the ground beneath the rest of the ecosystem — without
LangGraph's formalization here, every ADR that mentions `interrupt()`,
checkpointers, or subgraphs (ADR-004, ADR-002, ADR-015) would rest on a
technology choice never justified in writing.

Milestone 1 operates with a single orchestrator (SupervisorAgent in
LangGraph) managing a linear pipeline of 6 skills. Milestone 2
introduces 9 additional skills (0005–0007, 0009–0010, 0012–0015)
covering ML/DL training, explainability, advanced HITL, and inspection —
domains with radically different trajectories, execution times, and
supervision needs.

A single flat orchestrator would have to know the details of all 15
skills, their cross-dependencies, and their retry policies — a decision
monolith that grows quadratically in complexity with every new skill.

Additionally, the ADR-015 audit found that no formal decision backed the
choice of LangGraph: it had been used de facto since Milestone 1 without
a justifying ADR. This document records that decision.

---

## Decision

### 2.1 — Base decision: LangGraph as the orchestration engine

LangGraph (MIT license, LangChain ecosystem) is formalized as SIGMA's
orchestration engine for all Milestones, based on evidence from
Milestone 1:

- Typed state graph (`PipelineState`) with validation at every
  transition.
- Native checkpointing (`SqliteSaver`) enabling HITL via `interrupt()`,
  verified in ADR-004 v1.5.
- Conditional edges implementing the fail-fast circuit breaker: the DAG
  short-circuits as soon as `pipeline_status == 'failed'`.
- Subgraphs as a composition mechanism — the technical foundation of
  this ADR.

### 2.2 — The three orchestrators

**Fig. 1 — Milestone 2 orchestration hierarchy**

```
                DIRECTOR ORCHESTRATOR (level 0)
                ├─ Receives user intent
                ├─ Decomposes into phases and assigns to Engineers
                ├─ Sole point of contact with global HITL (ADR-004)
                └─ Consolidates results and evaluates 7D (ADR-007)
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
ENGINEER DATA        ENGINEER MODELS    ENGINEER AUDITOR
(subgraph 1)          (subgraph 2)       (subgraph 3)
skills:               skills:            skills:
0000-0004, 0008,      0005-0007,         0012-0015
0011                  0009-0010          (inspector,
(core batch           (ML/DL trainers,    explainability,
 pipeline +            advanced HITL)     audit)
 sentiment +
 dashboard)
```

Each Engineer is a **complete LangGraph subgraph** with its own
checkpointer, its own error nodes, and its own retry policy. The
Director only knows each Engineer's input/output contract, not its
internal skills.

### 2.3 — Hierarchy rules

**Tab. 1 — Division of responsibilities**

| Responsibility | Director | Engineer |
|---|---|---|
| Interpret user intent | ✅ | ⛔ |
| Know individual skills | ⛔ | ✅ (only its own) |
| Escalate to global HITL | ✅ | ⛔ (escalates to Director) |
| Intra-phase retries | ⛔ | ✅ |
| Final 7D evaluation | ✅ | ⛔ (emits partial metrics) |
| Langfuse traceability | Parent trace | Child span per subgraph (ADR-011) |

Non-negotiable rules:

1. An Engineer **never** invokes another Engineer's skills. If it needs
   their output, it requests it from the Director.
2. One Engineer's failure does not bring down the others: the Director
   decides whether to continue in degraded mode or abort (consistent
   with the circuit breaker).
3. The Red/Blue/Green team (ADR-003) operates at the Director level;
   Engineers emit AgBOM events like any worker.
4. The K ⊆ X constraint (ADR-008) and the seven-artifact protocol
   (ADR-009 v1.5) apply without exception within every subgraph.

### 2.4 — Rollout implementation plan

The Director never knows about Engineers that do not yet exist — in
Rollout 1, its routing logic contemplates only one possible destination.
This avoids building speculative coordination code for Engineers that
are not yet written, consistent with the K⊆X constraint (ADR-008)
applied to the system's own design, not only to the data it processes.

**Tab. 2 — Rollouts of the three-orchestrator hierarchy**

| Rollout | Built | Skills pending real-code verification | Exit condition |
|---|---|---|---|
| **Rollout 1** | Minimum viable Director + Engineer Data subgraph (`0000-0004, 0008, 0011`) | `0004-statistical-validator` — corrected spec (v1.0.1), `skill.py` unconfirmed. `0000-0003, 0008, 0011` already have real code and passing tests since Milestone 1 | (a) Engineer Data's full pytest-bdd suite green, including `0008` and `0011` · (b) 3 consecutive real runs without failure via the Director, not just 1 · (c) circuit breaker explicitly tested: at least 1 run with a forced non-recoverable failure, verifying correct fast-fail behavior · (d) complete Langfuse trace: parent trace (Director) + child span (Engineer Data) verified end-to-end, including the `viz-reporter.success` event |
| **Rollout 2** | Engineer Models added as a second subgraph | `0005-framework-selector`, `0006-ml-trainer`, `0007-dl-trainer`, `0009-cluster-analyzer`, `0010-engagement-calculator` — all ⬜ pending, none with code | (a) Engineer Models passes its own isolated suite, without the Director, before connecting · (b) Engineer Data → Engineer Models input contract explicitly tested (Data's output consumable without manual transformation) · (c) at least 1 real run with both Engineers coordinated · (d) the non-negotiable rule from section 2.3 is verified live: a failure in Engineer Models does not bring down Engineer Data |
| **Rollout 3** | Engineer Auditor added, full hierarchy | `0012-code-reviewer`, `0013-skill-discovery`, `0014-stride-modeling`, `0015-pipeline-inspector` — all pending; `0015` additionally requires resolving its scope (LLM over Langfuse vs. query engine over Redis) before writing its SKILL.md | (a) Engineer Auditor passes its isolated suite · (b) the 3 coordinated Engineers produce the full 7D evaluation (ADR-007) generated by the Director · (c) ADR-017 (sandboxing, pending write-up) must be approved and applied to Engineer Auditor before this phase, since auditing is the point most likely to trigger dynamic skill generation (ADR-014) |

**Note on ADR-017:** sandboxing existed in earlier project iterations
(ephemeral Docker/gVisor containers) but did not survive consolidation
into the current 16 ADRs. It is drafted as a new ADR, not an extension
of ADR-003, because its scope — containment of generated code
*execution* — is orthogonal to the threat detection ADR-003 already
covers; forcing it into ADR-003 would mix two distinct responsibilities
under one document.

---

## Consequences

### Benefits

- Decision complexity grows linearly per Engineer, not quadratically
  per skill.
- Subgraphs are testable in isolation — each Engineer has its own
  pytest-bdd suite.
- The pattern enables Milestone 3: the streaming graph (ADR-015)
  integrates as a fourth peer subgraph, without touching the other
  three.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Added latency from the coordination layer | Director↔Engineer contracts are synchronous and lightweight; measured overhead must be reported in D4 (ADR-007) |
| The Director becomes a decision bottleneck | The Director does not process data, only coordinates; its load is proportional to phases, not rows |
| Configuration duplication across subgraphs | Per-skill `defaults.yaml` (ADR-006) + a single root-level `policies.yaml` |

### Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-002 | Intra-skill MapReduce operates within each Engineer unchanged |
| ADR-003 | Red/Blue/Green operates at the Director level; Engineers emit AgBOM |
| ADR-009 | Milestone 2's 9 new skills follow the seven-artifact protocol |
| ADR-011 | Parent trace at the Director; one child span per Engineer subgraph |
| ADR-013 | The auditable trajectory includes the Director's assignment decisions |
| ADR-015 | Milestone 3's streaming graph will integrate as a peer subgraph |
| ADR-017 (pending) | Execution sandboxing becomes an entry condition for Rollout 3, where the risk of uncontained dynamic skill generation (ADR-014) is highest |

---

## Alternatives considered

| Alternative | Why it was discarded |
|---|---|
| Single flat orchestrator with 15 skills | Quadratic decision complexity; a monolith impossible to test piecewise |
| Independent microservices per domain | Unjustified network and deployment overhead for local SIGMA Full |
| Two-level hierarchy with a single Engineer | Does not separate data/models/quality, which have incompatible retry and HITL policies |
| CrewAI or another hierarchical framework | Would introduce a second orchestration framework; LangGraph already provides native subgraphs |

---

## Version history

This is the first record of this ADR. The design decision was verbally
approved in "Eco MultiAgentes 5 Skills 3" and remained pending formal
documentation until this version.

**Changes in v1.2:**
- **a** Adds section 2.4, Rollout implementation plan (1/2/3), resolving
  the build sequence that v1.1 left implicit. Each Rollout declares a
  verifiable exit condition and skills pending real code.
- **b** Adds a cross-reference to ADR-017 (sandboxing, pending
  write-up), required as an entry condition for Rollout 3.

**Changes in v1.3:**
- **a** Corrects Fig. 1 and Tab. 2: `0008-sentiment-analyzer` and
  `0011-viz-reporter` were not assigned to any Engineer. Reassigned to
  Engineer Data (`0000-0004, 0008, 0011`), preserving the functional
  pipeline inherited from Milestone 1 without restructuring it.
