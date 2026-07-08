---
id: ADR-006
title: Context Hygiene with Placeholders and ContextResolver
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-006 v1.3
minimum-references: ADR-005, ADR-010, ADR-011
approved-by: Prof. Marx A. García Delgado
---

# ADR-006: Context Hygiene with Placeholders and ContextResolver

## Executive summary of changes in v1.4

The Context section is expanded to first explain what the
ContextResolver is and why it exists — as the mechanism that makes a
single `skill.py` portable across all four variants with no secret
leakage, connecting directly to ADR-010 — before descending into the
detail of the three concrete problems it solves.

## Executive summary of changes in v1.3

Added Fig. 1 with the ContextResolver's resolution hierarchy. Added
Table 1 with the explicit separation between configuration types and
secret types. Incorporated the version history.

---

## Context

The ContextResolver is the mechanism that lets a single `skill.py`,
written once, run unmodified across SIGMA Dev, Lite, Full, or Runtime —
substituting any environment-dependent value at execution time, without
that value ever living written directly in the code or in the skill's
specification. Without this mechanism, every skill would have to
hardcode environment-specific paths, table names, and credentials,
which — beyond coupling the code to a specific environment — would open
exactly the secret-leakage door ADR-010 exists to close.

Skills contain prompts, paths, and parameters that vary across
environments and across runs. Writing these values directly into the
code produces three concrete problems: hardcoded secrets, environment
coupling (the skill stops being portable), and silent failures when a
variable isn't defined — the worst of the three, because the system
doesn't fail immediately with a clear message, it just behaves
incorrectly without warning.

---

## Decision

Use `${VARIABLE}` syntax for every environment- or execution-dependent
value. A centralized `context_resolver.py` middleware replaces these
placeholders at runtime before the prompt reaches the LLM.

### Fig. 1 — ContextResolver's resolution hierarchy

```
Skill with a ${OUTPUT_TABLE} placeholder
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
  3. defaults.yaml  ← The skill's non-sensitive default values
        │ Found?
        ├─ YES → Sanitization → Passes? → Substitute → Log source in Langfuse
        └─ NO ↓
  NO SOURCE FOUND → ContextResolutionError (fail-fast with a descriptive message)

Sanitization checks:
  ✓ No path traversal (../ or absolute paths outside the project)
  ✓ No credential patterns per ADR-010
  ✓ Type compatible with the one declared in defaults.yaml
```

### Table 1 — Separation between configuration and secrets

| Value type | Mechanism | Can it appear in Langfuse? |
|---|---|---|
| File paths | `${VAR}` placeholder in SKILL.md | Yes (only the name, never the content) |
| Table names | `${VAR}` placeholder in SKILL.md | Yes |
| Endpoint URLs | `${VAR}` placeholder in SKILL.md | Yes |
| API keys | `get_required_env()` in Python code | **Never** |
| DB passwords | `get_required_env()` in Python code | **Never** |
| Access tokens | `get_required_env()` in Python code | **Never** |
| TOTP seed | Path to the encrypted file as the placeholder; the value itself is never a placeholder | **Never** |

### Logging in Langfuse

The ContextResolver logs the **name** of the resolved placeholder and
the resolution **source** (`override_state`, `os.environ`, or
`defaults.yaml`). It never logs the resolved value, so as not to expose
sensitive configuration. The log entry carries the active `trace_id`
per ADR-011.

### CI validation

The CI GitHub Action verifies that no `SKILL.md` file or prompt contains
unresolved placeholders or credential patterns before merging.

---

## Positive consequences

- A skill written in Dev works in production with no modifications.
- `fail-fast` eliminates silent failures from undefined variables.
- Sanitization prevents path-traversal attacks and accidental credential
  exposure through the resolution system.

## Negative consequences

- Developers must remember to use the placeholder syntax.
- CI validation acts as a safety net, not a substitute for development discipline.

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
- **b.1.2** Added Langfuse logging of the name and source of each
  resolved placeholder without exposing the value.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the full resolution hierarchy, including
  `fail-fast`.
- **b.1.3** Added Table 1 with the explicit separation between
  configuration types and secret types.

**Changes in v1.4:**
- **a** Expanded Context to explain what the ContextResolver is and why
  it exists, before descending into the detail of the three concrete
  problems it solves.
