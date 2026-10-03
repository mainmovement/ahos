# MISSION 10 — SAFE DOCKER / n8n REMOVAL — STAGE 1 INVENTORY + DECISION

Date: 2026-10-03 ~13:38 Tehran (10:08 UTC). Author: Claude (Atria), branch `ahos`.
Owner order: 2026-10-02 18:49 Tehran ("REMOVE n8n/Docker safely", binding).
Predecessor doc: `reports/grok/DOCKER_N8N_DEPENDENCY_MAP.md` (Grok, read-only, 2026-10-02).
Reality ladder used throughout. Nothing here is a readiness claim; each row is
evidence-backed. **PAPER_ONLY. No live trading. Lane A untouched.**

---

## 0. HEADLINE: the Docker surface is exactly one thing — Postgres for the TS gateway

Evidence (verified this session, not inherited):

- **Python Lane B never touches Postgres.** No Python Postgres driver exists in
  the repo (`psycopg2` import fails; `requirements.txt` has no pg driver). All
  Lane B evidence/decision/canonical paths run on SQLite in `data/`
  (`e01_discovery.sqlite`, `paper_trading.sqlite`, `ahos_local.sqlite`,
  `ahos_knowledge.sqlite`). **Docker removal cannot affect Lane B.**
- **The TS gateway reaches Postgres through exactly one client module**,
  `db/index.ts` (`getDatabaseUrl()` :11-22, `getPool()` :24-45 — sole
  `pg.Pool`; `getDb()` :47-52 — sole `drizzle()`; lazy Proxy exports `pool`
  :59-65 and `db` :67-73 so importing never throws). Exactly **four live
  modules import `@/db`** (grep-confirmed): `snapshot.ts:1` (main reader, 13
  tables), `engine.ts:1` (main writer), `chat.ts:1` (best-effort persist
  :79-92, history :425-432), `news.ts:1` (one translation-cache read :92).
  Every API route reaches the DB through those four — no route imports `db`
  directly. (The `01/`, `advanced-3d-audiovisual-website*/`,
  `سایت درخت…/` trees are stray duplicates with their own `db/index.ts`;
  they are not live and are out of scope.)
- **Graceful degradation already exists**, so the swap is low-risk:
  `db/index.ts` never throws at import; `snapshot.ts:56-109`
  `failClosedCommandSnapshot` returns CODE_FAILURE with `running=false`;
  `app/api/command/route.ts:20-23` returns **200** on DB failure (honest
  degradation); `app/api/chat/route.ts:19-24` `isTransientPgError()` retries
  and returns **500 with hint** at :91-115.
- **`start_ahos.bat` / `start_ahos.ps1` are already 100% Docker-free**:
  `.venv` → `scripts/init_databases.py --with-guards` (4 SQLite stores) →
  `python -m architecture.runtime --daemon --interval-sec 60
  --observation-cycle --evidence-source local` with `AHOS_PAPER_ONLY=1`.
- **n8n has zero app-code coupling.** No `.py`/`.ts` file makes an HTTP or
  webhook call to n8n (grep-confirmed by Grok and re-confirmed by the Stage-1
  agent). Its footprint is workflow JSONs, structural validators, config
  references, policy deny-lists, and docs. The live n8n DB has **0 imported
  workflows** (`workflow_entity` count = 0, read-only query 2026-10-02
  ~10:25Z), so nothing is running to break.

**Correction to a prior claim:** the M9 outcome note in
`OWNER_DIRECTIVE_MISSION_PLAN.md:105-108` says "Postgres was never live on this
host". That is **wrong for data purposes**. Exact `count(*)` this session shows
**17 non-zero `ahos_*` tables holding 778 real rows** — including
`ahos_expert_votes` 352, `ahos_chat_messages` 74, `ahos_provider_snapshots` 66,
`ahos_translation_cache` 56, `ahos_news_items` 56, `ahos_tokens` 32,
`ahos_opportunities` 32, `ahos_observations` 32, `ahos_council_reports` 32,
`ahos_predictions` 29, `ahos_security_reports` 10, `ahos_findings` 2,
`ahos_watchlist` 1, `ahos_system_state` 1, `ahos_paper_positions` 1,
`ahos_market_snapshots` 1, `ahos_cycles` 1. (`ahos_lessons` 0, `ahos_outcomes`
0.) The likely source of the error was stale `pg_stat_user_tables.n_live_tup`,
which read zero. **This is why Stage 2 backup + row-count parity is mandatory,
not optional.**

