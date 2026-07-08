---
id: ADR-011
title: Pipeline Traceability in Langfuse V2
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-011 v1.4
minimum-references: ADR-003, ADR-005, ADR-007, ADR-009
approved-by: Prof. Marx A. García Delgado
---

# ADR-011: Pipeline Traceability in Langfuse V2

## Executive summary of changes in v1.5

The Context section is expanded to first explain that this traceability
is what allows correlating the Policy Server's decisions (ADR-005), the
Blue Team's verifications (ADR-003), and the 7D evaluations (ADR-007)
under a single `trace_id` — before descending into the detail of the
trace hierarchy.

## Executive summary of changes in v1.4

The Langfuse Docker image is pinned to the `:2` tag, and the
`langfuse<3` constraint in `requirements.txt` is declared critical: the
self-hosted v2 server lacks an OTLP (OpenTelemetry Protocol) endpoint,
so the v3 SDK (which requires it) is incompatible. Finding verified
during Milestone 1.

---

## Context

Traceability in Langfuse is the shared eye that makes everything else
auditable: without it, the Policy Server's decisions (ADR-005), the
Blue Team's AgBOM verifications (ADR-003), and the seven-dimension
evaluations (ADR-007) would exist as isolated events, with no way to
correlate them with each other under a single `trace_id`, or to
reconstruct afterward what actually happened during a run. In that
sense, it's the short-term audit-memory layer that complements the
long-term Epistemic Memory of ADR-001.

A multi-agent system with no observability is a black box. When a
pipeline fails, you need to know which tools ran, how many tokens were
consumed, which model executed which subtask, which worker failed, and
how long each stage took. Langfuse V2 is the observability backend of
choice because it's open source and self-hostable.

---

## Decision

Every run emits structured traces to Langfuse V2 following a
consistent, predictable hierarchy.

### Fig. 1 — Full trace hierarchy in Langfuse

```
LEVEL 0 — Parent trace (the full pipeline)
  └─ id: {run_id}
  └─ tags: [sigma_variant, sigma_env]
  └─ session_id: {pipeline_run_id}

LEVEL 1 — Children spans of the parent trace
  ├─ Span: orchestrator.plan
  ├─ Span: skill.{skill_id}              ← One span per skill
  ├─ Span: red_team_probe                ← Red Team subgraph
  └─ Artifacts: 7D evaluations (ADR-007)

LEVEL 2 — Children of each skill span
  ├─ Generation: llm.{model_name}        ← LLM call
  ├─ Event: tool.{tool_name}             ← Tool call
  ├─ Event: policy_server.decision       ← Policy Server decision
  │    └─ payload: {verdict, layer, rule, timestamp}
  ├─ Span: blue_team_agbom               ← AgBOM verification
  │    └─ payload: {model_hash, dep_hashes, result}
  └─ Span: mapreduce.worker.{n}          ← Individual worker

LEVEL 3 — Children of each worker span
  ├─ Event: tool.{tool_name}
  └─ Generation: llm.{model_name}

TRANSVERSAL — Policy Server decisions
  Every decision (allowed or blocked) emits a LEVEL 2 Event with the
  active pipeline's same trace_id. This implements the auditing
  intent declared in ADR-005.
```

### Table 1 — Trace retention policy by variant

| Variant | Default retention | Configurable in |
|---|---|---|
| **SIGMA Full** | 30 days | `docker-compose.yml` |
| **SIGMA Lite** | Per the Langfuse cloud plan | Provider's configuration |
| **SIGMA Dev** | 7 days | `docker-compose.yml` |
| **SIGMA Runtime** | 90 days minimum | `docker-compose.yml` |

### Version constraints — Langfuse v2 pinned (critical)

SIGMA Full's self-hosted deployment uses **Langfuse V2**, and its
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

**Reason verified in Milestone 1:** the Langfuse v3 SDK requires an OTLP
endpoint that the self-hosted v2 server doesn't expose. Using `:latest`
for the image, or installing `langfuse>=3` on the client, silently
breaks traceability. Migrating to Langfuse v3 would require deploying
the full v3 server and is out of scope for Milestones 1 and 2.

### Last-resort policy on simultaneous outage

If Langfuse is unavailable, events are queued in Redis. If Redis is also
unavailable, events are written to local log files with daily rotation
and 7-day retention in the `sigma_fallback_logs` directory. The
`scripts/reconcile_logs.py` script can be run manually to forward the
logs to Langfuse once services are restored. The pipeline **does not
fail** due to Langfuse being unavailable.

---

## Positive consequences

- The predictable hierarchy makes debugging systematic: you always know
  where to look for each type of information.
- Graceful degradation guarantees pipelines don't fail due to Langfuse
  connectivity issues.
- Auditing the Policy Server and the Blue Team in the same system
  simplifies event correlation.

## Negative consequences

- Langfuse V2 requires an additional PostgreSQL instance in the SIGMA
  Full stack.
- In VPN or restricted-network environments, tunnel configuration can be
  complex.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| LangSmith (LangChain) | Paid service; not self-hostable in SIGMA Full |
| OpenTelemetry + Jaeger | Requires more configuration for LLM use cases |
| Flat file logs | Doesn't allow querying or trace correlation |
| W&B Weave | Less suited to agent and tool traces |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added that Policy Server decisions are traced as events with
  the active pipeline's `trace_id`.
- **b.1.2** Specified the trace structure for the Red Team subgraph with
  the `red_team_probe` tag.
- **c.1.2** Specified the trace structure for the Blue Team with the
  `blue_team_agbom` tag.
- **d.1.2** Added the last-resort policy with local logging when
  Langfuse and Redis are both down simultaneously.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the full trace hierarchy in Langfuse,
  detailing every level.
- **b.1.3** Added Table 1 with the trace retention policy by variant.

**Changes in v1.4:**
- **a.1.4** Pinned the Langfuse Docker image to the `:2` tag (never
  `:latest`) and declared the `langfuse<3` constraint in
  `requirements.txt`, due to the v3 SDK's OTLP incompatibility with the
  self-hosted v2 server. Finding verified during Milestone 1.

**Changes in v1.5:**
- **a** Expanded Context to explain that this traceability is what
  allows correlating the Policy Server's decisions (ADR-005), the Blue
  Team's verifications (ADR-003), and the 7D evaluations (ADR-007) under
  a single `trace_id`, before descending into the detail of the trace
  hierarchy.
