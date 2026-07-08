---
id: ADR-004
title: Persistent Vibe Diff and Human-in-the-Loop with MFA
version: 1.6
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-004 v1.5
minimum-references: ADR-003, ADR-005, ADR-010, ADR-011
approved-by: Prof. Marx A. García Delgado
file-name: adr-004-vibe-diff-mfa.md
---

# ADR-004: Persistent Vibe Diff and Human-in-the-Loop with MFA

## Executive summary of changes in v1.6

The Context section is expanded to first explain what the Vibe Diff +
HITL with MFA mechanism is and why it exists in the ecosystem — as the
necessary closure to the autonomy ADR-001 and ADR-002 enable, preventing
an agent's error from becoming irreversible damage without human
intervention — before descending into the specific risk details.

## Executive summary of changes in v1.5

The primary HITL pause/resume mechanism is updated to the one verified
in Milestone 1: **LangGraph `interrupt()` + the `SqliteSaver`
checkpointer**, with `webhook_receiver.py` invoking `resume_pipeline()`
by `trace_id`. The Redis polling from the v1.4 design is documented as a
historical fallback: the real implementation showed that the polling
approach was architecturally inferior to LangGraph's native
checkpointing. The separation of Zulip topics (`RUNS`/`HITL`) and the
automatic HITL trigger when `pct_unclear > 30%` are documented. Appendix
A is completed, moving from a theoretical comparison to a verified
implementation status.

---

## Context

SIGMA delegates to autonomous agents actions that modify real data, run
code, and can deploy changes to production — precisely the autonomy
ADR-001 and ADR-002 make possible. That autonomy, without an explicit
human-approval mechanism, would turn any agent error into irreversible
damage before anyone could step in. The persistent Vibe Diff and the
Human-in-the-Loop (HITL) cycle with multi-factor authentication are the
mechanism that closes that gap: no medium- or high-impact action
executes without leaving an auditable record of what was about to
happen, and without a human explicitly confirming it should proceed.

A system that can run code, modify databases, and deploy models poses a
real risk if a destructive action executes without human oversight. The
concrete risks are: an LLM overestimating its own confidence and
executing an irreversible action, a malicious prompt impersonating the
user's intent, and the absence of a chain of custody that makes
after-the-fact auditing impossible.

Milestone 1 provided real implementation evidence: the polling-based
pause mechanism specified in v1.4 was built, evaluated, and replaced by
LangGraph's native mechanism, which proved simpler, more robust, and
consumed no CPU while waiting.

---

## Decision

### Fig. 1 — Canonical approval flow for MEDIUM-level or higher actions

```
Skill requests an action
        │
        ▼
Structural Policy Server ──→ [BLOCKS] ──→ Langfuse log → END
        │ ALLOWS
        ▼
Semantic Policy Server ──→ [BLOCKS] ──→ Langfuse log → END
        │ ALLOWS
        ▼
Orchestrator generates a Vibe Diff (JSON) → persists to MinIO (WORM)
        │
        ▼
node_hitl_wait node executes interrupt()          ← v1.5 MECHANISM
  └─ LangGraph pauses the graph
  └─ SqliteSaver persists the full state with the trace_id
  └─ Operator notification via Zulip (HITL topic)
        │
        ▼
Operator responds (Zulip / HTTP POST to the webhook)
        │
        ▼
webhook_receiver.py → resume_pipeline(trace_id, decision)
  └─ LangGraph restores the state from the checkpoint
  └─ The graph continues exactly where it paused
        │
        ├─ [REJECTS] → Vibe Diff marked REJECTED → END
        │
        ▼
Have policies changed since approval?
        ├─ [YES] → Vibe Diff marked STALE → back to the start
        ▼
Action execution
```

### Pause/resume mechanism — LangGraph `interrupt()` + SqliteSaver

**This is the primary mechanism verified in Milestone 1** (65/65 tests,
functional HITL confirmed). Components:

- `core/checkpointer.py` — configures `SqliteSaver` as the graph's
  checkpointer. The pipeline's full state is persisted to SQLite at
  every step.
- `node_hitl_wait` in `orchestrator.py` — a graph node that executes
  `interrupt()` when an action requires approval. The process can even
  terminate: the state survives in the checkpoint.
