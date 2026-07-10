---
id: TROUBLESHOOTING
title: Incident and Diagnosis Log — SIGMA
version: 1.1
status: Active
original-date: 2026-07-04
revision-date: 2026-07-06
author: Prof. Marx A. García Delgado
minimum-references: ADR-001, ADR-006, ADR-010
---

# Incident and Diagnosis Log — SIGMA

This document collects the real problems found during SIGMA's development
and rollout, with their complete diagnosis and the exact fix applied.
Every entry originated from a real, evidence-verified incident — never a
guess. If the symptom matches, the cause is almost certainly the same.

**Diagnostic protocol applied to every incident in this document:**

1. Verify the real on-disk content of the suspect file
   (`findstr`/`grep` for a known signature) — never trust that "the
   correct version was already delivered" without checking.
2. Reproduce the exact symptom with the simplest possible command before
   touching any code.
3. One change at a time between each check — avoids mixing variables and
   losing track of what fixed (or broke) what.

---

## Incident 1 — PostgreSQL and Redis reported "down" despite being healthy

**Date:** July 4, 2026
**Severity:** High — blocked the first full pipeline run
**Status:** Resolved

### Symptom

During Milestone 1's first full pipeline run against real infrastructure
(PostgreSQL, Redis, MinIO, Langfuse, Ollama in Docker), the
`0000-system-health-check` skill consistently reported PostgreSQL and
Redis as down, even though both containers showed as `healthy` in Docker
and both responded correctly to manual connection tests.

The PostgreSQL check consistently took between 4.0 and 4.4 seconds before
reporting failure, and the Redis one between 47.5 and 49.5 seconds —
remarkably consistent figures across successive runs, which already
suggested a deterministic cause rather than a genuinely intermittent
network issue.

### Hypotheses ruled out, in the order they were investigated

1. **IPv6 resolution of `localhost` on Windows.** `localhost` was
   replaced with explicit `127.0.0.1` in the three connection URLs.
   Timings didn't change. Ruled out.
2. **Environment variables not loading correctly.** The code was
   instrumented to print the actual values seen by the process. The
   values turned out to be exactly correct. Ruled out.
3. **`psycopg2` parameter combination.** Isolated in a standalone script
   (`test_postgres_sin_ssl.py`): instant connection. Ruled out.
4. **Interference from the Langfuse client's background thread.**
   Completely neutralized (`test_orchestrator_sin_langfuse.py`). No
   change. Ruled out.
5. **Windows Antivirus/Firewall.** Temporarily disabled. No change.
   Ruled out.
6. **Real TCP connectivity failure (Docker Desktop, WSL2 backend).**
   Tested with a raw Python socket (`test_socket_crudo.py`). All four
   relevant ports connected in `0.00s`. Ruled out.
7. **Slow address resolution (`getaddrinfo`).** Tested with `AF_UNSPEC`
   and `AF_INET` (`test_getaddrinfo.py`). Instant. Ruled out.
8. **`libpq` SSL/GSSAPI negotiation.** Tested with explicit
   `sslmode=disable` and `gssencmode=disable`. Even the first test
   without these parameters was already instant — not the cause.
9. **Suboptimal Redis client construction.** Tested with three different
   constructions (`test_redis_minimo.py`). All three, instant. Ruled out.
10. **Contention from `aiosqlite`'s background thread (LangGraph
    checkpointer).** Compiled the graph with no checkpointer at all. No
    change. Ruled out.
11. **LangSmith environment variables triggering external tracing.**
    Verified that no `LANGCHAIN_*`/`LANGSMITH_*` variable was present.
    Ruled out.
12. **First-load cost of `psycopg2`'s C extension.** Tested with a double
    call in the same "warm" process (`test_doble_llamada.py`). Both
    equally slow. Ruled out.

### Root cause

None of the twelve hypotheses explained the symptom because **the
symptom was never a network issue at all**. The `test_error_real.py`
script — which, for the first time, printed the exact exception text
instead of just measuring timings — revealed that the connection was
being attempted against `localhost`, port `5432` (PostgreSQL) and `6379`
(Redis): **each service's default port, not the actually configured real
ports** (`5433` and `6380`).

The cause was that the `skills/_common.py` file installed in the project
didn't match the most recent version delivered during that same
conversation — it lacked support for reading `DATABASE_URL`, and
silently fell back to the default values. The observed wait time matched
exactly how long Windows takes to exhaust retries against a port with
nothing listening.

