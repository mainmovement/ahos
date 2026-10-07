# M10 Stage 4 — the one-line flip + rollback runbook (owner-gated)

**Status:** PREPARED, NOT EXECUTED. Per the owner's 2026-10-07 decision, M10
completes Stage 4 as *prepare + document, do NOT flip*: the switch mechanism is
built, tested against a scratch store, and this runbook records the single act
the owner performs. Nothing on this page has been applied to `.env`.

**Nothing here touches a secret.** The existing `.env` values are never printed
or committed. The flip changes one value the owner already holds.

---

## What is already done (so the flip is not a leap)

| Item | Where | Evidence |
|---|---|---|
| Two-backend DB client | `db/index.ts` | `DATABASE_URL` scheme selects the backend; `pglite:<dataDir>` → `drizzle-orm/pglite`, anything else → node-postgres `Pool`. The WASM module loads only on the pglite path |
| Canonical URL parsing (single source of truth) | `db/pglite_url.mjs` | Imported by both the gateway and the readiness probe, so a green probe can never describe a store the gateway does not open |
| Readiness probe, both backends | `scripts/ahos_pg_probe.mjs` | Same report schema and exit contract (0 = `ahos_system_state` readable, 2 = blocked) on both branches |
| Schema-only restore into a scratch store | `npm run db:restore-pglite -- --dataDir <dir>` | 33 migration statements, `ready: ahos_system_state present` |
| Full parity restore against real data | same tool with `--dump` + `--counts` | **19/19 tables OK, 778 rows, 0 parity failures** from the Stage 2 dump; jsonb + timestamptz round-trip verified |
| Gateway runtime smoke | `reports/grok/M10_STAGE4_SMOKE_RECEIPT.md` | Booted against the PGlite parity store — authorized `GET /api/command` 200 with a real store-backed snapshot (`lastCycleStatus: SUCCESS`, 30 opportunities, 352 council votes) — and against a dead Postgres URL (200 fail-closed, no crash) |
| The bug the smoke caught | `db/index.ts` + `scripts/pglite_backend_selftest.ts` | The first smoke run exposed a live `ReferenceError: pgliteDataDir is not defined` on the gateway's PGlite path: a re-export without a local value binding, invisible to `tsc`. Fixed with a value import, plus a regression test that opens a throwaway dataDir through `db.$client` and asserts `PG_VERSION`. Selftest 17/17 |
| Launcher schema init on first start | M10.1 (`scripts/pglite_restore.ts --check`, `launcher/components.py`) | The launcher initialises the store on first start when `PG_VERSION` is absent |

## Before you flip (two minutes, do it once)

1. **Copy the current `DATABASE_URL` line out of `.env` into a password-safe
   note.** That value is your rollback. It is not recorded anywhere in the repo
   and never will be.
2. Confirm the Docker Postgres container is stopped or you are happy to stop
   it (`docker compose -f deployment/docker-compose.windows.yml down`). The flip
   does not require this, but it makes the rollback story unambiguous.
3. Confirm `G:/robat/ahos_runtime/pglite/ahos` is the directory you want as the
   permanent store. It lives outside the repo and is never committed. A
   different drive/path is fine — put that path in the flip line below.

## The flip (one line + one restart)

In `.env`, set:

```
DATABASE_URL=pglite:G:/robat/ahos_runtime/pglite/ahos
```

Then restart the gateway (`scripts/windows_restart_next_dev.ps1`, or restart the
launcher). On first start the launcher initialises the schema if the store is
empty (M10.1) — no `db:migrate`, no `db:push`, ever.

Verify:

```powershell
# Probe the live backend (exit 0 = ahos_system_state readable)
node scripts\ahos_pg_probe.mjs --json-out reports\pg_probe_latest.json

# Or the structural readiness gate the launcher uses
npm run db:restore-pglite -- --check --dataDir G:/robat/ahos_runtime/pglite/ahos
```

Then open the dashboard and confirm `/api/command` shows the command snapshot.

### Optionally seed the store from the verified backup

An empty-but-initialised store is a legitimate starting point (the Python lane
never used Postgres). If you want the historical rows the Docker store held:

```powershell
npm run db:restore-pglite -- `
  --dataDir G:/robat/ahos_runtime/pglite/ahos `
  --dump   G:/robat/ahos_backups/pg_20261003T091351Z/ahos_full.sql `
  --counts G:/robat/ahos_backups/pg_20261003T091351Z/row_counts.txt
```

That is the exact command that produced the 19/19 + 778/778 parity receipt. It
is idempotent against the schema but re-inserts rows, so prefer running it once,
against a fresh store.

## Rollback (restore the line you saved)

1. Put the saved `postgresql://...` line back into `.env`.
2. Restart the gateway.
3. Start the Docker Postgres container if you stopped it.

Rollback is a **config flip, not a restore from backup**. The Docker files stay
in the repository (Stage 5 archives them; nothing is deleted), and the PGlite
store is left in place — it is just not read until you flip back. No data is
destroyed in either direction.

If the Postgres volume's password has drifted from `.env`, `scripts/windows_ensure_database_url.ps1`
still handles the realign path it always has.

## After you confirm green: the second half of the archive

These five files are the **live rollback path** while `.env` still points at
Postgres, so they deliberately stay in place through the flip. Once you are
green and want the retirement closed out, they move into the Stage 5 archive
(`docs/archive/quarantine_2026-10/docker_n8n/`) as a second half — tell the
agent, or move them with the re-anchors already listed in the M10 plan:

- `deployment/docker-compose.windows.yml`
- `deployment/Dockerfile`
- `deployment/entrypoint.sh`
- `deployment/healthcheck.py`
- `database/postgresql_schema.sql`

`scripts/windows_diagnose_docker_health.ps1` and `scripts/windows_validate_g2.ps1`
go with them at the same time (the G2 pipeline invokes the diagnose script, and
`tests/test_web_api_auth_gate.py` asserts both scripts' contents in place, so
they must move together).

One cosmetic gap: `config/.env.template:14-20` was meant to get a comment naming
the native backend (keys unchanged either way). That directory is not writable
from the agent session that did Stage 5, so it is outstanding — harmless, since
a template comment is not a runtime path, but worth finishing when `config/`
is next edited.

## What can never be flipped away

- The GM-06 quarantine on `ahos_03_telegram_control.json` — name-enforced by
  `tests/validate_n8n.py`, unaffected by any backend choice.
- The honest-degradation contract, as it is actually implemented (verified
  end-to-end in the Stage 4c smoke receipt, not assumed):
  - `GET /api/command` returns **200 with a fail-closed snapshot** on any store
    failure — `running: false`, `lastCycleStatus: CODE_FAILURE`, the redacted
    last error, and every list emptied. Observed against a dead Postgres URL.
  - `POST /api/chat` returns **200 with a normal reply**; a failed persistence
    is swallowed by `chat.ts` and never surfaces to the caller.
  - The route's retry-then-500-with-hint branch is a **provider-failure** path,
    not a store-failure path, and is not reachable from a store error. M10
    changes neither branch and does not rely on it.
- The policy deny-lists (`ahos_org/policy.py`, `research_worker/protocol.py`) —
  safety boundaries, not Docker coupling.
- `.env` secrets. `POSTGRES_PASSWORD` and `N8N_BASIC_AUTH_PASSWORD` stay put;
  unused keys are not deleted.
