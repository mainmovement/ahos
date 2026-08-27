# AHOS — Owner Action Required

**Date:** 2026-08-27  
**Phase:** WINDOWS OPERATOR VALIDATION (handoff ready)  
**Classification:** `INTEGRATION_READY` (agent-host) · **`OPERATOR_READY = NOT_VERIFIED`**

## Agent completed (this pass)

- Hardened `scripts/operator_validation_gate.py` (Windows paths, exit codes, no fake PASS)
- `docs/OPERATOR_VALIDATION_PROTOCOL.md` — copy/paste-safe PowerShell
- `docs/PRE_SOAK_PROTOCOL.md` — entry only after Windows G1–G10
- `docs/WINDOWS_OPERATOR_HANDOFF.md` — single operator handoff
- Removed/gitignored `reports/_scratch/`
- **Did not** invent Windows run results or merge PR #19

## Owner must do (in order)

| ID | Action | Command / artifact |
|----|--------|---------------------|
| OA-H | Read handoff | `docs/WINDOWS_OPERATOR_HANDOFF.md` |
| OA-W0 | Start One-Brain for G2 | `npm run dev` (port 3000) |
| OA-W1 | Run operator gates on **Windows** | `python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill` → `reports\operator_validation_report_windows_*.json` |
| OA-W2 | Confirm `pre_soak_entry_ok` | G1–G10 PASS in that JSON |
| OA-PS | Run PRE_SOAK only after unlock | `docs/PRE_SOAK_PROTOCOL.md` |
| OA-4 | After pre-soak: real T+72h | `python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local` |
| OA-1/2 | Telegram live E2E (G11) | `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md` — required for `OPERATOR_READY` |
| OA-n8n | Optional n8n operational | `docs/N8N_OPERATIONAL_PROCEDURE.md` |
| OA-8 | Merge PR #19 when ready | human merge only |

**Do not claim `OPERATOR_READY` until Windows G1–G11 PASS artifacts exist.**  
**Do not start PRE_SOAK until `summary.pre_soak_entry_ok` is true on a Windows report.**
