# AHOS — Canonical Operational Command Reference

**Purpose:** The ONE place for current, working AHOS commands. Supersedes
command listings scattered across `README.md`, `QUICKSTART.md`,
`AHOS_LOCAL_SOAK_PROTOCOL.md`, `AHOS_WINDOWS_OPERATOR_RUNBOOK.md`,
`AHOS_OPERATOR_QUICKSTART_WINDOWS.md`, `AGENTS.md`, and the `.bat` files.

**Law:** If a command appears in a historical document but not here, the
historical document is describing an older procedure. Historical documents may
retain their commands, but they must not be mistaken for current instructions
(this is why `AHOS_FINAL_STATUS.md` and `AHOS_PRODUCTION_READINESS_REPORT.md`
are bannered superseded in `docs/DOC_TRUTH_MAP.md` §B).

**Verified:** every command below was verified against the tree at
`4b37be3` (2026-09-24) — the entrypoints exist and the documented flags match
the implemented CLI parsers.

**Paper-only.** No command here trades, spends, or moves real funds.

---

## 0. Absolute constraints (read first)

| Constraint | Rule |
|---|---|
| Lane A | `discovery/**` and `paper_trading/**` are FROZEN. Never edit them. `scripts/freeze_lane_a.py --write` is **human-only**. |
| Live trading | Disabled at every layer. Any command that would enable it is forbidden (`AGENTS.md` §Safety). |
| Databases | Never share SQLite/Postgres between worktrees. Never copy an external runtime `.sqlite` into the tree. |
| `db:migrate` | **Never run it casually.** The `.bat` operator files carry the standing rule: "STATE B: never `db:migrate` / `db:push`". Schema changes require an owner-approved reviewed change. |
| Read-only first | When in doubt, run the `--status` / `--help` / verify-only form of any command. |

---

## 1. Environment prerequisites

```bash
# Python 3.11+ in .venv (repo-local, already present)
.venv/Scripts/python.exe --version        # Windows
# .venv/bin/python --version              # POSIX

# Node for the TypeScript surface
npm install
```

`AHOS_GATEWAY_URL`, alert keys, and provider keys are documented in
`.env.example`. Never place tokens in `NEXT_PUBLIC_*` (`AGENTS.md` §Safety).

---

## 2. Developer gates (run before any change)

```bash
# Import boundary check (fast, non-mutating)
.venv/Scripts/python.exe scripts/validate_imports.py

# Lane-A freeze integrity (verify-only; --write is human-only)
.venv/Scripts/python.exe scripts/freeze_lane_a.py

# Python test suite
.venv/Scripts/python.exe -m pytest tests -q

# TypeScript gates
npm run typecheck
npm run lint

# TypeScript selftests (fail-closed behaviour, no external services)
npm run test:web-api-auth
npm run test:canonical-read-model
npm run test:canonical-security
npm run test:alert-banner
```

---

## 3. Canonical runtime (Lane B observation daemon)

```bash
# Entrypoint help — always safe
.venv/Scripts/python.exe -m architecture.runtime --help

# One complete cycle, then exit (safe smoke test; writes only to its own stores)
.venv/Scripts/python.exe -m architecture.runtime --single-cycle

# Continuous daemon with the frozen Lane-A observation cycle attached
.venv/Scripts/python.exe -m architecture.runtime \
    --daemon --interval-sec 60 --observation-cycle

# Chain selection (solana | ethereum | bsc | base)
.venv/Scripts/python.exe -m architecture.runtime --chain solana --single-cycle

# Provider reachability probe — writes a committed JSON artifact
.venv/Scripts/python.exe -m architecture.runtime --probe-providers

# Soak snapshots (every N hours while the daemon runs)
.venv/Scripts/python.exe -m architecture.runtime \
    --daemon --observation-cycle --snapshot-interval-hours 6
```

Evidence provenance is stamped per run via `--evidence-source
{local,sandbox,test,synthetic}`. Only `local` is calibration-eligible
(`AHOS_GAP_REGISTER.md` M-GAP-015). Default is `sandbox` (opt-in, never
opt-out).

---

## 4. Scheduler watchdog (local-only by design)

```bash
.venv/Scripts/python.exe -m architecture.scheduling.watchdog --status
.venv/Scripts/python.exe -m architecture.scheduling.watchdog --status --json
.venv/Scripts/python.exe -m architecture.scheduling.watchdog \
    --status --max-age-sec 300 --json
```

Off-box watchdog alerting is **optional**, not an acceptance item
(M-GAP-012).

---

## 5. Windows operator sequence (owner, human-run)

Authoritative order per `AHOS_WINDOWS_OPERATOR_RUNBOOK.md` and
`docs/WINDOWS_OPERATOR_HANDOFF.md`:

