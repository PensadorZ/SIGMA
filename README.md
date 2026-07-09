# SIGMA — Integrated System for Multi-Agent Management

> **SIGMA is not an answer. It's the system that learns to answer.**

🇪🇸 [Versión en español disponible aquí](README.es.md)

---

SIGMA is an open-source autonomous agent ecosystem for analyzing,
designing, calculating, and deciding, built through an AI-assisted
development methodology (*vibecoding*) and documented from its
architecture down to real production incident resolution.

Multiple specialized agents collaborate under a triangular central
orchestration architecture — Director/Auditor/Engineer, three
orchestrators (see ADR-016) — to tackle projects in Data Engineering,
Data Science, Data Analysis, General Engineering, Physics, Mathematics,
and Axiometrics.

## Why SIGMA is different

Most agent projects build flashy functionality first and add governance
later, if at all. SIGMA was built backwards, deliberately: epistemic
memory, automated security, secrets management, and hallucination
containment (`K ⊆ X`) existed **before** there was a single dashboard to
show. Every architectural decision is backed by an explicit Architecture
Decision Record (ADR) — 16 to date — not tacit convention.

## Cost tiers

SIGMA adapts to four budget levels on the same architectural stack:

| Variant | Cost | For whom |
|---|---|---|
| **SIGMA-FE** (Full Engineer) | $0 | Own engineering, 100% self-hosted stack |
| **SIGMA-LE** (Low-Cost Engineer) | Low | Essential pre-built services |
| **SIGMA-ME** (Medium-Cost Engineer) | ~50% paid | Teams with moderate budget |
| **SIGMA-HE** (High-Cost Engineer) | High | Enterprises requiring high performance |

Each variant can additionally operate in **Dev** (debugging) or
**Runtime** (production with real data) submode. Full detail in
[SIGMA_v1.7.md](docs/SIGMA_v1.7.md).

## Prerequisites

- Docker and Docker Compose
- Python 3.12+
- [Ngrok](https://ngrok.com/download) — exposes the local HITL webhook to
  Zulip during development (not a Python package, installed and run
  separately)
- Kaggle account with an API token (KGAT format) — to download the
  training dataset

## Getting started

```bash
git clone https://github.com/PensadorZ/SIGMA.git
cd SIGMA
cp .env.example .env
# Edit .env with your real values
docker compose up -d
python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv
```

Full step-by-step guide in [ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md)
(project structure document — currently Spanish-only).

## Documentation

| Document | What you'll find there |
|---|---|
| [SIGMA_v1.7.md](docs/SIGMA_v1.7.md) | Full Master Plan — architecture, variants, roadmap |
| [AGENTS_CREATOR.md](docs/AGENTS_CREATOR.md) | Founding charter — the contract every agent follows |
| [docs/adr/](docs/adr/) | 16 Architecture Decision Records |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Real incidents found and their exact resolution |

## Project status

Milestone 1 (Hito 1) complete: a 6-skill pipeline running end to end
against real data, with 65/65 automated tests passing. Milestone 2 in
design: three-level hierarchical orchestration (Director/Engineer).

## License

[MIT](LICENSE)
