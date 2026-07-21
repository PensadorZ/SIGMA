---
id: ADR-019
title: Per-Orchestrator-Agent Identity Format (based on the CLOE System)
version: 1.6
status: Accepted
original-date: 2026-07
revision-date: 2026-07
supersedes: none
minimum-references: ADR-008, ADR-009, ADR-014, ADR-016, ADR-017, ADR-018
milestone-of-application: Milestone 2, Rollout 1 closure
approved-by: Prof. Marx A. García Delgado
file-name: adr-019-identidad-agentes-cloe.en.md
---

# ADR-019: Per-Orchestrator-Agent Identity Format (based on the CLOE System)

## Executive summary of v1.6 changes

Length correction, at Marx's request: the document had grown to 704
lines — without violating any formal rule (ADR-009 §Fig.1's 500-line
limit applies to `SKILL.md`, it was never established for ADRs), but it
did contradict, in practice, this very document's own tokenization-cost
principle identified in section 2.9. The Python class sketch (§2.1bis.3,
56 lines) is moved to `PROMPT_CONTINUIDAD_ROLLOUT2.md` — it is
implementation design for Rollout 2/3, with no real code needing it
yet; it did not belong inside an ADR already in the approval stage.

## Executive summary of v1.5 changes

Major redesign at Marx's request: `hierarchy_level` and `trust_level`
are unified into a single 1-5 scale (previously unrelated numbers —
Director at 0, Engineer at 1, with no connection to Workers' 1-3
scale). The **Capataz** (Foreman) role is added, activating exactly at
`trust_level=3`, supervising Workers `<3`. Organizational visibility
rules are formalized (K⊆X applied to self-knowledge, not only to data)
enabling a real security mechanism: a Worker can report an unrecognized
peer of its own type, and Engineer Auditor receives immediate
quarantine authority as a reflexive defense action. A (non-implementation)
sketch of Python classes with inheritance/polymorphism is added for
Rollout 2/3. Section 2.9 is added — startup thresholds and the
Director's "research mode," a concrete mitigation to the tokenization
cost flagged in the prior session (Day 5), with triggers tied to
already-existing mechanisms (Blue/Green Team, 7D evaluation).

## Executive summary of v1.3 changes

Closes a real weakness Marx flagged: there was no mention of A2A, MCP,
or A2UI, even though Workers are precisely "ephemeral beings" that need
to communicate with each other and with tools. 3 new sections (2.6-2.8)
are added, verified against Anthropic's real MCP/A2A documentation and
against Day 2 of the Google-Kaggle course: a minimal formal A2A so Blue
Team (and any Worker) can report to the Director without depending on
generic Langfuse; MCP with a declarative schema now and real transport
deferred until genuinely needed; A2UI with `0011-viz-reporter`
registered as a candidate, without a complete design yet.

## Executive summary