---

## 1. THE REQUIRED INVENTORY TABLE

Columns as specified by the mission: item, path, what it does, replacement,
risk, status. Status values are reality-ladder, not prose.

### 1a. Docker — compose and containers

| Item | Path | What it does | Replacement | Risk | Status |
|---|---|---|---|---|---|
| **LIVE compose project** | `deployment/docker-compose.windows.yml` | The running project (`com.docker.compose.project=deployment`): `postgres` (16.15-alpine, `ahos_postgres_win`, 127.0.0.1:5432), `n8n` (`ahos_n8n_win`, 0 workflows), `ahos-runtime` (`ahos_runtime_win`) | Config switch: `DATABASE_URL` → embedded PGlite; runtime container deleted as duplicate (native daemon is the single owner) | HIGH — the only real data store; must back up + prove parity first. Mitigated: backup done (§2), parity proven 19/19 | `VERIFIED` for backup+parity; switchover `NOT_STARTED` |
| Root compose | `docker-compose.yml` | **Not** the running project (`docker compose ps` at root → empty) | Archive (Stage 5) | LOW — not live | `NOT_STARTED` |
| VPS compose | `deployment/docker-compose.yml` | VPS target, not running on this host | Archive | LOW | `NOT_STARTED` |
| Production compose | `deployment/docker-compose.production.yml` | runtime-only target, not running | Archive | LOW | `NOT_STARTED` |
| Design artifact | `deployment/docker-compose.target.yml` | never built (design only) | Archive | NONE | `NOT_STARTED` |
| `ahos-runtime` container | compose service | Runs `python3 -m architecture.runtime` against bind-mounted `../data` SQLite — **duplicate of the native daemon**; today the only running observer | Native daemon (`start_ahos.ps1`) becomes sole runtime owner | MEDIUM — **dual-writer hazard**: container + native daemon both writing `data/*.sqlite` via bind mount. Single-owner is a governance decision; default = native | `NOT_STARTED` (human-visible choice, listed §5) |
| `deployment/Dockerfile` | `python:3.13-slim`, `ENTRYPOINT /app/deployment/entrypoint.sh`, `CMD python3 -m architecture.runtime`, HEALTHCHECK 30s/5s → `deployment/healthcheck.py` | Archive | LOW | `NOT_STARTED` |

### 1b. Docker — Postgres data (the only thing that must survive)

