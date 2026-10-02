# GM-04 proposal: capability gate for chat/Telegram operational control

| Field | Value |
|---|---|
| Status | **IMPLEMENTED / TESTED (self-tests only), conservative capability-reducing form; PENDING INDEPENDENT REVIEW** by سپهر/قاسم/رضا. Phase 4 (2026-10-02), local commit only (pushes paused by owner). Not INTEGRATED/OPERATIONAL until the owner's live Telegram E2E (`reports/grok/G11_LIVE_E2E_RUNBOOK.md`). §1–§6 are the original design, kept for review history; §7 is what was implemented in Phase 4. **§8: OWNER AUTHORITY DECISION 2026-10-02 (Phase 7b) replaces the blanket refusal with a confirm-gated path for the owner only; flagged for سپهر/قاسم/رضا review.** |
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

## 7. Implementation (Phase 4, 2026-10-02): conservative, capability-reducing form

**Status:** IMPLEMENTED / TESTED with self-tests only. **PENDING INDEPENDENT REVIEW** by سپهر, قاسم and رضا. This change only removes capability, so the owner instructed that it does not need governance approval before implementation. It has not been independently verified.

### 7.1 What was chosen

This is option 3(b) of §3, the safest option that needs no new secret.

- `/api/chat` cannot prove the request came from the local dashboard:
  - It uses one shared bearer, `AHOS_WEB_API_TOKEN`.
  - Telegram and dashboard chat reach the same route.
  - `channel` and `user_id` are client-asserted body fields.
- So the chat path now **refuses `start`, `stop` and `paper_buy` for every channel**, including a claimed `web`, `local` or `dashboard`.
- The refusal is a Persian reply. The decision never reads the `channel` field. That field is recorded in the audit only, sanitized and labelled `channel_claimed`.

### 7.2 Dashboard behaviour (documented change)

Dashboard **chat** was exactly as exposed as Telegram: same route, same token, client-asserted channel. Per the task rule, this change is documented here rather than made silently.

- **Changed:** typing «شروع» / «توقف» / «خریدم …» in the dashboard *chat box* is now refused. The reply points to the dashboard buttons.
- **Unchanged:**
  - The dashboard **Start/Stop buttons** still call `/api/engine`.
  - The dashboard **paper buy** still calls `/api/paper`, which keeps the canonical BUY requirement and the overlay.
- `/api/engine` start/stop now also appends an `ALLOWED` audit line (surface `engine_api`).
- Residual (not changed, for review): any holder of `AHOS_WEB_API_TOKEN` can still call `/api/engine` directly. Closing that needs a real local-only proof such as a loopback check or a second secret. That is GM-04 phase 2 and needs review.

### 7.3 Intent matching fix (T2)

`detectControlCommand` (in `chat_control_gate.ts`) matches the **whole message** against explicit phrase lists only. Before matching it normalizes the text:

- NFKC (folds fullwidth characters)
- strips zero-width and bidi marks
- ZWNJ becomes a space
- Arabic ي/ى/ك become ی/ک
- strips harakat
- lowercases and collapses whitespace
- removes trailing punctuation
- removes an optional «لطفا»/please
- rewrites `/cmd@bot` to `cmd`

Results:

| Matches? | Messages |
|---|---|
| Never | "stop loss", "stoploss", "Stop-Loss", "start-up", "startup", "restart", "nonstop", "قیمت توقف ضرر چنده", "توقف ضرر", "چرا موتور خاموشه؟", "start the analysis of BTC" |
| Yes | "STOP", " stop! ", "/stop@Sun_sniperbot", "لطفا خاموش کن", "شروع کن؟", "ｓｔｏｐ", "st\u200Bop" |

These matches are refused anyway. `paper_buy` now needs an explicit phrase (خریدم / خرید کاغذی / ثبت خرید / paper buy), so a bare "paper" (as in "paper trading چیه") no longer counts as a buy.

### 7.4 Audit (T5)

The audit is append-only JSONL with a hash chain:

- **Location:** `AHOS_CONTROL_AUDIT_PATH`, otherwise `(AHOS_DATA_DIR || <cwd>/data)/control_audit/chat_control_audit.jsonl`. `data/` is gitignored.
- **Schema:** `ahos.chat_control_audit.v1`
- **Fields:** ts, surface, intent, capability, decision, reason, channel_claimed, `user_id_hash` (sha256 of `ahos:user:<id>`, first 16 hex chars), `message_sha256`, message_len, prev_hash, entry_hash
- **No raw text and no raw ids.**
- A torn tail is isolated on its own line and never rewritten.
- A sink failure never throws, and the refusal still applies (fail-closed).
- `verifyAuditLines` detects tampering and deletion.

### 7.5 Replay (T4)

