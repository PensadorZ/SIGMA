---
id: ADR-README
title: Architecture Decision Records Index — SIGMA
version: 1.6
status: Active
revision-date: 2026-07
approved-by: Prof. Marx A. García Delgado
---

# Architecture Decision Records Index — SIGMA

This document is the entry point to SIGMA's architectural decision
system. It contains no decisions of its own: it organizes, describes,
and relates the ecosystem's ADRs, showing how they connect to each other
and which variants and submodes each one applies to. Any agent,
developer, or operator who needs to understand why the system works the
way it does — and not some other way — should start here, before
touching any code or proposing a design change.

---

## How to read the ADRs

Every ADR has five mandatory sections: frontmatter with metadata, an
executive summary explaining that version's changes, context, decision,
and consequences. All of them include a **version history** at the end:
changes from previous versions carry numbered literals (e.g. `a.1.2`,
`b.1.3`), and changes in the current version carry unnumbered literals
(`a`, `b`). ADRs for future Milestones include the `hito-de-aplicacion`
(applicable-milestone) field in the frontmatter.

---

## Reference rule

Every ADR references a minimum of three prior ADRs. This guarantees that
decisions aren't isolated, and that any change to an ADR triggers a
review of everything that depends on it.

---

## Possible statuses

| Status | Meaning |
|---|---|
| ✅ **Accepted** | Decision in effect, implemented or being implemented |
| 🟡 **Proposed** | Under review, pending approval |
| 🔄 **Superseded** | Replaced by a later ADR. The old ADR is kept with its updated status and a link to its successor |
| ⛔ **Deprecated** | Retired with no direct replacement |

## Table 1 — Full ADR log

| ADR | File | Title | Status | Version |
|---|---|---|---|---|
| ADR-001 | [adr-001-memoria-epistemica.md](adr-001-memoria-epistemica.md) | Epistemic Memory — Feature Store and Assumption Graph | ✅ Accepted | **1.5** |
| ADR-002 | [adr-002-mapreduce-skills.md](adr-002-mapreduce-skills.md) | Massive Intra-Skill Parallelism via MapReduce | ✅ Accepted | **1.4** |
| ADR-003 | [adr-003-equipo-3-colores.md](adr-003-equipo-3-colores.md) | Automated Security with a Red/Blue/Green Model | ✅ Accepted | **1.4** |
| ADR-004 | [adr-004-vibe-diff-mfa.md](adr-004-vibe-diff-mfa.md) | Persistent Vibe Diff and Human-in-the-Loop with MFA | ✅ Accepted | **1.6** |
| ADR-005 | [adr-005-policy-server.md](adr-005-policy-server.md) | Hybrid Policy Server — Structural and Semantic | ✅ Accepted | **1.4** |
| ADR-006 | [adr-006-context-placeholders.md](adr-006-context-placeholders.md) | Context Hygiene with Placeholders and ContextResolver | ✅ Accepted | **1.4** |
| ADR-007 | [adr-007-evaluacion-multidimensional.md](adr-007-evaluacion-multidimensional.md) | Multidimensional Evaluation (7D) with LLM-as-Judge | ✅ Accepted | **1.4** |
| ADR-008 | [adr-008-restriccion-epistemica.md](adr-008-restriccion-epistemica.md) | Strict Epistemic Containment (K ⊆ X) | ✅ Accepted | **1.4** |
| ADR-009 | [adr-009-especificacion-skills.md](adr-009-especificacion-skills.md) | Skill Specification — Gherkin, LTL, and Granular Structure | ✅ Accepted | **1.7** |
| ADR-010 | [adr-010-gestion-secretos.md](adr-010-gestion-secretos.md) | Secrets Remediation Directive — 12-Factor | ✅ Accepted | **1.4** |
| ADR-011 | [adr-011-trazabilidad-langfuse.md](adr-011-trazabilidad-langfuse.md) | Pipeline Traceability in Langfuse V2 | ✅ Accepted | **1.5** |
| ADR-012 | [adr-012-versionado-skills.md](adr-012-versionado-skills.md) | Skill Version Management and Promotion | ✅ Accepted | **1.4** |
| ADR-013 | [adr-013-auditoria-trayectoria.md](adr-013-auditoria-trayectoria.md) | Agent Trajectory Audit | ✅ Accepted | **1.4** |
| ADR-014 | [adr-014-generacion-dinamica-skills.md](adr-014-generacion-dinamica-skills.md) | Dynamic Generation of New Skills on Demand | 🟡 Proposed | **1.1** |
| ADR-015 | [adr-015-hamilton-selector-streaming.md](adr-015-hamilton-selector-streaming.md) | Real-Time Analysis Architecture with Hamilton Selector | 🟡 Proposed | **1.2** |
| ADR-016 | [adr-016-orquestacion-jerarquica.md](adr-016-orquestacion-jerarquica.md) | Three-Orchestrator Hierarchical Orchestration (Director/Engineer/Auditor) | 🟡 Proposed | **1.1** |