| Item | Path | What it does | Replacement | Risk | Status |
|---|---|---|---|---|---|
| **AHOS canonical TS tables (19)** | Postgres `public.ahos_*`, DDL at `drizzle/0000_ahos_canonical_tables.sql` (33 statements, 19 additive `CREATE TABLE`, no SCHEMA/EXTENSION/OWNER) | TS One-Brain read model + chat persistence; Drizzle owns `ahos_*` | PGlite file store, DDL applied verbatim | **HIGHEST** — 778 real rows. **Mitigated: dumped + parity proven** (§2) | `VERIFIED` |
| `DATABASE_URL` env | `.env` (gitignored — confirmed via `git check-ignore`; values never printed or committed) | Gateway → Postgres | Same key, PGlite-flavoured value (`pglite://<dataDir>` or explicit flag) | LOW — one-key switch, rollback = restore old value | `NOT_STARTED` |
| `POSTGRES_PASSWORD` env | `.env` | Container DB superuser | Unused after switch; leave in place (never delete secrets) | NONE | `NOT_STARTED` |
| Legacy non-`ahos` tables | Postgres `public."user"`, `trade_decisions`, `agent_audit_trail`, `agent_registry`, n8n schemas | n8n + legacy audit; only `public."user"` needs `uuid-ossp` | Drop from scope; n8n data not needed (0 workflows). Legacy audit tables have **no live reader** in app code | LOW — but destructive to leave behind; **do not delete dumps**, archive | `NOT_STARTED` |
| `scripts/windows_ensure_postgres_win.ps1` | Ensures `ahos_postgres_win` container exists | Native equivalent: ensure PGlite dataDir exists + migration applied | MEDIUM — operator script; rewrite as no-op/bridge | `NOT_STARTED` |
| `scripts/windows_pg_probe.ps1` | `pg_isready`-style probe | Health probe against PGlite (in-process, always "up" once dataDir opens) | LOW | `NOT_STARTED` |
| `scripts/windows_ensure_database_url.ps1` | Writes `DATABASE_URL` for Docker PG | Rewrite for native target | LOW | `NOT_STARTED` |
| `scripts/windows_diagnose_docker_health.ps1`, `windows_pre_soak_readiness.ps1`, `windows_preflight_ops.ps1`, `windows_post_merge_reconcile.ps1`, `windows_write_ops_failure_paste.ps1`, `windows_test_reconcile_dirty_allow.ps1`, `windows_restore_owner_preserve.ps1`, `windows_checkout_unlock_tip.ps1`, `windows_bootstrap_presoak.ps1`, `windows_wait_for_web_api.ps1` | 10 further PS scripts invoking `docker`/`psql`/`pg_isready` | Ops/soak/g2 validation glue | Update Docker-dependent branches; keep their non-Docker logic | MEDIUM — soak/g2 pipelines; must be updated **in step** with the switch, not after | `NOT_STARTED` |
| `.bat` launchers shelling to the above | `AHOS_WINDOWS_OPS.bat`, `AHOS_PRE_SOAK_NOW.bat`, `AHOS_VALIDATE_G2_NOW.bat`, `AHOS_PULL_OPS_UNLOCK.bat` | Operator one-click entrypoints | Update targets; `start_ahos.bat` already Docker-free and becomes primary | LOW | `NOT_STARTED` |
| Guard regex | `.cursor/hooks/ahos-guard.py:45-46` | Blocks `docker compose up` in this repo | Keep (defense-in-depth; also blocks accidental re-launch) | NONE — **do not touch `.cursor/hooks.json` overlay** (binding) | `UNCHANGED` (human-gated, §5) |

### 1c. TypeScript gateway — the code that must keep working

| Item | Path | What it does | Replacement | Risk | Status |
|---|---|---|---|---|---|
| **DB client** | `db/index.ts` (73 lines) | Sole `pg.Pool` + `drizzle()`; lazy Proxy so import never throws | Add a **config-driven PGlite branch** (`drizzle-orm/pglite`, already bundled in `drizzle-orm@0.45.2`) | MEDIUM — but the change is one file, and the lazy-Proxy + fail-closed pattern already exists | `IMPLEMENTED` for the branch, `NOT_STARTED` for repo wiring |
| Schema | `schema.ts` (340 lines) + `db/schema.ts` (re-export shim) | 20 `pgTable`, 67 jsonb/serial/timestamp uses, **0 pgEnum**, **0 uuid columns** | **No rewrite needed** — PGlite driver exposes the same `PgDatabase`/`PgDialect`; all used types (jsonb, serial, timestamptz w/ tz, integer, text) are PGlite-supported (probe-proven) | LOW | `VERIFIED` (type-level, by probe + migration apply) |
| Migration | `drizzle/0000_ahos_canonical_tables.sql` | Canonical DDL | Applies to PGlite **verbatim** (all 33 statements ran clean) | NONE | `VERIFIED` |
| `drizzle.config.ts` | `dialect: "postgresql"`, `tablesFilter: ["ahos_*"]`, requires `DATABASE_URL` | Drizzle Kit config | Keep `postgresql` dialect (PGlite IS Postgres); point at native target | LOW | `NOT_STARTED` |
| Reader | `snapshot.ts:1-17` (13 tables), `failClosedCommandSnapshot` :56-109 | Dashboard/command read model | Unchanged — Drizzle API is identical | LOW | `NOT_STARTED` (needs runtime smoke) |
| Writer | `engine.ts:1` | Cycle/snapshot/opportunity writes | Unchanged | LOW | `NOT_STARTED` (needs runtime smoke) |
| Chat persist | `chat.ts:79-92`, `:425-432` | Best-effort insert + history | Unchanged | LOW | `NOT_STARTED` |
| News cache | `news.ts:92` | translation-cache read | Unchanged | NONE | `NOT_STARTED` |
| Route behaviour | `app/api/command/route.ts:20-23` (200 on failure), `app/api/chat/route.ts:19-24` + `:91-115` (retry + 500 w/ hint) | Honest degradation contract | **Preserve exactly** — this is the acceptance criterion for the smoke test | LOW | `NOT_STARTED` (must be asserted by a test) |

