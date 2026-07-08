# SIGMA v1.7 — Integrated System for Multi-Agent Management

> **SIGMA is not an answer. It's the system that learns to answer.**

SIGMA is an autonomous agent ecosystem for analyzing, designing,
calculating, and deciding across diverse situations and levels of
complexity, from exploratory analysis of a dataset to the full design
of a production pipeline. Every decision the system makes is backed by
explicit governance — epistemic memory, hallucination containment
(`K ⊆ X`), and full traceability — instead of tacit convention.

Multiple specialized agents collaborate under a triangular central
orchestration architecture — the proposal comes with the designation of
three orchestrators, Director/Auditor/Engineer (see ADR-016), who work
together to tackle projects in the domains of Data Engineering, Data
Science, Data Analysis, General Engineering, Physics, Mathematics, and
Axiometrics.

---

## Ecosystem status

### Canonical documents

| # | Document | Version | Status |
|---|---|---|---|
| 01 | README.md | — | ✅ Operational |
| 02 | AGENTS_CREATOR.md | — | ✅ Operational |
| 03 | SIGMA_v1.7.md (this document) | 1.7 | ✅ Operational |
| 04 | PROJECT_FRAMEWORK.md | 1.1.0 | ✅ Operational |
| 05 | SKILL_STANDARD.md | 1.0.0 | 🔄 Under review |
| 06 | PIPELINES.md | — | ⬜ Pending |
| 07 | INSTALL.md | — | ⬜ Pending |
| 08 | TROUBLESHOOTING.md | 1.1 | ✅ Operational |

### Architecture Decision Records (ADRs)

| ADR | Title | Version | Status |
|---|---|---|---|
| ADR-001 | Epistemic Memory — Feature Store + Assumption Graph | 1.3 | ✅ Accepted |
| ADR-002 | Massive Intra-Skill Parallelism via MapReduce | 1.3 | ✅ Accepted |
| ADR-003 | Automated Security with a Red/Blue/Green Model | 1.3 | ✅ Accepted |
| ADR-004 | Persistent Vibe Diff and Human-in-the-Loop with MFA | 1.4 | ✅ Accepted |
| ADR-005 | Hybrid Policy Server — Structural + Semantic | 1.3 | ✅ Accepted |
| ADR-006 | Context Hygiene with Placeholders and ContextResolver | 1.3 | ✅ Accepted |
| ADR-007 | Multidimensional Evaluation (7 Dimensions) with LLM-as-Judge | 1.3 | ✅ Accepted |
| ADR-008 | Strict Epistemic Containment (K ⊆ X) | 1.3 | ✅ Accepted |
| ADR-009 | Skill Specification with Gherkin + LTL | 1.4 | ✅ Accepted |
| ADR-010 | Secrets Remediation Directive — 12-Factor | 1.3 | ✅ Accepted |
| ADR-011 | Pipeline Traceability in Langfuse V2 | 1.3 | ✅ Accepted |
| ADR-012 | Skill Version Management and Promotion | 1.3 | ✅ Accepted |
| ADR-013 | Agent Trajectory Audit | 1.3 | ✅ Accepted |
| ADR-014 | Dynamic Generation of New Skills on Demand | 1.0 | 🔄 Proposed |
| ADR-015 | Real-Time Analysis Architecture with Hamilton Selector | 1.0 | 🔄 Proposed |
| ADR-016 | Three-Orchestrator Hierarchical Orchestration (Director/Engineer) | 1.0 | 🔄 Proposed |

### Skill catalog (16 skills)

> ✅ Delivered · 🔄 In progress · ⬜ Pending · ⚠️ Needs clarification