---

## Table 2 — ADR dependency map

| ADR | Depends on | Is read by |
|---|---|---|
| ADR-001 | — | ADR-007, ADR-008, ADR-015 |
| ADR-002 | ADR-001 | ADR-008, ADR-009, ADR-015, ADR-016 |
| ADR-003 | ADR-004, ADR-005 | ADR-011, ADR-013, ADR-016 |
| ADR-004 | ADR-003, ADR-005, ADR-010 | ADR-003, ADR-013, ADR-014 |
| ADR-005 | ADR-006, ADR-010 | ADR-003, ADR-004, ADR-011, ADR-013 |
| ADR-006 | ADR-005, ADR-010 | ADR-009 |
| ADR-007 | ADR-001, ADR-008, ADR-011 | ADR-016 |
| ADR-008 | ADR-001, ADR-002 | ADR-007, ADR-013, ADR-015, ADR-016 |
| ADR-009 | ADR-002, ADR-006 | ADR-011, ADR-012, ADR-014, ADR-015, ADR-016 |
| ADR-010 | ADR-004, ADR-005, ADR-006 | ADR-012, ADR-015 |
| ADR-011 | ADR-003, ADR-005, ADR-007, ADR-009 | ADR-012, ADR-013, ADR-016 |
| ADR-012 | ADR-009, ADR-010, ADR-011 | ADR-014, ADR-015 |
| ADR-013 | ADR-003, ADR-005, ADR-008, ADR-011 | ADR-016 |
| ADR-014 | ADR-003, ADR-004, ADR-009, ADR-012 | — |
| ADR-015 | ADR-002, ADR-008, ADR-009, ADR-010, ADR-012 | ADR-016 |
| ADR-016 | ADR-002, ADR-003, ADR-009, ADR-011, ADR-013 | — |

---

### Table 3 — Applicability by variant and submode

| ADR | Cost variants (FE/LE/ME/HE) | Dev (transversal) | Runtime (transversal) |
|---|---|---|---|
| ADR-001 | Mandatory | Partial | Mandatory |
| ADR-002 | Mandatory | Partial | Mandatory |
| ADR-003 | Mandatory | Not applicable | Mandatory |
| ADR-004 | Mandatory | Relaxed | Mandatory |
| ADR-005 | Mandatory | Structural only | Mandatory |
| ADR-006 | Mandatory | Mandatory | Mandatory |
| ADR-007 | Mandatory | Partial | Mandatory |
| ADR-008 | Mandatory | Mandatory | Mandatory |
| ADR-009 | Mandatory | Mandatory | Mandatory |
| ADR-010 | Mandatory | Mandatory | Mandatory |
| ADR-011 | See note (*) | Optional | Mandatory (self-hosted) |
| ADR-012 | Mandatory | Partial | Mandatory |
| ADR-013 | Mandatory | Optional | Mandatory |
| ADR-014 | Mandatory | Not applicable | With approval |
| ADR-015 | Milestone 3 | Not applicable | Milestone 3 with approval |
| ADR-016 | Milestone 2 | Partial | Milestone 2 |

(*) ADR-011 is the one real exception: it varies by stack cost, not by
governance. SIGMA-FE and SIGMA-LE use self-hosted Langfuse; SIGMA-ME and
SIGMA-HE use Langfuse Cloud / LangSmith (see SIGMA_v1.7.md, cost
comparison table).

