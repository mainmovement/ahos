# AHOS — Owner Action Required

**Date:** 2026-08-27 · Companions: `FINAL_TRUTH_AUDIT.md`, `NEXT_DEVELOPMENT_BACKLOG.md`

## Cursor / agent can do (and did)

- Code, tests, docs, Lane-A freeze, n8n JSON validation, typecheck
- Live provider probe **on agent host** + pipeline evidence accrual
- Narrative / market-structure / tokenomics / catalyst wiring
- PR updates on `cursor/ahos-cleanup-alignment-4bde`

## Owner must do

| ID | Action | Artifact proving done |
|----|--------|------------------------|
| OA-1 | Set `TELEGRAM_BOT_TOKEN` + allowlist | Live Telegram transcript |
| OA-2 | `npm run dev` + `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` | Reply `source=conversation_gateway` |
| OA-3 | On **Windows laptop**: `python -m architecture.runtime --probe-providers` | Probe JSON SUCCESS (may differ from agent host) |
| OA-4 | Keep daemon + observation until outcome labels exist; then `python scripts/calibration_report.py` | Report with eligible pairs > 0 |
| OA-5 | 168h soak per protocol | 7-day snapshot series |
| OA-6 | Nightly backups ×7 UTC dates | `series_complete=true` |
| OA-7 | Optional CI `workflows` permission | Green Actions run |
| OA-8 | Human review + merge PR #19 | `main` contains integration commits |

**Not required:** exchange trade keys, paid social scrape, declaring PRODUCTION_READY.