| # | Skill | Responsibility | Status | Milestone |
|---|---|---|---|---|
| 0000 | `system-health-check` | Verifies MCP availability before the pipeline runs | ✅ Delivered v2.0.0 | Milestone 1 |
| 0001 | `data-ingestion` | Loads data from CSV, API, or database | ✅ Delivered v2.0.0 | Milestone 1 |
| 0002 | `data-cleanser` | Cleans duplicates, nulls, and normalizes text | ✅ Delivered v2.0.0 | Milestone 1 |
| 0003 | `data-preprocessor` | Scales, encodes, imputes, and balances classes | ✅ Delivered v2.0.0 | Milestone 1 |
| 0004 | `statistical-validator` | Detects drift, leakage, and confounders (2 modes) | ✅ Delivered v1.0.0 | Milestone 2 |
| 0005 | `framework-selector` | Selects ML/DL framework via Hamiltonian energy | ⬜ Pending | Milestone 2 |
| 0006 | `ml-trainer` | Classic sklearn models with cross-validation | ⬜ Pending | Milestone 2 |
| 0007 | `dl-trainer` | Neural networks with gradient control | ⬜ Pending | Milestone 2 |
| 0008 | `sentiment-analyzer` | Classifies polarity with local RoBERTa | ✅ Delivered v1.1.0 | Milestone 1 |
| 0009 | `cluster-analyzer` | Groups text via embeddings and K-Means | ⬜ Pending | Milestone 2 |
| 0010 | `engagement-calculator` | Computes interaction metrics by period | ⬜ Pending | Milestone 2 |
| 0011 | `viz-reporter` | Autonomous dashboard, budget-adaptive | ✅ Delivered v1.1.0 | Milestone 1 |
| 0012 | `code-reviewer` | Audits generated code before execution | ⬜ Pending | Milestone 2 |
| 0013 | `skill-discovery` | Dynamically lists available skills | ⬜ Pending | Milestone 2 |
| 0014 | `stride-modeling` | STRIDE threat modeling over pipelines | ⬜ Pending | Milestone 2 |
| 0015 | `pipeline-inspector` | Interactive queries on pipeline state | ⚠️ Pending clarif. | Milestone 2 |

> **Note on 0015-pipeline-inspector:** it still needs to be decided whether
> it operates as an LLM that reads DAG state from Langfuse, or as a query
> engine over Redis. This decision affects its expected_trajectory and
> output_schema. Will be clarified before writing its SKILL.md.

> **Note on 0016–0019 (reserved):** ADR-015 reserves these numbers for
> the Milestone 3 streaming work — `hamilton-selector` (0016, real-time
> message prioritization) and three Faust consumers (0017–0019). The full
> ecosystem catalog will reach 20 skills once implemented.

---

## Design philosophy

**Multi-agent by design.** Every responsibility — cleaning, calculating,
validating, visualizing — is owned by a specialized agent that collaborates
with the others through explicit interfaces and verifiable Gherkin + LTL
contracts.

**Security and governance built in.** Not as an afterthought, but as a
structural layer wrapping every step: pre-commit hooks, Policy Server,
Red/Blue/Green teams, STRIDE modeling before implementation.

**Continuous evaluation across 7 dimensions.** A correct result isn't
enough: it must also be efficient, reproducible, and faithful to the
user's real intent, with advanced tests for high-uncertainty cases.

**Cost-adaptable stack.** SIGMA can run at four operating cost tiers
(SIGMA-FE, free, up to SIGMA-HE, high performance), each also operable in
Dev or Runtime submode depending on the usage context.

**Epistemic containment K⊆X.** Every agent can only assert what it can
trace back to an observed data point. No hallucination can leak into the output.

---

## Application domains

| Domain | Main capabilities |
|---|---|
| Data Engineering | Ingestion, transformation, storage, and orchestration pipelines at scale |
| Data Science | ML/DL modeling, hypothesis validation, advanced statistical tests |
| Data Analysis | Exploration, visualization, interactive dashboards |
| General Engineering | System simulation, process optimization, automation |
| Physics | Numerical modeling, simulations, time-series analysis |
| Mathematics | Axiomatic systems, symbolic computation, assisted theorem proving |
| Axiometrics | Analysis of: Axiological Map, Inter-Agent Axiological Reasoning |

---

## System variants

Classification axis: **operating cost**, in four tiers. Each variant can
additionally operate in two transversal submodes, independent of cost:
**Dev** (debugging, relaxed constraints) and **Runtime** (deployed
instance with real data, MFA mandatory).

```bash
SIGMA_VARIANT=FE       # SIGMA Full Engineer — $0 cost
SIGMA_MODE=Dev         # optional transversal submode: Dev | Runtime | (empty = standard)
```

### Cost comparison table

| Criterion | SIGMA-FE | SIGMA-LE | SIGMA-ME | SIGMA-HE |
|---|---|---|---|---|
| Full name | Full Engineer | Low-Cost Engineer | Medium-Cost Engineer | High-Cost Engineer |
| Operating cost | $0 | Low | ~50% paid services | High |
| Engineering effort required | Very high | High | Medium | Low |
| Recommended profile | Senior engineer, willing to research in parallel | Mid-level engineer | Team with moderate budget | Company needing high performance |
| Pre-built paid services | None | Essentials only | ~50% of the stack | Most of the stack |
| Langfuse | Self-hosted | Self-hosted or basic Cloud | LangSmith / Cloud | LangSmith Enterprise |
| Storage | Local MinIO | Local MinIO | Managed GCS/S3 | GCS/S3 with SLA |
| LLM orchestrator | Gemini free tier / Ollama | Gemini free tier | Gemini Pro | Vertex AI or enterprise equivalent |

