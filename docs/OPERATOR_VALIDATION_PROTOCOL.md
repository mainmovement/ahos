# AHOS — Operator Validation Protocol

**Canonical:** yes  
**Audience:** Windows laptop operator + agent assisting preparation  
**Classification impact:** only PASS on all required gates (with artifacts) can support `OPERATOR_READY`  
**Law:** NO CLAIM WITHOUT ARTIFACT.

Related: `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`, `docs/CALIBRATION_LIFECYCLE.md`, `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md`, `docs/N8N_OPERATIONAL_PROCEDURE.md`, `docs/PRE_SOAK_PROTOCOL.md`.

---

## How to run

From repo root in **PowerShell** (Windows) or bash (agent-host partial):

```powershell
# Windows
.\.venv\Scripts\Activate.ps1
$env:AHOS_EVIDENCE_SOURCE = "local"
python scripts\operator_validation_gate.py --platform windows --json-out reports\operator_validation_report.json

# Agent host (partial — never claims OPERATOR_READY)
python scripts/operator_validation_gate.py --platform agent-host --json-out reports/operator_validation_report_agent_host.json
```

The script writes machine-readable results. Humans may also fill `docs/OPERATOR_VALIDATION_REPORT.md` from that JSON.

Gate verdicts: `PASS` | `FAIL` | `BLOCKED` | `NOT_VERIFIED` | `OWNER_ACTION_REQUIRED`

---

## Prerequisites

1. Clone/pull AHOS on the operator Windows machine
2. Python 3.11+ with `.venv` (`pip install -r requirements.txt` or project install script)
3. Node/npm for One-Brain (`npm install`)
4. `.env` from `.env.example` (no secrets committed)
5. For G3/G5 live discovery: working egress (proxy if Iran-filtered)
6. For G11 live: BotFather token (never commit)
7. For G12 operational: n8n instance + credentials

---

## Gates

### G1 — Environment

| | |
|--|--|
| Goal | Python, Node, paths, venv, SQLite writable |
| Commands | `python --version`; `npm --version`; `python scripts\operator_validation_gate.py` (G1 section) |
| PASS | Interpreter OK; project importable; data/ writable |
| Artifact | report JSON `gates.G1` |

### G2 — Gateway (One-Brain)

| | |
|--|--|
| Goal | `npm run dev` serves chat API |
| Commands | `npm run dev`; then `curl http://127.0.0.1:3000/api/chat` or script probe |
| PASS | HTTP response from `/api/chat` (not connection refused) |
| BLOCKED | Node not installed / port busy |
| Artifact | response status + body snippet (no secrets) |

### G3 — Discovery (providers)

| | |
|--|--|
| Goal | Real provider SUCCESS with tokens>0 |
| Commands | `python -m architecture.runtime --probe-providers` |
| PASS | ≥1 discovery provider `SUCCESS` and `token_count>0` |
| Artifact | `reports/provider_probe_*.json` |
| Note | Agent-host SUCCESS ≠ Windows SUCCESS — record platform |

### G4 — Evidence persistence

| | |
|--|--|
| Goal | Observations land in discovery DB |
| Commands | After a collect/cycle: `python scripts\prediction_lifecycle_status.py` |
| PASS | `discovery_observations > 0` or `production_observations > 0` |
| Artifact | lifecycle_status JSON |

### G5 — Scoring pipeline

| | |
|--|--|
| Goal | Candidates scored and optionally ledgered |
| Commands | `python -m architecture.runtime --single-cycle --evidence-source local --limit 5` |
| PASS | Log shows `scores=` > 0; if local source, ledger rows increase |
| Artifact | runtime log excerpt + ledger census |

### G6 — Security veto authority

| | |
|--|--|
| Goal | Critical security overrides opportunity enthusiasm |
| Commands | Gate script runs offline invariant tests / hygiene assert |
| PASS | `assert_safe_environment` OK; PAPER_ONLY; veto tests green |
| Artifact | pytest subset or script G6 block |

