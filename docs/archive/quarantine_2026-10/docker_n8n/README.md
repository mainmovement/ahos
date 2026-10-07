# Archive: Docker + n8n (Mission 10 retirement, 2026-10)

**Nothing here is deleted.** Every file moved verbatim with `git mv`, so
`git log --follow <path>` reaches its full history. To restore any of it, move
the file back to its original path (listed below) and revert the re-anchors that
point at this directory: `config/paths.py::get_n8n_workflows_dir()`,
`engine/doc_hygiene.py:177`, `tests/validate_n8n.py`, `tests/test_ahos.py`,
`tests/test_n8n_governance_rules.py`, `tests/test_validate_n8n_utf8.py`, and
`tests/test_deployment_config.py::COMPOSE`. That is the whole undo procedure.

## Why this is dead

Mission 10 (`reports/grok/DECKER_N8N_MIGRATION.md`) retired Docker and n8n:

- **The Python lane never used either.** No Python Postgres driver exists in the
  repo; all Lane B state runs on SQLite in `data/`. n8n had **zero imported
  workflows at runtime** — the automation surface was already empty.
- **The Docker surface was exactly one thing**: Postgres for the TypeScript
  gateway. That role is now served by the embedded PGlite backend selected by
  the `DATABASE_URL` scheme (`db/index.ts`, `pglite:<dataDir>`).
- **The six n8n cadences are recorded, not lost.** The authoritative ownership
  map is `architecture/scheduling/n8n_migration.py` — 1 already-running, 1
  superseded at higher frequency, 3 mapped with execution wiring deferred to
  M44, 1 quarantined. Verified by `tests/test_n8n_migration_registry.py`.

The live `.env` `DATABASE_URL` flip is **owner-gated** and was deliberately not
performed. See `reports/grok/M10_STAGE4_FLIP_RUNBOOK.md`.

## What is here

| File (archive path) | Original path | Last commit touching it | What it was |
|---|---|---|---|
| `docker-compose.yml` | `docker-compose.yml` (repo root) | `f9a21e9` (2026-08-17) | Root dev compose: Postgres + n8n + the gateway. Had no live consumer in the repo; the Windows operator path used `deployment/docker-compose.windows.yml` instead |
| `deployment/docker-compose.yml` | `deployment/docker-compose.yml` | `86ebbc0` (2026-08-16) | Deployment compose template. Docs-only by 2026-10: no script or test booted it |
| `deployment/docker-compose.production.yml` | `deployment/docker-compose.production.yml` | `86ebbc0` (2026-08-16) | Production/VPS compose target — **design-only, never built** (`docs/canonical/KNOWLEDGE_MAP.md:59`) |
| `deployment/docker-compose.target.yml` | `deployment/docker-compose.target.yml` | `86ebbc0` (2026-08-16) | Service-target declaration. Design-only (`AHOS_ISSUE_REGISTER.md:446`) |
| `n8n/ahos_01_data_ingest_integrity.json` | `n8n/workflows/ahos_01_data_ingest_integrity.json` | `86ebbc0` (2026-08-16) | Hourly ingest + integrity gate. Recorded as `CADENCE_SUPERSEDED_NOT_REIMPLEMENTED` |
| `n8n/ahos_02_signal_pipeline.json` | `n8n/workflows/ahos_02_signal_pipeline.json` | `86ebbc0` (2026-08-16) | Hourly strategy+risk gate mirror. `MIGRATED_ALREADY_RUNNING` in the daemon's 60s loop |
| `n8n/ahos_03_telegram_control.json` | `n8n/workflows/ahos_03_telegram_control.json` | `86ebbc0` (2026-08-16) | **STILL QUARANTINED (GM-06).** Never imported, never to be re-implemented 1:1 — SQL interpolation, audit `DELETE`, an approve path bypassing canonical authority. The quarantine is name-enforced (`tests/validate_n8n.py:QUARANTINED_WORKFLOWS`) and moves with this file |
| `n8n/ahos_10_research_lab.json` | `n8n/workflows/ahos_10_research_lab.json` | `86ebbc0` (2026-08-16) | Weekly research lab. `MAPPED_EXECUTION_DEFERRED_TO_M44` |
| `n8n/ahos_11_data_update.json` | `n8n/workflows/ahos_11_data_update.json` | `86ebbc0` (2026-08-16) | Daily 3-year data acquisition + audit. `MAPPED_EXECUTION_DEFERRED_TO_M44` |
| `n8n/ahos_12_research_report.json` | `n8n/workflows/ahos_12_research_report.json` | `86ebbc0` (2026-08-16) | Weekly research report. `MAPPED_EXECUTION_DEFERRED_TO_M44` |
| `n8n_setup_guide.md` | `docs/n8n_setup_guide.md` | `4cbdd77` (2026-08-27) | n8n integration setup instructions. Superseded by the native backend; retained as the historical record of how the integration was wired |

## What deliberately stayed in the live tree

These are the **live rollback path** while `.env` still points at Postgres, so
they move only after the owner flips and confirms green (second half, per the
flip runbook):

- `deployment/docker-compose.windows.yml` — the compose `.env`'s URL points at
- `deployment/Dockerfile`, `deployment/entrypoint.sh`, `deployment/healthcheck.py`
- `database/postgresql_schema.sql`
- `scripts/windows_diagnose_docker_health.ps1` (invoked by the live G2 pipeline)

## Safety invariants that the move must not disturb

- The GM-06 quarantine is **name-based, not path-based**. It keys on the exact
  filename `ahos_03_telegram_control.json` and is asserted from this archive
  path by `tests/test_n8n_governance_rules.py` and `tests/validate_n8n.py`.
- The structural validator still runs over these JSONs in the CI chain
  (`engine/run_all_checks.sh` stage 6), so drift in an archived workflow is
  still caught.
- The policy deny-lists that blocked n8n-directed egress
  (`ahos_org/policy.py`, `research_worker/protocol.py`) stayed exactly as
  written — they are safety boundaries, not Docker coupling.
- This directory is excluded from `tsconfig.json`, so archived artifacts cannot
  break the type-check. It holds no TypeScript or JavaScript, so eslint has
  nothing to lint here either — verified, not assumed.