### Narrative description

**SIGMA-FE (Full Engineer)** — $0 cost. Requires genuine engineering
skill: not recommended for beginners or newcomers, unless they're willing
to research in parallel while setting up the first Milestone. Reference
variant — all active ADRs, 100% self-hosted stack.

**SIGMA-LE (Low-Cost Engineer)** — Pays for pre-built services, but only
the essential ones, at low cost. Reduces setup friction without
significantly impacting the budget.

**SIGMA-ME (Medium-Cost Engineer)** — Uses roughly 50% of its services in
paid mode. A middle ground between full self-management and complete
outsourcing.

**SIGMA-HE (High-Cost Engineer)** — High costs, reserved for companies
needing high performance and guaranteed support.

### Transversal submodes (apply to any of the four variants)

**Dev** — Relaxed constraints so as not to interrupt debugging: workers
forced to 1 (ADR-002), SMOTE replaced with class_weight, Red/Blue/Green
teams disabled, HITL disabled, Policy Server structural-only. Data is
synthetic or test data. Never used in production.

**Runtime** — The corresponding variant deployed with real data.
Requires TOTP MFA at the Approval Endpoint. Any dynamic skill generation
(ADR-014) requires operator approval regardless of impact level.

Example combination: `SIGMA-FE` in `Dev` mode is the typical, cost-free
local development environment; `SIGMA-HE` in `Runtime` mode is a
high-performance enterprise deployment with real production data.

---

## General architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│         User / CLI / Interactive Chat / A2UI Dashboard          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          Orchestrator (LangGraph + Gemini API / Ollama)         │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Skills (MCP)   │  │  A2A Agents     │  │  Policy Server │  │
│  │  0000 → 0015    │  │  Auditor        │  │  Structural    │  │
│  │                 │  │  Red Team       │  │  + Semantic    │  │
│  │                 │  │  Blue Team      │  │  (judge LLM ≠  │  │
│  │                 │  │  Green Team     │  │  Orchestrator) │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ Epistemic       │  │ 7D Evaluation   │  │ Approval       │  │
│  │ Memory          │  │ Intent          │  │ Endpoint       │  │
│  │ Feature Store   │  │ Correctness     │  │ (local HITL,   │  │
│  │ + Assumption    │  │ Cost · Code     │  │ port 8765)     │  │
│  │ Graph           │  │ Trajectory      │  │                │  │
│  │ (ADR-001)       │  │ Self-repair     │  │                │  │
│  │                 │  │ Visual (ADR-007)│  │                │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Chat API        │  │ Langfuse V2     │                      │
│  │ /chat/status    │  │ Full            │                      │
│  │ /chat/ask       │  │ traceability    │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            Infrastructure (per variant)                         │
│  PostgreSQL · Redis · MinIO · Ollama · Docker + WSL2            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Full execution flow

```text
1. INPUT
   User submits a prompt or selects a YAML pipeline
   └─ Orchestrator interprets the request

2. PLANNING
   Orchestrator builds a dynamic DAG
   └─ Reads each skill's frontmatter (ADR-009)

3. SECURITY PRE-FLIGHT [Runtime only]
   Red Team runs a cloned subgraph against test data
   └─ Detects vulnerabilities before touching real data (ADR-003)

4. EXECUTION
   DAG executes node by node
   ├─ Policy Server intercepts every tool call
   ├─ ContextResolver resolves ${VAR} before each skill
   └─ MapReduce workers / chain depending on configuration

5. CONTINUOUS EVALUATION
   At the end of each skill:
   ├─ Fast deterministic evaluator → 100% of executions
   └─ LLM-as-Judge → 5% of executions (+ anomalies)

6. HITL APPROVAL [If level ≥ MEDIUM]
   Orchestrator pauses the DAG
   ├─ Generates a Vibe Diff in MinIO (WORM)
   └─ Waits for a response at the Approval Endpoint (300s timeout)

7. COMPLETION
   Output produced
   ├─ All events traced in Langfuse (ADR-011)
   └─ Result stored in MinIO
```

---

## Cyclicity vs. Acyclicity in orchestration

SIGMA's main DAG is acyclic by design. This guarantees termination,
traceability, and epistemic containment K⊆X. However, SIGMA allows
controlled cycles within specific subgraphs.

**Why is the main DAG acyclic?**

A cycle in the main DAG could cause infinite loops, hinder trace
correlation in Langfuse, and reintroduce unobserved data into set X,
violating ADR-008.

