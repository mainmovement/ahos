# Pre-Soak Protocol

**Entry condition (hard):** Windows Operator Validation **G1–G10** must PASS first.

Do **not** start when:

- Only agent-host `INTEGRATION_READY` exists
- `OPERATOR_READY` is being assumed without Windows JSON
- Gate JSON missing, or `platform_effective` ≠ `windows`
- `summary.pre_soak_entry_ok` ≠ `true`
- Any of G1–G10 is FAIL / BLOCKED / NOT_VERIFIED on Windows

**Unlock checklist:**

| Check | Evidence |
|-------|----------|
| Operator protocol run on Windows | `docs/OPERATOR_VALIDATION_PROTOCOL.md` |
| Artifact present | `reports/operator_validation_report_windows_*.json` |
| `summary.pre_soak_entry_ok` | `true` |
| G11 Telegram | May still be OWNER_ACTION_REQUIRED for **short** pre-soak |
| G12 n8n | STRUCTURAL_VALID allowed; operational not required for entry |

Full claim **`OPERATOR_READY`** still requires G11 PASS. Short pre-soak must not be labeled OPERATOR_READY.

Until unlock: **STOP**.

---

## Purpose

Controlled soak on the **Windows operator host** after G1–G10 PASS — stability before longer observation (T+72h).

---

## Pre-soak commands (PowerShell, after unlock)

```powershell
cd <PATH_TO_AHOS_REPO>
.\.venv\Scripts\Activate.ps1
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"

python -m architecture.runtime --single-cycle --evidence-source local --limit 5
python scripts\prediction_lifecycle_status.py
python -m architecture.runtime --observation-cycle --evidence-source local
```

Record wall-clock **T0** when Windows soak predictions are registered. Outcomes require real elapsed time to T+72h.

Multi-hour:

```powershell
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local
```

---

## Stop conditions (abort immediately)

| Condition | Action |
|-----------|--------|
| PAPER_ONLY violated / live trading flags | STOP |
| Lane A freeze verify FAIL | STOP |
| DB corruption / backup restore fail | STOP |
| Provider outage hidden by mocks | STOP |
| Security veto bypassed | STOP |
| Gateway required but down | STOP or mark degraded |
| Fabricating outcome_labels | STOP |

---

## What pre-soak does **not** prove

- Full Telegram production (G11)
- n8n operational (G12)
- Calibration sufficiency (real T+72h labels)
- Agent-host success ≠ Windows soak success
- `OPERATOR_READY`

---

## Related

- Handoff: `docs/WINDOWS_OPERATOR_HANDOFF.md`
- Operator Validation: `docs/OPERATOR_VALIDATION_PROTOCOL.md`
- Calibration lifecycle: `docs/CALIBRATION_LIFECYCLE.md`
