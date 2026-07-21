---
id: ADR-003
title: Automated Security with the Red/Blue/Green Model
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-003 v1.3
minimum-references: ADR-004, ADR-005, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-003: Automated Security with the Red/Blue/Green Model

## Executive summary of changes in v1.4

The Context section is expanded to first explain what the Red/Blue/Green
model is and why it exists in the ecosystem — as the mechanism covering
the three risk phases (before, during, and after execution) that no
purely preventive control like the Policy Server (ADR-005) can cover on
its own — before descending into the classification of the three threat
classes.

## Executive summary of changes in v1.3

Added Fig. 1 with the coordination diagram of the three teams relative
to the DAG. Added Table 1 with applicability by variant. Incorporated
the version history.

---

## Context

SIGMA delegates code generation, prompt interpretation, and
execution-bound decisions to LLMs against real data and infrastructure.
That delegation is precisely what makes the system's autonomy possible,
as described elsewhere in the ecosystem (ADR-001, ADR-002) — but it also
opens a risk surface that no purely preventive governance mechanism
(like the Policy Server in ADR-005) can cover on its own: an LLM can
behave correctly at the moment of structural validation and still
degrade, be manipulated, or fail midway through a long-running
execution. SIGMA therefore needs a security mechanism that doesn't just
validate before acting, but also watches during execution and knows how
to recover after a failure — the three phases no static control covers.

A multi-agent system that runs LLM-generated code and accesses external
data is vulnerable to three distinct threat classes, each with a
different time window:

- **Active threats:** prompt injection, slopsquatting, malicious code —
  occur at the moment of generation or execution.
- **Passive threats:** silent drift in agent behavior, unaudited
  dependencies — accumulate over time, with no single triggering event.
- **Recovery failures:** an agent that fails midway through the pipeline
  can corrupt partial state with no possibility of a clean rollback —
  occur after the fact, when it's already too late to prevent them.

A single auditor at the end of execution can't detect or prevent these
three threats in real time, because by the time it reviews the result,
all three time windows have already closed.

---

## Decision

Implement three specialized security agents that run in parallel to the
main DAG throughout the entire execution.

### Fig. 1 — Coordination of the Red/Blue/Green teams relative to the DAG

```
PRE-FLIGHT PHASE (before the real DAG):
─────────────────────────────────────────
Orchestrator creates a checkpoint of the initial state
        │
        ▼
Temporary subgraph (cloned data, relaxed ADR-005 policies)
        │
        ├─ Red Team operates on the subgraph
        │    └─ Injects adversarial prompts, simulated dependencies
        │    └─ Emits an immutable report → MinIO
        │
        ▼
Subgraph destroyed → real DAG begins

DURING THE REAL DAG:
─────────────────────────────────────────
Each worker emits an AgBOM event on startup:
  {model_hash, dependency_hashes, worker_id}
        │
        ▼
Blue Team verifies hashes against the reference AgBOM in Langfuse
  └─ Deviation detected → alert to the Orchestrator

ON FAILURE:
─────────────────────────────────────────
Failure detected (exception or Blue Team alert)
        │
        ▼
Green Team: snapshots the state → isolates the compromised agent
        │
        ▼
code-reviewer evaluates the refactor code
        │
        ├─ LOW impact  → Green Team applies it automatically
        └─ MEDIUM/HIGH impact → Vibe Diff → Approval Endpoint (ADR-004)
```

### Red Team — Pre-flight model

The Red Team doesn't operate on real data during the production
pipeline. It operates in a pre-flight phase before the real DAG begins.
Findings are immutable reports stored in MinIO, not mutations of the
real state.

### Table 1 — Team applicability by variant

| Team | SIGMA Full | SIGMA Lite | SIGMA Dev | SIGMA Runtime |
|---|---|---|---|---|
| **Red Team** | Active | Active | Disabled by default | Mandatory before a critical pipeline |
| **Blue Team** | Active | Active | Optional | Active |
| **Green Team** | Active | Active | Active | Active |

### Blue Team — AgBOM-based monitoring

The Blue Team doesn't manage one thread per worker. Each worker emits an
AgBOM event on startup with its `model_hash` and `dependency_hashes`.
The Blue Team verifies those hashes against the reference AgBOM in
Langfuse. The number of workers it can handle is bounded by Langfuse's
event limits, not by any intrinsic limit of the Blue Team itself.

### Green Team — Recovery with a review cycle

All auto-refactor-generated code mandatorily passes through the
`code-reviewer` skill. If the impact is `LOW`, the Green Team applies it
automatically. If the impact is `MEDIUM` or higher, it generates a Vibe
Diff with the exact code diff and waits for approval per ADR-004.
Quarantine preserves forensic state: the pre-quarantine snapshot is
never automatically deleted.

---

## Positive consequences

- Splitting the work into three roles removes conflicts of interest.
- The Red Team's pre-flight model guarantees real data is never
  contaminated by simulated attacks.
- The Blue Team scales to any number of workers via Langfuse events.
- The `code-reviewer` + Vibe Diff cycle guarantees recovery code is
  audited before being applied.

## Negative consequences

- The Red Team's pre-flight step adds latency before every critical
  pipeline run.
- The Green Team requires write access to checkpoints on fast local storage.
- Coordinating the three teams adds complexity to the Orchestrator.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| A single post-execution auditor | The damage is already done by the time it runs |
| Input/output validation only | Doesn't detect compromises during execution |
| External SIEM | Dependencies outside the SIGMA ecosystem |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Redefined the Red Team to operate in a pre-flight model over
  a cloned subgraph, removing the risk of contaminating real data.
- **b.1.2** Added the Green Team's recovery cycle with `code-reviewer`
  and Vibe Diff integration.
- **c.1.2** Specified the Blue Team's scalability via AgBOM events in
  Langfuse instead of per-worker threads.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the coordination diagram of the three
  teams relative to the DAG.
- **b.1.3** Added Table 1 with applicability by variant.

**Changes in v1.4:**
- **a** Expanded Context to explain what the Red/Blue/Green model is and
  why it exists in the ecosystem before descending into the threat
  classification.
