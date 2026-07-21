---
id: ADR-008
title: Strict Epistemic Containment (K ⊆ X)
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-008 v1.3
minimum-references: ADR-001, ADR-002, ADR-007
approved-by: Prof. Marx A. García Delgado
---

# ADR-008: Strict Epistemic Containment (K ⊆ X)

## Executive summary of changes in v1.4

The Context section is expanded to first explain that K ⊆ X is SIGMA's
central epistemic law, one that ADR-001, ADR-002, and ADR-007 all depend
on — before descending into the detail of the three implementation layers.

## Executive summary of changes in v1.3

Added Fig. 1 with the diagram of the three implementation layers. Added
Table 1 with the standard response states for different insufficient-data
situations. Incorporated the version history.

---

## Context

Epistemic Containment K ⊆ X is SIGMA's central epistemic law: it's the
constraint that Epistemic Memory (ADR-001, which splits facts from
assumptions precisely so this constraint can be applied to each
separately), the `trace_id` propagation ADR-002 requires, and the
Multidimensional Evaluation in ADR-007 (which evaluates *quality* given
that the *honesty* of the output is already guaranteed here, not the
other way around) all depend on, directly or indirectly. Without this
constraint, none of those pieces would have a unifying principle
connecting them.

Language models generate statistically plausible text. When the context
doesn't contain the necessary information, the model fills the gap with
text that can be factually incorrect. In SIGMA, a hallucination isn't
just a quality error: it can be a business error with real consequences.

---

## Decision

Every SIGMA agent operates under the formal constraint `K ⊆ X`, where:
- **X** = the set of real data observed in the current execution
- **K** = the set of claims the agent is allowed to make

The agent is **prohibited** from making claims about elements outside X.

### Fig. 1 — The three implementation layers of K ⊆ X

```
LAYER 1 — Contract in the Orchestrator's prompt
─────────────────────────────────────────────────
"You may only use knowledge from the data in X_observed.
 On information gaps → INSUFFICIENT_DATA.
 Hypotheses must be flagged as ASSUMPTION in the
 Assumption Graph (ADR-001)."

         ↓ If the output attempts to include claims outside X:

LAYER 2 — Automatic verification with Pydantic
─────────────────────────────────────────────────
The skill's OutputSchema only allows fields derivable
from the input data.
  ├─ VIOLATION → OUTPUT_SCHEMA_VIOLATION → pipeline ends
  └─ OK → output leaves the skill

         ↓ For legitimate hypotheses that go beyond X:

LAYER 3 — Assumption Graph (ADR-001)
─────────────────────────────────────────────────
assumption_graph.add(
  entity="...",
  claim="...",
  evidence_count=N,
  status="PROPOSED"   ← Never presented as fact in the output
)
```

### Data lineage as an implementation requirement

For a claim to be verifiable as belonging to X, every row of the dataset
must carry a `trace_id` field that allows tracing its origin and
transformations per ADR-002. Without lineage, `K ⊆ X` is verifiable only
at the schema level, not at the individual data-point level.

### The constraint applies 100% of the time

Pydantic verification operates on 100% of outputs. ADR-007's 5%
LLM-as-Judge is an evaluation of user intent, not of epistemic
containment. They're different layers with different purposes.

### Table 1 — Standard responses to insufficient data

| Situation | Standard response | Processable by the Orchestrator |
|---|---|---|
| Data completely absent | `INSUFFICIENT_DATA` indicating the missing data | Yes |
| Data outside the acceptable range | `DATA_OUT_OF_RANGE` with the received value and expected range | Yes |
| Hypothesis based on inference | `ASSUMPTION` with the claim, available evidence, and `PROPOSED` status in the Graph | Yes |
| Data present with low model confidence | `UNCLEAR` with the confidence score | Yes |

---

## Positive consequences

- Eliminates hallucinations by design, not by prompt engineering.
- Outputs are auditable: every claim can be traced back to its source
  data point in X.
- Pydantic verification is automatic and zero-cost.

## Negative consequences

- The agent can't make creative generalizations based on its training.
- `INSUFFICIENT_DATA` outputs can frustrate users expecting a complete answer.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Prompt engineering only | The model ignores the instruction under context pressure |
| RAG without K⊆X | Reduces hallucinations but doesn't formally eliminate them |
| Model confidence threshold | Models are poorly calibrated |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added data lineage as an implementation requirement of K⊆X.
- **b.1.2** Reinforced that the constraint applies to 100% of results via
  Pydantic, clarifying the distinction from the LLM-as-Judge's 5%.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the diagram of the three implementation layers.
- **b.1.3** Added Table 1 with the standard response states for
  different insufficient-data situations.

**Changes in v1.4:**
- **a** Expanded Context to explain that K ⊆ X is SIGMA's central
  epistemic law, one that ADR-001, ADR-002, and ADR-007 all depend on,
  before descending into the detail of the three implementation layers.