### 1d. n8n — automation edge, zero runtime coupling

| Item | Path | What it does | Replacement | Risk | Status |
|---|---|---|---|---|---|
| Ingest + integrity | `n8n/workflows/ahos_01_data_ingest_integrity.json` (7,165 B) | Scheduled ingest + integrity check | In-repo Python scheduler job (existing scheduler infra in `ahos_local.sqlite`: `scheduler_runs` 2,640, `scheduler_heartbeats`, `scheduler_locks`; spec at `docs/architecture/PRODUCTION_SCHEDULER_SPEC.md`) | LOW | `NOT_STARTED` |
| Signal pipeline | `n8n/workflows/ahos_02_signal_pipeline.json` (12,750 B) | strategy+risk gate mirror — **already mirrored in Python** (`engine/dryrun_simulation.py`) | In-repo job wrapping the existing Python path | LOW | `NOT_STARTED` |
| **QUARANTINED Telegram control** | `n8n/workflows/ahos_03_telegram_control.json` (15,605 B) | **UNSAFE**: SQL interpolation, audit `DELETE`, `/approve` bypassing canonical authority (see `reports/grok/GM06_N8N_QUARANTINE.md`, `TELEGRAM_REALITY_MAP.md` §5) | **NEVER imported, never replaced 1:1.** Its safe surfaces (status/health/agents read-only replies) already live in `run_bot.py`; the kill switch becomes an **independent Lane B control**, not edge-coupled; the human gate must route through the Canonical Decision Authority | **HIGH if revived** — stays quarantined. Kept under test-enforced name `ahos_03` | `BLOCKED` (by design — quarantine enforced by `tests/test_n8n_governance_rules.py` requiring `GM06_N8N_QUARANTINE.md`) |
| Research lab | `n8n/workflows/ahos_10_research_lab.json` (3,731 B) | research job | In-repo scheduler job (read-only research worker already exists: `research_worker/`, network-denied by policy) | LOW | `NOT_STARTED` |
| Data update | `n8n/workflows/ahos_11_data_update.json` (3,161 B) | data update | In-repo scheduler job | LOW | `NOT_STARTED` |
| Research report | `n8n/workflows/ahos_12_research_report.json` (2,242 B) | report scheduling | In-repo scheduler job | LOW | `NOT_STARTED` |
| Structural validator | `tests/validate_n8n.py` | G12 gate: validates workflow JSON structurally (`scripts/operator_validation_gate.py:595-609`, `:846`) | Retain as a **static schema check** over the archived JSONs (validates artifacts, not a live service) | LOW | `UNCHANGED` (keep passing) |
| Governance test | `tests/test_n8n_governance_rules.py` | Enforces quarantine naming `ahos_03` | Keep passing — it guards a real safety property | NONE | `UNCHANGED` |
| UTF-8 test | `tests/test_validate_n8n_utf8.py` | Encoding correctness of validator | Keep passing | NONE | `UNCHANGED` |
| Pipeline stage | `engine/run_all_checks.sh:28-29` (stage 6/6) | Runs n8n validation in the check chain | Keep (still validating archived files) | NONE | `UNCHANGED` |
| Path helper | `config/paths.py:99-100` | Resolves `n8n/` dir | Point at archive location **after** Stage 5, or keep resolving the original path if files stay in place | LOW | `NOT_STARTED` |
| Config references | `config/control_plane.yaml:24,50-52`, `config/agent_registry.yaml:16`, `config/.env.template:14-20` | Named n8n surfaces + `N8N_BASIC_AUTH_PASSWORD` template key | Update to native scheduler names; template key kept for compat | LOW | `NOT_STARTED` |
| Policy deny-lists | `ahos_org/policy.py:52,74`, `ahos_org/registry.py:141`, `ahos_org/resources.py:21`, `research_worker/protocol.py:98,130` (`network_denied`) | Deny n8n-directed network egress for agents | **Keep exactly** — these are safety boundaries, not Docker coupling | NONE | `UNCHANGED` |
| Docs | `docs/N8N_OPERATIONAL_PROCEDURE.md`, `docs/n8n_setup_guide.md`, `docs/RUNBOOK_OPERATIONS.md`, `docs/WINDOWS_OPERATOR_HANDOFF.md`, `docs/OPERATOR_VALIDATION_PROTOCOL.md` | Operator runbooks naming n8n | Update to native scheduler; archive the setup guide | LOW | `NOT_STARTED` |

