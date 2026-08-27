# AHOS — Owner Action Required

**Date:** 2026-08-27  
**Phase:** OPERATOR VALIDATION & EVIDENCE ACCRUAL

## Agent completed

- `docs/CURRENT_TRUTH_SNAPSHOT.md`
- `docs/OPERATOR_VALIDATION_PROTOCOL.md` + gate runner
- Agent-host gate report (honest; not Windows)
- `docs/PRE_SOAK_PROTOCOL.md`
- Calibration lifecycle already bridged (await T+72h)

## Owner must do (in order)

| ID | Action | Command / artifact |
|----|--------|---------------------|
| OA-W1 | Run operator gates on **Windows** | `python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill --json-out reports\operator_validation_report.json` |
| OA-W2 | Start One-Brain for G2 | `npm run dev` then re-run gate script |
| OA-3 | Confirm Windows provider SUCCESS | probe JSON → `OPERATOR_WINDOWS_VERIFIED` |
| OA-PS | Run PRE_SOAK (≥2h) | `docs/PRE_SOAK_PROTOCOL.md` → `reports/pre_soak_*` |
| OA-4 | After PRE_SOAK PASS: ≥72h daemon | `--observation-cycle --evidence-source local` → calibration_report |
| OA-1/2 | Telegram live E2E | `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md` |
| OA-n8n | Optional n8n operational | `docs/N8N_OPERATIONAL_PROCEDURE.md` |
| OA-8 | Merge PR #19 when ready | human merge |

**Do not claim OPERATOR_READY until OA-W1…OA-W2 (+ G11) produce PASS artifacts.**
