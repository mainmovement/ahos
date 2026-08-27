# AHOS — Owner Action Required

**Date:** 2026-08-27  
**Phase:** WINDOWS OPERATOR VALIDATION  
**Classification:** `INTEGRATION_READY` (agent-host) · **`OPERATOR_READY = NOT_VERIFIED`**  
**Merge:** human decision only — see `docs/MERGE_READINESS_AUDIT.md`

## Agent completed (transfer control)

- Environment contract: documented `AHOS_PAPER_ONLY` + clarified required keys in `.env.example`
- Merge readiness audit document
- Reconfirmed Lane-A freeze; no frozen sources changed vs `main`
- **Did not** invent Windows PASS, merge PR #19, or add speculative features

## Owner must do (post-merge / transfer)

| ID | Action | Evidence |
|----|--------|----------|
| OA-MERGE | Human merge PR #19 when MERGE_READY | GitHub |
| OA-H | Follow `docs/WINDOWS_OPERATOR_HANDOFF.md` on Windows | — |
| OA-PG | Postgres + `DATABASE_URL` | G2 |
| OA-W1 | Windows operator gate | `reports\operator_validation_report_windows_*.json` |
| OA-PS | PRE_SOAK if `pre_soak_entry_ok` | protocol |
| OA-4 | Real T+72h | calibration |
| OA-TG | Telegram E2E | G11 |
| OA-LA | Optional Lane-A URI fix + freeze re-anchor | governance |

**Do not claim `OPERATOR_READY` until Windows G1–G11 PASS artifacts exist.**