### G7 — Lane separation

| | |
|--|--|
| Goal | Lane-A freeze intact; bridge only calls frozen APIs |
| Commands | `python scripts\freeze_lane_a.py` |
| PASS | Lane-A integrity OK |
| FAIL | drift/missing freeze files |
| Artifact | freeze stdout |

### G8 — Prediction lifecycle registration

| | |
|--|--|
| Goal | Scored candidates enter `observation_state` |
| Commands | After cycle: lifecycle_status; or backfill once |
| PASS | `observation_state` counts > 0 |
| Artifact | lifecycle_status JSON |

### G9 — Observation lifecycle

| | |
|--|--|
| Goal | `discovery_observations` grow; no fabricated outcomes |
| Commands | lifecycle_status before/after `--observation-cycle` |
| PASS | observations ≥ prior; `outcome_labels` only increase via materialize after RESOLVED |
| Artifact | before/after JSON |

### G10 — Restart / recovery

| | |
|--|--|
| Goal | Stop/start daemon without corrupt DBs |
| Commands | Run cycle → stop → `python scripts\sqlite_backup_restore.py drill` → restart cycle |
| PASS | integrity_check ok; no crash; ledger append-only behavior preserved |
| Artifact | drill JSON + second cycle log |

### G11 — Telegram gateway honesty

| | |
|--|--|
| Goal | W57 gateway-only; live E2E only with token |
| Unit PASS | existing Telegram unit tests |
| Live | Follow `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md` |
| Without token | `OWNER_ACTION_REQUIRED` — never PASS live |

### G12 — n8n

| | |
|--|--|
| STRUCTURAL_VALID | `python tests\validate_n8n.py` |
| IMPORT_VALID / OPERATIONAL_VALID | Owner n8n import+execute per `docs/N8N_OPERATIONAL_PROCEDURE.md` |
| Without n8n | STRUCTURAL only; OPERATIONAL = `OWNER_ACTION_REQUIRED` |

---

## OPERATOR_READY promotion rule

Promote **only** when artifacts show:

| Gate | Required for OPERATOR_READY |
|------|-----------------------------|
| G1 | PASS on **Windows** |
| G2 | PASS on **Windows** |
| G3 | PASS on **Windows** (`OPERATOR_WINDOWS_VERIFIED`) |
| G4–G5 | PASS on Windows |
| G6–G7 | PASS |
| G8–G9 | PASS (observation_state + discovery_observations > 0) |
| G10 | PASS on Windows |
| G11 | Live PASS **or** explicit deferral documented (not silent) |
| G12 | STRUCTURAL_VALID minimum; OPERATIONAL optional for this gate |

Telegram live may remain OWNER_ACTION if deferred, but then classification note must say:

`OPERATOR_READY_CORE` / or stay `INTEGRATION_READY` until G11 live — **this project requires Persian Telegram as primary UX**, so **OPERATOR_READY requires G11 live PASS**.

Calibration pairs and 72h soak are **not** required for OPERATOR_READY but are required for PRODUCTION_CANDIDATE.

---

## Failure / recovery

| Failure | Recovery |
|---------|----------|
| G3 TLS/timeout | Configure `ALL_PROXY` / `HTTPS_PROXY`; re-probe |
| G2 port in use | Stop other Node; change port and `AHOS_GATEWAY_URL` |
| G8 empty | `python scripts\backfill_lane_a_from_production.py` then cycle |
| G10 corrupt DB | Restore from backup; do not invent rows |
| Secrets in tree | Rotate; never commit `.env` |

---

## Evidence locations

| Artifact | Path |
|----------|------|
| Gate report JSON | `reports/operator_validation_report.json` |
| Provider probe | `reports/provider_probe_*.json` |
| Lifecycle | `reports/` or stdout from status script |
| Calibration | `reports/calibration_*.json` |
| Pre-soak | `reports/pre_soak_*.json` |
| Human summary | `docs/OPERATOR_VALIDATION_REPORT.md` |
