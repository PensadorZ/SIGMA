---
id: ADR-010
title: Secrets Remediation Directive — 12-Factor Configuration
version: 1.5
status: Accepted
original-date: 2026-06
revision-date: 2026-07
supersedes: ADR-010 v1.4
minimum-references: ADR-004, ADR-005, ADR-006
approved-by: Prof. Marx A. García Delgado
---

# ADR-010: Secrets Remediation Directive — 12-Factor Configuration

## Executive summary of v1.5 changes

Corrected the `INSTALL.md` reference in the secret-rotation protocol —
that file doesn't exist yet (confirmed against the `README.md` already
updated in Milestone 2); it now points to where to check the real
restart order in the meantime (`ESTRUCTURA_PROYECTO.md`).

## Executive summary of v1.4 changes

The Context section is expanded to first explain that this ADR is the
foundation ADR-004, ADR-005, and ADR-006 depend on for their own
secrets management — before getting into the detail of the Zero
Injection Principle.

## Executive summary of v1.3 changes

Fig. 1 is added with the flow of the protocol's four steps. Tab. 1 is
added with the secret types and their management mechanism. Version
history is incorporated.

---

## Context

The Secrets Remediation Directive is the foundation several other SIGMA
governance mechanisms rest on: the Human-in-the-Loop TOTP seed
(ADR-004), the Policy Server's configuration (ADR-005), and the
ContextResolver's guarantee of never logging a resolved value in
Langfuse (ADR-006) — all of them assume there is a single, disciplined
way of handling credentials, and this ADR is that way. Without this
directive, each of those mechanisms would have to solve the secrets-
management problem on its own, inconsistently.

Hardcoded credentials are the most frequent and most avoidable attack
vector. In SIGMA the risk is especially high because the repository can
be public, LLMs can include credentials in their outputs, and logged
prompts can expose credentials if they are embedded.

---

## Decision

**Zero Injection Principle:** it is strictly forbidden to write literal
credential strings into any file in the repository.

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
IS versioned. Documents the required variables.
Example:
  GEMINI_API_KEY=your_google_ai_studio_api_key
  DB_PASSWORD=your_password_here
  TOTP_SEED_PATH=/path/to/the/.sigma_totp.enc file

STEP 4: get_required_env() function throughout all code
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

### Tab. 1 — Secret types and their management mechanism

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

Secret rotation is only performed between runs. A verification script
checks Redis's state to confirm there are no active pipelines before
proceeding. Services are restarted in the order specified in
`INSTALL.md`. **Real note (Milestone 2):** `INSTALL.md` still doesn't
exist as a file — `README.md` already documents this as a known
limitation. Until it exists, the restart order lives in
`ESTRUCTURA_PROYECTO.md`, which is real and up to date; this ADR does
not create `INSTALL.md` on its own, it only points to where to check
the real order until it is written.

---

## Positive consequences

- The repository can be public with no risk of exposing credentials.
- `fail-fast` makes the error explicit at the start of the pipeline,
  not midway through.
- `.env.example` automatically documents all required variables.

## Negative consequences

- Requires team discipline: the only way to introduce a hardcoded
  credential is to deliberately ignore the protocol.
- If `.env` is misconfigured, the system doesn't start (intended
  behavior, but can be frustrating during initial setup).

## Alternatives considered

| Alternative | Why it was rejected |
|---|---|
| Hardcoded credentials with a "change in prod" comment | Risk of being forgotten; stays in Git history |
| Per-environment versioned configuration file | Prod credentials end up in the repository |
| Only system environment variables, no `.env` | Hard to manage in local development |

---

## Version history

**Changes in v1.2:**
- **a.1.2** Added the encrypted TOTP seed as a secret type managed by
  this ADR, with generation and storage instructions.
- **b.1.2** Added the zero-downtime secret-rotation protocol for runs
  in progress.

**Changes in v1.3:**
- **a** Added Fig. 1 with the visual flow of the protocol's four steps.
- **b** Added Tab. 1 with the secret types, their management mechanism,
  and their exposure restrictions.

**Changes in v1.5 (Milestone 2, Rollout 1 close):**
- **a** Corrected the `INSTALL.md` reference (doesn't exist yet) in the
  secret-rotation protocol — pointed to `ESTRUCTURA_PROYECTO.md` as the
  real source in the meantime, without creating the file on its own.
