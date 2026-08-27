# Windows Operator Handoff

**Audience:** Owner / Windows operator  
**This pass:** Protocols + gate runner only — **no** simulated Windows PASS commits.

---

## CURRENT TRUTH

| Claim | Value |
|-------|--------|
| Integration (agent-host) | `INTEGRATION_READY` |
| Operator (Windows) | **`OPERATOR_READY = NOT_VERIFIED`** |
| Calibration | `CALIBRATION_READY_BUT_DATA_REQUIRED` |
| Pre-soak | **Blocked** until Windows `pre_soak_entry_ok` |
| PR #19 | Do **not** merge as part of this handoff |

Only your real Windows artifacts can change the operator row.

---

## WINDOWS PREREQUISITES

| Item | Notes |
|------|--------|
| OS | Windows 10 or 11 |
| Python | 3.11+ (`python --version`) |
| Node.js + npm | LTS on PATH |
| Git | Clone of AHOS |
| venv | `.\.venv\Scripts\Activate.ps1` |
| Network | HTTPS for live providers |
| Env | `AHOS_PAPER_ONLY=1`, `PYTHONPATH=.` |
| Gateway URL | `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` when `npm run dev` is up |
| DB | Under `.\data\` (created by runtime / lifecycle) |
| Telegram | Bot token — owner only (G11) |
| n8n | Optional (G12 operational) |

---

## EXACT COMMANDS (PowerShell, in order)

### 0) Identity

```powershell
cd <PATH_TO_AHOS_REPO>
pwd
git rev-parse --short HEAD
git status -sb
python --version
node --version
npm --version
```

### 1) Python setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
pip install -e .
```

### 2) Seed evidence (fresh laptop DB)

```powershell
$env:AHOS_PAPER_ONLY = "1"
$env:PYTHONPATH = "."
$env:AHOS_LIVE_COLLECT = "1"
python -m architecture.runtime --single-cycle --evidence-source local --limit 5
python scripts\prediction_lifecycle_status.py
```

### 3) Gateway (Terminal A) — required for G2 PASS

```powershell
cd <PATH_TO_AHOS_REPO>
npm install
npm run dev
```

Leave running on port **3000**.

### 4) Gate runner (Terminal B)

```powershell
cd <PATH_TO_AHOS_REPO>
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:PYTHONPATH = "."
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"

python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

### 5) Pre-soak — only if `pre_soak_entry_ok` is true

Follow `docs\PRE_SOAK_PROTOCOL.md`. Do **not** run if any of G1–G10 FAIL/BLOCKED.

### 6) G11 / G12 (owner)

- `docs\TELEGRAM_OPERATOR_E2E_PROTOCOL.md`
- `docs\N8N_OPERATIONAL_PROCEDURE.md`

---

## EXPECTED OUTPUT

| Step | Expected |
|------|----------|
| 0–1 | Versions + venv OK |
| 2 | local_predictions / observations > 0 (or honest provider failure) |
| 3 | Next on `:3000` |
| 4 | Report JSON; G1–G12 rows honest |
| 4 core success | `pre_soak_entry_ok: true`, often exit code **3** until G11 PASS |
| 4 with FAIL | exit code **2**; `operator_ready: false` |
| G3 | Real provider SUCCESS only — never mock |
| G11 | `OWNER_ACTION_REQUIRED` until live E2E archived |
| G12 | `STRUCTURAL_VALID` until operational proof |
| Full OPERATOR_READY | `operator_ready: true` only after G11 PASS (+ G1–G10) |

---

## FAILURE INTERPRETATION

| Failure | Meaning | Do not |
|---------|---------|--------|
| G1 BLOCKED | Missing Node/npm | Claim ready |
| G2 FAIL | `npm run dev` down | Edit docs to OPERATOR_READY |
| G3 FAIL | Live providers failed | Fixture as live |
| G4–G9 FAIL | No/broken local evidence or freeze/safety | Fabricate ledger / break Lane A |
| G10 FAIL | Backup drill failed | Skip recovery claim |
| Exit 3 | Not full OPERATOR_READY (often G11) | Treat as Windows production done |
| Urge to soak early | Entry blocked | Start PRE_SOAK |

**Do not add AG-25 / holders / AI orchestration features to clear a gate.**

---

## REQUIRED ARTIFACTS

1. `reports\operator_validation_report_windows_<YYYYMMDD_HHMMSS>.json`
2. Windows evidence filled in `docs\OPERATOR_VALIDATION_REPORT.md`
3. (G11) `reports\telegram_e2e_<UTC>.md` when run
4. (G12) operational proof when run

**Reject:** agent-host JSON as Windows; `_scratch` as readiness; mocks; invented calibration pairs.

---

## GATE MAP (G1–G12)

| Gate | Windows proof |
|------|----------------|
| G1 Environment | Python + node/npm + writable data |
| G2 Gateway | Live POST `/api/chat` on :3000 |
| G3 Providers | Live probe SUCCESS (tokens>0) |
| G4 Evidence | Observations present |
| G5 Scoring | local_predictions > 0 |
| G6 Security | PAPER_ONLY / safe env |
| G7 Lane-A | Freeze verify OK |
| G8 Lifecycle reg | observation_state > 0 |
| G9 Observation | discovery_observations > 0; labels may be 0 |
| G10 Restart | `--backup-drill` PASS |
| G11 Telegram | Owner E2E only |
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

All required:

1. Windows gate JSON on disk  
2. `platform_effective == "windows"`  
3. `summary.pre_soak_entry_ok == true`  

Then `docs\PRE_SOAK_PROTOCOL.md`. Else **STOP**.

---

## STOP CONDITIONS (soak)

- PAPER_ONLY / security veto compromised  
- Lane A freeze FAIL  
- DB/backup failure  
- Provider failure hidden by mocks  
- Fabricating outcomes or readiness  

---

## OWNER ACTIONS

1. Run the PowerShell sequence; keep the Windows JSON  
2. Telegram bot token + G11 E2E  
3. Optional n8n operational (G12)  
4. After unlock: pre-soak; wait real T+72h for outcomes  
5. Decide PR #19 merge (agents must not merge)  
6. CI workflow permissions if needed  

**Do not invent Windows PASS commits.**

---

## Pointers

- Protocol: `docs\OPERATOR_VALIDATION_PROTOCOL.md`  
- Runner: `scripts\operator_validation_gate.py`  
- Pre-soak: `docs\PRE_SOAK_PROTOCOL.md`  
- Snapshot: `docs\CURRENT_TRUTH_SNAPSHOT.md`  
- Quickstart: `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`  