**Where are controlled cycles allowed?**

| Mechanism | Implementation | Exit condition |
|---|---|---|
| MapReduce retries (ADR-002) | Loop within the skill node | Max counter (policies.yaml); if exceeded → Green Team |
| Green Team auto-refactor (ADR-003) | Subgraph: diagnosis → fix → re-run | Max 2 iterations; if not recovered → HITL |
| Approval Endpoint (ADR-004) | Redis polling every 5 seconds | Configurable timeout (default 300s) |
| Graph update (ADR-001) | Workers queue in Redis; FIFO serializer | No execution cycle; it's asynchronous |

**Example: Failure during statistical analysis**

```text
Main DAG (acyclic):
Ingestion → Cleansing → Analysis → Evaluation → End
                         │
                         ▼ (failure)
              ┌──────────────────────┐
              │  Green Team subgraph │
              │  ┌────────────────┐  │
              │  │  Diagnosis     │  │
              │  │  Fix           │  │
              │  │  Re-run        │  │
              │  └────────────────┘  │
              │  (max 2 times)       │
              └──────────────────────┘
                         │
              Fixed? → Yes → DAG continues
                     No → HITL
```

---

## Defense in depth

### Policy Server — Tool interceptor

Intercepts **all** tool calls before they execute.

| Layer | Mechanism | Latency | Coverage |
|---|---|---|---|
| Structural (YAML) | Deterministic rules by environment and role | < 5 ms | ~95% of calls |
| Semantic (judge LLM) | Model different from the Orchestrator | Variable | ~5% of calls (ambiguous cases) |

The judge LLM is always a different model from the Orchestrator (ADR-005).
If both were the same model, a compromised model could judge its own actions.

**Availability:**

All four cost variants (SIGMA-FE/LE/ME/HE) have both layers active by
default. **Dev** submode (transversal to any of the four) keeps the
structural layer always active, but the semantic layer becomes optional —
so as not to interrupt fast debugging cycles.

### Approval Endpoint — local HITL

Lightweight HTTP server on port 8765. No dependency on external services.

| Level | Criterion | Vibe Diff | Approval |
|---|---|---|---|
| LOW | Reversible, < 1000 rows | Not required | Automatic |
| MEDIUM | Reversible, > 1000 rows or PII | Required | Approval Endpoint |
| HIGH | Irreversible or impacts _prod | Required + WORM | Endpoint + MFA |
| CRITICAL | Deployment or bulk deletion | Required + max retention | Endpoint + hardware MFA |

### STRIDE Modeling (skill 0014)

Before implementing any production pipeline, the stride-modeling skill
analyzes the system design and identifies threats across six categories:
Spoofing, Tampering, Repudiation, Information Disclosure, Denial of
Service, and Elevation of Privilege. The result is a threat report that
feeds the "Security Boundaries and Assertions" section of PROJECT_FRAMEWORK.md.

### Pre-commit hook with auto-fix

```bash
# Install hook
cp hooks_SIGMA/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# With auto-fix
SIGMA_AUTO_FIX=true git commit -m "feat: new skill"
```

The hook runs custom Semgrep rules (hooks_SIGMA/semgrep_rules/) that
detect race conditions and hardcoded API keys in model initializations.

---

## Evaluation: 7 dimensions + advanced statistical tests

### The 7 dimensions (ADR-007)

| # | Dimension | Method | Token cost |
|---|---|---|---|
| D1 | User intent | LLM-as-Judge (5% of executions) | Low |
| D2 | Functional correctness | Deterministic tests + Pydantic | Zero |
| D3 | Visual correctness | HTML/dashboard schema validation | Zero |
| D4 | Cost and efficiency | Langfuse metrics | Zero |
| D5 | Code quality | Static analysis (pylint, bandit) | Zero |
| D6 | Trajectory quality | Comparison against expected_trajectory | Zero |
| D7 | Self-repair | Successful-retry ratio vs. HITL | Zero |

### Advanced tests under uncertainty (skill 0004)

| Project condition | Method applied | Verdict if evidence is weak |
|---|---|---|
| Explicit hypothesis declared | Bayes Factor (uniform prior by default) | INSUFFICIENT_EVIDENCE (BF < 3) |
| No hypothesis, unknown distribution | Permutation Test + Bootstrapping | PAUSED_HITL if CI too wide |
| Data with a time index | ADF Test + Granger Causality | APPROVED_WITH_WARNINGS if non-stationary |
| Live environment with immediate feedback | Bayesian A/B Testing (Multi-Armed Bandits) | INSUFFICIENT_EVIDENCE if too few samples |
| None of the above | Basic descriptives (nulls, variance, duplicates) | PAUSED_HITL if thresholds exceeded |

