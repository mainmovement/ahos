# W45 — Telegram + Conversational Intelligence Upgrade

**Date:** 2026-08-21  
**Repo:** `mainmovement/ahos` @ main  
**Rule:** Evidence > Claim · UNKNOWN > Fabricated · Paper-only

---

## 1. Pre-W45 baseline

| Area | Status before W45 |
|------|-------------------|
| Next.js Command Center | Present (`CommandCenter.tsx`, cinematic CSS) |
| Continuous engine | Present (`engine.ts` start → 70s cycles → stop) |
| Web chat intents | Present (`chat.ts` rule-based Persian) |
| Python Telegram domain | Present (`telegram_ai/*`, `scripts/run_sun_sniper_bot.py`) |
| Pump alert (Python) | Present (`telegram_ai/pump_alert.py`) |
| Web alert API | Thin reader of `reports/pump_alert_state.json` |
| TS cycle → Telegram alert | **Not wired** |
| Chat focus / “این توکن” | Partial (symbol match only) |

---

## 2. What changed in W45

### IMPLEMENTED (code on GitHub)

1. **`alerts.ts`** — Shared Node alert engine:
   - Gates: WATCH + rankScore ≥ 0.72 + security not honeypot + liquidity floor + anti-paid-boost
   - Cooldown per token (default 900s)
   - Writes `reports/pump_alert_state.json` with full payload for web
   - Optional Telegram `sendMessage` only if `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALLOWED_CHAT_IDS` in **environment** (never in repo)

2. **`engine.ts`** — After ranking each cycle calls `processOpportunityAlerts(ranked)`; cycle notes include alert counts; alert failures cannot fail the cycle.

3. **`app/api/chat/route.ts`** — Accepts `history` + `focusToken` for conversational continuity.

4. **`app/api/alerts/route.ts`** — Returns `payload`, 3-minute hot window, disclaimer.

5. **Security path** — `.env.example` already documents empty `TELEGRAM_BOT_TOKEN=`; no real token committed in W45 commits.

6. **Prior session** — Full cinematic `CommandCenter.tsx` restored + performance pass (memo, abortable poll, visibility pause).

### TESTED (this environment)

| Test | Result | Evidence |
|------|--------|----------|
| Telegram `getMe` with previously shared token | **FAIL 401 Unauthorized** | Live HTTP to `api.telegram.org` |
| Telegram `getWebhookInfo` | **FAIL 401** | Same |
| Token committed to git in W45 | **No** | File writes inspected; token only used in ephemeral shell |
| Alert module unit logic | Static review OK | Gates match scoring anti-hype |
| Full Next.js cycle with DB | **Not run here** | No `DATABASE_URL` / Postgres in this agent sandbox |
| Live Telegram conversational round-trip | **Not run** | Blocked by 401 |

### BLOCKED

1. **Telegram live bot** — Credential returned **401 Unauthorized**. Token is revoked, rotated, or invalid. Operator must:
   - Open @BotFather → issue **new** token for `@sun_sniperbot`
   - Put only in local `.env` as `TELEGRAM_BOT_TOKEN=`
   - Set `TELEGRAM_ALLOWED_CHAT_IDS`
   - Run `python scripts/run_sun_sniper_bot.py`
   - Optional: `ALL_PROXY` if Telegram is filtered

2. **End-to-end web + DB soak** — Requires operator `DATABASE_URL` and `npm run dev` on a machine with network to free market APIs.

3. **Agent cannot persist secrets** into GitHub Actions / Vercel secrets from this session — operator must set them in hosting UI.

### UNKNOWN

- Whether operator still controls chat id for allow-list
- Whether Iran network filter blocks Telegram from operator machine (use `ALL_PROXY`)
- Live DexScreener/Gecko health at operator runtime (providers are independent; failures → UNKNOWN, not fabricated scores)

---

## 3. Subsystem status

### Telegram

| Item | Status |
|------|--------|
| Architecture (poll runner + domain service) | IMPLEMENTED (Python) |
| Secure config (env only) | IMPLEMENTED |
| Live connection with provided token | **BLOCKED (401)** |
| Conversational intents (Persian) | IMPLEMENTED in `telegram_ai` |
| Unified core with Next chat | **Partial** — Python path uses discovery SQLite; Next path uses Postgres snapshot. Same *policies*, not one process |

### Web Chat

| Item | Status |
|------|--------|
| Natural Persian intents | IMPLEMENTED |
| Evidence / UNKNOWN language | IMPLEMENTED |
| API history + focusToken | IMPLEMENTED |
| Client sending history/focus | **Partial** — API ready; CommandCenter can pass history in a follow-up UI patch |
| LLM backend | Not claimed — rule engine + snapshot evidence |

### Alert Engine

| Item | Status |
|------|--------|
| TS cycle emission | IMPLEMENTED |
| Web state file | IMPLEMENTED |
| Telegram push from Node | IMPLEMENTED (env-gated) |
| Loud web banner + sound | CSS/API ready; UI already has alarm banner for system errors — critical opportunity banner uses `/api/alerts` |
| Anti-FOMO copy | IMPLEMENTED in payload disclaimer |

### Opportunity Engine

| Item | Status |
|------|--------|
| Multi-factor scoring + anti-hype | Already strong in `scoring.ts` |
| Parallel security | Already in `engine.ts` |
| Continuous daemon | Already |

---

## 4. Operator checklist (real activation)

```bash
cp .env.example .env
# set DATABASE_URL, TELEGRAM_BOT_TOKEN (NEW from BotFather), TELEGRAM_ALLOWED_CHAT_IDS
npm install && npm run dev          # web command center
python scripts/run_sun_sniper_bot.py  # Telegram edge
```

Never commit `.env`.

If the old token was posted in chat: **revoke it** even though it already returns 401.

---

## 5. Final honesty matrix

| Claim | Classification |
|-------|----------------|
| Alert code path in engine | **IMPLEMENTED** |
| Telegram code path | **IMPLEMENTED** |
| Telegram LIVE with shared token | **BLOCKED** |
| Web chat conversational API | **IMPLEMENTED** |
| Full production soak | **BLOCKED** (env) |
| Awwwards #1 site complete | **NOT CLAIMED** — cinematic shell present; not a competition submission |
| Real trading | **DISABLED** by design |

---

*End of W45 report.*
