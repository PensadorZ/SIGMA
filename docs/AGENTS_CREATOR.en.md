# AGENTS_CREATOR.md — Global Agent Contract

**SIGMA v1.7 — Integrated System for Multi-Agent Management**
Author: Prof. Marx Agustín García Delgado
Version: 1.2.0
Repository: `PensadorZ/SIGMA` — single repository (code and documentation live together)

---

## Purpose of this document

`AGENTS_CREATOR.md` is the founding charter that defines the contract
every agent in the SIGMA ecosystem must follow — a human coordinating
AIs, an AI generating code, or an AI reviewing another's work. It's the
reference any new conversation (Claude, DeepSeek, or any other assistant)
must read first.

**Never called `AGENTS.md`** — that name belongs to a previous-version
convention of the project, already retired.

---

## 1. Project identity

SIGMA is a multi-agent ecosystem for Big Data analysis, built 100% on an
open-source, free stack in its `SIGMA-FE` variant. The project's sole
operator is Marx Agustín García Delgado — a multi-operator architecture
was evaluated and explicitly rejected.

**Recognized variants (by cost):**

| Variant | Meaning |
|---|---|
| `SIGMA-FE` (Full Engineer) | 100% self-hosted, no paid services, $0 — Milestone 1's canonical variant |
| `SIGMA-LE` (Low-Cost Engineer) | Minimal mix of paid services |
| `SIGMA-ME` (Medium-Cost Engineer) | Moderate paid services |
| `SIGMA-HE` (High-Cost Engineer) | Maximum capacity, paid services (pending Google Cloud credits to reflect in Vertex AI/Google AI Studio) |

**Transversal submodes (independent of the cost variant):**

| Submode | Meaning |
|---|---|
| `Dev` | Local, synthetic data, no real infrastructure |
| `Runtime` | Real deployment (future, Hetzner VPS) |

A submode applies to any variant — e.g. "SIGMA-FE in Dev mode" is valid
and is the combination used in Milestone 1's day-to-day development.

`SIGMA_VARIANT` is the canonical environment variable name for the cost
variant. Never `SIGMA_ENV` — explicitly evaluated and rejected adopting
that name from a parallel line of work, because the cost of propagating
the rename across the whole project wasn't justified by the cosmetic benefit.

---

## 2. Working protocol — non-negotiable

Every agent working on SIGMA follows this order, without exception:

1. **Audit before generating.** Search prior conversations and the
   project for whether something similar already exists, before
   proposing something new. Never claim a file exists without having
   verified it.
2. **Propose structure, not code, first.** Present the files about to
   be generated and the open decisions that need operator confirmation,
   before writing a single line.
3. **Full text before file.** Complete content is shown in the
   conversation for review before the physical file is created.
4. **Verify after generating.** Run tests, `grep`/`findstr`, counts —
   any mechanical verification available — before considering a
   delivery closed.

