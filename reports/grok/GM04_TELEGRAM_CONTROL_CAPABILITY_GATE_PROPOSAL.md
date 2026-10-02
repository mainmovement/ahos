# GM-04 proposal: capability gate for chat/Telegram operational control

| Field | Value |
|---|---|
| Status | **DESIGN_ONLY**. No code has been written. Implementation waits for security review. |
| Reviewers requested | سپهر, قاسم, رضا (security review), then owner approval |
| Author / date | Grok, 2026-10-02 (Phase 2) |
| Scope | TS gateway route behaviour for the `start`, `stop` and `paper_buy` intents (`chat.ts`) when the request arrives through `/api/chat` |
| Out of scope | Canonical Decision Authority (unchanged; it still decides every paper_buy), Lane A, the hooks overlay, the Credential Manager, live trading (stays DISABLED) |

## 1. Current reality (read from code at 789dfa2)

- `app/api/chat/route.ts`:
  - `authorizeWebApi(req)` checks the shared bearer `AHOS_WEB_API_TOKEN`.
  - It then builds the payload, with `channel` and `user_id` taken **from the request body**. Both are client-asserted.
- `conversation_gateway.ts:24`: `handleChat(message, {focusToken, history})`. **`channel` and `user_id` are dropped**; `channel` only appears in `entities` in the response.
- `chat.ts` `detectIntent` (lines ~232-236):
  - `start` = `/(^|\s)(شروع|استارت|start|روشن)(\s|$)/` → `startEngine()` (`chat.ts:43-45`)
  - `stop` = `/(توقف|استاپ|stop|خاموش)/` → `stopEngine()` (`chat.ts:46-48`). **This has no word boundary**, so a casual message such as "stoploss چنده؟" or "...stop loss..." stops the engine.
  - `paper_buy` = `/(خریدم|خرید کاغذی|ثبت خرید|paper)/` → `addPaper` (still gated by the canonical decision and overlay; PAPER only)
- Telegram path:
  - `telegram_ai/bot.py` → `service.py` → POST `/api/chat` with `channel="telegram"`, and since GM-02 with a real `user_id`.
  - The bot's allowlist (`TELEGRAM_ALLOWED_CHAT_IDS`) is the only control-plane check before an engine start or stop.
  - There is no confirmation and no audit record of who started or stopped the engine.

## 2. Threats

| # | Threat | Today |
|---|---|---|
| T1 | An allowlisted chat member (or a compromised Telegram account) types a message containing "stop" or "start" | The engine starts or stops immediately. Not audited. |
| T2 | False-positive intent from substring match (`stop loss`, `paper trading چیه؟`) | Engine stopped, or a paper position attempted |
| T3 | Any holder of `AHOS_WEB_API_TOKEN` asserts `channel:"web"` to escape channel rules | Possible: channel comes from the body |
| T4 | Replayed Telegram update | Mitigated in the bot by GM-02 `ReplayGuard`. Not mitigated at `/api/chat` |
| T5 | No attribution | `stopEngine` records no principal |

## 3. Proposed design (for review; no code yet)

1. **Intent → capability map** (new pure module, e.g. `control_capability.ts`):
   - `start` → `ENGINE_CONTROL`
   - `stop` → `ENGINE_CONTROL`
   - `paper_buy` → `PAPER_WRITE`
   - every other intent → `READ`
2. **Default deny for control from remote channels.** Rule: `channel ∈ {telegram, api}` and capability ≠ READ → reply with a refusal plus the instruction "use the dashboard". No engine call is made.
3. **Channel is not trusted from the body (T3).** Two options for reviewers:
   - (a) separate bearer tokens per channel (`AHOS_WEB_API_TOKEN` for the web UI, `AHOS_TELEGRAM_GATEWAY_TOKEN` for the bot); the server derives the channel from which token matched; or
   - (b) keep one token, but treat *every* `/api/chat` call as remote for capability purposes, and keep ENGINE_CONTROL only on the dashboard's dedicated start/stop endpoints.

   Option (b) is the smaller change.
4. **Optional, later: an admin principal plus a confirmation nonce for Telegram.** This applies only if the owner wants remote control at all.
   - An `AHOS_TELEGRAM_ADMIN_USER_IDS` allowlist, separate from the chat allowlist, matched against the GM-02-propagated `user_id`, which is server-side verified only under option 3(a).
   - A two-step flow: `stop` → the server returns a one-time nonce (random, single-use, TTL 60 s, bound to user_id and intent) → `/confirm <nonce>` executes.
5. **Intent matching hardening (T2).**
   - `stop` and `start` use word boundaries plus an exact-command form (`/stop`, `توقف موتور`).
   - `stop loss` and `stoploss` are explicitly excluded.
   - This is pure regex, with negative tests.
6. **Audit (T5).** Append-only record for every control attempt:
   - fields: allowed or denied, intent, channel, hashed user_id, reason, ts
   - reuse the GM-02 `hash_identifier` convention
   - no raw text
7. **The canonical authority is untouched.** `paper_buy` still passes through `addPaper` → canonical decision → overlay. This gate only adds a *deny* in front of it and never upgrades anything.

## 4. Test plan (to be written first when approved)

- A selftest table of message → intent → capability, including the false positives `stop loss`, `stoploss`, `paper trading چیه`.
- `channel=telegram` plus start/stop/paper_buy → denied; `startEngine`/`stopEngine`/`addPaper` are never called (injected spies).
- `channel=web` start → allowed only under the chosen option 3 semantics.
- Nonce flow: single use, expiry, wrong user, wrong intent, replay.
- An audit row for every allowed and denied control attempt, with no raw text.
- Existing selftests unchanged: canonical-security, canonical-read-model, web-api-auth, alert-banner.

## 5. Rollout and rollback

- Code is behind no flag: default deny for remote control is the safe default. Rollback means reverting a single commit.
- It takes effect after the Next dev server hot-reloads. No DB migration is involved.
- OWNER_ACTION: decide whether Telegram should be able to control the engine at all. The recommendation is **no** (read-only Telegram).

## 6. Open questions for reviewers

1. Option 3(a) or 3(b)?
2. Is remote engine control wanted at all? If so, should the nonce be required?
3. Should `paper_buy` from Telegram be allowed, given that it is canonical-gated and PAPER only?
4. Where should the audit be stored: JSONL under `data/`, or the existing audit table? A table would need a DB write path, which needs governance.
