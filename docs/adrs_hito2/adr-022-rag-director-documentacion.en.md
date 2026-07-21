---
id: ADR-022
title: Director RAG over Internal Documentation (ChromaDB)
version: 1.0
status: Accepted
original-date: 2026-07
revision-date: 2026-07
supersedes: none
minimum-references: ADR-008, ADR-016, ADR-019, ADR-021
milestone-of-application: Milestone 3 (prospective) — implementation out of scope for Rollout 2/3
approved-by: Prof. Marx A. García Delgado
file-name: adr-022-rag-director-documentacion.en.md
---

# ADR-022: Director RAG over Internal Documentation (ChromaDB)

## Executive summary

Formalizes the real technical mechanism behind
`Director.enter_research_mode()`, a stub that has existed in `ADR-019`
§2.9 since its origin without an implementation body. When the
Director enters research mode, this ADR defines how it queries SIGMA's
internal documentation (ADRs, the Founding Charter) to answer with
traceable evidence instead of free narrative. **It does not connect to
the Ag-DRs** — that is a different, agent-facing memory, covered by
`ADR-023`.

---

## Context

The Director is the sole point of contact with user intent (`ADR-016`
Tab. 1). As the ecosystem grows — 21+ ADRs and counting — loading all
that context into every conversation becomes expensive in tokens (a
problem already flagged during Day 5 of the Google-Kaggle course, with
no real mitigation mechanism until now). The Director needs to be able
to retrieve only the relevant fragments of its own documentation, on
demand, instead of having everything loaded always or nothing
available ever.

---

## Decision

### 2.1 — Module location

```
sigma/
└── memory/
    └── rag/
        ├── indexer.py      # builds/updates the Chroma collection
        ├── retriever.py    # interface the Director queries
        └── chroma_data/    # local persistence, SIGMA-FE, $0
```

It does not live inside `director.py` — it is a tool the Director
decides to invoke, the same contract pattern it already uses with the
Engineers: it knows the interface, not the internal implementation.

### 2.2 — Indexing scope, deliberately bounded

Only **stable, versioned** documents are indexed: accepted ADRs and the
Ecosystem's Founding Charter (`SIGMA_v2.4.md` onward). **Ag-DRs are not
indexed** — their volume and format change with every real Rollout;
indexing them here would mean indexing something that goes stale within
weeks. Ag-DRs have their own agent-facing mechanism, in `ADR-023`.

### 2.3 — K⊆X compliance, non-negotiable

If the Director retrieves fragments and generates a response from
them, that is exactly the surface `ADR-008` exists to contain. Every
retrieved fragment carries traceable metadata:

```yaml
chunk_metadata:
  source_file: adr-018-memoria-operativa-agdr.md
  adr_id: ADR-018
  version: "1.2"
  chunk_id: "018-2.5"
```

The Director may **paraphrase** what it retrieves, never **invent** on
top of it — the same principle that already governs the Ag-DR's "Run
summary" section (`ADR-018` §2.3). Every response generated in research
mode must be able to cite which document and version each claim came
from.

### 2.4 — Embedding model

Local, via `sentence-transformers` (`all-MiniLM-L6-v2`) — no paid API,
consistent with `SIGMA-FE` and with the same pattern already used for
RoBERTa via Hugging Face. Migration to a paid embedding is reserved for
`SIGMA-HE`, if a real problem ever justifies it — not before.

### 2.5 — Trigger: `Director.enter_research_mode()`

This RAG is the real implementation of the method `ADR-019` §2.9
already declares with a signature but no body, triggered by: a
deviation reported by the Blue Team, a Green Team quarantine, or a
critical failure in the 7D evaluation (`ADR-007`). Research mode
queries this index before responding, not on every normal conversation
turn — avoiding the same token-cost problem that motivated the ADR in
the first place.

---

## Consequences

### Benefits
- $0 cost on `SIGMA-FE` — Chroma and `sentence-transformers` run
  locally, with no new paid dependency.
- Closes the `Director.enter_research_mode()` gap, which until now was
  a signature without an implementation.

### Risks and mitigations
| Risk | Mitigation |
|---|---|
| The index goes stale when a new ADR is approved | `indexer.py` runs as part of the same ADR approval flow — discipline equivalent to what already governs Identity/`SKILL.md` |
| The Director "hallucinates" by citing an ADR that doesn't say what it claims | 2.3 — traceable metadata + paraphrase rule, mechanically verifiable the same way as D3 of `ADR-007` |

---

## Alternatives considered

| Alternative | Why it was discarded |
|---|---|
| Load the full ADR context directly into the Director's prompt | Unviable past a certain volume — the same tokenization problem this ADR solves |
| Pinecone or another SaaS vector DB | Contradicts `SIGMA-FE`'s commitment to operate at $0; a legitimate candidate if `SIGMA-LE/ME` is ever built with this component |
| Also index the Ag-DRs in the same module | Would mix a human-facing consumer (the Director talking with you) with an agent-facing one (pattern detection) — distinct responsibilities, separated in `ADR-023` |

---

## Relationship to other ADRs

| ADR | Relationship |
|---|---|
| ADR-008 | K⊆X governs Rule 2.3 without exception |
| ADR-016 | The Director queries this RAG as a tool, without altering its routing contract with the Engineers |
| ADR-019 | Implements the real body of `Director.enter_research_mode()` (§2.9) |
| ADR-021 | The traceability cited here is concrete evidence of *documentation* and *effective challenge* |
| ADR-023 | Sibling ADR — same technical stack (Chroma), different consumer and data scope |

---

## Version history

v1.0 — First version, approved by Marx in the same session it was
proposed. Implementation scope explicitly prospective (Milestone 3) —
the design is accepted now, the code is not built before Rollout 3
closes.
