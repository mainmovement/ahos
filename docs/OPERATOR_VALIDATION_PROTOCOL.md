# Operator Validation Protocol (Windows-first)

**Purpose:** Prove AHOS on the **owner's Windows 10/11 host** before any soak.

**Current product claim (do not invent):**

| Claim | Status |
|-------|--------|
| Integration (agent-host) | `INTEGRATION_READY` |
| Operator (Windows) | **`OPERATOR_READY = NOT_VERIFIED`** |
| Pre-soak | **blocked** until Windows **G1–G10** all PASS (`summary.pre_soak_entry_ok`) |

**Do not:** add features, fabricate PASS, invent calibration pairs, merge PR #19, or start PRE_SOAK without Windows G1–G10 evidence.

Canonical handoff: `docs/WINDOWS_OPERATOR_HANDOFF.md`.

---

## Prerequisites (Windows PowerShell)

| Tool | Check command | Required |
|------|---------------|----------|
| Python 3.11+ | `python --version` | Yes |
| Node.js LTS | `node --version` | Yes (G1/G2) |
| npm | `npm --version` | Yes (G1/G2) |
| Git | `git --version` | Yes |
| Repo at AHOS root | `pwd` shows repo | Yes |
| venv | `.\.venv\Scripts\python.exe` | Yes after setup |
| Network HTTPS | DexScreener / GeckoTerminal | Yes for G3 |
| Telegram bot token | env only for G11 | Owner-only |
| n8n | optional G12 operational | Owner-only |

**Environment:**

```powershell
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_DB_PATH = ".\data\ahos.db"
$env:PYTHONPATH = "."
# When Terminal A (npm run dev) is up:
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"
```

**Paths (repo-relative):**

| Role | Path |
|------|------|
| Primary SQLite (typical) | `.\data\ahos.db` / lifecycle DBs under `.\data\` |
| Backup drill workdir | `.\reports\_scratch\backup_restore_drill\` (gitignored) |
| Gate report | `.\reports\operator_validation_report_windows_<stamp>.json` |

---

## Exact PowerShell sequence (copy/paste)

Run from the **repository root**.

### Step 0 — Identity

```powershell
cd <PATH_TO_AHOS_REPO>
pwd
git rev-parse --short HEAD
git status -sb
python --version
node --version
npm --version
```

**Expected:** Versions print. No gate PASS yet.

### Step 1 — Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
pip install -e .
```

If `Activate.ps1` is blocked:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

**Expected:** Install succeeds. Failure → fix prerequisites; do not claim OPERATOR_READY.

### Step 2 — Seed local evidence (needed for G4/G5/G8/G9 on a fresh Windows DB)

```powershell
$env:AHOS_PAPER_ONLY = "1"
$env:PYTHONPATH = "."
$env:AHOS_LIVE_COLLECT = "1"
python -m architecture.runtime --single-cycle --evidence-source local --limit 5
python scripts\prediction_lifecycle_status.py
```

**Expected:** Cycle completes; local_predictions / discovery_observations > 0. If providers fail, G3/G4 will FAIL honestly — do not mock.

### Step 3 — One-Brain gateway (Terminal A) — required for G2 PASS

```powershell
cd <PATH_TO_AHOS_REPO>
npm install
npm run dev
```

**Expected:** Next.js listens on port **3000**. Leave running.  
G2 probes **`POST http://127.0.0.1:3000/api/chat`** (not `/health`).

If you skip Terminal A, G2 must be **FAIL**.

### Step 4 — Operator validation gate (Terminal B)