---

## Interaction channels

| Channel | Purpose | Active by default | Variant |
|---|---|---|---|
| CLI (python -m sigma run) | Pipeline execution | ✅ Yes | All |
| Approval Endpoint (port 8765) | HITL for critical actions | ✅ Yes | Runtime |
| Chat API (/chat/ask) | Queries during execution | ✅ Yes | All |
| Zulip | Notifications and approvals via chat | ⚠️ Optional | All |
| BurntToast (Windows) | Desktop alerts | ⚠️ Optional | All |
| A2UI Dashboard | Result visualization | ✅ Yes (viz-reporter) | All |

---

## Ecosystem components

| Component | Main function | ADR | Variant |
|---|---|---|---|
| Orchestrator (LangGraph) | Builds and runs the DAG | ADR-002, ADR-009, ADR-016 | All |
| Auditor Agent | Verifies trajectory, K⊆X, and quality | ADR-013 | All |
| Red Team | Simulated pre-flight attack | ADR-003 | Runtime |
| Blue Team | Model monitoring (AgBOM) | ADR-003 | All except Dev |
| Green Team | Automatic recovery and rollback | ADR-003 | All |
| Epistemic Memory | Feature Store + Assumption Graph | ADR-001, ADR-008 | All |
| 7D Evaluation | Continuous multidimensional evaluation | ADR-007 | All |
| ContextResolver | Resolves ${VAR} and sanitizes inputs | ADR-006 | All |
| Policy Server | Intercepts tools before execution | ADR-005 | All |
| Langfuse V2 | Centralized traceability of all events | ADR-011 | All |
| Secrets management | .env + get_required_env() | ADR-010 | All |
| Skill versioning | SemVer + Dev→Staging→Prod promotion | ADR-012 | All |
| Approval Endpoint | Local HITL with persistent Vibe Diff | ADR-004 | Runtime |
| Chat API | Interactive queries on pipeline state | — | All |

---

## Prerequisites by variant

> ✅ Required · ⚠️ Optional · ❌ Not applicable · (*) Replaceable with a paid service
> Dev and Runtime are transversal submodes — they don't alter this table
> by themselves, except for the recommended RAM reduction in Dev.

| Component | SIGMA-FE | SIGMA-LE | SIGMA-ME | SIGMA-HE | Minimum version |
|---|:---:|:---:|:---:|:---:|---|
| Python | ✅ | ✅ | ✅ | ✅ | 3.12.4 |
| Docker Desktop / Podman | ✅ | ✅ | ✅ | ✅ | 4.x |
| PostgreSQL | ✅ | ✅ | ✅ | ✅ | 14+ |
| Redis | ✅ | ✅ | ✅ | ✅ | 7+ |
| MinIO | ✅ | (*) | (*) | ❌ | latest |
| Ollama | ✅ | (*) | (*) | ❌ | latest |
| Langfuse V2 (self-hosted) | ✅ | (*) | (*) | ❌ | V2 |
| Gemini API (free tier) | ✅ | ✅ | (*) | ❌ | — |
| Gemini Pro / Vertex AI | ❌ | ❌ | (*) | ✅ | — |
| GCS / S3 | ❌ | ⚠️ | (*) | ✅ | — |
| BigQuery / AWS Athena | ❌ | ❌ | (*) | (*) | — |
| LangSmith | ❌ | ❌ | (*) | (*) | — |
| Neo4j Aura | ❌ | ❌ | (*) | (*) | — |
| Alpha Envolve (ext. validation) | ❌ | ❌ | (*) | (*) | — |
| Minimum RAM | 16 GB | 12 GB | 8 GB | — (managed) | — |
| Recommended RAM | 32 GB | 24 GB | 16 GB | — (managed) | — |

---

## Repository structure

