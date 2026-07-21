---
id: ADR-017
title: Execution Sandboxing for Dynamically Generated Code and Workers
version: 1.3
status: Accepted
original-date: 2026-07
revision-date: 2026-07
supersedes: none
minimum-references: ADR-003, ADR-005, ADR-008, ADR-014, ADR-016, ADR-019
approved-by: Prof. Marx A. García Delgado
---

# ADR-017: Execution Sandboxing for Dynamically Generated Code and Workers

## Executive summary of v1.2 changes

The prior version was correct in its decision but weak in its
reasoning — it did not explain *why* each configuration parameter was
necessary, it only declared it. This version deepens the reasoning
against Day 4 of the Google-Kaggle course (Pillar 1 and Pillar 5 of the
7-pillar agentic security framework): it adds the direct parallel
between the course's "vibe loop" and ADR-014's dynamic generation; it
formally names the "Zero Ambient Authority" principle behind JIT
downscoping; it adds two mechanisms that were completely missing
(network isolation — why "none" and not an allowlist — and
deny-by-default file allowlists); and it documents that ADR-003's
Red/Blue/Green model independently coincides with Pillar 6 of the same
course — cross-validation of the already-existing design, not a new
idea.

## Executive summary

This ADR formalizes execution isolation (sandboxing) for the only two
sources of code SIGMA can produce without direct human authorship:
dynamically generated skills (`ADR-014`) and Workers (`ADR-019`
§2.1ter). It existed in prior iterations of the project (Docker/gVisor
containers) but did not survive consolidation into the original 16
ADRs — it is recovered here, formally, as a mandatory entry condition
for Rollout 3 (`ADR-016` Tab. 2). **It does not apply retroactively to
Rollout 1's 7 Engineer Data skills** — all of human authorship, reviewed
before being integrated; the risk this ADR contains is specifically
that of code the system itself writes without that prior review step.

---

## Context

`ADR-003` already covers security at three moments — before (Red
Team), during (Blue Team), after a failure (Green Team) — but none of
the three **prevents** a failure from having a wide blast radius from
the start. Green Team isolates *after* detecting a problem; the Policy
Server (`ADR-005`) validates *before* a tool is invoked. Neither
contains the *execution itself* while it happens — if a dynamically
generated skill has a real bug (not necessarily malicious, simply
defective), today nothing stops it from, for example, writing outside
its designated tables or consuming unbounded memory before any other
mechanism notices.

This risk was theoretical until Rollout 1 — now it is concrete:
`ADR-014` is already approved at the design level (code the Orchestrator
writes and executes with real authority), and `ADR-019` introduces
Workers that are born and die within a single run. Both are, by design,
code without the same human-review history the 7 current skills have —
exactly the scenario ADR-014 itself describes as "the ecosystem's
highest-risk one."

**Verified against Day 4 of the Google-Kaggle course (Pillar 1,
"Sandboxes and Supply Chain Defence"):** the course material itself
describes SIGMA's dynamic-generation mechanism (ADR-014) almost word
for word — an agent that writes a script, runs it, reads the error, and
rewrites the logic until it works (the "vibe loop"). That process is,
by nature, highly variable — the resulting code cannot be implicitly
trusted just because it compiled without errors. The course is explicit
that running that code directly alongside the root agent, or on the
host's standard infrastructure, introduces an unacceptable level of
risk — matching, point by point, why this ADR exists.

---

## Decision

### 2.1 — Scope: what code is sandboxed, what isn't

| Code | Sandboxed? | Why |
|---|---|---|
| Engineer Data's 7 skills (Rollout 1) | Not for now | Human authorship, reviewed before integration — same trust level as the rest of the project's code |
| Dynamically generated skills (`ADR-014`) | **Yes, mandatory** | No human review prior to their first test execution (Green Team, ADR-014 step 5) |
| Workers (`ADR-019` §2.1ter) | **Yes, mandatory** | Born with no history — `trust_level` always `1` on creation (ADR-019 §2.1bis) |
| Future Engineer Models/Auditor skills (Rollout 2/3) | No, if of human authorship like the current ones | Same criterion as row 1 — sandboxing depends on *how the code originated*, not *which Engineer* runs it |

### 2.2 — Mechanism: low-privilege ephemeral container, with full state reset