```powershell
cd <PATH_TO_AHOS_REPO>
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:PYTHONPATH = "."
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"

python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

**Expected:** JSON printed; file under `reports\operator_validation_report_windows_*.json`.

| Field | Meaning |
|-------|---------|
| `summary.g1_g10_all_pass` | true only if G1–G10 all PASS |
| `summary.pre_soak_entry_ok` | true only on Windows when G1–G10 all PASS |
| `summary.operator_ready` | true only if G1–G11 PASS (+ G12 structural) — **G11 never auto-PASS** |
| `summary.classification` | stays `INTEGRATION_READY` until full OPERATOR_READY |

**Exit codes:**

| Code | Meaning |
|------|---------|
| `0` | No FAIL; on Windows also `operator_ready=true` (needs G11 PASS artifact) |
| `1` | Fatal runner error |
| `2` | At least one gate **FAIL** |
| `3` | Windows run, no FAIL, but `operator_ready` still false (typical until G11) |

### Step 5 — Human report

Fill Windows columns in `docs\OPERATOR_VALIDATION_REPORT.md` from the JSON. Do not invent PASS.

### Step 6 — Telegram E2E (G11) — owner

`docs\TELEGRAM_OPERATOR_E2E_PROTOCOL.md` → archive `reports\telegram_e2e_<UTC>.md`.  
Until then G11 = **OWNER_ACTION_REQUIRED** (or NOT_VERIFIED if token set without transcript).

### Step 7 — n8n (G12) — owner

JSON import ≠ operational. `docs\N8N_OPERATIONAL_PROCEDURE.md`.

---

## Gate map (G1–G12) — matches `scripts/operator_validation_gate.py`

| Gate | Name | Windows proof | Honest non-PASS |
|------|------|---------------|-----------------|
| **G1** | Environment | Python≥3.10, `architecture` import, writable `data\`, node+npm on PATH | Missing node/npm → **BLOCKED** |
| **G2** | Gateway | Live POST to `AHOS_GATEWAY_URL` (default `http://127.0.0.1:3000/api/chat`) while `npm run dev` | Connection refused → **FAIL**; empty URL → **BLOCKED** |
| **G3** | Discovery providers | `--probe-providers` live SUCCESS with tokens>0 | No SUCCESS → **FAIL**; flag omitted → **NOT_VERIFIED** (not PASS) |
| **G4** | Evidence persistence | DB has discovery or production observations | Empty → **FAIL** |
| **G5** | Scoring / predictions | `local_predictions > 0` | Zero → **FAIL** |
| **G6** | Security / PAPER_ONLY | `assert_safe_environment()` | Violation → **FAIL** |
| **G7** | Lane-A freeze | `freeze_lane_a.verify` clean | Drift → **FAIL** |
| **G8** | Prediction lifecycle | observation_state total > 0 | Zero → **FAIL** |
| **G9** | Observation lifecycle | discovery_observations > 0; labels may be 0 until T+72h | Zero obs → **FAIL** |
| **G10** | Restart/recovery | `--backup-drill` sqlite drill exit 0 | Fail/missing script → **FAIL**/**BLOCKED** |
| **G11** | Telegram live E2E | Owner protocol + transcript | No token → **OWNER_ACTION_REQUIRED**; never fake PASS |
| **G12** | n8n | `tests/validate_n8n.py` | Structural only → **STRUCTURAL_VALID**; not operational PASS |

---

## Failure interpretation

| Symptom | Meaning | Do **not** |
|---------|---------|------------|
| G1 BLOCKED | Node/npm missing | Claim env PASS |
| G2 FAIL | Gateway not listening | Claim OPERATOR_READY; change readiness docs |
| G3 FAIL / NOT_VERIFIED | Live providers missing or not probed | Use mocks as live evidence |
| G4/G5/G8/G9 FAIL | No local evidence yet | Fabricate DB rows or calibration pairs |
| G6 FAIL | Safety/PAPER_ONLY broken | Disable safety to green |
| G7 FAIL | Lane A freeze broken | Rewrite frozen Lane A |
| G10 FAIL | Backup drill failed | Skip drill and claim recovery |
| G11 OWNER_ACTION | Need live Telegram | Fake screenshots |
| Exit 3 with `pre_soak_entry_ok=true` | Core Windows gates OK; OPERATOR_READY still blocked on G11 | Promote OPERATOR_READY |

**Never change readiness classification without the Windows JSON artifact as evidence.**

---

## Required artifacts (real Windows run)

1. `reports\operator_validation_report_windows_<stamp>.json`
2. Updated Windows section in `docs\OPERATOR_VALIDATION_REPORT.md`
3. Optional: `reports\provider_probe_opval_*.json` from G3
4. G11: `reports\telegram_e2e_<UTC>.md` when you run it

**Reject:** `reports\_scratch\*` as readiness evidence; agent-host JSON renamed as Windows; mocks; invented outcome labels.

---

## Calibration clock

1. Starts only after Windows G4/G5/G8 leave real predictions **OBSERVING**.
2. **T0** = wall clock on the Windows host at that registration.
3. Wait real **T+72h**; run observation cycles; never fabricate pairs.

Until then: `CALIBRATION_READY_BUT_DATA_REQUIRED`.

---

## Pre-soak entry (hard)

Unlock when Windows JSON shows:

- `meta` / `platform_effective` == `windows`
- `summary.pre_soak_entry_ok` == `true` (G1–G10 all PASS)

Then `docs/PRE_SOAK_PROTOCOL.md`.  
Agent-host PASS does **not** unlock soak.  
`operator_ready=true` is **not** required for short pre-soak, but **is** required to claim `OPERATOR_READY`.

---

## Related

- Handoff: `docs/WINDOWS_OPERATOR_HANDOFF.md`
- Pre-soak: `docs/PRE_SOAK_PROTOCOL.md`
- Snapshot: `docs/CURRENT_TRUTH_SNAPSHOT.md`
- Quickstart: `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`
