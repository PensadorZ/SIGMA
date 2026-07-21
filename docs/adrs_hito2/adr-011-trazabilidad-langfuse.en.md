---
id: ADR-011
title: Pipeline Traceability in Langfuse V2
version: 1.6
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-011 v1.5
minimum-references: ADR-003, ADR-005, ADR-007, ADR-009
approved-by: Prof. Marx A. García Delgado
---

# ADR-011: Pipeline Traceability in Langfuse V2

## Executive summary of v1.6 changes

Three corrections (Milestone 2, Rollout 1 close): "worker" renamed to
"compute node" in Fig. 1 and context; Tab. 1 corrected to the real
cost-variant scheme separated from submode; and a verified
implementation note — a real bug found with database evidence
(`client.event()` with no prior `client.trace()` leaves `observations`
orphaned from their corresponding `trace`), already fixed in
`tracing.py`.

## Executive summary of v1.5 changes

The Context section is expanded to first explain that this traceability
is what allows correlating the Policy Server's decisions (ADR-005), the
Blue Team's checks (ADR-003), and the 7D evaluations (ADR-007) under a
single `trace_id` — before getting into the detail of the trace
hierarchy.

## Executive summary of v1.4 changes

Langfuse's Docker image is pinned to the `:2` tag and the `langfuse<3`
constraint is declared in `requirements.txt` as critical constraints:
the self-hosted v2 server lacks an OTLP (OpenTelemetry Protocol)
endpoint, so the v3 SDK (which requires it) is incompatible. Finding
verified during Milestone 1.

---

## Context

Langfuse traceability is the common eye that allows auditing everything
else: without it, the Policy Server's decisions (ADR-005), the Blue
Team's AgBOM checks (ADR-003), and the 7-dimension evaluations
(ADR-007) would exist as isolated events, with no way to correlate them
with each other under a single `trace_id`, nor to reconstruct
afterward what really happened during a run. It is, in that sense, the
short-term audit-memory layer that complements the long-term Epistemic
Memory (ADR-001).

A multi-agent system with no observability is a black box. When a
pipeline fails, one needs to know which tools ran, how many tokens were
consumed, which model ran which subtask, which compute node failed,
and how long each stage took. Langfuse V2 is the chosen observability
backend for being open source and self-hostable.

---

## Decision

Every run emits structured traces to Langfuse V2 following a
consistent, predictable hierarchy.

### Fig. 1 — Full trace hierarchy in Langfuse

```
LEVEL 0 — Parent trace (full pipeline)
  └─ id: {run_id}
  └─ tags: [sigma_variant, sigma_env]
  └─ session_id: {pipeline_run_id}

LEVEL 1 — Parent trace's child spans
  ├─ Span: orchestrator.plan
  ├─ Span: skill.{skill_id}              ← One span per skill
  ├─ Span: red_team_probe                ← Red Team sub-graph
  └─ Artifacts: 7D evaluations (ADR-007)

LEVEL 2 — Children of each skill span
  ├─ Generation: llm.{model_name}        ← LLM call
  ├─ Event: tool.{tool_name}             ← Tool call
  ├─ Event: policy_server.decision       ← Policy Server decision
  │    └─ payload: {verdict, layer, rule, timestamp}
  ├─ Span: blue_team_agbom               ← AgBOM verification
  │    └─ payload: {model_hash, dep_hashes, result}
  └─ Span: mapreduce.compute_node.{n}     ← Individual compute node

LEVEL 3 — Children of each compute-node span
  ├─ Event: tool.{tool_name}
  └─ Generation: llm.{model_name}

CROSS-CUTTING — Policy Server decisions
  Every decision (allowed or blocked) emits an Event at LEVEL 2
  with the active pipeline's same trace_id. This implements the
  auditing intent declared in ADR-005.
```

### Tab. 1 — Trace retention policy by variant

**Corrected (Milestone 2):** separated into the two real axes — cost
variant and submode, previously mixed in the same rows.

| Cost variant | Default retention | Configurable in |
|---|---|---|
| **SIGMA-FE** | 30 days | `docker-compose.yml` |
| **SIGMA-LE** | 30 days | `docker-compose.yml` |
| **SIGMA-ME** | Per Langfuse's cloud plan | Provider configuration |
| **SIGMA-HE** | Per Langfuse's cloud plan | Provider configuration |