### Fix

`skills/_common.py` was replaced with the correct version already
delivered earlier, which includes `DATABASE_URL`/`REDIS_URL` support.
Verified immediately: both services connected in under 0.3 seconds, no error.

### Related permanent decision

Although the investigation ruled out IPv6 as the cause of this specific
incident, it was decided to keep `127.0.0.1` permanently in
`DATABASE_URL`, `REDIS_URL`, and `LANGFUSE_HOST`, out of a preference for
explicitness, not out of a technical need derived from this incident.
`127.0.0.1` and `localhost` identify the same machine — the difference is
purely textual, with no effect on real connectivity.

### Diagnostic scripts produced (reusable)

| Script | What it tests |
|---|---|
| `test_socket_crudo.py` | Pure TCP connectivity, no third-party libraries |
| `test_getaddrinfo.py` | Address resolution (`AF_UNSPEC`/`AF_INET`) |
| `test_postgres_sin_ssl.py` | `libpq` SSL/GSSAPI negotiation |
| `test_redis_minimo.py` | Minimal Redis client construction |
| `test_aislamiento_langfuse_postgres.py` | Isolated Langfuse → PostgreSQL sequence |
| `test_orchestrator_sin_langfuse.py` | Real pipeline with Langfuse neutralized |
| `test_orchestrator_sin_checkpointer.py` | Real pipeline without `SqliteSaver` |
| `test_doble_llamada.py` | First-load cost vs. repeated calls |
| `test_error_real.py` | The real exception message — the one that revealed the cause |

Located in `scripts/diagnosticos_2026-07-04/`. Not deleted: kept as a
record of the method applied and as reusable tools for a similar future incident.

### Closure — successful full run (July 5, 2026)

After resolving this incident and a handful of additional bugs found
along the way (conda environment contamination from global packages, an
initially incorrect RoBERTa model download, Windows path escaping inside
YAML, and a MinIO bucket that was never created), Milestone 1's full
pipeline ran start to finish against real Docker infrastructure and the
real Tirendaz dataset:

```
0000-system-health-check   → success
0001-data-ingestion        → success
0002-data-cleanser         → success
0003-data-preprocessor     → success_with_warnings
0008-sentiment-analyzer    → success
0011-viz-reporter          → success
✓✓ Pipeline completed successfully
```

---

## Incident 2 — `json.dumps()` rejects pandas NaN values

**Date:** July 5, 2026
**Severity:** Medium — blocked `0001-data-ingestion` on rows with empty
optional columns
**Status:** Resolved

### Symptom

```
PostgreSQLConnectionError — invalid input syntax for type json
DETAIL: Token "NaN" is invalid.
```

### Cause

