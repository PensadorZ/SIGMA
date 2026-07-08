---
id: ADR-007
title: Multidimensional Evaluation (7 Dimensions) with LLM-as-Judge
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-007 v1.3
minimum-references: ADR-001, ADR-008, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-007: Multidimensional Evaluation (7 Dimensions) with LLM-as-Judge

## Executive summary of changes in v1.4

The Context section is expanded to first explain what this framework
evaluates and why it's different from K ⊆ X (ADR-008) — one measures
whether the output is honest, the other whether it's good — before
descending into the detail of the layers and the seven dimensions.

## Executive summary of changes in v1.3

Added Fig. 1 with the evaluation-layer diagram in execution order. Added
Table 1 with the seven dimensions, their method, and their cost.
Incorporated the version history.

---

## Context

Multidimensional Evaluation is the mechanism that decides whether a
technically correct result is also a *good* result — and it exists
because "passing the tests" and "being a quality result" aren't the same
thing. Without this framework, SIGMA would only know whether a skill
worked, never whether it worked well: whether it spent a reasonable
amount of resources, whether it understood what the user actually
wanted, or whether the code it produced is maintainable. This ADR works
alongside Epistemic Containment K ⊆ X (ADR-008, the constraint on what
can be asserted as true) and the traceability from ADR-011 (where each
evaluation gets logged), but it solves a different problem from both: not
whether the output is honest, but whether the output is good.

A pipeline that passes its unit tests can still misread the user's
intent, spend ten times more resources than necessary, need five
corrections before landing on what was actually requested, or produce
code that's functional but unreadable. Traditional evaluation frameworks
measure one or two dimensions — typically functional correctness alone.
SIGMA needs a complete framework that captures the seven real facets of
what makes a result good.

---

## Decision

### Fundamental separation

`K ⊆ X` **is not an evaluation dimension**. It's a system invariant that
operates before evaluation, in the `OutputSchema`'s Pydantic validation
layer. If the output violates `K ⊆ X`, the pipeline fails with
`OUTPUT_SCHEMA_VIOLATION` before reaching any dimension. There's no
contradiction between the LLM-as-Judge's 5% sampling and the epistemic
constraint, because they operate in different layers with different purposes.

### Fig. 1 — Evaluation layers in execution order

```
Skill output
        │
        ▼
LAYER 0 — Pydantic validation (100% of runs)
  Verifies K⊆X: does the output only contain fields derivable from the data?
  ├─ FAILS → OUTPUT_SCHEMA_VIOLATION → pipeline ends
  └─ PASSES ↓
        ▼
LAYER 1 — Fast deterministic evaluator (100% of runs)
  Verifies: statistical rules, required fields, ranges, known biases
  No LLM token consumption
  ├─ ANOMALY detected → triggers LLM-as-Judge (in addition to routine sampling)
  └─ OK ↓
        ▼
LAYER 2 — LLM-as-Judge (5% of runs + anomaly-triggered activations)
  Evaluates D1: user intent
  Model: different from the Orchestrator (ADR-005 principle)
        │
        ▼
Evaluation artifacts → Langfuse V2 (pipeline's parent trace)
```

### Table 1 — The seven evaluation dimensions

| # | Dimension | Evaluation method | Cost |
|---|---|---|---|
| **D1** | User intent | LLM-as-Judge (5% + anomaly-triggered activations) | Low |
| **D2** | Functional correctness | Deterministic tests + Pydantic | Zero |
| **D3** | Visual/behavioral correctness | HTML/dashboard schema validation | Zero |
| **D4** | Cost and efficiency | Langfuse metrics (tokens, time, session convergence) | Zero |
| **D5** | Code quality | Static analysis (`pylint`, `bandit`) | Zero |
| **D6** | Trajectory quality | Comparison against `expected_trajectory` in SKILL.md | Zero |
| **D7** | Self-repair capability | Successful-retry ratio vs. escalated to HITL | Zero |

All evaluations are stored in Langfuse V2 as artifacts of the parent
trace, per ADR-011.

---

## Positive consequences

- 95% of evaluations consume no LLM tokens.
- Session convergence (D4) objectively captures perceived user quality
  without surveys.
- Accumulated evaluations allow detecting quality degradation over time.

## Negative consequences

- LLM-as-Judge introduces subjectivity. The 5% sampling limits the
  impact but doesn't eliminate it.
- The expected trajectory in `SKILL.md` must be kept up to date.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Unit tests only | Don't capture intent, efficiency, or trajectory |
| LLM-as-Judge at 100% | Prohibitive cost |
| External frameworks (Ragas, TruLens) | SIGMA's 7 dimensions are more specific |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Declared the separation between K⊆X (100% Pydantic) and
  intent evaluation (5% LLM-as-Judge), resolving the apparent
  contradiction with ADR-008.
- **b.1.2** Added the 100% fast deterministic evaluator as the first
  evaluation layer.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the evaluation-layer diagram in execution
  order.
- **b.1.3** Added Table 1 with the seven dimensions, their method, and
  their cost.

**Changes in v1.4:**
- **a** Expanded Context to explain what this framework evaluates and
  why it's different from K ⊆ X (ADR-008), before descending into the
  detail of the layers and the seven dimensions.
