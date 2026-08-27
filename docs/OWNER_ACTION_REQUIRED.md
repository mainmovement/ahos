# AHOS — Owner Action Required

**Date:** 2026-08-27 · **Companion:** `docs/NEXT_DEVELOPMENT_BACKLOG.md`, `docs/FINAL_TRUTH_AUDIT.md`

## Cursor / agent can do (no owner secrets)

- Code, tests, docs, Lane-A freeze checks, n8n JSON validation, typecheck, offline provider/security/scoring tests
- PR preparation on `cursor/ahos-cleanup-alignment-4bde`
- Architecture reconciliation without live credentials

## Owner must do (cannot be simulated)

| ID | Action | Artifact proving done |
|----|--------|------------------------|
| OA-1 | Set `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALLOWED_CHAT_IDS` in local `.env` | Live Telegram transcript |
| OA-2 | Run `npm run dev` and set `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` | Reply `source=conversation_gateway` |
| OA-3 | On a host with egress: `python -m architecture.runtime --probe-providers` | Probe JSON with SUCCESS + tokens>0 |
| OA-4 | Daemon with `AHOS_EVIDENCE_SOURCE=local`; then `python scripts/calibration_report.py` | Calibration report with real `local` pairs |
| OA-5 | 168h soak per `AHOS_LOCAL_SOAK_PROTOCOL.md` | Snapshots across 7 distinct days |
| OA-6 | `python scripts/sqlite_backup_restore.py nightly` × 7 UTC dates | `series_complete=true` |
| OA-7 | Optional: GitHub App `workflows` permission + copy CI template | Green Actions run |
| OA-8 | Human review + merge PR #19 | `main` contains handoff commits |

**Not required:** exchange trade keys, paid social scrape, declaring PRODUCTION_READY before OA-3…OA-5.