```text
/
├── AGENTS_CREATOR.md           # Founding charter — defines all agents
├── README.md                   # Repository entry point
├── SIGMA_v1.7.md                # This document — Master Plan
├── TROUBLESHOOTING.md          # Real incidents and their resolution
├── PROJECT_FRAMEWORK.md        # Project lifecycle within SIGMA
├── SKILL_STANDARD.md           # Open standard for skill packaging
├── policies.yaml               # Tool policies by environment and role
│
├── pipelines/                  # Predefined YAML pipelines
│   └── analisis_opinion_twitter.yaml
│
├── specs/                      # Project specifications
│
├── skills/                     # 16 skills (0000–0015)
│   ├── 0000-system-health-check/
│   ├── 0001-data-ingestion/
│   ├── 0002-data-cleanser/
│   ├── 0003-data-preprocessor/    # ✅ Delivered v2.0.0
│   ├── 0004-statistical-validator/ # ✅ Delivered v1.0.0
│   ├── 0005-framework-selector/
│   ├── ...
│   └── 0015-pipeline-inspector/
│
├── agent_cards/                # External agent identity
│   ├── orchestrator.yaml
│   ├── auditor.yaml
│   ├── red_team.yaml
│   ├── blue_team.yaml
│   └── green_team.yaml
│
├── hooks_SIGMA/                # Cross-cutting deterministic scripts
│   ├── pre-commit.sh
│   └── semgrep_rules/
│       └── concurrency.yaml
│
├── endpoints/                  # Ecosystem APIs
│   ├── approval_endpoint.py
│   ├── chat_api.py
│   ├── dashboard_api.py
│   └── zulip_adapter.py
│
├── evals_SIGMA/                # Cross-cutting evaluations for all of SIGMA
├── assets_SIGMA/                # Shared global assets
├── references_SIGMA/           # Global ecosystem references
├── outputs/                    # Results, reports, and checkpoints
│
└── docs/
    └── adr/                    # 16 Architecture Decision Records
        ├── adr-README.md
        ├── adr-001-memoria-epistemica.md
        └── ... (adr-002 through adr-016)
```

> **Naming convention:** folders with the `_SIGMA` suffix are cross-cutting
> resources for the whole ecosystem. Folders without a suffix inside each
> skill (tests/, evals/, references/) are that skill's local resources.
> This distinction avoids collisions and lets anyone immediately identify
> which resources belong where.

---

## Implementation roadmap

### Milestone 1 — SIGMA v1.0 Executable

**Goal:** functional end-to-end pipeline with a real dataset.

**Required skills (6):**

| Skill | Status |
|---|---|
| 0000-system-health-check | ✅ Delivered v2.0.0 |
| 0001-data-ingestion | ✅ Delivered v2.0.0 |
| 0002-data-cleanser | ✅ Delivered v2.0.0 |
| 0003-data-preprocessor | ✅ Delivered v2.0.0 |
| 0008-sentiment-analyzer | ✅ Delivered v1.1.0 |
| 0011-viz-reporter | ✅ Delivered v1.1.0 |

**Dataset:** Tirendaz Twitter Sentiment (22,500 tweets)

**Deliverable:** the analisis_opinion_twitter.yaml pipeline running end to
end, producing an HTML dashboard with visible sentiment analysis.

**Success criterion:** a human can run `python -m sigma run pipelines/analisis_opinion_twitter.yaml` and see the dashboard in the browser without errors.

### Milestone 2 — SIGMA v1.5 Complete

**Goal:** complete ecosystem with all 16 skills, advanced statistical
tests, STRIDE security, interactive chat, and dynamic skill generation.

**Dataset:** WC2026-Tweets (target: 130K–28M tweets)

**Deliverable:** SIGMA at full production capacity, documented, tested,
and deployable with a single command.

**Migration of the variant scheme at the code level.** `orchestrator.py`,
  `sigma/core/pipeline_state.py`, and `sigma/skills/_common.py` (plus the
  duplicated type in `sigma/skills/0000-system-health-check/skill.py`)
  still use the `Full/Lite/Dev/Runtime` scheme as parallel values of
  `--variant`. Migrating to the current scheme (`SIGMA-FE/LE/ME/HE` +
  separate `Dev`/`Runtime` submode) touches 10 files, including the 6 test
  step definitions that simulate Dev mode via Gherkin — postponed to
  Milestone 2 so as not to risk Milestone 1's verified 65-test suite.

---

## Quick start

```bash
# 1. Initialize a SIGMA project (new in v1.5)
sigma init my-project
cd my-project

# 2. Configure environment variables
cp .env.example .env
# Required variables: GEMINI_API_KEY, SIGMA_VARIANT=FE

# 3. Bring up base services
docker compose up -d

# 4. Verify the system is operational
python -m sigma status

# 5. Run your first pipeline
python -m sigma run pipelines/analisis_opinion_twitter.yaml
```

---

## Usage examples

### Tweet sentiment analysis

```bash
python -m sigma run pipelines/analisis_opinion_twitter.yaml \
  --input data/tweets_raw.parquet \
  --workers 50 \
  --output outputs/opinion_dashboard.html
```

### STRIDE threat modeling before implementation

```bash
python -m sigma run pipelines/stride_analysis.yaml \
  --target pipelines/analisis_opinion_twitter.yaml \
  --output outputs/stride_report.md
```