This protocol exists because its absence already caused a real,
documented problem: two separate lines of work ("Eco MultiAgentes 3
Skills 1" and "Eco MultiAgentes 4 Skills 2") built the same 6 Milestone 1
skills in parallel, neither aware of the other, producing duplicate work
that took a full audit session to reconcile (see
`docs/reportes/fusion_0001_0002_v2.0.0.md`).

---

## 3. Artifact naming conventions

**Skill vs. skill.py.** `Skill` (capitalized, or `SKILL.md`) refers
exclusively to the specification — the document describing what the
skill does. `skill.py`, always lowercase, is the executable code.
"Skill.py" with a capital S is never used under any circumstance — the
way it's written must be unambiguous about which of the two it refers to.

**Versioning — never overwritten, always preserved.** Every script,
skill, or artifact keeps its version number in the filename when it's
archived (e.g. `0000_skill_v2.py` in `scripts/old_scripts_sigma/`).
Overwriting or renaming a versioned file is never suggested — each
version is kept for traceability.

**`scripts/old_scripts_sigma/` is conceptually read-only.** It contains
historical versions replaced in the active tree. No file there is
executed or imported by the pipeline. Explicitly marked "DO NOT TOUCH"
in its own `README.md`.

---

## 4. Artifact centralization protocol

Before delivering any set of files, the agent explicitly states the
scope of the delivery, and asks when it isn't clear:

- **A single script** — one file.
- **A group of scripts** — several related files, explicitly delimited
  by the operator.
- **A complete Skill** — the 7 canonical artifacts for that specific
  folder (see ADR-009), delivered together, not split across separate
  messages.

The most convenient scope for the agent is never assumed — it's asked
when it isn't unambiguous.

---

## 5. Technical contract for each skill

See **ADR-009** for the full detail. Summary: 7 canonical files per
skill (`SKILL.md`, `defaults.yaml`, `skill.py`, `references/schemas.md`,
`evals/eval_adherencia.yaml`, `tests/test_{name}.feature`,
`tests/test_000X_{name}.py`), `skill.py` loaded dynamically by file path
(`sigma/skills/_loader.py`) due to the invalid-Python-identifier problem
in hyphenated folders, and no hardcoded constant that `defaults.yaml`
already declares as configurable.

Every successful skill output explicitly includes `run_id` and
`trace_id`, without exception.

Shared pytest-bdd fixtures (`ctx`, `make_state`) live in the root
`conftest.py`, automatically available to every skill without needing
explicit imports.

---

## 6. Epistemic restriction K ⊆ X (ADR-008)

No skill infers, imputes, or fills in information beyond what its input
data or deterministic observation allows. Detection of target columns,
language, or any structural feature is always structural (does the key
exist?), never semantic (what does the key mean?).

---

## 7. Security boundaries — non-negotiable, no exceptions

Any future SIGMA work related to pentesting, anti-hacking protocols, or
third-party system vulnerability analysis operates exclusively under
these conditions: the operator's own systems, client systems under
signed contract, or bug bounty programs with explicit authorization
(HackerOne, Bugcrowd, Intigriti). Scanning or accessing a system without
prior authorization from its owner is out of scope with no exception,
regardless of whether the organization is for-profit, whether the flaw
found is real, or whether the ultimate intent is commercially beneficial
to that organization.

---

## 8. Milestone numbering — current

| Milestone | Content |
|---|---|
| Milestone 1 | Linear LangGraph pipeline, 6 skills (0000-0003, 0008, 0011) — closed, 65/65 tests passing |
| Milestone 2 | Three-orchestrator architecture with subgraphs (hierarchical Director/Engineer pattern, ADR-016), read-only context injected at startup (never live mutable shared memory) |
| Milestone 3 | Real-time streaming (ADR-015), Hamilton Selector among Kafka/Redis Streams/Faust |
| Future milestones (unnumbered) | Financial analysis of cardholders (anonymized/pseudonymized data), video/image analysis, security work under the boundaries in section 7 |

---

## 9. Status against agent interoperability standards

Consistent with SIGMA's philosophy of building governance before flashy
functionality, Milestone 1 established the complete Harness (ADRs
001-013) before addressing the agent interoperability layer. This table
documents the real status of each standard today:

| Standard | Role | Status in SIGMA |
|---|---|---|
| MCP | Connects models to tools/data | Not implemented — evaluated for Milestone 2 |
| A2A | Agent-to-agent negotiation, Agent Cards | Not implemented — no current component has an Agent Card; a candidate for Director/Engineer/Auditor (ADR-016) |
| A2UI | Secure generative interfaces | Not implemented — a candidate for Milestone 3's reactive dashboards (ADR-015) |
| AP2 / UCP | Autonomous commerce between agents | Out of scope — SIGMA doesn't handle transactions |

Neither any skill nor Milestone 1's orchestrator constitutes an
"Agent" in the strict A2A sense: they are the orchestration logic and
the functions the Harness coordinates. Formalizing this layer is
explicit Milestone 2 work, not a Milestone 1 omission.

---

## 10. Changelog

| Version | Date | Change |
|---|---|---|
| 1.0.0 | Eco MultiAgentes 4 Skills 2, July 2026 | First generation as a real file. Previously only referenced, never materialized. Consolidates decisions already made across multiple conversations. |
| 1.1.0 | July 2026 | Updated to SIGMA v1.7. Migrated the variant scheme from Full/Lite/Dev/Runtime to SIGMA-FE/LE/ME/HE with Dev/Runtime as transversal submodes. Unified into a single repository (`PensadorZ/SIGMA`) — the split between a documentation repo and a code repo is retired. Code paths updated to reflect the restructuring inside the `sigma/` package (`sigma/skills/`, `sigma/core/`, `sigma/hooks/`). Corrected the historical-archive folder name to `scripts/old_scripts_sigma/`. |
| 1.2.0 | July 2026 | Incorporates the Agent = Model + Harness formula and documents the real status against agent interoperability standards (MCP, A2A, A2UI, AP2, UCP), verified against the "Vibecoding with Multi-Agent Systems" course (Google-Kaggle). No Milestone 1 component is an A2A-compliant Agent — it's the Harness that precedes them, by design. |