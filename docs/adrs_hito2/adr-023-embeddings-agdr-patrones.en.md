---
id: ADR-023
title: Queryable Operational Memory — Embeddings over Ag-DRs for Pattern Detection
version: 1.0
status: Accepted
original-date: 2026-07
revision-date: 2026-07
supersedes: none
minimum-references: ADR-008, ADR-016, ADR-018, ADR-022
milestone-of-application: Milestone 3 (prospective) — implementation out of scope for Rollout 2/3
approved-by: Prof. Marx A. García Delgado
file-name: adr-023-embeddings-agdr-patrones.en.md
---

# ADR-023: Queryable Operational Memory — Embeddings over Ag-DRs for Pattern Detection

## Executive summary

A functional extension of `ADR-018`, not a standalone decision: it
builds the mechanism `ADR-018` promised from its very first draft and
never implemented — *"opens the door to detecting patterns (e.g.,
`0004` dropping into `PAUSED_HITL` with unusual frequency for datasets
of a certain size) without manually reviewing Langfuse."* Unlike
`ADR-022` (the Director's RAG, human consumption via conversation),
this index is **agent-facing** — queried by the Director and Engineer
Auditor, not by you directly.

---

## Context

Today, if `0004` starts dropping into `PAUSED_HITL` more often than
normal for a certain kind of dataset, the only way to notice is for you
to detect it by manually reviewing Langfuse — exactly what `ADR-018`
identified as the problem to solve, without ever building the
mechanism. The Ag-DRs already contain the necessary structured
information (`verdicts`, `hitl_disparado`, `skills_ejecutados`); what's
missing is the similarity-search layer that would allow finding
"situations similar to this one" instead of only "the Ag-DR with this
exact `trace_id`."

---

## Decision

### 2.1 — Module location, separated from ADR-022 by consumer and by data

```
sigma/
└── memory/
    ├── rag/                  # ADR-022, human-facing, static documents
    └── agdr_index/           # this ADR, agent-facing, dynamic Ag-DRs
        ├── indexer.py        # runs after every approved Ag-DR
        ├── pattern_query.py  # query interface for the Director/Engineer Auditor
        └── chroma_data/
```

Same technical stack as `ADR-022` (Chroma + local `sentence-transformers`,
$0 on `SIGMA-FE`) — but a different consumer and update cycle, which is
why this is a separate module rather than a shared folder.

### 2.2 — Hard rule: only an Ag-DR in `approved` state is indexed

**Non-negotiable, inherited directly from `ADR-018` §2.5.** `indexer.py`
fires only when an Ag-DR moves from `pending_review` to `approved` —
never before. Indexing an Ag-DR without your review would be exactly
the scenario `ADR-018` §2.5 exists to prevent: the system "learning"
from a run nobody validated.

```yaml
# indexer.py trigger
on_agdr_state_change:
  from: pending_review
  to: approved
  action: index_embedding
# any other transition (to rejected, or already indexed) triggers nothing
```

### 2.3 — Who queries it, and for what

| Consumer | Use |
|---|---|
| Director | `pattern_query.py` during `research_mode` (`ADR-019` §2.9) — "has this situation happened before under similar conditions?" |
| Engineer Auditor (Rollout 3) | Candidate tool for the future automated-judgment mechanism (`ADR-018` §2.8) — the judge can consult precedents before issuing a verdict, without this ADR thereby defining the judge itself |

The Judge does not have its own ADR as of this document — this index is
a tool available to it by cross-reference, not a merger of scope.

### 2.4 — K⊆X compliance

Same as in `ADR-022`: any synthesis the Director or Engineer Auditor
generate from this index's results must cite `trace_id` values and
concrete fields from the retrieved Ag-DRs — never an aggregated
narrative without verifiable anchoring. A detected pattern (`"0004
pauses with unusual frequency"`) must be traceable to a concrete list
of `trace_id` values, not to the model's general impression.

---

## Consequences

### Benefits
- Closes the functional gap `ADR-018` left open since its first draft
  — with a real mechanism, not just a stated intention.
- Reuses infrastructure already approved in `ADR-022` (same stack)
  without mixing consumer responsibilities.

### Risks and mitigations
| Risk | Mitigation |
|---|---|
| The index grows without bound over time | Same retention policy, still to be defined, that `ADR-018` already left as an open risk — not resolved here, inherited |
| A false-positive pattern (vector similarity without real causal relationship) | 2.4 — any pattern must be anchored to concrete `trace_id` values, verifiable by a human, never accepted on similarity score alone |

---

## Alternatives considered

| Alternative | Why it was discarded |
|---|---|
| Merge this module with `ADR-022` | Would mix a human-facing consumer with an agent-facing one, and static data with dynamic — two distinct responsibilities |
| Give the Judge its own ADR now, including this index as part of it | Premature — the Judge doesn't yet have a code form; its ADR (if it needs one) gets decided when Rollout 3 actually builds it |
| Also index `pending_review` Ag-DRs, with a low-confidence flag | Rejected — any degree of influence from an unapproved Ag-DR contradicts `ADR-018` §2.5 without exception |

---

## Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-008 | K⊆X governs Rule 2.4 without exception |
| ADR-016 | Engineer Auditor is the intended consumer, without breaching Engineer↔Engineer isolation |
| ADR-018 | Direct functional extension — this ADR builds what 018 left as a promised, unimplemented benefit |
| ADR-022 | Sibling ADR — same technical stack, different consumer and data cycle |

---

## Version history

v1.0 — First version, approved by Marx in the same session it was
proposed, alongside `ADR-022`. Implementation scope explicitly
prospective (Milestone 3) — the design is accepted now, the code is
not built before Rollout 3 closes.
