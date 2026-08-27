# AHOS — Owner Action Required

**Date:** 2026-08-27  
**Purpose:** Single checklist of actions that **only the project owner** can complete.  
**Engineering status:** Core local engineering is complete enough for `DEVELOPMENT_READY` (see `docs/FINAL_TRUTH_AUDIT.md`).  
**These boxes are NOT simulated and are NOT claimed PASS.**

| ID | Action | Why | Exact command / step | Acceptance evidence |
|----|--------|-----|----------------------|---------------------|
| OA-1 | Provide Telegram bot token + allowed chat ids | Live Telegram E2E (M-GAP-009) | Copy `.env.example` → `.env`; set `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_CHAT_IDS` | Live transcript archived |
| OA-2 | Point Telegram at Conversation Gateway | W57 One-Brain path | Start `npm run dev`; set `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` | Telegram reply `source=conversation_gateway` |
| OA-3 | Run provider probe on a host with egress | Live SUCCESS path (M-GAP-007) | `python -m architecture.runtime --probe-providers` | Committed probe artifact with `SUCCESS` + tokens>0 |
| OA-4 | Accrue local evidence + calibration | Measurement (M-GAP-008) | Daemon with `AHOS_EVIDENCE_SOURCE=local`; then `python scripts/calibration_report.py` | Report with real `local` pairs (not INSUFFICIENT_DATA only) |
| OA-5 | Execute 168h laptop soak | Reliability (M-GAP-003) | Follow `AHOS_LOCAL_SOAK_PROTOCOL.md` / `AHOS_SOAK_OPERATOR_START.md` | Snapshots every 6h for 7 distinct days |
| OA-6 | Nightly backups × 7 distinct UTC dates | Persistence (M-GAP-010 residual) | `python scripts/sqlite_backup_restore.py nightly` | `reports/nightly_backup_series.json` `series_complete=true` |
| OA-7 | Optional CI workflows permission | M-GAP-004 | Grant GitHub App `workflows`; copy `deployment/github-actions-ci.yml.template` → `.github/workflows/ci.yml` | Green CI on PR |
| OA-8 | Review + merge PR #19 | Release into next phase | Human review of matrix/audit; merge when satisfied | `main` contains alignment commits |

## Explicitly NOT required for AHOS

- Exchange TRADE-ONLY / withdrawal API keys — **no live execution surface**
- Paid social scrape (X/IG/TikTok) — OUT_OF_POLICY / COST_BLOCKED
- Claiming `PRODUCTION_READY` before OA-3…OA-5 evidence exists

## Pointers

- Gaps: `AHOS_GAP_REGISTER.md`
- Matrix: `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`
- Truth audit: `docs/FINAL_TRUTH_AUDIT.md`
- Soak start: `AHOS_SOAK_OPERATOR_START.md`
