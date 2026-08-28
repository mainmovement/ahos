# Windows DB STATE B — post-PR#30 ops wave: Lane-B web API auth

**Date:** 2026-08-28  
**Branch intent:** `cursor/post-state-b-ops-wave-4bde`  
**Classification:** engineering harden — **NOT OPERATOR_READY** · **MIGRATION still BLOCKED (STATE B)**

## Problem

Telegram allowlist does not protect direct HTTP to Next `:3000`. Unauthenticated `/api/engine|paper|watch|chat|command|metrics|alerts` was a CRITICAL control-plane gap.

## Change

| Surface | Behavior |
|---------|----------|
| `web_api_auth.ts` | Fail-closed gate: LOCKED / OPEN_ACCESS / RESTRICTED |
| All `app/api/*/route.ts` | `authorizeWebApi` + `sanitizePublicError` |
| `CommandCenter.tsx` | `webApiFetch` sends `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` |
| `telegram_ai/service.py` | Sends `Authorization: Bearer` from `AHOS_WEB_API_TOKEN` |
| `package.json` | `next dev/start --hostname 127.0.0.1` |

## Owner Windows (one card)

After merge to `main` on `G:\robat\ahos`:

1. `git pull`
2. In `.env` set the **same** random string for:
   - `AHOS_WEB_API_TOKEN=`
   - `NEXT_PUBLIC_AHOS_WEB_API_TOKEN=`
3. Keep `AHOS_WEB_API_ALLOW_OPEN_ACCESS=0`
4. Restart Next (`npm run dev`) and Telegram bot
5. **Do not** run `db:migrate` / `db:push` (STATE B)

Still: MERGE ≠ OPERATOR_READY. Run Windows operator gate when ready.
