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

## Executive summary of v1.6 changes

Four corrections (Milestone 2, Rollout 1 close): `node_hitl_wait`
updated from `orchestrator.py` (archived) to
`sigma/core/engineer_datos.py` (real post-Rollout 1 code); Tab. 2
corrected to the real cost-variant scheme separated from submode;
`INSTALL.md` reference corrected (doesn't exist yet, see ADR-010 v1.5);
and an unresolved verification note: the real `.env` seen in this
session uses a single Zulip topic, not the RUNS/HITL pair this document
describes — flagged for Marx to confirm, not corrected unilaterally.

## Executive summary of v1.5 changes

The primary HITL pause/resume mechanism is updated to the one verified
in Milestone 1: **LangGraph `interrupt()` + `SqliteSaver` checkpointer**,
with `webhook_receiver.py` invoking `resume_pipeline()` by `trace_id`.
The Redis polling from the v1.4 design is documented as a historical
fallback: the real implementation showed the polling approach was
architecturally inferior to LangGraph's native checkpointing. The
separation of Zulip topics (`RUNS`/`HITL`) and the automatic HITL
trigger when `pct_unclear > 30%` are documented. Appendix A is
completed, moving from a theoretical comparison to a verified
implementation status.

---

## Context

A system that can execute code, modify databases, and deploy models
represents a real risk if a destructive action runs without human
oversight. The concrete risks are: an LLM overestimating its confidence
and executing an irreversible action, a malicious prompt impersonating
user intent, and the absence of a chain of custody that makes
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
node_hitl_wait node runs interrupt()          ← v1.5 MECHANISM
  └─ LangGraph pauses the graph
  └─ SqliteSaver persists the full state with the trace_id
  └─ Notification to the operator via Zulip (HITL topic)
        │
        ▼
Operator responds (Zulip / HTTP POST to the webhook)
        │
        ▼
webhook_receiver.py → resume_pipeline(trace_id, decision)
  └─ LangGraph restores the state from the checkpoint
  └─ The graph continues exactly where it paused
        │
        ├─ [REJECT] → Vibe Diff marked REJECTED → END
        │
        ▼
Did policies change since approval?
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
- `node_hitl_wait` — the graph node that runs `interrupt()` when an
  action requires approval. The process can even terminate: the state
  survives in the checkpoint. **Corrected (Milestone 2):** in Milestone
  1 it lived in `orchestrator.py` (now archived as
  `orchestrator_hito1_v1.0.py`); after Rollout 1 it lives inside
  `sigma/core/engineer_datos.py` — each Engineer handles its own HITL,
  not a single monolithic orchestrator (a decision already formalized
  in ADR-016).
- `webhook_receiver.py` — a lightweight HTTP process that receives the
  operator's decision and calls `resume_pipeline(trace_id, decision)`
  to resume the paused graph from its exact checkpoint.

**Why it replaces Redis polling (v1.4 design):** polling kept the
Orchestrator alive consuming a thread, did not survive process
restarts, and duplicated state LangGraph already manages natively.
`interrupt()` + checkpointer consumes no resources while waiting,
survives restarts, and uses the framework's idiomatic mechanism. Redis
retains its other roles (Assumption Graph queues ADR-001, `chain`
buffer ADR-002, Langfuse event queue ADR-011).

### Notifications — Zulip with separate topics

| Topic (`.env` variable) | Content |
|---|---|
| `ZULIP_TOPIC_RUNS` | Execution events: pipeline start, end, failures |
| `ZULIP_TOPIC_HITL` | Approval requests pending human response |

**Verification note, not resolved on my own:** the real `.env` I have
seen in this session only has `ZULIP_TOPIC=hitl-approvals` (a single
topic, not the separate `RUNS`/`HITL` pair this document describes) —
it may be that the design is correct and the `.env` simply hasn't been
updated yet to use both variables, or that, in practice, it was decided
not to split the topics. I am not changing this myself — verify it
against your real `.env` before assuming which of the two is current.

The separation prevents approval requests from being lost among the
noise of execution events. `zulip_notifier.py` operates silently if the
variables aren't configured and degrades to a local log without
interrupting the pipeline.

### Automatic HITL trigger by quality

When the `0008-sentiment-analyzer` skill reports `pct_unclear > 30%` in
a batch, the Orchestrator automatically triggers an HITL alert via
Zulip: such a high percentage of `UNCLEAR` classifications (ADR-008)
indicates out-of-distribution data and requires a human decision before
continuing.

### Tab. 1 — Approval levels

| Level | Criterion | Vibe Diff | Approval required |
|---|---|---|---|
| **LOW** | Reversible, no impact on `_prod` | Not required | Enter in the console |
| **MEDIUM** | Reversible, >1,000 rows or with PII | Required | HITL via `interrupt()` |
| **HIGH** | Irreversible or impacts `_prod` | Required + persistent | HITL + MFA |
| **CRITICAL** | Deployment or mass deletion | Required + maximum retention | HITL + hardware MFA (recommended) |

### Tab. 2 — Approval channel authentication by variant

**Corrected (Milestone 2):** separated into the two real axes — cost
variant and submode, previously mixed in the same rows.

| Cost variant | Authentication |
|---|---|
| **SIGMA-FE** | Static `APPROVAL_TOKEN` token in `.env` |
| **SIGMA-LE** | Static `APPROVAL_TOKEN` token in `.env` |
| **SIGMA-ME** | TOTP or the cloud provider's mechanism |
| **SIGMA-HE** | TOTP or the cloud provider's mechanism, with hardware MFA recommended |

Dev submode (any variant): no authentication, console confirmation.
Runtime submode: TOTP with a Fernet-encrypted seed (ADR-010),
regardless of the active cost variant.

The wait timeout is configured via `APPROVAL_TIMEOUT_SECONDS` (default
`300`). With the checkpointer, an expired timeout cancels the action
but the paused state is kept for audit.

### STALE Vibe Diff

If the Policy Server detects that policies changed between approval and
execution: it blocks execution, marks the Vibe Diff as `STALE` in
MinIO, notifies the operator with the reason, and requires a new full
cycle.

### Integration with the Green Team

Green Team recovery actions of `MEDIUM` impact or higher generate their
own Vibe Diff with the exact code diff. Those of `LOW` impact are
applied automatically without a Vibe Diff.

### Lifecycle of a failed pipeline

Partial results are kept in MinIO marked as `PARTIAL`. With the
`SqliteSaver` checkpointer, resuming from the last checkpoint is
native: `resume_pipeline(trace_id)`. If there is no action within seven
days, the pipeline is archived automatically.

---

## Positive consequences

- The Vibe Diff chain of custody in MinIO enables full auditing.
- The `interrupt()` + checkpointer mechanism consumes no resources
  while waiting and survives process restarts — verified in Milestone
  1.
- Differentiated levels prevent alert fatigue.
- Separating Zulip topics keeps approvals from getting lost among
  execution events.

## Negative consequences

- HIGH and CRITICAL actions block the pipeline until the operator
  responds.
- The SQLite checkpointer adds a local state file that must be
  excluded from the repository (`.gitignore`).
- If `webhook_receiver.py` is not active, the operator's decisions
  don't reach the paused graph; the system reports
  `WEBHOOK_RECEIVER_UNAVAILABLE`.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Redis polling every 5s (v1.4 design) | Consumes a permanent thread; doesn't survive restarts; duplicates state LangGraph manages natively. Replaced after verification in Milestone 1 |
| Console-only approval | Generates no auditable chain of custody |
| LLM confidence threshold | A compromised LLM can overestimate its own confidence |
| Email-only notifications | Doesn't guarantee low latency |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Declared the canonical order: Policy Server → Vibe Diff →
  approval → execution.
- **b.1.2** Specified behavior on a `STALE` Vibe Diff.
- **c.1.2** Integrated the Green Team into the approval flow.
- **d.1.2** Specified the Approval Endpoint as a separate process with
  Redis polling.
- **e.1.2** Added MFA management via TOTP with an encrypted seed.
- **f.1.2** Added the lifecycle of a failed pipeline.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the full canonical flow.
- **b.1.3** Added Tab. 1 with the approval levels.
- **c.1.3** Added Tab. 2 with authentication by variant.
- **d.1.3** Made the timeout configurable via
  `APPROVAL_TIMEOUT_SECONDS`.

**Changes in v1.4:**
- **a.1.4** Added Appendix A with the polling-versus-webhooks
  comparison.

**Changes in v1.5:**
- **a** Updated the primary HITL mechanism to the one verified in
  Milestone 1: LangGraph `interrupt()` + `SqliteSaver`, with
  `webhook_receiver.py` and `resume_pipeline()` by `trace_id`. Redis
  polling moves to Alternatives Considered with the justification for
  the replacement.
- **b** Updated Fig. 1 with the real pause/resume flow.
- **c** Documented the Zulip topic separation (`ZULIP_TOPIC_RUNS` /
  `ZULIP_TOPIC_HITL`).
- **d** Added the automatic HITL trigger when `pct_unclear > 30%` in
  skill 0008.
- **e** Completed Appendix A with the full configuration block and the
  real implementation status of each mechanism.

---

## Appendix A — Notification and resumption mechanisms (verified status)

In v1.4 this appendix compared Redis polling against webhooks as
theoretical alternatives. After Milestone 1, the status is one of
verified implementation.

### Tab. A.1 — Mechanisms: implementation status after Milestone 1

| Mechanism | Status | Current role |
|---|---|---|
| **LangGraph `interrupt()` + SqliteSaver** | ✅ Implemented and verified | Primary graph pause/resume mechanism |
| **Webhook (`webhook_receiver.py`)** | ✅ Implemented and verified | Entry channel for the operator's decision; invokes `resume_pipeline(trace_id)` |
| **Zulip (RUNS/HITL topics)** | ✅ Implemented (`zulip_notifier.py`) | Operator notification; degrades to a local log if not configured |
| **Redis polling** | ⛔ Replaced | Discarded as the HITL mechanism; Redis retains its other roles (ADR-001, ADR-002, ADR-011) |

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
  MEDIUM-level or higher actions. **Corrected (Milestone 2):**
  `INSTALL.md` still doesn't exist as a file (confirmed against the
  updated `README.md`) — today activation is manual (`uvicorn` +
  `ngrok` in two terminals, documented in `ESTRUCTURA_PROYECTO.md`).
  The automated startup script is left for when `INSTALL.md` is
  written, at Rollout 3's close (see ADR-010 v1.5).
- Webhook authentication uses `APPROVAL_TOKEN` (SIGMA-FE/LE) or TOTP
  (Runtime submode) per Tab. 2.
- In firewalled or VPN environments, the webhook operates on localhost
  with no external exposure: the operator responds via Zulip and the
  local Zulip connector forwards to the webhook.

**Changes in v1.6 (Milestone 2, Rollout 1 close):**
- **a** `node_hitl_wait` updated to its real post-Rollout 1 location
  (`engineer_datos.py`, not `orchestrator.py`).
- **b** Tab. 2 corrected to the 4 real cost-variant levels, separated
  from Dev/Runtime submode.
- **c** `INSTALL.md` reference corrected — it doesn't exist yet.
- **d** Added a verification note about the discrepancy between the
  Zulip topic design (separate RUNS/HITL) and the observed real `.env`
  (a single topic) — unresolved, pending confirmation.