Pandas converts empty cells (e.g. `selected_text` with no value) into
`NaN` (NumPy's special float). `json.dumps()` serializes `NaN` as the
literal token `NaN`, which **is not valid JSON** per RFC 8259 —
PostgreSQL rejects it. `json.dumps()`'s `default=str` parameter doesn't
help here because it only kicks in for non-serializable types, and `NaN`
technically is serializable (it just produces invalid JSON).

### Fix

Sanitize each value with `pd.isna()` before building the dictionary, in
`skills/0001-data-ingestion/skill.py`:

```python
metadata = {
    k: (None if pd.isna(v) else v)
    for k, v in row.items()
    if k not in ("row_id", "text")
}
```

Python's `None` does serialize correctly as `null`, which is valid for
PostgreSQL.

---

## Incident 3 — Langfuse reports `unhealthy` despite working fine

**Date:** July 6, 2026
**Severity:** Low (cosmetic) — doesn't affect real functionality
**Status:** Resolved

### Symptom

`docker ps` shows `sigma_langfuse` as `(unhealthy)` indefinitely, but
`http://localhost:3001` loads and works normally, and pipeline traces do
arrive (confirmed with `test_langfuse_connection.py`, sending and
verifying a real trace via the API).

### Why it isn't serious

The `healthy`/`unhealthy` status is a label Docker only uses for
orchestration decisions (e.g. whether another container with
`depends_on: condition: service_healthy` should wait). It has no effect
whatsoever on whether the application correctly receives and stores data.

### Real causes found (three, accumulated across the same investigation)

1. **`curl` doesn't exist in the image.** The `ghcr.io/langfuse/langfuse:2`
   image doesn't include the `curl` binary — the original healthcheck
   failed with `executable file not found in $PATH`. Partial fix: use
   `wget` instead (it is present, BusyBox 1.36.1).

2. **`wget` resolved `localhost` to IPv6 (`::1`).** Inside the container,
   the connection over that path was refused. Forcing `127.0.0.1`
   explicitly was tried — it improved the diagnosis but didn't fix the
   underlying problem (see cause 3).

3. **Real root cause: the server doesn't listen on any loopback
   interface** (neither `127.0.0.1` nor `::1`) inside the container —
   only on the network IP Docker dynamically assigns it. Confirmed with:
   ```
   docker exec sigma_langfuse hostname -i
   docker exec sigma_langfuse wget --spider http://<that_ip>:3000/api/public/health
   ```
   That IP responded `remote file exists`, while `127.0.0.1` gave
   `Connection refused`.

### Final fix

Resolve the container's IP dynamically inside the healthcheck itself,
never hardcode it:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://$(hostname -i):3000/api/public/health || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 30s
```

### Design note — alignment with ADR-006

Hardcoding the observed IP (`172.18.0.2`) directly into the healthcheck
was deliberately ruled out. Docker can reassign that address on any
future container recreation, and a fixed value would have silently
broken again down the line — the same cross-environment portability
problem ADR-006 prevents through dynamic resolution instead of fixed
values. `$(hostname -i)` resolves the correct IP on every startup, no
matter what it is.

---

## Incident 4 — Zulip: writing in the topic doesn't trigger the webhook

**Date:** July 6, 2026
**Severity:** High — completely blocked HITL approval via Zulip
**Status:** Resolved

### Symptom

Replying "yes"/"no" in the `hitl-approvals` topic never triggers the
Outgoing webhook, with no visible error anywhere.

### Cause

Per Zulip's official documentation, an Outgoing webhook **only fires on
an `@-mention` of the bot or a direct message (DM)** — never on a plain
message in a stream/topic, even if the bot is subscribed to it.

### Adopted fix

HITL responses are sent via DM to the bot, not in the channel. See
`webhook_receiver.py`, the `message.get("type") == "private"` check.

---

## Incident 5 — Zulip's `sender_email` doesn't match the real email

**Date:** July 6, 2026
**Severity:** Medium
**Status:** Resolved

### Symptom

The webhook rejects DMs with `sender_not_authorized`, even though the
sender is the legitimate operator.

### Cause

Zulip can mask the sender's email in the payload (`userNNNNN@domain`
format) depending on its privacy setting
(`email_address_visibility`), unrelated to the real email configured in
`ZULIP_EMAIL`.

### Temporary solution — resume manually without Zulip

While the bot account is deactivated, use
`scripts/resume_hitl_manual.py` to approve or reject an HITL pause
without depending on the webhook. Edit `TRACE_ID` and `DECISION` inside
the script before running it:

```cmd
python scripts/resume_hitl_manual.py
```

### Fix

Validate by `sender_id` (stable, always visible in the payload) instead
of `sender_email`. New variable in `.env`: `ZULIP_OWNER_USER_ID`.

---

## Normal behaviors that look like bugs (but aren't)

### "Do I need Zulip/the webhook running before launching the pipeline?"

**No.** The pipeline can pause at an HITL point, and the process that
resumes it (`webhook_receiver.py`) can start well after that. The state
lives in `sigma_checkpoints.sqlite` on disk, not in shared memory — if
the pipeline reaches a pause before `uvicorn`/`ngrok` are ready, it
simply waits there indefinitely.

### "The ngrok URL changes every time I restart it"

This is expected behavior on ngrok's free plan — it assigns a new URL on
every tunnel restart. The bot's "Endpoint URL" in Zulip has to be updated
manually each time. Permanent fix: migrate to a VPS with a fixed
IP/domain (planned starting at Milestone 2).

### "Kaggle gave me a token with a strange format (`KGAT_...`)"

It's not the classic `kaggle.json` — it's a new personal access token.
Set it as an environment variable:
```cmd
set KAGGLE_API_TOKEN=KGAT_your_full_token
```
or in `%USERPROFILE%\.kaggle\access_token`.

### "A Markdown table I pasted looks broken, each cell on its own line"

This isn't a rendering problem or a Markdown issue per se. It happens
when the text is copied from an environment that reformats a table's
cells onto separate lines during copy (losing the single-row-per-line
format separated by `|`). Fix: paste the original source Markdown again,
one line per row — it will then render correctly on GitHub or any
standard Markdown viewer.
