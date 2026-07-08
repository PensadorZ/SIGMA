---
id: ADR-005
title: Hybrid Policy Server — Structural and Semantic
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-005 v1.3
minimum-references: ADR-003, ADR-004, ADR-006, ADR-010, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-005: Hybrid Policy Server — Structural and Semantic

## Executive summary of changes in v1.4

The Context section is expanded to first explain what the Policy Server
is and why it exists as an upstream interception point — before a Vibe
Diff (ADR-004) is even generated or the Red/Blue/Green Team (ADR-003)
needs to intervene — before descending into the detail of the two
restriction layers.

## Executive summary of changes in v1.3

Added Fig. 1 with the full interception flow. Added Table 1 with LLM
model assignment by variant. Incorporated the version history.

---

## Context

The Policy Server is the mechanism that decides, at the exact moment an
agent requests to use a tool, whether that call can proceed — before a
Vibe Diff (ADR-004) is even generated, or before the Red/Blue/Green Team
(ADR-003) needs to step in. Without this interception layer at the entry
point, any downstream control (human approval, auditing, security teams)
would always act after the fact, never before the action has already run.

Every tool SIGMA can execute represents a real risk vector. The
constraints needed to govern that risk fall into two fundamentally
different types: structural (deterministic rules, verifiable without
ambiguity — can this role touch this resource in this environment?) and
semantic (requiring real understanding of context — does this call,
even if technically permitted, expose sensitive data or drift from the
user's original intent?). A single layer can't resolve both efficiently:
forcing everything through semantic evaluation would be prohibitive in
latency and cost for the 95% of calls that are trivial to resolve by
rule, while resolving everything by structural rule alone would let
through violations that only contextual judgment can catch.

---

## Decision

Implement a Policy Server in two sequential layers. Every tool call
passes through the structural layer first. Only if it clears that layer
and ambiguity remains does it move to the semantic layer.

### Fig. 1 — Policy Server interception flow

```
Agent requests a tool
        │
        ▼
Did policies.yaml's hash change? ──YES──→ Hot reload (no restart)
        │ NO (or after reload)
        ▼
STRUCTURAL LAYER (policies.yaml)
  Verifies: role, environment, resource
  Latency: < 5 ms
  Covers: 95% of calls
        │
        ├─ BLOCKS ──→ Langfuse event (trace_id) → END
        │
        ├─ ALLOWS (deterministic case) ──→ Langfuse event → Execution
        │
        └─ AMBIGUOUS ──→ SEMANTIC LAYER
                              │
                        Judge LLM (model ≠ Orchestrator)
                        Detects: PII, credentials, intent deviation
                        Verdict: {verdict, confidence, reason, evidence}
                              │
                              ├─ confidence < 0.7 ──→ Escalate to HITL (ADR-004)
                              ├─ BLOCKS ──→ Langfuse event → END
                              └─ ALLOWS ──→ Langfuse event → Execution

Does the Policy Server not respond within 100 ms? ──→ FAIL-CLOSED
  Automatic block + POLICY_SERVER_TIMEOUT in Langfuse
  Exception: SIGMA Dev can configure fail-open in policies.yaml
```

### Table 1 — Judge LLM model assignment by variant and Orchestrator

The semantic judge is **always a different model from the Orchestrator**,
to avoid the conflict of interest where a compromised model judges its
own actions.

| Variant | Orchestrator model | Semantic judge model |
|---|---|---|
| **SIGMA Full** (option A) | Gemini API (free tier) | Local `mistral` via Ollama |
| **SIGMA Full** (option B) | Local Ollama | Gemini API (free tier) |
| **SIGMA Lite** | Gemini Pro | Gemini Flash or another lower-cost model |
| **SIGMA Dev** | Any | Semantic layer disabled (structural only) |
| **SIGMA Runtime** | Depends on environment | Same logic as Full or Lite |

### Policy context for the Red Team subgraph

When the Policy Server detects the `red_team_probe` tag in the LangGraph
context, it applies `red_team_policies.yaml` instead of `policies.yaml`.
This lets the Red Team inject simulated malicious dependencies without
being blocked.

### Hot reload

The Policy Server checks `policies.yaml`'s SHA-256 hash on every
structural evaluation. If it changed, it reloads the full file without
restarting. `allowed_packages.yaml` follows the same mechanism. Changes
take effect immediately on new calls without affecting evaluations
already in progress.

### Slopsquatting prevention

Any request to install a package not present in `allowed_packages.yaml`
is blocked by the structural layer with no semantic evaluation.

---

## Positive consequences

- 95% of calls resolve with minimal latency.
- Separating models removes the conflict of interest.
- `fail-closed` guarantees a downed Policy Server never opens the system up.
- Hot reload avoids interruptions from policy changes.
- Langfuse auditing allows reconstructing any governance decision.

## Negative consequences

- `policies.yaml` must be kept up to date whenever new tools or roles
  are added.
- Hot reload can introduce minimal inconsistencies if the file changes
  while evaluations are in progress (unlikely, given structural
  evaluations take < 5 ms).

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Structural layer only | Doesn't detect semantic violations |
| Semantic layer on every call | Prohibitive latency and cost |
| Validation only at the Orchestrator's input | Doesn't intercept subagents' tools |
| External WAF | Dependencies outside the SIGMA ecosystem |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Declared that the judge LLM must be a different model from
  the Orchestrator.
- **b.1.2** Established `fail-closed` as the default behavior, with a
  configurable exception in SIGMA Dev.
- **c.1.2** Added decision auditing in Langfuse with the active `trace_id`.
- **d.1.2** Specified the relaxed policy context for the Red Team
  subgraph via `red_team_policies.yaml`.
- **e.1.2** Added hot reload of `policies.yaml` and
  `allowed_packages.yaml` via SHA-256 hash.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the full interception flow, including
  `fail-closed` and hot reload.
- **b.1.3** Added Table 1 with judge LLM model assignment by variant and
  Orchestrator model.

**Changes in v1.4:**
- **a** Expanded Context to explain what the Policy Server is and why it
  exists as an upstream interception point, before descending into the
  detail of the two restriction layers.