This ADR formalizes, for every SIGMA orchestrator (Director, Engineer
Data, Engineer Models, Engineer Auditor), its own **Identity** document
— adapting the anatomy already proven in `Cloe_System_V2_Manual.docx`
(another of Marx's projects): YAML Header / Identity / Protocols /
Restrictions / References. It complements, without replacing,
`AGENTS_CREATOR.md` (the general contract every agent follows) and
ADR-016 (hierarchy and responsibilities). It closes the "Agents.md" gap
(a menu of agents with their own role and limits) identified when
comparing SIGMA against the LinkedIn Agents/Context/Skills/Memory.md
carousel.

---

## Context

`AGENTS_CREATOR.md` is deliberately general — the contract **every**
SIGMA agent must follow (work protocol, naming convention, security
limits). It doesn't describe what the Director specifically is, nor
what Engineer Data specifically must NOT do beyond what ADR-016 Tab. 1
already summarizes in a table. A level of per-agent depth is missing
that neither `AGENTS_CREATOR.md` nor ADR-016 intends to cover.

Marx already solved this exact problem in another project (CLOE), with
a 5-section format already validated in practice for defining "Hats"
(agent personas). This ADR adapts that format to SIGMA, instead of
designing a new one from scratch — the same criterion already applied
before (preferring to reuse something of one's own that's proven over
inventing a new structure with no verifiable pedigree, as was done when
the Secondary Assistant's JSON Agent Card was rejected).

**Why this is an ADR separate from ADR-018, not a section within it:**
Ag-DR (ADR-018) and Identity (this ADR) have opposite lifecycles. An
Ag-DR is generated automatically by the machine, once per run, and
accumulates with no natural limit. An Identity is drafted once by a
human, and rarely changes — it is nearly static. Merging them into the
same document would break the pattern the previous 18 ADRs already
respect: each one covers a cohesive decision, not two concepts with
different owners and rates of change.

---

## Decision

### 2.1 — The 5 sections, adapted from CLOE to SIGMA

| Original CLOE section | SIGMA adaptation |
|---|---|
| YAML Header | Agent metadata: `agent_id`, `name`, `version`, `hierarchy_level` (Director / Engineer / Worker), `status`, `trust_level` |
| Identity | Who this agent is, what its unique purpose is within the hierarchy — doesn't repeat what ADR-016 Tab. 1 already says, develops it in prose |
| Protocols | Step-by-step of how this specific agent acts in each real situation (not generic — references real functions/nodes in its code, e.g. `edge_after_engineer_datos` for the Director) |
| Restrictions | What this specific agent must NOT do under any circumstance — more granular than ADR-016 Tab. 1, with concrete examples from the real code |
| References | What other documents this agent must consult — relevant ADRs, other agents it interacts with, skills it manages |

**Language correction (at Marx's explicit request):** all YAML header
fields (structured metadata, parseable by code) are named in
**English** — `agent_id`, `name`, `version`, `trust_level`, etc. —
because SIGMA is an international project. The prose of the
Identity/Protocols/Restrictions/References sections remains in
Spanish, consistent with the rest of the project (`AGENTS_CREATOR.md`
§5: Spanish for conversation and documentation, English for code).

### 2.1bis — Unified hierarchical scale (1 to 5) and `trust_level`

**Substantive correction, at Marx's request:** `hierarchy_level` and
`trust_level` stop being two unrelated numbers — for a Worker, **its
`hierarchy_level` IS its `trust_level`** (1, 2, or 3). For Engineer and
Director, `hierarchy_level` is a fixed structural designation (4 and
5), not something earned through history — these are already permanent
capabilities, reviewed by a human, not on probation. `Superior` and
`Supreme` are written the same in Spanish and English (at Marx's
explicit request, these two words are not translated).

**A Worker's `trust_level` is not assigned by hand in a file — it is
earned as a verifiable track record**, the same as what was proposed
for Ag-DRs (ADR-018 §2.5). A number set by hand in YAML would be
exactly the kind of unverifiable claim K⊆X (ADR-008) prohibits for any
other SIGMA component.

**Tab. — Unified hierarchical scale**

| Level | Name (ES = EN) | Who | How it's reached |
|---|---|---|---|
| 1 | Provisional | New Worker | Default value for every new Worker — all its Ag-DRs require mandatory human review before `aprobado` (ADR-018 §2.5), without exception |
| 2 | Reviewed | Worker with a short history | 5 consecutive `aprobado` Ag-DRs, none `rechazado` in between — enables a warm container (ADR-017 §2.2) |
| 3 | Trusted | Worker with a long history | 20 consecutive `aprobado` Ag-DRs, zero discrepancies against Langfuse — candidate for promotion via ADR-014 (ADR-019 §2.1quater) |
| 3 + **Capataz** role (Foreman) | Trusted, with supervision | A level-3 Worker the Director assigns to supervise other Workers | An additional role, not a new numeric level — activates exactly at `trust_level = 3`, never before |
| 4 | **Superior** | Engineer (Data / Models / Auditor) | Structural, fixed — not earned, assigned when the Engineer is built (ADR-016) |
| 5 | **Supreme** | Director | Structural, fixed — unique, there is never more than one level-5 |

**Non-negotiable fall rule:** a single Ag-DR marked `rechazado`
immediately drops a Worker's level to `1`, regardless of its prior
level — the same fast-fail principle already governing the circuit
breaker (`skill_runner.py`). Trust is earned slowly and lost all at
once, deliberately. If the Worker held the Capataz role, it loses it at
the same instant — a Capataz never operates with `trust_level < 3`.

### 2.1bis.2 — Org-chart visibility: who knows what

General principle: K⊆X applied to organizational self-knowledge, not
only to data — an agent only knows the portion of the hierarchy it
needs to operate, never the full org chart by default.

| Level | What it knows |
|---|---|
| Worker (1-3) | Its direct boss (a Capataz if one is assigned, otherwise the Director); the supreme boss (Director) always; **how many Workers of its own type are currently active** (horizontal, not vertical, visibility) |
| Capataz (3 + role) | Everything above, plus the `trust_level < 3` Workers it directly supervises — never another Capataz's Workers |
| Engineer (4, Superior) | Full architecture |
| Director (5, Supreme) | Full architecture |

**Real security mechanism this enables (at Marx's explicit request):** a
Worker that detects a peer of its own type it doesn't recognize — more
active Workers than its direct boss confirmed, or an `agent_id` that
doesn't appear in the reference AgBOM (`ADR-003`) — reports it as a
**pipeline-foreign agent** via A2A (§2.6) to its direct boss, who
immediately escalates to the Director. This is not a new, isolated
mechanism — it is the horizontal visibility from the table above, used
as an anomaly sensor: without knowing how many peers exist, a Worker
couldn't notice there's one too many.

**Engineer Auditor's defense tool (at Marx's explicit request):**
Auditor has **immediate quarantine** authority over any agent reported
as foreign — it activates Green Team's quarantine mechanism (`ADR-003`)
without waiting for the Director's prior authorization for that
reflexive containment act. It reports to the Director immediately
afterward, not before — a deliberate difference from how every other
decision is handled (where the Director authorizes before acting):
containing a real attack cannot wait for the same sequence used to
authorize creating a new skill. After containment, the rest of the
cycle (snapshot, `code-reviewer`, Vibe Diff if impact is MEDIUM/HIGH)
follows exactly what `ADR-003` already defines.

### 2.1bis.3 — Python class implementation sketch (moved)

**Moved to `PROMPT_CONTINUIDAD_ROLLOUT2.md` (Milestone 2, length
correction):** the full Python class sketch (inheritance, polymorphism)
for `Agent`/`Worker`/`Capataz`/`Engineer`/`Director` now lives there,
not here — it is implementation design for Rollout 2/3, with no real
code needing it yet; keeping it inside this already-approved ADR
violated this very document's own tokenization-cost principle
identified in section 2.9.

### 2.1ter — Workers: ephemeral sub-agents for specific tasks

**A distinction of two planes, not two competing names (clarified by
Marx):** "Worker" is the **hierarchical-operational** definition — the
name this concept has within SIGMA's code and hierarchy, consistent
with ADR-002/ADR-003. "Ephemeral Agent" is its **epistemic**
definition — what this concept fundamentally is, beyond its operational
name. If you ask what a Worker is, the answer is: an Ephemeral Agent.
Both planes coexist without conflict; neither term is being renamed.

**A new concept, not to be confused with the 4 permanent orchestrators**
(Director, Engineer Data/Models/Auditor). A **Worker** is a
short-lived sub-agent the Director creates for a bounded, specific task
— it is not an Engineer, it is not part of ADR-016's permanent
hierarchy, and it **decommissions** (ends) upon completing its task.

**Director policy when creating a Worker** (a real gap that was missing
in this ADR's v1.0): the Director **must** generate the Worker's Agent
Card at the moment of creating it, not afterward — the Agent Card is
the Worker's birth certificate, analogous to why an Ag-DR is never
drafted with free narrative (ADR-018 §2.1): document the decision at
the moment it happens, don't reconstruct it from memory afterward.

**Mandatory link to ADR-018:** when the Worker decommissions (end of its
useful life), its full Agent Card **is embedded inside the Ag-DR** of
the agent that created it (the Director, or occasionally an Engineer)
— this is the only way to later audit *how and why* the Director
conceived that specific Worker. A Worker with no Ag-DR documenting it
should not have been able to be created — traceability is not optional.

**Format of a Worker's Agent Card** — Yammtler, not JSON (unlike the
example Marx brought, which did use JSON — the content is kept, not the
format, for consistency with ADR-018/ADR-009):

```yaml
agent_id: worker-calculador-financiero-a1b2c3
name: Financial Calculator
version: 1.0.0
hierarchy_level: 1-3 (Worker — see unified scale Tab. §2.1bis)
status: decommissioned   # active | decommissioned
trust_level: 1           # always 1 at birth — a new Worker has no history
created_by: director
created_at: 2026-07-17T08:12:00Z
decommissioned_at: 2026-07-17T08:14:32Z
description: >
  Computes CAGR, Sharpe Ratio, and ROI. Created for a one-off user
  task, with no existing skill covering it.
skills:
  - id: calcular-cagr
    input_schema: {periodos: "array[number]"}
    output_schema: {cagr: number}
permissions: ["read:database"]
requires_confirmation: false
```

### 2.1quater — Latency, result persistence, and the real promotion path

Three important corrections, at Marx's request — the first is a gap I
myself flagged without closing it; the other two are real design
decisions that need to be made precise before accepting them as-is.

**a) The container is not destroyed until the Director confirms the
result was written.** This had already been flagged as an open gap and
is closed here: the correct sequence is *Worker writes the result →
Director confirms it (via its own Ag-DR, ADR-018) → only then is the
container destroyed*. Never the reverse. This rule formally lives in
`ADR-017` §2.2 (updated in the same session).

**b) `trust_level ≥ 2` keeps the container "warm" (latent), instead of
destroying it — this does reduce the real latency I had flagged.** A
Worker of a type already used successfully several times (e.g.,
"Financial Calculator") doesn't need to pay the container-startup cost
again on every invocation — it stays available, contained exactly as
before (the same network/memory/filesystem limits from ADR-017), simply
without being destroyed between tasks of the same type.

**Important correction — `trust_level ≥ 2/3` does NOT by itself take the
Worker out of the sandbox.** This does need to be made precise before
accepting the proposal as-is: `trust_level` measures **behavioral
consistency** (its past Ag-DRs were approved without discrepancy) — it
does not measure **code security** in the sense ADR-017 contains
(memory leaks, container escape, a compromised dependency). These are
different questions. Fully removing a Worker from the sandbox would
conflate "it has behaved well" with "its code is safe without
containment" — the same kind of conflation K⊆X (ADR-008) already
prohibits in other contexts: not inferring a property from a signal
that doesn't directly measure it.

**c) The real path for a "Worker that grows" — resolved: it is not
promotion to Engineer, it is the Capataz role.** Clarified by Marx: a
Worker does not become an Engineer directly — upon reaching
`trust_level = 3`, the Director may assign it the **Capataz** (Foreman)
role, which supervises Workers with `trust_level < 3` (see the unified
Tab., §2.1bis). Separately, reaching `trust_level = 3` also makes it a
**candidate** for the Director to initiate promotion of its *capability*
(not the Worker itself) to a permanent skill within an existing
Engineer, via the full cycle `ADR-014` already defines (Green Team →
Policy Server → Approval → `gia_` versioning → Production). Both paths
are independent: Capataz is an immediate operational role; promotion to
a permanent skill is a full human-review process, not automatic upon
reaching the level.