### Interactive query during execution

```bash
# In another terminal while the pipeline is running:
curl -X POST http://localhost:8080/chat/ask \
  -d '{"question": "What hypotheses have you detected so far?"}'
```

---

## Compatibility and standards

| Standard / Platform | SIGMA equivalent | Notes |
|---|---|---|
| Google Cloud Trace | Langfuse V2 (self-hosted) | Exportable to Cloud Trace on higher-cost variants |
| Google Cloud Logging | Langfuse + local logs | Falls back to Redis and files (ADR-011) |
| BigQuery | PostgreSQL + DuckDB | Replaceable with BigQuery on SIGMA-ME/HE |
| Google Agent Registry | skill-discovery (0013) | SIGMA implements its own registry |
| Redis (cache and queues) | Redis with AOF persistence | Foundation for future streaming (ADR-015); used by MapReduce (ADR-002) |
| MinIO | MinIO (S3-compatible, self-hosted) | Object storage — dashboards, artifacts, WORM for Vibe Diff |
| Zulip (notification observability) | Zulip with separate topics (RUNS/HITL) | HITL and execution notifications, not trace observability — that's Langfuse |
| LangGraph | LangGraph (graph orchestrator) | Real engine for the skill DAG; fast-fail circuit breaker; formalized in ADR-016 |

> **v1.6 note — Vercel npx skills and Google Antigravity removed from this
> table.** They had been present since v1.5 with the note "Compatible by
> design," conditioned on `SKILL_STANDARD.md` — a document that was never
> completed (remains `🔄 Under review`). That row's origin was an
> external-positioning decision, not an ecosystem maintenance need. Removed
> because the compatibility claim had no verifiable support, and mixing it
> with real equivalents (Langfuse, PostgreSQL+DuckDB) diluted this table's
> credibility. See `docs/reportes/` for the full debate behind this decision.

---

## Additional documentation

| Document | Description |
|---|---|
| AGENTS_CREATOR.md | Founding charter — defines and creates all agents |
| PROJECT_FRAMEWORK.md | Project lifecycle, phases, and mitigations |
| SKILL_STANDARD.md | Open standard for skill packaging |
| PIPELINES.md | Guide to creating and running pipelines |
| INSTALL.md | Detailed step-by-step installation guide |
| TROUBLESHOOTING.md | Real incidents found and their exact resolution |
| docs/adr/ | 16 Architecture Decision Records |

---

## Changelog

> Changes from previous versions are recorded with literal + version number.
> Changes in this version use only the literal.

### Changes in v1.1 (initial baseline)

- **a.1.1** Definition of the SIGMA ecosystem with multi-agent architecture.
- **b.1.1** First set of ADRs (001–009).
- **c.1.1** Initial catalog of 7 skills without canonical numbering.

### Changes in v1.2

- **a.1.2** Addition of ADR-010 (secrets), ADR-011 (Langfuse), ADR-012
  (versioning), ADR-013 (trajectory audit).
- **b.1.2** Renamed AGENTS.md to AGENTS_CREATOR.md.
- **c.1.2** Formal definition of the four variants: Full, Lite, Dev, Runtime.

### Changes in v1.3

- **a.1.3** Incorporation of ADR-014 (dynamic skill generation).
- **b.1.3** Catalog expanded to 13 skills with canonical numbering 0000–0012.
- **c.1.3** In-depth documentation of the Policy Server and the Approval Endpoint.
- **d.1.3** Incorporation of Alpha Envolve as an optional external validation tool.

### Changes in v1.3.1

- **a.1.3.1** "Cyclicity vs. Acyclicity in orchestration" section — how SIGMA
  keeps a main acyclic DAG while allowing controlled cyclic subgraphs.

### Changes in v1.4 (intermediate version, merged into v1.5)

- **a.1.4** Resolution of the Full/ZERO inconsistency: "Full" remains the
  canonical technical name; "SIGMA ZERO" is the commercial name for the Full variant.
- **b.1.4** Corrected placeholder syntax from [[VAR]] to ${VAR} across all
  pipelines and documents.
- **c.1.4** Catalog expanded to 15 skills (addition of 0013, 0014, 0015).
- **d.1.4** Global folders renamed with a _SIGMA suffix to avoid collisions
  with each skill's local folders.

### Changes in v1.5

- **a** Incorporation of 3 new skills: skill-discovery (0013), stride-modeling
  (0014), pipeline-inspector (0015) — see full catalog.
- **b** Interactive chat: chat_api.py endpoint + pipeline-inspector skill for
  natural-language queries during pipeline execution.
