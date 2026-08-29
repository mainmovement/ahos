# AHOS — Owner Action Required

**Date:** 2026-08-29  
**Phase:** WINDOWS PRE_SOAK ENTRY (PAPER_ONLY)  
**Classification:** `INTEGRATION_READY` · **`OPERATOR_READY = NOT_VERIFIED`** · **`PRE_SOAK` not entered**  
**STATE B:** never `db:migrate` / `db:push` without Cursor classification.

## Current blocker (authoritative)

Last Windows paste `20260828_220318` (`cursor/windows-gate-evidence-4bde` @ `988edcd`):

- G1 PASS, **G2 BLOCKED** (empty `AHOS_GATEWAY_URL`), G3–G10 PASS
- `pre_soak_entry_ok=false` · `operator_ready=false`
- Paste head was **before** empty-gateway merge #45 — main already defaults empty gateway

Unlock tip: **PR #58** (`cursor/windows-main-evidence-push-4bde`). Keep paste-sink **PR #56 OPEN** (do not merge #56).

## Do this on the Windows laptop (`G:\robat\ahos`)

```bat
cd /d G:\robat\ahos
curl.exe -L -o AHOS_RUN_TIP.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.cmd
AHOS_RUN_TIP.cmd
```

Then paste `reports\OWNER_PASTE_WINDOWS_GATE.txt` to **PR #56** or **#38**  
(or Desktop `AHOS_PASTE_TO_CURSOR.txt`).

**Please merge PR #58.** PRE_SOAK only if `pre_soak_entry_ok=true` (G1–G10). Do not invent READY.

Also see: `OWNER_ONE_LINER.txt` · `RUN_ME_WINDOWS.txt` · `WINDOWS_RUN_THIS_FIRST.txt` · `reports/OWNER_CARD_WEB_API_AUTH_PRE_SOAK_FA.md`

## Owner checklist

| ID | Action | Evidence |
|----|--------|----------|
| OA-58 | Merge unlock PR #58 | GitHub |
| OA-RUN | Run `AHOS_RUN_TIP.cmd` on Windows | console + OWNER_PASTE |
| OA-PASTE | Comment OWNER_PASTE on #56 (leave open) or #38 | GitHub |
| OA-PS | PRE_SOAK only if `pre_soak_entry_ok=true` | `docs/PRE_SOAK_PROTOCOL.md` |
| OA-TG | Telegram E2E (G11) for OPERATOR_READY only | G11 |
| OA-4 | Real T+72h calibration later | calibration |

**Do not claim `OPERATOR_READY` until Windows G1–G11 PASS artifacts exist.**  
**Do not claim `PRE_SOAK` until Windows-attested G1–G10 PASS (`pre_soak_entry_ok=true`).**