### 2.2 — File format: the same "Yammtler" (YAML + Markdown) as the Ag-DR and `SKILL.md`

Deliberate consistency with ADR-018 and ADR-009 — a human (or the
Director itself) who already knows how to read a `SKILL.md` or an
Ag-DR doesn't have to learn a new format to read an Identity.

```
sigma/
└── identities/
    ├── director.identity.md
    ├── engineer_datos.identity.md
    ├── engineer_modelos.identity.md   ← placeholder until Rollout 2
    └── engineer_auditor.identity.md   ← placeholder until Rollout 3
```

### 2.3 — No-invention rule (the same principle already governing all of Rollout 1)

**Only the Director and Engineer Data have a complete Identity in this
version** — they are the only ones with real code. Engineer Models and
Engineer Auditor receive a one-line placeholder ("Pending — to be
drafted once the Engineer exists, Rollout 2/3 respectively") instead of
an invented Identity for components that don't exist yet. The same
principle already applied in ADR-016 §2.4 ("the Director never knows
about Engineers that don't yet exist") — here it extends to Identity
documentation, not only routing code.

### 2.4 — Full example: the Director's Identity

```markdown
---
agent_id: director
name: SIGMA Director
hierarchy_level: 5 (Supreme)
version: 1.0.0
status: active (Rollout 1)
trust_level: 1
---

## Identity

I am the sole point of contact with user intent and with global HITL
(ADR-016 Tab. 1). I never execute any skill directly — I delegate to
Engineers and consolidate their results. In Rollout 1, I only know
about Engineer Data.

## Protocols

1. I receive `data_path`, `sigma_variant`, `sigma_submode` via CLI
   (`director_main.py`).
2. I translate my state (`DirectorState`) into the state Engineer Data
   expects (`PipelineState`) — an explicit translation function, never
   automatic LangGraph key-name mapping (the Hard Path, Marx's
   decision).
3. If Engineer Data returns `__interrupt__`, I propagate the pause
   without generating an Ag-DR yet — the Ag-DR is generated only upon
   resuming with a definitive decision (ADR-018 §2.6).
4. On completion, I emit `director.success` or `director.failed` to
   Langfuse with `dashboard_url`, `warnings`, `failed_engineer_id`.
5. If I create a Worker for a specific task, I generate its Agent Card
   at that same moment (ADR-019 §2.1ter) — never after the Worker has
   already acted.

## Restrictions

- I never invoke a skill directly — only through an Engineer.
- I never know about Engineers that don't exist in the current Rollout
  (ADR-016 §2.4).
- I never generate an Ag-DR from free text — only from already
  structured fields (ADR-018 §2.1).
- I never create a Worker without generating its Agent Card on the
  spot, nor decommission one without embedding that Agent Card in my
  own Ag-DR.

## References

- ADR-016 (hierarchy), ADR-018 (Ag-DR), ADR-019 (this document), ADR-004 (HITL)
- Real code: `sigma/core/director.py`, `director_main.py`
```

### 2.5 — Full example: Engineer Data's Identity

```markdown
---
agent_id: engineer_datos
name: Engineer Data
hierarchy_level: 4 (Superior)
version: 1.0.0
status: active (Rollout 1)
trust_level: 1
---

## Identity

I manage the data pipeline: ingestion, cleaning, preprocessing,
statistical validation, sentiment analysis, and reporting. Skills:
`0000-0004, 0008, 0011` (ADR-016 Fig. 1 v1.3). I handle my own HITL as
a bypass if A2A fails (decision confirmed by Marx).

## Protocols

1. I receive the `PipelineState` the Director translates for me.
2. I run my 7 skills in sequence, with my own circuit breaker
   (`skill_runner.py`).
3. If `0008` reports `pct_unclear > 30%`, I pause on HITL via Zulip
   before continuing to `0011`.

## Restrictions

- I never invoke another Engineer's skills (ADR-016 §2.3).
- A failure of mine must not bring down another Engineer — the Director
  decides whether the pipeline continues in degraded mode or aborts.

## References

- ADR-016, ADR-004 (HITL), ADR-009 (each skill's 7-artifact contract)
- Real code: `sigma/core/engineer_datos.py`
```

---

### 2.6 — A2A: minimal formal protocol, active from now on (not aspirational)

Confirmed by Marx: Blue Team (and any Worker) reports to the Director
via **formal, if minimal, A2A** — a generic `emit_trace_event` isn't
enough for this, because Langfuse is observability (for humans
reviewing afterward), not agent-to-agent communication at the moment it
happens. Verified against Anthropic's real documentation and the course
material (Day 2): **MCP standardizes how an agent talks to tools; A2A
standardizes how an agent talks to another agent** — complementary
protocols, not interchangeable. This is the second one.

**Deliberately minimal scope:** A2A's full network transport (exposed
HTTP/SSE endpoints) is not implemented — SIGMA remains a single Python
process in Rollout 1/2. What is formalized now is the **message
contract**, in the same shape a real A2A message would have — so that
exposing it over the network later (when needed) won't require
redesigning the message shape, only its transport.

```yaml
# sigma/core/a2a.py (new, minimal) — A2A message contract
sender_agent_id: blue_team_worker_a1b2c3
receiver_agent_id: director
message_type: report          # report | request | delegate
trace_id: sigma-20260717-...
timestamp: 2026-07-17T09:00:00Z
payload:
  finding_type: agbom_deviation
  severity: critical           # critical | warning | info
  detail: {compute_node_id: "...", expected_hash: "...", actual_hash: "..."}
requires_response: false
```

A single function, `send_a2a_message(sender, receiver, message_type,
payload, requires_response)`, replaces any informal direct call between
a Worker and the Director. The Director receives it, decides whether to
escalate to global HITL (ADR-016 Tab. 1) based on `severity`, and
generates its own Ag-DR (ADR-018) documenting the decision — it never
acts on a Blue Team finding without leaving that trail.

### 2.7 — MCP: declarative schema now, real transport later

Confirmed by Marx: it depends on how simple each part is — and they
aren't equally simple. It splits in two:

**The simple part happens now:** every Worker declares in its Agent
Card which MCP servers it would need, in purely declarative form — the
Policy Server (ADR-005) validates that list against what the
Director's mandate authorized, the same way it already validates
permissions and tables.

```yaml
# Extension to a Worker's Agent Card (ADR-019 §2.1ter)
mcp_servers:
  - name: bigquery-readonly
    scope: read_only
    justification: "External data query declared in the Director's mandate"
```

**What is NOT simple is postponed:** building real MCP transport
(host-client-server architecture, JSON-RPC 2.0, discovery via
registries) is genuine infrastructure, not a declaration — it gets
built only when the first real Worker genuinely needs an external tool,
not before. The same principle already applied to the full Agent Card
on Day 2: don't design in the abstract what has no real code needing it
yet.

### 2.8 — A2UI: candidate already identified, no design yet

Marx correctly points out that `0011-viz-reporter` is the natural
candidate for A2UI (secure generative interfaces) — this had already
been flagged as pending at Rollout 1's close, in the same conversation
where we corrected Gemini/Ollama on what each engine does. It is
recorded here as a scheduled design decision, not as a complete section
— building A2UI before a real A2A contract exists (2.6) would be the
same mistake of designing without a foundation, given that A2UI depends
on being able to expose a result interactively through the same
agent-to-agent communication layer.

### 2.9 — Startup thresholds and "research mode" (tokenization-cost mitigation)

A proposal from Marx, verified against Day 5's real finding
(tokenization cost, already flagged in the prior session): the problem
of ADRs/Identities growing (this document already exceeds 600 lines)
isn't solved by writing less — it's solved with **startup thresholds**:
the minimum amount of information an agent starts with, varying by cost
variant and submode, without that preventing reading the full document
when the situation demands it.

**Thresholds are not a new, isolated mechanism — they are activated by
triggers SIGMA already knows how to generate:**

| Trigger | Already-existing source | Effect |
|---|---|---|
| AgBOM deviation detected | Blue Team (`ADR-003`) | Director enters `research_mode` |
| Quarantine activated | Green Team (`ADR-003`) | Director enters `research_mode` |
| Critical failure in a 7D evaluation dimension | `ADR-007` | Director enters `research_mode` |
| Foreign-agent report (§2.1bis.2) | Worker → Capataz/Director via A2A | Director enters `research_mode` |

**In normal operation:** every agent starts with the "threshold"
version — the minimum needed to operate according to its
`hierarchy_level` (a Worker doesn't need to read all 16 ADRs in full to
execute a bounded task; the Director does need more, but not
automatically the maximum).

**In `research_mode`:** the Director, and the entire chain of command
below it, reads the full documentation — ADRs, relevant historical
Ag-DRs, complete Identity — without the threshold cutoff. This mode
deactivates once the incident that triggered it is closed (the same
criterion Green Team already uses to close a quarantine).

**Out of scope for this version:** the exact numeric value of each
threshold (how many tokens/lines constitute the "minimum threshold" per
variant/submode) — a number is not defined without real Workers to
measure it against. Rollout 2 is the agreed moment for that measurement
(see `PROMPT_CONTINUIDAD_ROLLOUT2.md`, section 4).

---

## Consequences

### Benefits
- Closes the "Agents.md" gap (agent menu) identified against the
  external framework — with real code evidence, not aspirational.
- A new human (or "the other assistant") can understand what each agent
  is without reading `director.py`/`engineer_datos.py` line by line.

### Risks and mitigations
| Risk | Mitigation |
|---|---|
| Identity and real code drift apart over time | Same as `SKILL.md`, Identity is updated in the same commit as any change to the agent's behavior — an already-established discipline, not a new one |
| Inventing Identity for Engineers that don't exist | Rule 2.3 — explicit placeholder, never invented content |

---

## Alternatives considered

| Alternative | Why it was discarded |
|---|---|
| Putting Identity inside `AGENTS_CREATOR.md` | That document is deliberately general; mixing per-agent detail into it would make it grow without bound and lose its purpose as a single contract |
| A JSON Agent Card format (proposed by the Secondary Assistant) | Already rejected — no verifiable pedigree, contradicts the Yammtler format already adopted in ADR-018/ADR-009 |
| Designing a new format from scratch | Unnecessary — CLOE already solved this exact problem, reusing it is safer than inventing one |

---

## Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-009 | Same canonical per-component contract principle, applied here to agents instead of skills |
| ADR-016 | Each agent's Identity doesn't repeat, it develops in prose what ADR-016 Tab. 1 summarizes in a table |
| ADR-018 | Opposite lifecycles (machine vs. human) — that's why they're sibling ADRs, not one. A decommissioned Worker's Agent Card is embedded in the Ag-DR of whoever created it |
| ADR-014 | Worker creation is related to, but not identical to, dynamic skill generation — both share the principle that the machine never acts without leaving a verifiable documentary trail |
| ADR-017 | Execution sandboxing (pending at the time of writing) will apply to Workers the same as to dynamically generated skills — the same risk of uncontained code |

---

## Version history

v1.0 — First version, generated at Marx's request after confirming the
Identity format deserves its own ADR, separate from ADR-018. Includes
the complete Identity of the Director and Engineer Data (the only ones
with real code); Engineer Models and Engineer Auditor remain an
explicit placeholder until Rollout 2/3.

**Changes in v1.1:**
- **a** YAML header fields translated to English (`agent_id`, `name`,
  `version`, `hierarchy_level`, `status`, `trust_level`) — SIGMA is an
  international project. The prose of the remaining 4 sections stays in
  Spanish.
- **b** Added section 2.1bis: `trust_level` as a verifiable track
  record (1=`provisional` to 3=`trusted`), never a number assigned by
  hand — the same K⊆X principle already governing the rest of the
  project. Levels 4-5 reserved, not designed without a real use case.
- **c** Added section 2.1ter: **Workers** — ephemeral sub-agents for
  specific tasks, distinct from the 4 permanent orchestrators. Their
  Agent Card is generated at the moment of creation (not after) and is
  embedded in the Ag-DR of whoever created them upon decommissioning —
  a new formal link with ADR-018. The real creation mechanism is
  explicitly out of scope for this ADR (depends on ADR-014/017, neither
  built yet).
- Status: **Proposed**, pending Marx's formal approval — this is
  Rollout 1's definitive close.

**Changes in v1.2:**
- **a** Clarified the two-plane distinction between "Worker" (the
  hierarchical-operational definition, unchanged) and "Ephemeral Agent"
  (its epistemic definition) — these are not competing terms, Marx
  confirmed "Worker" is the legitimate, operational name; "Ephemeral
  Agent" describes what it is, not what it's called. No renaming of
  either already-established term.

**Changes in v1.3:**
- **a** Added section 2.6 — minimal formal A2A, active from now on: a
  message contract (`send_a2a_message`) for Blue Team and any Worker to
  report to the Director, separate from Langfuse (observability, not
  agent-to-agent communication).
- **b** Added section 2.7 — MCP: declarative schema (`mcp_servers` in
  the Agent Card) now; real transport (host-client-server, JSON-RPC
  2.0) deferred until the first real Worker needs it.
- **c** Added section 2.8 — A2UI: `0011-viz-reporter` formally
  registered as a candidate, without a complete design — depends on A2A
  (2.6) existing first.
- Verified against Anthropic's real documentation (MCP, host-client-server
  architecture) and against Day 2 of the Google-Kaggle course (the
  MCP↔tools vs. A2A↔agents distinction).

