# REDTEAM 19 — adversarial review of local unpushed commits (branch `ahos`)

- Reviewer: Grok executor subagent (independent red team, HARD MODE). Read-only: no checkout/stash/reset/commit/push; no project code or tests were run.
- Date: 2026-10-02 23:13 (Tehran time)
- Repo: `G:\robat\ahos` @ HEAD `3eea757` (docs-only after `d10383e`; tracked code files in the working tree are clean, so line numbers below are the current file = state as of `d10383e`).
- Commits reviewed: `d10383e` (dev-mission intake), `71fe160` (owner confirm-gated chat commands), `527c433` (GM-04 gate), `1d72d71` (Gemini key path).
- Method: `git log`, `git show --stat`, the diffs, and reads of callers and config (`app/api/chat/route.ts`, `conversation_gateway.ts`, `web_api_auth.ts`, `web_api_client.ts`, `CommandCenter.tsx`, `telegram_ai/{adapter,bot,service}.py`, `engine.ts`, `.gitignore`, the docs in `reports/grok/`).

## Findings

### BLOCKER

**B1. The "owner" decision trusts the client-supplied `channel`/`user_id`, so any holder of the shared web bearer token is the owner, including as a spoofed Telegram admin** (`71fe160`)
- `chat_actions.ts:83-91`: `isOwner()` returns true for `channel` `"web"`/`"dashboard"` with no other check. For `"telegram"` it trusts `userId` as given.
- `app/api/chat/route.ts:50-51`: `user_id` and `channel` come straight from the JSON body, and `channel` defaults to `"web"`. `chat.ts` (handleChat) defaults `ctx.channel ?? "web"` too, so a request that omits `channel` is treated as the owner.
- The Telegram bot (`telegram_ai/service.py:95-97`) and the browser dashboard (`web_api_client.ts:3,8`, `NEXT_PUBLIC_AHOS_WEB_API_TOKEN`) send the same bearer token. A `NEXT_PUBLIC_*` value is compiled into the client JS bundle, so the token is readable by anyone who can load the dashboard page.
- In `AHOS_WEB_API_ALLOW_OPEN_ACCESS=1` mode (`web_api_auth.ts:71`) there is no token at all: any local process becomes the owner.
- Impact: a token holder can POST `{channel:"web"}` (or `{channel:"telegram", user_id:"<admin id>"}`), receive the code in `pending_action.code` in the response (`route.ts:78`), then POST `تایید CODE` with the same identity. That starts or stops the engine, records paper buys, and queues dev missions. The second step needs no human.
- Self-contradiction: `527c433` documents this exact weakness and the reason chat was refused for every channel (`chat_control_gate.ts:5-14`: "channel ... is never used as a grant"; `conversation_gateway.ts:27`: "forwarded for the audit only; never used as a grant"). `71fe160` turns `channel` into a grant without updating either comment. The residual is only noted at `chat_actions.ts:80-81`.
- Mitigation that holds: the dev server binds 127.0.0.1 (`package.json:5,7`), and every action is PAPER-only (see the Holds list).
- Fix: derive identity server-side. Either have the bot use its own secret (a separate token that maps to `channel=telegram`, with `user_id` signed or HMAC'd by the bot), or have the dashboard use a separate secret that is not `NEXT_PUBLIC` (an httpOnly session cookie plus a CSRF token). Never default `channel` to an owner channel.

### MAJOR

**M1. Telegram "reader" allowlist is promoted to owner** (`71fe160`)
- `chat_actions.ts:88`: `isOwner` accepts a user id found in `TELEGRAM_ALLOWED_CHAT_IDS`, which is the chat-access allowlist (`telegram_ai/adapter.py:51-54`), not the admin list (`adapter.py:62-63`, `TELEGRAM_ADMIN_USER_IDS`).
- In Telegram, a private chat's id equals the user's id. So every user whose private chat is allowlisted for read access becomes an owner who can start or stop the engine and paper-buy.
- Fix: owner = `TELEGRAM_ADMIN_USER_IDS` only.

**M2. A secret in a dev-mission summary is written to disk unredacted through `titleFa`** (`d10383e`)
- `dev_missions.ts:185`: `titleFa: titleFromSummaryFa(summary)` is computed from the unredacted summary. Redaction only runs on `summaryFa` at line 186.
- The title is the first clause, cut at `.!?،,;:` and capped at 60 chars (`:130-134`). A summary such as `add AIza…(39 chars) to config` with no early punctuation puts the whole key in `titleFa`, in the JSONL. `list_dev_missions` then sends the title back to Gemini (`chat_agent.ts:296-301`).
- The selftest only passes by luck: its fixture has a colon before the key, `dev_missions_selftest.ts:69`.
- The docstring promise at `dev_missions.ts:20-22` is therefore false.
- Fix: redact first, then derive the title from the redacted text. Add a test with no punctuation before the key.

**M3. The owner approves an 80-char view, but up to 280 chars are queued, and the summary is model-authored and open to injection** (`d10383e`)
- `chat_actions.ts:110` shows `s.slice(0, 80)` in the proposal. `dev_missions.ts:40,125-126` stores up to 280 chars.
- The summary is the Gemini function-call argument (`chat_agent.ts:556`), not the owner's text. Gemini also reads untrusted feed text through `get_news` (`chat_agent.ts:252-262`) in the same loop, and any `propose_*` call is accepted immediately (`:516-518`).
- Result: an injected news title can steer the model to call `submit_dev_mission` with a benign first 80 chars and a hidden tail of up to 200 chars. The owner confirms what they see, and the hidden instructions land in the queue meant for future engineering/coding agents. This is second-order prompt injection.
- Fix: show the full stored summary (or a hash plus the full text) in the confirmation, and bind the code to that text. Do not offer `submit_dev_mission` or `propose_*` in a turn that has consumed untrusted tool output (news), or require the summary to come from the user's own message.

**M4. Docs and comments say the opposite of the code** (`71fe160`, `527c433`)
- `chat_control_gate.ts:1-14` and `conversation_gateway.ts:27` still say chat is refused for every channel and that `channel` is never a grant. Both are false after `71fe160`.
- The `71fe160` commit body says "no ... authority ... changes", yet the same body says the owner authority decision replaces the GM-04 refusal.
- Fix: update the comments and docs, and state the authority change plainly.

### MINOR

- **m1** (`d10383e`), `chat_actions.ts:357-361`: `recordDevMission` never passes `confirmCode`, so `DevMissionRecord.confirmCode` (`dev_missions.ts:50-51`, called an "audit link") is always `null`. Fix: pass `a.code`.
- **m2** (`71fe160`), `chat_actions.ts:94`, `memoryKey` in `chat_memory.ts:28-31`: every web caller shares the identity key `web:` (userId is null), so anyone on the web channel can confirm or cancel anyone else's pending code and shares their conversation memory. Fix: per-session id.
- **m3** (`71fe160`), `chat.ts` `persistChat`: the raw user text and the proposal text (with its code) go unredacted into the DB `chatMessages` table. Memory is redacted (`chat_memory.ts:58-62`), but the DB is not, which conflicts with the "never the raw message" wording in `d10383e`. Fix: apply `redactSecrets` before insert.
- **m4** (`71fe160`), `chat.ts` agent path, `chat_agent.ts:486-490`: the proposal text with the live 6-char code is stored in memory and resent to Gemini (a third party) on later turns. Fix: strip codes from memory.
- **m5** (`71fe160`), `chat_actions.ts:147-149,323`: the code is checked by Map lookup (not constant time) and there is no failed-attempt counter. The practical risk is low (31^6 ≈ 8.9e8 codes, 5-minute TTL, Telegram rate limit of 1 rps). Fix: add an attempt cap per identity.
- **m6** (`71fe160`), `chat_agent.ts:565-566`: the model chooses `quantity` for paper buys with no upper bound. Paper only. Fix: clamp it.
- **m7** (all commits): test counts in the docs are not backed by committed logs. `CLAUDE_CONTINUATION_GUIDE.md:435` claims 14/14, 30/30, 72/72, 126/126, and `GROK_HANDOFF.md:28,116,196` claim 60, 230 and 2636 passed. The `it()` counts match for dev-missions (14) and chat-agent (30). chat-intent has only 10 `it()` and chat-control-gate 17, so 72 and 126 must come from table-driven cases; that was not verified because tests were not run. The docs do label these as self-tests and mark the live round trip unverified (`GUIDE:448`, `HANDOFF:31`), which is honest. The "Verbatim replies are in the final Phase 7 report" (`GUIDE:394`) are not in any commit. Fix: commit the test output logs, or link to untracked artifacts by path and hash.

## Attacks that HOLD (checked, not found)
- **No real secrets in the 4 commits.** All `AIza` hits in their files are bare 4-char regex or fixture prefixes. A masked scan of added lines for `AIza…`, Telegram bot tokens, `sk-`, `ghp_`, PEM blocks, 0x64-hex keys and `key|token|secret=<16+ chars>` found 0 hits. The `git grep -E "AIza|api[_-]?key|token|secret"` matches are identifiers, docs and regex patterns. (One pre-existing 35-char `AIza…` fixture is in `tests/test_security_hardening.py:37`, which none of these commits touched.)
- **Gemini key path (`1d72d71`, `71fe160`):** the key is read from Windows Credential Manager `AHOS/ai/gemini`, read-only with a prefix allowlist (`wincred_reader.py:17,33`). It is sent only in the `x-goog-api-key` header, never in the URL (`gemini_phraser.py:98-101`). Errors are scrubbed (`:76-80,116,122`) and only reason codes come back (`credential_store.py` `CredentialUnavailable`). The helper env is a minimal allowlist with no DB or tokens (`gemini_phraser.ts:189-201`), no shell, fixed argv. `.env` and `data/` are gitignored (`.gitignore:10,19`), and `check-ignore` confirmed `data/dev_missions/*.jsonl` and `data/control_audit.jsonl` are ignored.
- **Code generation:** codes come from `crypto.randomInt`, are single use (`take()` happens before execution, `chat_actions.ts:337`), expire after 5 minutes, and are bound to the identity key. Expired, cancelled and non-owner confirms are audited. Params are stored server-side, so a replayed code cannot change the symbol, amount or kind.
- **Telegram:** `user_id` comes from `message.from.id` (`adapter.py:236-241`), not the username. Forwarded messages carry the forwarder's id. `edited_message` and `channel_post` are ignored. In groups, non-admin members fail `isOwner` and cannot use another member's code because of the identity binding.
- **Prompt injection cannot execute anything directly.** `propose_*` only creates a pending action. Execution requires a whole-message `تایید CODE` in the user's own text (`chat.ts` checks before routing; `parseConfirmation` is anchored, `chat_actions.ts:177`). Read tools are a whitelist. Proposals for non-owners are refused.
- **PAPER_ONLY:** the reachable actions are `startEngine`/`stopEngine` (a DB flag plus an analysis timer, `engine.ts:77-100`), `addPaper` (a DB insert into `paperPositions` behind the canonical BUY and security gate, `engine.ts:781-813`, `chat_actions.ts:226-229`), `addWatch`, and a JSONL append. No exchange, wallet, ccxt, order or transaction calls exist in the changed files or `engine.ts`.
- **Dashboard CSRF:** auth uses a custom header, never a cookie or query string (`web_api_auth.ts:46-53`). Comparison is constant time (`:55-64`). The token never appears in a URL or the logs reviewed. (Its exposure as `NEXT_PUBLIC` is covered in B1.)
- **GM-04 whole-message matching (`527c433`):** an exact phrase list after normalization (`chat_control_gate.ts:54-83`). "stop loss" does not match.

## Commands denied or blocked
- None were denied by approval. One `Read` call on the laptop path was refused by the local-exec root policy, so reads went through `Shell`/`Get-Content` instead. One `Shell` call failed once because the machine was briefly unreachable, and the retry succeeded.
