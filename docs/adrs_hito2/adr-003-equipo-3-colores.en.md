---
id: ADR-003
title: Automated Security with the Red/Blue/Green Model
version: 1.7
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-003 v1.4
minimum-references: ADR-004, ADR-005, ADR-011, ADR-017, ADR-019
approved-by: Prof. Marx A. García Delgado
---

# ADR-003: Automated Security with the Red/Blue/Green Model

## Executive summary of v1.7 changes

The full definition of AgBOM (Agent Bill of Materials) is added, which
the document had used since v1.0 without ever explaining it — its real
origin (SBOM, Executive Order 14028), and the JSON example already
established in earlier project sessions, inserted in the Blue Team
section where it belongs for the first time.

## Executive summary of v1.5 changes

Migration of the variant scheme in Tab. 1: the original table mixed
cost (Full/Lite) and submode (Dev/Runtime) with cost contributing no
real behavioral difference. It is simplified to a single axis
(submode), applicable uniformly across the 4 current cost variants
(`SIGMA-FE/LE/ME/HE`). New links are added with ADR-017 (sandboxing,
drafted in this same session) and ADR-019 (Agent Identity).
**Terminology correction (Marx's decision, not mine):** the term
"Worker" legitimately belongs to ADR-019 (a hierarchical-operational,
scalable concept) — it is MapReduce's parallel compute unit (ADR-002)
that needs its own name, having used "worker" generically without ever
defining it as its own concept. It is renamed here to **"compute node"**
(`ComputeNode`).

## Executive summary of v1.4 changes

The Context section is expanded to first explain what the Red/Blue/
Green model is and why it exists in the ecosystem — as the mechanism
covering the three risk phases (before, during, after execution) that
no purely preventive control such as the Policy Server (ADR-005) can
cover on its own — before getting into the classification of the three
threat classes.

## Executive summary of v1.3 changes

Fig. 1 is added with the coordination diagram of the three teams
relative to the DAG. Tab. 1 is added with per-variant applicability.
Version history is incorporated.

---

## Context

SIGMA delegates code generation, prompt interpretation, and decisions
executed against real data and infrastructure to LLMs. That delegation
is exactly what makes the system autonomy described across the rest of
the ecosystem possible (ADR-001, ADR-002), but it also opens a risk
surface that no purely preventive governance mechanism (such as the
ADR-005 Policy Server) can cover on its own: an LLM can behave
correctly at the moment of structural validation and still degrade, be
manipulated, or fail midway through a long execution. SIGMA therefore
needs a security mechanism that not only validates before acting, but
also watches during execution and knows how to recover after a
failure — the three phases no static control covers.

A multi-agent system that executes LLM-generated code and accesses
external data is vulnerable to three distinct threat classes, each with
a different time window:

- **Active threats:** prompt injection, slopsquatting, malicious
  code — occur at the moment of generation or execution.
- **Passive threats:** silent drift in agent behavior, unaudited
  dependencies — accumulate over time, with no single triggering
  event.
- **Recovery failures:** an agent that fails midway through the
  pipeline can corrupt partial state with no possibility of a clean
  rollback — they occur after the fact, when it's already too late to
  prevent.

A single auditor at the end of execution cannot detect or prevent these
three threats in real time, because by the time it reviews the result,
all three time windows have already closed.

---

## Decision

Implement three specialized security agents that run in parallel to the
main DAG throughout execution.

### Fig. 1 — Coordination of the Red/Blue/Green teams relative to the DAG

```
PRE-FLIGHT PHASE (before the real DAG):
─────────────────────────────────────
Orchestrator creates a checkpoint of the initial state
        │
        ▼
Temporary sub-graph (cloned data, relaxed ADR-005 policies)
        │
        ├─ Red Team operates on the sub-graph
        │    └─ Injects adversarial prompts, simulated dependencies
        │    └─ Emits an immutable report → MinIO
        │
        ▼
Sub-graph destroyed → real DAG begins

DURING THE REAL DAG:
─────────────────────────────────────
Each compute node (parallel MapReduce unit, ADR-002 — previously
called a "worker" generically, with no name of its own) emits an
AgBOM event on startup:
  {model_hash, dependency_hashes, compute_node_id}
        │
        ▼
Blue Team verifies hashes against the reference AgBOM in Langfuse
  └─ Deviation detected → alert to the Orchestrator

ON A FAILURE:
─────────────────────────────────────
Failure detected (exception or Blue Team alert)
        │
        ▼
Green Team: state snapshot → isolates the compromised agent
        │
        ▼
code-reviewer evaluates the refactor code
        │
        ├─ LOW impact  → Green Team applies it automatically
        └─ MEDIUM/HIGH impact → Vibe Diff → Approval Endpoint (ADR-004)
```

### Red Team — Pre-flight model

The Red Team does not operate during the production pipeline against
real data. It operates in a pre-flight phase before the real DAG
begins. Findings are immutable reports stored in MinIO, not mutations
of real state.

### Tab. 1 — Team applicability by submode

**Corrected (Milestone 2, Rollout 1 close):** the original table mixed
cost variants (Full/Lite) with submodes (Dev/Runtime) in the same
columns — and in practice, Full and Lite never differed from each
other (both said identical "Active" across all three rows). The axis
that actually determines the 3 teams' applicability is **submode**, not
cost — the table is simplified to reflect that, and it is clarified
that it applies equally across the 4 cost variants
(`SIGMA-FE/LE/ME/HE`).

| Team | Dev submode | Runtime submode |
|---|---|---|
| **Red Team** | Disabled by default | Mandatory before a critical pipeline |
| **Blue Team** | Optional | Active |
| **Green Team** | Active | Active |

Applies identically across any of the 4 cost variants (`SIGMA-FE`,
`SIGMA-LE`, `SIGMA-ME`, `SIGMA-HE`) — submode, not variant, is what
changes security behavior.

### Blue Team — Monitoring via AgBOM

**What AgBOM is and where it comes from** (a definition missing from
earlier versions of this document — it was assumed known, never
explained): **AgBOM = Agent Bill of Materials**, a direct extension of
**SBOM (Software Bill of Materials)** — a formal inventory of software
components (packages, versions, hashes) already established in the
security industry, mandated in the US by Executive Order 14028 for
software supply chains. SIGMA extends it from "Software" to "Agent": an
equivalent inventory but of agents — which model runs, with which exact
dependencies, verifiable by hash — instead of just packages.

**Real AgBOM example** (format already established in earlier project
sessions):

```json
{
  "run_id": "sigma-20260717-a1b2c3d4",
  "agents": [
    {
      "id": "data-cleanser-compute-node-01",
      "model": "deepseek-coder:6.7b",
      "model_hash": "sha256:...",
      "dependencies": ["pandas==2.2.1", "pydantic==2.7.0"],
      "dep_hashes": {"pandas": "sha256:...", "pydantic": "sha256:..."},
      "started_at": "2026-06-01T10:00:00Z",
      "status": "running"
    }
  ]
}
```

The `id` field identifies either a **compute node** (MapReduce,
ADR-002) or a **Worker** (ADR-019 §2.1ter) indistinctly — the Blue Team
does not need a separate schema for each, as already noted above in
this same version: it treats them uniformly.

The Blue Team does not manage a thread per compute node. Each compute
node emits an AgBOM event on startup with its `model_hash` and
`dependency_hashes`. The Blue Team verifies those hashes against the
reference AgBOM in Langfuse. The number of compute nodes it can handle
is bounded by Langfuse's event limit, not by any intrinsic Blue Team
limit.

**Link to ADR-019 (Agent Identity):** the **Worker** (ADR-019 §2.1ter —
an ephemeral subagent for specific tasks, distinct from MapReduce
compute nodes) emits the **same AgBOM event** when created, with its
`agent_id` instead of `compute_node_id`. The Blue Team treats them
uniformly — no separate monitoring mechanism is needed for Workers than
for MapReduce compute nodes.

### Green Team — Recovery with a review cycle

All code produced by auto-refactoring must go through the
`code-reviewer` skill. If impact is `LOW`, the Green Team applies it
automatically. If impact is `MEDIUM` or higher, it generates a Vibe
Diff with the exact code diff and awaits approval per ADR-004.
Quarantine preserves forensic state: the pre-quarantine snapshot is
never automatically deleted.

**Link to ADR-017 (Sandboxing, new):** the Green Team's isolation upon a
failure ("isolates the compromised agent") and ADR-017's execution
sandboxing are complementary mechanisms, not redundant ones — Green
Team acts *after* a failure is detected; ADR-017 prevents that failure
from having a blast radius *from the start*, for dynamically generated
code (ADR-014) or Ephemeral Agents (ADR-019).

---

## Positive consequences

- Splitting into three roles removes conflicts of interest.
- The Red Team's pre-flight model guarantees real data is never
  contaminated with simulated attacks.
- The Blue Team scales with any number of compute nodes via Langfuse
  events.
- The `code-reviewer` + Vibe Diff cycle guarantees recovery code is
  audited before being applied.

## Negative consequences

- The Red Team's pre-flight adds latency before every critical
  pipeline.
- The Green Team requires write access to checkpoints on fast local
  storage.
- Coordination between the three teams adds complexity to the
  Orchestrator.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| A single post-execution auditor | The damage is already done by the time it finishes |
| Only input/output validation | Doesn't detect compromises during execution |
| External SIEM | Dependencies outside the SIGMA ecosystem |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Redefined the Red Team to operate in a pre-flight model on
  a cloned sub-graph, removing the risk of contaminating real data.
- **b.1.2** Added the Green Team's recovery cycle with `code-reviewer`
  and Vibe Diff integration.
- **c.1.2** Specified the Blue Team's scalability via AgBOM events in
  Langfuse instead of a thread per compute node.

**Changes in v1.3:**
- **a** Added Fig. 1 with the coordination diagram of the three teams
  relative to the DAG.
- **b** Added Tab. 1 with per-variant applicability.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** Tab. 1 migrated from the old, mixed variant scheme
  (Full/Lite/Dev/Runtime) to the real scheme — submode (Dev/Runtime) is
  the sole axis determining applicability; the table was simplified and
  it was clarified it applies equally across the 4 cost variants.
- **b** Terminology correction (Marx's decision): MapReduce's parallel
  compute unit (ADR-002), which this document called "worker"
  generically, is renamed to "compute node" — "Worker" legitimately
  belongs to ADR-019 (a hierarchical-operational concept), distinct
  from the "Ephemeral Agent" (its epistemic definition).
- **c** New link to ADR-017 (sandboxing, drafted in this same session):
  complementary mechanisms — Green Team recovers after a failure,
  ADR-017 prevents the blast radius from the start.

**Changes in v1.7:**
- **a** Added the full AgBOM definition (SBOM/Executive Order 14028
  origin, real JSON example) inside the Blue Team section — the
  document had used the term since v1.0 without ever defining it.
