# AHOS — Owner Action Required

**Date:** 2026-08-27

## Agent completed (no secrets)

- Prediction→Lane-A observation bridge + backfill + status tools
- Calibration lifecycle documentation
- Telegram / n8n operator protocols (docs only)
- Windows quickstart lifecycle section

## Owner must do

| ID | Action | Artifact |
|----|--------|----------|
| OA-1 | Telegram BotFather token + allowlist | Live transcript |
| OA-2 | `AHOS_GATEWAY_URL` + `npm run dev` | gateway-sourced replies |
| OA-3 | Windows laptop `--probe-providers` | SUCCESS probe JSON |
| OA-4 | Daemon ≥72h with `--observation-cycle --evidence-source local`; then calibration_report | `joined_pairs > 0` (guards may still fail) |
| OA-4b | Optional: `python scripts\backfill_lane_a_from_production.py` once | lifecycle_status OBSERVING > 0 |
| OA-5 | 168h soak | 7-day snapshots |
| OA-6 | Nightly backups ×7 | series_complete |
| OA-7 | CI workflows permission | Green Actions |
| OA-8 | Merge PR #19 | main updated |

See also: `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md`, `docs/N8N_OPERATIONAL_PROCEDURE.md`, `docs/CALIBRATION_LIFECYCLE.md`.