### 1e. Tests that assert compose/n8n specifics — MUST move in step

| Item | Path | Assertion | Action | Risk |
|---|---|---|---|---|
| Deployment config test | `tests/test_deployment_config.py:64-77` | n8n service + `N8N_DIAGNOSTICS_ENABLED=="false"` — asserted against the **ROOT** `docker-compose.yml` (not the live windows one) | Re-anchor to archive location or to the native scheduler config | MEDIUM — will break on archive unless updated in the same commit |
| Web API auth gate test | `tests/test_web_api_auth_gate.py:254-263` | Windows compose: `$$POSTGRES_USER`, `start_period`, `postgresql_schema.sql` mount, `healthcheck: disable: true`, `service_started`, no `db:migrate` | Same — re-anchor | MEDIUM |
| Drizzle static safety test | `tests/test_drizzle_migration_static_safety.py:97-102` | Compose mounts legacy init SQL, **not** a drizzle migration | Same — re-anchor | MEDIUM |
| Broad grep hits | `tests/test_ahos.py`, `tests/test_boundaries.py`, `tests/test_operator_validation_gate.py`, `tests/test_runtime_w11.py` | Incidental compose/n8n string references | Verify each still passes post-switch; do not bulk-edit | LOW |

**No test connects to Postgres or starts a container** — all DB-touching tests
are static or monkeypatched. `.github/workflows/pytest-minimal.yml` has no
Docker/Postgres service. So the suite can validate the switch without Docker.

---

## 2. STAGE 2 — BACKUP + PARITY BASELINE (DONE, `VERIFIED`)

