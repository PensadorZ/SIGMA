---
id: ADR-006
title: Context Hygiene with Placeholders and ContextResolver
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-006 v1.4
minimum-references: ADR-005, ADR-010, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-006: Context Hygiene with Placeholders and ContextResolver

## Executive summary of v1.5 changes

Corrected the mention of the 4 cost variants in the Context section,
which used the old scheme ("SIGMA Dev, Lite, Full or Runtime" as if
they were flat categories) — it now reflects the two real, independent
axes: cost variant (SIGMA-FE/LE/ME/HE) and submode (Dev/Runtime).

## Executive summary of v1.4 changes

The Context section is expanded to first explain what the
ContextResolver is and why it exists — as the mechanism that makes a
single `skill.py` portable across the four variants without secret
leakage, connecting directly to ADR-010 — before getting into the
detail of the three concrete problems it solves.

## Executive summary of v1.3 changes

Fig. 1 is added with the ContextResolver's resolution hierarchy. Tab. 1
is added with the explicit separation between configuration types and
secret types. Version history is incorporated.

---

## Context

The ContextResolver is the mechanism that allows a single `skill.py`,
written once, to run unmodified on any cost variant (SIGMA-FE, LE, ME,
HE) and in any submode (Dev, Runtime) — substituting, at runtime, any
value that depends on the environment, without that value ever living
written directly in the code or in the skill specification. Without
this mechanism, every skill would have to hardcode paths, table names,
and credentials specific to each environment, which, besides coupling
the code to a specific environment, would open exactly the secret-leak
door ADR-010 exists to close.

Skills contain prompts, paths, and parameters that vary across
environments and across runs. If these values are written directly
into the code, three concrete problems occur: hardcoded secrets,
environment coupling (the skill stops being portable), and silent
failures when a variable isn't defined — the worst of the three,
because the system doesn't fail immediately with a clear message, it
instead behaves incorrectly without warning.

---

## Decision

Use `${VARIABLE}` syntax for every environment- or execution-dependent
value. A centralized `context_resolver.py` middleware replaces these
placeholders at runtime before the prompt reaches the LLM.

### Fig. 1 — ContextResolver's resolution hierarchy

```
Skill with placeholder ${OUTPUT_TABLE}
        │
        ▼
ContextResolver looks in:
  1. override_state  ← Highest priority (injected by the Orchestrator at runtime)
        │ Found?
        ├─ YES → Sanitization → Passes? → Substitute → Log source in Langfuse
        └─ NO ↓
  2. os.environ  ← Variables from the .env file loaded at startup
        │ Found?
        ├─ YES → Sanitization → Passes? → Substitute → Log source in Langfuse
        └─ NO ↓
  3. defaults.yaml  ← Non-sensitive default values for the skill
        │ Found?
        ├─ YES → Sanitization → Passes? → Substitute → Log source in Langfuse
        └─ NO ↓
  NO SOURCE → ContextResolutionError (fail-fast with a descriptive message)

Sanitization verifies:
  ✓ No path traversal (../ or absolute paths outside the project)
  ✓ No credential patterns per ADR-010
  ✓ Type compatible with what defaults.yaml declares
```

### Tab. 1 — Separation between configuration and secrets

| Value type | Mechanism | Can it appear in Langfuse? |
|---|---|---|
| File paths | `${VAR}` placeholder in SKILL.md | Yes (only the name, never the content) |
| Table names | `${VAR}` placeholder in SKILL.md | Yes |
| Endpoint URLs | `${VAR}` placeholder in SKILL.md | Yes |
| API keys | `get_required_env()` in Python code | **Never** |
| DB passwords | `get_required_env()` in Python code | **Never** |
| Access tokens | `get_required_env()` in Python code | **Never** |
| TOTP seed | Path to the encrypted file as the placeholder; the value is never a placeholder | **Never** |

### Logging in Langfuse

The ContextResolver logs the **name** of the resolved placeholder and
the **source** of resolution (`override_state`, `os.environ`, or
`defaults.yaml`). It never logs the resolved value, to avoid exposing
sensitive configuration. The log entry carries the active `trace_id`
per ADR-011.

### CI validation

The CI GitHub Action verifies that no `SKILL.md` file or prompt
contains unresolved placeholders or credential patterns before merging.

---

## Positive consequences

- A skill written in Dev works in production with no modifications.
- `fail-fast` eliminates silent failures from undefined variables.
- Sanitization prevents path-traversal attacks and accidental
  credential exposure through the resolution system.

## Negative consequences

- Developers must remember to use the placeholder syntax.
- CI validation acts as a safety net but not as a substitute for
  development discipline.

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Hardcoded values per environment | The same skill can't be used across multiple environments |
| Direct, unresolved environment variables | The LLM receives the placeholder literally |
| Jinja2 as the templating engine | Python's `string.Template` is sufficient |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added sanitization of resolved values with three checks:
  path traversal, credential patterns, and type compatibility.
- **b.1.2** Added logging in Langfuse of each resolved placeholder's
  name and source without exposing the value.

**Changes in v1.3:**
- **a** Added Fig. 1 with the full resolution hierarchy including
  `fail-fast`.
- **b** Added Tab. 1 with the explicit separation between configuration
  types and secret types.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** Corrected the mention of variants in the Context section to the
  real scheme (SIGMA-FE/LE/ME/HE + Dev/Runtime submode, two independent
  axes), replacing the legacy flat scheme.