- `webhook_receiver.py` — a lightweight HTTP process that receives the
  operator's decision and calls `resume_pipeline(trace_id, decision)` to
  resume the paused graph from its exact checkpoint.

**Why it replaces Redis polling (v1.4 design):** polling kept the
Orchestrator alive consuming a thread, didn't survive process restarts,
and duplicated state LangGraph already manages natively. `interrupt()` +
checkpointer consumes no resources while waiting, survives restarts, and
uses the framework's idiomatic mechanism. Redis keeps its other roles
(Assumption Graph queues from ADR-001, the `chain` buffer from ADR-002,
Langfuse's event queue from ADR-011).

### Notifications — Zulip with separate topics

| Topic (`.env` variable) | Content |
|---|---|
| `ZULIP_TOPIC_RUNS` | Execution events: pipeline start, end, failures |
| `ZULIP_TOPIC_HITL` | Approval requests awaiting a human response |

The separation prevents approval requests from getting lost among
execution-event noise. `zulip_notifier.py` operates in silent mode if
the variables aren't configured and degrades to a local log without
interrupting the pipeline.

### Automatic HITL trigger for quality

When the `0008-sentiment-analyzer` skill reports `pct_unclear > 30%` on
a batch, the Orchestrator automatically fires an HITL alert via Zulip: a
percentage that high of `UNCLEAR` classifications (ADR-008) indicates
out-of-distribution data and requires a human decision before continuing.

### Table 1 — Approval levels

| Level | Criterion | Vibe Diff | Approval required |
|---|---|---|---|
| **LOW** | Reversible, no impact on `_prod` | Not required | Console Enter |
| **MEDIUM** | Reversible, >1,000 rows or with PII | Required | HITL via `interrupt()` |
| **HIGH** | Irreversible or impacts `_prod` | Required + persistent | HITL + MFA |
| **CRITICAL** | Deployment or bulk deletion | Required + maximum retention | HITL + hardware MFA (recommended) |

### Table 2 — Approval channel authentication by variant

| Variant | Authentication |
|---|---|
| **SIGMA Full** | Static `APPROVAL_TOKEN` in `.env` |
| **SIGMA Lite** | TOTP or the cloud provider's mechanism |
| **SIGMA Dev** | No authentication, console confirmation |
| **SIGMA Runtime** | TOTP with a Fernet-encrypted seed (ADR-010) |

The wait timeout is configured with `APPROVAL_TIMEOUT_SECONDS` (default
`300`). With the checkpointer, an expired timeout cancels the action but
the paused state is kept for auditing.

### STALE Vibe Diff

If the Policy Server detects that policies changed between approval and
execution: it blocks execution, marks the Vibe Diff as `STALE` in MinIO,
notifies the operator with the reason, and requires a full new cycle.

### Integration with the Green Team

Green Team recovery actions with `MEDIUM` impact or higher generate
their own Vibe Diff with the exact code diff. `LOW`-impact ones are
applied automatically with no Vibe Diff.

### Lifecycle of a failed pipeline

Partial results are kept in MinIO marked `PARTIAL`. With the
`SqliteSaver` checkpointer, resuming from the last checkpoint is native:
`resume_pipeline(trace_id)`. If there's no action within seven days, the
pipeline is automatically archived.

---

## Positive consequences

- The chain of custody of Vibe Diffs in MinIO enables full auditing.
- The `interrupt()` + checkpointer mechanism consumes no resources while
  waiting and survives process restarts — verified in Milestone 1.
- The differentiated levels prevent alert fatigue.
- Separating Zulip topics prevents approvals from getting lost among
  execution events.

## Negative consequences

- HIGH and CRITICAL actions block the pipeline until the operator responds.
- The SQLite checkpointer adds a local state file that must be excluded
  from the repository (`.gitignore`).
- If `webhook_receiver.py` isn't active, the operator's decisions don't
  reach the paused graph; the system reports `WEBHOOK_RECEIVER_UNAVAILABLE`.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Redis polling every 5s (v1.4 design) | Consumes a permanent thread; doesn't survive restarts; duplicates state LangGraph already manages natively. Replaced after verification in Milestone 1 |
| Console-only approval | Produces no auditable chain of custody |
| LLM confidence threshold | An impersonated LLM can overestimate its own confidence |
| Email notifications only | Doesn't guarantee low latency |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Declared the canonical order: Policy Server → Vibe Diff →
  approval → execution.
- **b.1.2** Specified the behavior on a `STALE` Vibe Diff.
- **c.1.2** Integrated the Green Team into the approval flow.
- **d.1.2** Specified the Approval Endpoint as a separate process with
  Redis polling.
- **e.1.2** Added MFA management via TOTP with an encrypted seed.
- **f.1.2** Added the lifecycle of a failed pipeline.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the full canonical flow.
- **b.1.3** Added Table 1 with the approval levels.
- **c.1.3** Added Table 2 with authentication by variant.
- **d.1.3** Made the timeout configurable via `APPROVAL_TIMEOUT_SECONDS`.

**Changes in v1.4:**
- **a.1.4** Added Appendix A with the polling-versus-webhooks comparison.

**Changes in v1.5:**
- **a.1.5** Updated the primary HITL mechanism to the one verified in
  Milestone 1: LangGraph `interrupt()` + `SqliteSaver`, with
  `webhook_receiver.py` and `resume_pipeline()` by `trace_id`. Redis
  polling moves to Alternatives Considered with the justification for
  its replacement.
- **b.1.5** Updated Fig. 1 with the real pause/resume flow.
- **c.1.5** Documented the separation of Zulip topics
  (`ZULIP_TOPIC_RUNS` / `ZULIP_TOPIC_HITL`).
- **d.1.5** Added the automatic HITL trigger when `pct_unclear > 30%` in
  skill 0008.
- **e.1.5** Completed Appendix A with the full configuration block and
  the real implementation status of each mechanism.

**Changes in v1.6:**
- **a** Expanded Context to explain what the Vibe Diff + HITL with MFA
  mechanism is and why it exists in the ecosystem, before descending
  into the specific risk details.

---

## Appendix A — Notification and resume mechanisms (verified status)

In v1.4 this appendix compared Redis polling against webhooks as
theoretical alternatives. After Milestone 1, the status is verified
implementation.

### Table A.1 — Mechanisms: implementation status after Milestone 1

| Mechanism | Status | Current role |
|---|---|---|
| **LangGraph `interrupt()` + SqliteSaver** | ✅ Implemented and verified | Primary graph pause/resume mechanism |
| **Webhook (`webhook_receiver.py`)** | ✅ Implemented and verified | Entry channel for the operator's decision; invokes `resume_pipeline(trace_id)` |
| **Zulip (RUNS/HITL topics)** | ✅ Implemented (`zulip_notifier.py`) | Operator notification; degrades to a local log if not configured |
| **Redis polling** | ⛔ Replaced | Discarded as the HITL mechanism; Redis keeps its other roles (ADR-001, ADR-002, ADR-011) |

### Approval channel configuration

```yaml
# policies.yaml
approval:
  notification_mechanism: webhook       # webhook (default since v1.5) | zulip_only
  webhook_url: http://localhost:8765/approve-webhook
  webhook_timeout_ms: 2000
  webhook_retries: 3
  zulip_topic_runs: ${ZULIP_TOPIC_RUNS}
  zulip_topic_hitl: ${ZULIP_TOPIC_HITL}
  approval_timeout_seconds: ${APPROVAL_TIMEOUT_SECONDS}   # default: 300
  auto_hitl_unclear_threshold: 0.30     # pct_unclear > 30% triggers HITL
```

### Operating conditions

- `webhook_receiver.py` must be active before running pipelines with
  MEDIUM-level or higher actions. INSTALL.md's startup script launches
  it together with the Docker infrastructure. In Milestone 1, however,
  these activations are done manually.
- Webhook authentication uses the `APPROVAL_TOKEN` (Full) or TOTP
  (Runtime) per Table 2.
- In firewalled or VPN environments, the webhook operates on localhost
  with no external exposure: the operator responds via Zulip, and the
  local Zulip connector forwards to the webhook.