- **c** Pre-commit hook with auto-fix (SIGMA_AUTO_FIX=true) and custom Semgrep
  rules in hooks_SIGMA/semgrep_rules/concurrency.yaml.
- **d** sigma init command to bootstrap projects from scratch.
- **e** SKILL_STANDARD.md as an open standard for skill packaging,
  compatible with Google Antigravity and Vercel npx skills.
- **f** Corrected description of SIGMA Lite: the difference from Full is the
  stack (paid services), not the security level.
- **g** Added implementation Roadmap with two concrete milestones.
- **h** Absorbed recommendations from Google's Vibecoding course (5 days):
  equivalences with Cloud Trace, Cloud Logging, and BigQuery are documented as
  SIGMA Lite options; they do not modify SIGMA Full.
- **i** Corrected catalog status after the full audit and merge of
  "Eco MultiAgentes 4 Skills 2": the 6 Milestone 1 skills (0000, 0001, 0002, 0003,
  0008, 0011) are confirmed as Delivered. Versions updated to the real
  post-merge ones (0000-0003 → v2.0.0; 0008, 0011 → v1.1.0, not v1.2.0 as
  this document previously stated before the correction). Verified against
  65/65 automated tests passing.

### Changes in v1.6

- **a** Added `ADR-015` (Real-Time Analysis Architecture with Hamilton
  Selector) to the ADR table — completely missing in v1.5.
- **b** Added 4 rows to "Compatibility and standards": Redis (cache and
  queues, foundation of the Milestone 3 streaming work), MinIO (object
  storage), Zulip (HITL/execution notifications, distinct from trace
  observability), LangGraph (the orchestrator's real engine).
- **c** Removed "Vercel npx skills" and "Google Antigravity" from the same
  table, after a documented debate (5 arguments per position): compatibility
  depended on `SKILL_STANDARD.md`, which was never completed (remains
  `🔄 Under review`); that row's origin was an external-positioning decision
  confirmed in a prior audit, not a technical need. See
  `docs/reportes/` for the full debate.
- **d** `SKILL_STANDARD.md` remains `🔄 Under review` with no closing date —
  determined that, as originally framed (tied to third-party platform
  compatibility), it adds no maintenance value; `ADR-009` already rigorously
  covers skill packaging format. Its only future justification would be an
  independent external publication decoupled from internal ADR governance,
  not yet confirmed.
- **e** ADR count updated from 14 to 15 across the repository structure and
  additional documentation tables.

### Changes in v1.7

- **a** Added `ADR-016` (Three-Orchestrator Hierarchical Orchestration,
  Director/Engineer pattern) to the ADR table. Formalizes LangGraph as the
  orchestration engine — a decision no prior ADR had backed. Total count
  updated from 15 to 16 ADRs throughout the document.
- **b** Corrected the Milestone 1 Roadmap: the text said "Required skills
  (5)" when the immediately following table lists 6 skills. Corrected to "(6)".
- **c** `TROUBLESHOOTING.md` added to "Canonical documents" and "Additional
  documentation" — a consolidated record of real incidents with their
  diagnosis and resolution.
- **d** Skill `0005` renamed from `hamilton-selector` to
  `framework-selector`. Reason: name collision with the "Hamilton Selector"
  from ADR-015 (skill `0016`, Milestone 3), which designates a completely
  different component (message prioritization in streaming, not ML/DL
  framework selection). The name "Hamilton Selector" is now reserved
  exclusively for `0016`, where it has formal mathematical backing in ADR-015.
- **e** **Complete renaming of the variant axis.** The Full/Lite notation is
  replaced with four explicit cost tiers: **SIGMA-FE** (Full Engineer, $0
  cost), **SIGMA-LE** (Low-Cost Engineer), **SIGMA-ME** (Medium-Cost
  Engineer), **SIGMA-HE** (High-Cost Engineer). The **Dev** and **Runtime**
  submodes are kept, now as transversal: they apply to any of the four cost
  variants (e.g. "SIGMA-FE in Dev mode"), instead of being independent
  parallel variants. The commercial name "SIGMA ZERO" is absorbed by
  SIGMA-FE, which already communicates zero cost in its own description.
  "Availability by variant" and "Prerequisites by variant" tables updated
  to the new notation.
  *Note: this renaming is still pending application in ADR-014 and
  adr-README-v1.5.md — to be addressed in the next round of ADR review.*

---

## License

[MIT](LICENSE)

---

> **SIGMA** is not a closed product: it's a living framework.
> If you understand this document, you understand the ecosystem's entry point.