```bash
# 1. Initialise the four local SQLite stores
.venv/Scripts/python.exe scripts/init_databases.py

# 2. Developer gates (§2 above)

# 3. Record the official laptop baseline (Windows + Python 3.11+, clean tree)
#    Emits official_168h_eligible=true only if every gate passes.
#    Exits 2 when ineligible. Rejects enabled live-trading env vars.
.venv/Scripts/python.exe scripts/record_local_laptop_baseline.py

# 4. Start the observation daemon (§3)

# 5. Confirm watchdog OK, write the t0 snapshot
.venv/Scripts/python.exe scripts/system_state_snapshot.py

# 6. Begin the 168-hour clock: sleep disabled, AC power connected.
```

`OPERATOR_READY` stays `NOT_VERIFIED` until a real
`reports/operator_validation_report_windows_*.json` exists from the owner host.

---

## 6. Soak, evidence, and persistence tooling

```bash
# Soak snapshot
.venv/Scripts/python.exe scripts/soak_snapshot.py

# Reliability challenge (controlled-failure matrix)
.venv/Scripts/python.exe scripts/reliability_challenge.py

# Backup/restore drill (Online Backup API; verifies source/backup/restored sha256)
.venv/Scripts/python.exe scripts/sqlite_backup_restore.py drill

# Nightly series — appends one verified night; counts DISTINCT UTC dates
# (re-running in one evening still reads 1/7, so the series cannot be gamed)
.venv/Scripts/python.exe scripts/sqlite_backup_restore.py nightly

# Calibration report (honest INSUFFICIENT_DATA until real pairs accrue — M-GAP-008)
.venv/Scripts/python.exe scripts/calibration_report.py
```

---

## 7. Web Command Center (TypeScript surface)

```bash
npm run dev          # next dev on 127.0.0.1
npm run build        # production build
npm run start        # serve the built app on 127.0.0.1
```

Open the site once, press **شروع پروژه**; cycles continue until **توقف**.

This surface is a read model and presentation layer. `scoring.ts` /
`council.ts` may rank and fail-closed REJECT/ABSTAIN for display, but they
**must not** emit `WATCH` / `PAPER_CANDIDATE` without an injected Python
`canonicalBackend` (`AGENTS.md` §Authority).

---

## 8. Git hygiene

```bash
# The repository's own maintenance pattern (from git reflog main):
git pull --ff-only origin main

# Worktrees for concurrent writers — isolate DBs, ports, and evidence paths
# (AGENTS.md §Workflow). Never share a SQLite/Postgres store between worktrees.
```

Never force-push, never auto-merge, never push to `main` without review
(`AGENTS.md` §Safety).

---

## 9. Commands that are intentionally NOT current

| Command / artifact | Status |
|---|---|
| `AHOS_MAIN_FIRST.bat`, `AHOS_APPLY_TIP.bat`, `AHOS_BOOTSTRAP_PRESOAK.bat`, `AHOS_FIX_G2_AND_GATE.bat`, `AHOS_PRE_SOAK_NOW.bat`, `AHOS_PULL_OPS_UNLOCK.bat`, `AHOS_PUSH_EVIDENCE_NOW.bat`, `AHOS_VALIDATE_G2_NOW.bat`, `AHOS_WINDOWS_OPS.bat`, `start_ahos.bat` | **Historical operator unlock scripts.** They download tips from the branch `cursor/windows-evidence-notify-retarget-4bde` (branch still exists). They are Windows convenience wrappers around §2/§3/§5 above, not new authority. Their "STATE B: never `db:migrate` / `db:push`" rule remains binding. |
| `python3 -m architecture.runtime ...` | POSIX form; on Windows use `.venv/Scripts/python.exe`. Both resolve the same package (`architecture/runtime/__main__.py`). |
| `/home/user/ahos` paths in `reports/*.json`, `research/experiments/*.json`, `docs/mission_v1_1/*` | **Historical evidence.** These recorded where data lived on the original Linux host. They must not be rewritten — rewriting historical evidence is forbidden. `config/paths.py` already eliminates the hard-coded dependency at runtime. |
| `tests/test_ahos.py` `UPLOAD_BTC = Path("/home/user/uploads/...")` | **Safe legacy hint, not a dependency.** It is guarded: `BTC = str(UPLOAD_BTC if UPLOAD_BTC.exists() else RESEARCH_BTC)`, falling back to the repo-relative `research/data/BTCUSDT_1h_3yr.csv`. No change needed. |
| `db:migrate`, `db:generate` | Present in `package.json`; **never run casually** (§0). |

---

## 10. Honest status of what these commands can prove

Running everything above proves: import boundaries hold, Lane A is intact,
tests pass, the daemon starts, and providers either answer or are honestly
reported as `TLS_ERROR` / `NO_KEY` / `UNSUPPORTED`.

It does **not** prove: soak passed (M-GAP-003, ~84H evidenced < 168H),
calibration (M-GAP-008, 0 joined pairs), live Telegram (M-GAP-009), or
`OPERATOR_READY` (no Windows artifact). See `AHOS_GAP_REGISTER.md`.
