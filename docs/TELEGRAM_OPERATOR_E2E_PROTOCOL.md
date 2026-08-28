# Telegram Operator E2E Protocol (Windows)

**Status:** OWNER_ACTION_REQUIRED for live execution  
**Unit/gateway tests:** TEST_VERIFIED (W57 gateway-only)  
**Live BotFather E2E:** NOT_VERIFIED until this protocol is completed

## Preconditions

1. Copy `.env.example` → `.env`
2. Set `TELEGRAM_BOT_TOKEN` from BotFather
3. Set `TELEGRAM_ALLOWED_CHAT_IDS` to your chat id (empty allowlist is LOCKED unless `AHOS_TELEGRAM_ALLOW_OPEN_ACCESS=1`)
4. Set matching `AHOS_WEB_API_TOKEN` and `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` (or run `scripts\windows_ensure_web_api_token.ps1`)
5. Start One-Brain: `npm run dev` (binds `127.0.0.1`)
6. Set `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat`
7. Start Telegram domain service / bot per `docs/WINDOWS_OPERATOR_HANDOFF.md`
8. After live checks, attest G11 via gate:

```powershell
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill --telegram-e2e-artifact reports\telegram_e2e_<UTC>.md
```

## Exact checks

| # | Action | Expected |
|---|--------|----------|
| 1 | Send a Persian greeting | Reply exists; **not** an independent score when gateway down |
| 2 | Stop `npm run dev`; send message | `EMERGENCY_FALLBACK_ONLY` / gateway unavailable honesty |
| 3 | Restart gateway; ask «فرصت‌های جدید چیست؟» | Reply `source=conversation_gateway` (or equivalent provenance) |
| 4 | Ask «ریسک آن چیست؟» for a known symbol | Risk/unknowns from canonical evidence — no fabricated prices |
| 5 | Ask about a honeypot/rejected token if available | Security veto language present; opportunity not sold over veto |

## Artifact to archive

Save the chat transcript under `reports/telegram_e2e_<UTC>.md` (redact token).

Until archived: **Telegram live E2E = NOT_VERIFIED**.