Location: `G:\robat\ahos_backups\pg_20261003T091351Z\` — **outside the repo**,
never committed (`.gitignore`-independent by path; nothing was staged).

| Artifact | Size / count | Purpose |
|---|---|---|
| `ahos_full.sql` | 762,965 B | `pg_dump --no-owner --no-privileges` plain format from PostgreSQL **16.15** (Alpine). 19 `COPY public.ahos_* ... FROM stdin;` blocks (lines 5668–6589) |
| `row_counts.txt` | 156 lines | Exact `count(*)` per table — the parity contract |

Server version: PostgreSQL 16.15 on x86_64-pc-linux-musl (Alpine), matching the
compose image `postgres:16.15-alpine`.

**Parity proof (this session, throwaway PGlite instance, since cleaned up):**
applied `drizzle/0000_ahos_canonical_tables.sql` (19/19 tables created), parsed
the 19 `COPY` blocks (TSV, `\N` → null), inserted via parameterized multi-row
INSERT, then compared to `row_counts.txt`:

```
rows copied: 778 | tables with data: 17
PARITY: 19 OK / 0 FAIL of 19
jsonb spot check: {"at":"2026-08-30T10:09:09.821Z","intent":"general",...}
timestamptz spot check: 2026-08-30T10:09:10.036Z
DONE
```

**19/19 tables, 778/778 rows, jsonb and timestamptz round-trip correctly.**
This is the strongest single piece of evidence for the whole mission: the
target engine restores the real dump with zero loss.

---

## 3. STAGE 3 — TECHNOLOGY DECISION (evidence-backed, `VERIFIED`)

The mission offers "native Windows PostgreSQL (portable/zip install … no admin
service)" and asks to justify the choice. **Native Windows binaries are
unobtainable from this network, and nothing is installed on the host.** Probe
results (this session):

| Source | Result |
|---|---|
| `enterprisedb.com` / `get.enterprisedb.com` | **403** — WAF error page (confirmed by ranged GET returning HTML, not a zip) |
| `postgresql.org` | DNS resolves (72.32.157.230, 87.238.57.232, 217.196.149.50) but **TLS handshake failure** (`schannel: failed to receive handshake, SSL/TLS connection failed`) |
| `bigsql.org`, `mirror.accum.se` | **000** — connection failed |
| Host filesystem | No `psql`, `pg_ctl`, or `postgres` binary; no `C:\Program Files\PostgreSQL` |

**Reachable:** `pypi.org`, `registry.npmjs.org`, `google.com`, `github.com`
releases.

**Decision: embedded PGlite (`@electric-sql/pglite`) via the driver already
bundled in `drizzle-orm@0.45.2` (`drizzle-orm/pglite`).**

Why this satisfies every mission constraint:

1. **It IS Postgres.** PGlite is real PostgreSQL 16 compiled to WASM — not a
   re-implementation, not a SQLite shim. `schema.ts` and the Drizzle migration
   apply unmodified; the Drizzle `PgDatabase` API is identical, so **zero
   schema rewrite and zero query rewrite**. This directly serves "prefer
   keeping Postgres semantics where code relies on them."
2. **Proven on this exact data.** §2 — 19/19 tables, 778/778 rows, jsonb and
   timestamptz intact. Feature probes passed: `jsonb`, `serial`/sequences,
   `timestamptz` with tz, `gen_random_uuid()`, indexes. (The `uuid-ossp`
   extension is genuinely unavailable in PGlite — irrelevant, since **no
   `ahos_*` table uses uuid**; the only uuid default belongs to n8n's
   `public."user"`, which is out of scope.)
3. **No blocked download.** Comes from npm, which is reachable. No binary from
   a 403/TLS-failing host.
4. **No admin rights, no service, no port.** Runs in-process as the gateway's
   own user process, persisting to a filesystem `dataDir`. Removes the port
   entirely — nothing to collide with, nothing to firewall, no service to
   install/uninstall. Strongly favours the owner's one-click-launcher goal.
5. **Consistent with the existing architecture.** Lane B already runs on
   embedded SQLite as user files; the gateway moving to an embedded file store
   is the same topology, not a new one. It also removes the dual-writer hazard
   for `data/*.sqlite` by making the native daemon the sole runtime owner.

**DataDir (proposed):** `G:\robat\ahos_runtime\pglite\ahos` (outside the repo,
next to the existing `ahos_runtime` stores), overridable by env. Never inside
the repo (would risk committing data).

**Where SQLite is justified instead:** Lane B stays on SQLite as-is — no change
needed, no change wanted. PGlite replaces only the Postgres the gateway used.

### 3a. STAGE 3 IMPLEMENTATION — `VERIFIED` (restore path), switch-over NOT started

What was actually built this session, all behind the existing config surface:

| Artifact | Path | What it proves |
|---|---|---|
| Dual-backend client | `db/index.ts` | `DATABASE_URL` scheme selects the backend. `pglite:<dataDir>` → embedded PGlite 16 via `drizzle-orm/pglite`; anything else → the existing node-postgres Pool, byte-for-byte unchanged. Both expose the same drizzle `PgDatabase` API, so the 4 live consumers (`snapshot.ts`, `engine.ts`, `chat.ts`, `news.ts`) are unmodified. |
| Restore + parity tool | `scripts/pglite_restore.ts` (CLI), `scripts/pglite_restore_lib.ts` (library) | Applies the canonical Drizzle migration to a dataDir, restores `ahos_*` COPY blocks from the Stage 2 dump, verifies exact row-count parity. Exit 1 on any parity gap so the launcher can treat restore as a real gate. PAPER_ONLY: read-only on the dump/counts files, writes only into `--dataDir`, never deletes the source. |
| Self-test | `scripts/pglite_backend_selftest.ts` → `npm run test:pglite-backend` | 14 tests, 14 pass: URL-scheme selection, dataDir extraction (Windows absolute / leading-slash / relative), end-to-end round-trip through the real drizzle layer (`serial`, `jsonb` as a parsed object, `timestamptz` as a UTC-exact `Date`, naive `timestamp`), COPY parser (block filtering, `\N`→NULL, `\t`/`\\` unescaping, empty blocks), full restore to exact parity, and that the legacy `pool` refuses to masquerade on the embedded path. |
| Package config | `package.json`, `next.config.ts` | `@electric-sql/pglite@^0.5.8` added; `serverExternalPackages` keeps the WASM module out of the webpack server bundle (it must resolve at runtime, not be bundled). |

**Verification on the real backup** (not a fixture) — the permanent tool,
restoring `pg_20261003T091351Z/ahos_full.sql` into a throwaway dataDir:

```
migration: applied 33 statements
restore: copied 778 rows across 19 tables
PARITY: 19 OK / 0 FAIL of 19
jsonb spot check: {"at":"2026-08-30T10:09:09.821Z","intent":"general",...}
timestamptz spot check: 2026-08-30T10:09:10.036Z
EXIT=0
```

This reproduces the Stage 2 throwaway-script result with the permanent code
path: same 19/19 tables, same 778 rows, same exit code.

**Gates run after the change:** `tsc --noEmit` clean; `eslint` clean on all
touched files; `test:pglite-backend` 14/14; `test:chat-handlechat` 18/18 and
`test:chat-agent` 30/30 (these transitively load `@/db` through `chat.ts` /
`snapshot.ts`, so they are the regression signal that the client change did
not break the import surface).

**Deliberate non-changes:** the legacy Postgres path is untouched — PGlite is
loaded through a lazy `require` so the legacy path never pays the WASM import
cost and never inherits its failure mode; `pool` still works there and throws
a clear message only on the embedded path. No Lane A file, no Python file, no
compose file, no n8n workflow, and no `.env` value was modified. The live
`DATABASE_URL` was NOT flipped — that is Stage 4 and stays owner-gated.

---

## 4. WHAT MUST NOT CHANGE (safety surface)

- Lane A (`discovery/`, `paper_trading/`) — FROZEN, untouched by this mission.
- Python canonical authority, security overlay, identity — all SQLite, all
  untouched.
- Policy deny-lists blocking n8n-directed egress (§1d) — safety boundaries.
- `ahos_03` quarantine — stays quarantined, test-enforced.
- The honest-degradation contract in the API routes (§1c) — the acceptance
  criterion, not a nuisance to remove.
- `.env` values, credentials — never printed, never committed; `POSTGRES_PASSWORD`
  and `N8N_BASIC_AUTH_PASSWORD` are left in place rather than deleted.

---

## 5. HUMAN-GATED — NOT DONE BY THIS MISSION, LISTED

Per binding constraints and part1 §28/§72/§91:

1. **Single runtime owner for `data/*.sqlite`** (native daemon vs container):
   a governance/authority choice. This mission defaults to native and records
   the decision; it does not force-kill the container path.
2. **Promoting any DB target to "the live system of record"** beyond this
   host's paper-only operation — operator decision after Stage 4 smoke.
3. **Deleting Docker Desktop / WSL2** from the host — owner action. We archive
   repo files; we never uninstall host software.
4. **Removing the n8n container or its DB** — owner action; n8n data is not
   needed (0 workflows) but destruction is not ours to perform.
5. **Constitution / governance-authority / Lane A changes** — none made.
6. **Secret rotation / credential changes** — none made.

---

## 6. STAGE TRACKER

| Stage | Scope | Status |
|---|---|---|
| 1 | Inventory + decision (this document) | `COMPLETE` — committed `d80b5b7`, pushed to `origin/ahos` |
| 2 | Backup + parity baseline | `VERIFIED` — 19/19 tables, 778/778 rows |
| 3 | Native replacement (PGlite client + restore path + 6 n8n jobs) | `VERIFIED` for the PGlite client + restore path (§3a): 19/19 tables, 778/778 rows via the permanent tool. The 6 n8n jobs are still `NOT_STARTED` — they are zero at runtime (§1d) and move in Stage 4/5. |
| 4 | Switch-over behind config + full tests + runtime smoke; defaults flipped only after green; rollback path documented | `NOT_STARTED` |
| 5 | Archive (not delete) `archive/docker_n8n_<date>/` + README; update docs/runbooks/truth maps | `NOT_STARTED` |

Rollback path (will be documented in Stage 4, stated here so it is never
forgotten): revert `DATABASE_URL` to the Docker Postgres value, restart the
gateway. Docker files are **kept**, never deleted — so rollback is a config
flip, not a restore from backup.

**Next action:** Stage 3 — add the config-driven PGlite branch to
`db/index.ts`, land a tested in-repo restore path (migration + `COPY`/TSV parse
→ parameterized inserts → parity assertion, reproducing the proven throwaway
script), then the six n8n scheduler jobs with tests. Commit locally per
sub-part; never push.