**Dev submode (any variant):** 7 days. **Runtime submode:** 90 days
minimum, regardless of the active cost variant.

### Version constraints — Langfuse v2 pinned (critical)

The self-hosted deployment (SIGMA-FE/LE) uses **Langfuse V2**, and its
version must be explicitly pinned on both ends:

```yaml
# docker-compose.yml — NEVER use :latest
services:
  langfuse:
    image: langfuse/langfuse:2        # explicit pin to the v2 series
```

```text
# requirements.txt — critical constraint
langfuse<3
```

**Reason verified in Milestone 1:** the Langfuse v3 SDK requires an
OTLP endpoint the self-hosted v2 server does not expose. Using
`:latest` on the image or installing `langfuse>=3` on the client breaks
traceability silently. Migrating to Langfuse v3 would require deploying
the full v3 server and is out of scope for Milestones 1 and 2.

### Verified implementation note (Milestone 2, Rollout 1 close)

It was detected, with direct database evidence (360 `observations`
saved, only 6 `traces`), that calling `client.event(trace_id=...)`
directly on the Langfuse v2 client **without first creating the trace
via `client.trace(id=...)`** saves the event but leaves the
corresponding row in the `traces` table orphaned — Langfuse's UI lists
from `traces`, not from `observations`, so nothing appeared visible
even though the data was arriving. Fixed in `tracing.py`:
`client.trace(id=trace_id)` (upsert) before `.event()` on that object,
on every emission. Fig. 1's hierarchy describes the correct design;
this finding documents that the code did not follow it until this
fix.

### Last-resort policy for simultaneous outage

If Langfuse is unavailable, events are queued in Redis. If Redis is
also unavailable, events are written to local log files with daily
rotation and 7-day retention in the `sigma_fallback_logs` directory.
The `scripts/reconcile_logs.py` script can be run manually to resend
logs to Langfuse once services are restored. The pipeline **never
fails** due to Langfuse being unavailable.

---

## Positive consequences

- The predictable hierarchy makes debugging systematic: it's always
  known where to look for each type of information.
- Graceful degradation guarantees pipelines don't fail due to Langfuse
  connectivity issues.
- Auditing the Policy Server and the Blue Team in the same system
  eases event correlation.

## Negative consequences

- Langfuse V2 requires an additional PostgreSQL instance in the stack,
  on any self-hosted variant.
- In VPN or restricted-network environments, tunnel configuration can
  be complex.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| LangSmith (LangChain) | Paid service; not self-hostable on any variant |
| OpenTelemetry + Jaeger | Requires more configuration for LLM use cases |
| Flat file logs | Doesn't allow queries or trace correlation |
| W&B Weave | Less suited for agent and tool traces |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added that Policy Server decisions are traced as events
  with the active pipeline's `trace_id`.
- **b.1.2** Specified the trace structure for the Red Team sub-graph
  with the `red_team_probe` tag.
- **c.1.2** Specified the trace structure for the Blue Team with the
  `blue_team_agbom` tag.
- **d.1.2** Added the last-resort policy with a local log when Langfuse
  and Redis are simultaneously down.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the full trace hierarchy in Langfuse,
  detailing every level.
- **b.1.3** Added Tab. 1 with the trace retention policy by variant.

**Changes in v1.4:**
- **a** Pinned Langfuse's Docker image to the `:2` tag (never
  `:latest`) and declared the `langfuse<3` constraint in
  `requirements.txt`, due to the v3 SDK's OTLP incompatibility with the
  self-hosted v2 server. Finding verified during Milestone 1.

**Changes in v1.6 (Milestone 2, Rollout 1 close):**
- **a** "worker" renamed to "compute node" — consistent with ADR-002
  (already corrected in this session).
- **b** Tab. 1 corrected to the 4 real cost-variant levels, separated
  from Dev/Runtime submode.
- **c** Added a verified implementation note about the real
  `client.event()`-without-prior-`client.trace()` bug (orphaned
  observations), already fixed in `tracing.py`.
