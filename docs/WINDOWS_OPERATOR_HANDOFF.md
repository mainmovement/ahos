# Windows Operator Handoff

**Audience:** Owner / Windows operator  
**Agent role:** Make gates honestly runnable — **never** invent Windows PASS.

---

## CURRENT TRUTH

| Claim | Value |
|-------|--------|
| Integration (agent-host) | `INTEGRATION_READY` |
| Operator (Windows) | **`OPERATOR_READY = NOT_VERIFIED`** |
| Calibration | `CALIBRATION_READY_BUT_DATA_REQUIRED` |
| Pre-soak | **Blocked** until Windows `pre_soak_entry_ok` |
| Last paste | `20260828_220318` — G2 empty-gateway BLOCKED; G3–G10 PASS (paste predated #45) |
| Unlock tip | PR **#58** — prefer `AHOS_MAIN_CLEAR_G2.cmd` (see `docs/OWNER_ACTION_REQUIRED.md`) |
| Paste sink | PR **#56** — **LEAVE OPEN** (do not merge) |
| Installer | `.\install_windows.ps1` prepares tools — never upgrades readiness |

Only your real Windows artifacts can change the operator row.

### Right now (PAPER_ONLY)

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/4adfacb3154943a119396f5d7d82c06943a61a53/AHOS_MAIN_CLEAR_G2.cmd
AHOS_MAIN_CLEAR_G2.cmd
```

Or tip runner: `AHOS_RUN_TIP.cmd` from `cursor/windows-main-evidence-push-4bde`.

STATE B: never `db:migrate` / `db:push`. Do not invent PRE_SOAK / READY.

---

## WINDOWS PREREQUISITES

| Item | Notes |
|------|--------|
| OS | Windows 10 or 11 |
| Python | **3.11+** (`python --version`) |
| Node.js + npm | LTS on PATH |
| Git | Clone of AHOS |
| venv | `.\.venv\Scripts\Activate.ps1` |
| Network | HTTPS for live providers (G3) |
| Postgres | Required for One-Brain G2 — set `DATABASE_URL` in `.env` |
| Env | `AHOS_PAPER_ONLY=1`, `AHOS_EVIDENCE_SOURCE=local` |
| Gateway URL | `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` when `npm run dev` is up |
| Web API token | Same value in `AHOS_WEB_API_TOKEN` and `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` (fail-closed; empty locks `/api/*` unless `AHOS_WEB_API_ALLOW_OPEN_ACCESS=1`) |
| SQLite stores | `.\data\e01_discovery.sqlite`, `paper_trading.sqlite`, `ahos_local.sqlite`, `ahos_knowledge.sqlite` (via `init_databases.py`) |
| Telegram | Bot token — owner only (G11) |
| n8n | Optional (G12 operational) |

**Do not use** `AHOS_DB_PATH=.\data\ahos.db` — that path is not the canonical store. Use `AHOS_DATA_DIR` only if relocating the whole `data\` directory.

---

## EXACT COMMANDS (PowerShell, in order)

### 0) Identity

```powershell
cd <PATH_TO_AHOS_REPO>
Get-Location
git rev-parse --short HEAD
git status -sb
python --version
node --version
npm --version
```

### 0b) Optional one-click prep (canonical installer)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
# optional paper seed (live network):
# .\install_windows.ps1 -SeedEvidence
```

This prepares venv, `requirements.txt`, `npm install`, root `.env` from `.env.example` (never overwrites), `init_databases.py --with-guards`, and PAPER_ONLY.  
It does **not** claim OPERATOR_READY, does **not** start PRE_SOAK, and does **not** run the operator gate.

### 1) Python setup (manual alternative — no editable install)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

If `Activate.ps1` is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 2) Bootstrap SQLite stores (required before runtime)

```powershell
python scripts\init_databases.py --with-guards
```

Expect `RESULT: ALL STORES HEALTHY`.

### 3) Seed evidence (fresh laptop)

```powershell
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
python -m architecture.runtime --single-cycle --evidence-source local --limit 5
python scripts\prediction_lifecycle_status.py
```

### 4) One-Brain env + gateway (Terminal A) — required for G2 PASS

Copy `.env.example` → `.env` and set at least:

```text
DATABASE_URL=postgresql://USER:PASS@127.0.0.1:5432/ahos
AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat
AHOS_PAPER_ONLY=1
AHOS_WEB_API_TOKEN=<same-random>
NEXT_PUBLIC_AHOS_WEB_API_TOKEN=<same-random>
AHOS_WEB_API_ALLOW_OPEN_ACCESS=0
```

Or generate tokens without editing by hand:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_ensure_web_api_token.ps1
```

Then:

```powershell
cd <PATH_TO_AHOS_REPO>
npm install
npm run dev
```

Leave running on port **3000**. Without `DATABASE_URL`, Next may listen but `/api/chat` returns **500** → G2 **FAIL**. Without web API token (and without open-access), `/api/chat` returns **401** → G2 **BLOCKED**.

### 5) Gate runner (Terminal B)

```powershell
cd <PATH_TO_AHOS_REPO>
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"
# AHOS_WEB_API_TOKEN is loaded from .env by the gate runner (same Bearer as Next).

python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

After Telegram E2E (optional for pre-soak; required for `OPERATOR_READY`):

```powershell
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill --telegram-e2e-artifact reports\telegram_e2e_<UTC>.md
```

### 6) Pre-soak — only if `pre_soak_entry_ok` is true

Follow `docs\PRE_SOAK_PROTOCOL.md`.

### 7) G11 / G12 (owner)

- `docs\TELEGRAM_OPERATOR_E2E_PROTOCOL.md`
- `docs\N8N_OPERATIONAL_PROCEDURE.md`

---

## EXPECTED OUTPUT

| Step | Expected |
|------|----------|
| 0–1 | Versions + venv OK |
| 2 | ALL STORES HEALTHY |
| 3 | local_predictions / observations > 0 (or honest provider failure) |
| 4 | Next on `:3000` with working Postgres |
| 5 | `reports\operator_validation_report_windows_*.json` |
| 5 core success | `pre_soak_entry_ok: true` (often exit **3** until G11) |
| 5 with FAIL | exit **2** |
| G3 | Real provider SUCCESS only |
| G11 | `OWNER_ACTION_REQUIRED` / `NOT_VERIFIED` until artifact attestation |
| G12 | `STRUCTURAL_VALID` until operational proof |

---

## FAILURE INTERPRETATION

| Failure | Meaning | Do not |
|---------|---------|--------|
| G1 BLOCKED | Missing Node/npm | Claim ready |
| G2 FAIL (connection) | `npm run dev` down | Edit docs to OPERATOR_READY |
| G2 FAIL (HTTP 500) | Often missing/bad `DATABASE_URL` | Treat as “npm not running” only |
| G3 FAIL | Live providers failed | Fixture as live |
| G4–G9 FAIL | No/broken local evidence or freeze/safety | Fabricate ledger / edit Lane A |
| G10 FAIL | Backup drill failed | Skip recovery claim |
| Exit 3 | Not full OPERATOR_READY (often G11) | Treat as production done |
| Urge to soak early | Entry blocked | Start PRE_SOAK |

**Do not add AG-25 / holders / AI orchestration features to clear a gate.**

---

## REQUIRED ARTIFACTS

1. `reports\operator_validation_report_windows_<YYYYMMDD_HHMMSS>.json`
2. Windows evidence in `docs\OPERATOR_VALIDATION_REPORT.md`
3. (G11) `reports\telegram_e2e_<UTC>.md` when run
4. (G12) operational proof when run

**Reject:** agent-host JSON as Windows; `_scratch` as readiness; mocks; invented calibration pairs.

---

## GATE MAP (G1–G12)

| Gate | Windows proof |
|------|----------------|
| G1 Environment | Python **3.11+** + node/npm + writable data |
| G2 Gateway | Live POST `/api/chat` on :3000 with Bearer when token set (401 WEB_API_* = BLOCKED; 5xx=FAIL; other 4xx=reachable PASS) |
| G3 Providers | Live probe SUCCESS (tokens>0) |
| G4 Evidence | Observations present |
| G5 Scoring | local_predictions > 0 |
| G6 Security | PAPER_ONLY / safe env |
| G7 Lane-A | `python scripts\freeze_lane_a.py` OK |
| G8 Lifecycle reg | observation_state > 0 |
| G9 Observation | discovery_observations > 0; labels may be 0 |
| G10 Restart | `--backup-drill` PASS |
| G11 Telegram | Token + `--telegram-e2e-artifact` attestation |
| G12 n8n | Structural vs operational |

`pre_soak_entry_ok` ⇔ Windows ∧ G1–G10 PASS.  
`operator_ready` ⇔ Windows ∧ G1–G11 PASS ∧ G12 structural/PASS.

---

## CALIBRATION CLOCK

| Event | When |
|-------|------|
| Does not start | Agent-host only / failed G4–G9 |
| **T0** | Wall time when Windows leaves real preds in OBSERVING |
| **T+72h** | Real elapsed time + observation cycles |
| Forbidden | Hand-made pairs / clock injection as production evidence |

---

## PRE-SOAK ENTRY CONDITION

1. Windows gate JSON on disk  
2. `platform_effective == "windows"`  
3. `summary.pre_soak_entry_ok == true`  

Else **STOP**.

---

## STOP CONDITIONS (soak)

- PAPER_ONLY / security veto compromised  
- Lane A freeze FAIL  
- DB/backup failure  
- Provider failure hidden by mocks  
- Fabricating outcomes or readiness  

---

## OWNER ACTIONS

1. Run this PowerShell sequence; keep the Windows JSON  
2. Provide Postgres + `DATABASE_URL` for G2  
3. Telegram bot token + G11 E2E artifact  
4. Optional n8n operational (G12)  
5. After unlock: pre-soak; wait real T+72h  
6. Decide PR #19 merge (agents must not merge)  

**Do not invent Windows PASS commits.**

---

## KNOWN LANE-A WINDOWS GAP (do not silently “fix”)

Frozen Lane-A files still use naive `file:{path}?mode=ro` in:

- `discovery/observe_active.py`
- `paper_trading/ledger.py`

Lane B / scripts / runtime now use `config.paths.connect_sqlite_ro` (Windows-safe).  
Patching Lane A requires an explicit freeze re-anchor (`python scripts\freeze_lane_a.py --write`) after owner-approved change — **not done in this pass**.

---

## Pointers

- Protocol: `docs\OPERATOR_VALIDATION_PROTOCOL.md`  
- Runner: `scripts\operator_validation_gate.py`  
- Pre-soak: `docs\PRE_SOAK_PROTOCOL.md`  
- Snapshot: `docs\CURRENT_TRUTH_SNAPSHOT.md`  
- Quickstart: `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`  