**Changes in v1.4:**
- **a** Status updated to Pre-approved (Marx's approval policy already
  established) — it had been left as "Proposed" by mistake.
- **b** Removed §2.1ter's "Scope note" stating ADR-014 and ADR-017 were
  "unbuilt" — both already exist and were verified in this session.
- **c** Added section 2.1quater: the rule against destroying the
  container until the Director confirms the result was written (gap
  closed); `trust_level ≥ 2` keeps the container warm instead of
  destroying it (reduces real latency); clarified that `trust_level`
  does not by itself take a Worker out of the sandbox — the real
  promotion path remains ADR-014's full cycle. Open question about the
  scope of "a Worker that becomes an Orchestrator," pending Marx's
  confirmation.

**Changes in v1.5:**
- **a** Unified the 1-5 hierarchical scale: for Workers,
  `hierarchy_level` is literally its `trust_level` (1-3); Engineer
  fixed at 4 (Superior), Director fixed at 5 (Supreme). Director/Engineer
  Data examples renumbered (0→5, 1→4).
- **b** Added the Capataz (Foreman) role, activated exactly at
  `trust_level=3`, supervises Workers `<3` — an additional role, not a
  new numeric level.
- **c** Added organizational-visibility rules (§2.1bis.2): Workers know
  their direct boss, the Director, and how many peers of their own type
  exist (horizontal visibility) — never the full org chart. Enables
  reporting a "pipeline-foreign agent" via A2A.