Every execution of code within the scope of 2.1 runs in a disposable
Docker container. **The requirement isn't just "isolate" — it's that
the container block direct host access and fully reset its state
between runs, without exception** (verified against Day 4, "Ephemeral
Sandboxing and State Management"): even if the generated code has a
severe vulnerability or is manipulated toward a container-escape
attempt, that compromised logic cannot persist or affect the real node
while the agent keeps iterating. This is what justifies
`lifetime: single_execution` — it is not a design preference, it is the
condition that makes ADR-014's dynamic generation loop itself safe.

```yaml
# sigma/core/sandbox_config.yaml (new, to be built upon implementation)
sandbox:
  runtime: docker            # gVisor (runsc) optional for SIGMA-ME/HE, see 2.4
  network: none              # no network access, except an explicit allowlist (ADR-005) — see 2.3bis for why "none" and not an allowlist
  memory_limit: "512m"
  cpu_limit: "1.0"
  filesystem: read_only_root # only /tmp/{run_id} is writable, ephemeral
  filesystem_allowlist: []   # deny-by-default — see 2.3ter
  lifetime: single_execution # the container is destroyed on completion, without exception, with a full state reset
```

The container is **always** destroyed when execution ends, whether
successful or not — there is no persistent state between runs of the
same generated skill, not even for debugging (the log is already
emitted via `tracing.py` before destruction).

**Real correction (at Marx's request, a gap that had been left open):**
"ending execution" does not mean "the Worker's process returned" — it
means **"the Director confirmed, via its own Ag-DR (ADR-018), that the
result has already been written."** If the container were destroyed on
the process's first return, a failure between "the Worker computed the
result" and "the result was written with the JIT credential" would lose
it forever, with nothing to recover. Correct sequence:

```
Worker computes result → writes with JIT credential (2.3)
        │
        ▼
Director receives write confirmation (via A2A, ADR-019 §2.6)
        │
        ▼
Director generates its Ag-DR documenting the Worker's activity (ADR-018)
        │
        ▼
ONLY THEN: container is destroyed
```

**Exception — Workers with `trust_level ≥ 2` (ADR-019 §2.1bis):** the
container is not destroyed between tasks of the same Worker type, it is
kept warm (same network/memory/filesystem limits, none relaxed) —
reducing the real container-startup overhead this same ADR flags as a
negative consequence. This **does not** take the Worker out of the
sandbox — containment stays active, it only avoids destroying and
recreating the container between uses of the same, already-verified
Worker type, per its Ag-DR history.

```yaml
sandbox:
  # ... rest of the configuration unchanged ...
  lifetime_policy: single_execution  # trust_level 1: destroyed after write confirmation
                                       # trust_level >= 2: kept warm between tasks of the same type
```

### 2.3 — Zero Ambient Authority and ultra-short-lived credentials (JIT downscoping)

Verified against Day 4 (Pillar 5, IAM): the formal principle governing
this is called **Zero Ambient Authority** — an agent executing
generated code **never** inherits the full administrative privileges of
whoever invoked it. Instead, the container receives fresh credentials,
explicitly scoped to the exact data sources that specific script needs
— never the parent agent's broad permissions.

```
Policy Server (ADR-005, structural layer)
        │
        ▼
Reads the generated skill's defaults.yaml → determines what permissions it declares
        │
        ▼
Issues a credential whose lifetime = the container's duration, never longer
        │
        ▼
Container starts with ONLY that credential, never the full .env
```

This is not a new, isolated mechanism — it is a direct extension of
what the Policy Server (`ADR-005`) already does at its structural
layer, applied at container startup instead of only at each tool call.
Credentials expire at the exact moment the task concludes — there is no
grace period.

**Link to the "Confused Deputy" problem** (the same problem that already
motivated ADR-016's design for Director↔Engineer routing): Day 4
describes it as Pillar 5's central risk — an over-privileged agent can
be induced to run unauthorized commands. Zero Ambient Authority is the
direct mitigation: if the container never had broad permissions to
inherit, there's nothing an attack of this kind can exploit beyond what
that specific script could already touch.

### 2.3bis — Network isolation: why "none," not an allowlist

Verified against Day 4 (Pillar 1, egress governance): an allowlist of
approved domains **is not enough** — it does not protect against
indirect prompt injections hidden in third-party pages the agent itself
decides to visit. That is why `network: none` is the correct default in
2.2, not a per-skill configurable allowlist. If a dynamically generated
skill needs external data, it must go through an offline cache or a
pre-sanitized access service — never direct internet access from inside
the sandbox.

### 2.3ter — Allowed-file lists, deny-by-default

Verified against Day 4 (Pillar 5): in addition to network isolation,
the container's filesystem operates with explicitly allowed file lists
(`filesystem_allowlist`, see 2.2) — never a blocklist. By default,
everything is denied except what the generated skill's `defaults.yaml`
declares it needs — the same principle as ADR-006 (never hardcode,
always declare explicitly), applied here to file paths instead of
environment variables. This specifically blocks access to secrets,
build scripts, and production manifests unrelated to the skill's task.

### 2.4 — Runtime by cost variant

| Variant | Sandbox runtime |
|---|---|
| `SIGMA-FE` | Standard Docker with resource limits (2.2) — $0, no additional dependencies |
| `SIGMA-LE` / `SIGMA-ME` | Standard Docker, same as FE |
| `SIGMA-HE` | Docker + optional gVisor (`runsc`) — additional kernel isolation for those who need it; not a requirement, an available hardening option |

gVisor is not required in any variant — Docker with resource limits is
already the real, sufficient mechanism for the risk described in 2.1;
gVisor remains optional hardening, consistent with not requiring paid
infrastructure in SIGMA-FE.

### 2.5 — Link to Green Team (ADR-003)

If code inside the sandbox fails, ADR-003's sequence keeps applying
unchanged (snapshot → isolation → `code-reviewer` → Vibe Diff if impact
is MEDIUM/HIGH) — the sandbox does not replace Green Team, it limits
the damage that can occur *before* Green Team steps in.

**Cross-validation, not just a reference:** Day 4 (Pillar 6,
"Observability & Security Ops") describes, independently of the
project, an autonomous security triage with three roles — Blue Team
(continuous observability), Red Team (proactive attack simulation),
Green Team (executes "stateful quarantines" on an anomaly) — that
matches, without SIGMA having copied it from there, the Red/Blue/Green
model `ADR-003` already had approved before this course existed. This
is not a mechanism this ADR invents — it is confirmation that SIGMA's
already-existing design is aligned with what the industry considers the
baseline architecture for this.

---

## Consequences

### Benefits
- A generated skill with a real bug cannot, by design, exceed resource
  limits or access more credentials than it declared needing —
  contained from the first second, not only after something has already
  failed.
- $0 cost on `SIGMA-FE` — Docker with resource limits requires no paid
  service or new dependency (already in the stack).

### Risks and mitigations
| Risk | Mitigation |
|---|---|
| Overhead of starting a new container per execution | Acceptable — only applies to dynamically generated code (2.1), not to Rollout 1's 7 skills, which keep running without this overhead |
| A generated skill that legitimately needs more resources than the default limits | Limits are configurable per skill via its own `defaults.yaml`, following the same ADR-006 principle (placeholder, never hardcoded) |

---

## Alternatives considered

| Alternative | Why it was discarded |
|---|---|
| Mandatory gVisor in all variants | Contradicts `SIGMA-FE`'s commitment to operate at $0 with no additional dependencies — Docker with limits is already sufficient for the real risk |
| Sandboxing Rollout 1's 7 skills too | Over-engineering — those skills already have the trust level of human-reviewed code; applying the same isolation as unreviewed code reduces no real risk, only adds overhead |
| Relying solely on the Policy Server, without an ephemeral container | The Policy Server validates *which tool is called*, it does not contain *how* the skill's own code executes — distinct, complementary layers, not substitutes |

---

## Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-003 | Green Team recovers after a failure; this ADR prevents the blast radius from the start — complementary |
| ADR-005 | JIT downscoping (2.3) extends the Policy Server's structural layer to container startup |
| ADR-008 | K⊆X applies equally inside the sandbox — execution isolation is not an exception to the epistemic restriction |
| ADR-014 | Primary source of code within this ADR's scope (2.1) |
| ADR-016 | Mandatory entry condition for Rollout 3 (Tab. 2) |
| ADR-019 | Workers run mandatorily inside this sandbox, from creation through decommissioning |

---

## Version history

v1.0 — First version, drafted at Marx's explicit request after updating
ADR-003. Recovers the sandboxing concept from prior iterations of the
project (never formalized in the original 16 ADRs), with scope
explicitly bounded to dynamically generated code and Workers — does not
apply retroactively to Rollout 1's 7 human-authored skills.

**Changes in v1.1:** terminology correction — "Ephemeral Agent" was
reverted to "Worker" throughout the document (see ADR-019 §2.1ter for
the distinction between the operational and epistemic planes).

**Changes in v1.2:** see the v1.2 executive summary above — full
deepening against Day 4 of the Google-Kaggle course, without changing
any decision already made, only its rationale and two new mechanisms
(network isolation, allowed-file lists).

**Changes in v1.3:** closed the gap around persisting the result before
destroying the container (the "end of execution" is now defined as the
Director's write confirmation, not the process's return) — and added
the warm-container policy for `trust_level ≥ 2` (ADR-019 §2.1quater),
which reduces startup overhead without relaxing any containment limit.

**Approval note (no version change):** Approved in full by Marx. Still
a mandatory entry condition for Rollout 3 (`ADR-016` Tab. 2) — design
approval does not substitute for verifying that the sandbox is applied
in real code to Engineer Auditor before that phase.
