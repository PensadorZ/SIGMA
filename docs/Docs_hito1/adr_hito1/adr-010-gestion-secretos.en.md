---
id: ADR-010
title: Secrets Remediation Directive — 12-Factor Configuration
version: 1.4
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-010 v1.3
minimum-references: ADR-004, ADR-005, ADR-006
approved-by: Prof. Marx A. García Delgado
---

# ADR-010: Secrets Remediation Directive — 12-Factor Configuration

## Executive summary of changes in v1.4

The Context section is expanded to first explain that this ADR is the
foundation ADR-004, ADR-005, and ADR-006 depend on for their own secrets
handling — before descending into the detail of the Zero-Injection Principle.

## Executive summary of changes in v1.3

Added Fig. 1 with the flow of the protocol's four steps. Added Table 1
with the secret types and their management mechanism. Incorporated the
version history.

---

## Context

The Secrets Remediation Directive is the foundation several other SIGMA
governance mechanisms rest on: the Human-in-the-Loop's TOTP seed
(ADR-004), the Policy Server's configuration (ADR-005), and the
ContextResolver's guarantee of never logging a resolved value in
Langfuse (ADR-006) — all of them assume a disciplined, single way of
handling credentials exists, and this ADR is that way. Without this
directive, each of those mechanisms would have to solve the secrets
management problem on its own, inconsistently.

Hardcoded credentials represent the most frequent and most avoidable
attack vector. In SIGMA the risk is especially high because the
repository can be public, LLMs can include credentials in their
outputs, and logged prompts can expose credentials if they're embedded
in them.

---

## Decision

**Zero-Injection Principle:** writing literal credential strings into
any file in the repository is strictly prohibited.

### Fig. 1 — The four steps of the secrets protocol

```
STEP 1: Create a local .env file
─────────────────────────────────
The operator creates .env with real values.
This file NEVER enters the repository.

STEP 2: Protect the repository
─────────────────────────────────
.gitignore includes:
  .env
  .env.local
  .env.*.local
  *.totp_seed  ← encrypted TOTP seed

STEP 3: Public .env.example template
─────────────────────────────────
Same keys as .env but with empty or descriptive values.
This one IS versioned. Documents the required variables.
Example:
  GEMINI_API_KEY=your_google_ai_studio_api_key
  DB_PASSWORD=your_password_here
  TOTP_SEED_PATH=/path/to/.sigma_totp.enc

STEP 4: get_required_env() function throughout the code
─────────────────────────────────
def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Variable '{key}' not defined. "
            f"See .env.example for the full list."
        )
    return value
```

### Table 1 — Secret types and their management mechanism

| Secret type | Mechanism | In logs/Langfuse? |
|---|---|---|
| API keys (`GEMINI_API_KEY`) | `get_required_env()` in Python code | **Never** |
| DB passwords (`DB_PASSWORD`) | `get_required_env()` in Python code | **Never** |
| Langfuse tokens | `get_required_env()` in Python code | **Never** |
| Approval Endpoint token | `get_required_env()` in Python code | **Never** |
| Encrypted TOTP seed | Local file encrypted with Fernet; path as a placeholder in `.env.example` | **Never** the value; the path, yes |
| MinIO token | `get_required_env()` in Python code | **Never** |

### Encrypted TOTP seed

The TOTP seed for the Approval Endpoint's MFA is generated once with a
setup script, encrypted with the operator's password via Fernet, and
stored in a local file covered by `.gitignore`. The Approval Endpoint
decrypts the seed in memory to validate the TOTP code. No dependency on
external servers.

### Zero-downtime rotation protocol

Secret rotation only happens between runs. A verification script checks
Redis's state to confirm no pipelines are active before proceeding.
Services restart in the order specified in INSTALL.md.

---

## Positive consequences

- The repository can be public with no risk of exposing credentials.
- `fail-fast` makes the error explicit at pipeline startup, not midway
  through.
- `.env.example` automatically documents every required variable.

## Negative consequences

- Requires team discipline: the only way to introduce a hardcoded
  credential is to deliberately ignore the protocol.
- If `.env` is misconfigured, the system won't start (desired behavior,
  but can be frustrating during initial setup).

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Hardcoded credentials with a "change in prod" comment | Risk of forgetting; stays in Git history |
| Per-environment versioned config file | Prod credentials end up in the repository |
| System environment variables only, no `.env` | Hard to manage in local development |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added the encrypted TOTP seed as a secret type managed by
  this ADR, with generation and storage instructions.
- **b.1.2** Added the zero-downtime secret rotation protocol for
  in-progress runs.

**Changes in v1.3:**
- **a.1.3** Added Fig. 1 with the visual flow of the protocol's four steps.
- **b.1.3** Added Table 1 with the secret types, their management
  mechanism, and their exposure restrictions.

**Changes in v1.4:**
- **a** Expanded Context to explain that this ADR is the foundation
  ADR-004, ADR-005, and ADR-006 depend on for their own secrets
  handling, before descending into the detail of the Zero-Injection Principle.