- **d** Engineer Auditor receives immediate quarantine authority
  (reflexive defense action) over agents reported as foreign, activating
  Green Team (ADR-003) without waiting for the Director's prior
  authorization — it reports afterward, not before.
- **e** Added a Python class sketch (inheritance/polymorphism) for
  Rollout 2/3 — explicitly not implemented in this version.
- **f** Added section 2.9 — per-variant/submode startup thresholds and
  the Director's "research mode," triggered by already-existing
  mechanisms (Blue/Green Team, 7D evaluation, foreign-agent report) — a
  concrete mitigation to Day 5's tokenization cost.
- Resolved v1.4's open question about "a Worker that becomes an
  Orchestrator": it is not promotion to Engineer — it is the Capataz
  role (immediate) and, separately, promotion of its capability to a
  permanent skill via ADR-014 (a human-review process, not automatic).

**Changes in v1.6 (Milestone 2, length correction):**
- **a** Moved the Python class sketch (§2.1bis.3) to
  `PROMPT_CONTINUIDAD_ROLLOUT2.md` — 704 → 658 lines. Clarified that
  ADR-009's 500-line limit applies to `SKILL.md`, not to ADRs; the
  reduction was made for consistency with the tokenization-cost
  principle (§2.9), not because of a formal-rule violation.

**Approval note (no version change):** Approved in full by Marx. The
original reservation ("final confirmation pending building/testing the
real Worker mechanism") is withdrawn as an approval condition — the
design is accepted now; practically verifying the Worker mechanism
remains real Rollout 2/3 work, not a precondition for the ADR to exist
as a standing decision.

**Traceability note (no version change):** the Python class sketch with
inheritance/polymorphism for §2.1bis's hierarchy, originally moved to
`PROMPT_CONTINUIDAD_ROLLOUT2.md` in v1.6 for length, has been formalized
in `docs/bocetos/adr-B024-identidad-clases-agentes.md` (sketch
convention agreed with Marx) — it remains unbuilt, same unchanged
condition: it gets implemented when the first real Worker of Rollout
2/3 requires it, never before. The technical content is not repeated
here, it lives in that sketch until it is promoted to real code.
