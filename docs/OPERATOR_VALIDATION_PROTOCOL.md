# Operator Validation Protocol (Windows-first)

**Purpose:** Prove AHOS on the **owner's Windows 10/11 host** before any soak.

**Current product claim (do not invent):**

| Claim | Status |
|-------|--------|
| Integration (agent-host) | `INTEGRATION_READY` |
| Operator (Windows) | **`OPERATOR_READY = NOT_VERIFIED`** |
| Pre-soak | **blocked** until Windows **G1–G10** all PASS (`summary.pre_soak_entry_ok`) |

Canonical handoff: `docs/WINDOWS_OPERATOR_HANDOFF.md`.

---

## Prerequisites (Windows PowerShell)

| Tool | Check command | Required |
|------|---------------|----------|
| Python 3.11+ | `python --version` | Yes |
| Node.js LTS | `node --version` | Yes (G1/G2) |
| npm | `npm --version` | Yes (G1/G2) |
| Git | `git --version` | Yes |
| Postgres + `DATABASE_URL` | One-Brain `/api/chat` | Yes for G2 PASS |
| Network HTTPS | DexScreener / GeckoTerminal | Yes for G3 |

**Environment:**

```powershell
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"
# Also set AHOS_WEB_API_TOKEN (+ NEXT_PUBLIC_…) in .env — see windows_ensure_web_api_token.ps1
```

Canonical SQLite stores (under `.\data\` after `init_databases.py`):

- `e01_discovery.sqlite`
- `paper_trading.sqlite`
- `ahos_local.sqlite`
- `ahos_knowledge.sqlite`

Do **not** set `AHOS_DB_PATH=.\data\ahos.db` (non-canonical / ignored).

---

## Exact PowerShell sequence

### Step 0 — Identity

```powershell
cd <PATH_TO_AHOS_REPO>
Get-Location
git rev-parse --short HEAD
git status -sb
python --version
node --version
npm --version
```

### Step 1 — Python environment (no `pip install -e .`)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### Step 2 — Bootstrap databases

```powershell
python scripts\init_databases.py --with-guards
```

### Step 3 — Seed evidence

```powershell
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
python -m architecture.runtime --single-cycle --evidence-source local --limit 5
python scripts\prediction_lifecycle_status.py
```

### Step 4 — Gateway (Terminal A)

Set in `.env`: `DATABASE_URL=...`, `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat`, and matching `AHOS_WEB_API_TOKEN` / `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` (or run `scripts\windows_ensure_web_api_token.ps1`).

```powershell
npm install
npm run dev
```

### Step 5 — Gate runner (Terminal B)

```powershell
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3000/api/chat"

python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

Exit codes: `0` = no FAIL and (on Windows) `operator_ready`; `1` = fatal; `2` = FAIL present; `3` = Windows incomplete (`operator_ready` false).

Artifact: `reports\operator_validation_report_windows_<stamp>.json`

### Step 6 — Telegram G11 (owner)

Archive transcript, then:

```powershell
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill --telegram-e2e-artifact reports\telegram_e2e_<UTC>.md
```

---

## Gate map (matches runner)

| Gate | PASS requires | Non-PASS |
|------|---------------|----------|
| G1 Environment | Py≥3.11, architecture import, writable data, node+npm | missing node/npm → BLOCKED |
| G2 Gateway | Live POST chat URL; HTTP &lt;500 (incl. 4xx) | refused → FAIL; 5xx → FAIL (often DATABASE_URL) |
| G3 Providers | `--probe-providers` live SUCCESS tokens&gt;0 | else FAIL / NOT_VERIFIED |
| G4 Evidence | observations &gt; 0 | FAIL |
| G5 Scoring | local_predictions &gt; 0 | FAIL |
| G6 Security | assert_safe_environment | FAIL |
| G7 Lane-A | freeze verify clean | FAIL |
| G8 Lifecycle | observation_state total &gt; 0 | FAIL |
| G9 Observation | discovery_observations &gt; 0; labels may be 0 | FAIL if obs=0 |
| G10 Restart | `--backup-drill` exit 0 | FAIL/BLOCKED |
| G11 Telegram | token + `--telegram-e2e-artifact` | OWNER_ACTION / NOT_VERIFIED |
| G12 n8n | validate_n8n structural | STRUCTURAL_VALID ≠ operational |

`pre_soak_entry_ok` = Windows ∧ G1–G10 PASS.  
`operator_ready` = Windows ∧ G1–G11 PASS ∧ G12 structural/PASS.

---

## Related

- `docs/WINDOWS_OPERATOR_HANDOFF.md`
- `docs/PRE_SOAK_PROTOCOL.md`
- `docs/CURRENT_TRUTH_SNAPSHOT.md`
