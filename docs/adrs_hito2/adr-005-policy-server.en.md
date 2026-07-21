---
id: ADR-005
title: Hybrid Policy Server — Structural and Semantic
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-005 v1.4
minimum-references: ADR-003, ADR-004, ADR-006, ADR-010, ADR-011, ADR-017, ADR-019
approved-by: Prof. Marx A. García Delgado
---

# ADR-005: Hybrid Policy Server — Structural and Semantic

## Executive summary of v1.5 changes

Tab. 1 corrected to the real variant scheme (previously mixed cost and
submode, and never covered `SIGMA-ME`/`HE`). Two new links are added,
verified against ADRs drafted in this same session: `ADR-017` extends
this document's structural layer to the moment a sandbox container
starts up (Zero Ambient Authority / JIT downscoping); `ADR-019` §2.7
uses this same structural layer to validate which MCP servers a Worker
may declare in its Agent Card.

## Executive summary of v1.4 changes

The Context section is expanded to first explain what the Policy Server
is and why it exists as an upstream interception point — before a Vibe
Diff (ADR-004) is even generated or the Red/Blue/Green Team (ADR-003)
needs to step in — before getting into the detail of the two
restriction layers.

## Executive summary of v1.3 changes

Fig. 1 is added with the full interception flow. Tab. 1 is added with
the LLM model assignment by variant. Version history is incorporated.

---

## Context

The Policy Server is the mechanism that decides, at the exact instant
an agent requests to use a tool, whether that call may proceed — before
a Vibe Diff (ADR-004) even gets generated or the Red/Blue/Green Team
(ADR-003) needs to intervene. Without this interception layer at the
entry point, any downstream control (human approval, auditing, security
teams) would always act after the fact, never before the action has
already executed.

Every tool SIGMA can execute represents a real risk vector. The
restrictions needed to govern that risk are of two fundamentally
different types: structural (deterministic rules, unambiguously
verifiable — can this role touch this resource in this environment?)
and semantic (require real contextual understanding — does this call,
even if technically permitted, expose sensitive data or deviate from
the user's original intent?). A single layer cannot efficiently resolve
both: forcing everything through semantic evaluation would be
prohibitive in latency and cost for the 95% of calls that are trivial
to resolve by rule, while resolving everything by structural rule would
let through violations only contextual judgment can detect.

---

## Decision

Implement a Policy Server in two sequential layers. Every tool call
passes through the structural layer first. Only if it passes that layer
and ambiguity remains does it go to the semantic layer.

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
                        LLM judge (model ≠ Orchestrator)
                        Detects: PII, credentials, intent deviation
                        Verdict: {verdict, confidence, reason, evidence}
                              │
                              ├─ confidence < 0.7 ──→ Escalate to HITL (ADR-004)
                              ├─ BLOCKS ──→ Langfuse event → END
                              └─ ALLOWS ──→ Langfuse event → Execution

Policy Server doesn't respond within 100 ms? ──→ FAIL-CLOSED
  Automatic block + POLICY_SERVER_TIMEOUT in Langfuse
  Exception: Dev submode may configure fail-open in policies.yaml
```

### Tab. 1 — Judge LLM model assignment by cost variant

The semantic judge is **always a model different from the
Orchestrator's** to avoid the conflict of interest where a compromised
model judges its own actions. **Corrected (Milestone 2):** the original
table mixed cost (Full/Lite) and submode (Dev/Runtime) in the same
rows, and never explicitly covered `SIGMA-ME`/`SIGMA-HE` — it is
corrected to the 4 real variants, consistent with the mapping already
used across the rest of the project (Orchestrator: `SIGMA-FE`=
Ollama/Gemini free, `SIGMA-LE`=Gemini free, `SIGMA-ME`=Gemini Pro,
`SIGMA-HE`=Vertex AI).

| Variant | Orchestrator model | Semantic judge model |
|---|---|---|
| **SIGMA-FE** (option A) | Gemini API (free tier) | Local `mistral` via Ollama |
| **SIGMA-FE** (option B) | Local Ollama | Gemini API (free tier) |
| **SIGMA-LE** | Gemini API (free tier) | Local `mistral`/`llama3.2` via Ollama |
| **SIGMA-ME** | Gemini Pro | Gemini Flash (lower cost, same provider avoided as sole judge) |
| **SIGMA-HE** | Vertex AI (enterprise) | Gemini Pro or an enterprise model distinct from the Orchestrator's |

**Dev submode (any variant):** semantic layer fully disabled —
structural only, regardless of which models the variant active in
Runtime submode uses. **Runtime submode:** same logic as the table
above, with no additional submode-specific changes.

### Policy context for the Red Team sub-graph

When the Policy Server detects the `red_team_probe` tag in the LangGraph
context, it applies `red_team_policies.yaml` instead of
`policies.yaml`. This lets the Red Team inject simulated malicious
dependencies without being blocked.

### Hot reload

The Policy Server checks `policies.yaml`'s SHA-256 hash on every
structural evaluation. If it changed, it reloads the full file without
restarting. `allowed_packages.yaml` follows the same mechanism. Changes
take effect immediately on new calls without affecting evaluations
already in progress.

### Slopsquatting prevention

Any package-installation request not present in `allowed_packages.yaml`
is blocked by the structural layer without semantic evaluation.

### New links (Milestone 2)

**With ADR-017 (sandboxing):** this document's structural layer is not
limited to runtime tool calls — `ADR-017` §2.3 extends it to the moment
an ephemeral container starts up: the Policy Server reads the
generated skill/Worker's `defaults.yaml` and issues the ultra-short-lived
credential (Zero Ambient Authority). It is the same mechanism, applied
one moment earlier.

**With ADR-019 (declarative MCP):** when a Worker declares
`mcp_servers` in its Agent Card (`ADR-019` §2.7), it is this same
structural layer that validates that list against what the Director's
mandate authorized — not a separate validation mechanism.

---

## Positive consequences

- 95% of calls are resolved with minimal latency.
- Separating models removes the conflict of interest.
- `fail-closed` guarantees a downed Policy Server never opens up the
  system.
- Hot reload avoids interruptions from policy changes.
- Langfuse auditing allows reconstructing any governance decision.

## Negative consequences

- `policies.yaml` must be kept up to date whenever new tools or roles
  are added.
- Hot reload can introduce minor inconsistencies if the file changes
  while evaluations are in progress (unlikely given structural
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
- **a.1.2** Declared that the judge LLM must be a model different from
  the Orchestrator's.
- **b.1.2** Established `fail-closed` as the default behavior with a
  configurable exception in Dev submode.
- **c.1.2** Added decision auditing in Langfuse with the active
  `trace_id`.
- **d.1.2** Specified the relaxed-policy context for the Red Team
  sub-graph via `red_team_policies.yaml`.
- **e.1.2** Added hot reload of `policies.yaml` and
  `allowed_packages.yaml` via SHA-256 hash.

**Changes in v1.3:**
- **a** Added Fig. 1 with the full interception flow including
  `fail-closed` and hot reload.
- **b** Added Tab. 1 with the judge LLM model assignment by variant and
  Orchestrator model.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** Tab. 1 corrected to the real scheme of 4 cost variants
  (`SIGMA-FE/LE/ME/HE`), separated from submode (Dev/Runtime) — the
  previous version never explicitly covered ME/HE.
- **b** Added links with ADR-017 (JIT downscoping as an extension of
  this structural layer) and ADR-019 (validation of `mcp_servers`
  declared by Workers).
