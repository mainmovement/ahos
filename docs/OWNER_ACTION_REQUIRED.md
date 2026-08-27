# AHOS — Owner Action Required

**Date:** 2026-08-27  
**Phase:** WINDOWS OPERATOR VALIDATION  
**Classification:** `INTEGRATION_READY` (agent-host) · **`OPERATOR_READY = NOT_VERIFIED`**

## Agent completed

- Fixed Windows-blocking defects (SQLite RO URI helper, npm.cmd subprocess, G2 HTTPError, handoff commands)
- Documented Postgres `DATABASE_URL` for One-Brain G2
- Removed invalid `pip install -e .`; added `init_databases.py` to handoff
- G11 attestation via `--telegram-e2e-artifact`
- Reported remaining Lane-A frozen URI gap (not patched)
- **Did not** invent Windows PASS or merge PR #19

## Owner must do (in order)

| ID | Action | Evidence |
|----|--------|----------|
| OA-H | Follow `docs/WINDOWS_OPERATOR_HANDOFF.md` | — |
| OA-PG | Provide Postgres + `DATABASE_URL` in `.env` | G2 |
| OA-W0 | `npm run dev` | G2 |
| OA-W1 | `python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill` | `reports\operator_validation_report_windows_*.json` |
| OA-W2 | Confirm `pre_soak_entry_ok` | JSON |
| OA-PS | PRE_SOAK only after unlock | `docs/PRE_SOAK_PROTOCOL.md` |
| OA-4 | Real T+72h observation | lifecycle / calibration reports |
| OA-TG | Telegram E2E + `--telegram-e2e-artifact` | G11 / OPERATOR_READY |
| OA-n8n | Optional n8n operational | G12 |
| OA-LA | Decide whether to approve Lane-A URI fix + freeze re-anchor | Windows soak using Lane-A RO opens |
| OA-8 | Merge PR #19 | human only |

**Do not claim `OPERATOR_READY` until Windows G1–G11 PASS artifacts exist.**