- A replayed update reaching `/api/chat` is simply refused again and audited again. The repeat is visible as the same `message_sha256`. Since nothing is granted, a replay cannot cause action.
- Bot-side, the GM-02 `ReplayGuard` still drops duplicate `update_id`s.

### 7.6 Files

| File | Change |
|---|---|
| `chat_control_gate.ts` | New, pure module |
| `chat.ts` | Gate runs right after `detectIntent`, before any snapshot or DB access. `startEngine`/`stopEngine` imports and branches removed. The paper_buy branch is kept as unreachable defence in depth, with canonical pins intact. Help, greeting and hint wording updated. |
| `conversation_gateway.ts` | Forwards `channel`/`user_id` for the audit only |
| `app/api/engine/route.ts` | ALLOWED audit line |
| `scripts/chat_control_gate_selftest.ts` | New, plus npm `test:chat-control-gate` |
| `tests/test_chat_control_gate_static.py` | New |
| `scripts/verify_control_audit.ts` | New, read-only chain verifier; npm `audit:control-verify` |

**Self-tests** (not independent verification): npm `test:chat-control-gate` 126/126; Windows pytest Telegram + canonical sets 271 passed / 1 xfailed; `tsc --noEmit` 0 errors; eslint clean.

### 7.7 Rollback

`git revert <commit>`. No data migration is needed. The audit file can stay.

### 7.8 Questions for reviewers

1. Is refusing dashboard chat control acceptable, given that the buttons are unchanged?
2. Should the residual `/api/engine` bearer exposure be closed with a loopback check plus a second secret (GM-04 phase 2)?
3. Should the chat `watch` intent (watchlist write via `addWatch`) also be gated? It is out of this scope and unchanged.
4. Should `AHOS_CONTROL_AUDIT_PATH` be registered in the config schema? `tests/test_config_validation.py` only scans the fixed file list, which does not include the new module.

## 8. Owner authority decision, 2026-10-02 (Phase 7b): confirm-gated owner commands

| Field | Value |
|---|---|
| Decided by | Owner (Mehrdad Ghodrati), scope change relayed at 17:35 Tehran, 2026-10-02 |
| Status | IMPLEMENTED / TESTED (self-tests and live gateway check). **FLAGGED FOR سپهر/قاسم/رضا REVIEW.** Local commit only. |
| What changes | For the **owner only**, the §7 blanket refusal of start, stop and paper_buy over chat is replaced by a confirm-gated path. Non-owners are still refused and audited exactly as in §7. |
| What does not change | PAPER_ONLY; live trading stays DISABLED; Lane A, the Canonical Decision Authority (still decides every paper buy), the hooks overlay, keys/secrets/constitution/authority settings. None of these are reachable from chat. Whole-message command detection (normalized) stays, so «stop loss» never stops anything. |

**Owner identity** (`chat_actions.ts::isOwner`):
- Telegram: the sender's user_id must be in `TELEGRAM_ADMIN_USER_IDS` ∪ `TELEGRAM_ALLOWED_CHAT_IDS` (the existing bot allowlist; empty means nobody).
- Dashboard chat: channel `web`/`dashboard` behind the dashboard bearer token. This is the same trust as the `/api/engine` and `/api/paper` buttons.
- Any other channel is not the owner.

**Flow:**
1. The model (or the deterministic gate) proposes. Commands are limited to the whitelist: engine start/stop, paper buy, watch add.
2. The bot shows a Persian summary plus a 6-character code: «برای اجرا دقیقاً بفرست: تایید CODE». The code expires after 5 minutes, works once, and is bound to the proposer's identity.
3. Execution happens only on a whole-message `تایید CODE` from the same identity, re-checked as owner. It runs through the same functions as the dashboard routes (`startEngine`/`stopEngine`/`addWatch`; paper buy = `paperAllowedFromCanonical` + `addPaper`).
4. Every step is appended to the hash-chained control audit (surface `chat_confirm`): PROPOSED, then CONFIRMED / CANCELLED / EXPIRED / DENIED / FAILED.
- The model has no execute tool. It can only call `propose_*`, and an answer claiming execution is rejected by the validator.

**Residual risks for reviewers:**
1. Anyone holding `AHOS_WEB_API_TOKEN` can claim channel `web`, which is equal to the existing dashboard-button exposure.
2. A compromised allowlisted Telegram account can propose and confirm.
   - Mitigations: the confirmation is explicit, short-lived and audited.
   - It cannot reach live trading or secrets.
3. The pending store is in memory, so a gateway restart drops proposals (fail-safe).
4. Telegram has no inline buttons yet; confirmation is by text.

**Rollback:** set `AHOS_CHAT_AGENT=off` (agent off). To restore the full §7 refusal for everyone, revert the owner branch in `chat.ts::handleChat` (`if (gate.controlled) {…propose…}`), so that `isOwner` is no longer consulted.