---

## Modification protocol

ADRs are immutable once accepted. If a decision changes, a new version
of the same ADR is created. The history is never erased. A change to an
ADR requires reviewing every ADR that references it as a direct dependency.

---

## Review notes by table

- **ADR-001 → v1.5:** Context expanded with its role as K⊆X's foundation. Zeugmatization conceptual note added.
- **ADR-002 → v1.4:** Context expanded explaining its role as an ADR-009 extension.
- **ADR-003 → v1.4:** Context expanded with the three risk phases it covers.
- **ADR-004 → v1.6:** Context expanded as the closure to ADR-001/002's autonomy. v1.5 literals renumbered.
- **ADR-005 → v1.4:** Context expanded as interception upstream of the Vibe Diff and Red/Blue/Green.
- **ADR-006 → v1.4:** Context expanded as the portability mechanism across variants.
- **ADR-007 → v1.4:** Context expanded distinguishing honesty (K⊆X) from quality (7D).
- **ADR-008 → v1.4:** Context expanded as the central epistemic law ADR-001/002/007 depend on.
- **ADR-009 → v1.7:** Context expanded as the contract ADR-002/006/011 depend on.
- **ADR-010 → v1.4:** Context expanded as the foundation for ADR-004/005/006.
- **ADR-011 → v1.5:** Context expanded as the shared correlation layer for ADR-003/005/007. v1.4 literals renumbered.
- **ADR-012 → v1.4:** Context expanded as the operational process for ADR-009's tests/ mandate.
- **ADR-013 → v1.4:** Context expanded as the real implementation of D6 (ADR-007). Fixed broken "ADR-00" reference to **ADR-016**.
- **ADR-014 → v1.1:** Context expanded as the ecosystem's highest-risk scenario.
- **ADR-015 → v1.2:** Context expanded as the extension reserved since ADR-009, coexisting with ADR-016.
- **ADR-016 → v1.1:** Context expanded explaining its dual purpose: formalizing LangGraph and governing Milestone 2.

## Notes from the July 2026 review (index v1.5)

- **ADR-001 → v1.5:** Context expanded to explain what Epistemic Memory
  is and why it exists in the ecosystem (operational foundation of
  K ⊆ X, ADR-008) before descending into the technical problem. Added a
  conceptual cross-reference note to epistemological Zeugmatization,
  explicitly scoped outside the ADR's technical requirements.
- **ADR-004 → v1.5:** the HITL mechanism was updated to the one verified
  in Milestone 1 (LangGraph `interrupt()` + SqliteSaver); Redis polling
  moved to a discarded alternative.
- **ADR-009 → v1.5:** the seven-mandatory-canonical-artifacts protocol,
  verified against 65/65 tests; catalog extended to 20 skills (0000–0019).
- **ADR-001 → v1.4 and ADR-011 → v1.4:** minor adjustments verified in
  Milestone 1 (KS-test as the sole method / Langfuse `:2` pin +
  `langfuse<3`).
- **ADR-015 → v1.1:** migrated to the canonical format from "Eco
  MultiAgentes 4 Skills 2," keeping the correction of the false reference
  to ADR-011.
- **ADR-016 → v1.0 (new):** settles Milestone 2's documentation debt
  (three-orchestrator hierarchy) and formally registers LangGraph as the
  orchestration engine — the decision no prior ADR had backed.
- **Table 3 → v1.6:** collapsed from four columns (Full/Lite/Dev/Runtime)
  to a single cost-variant column (FE/LE/ME/HE) + two transversal columns
  (Dev/Runtime), reflecting the renaming applied in SIGMA_v1.7.md. The
  one real exception is ADR-011 (self-hosted Langfuse vs. Cloud),
  documented in the footnote.
- **ADR-016 → title updated:** the third orchestrator, Auditor, was added
  to the pattern's name (previously just "Director/Engineer"). No fixed
  canonical order among the three — "Director/Engineer/Auditor" is used
  for consistency with the rest of the documentation.
