# CLAUDE CONTINUATION GUIDE: Grok session 2026-10-02 (Phases 1–8)

**Audience:** Claude Code, continuing work on `G:\robat\ahos`, branch `ahos`.
**Written by:** Grok, 2026-10-02 (Tehran time, UTC+3:30).
**Status vocabulary:** IMPLEMENTED / TESTED / VERIFIED / OWNER_ACTION / DESIGN_ONLY. Nothing here is "DONE". Grok's self-tests are **not** independent verification.

Detailed history lives in `reports/grok/GROK_HANDOFF.md` (one `<!-- PHASEn:START/END -->` block per phase). This guide is the condensed "how to keep going" view.

---

## 0. Read this first

### 0.1 Git state: PUSHES ARE PAUSED BY THE OWNER
Everything after `a6638bf` exists **only as local commits** on `G:\robat\ahos` (branch `ahos`). Do not push unless the owner says so. Review the unpushed work with:
```
cd G:\robat\ahos
git fetch origin
git log --oneline origin/ahos..ahos
```

| Commit | Content | Pushed? |
|---|---|---|
| `78fa1e2` | Phase 1: reality inspection docs (`reports/grok/*`) | pushed |
| `552eda7` | GM-02 Telegram offline edge harness | pushed |
| `789dfa2` | GM-03 dashboard truthfulness | pushed |
| `06e44e6` | GM-05 gateway port resolver and diagnosis | pushed |
| `8e48cf3` | GM-06 n8n governance rules, ahos_03 quarantine | pushed |
| `4dd6f9e` | GM-04 design doc | pushed |
| `a6638bf` | P3-M1 tsconfig excludes `docs/archive` | pushed |
| `d1571c4` | GM-08 mission/engineering ledger | **local only** |
| `b4e67be` | GM-09 provider_status, credential_store interface, mission_guard | **local only** |
| `527c433` | GM-04 chat control gate + G11 live-E2E runbook | **local only** |
| `7dd075f` | Phase 5 reply presentation and shared response composer | **local only** |
| `1d72d71` | Phase 6 Gemini phraser + read-only Credential Manager backend + this guide | **local only** |
| `231e7ac` | Phase 7a intent router fix (price, trade_signal, thanks; `chat_intent.ts`) | **local only** |
| (commit adding §2 Phase 7 below) | Phase 7b conversational agent + confirm-gated owner paper commands | **local only** |

The box mirror (`/workspace/repo`, Grok's Linux clone) holds identical trees. It is not a remote.

### 0.2 Commit rules Grok followed (keep them)
- Run `git fetch` before every commit, fast-forward only, and stage **by explicit path**. Never `git add -A`.
- Never touch these Claude-owned dirty or untracked files:
  - modified `reports/backup_restore_drill.json`, `reports/month1_failure_matrix.json`, `reports/reliability_matrix.json`
  - untracked `reports/*` evidence, `next-env.d.ts`, `.cursor/hooks.json.local-backup`, `ahos-hooks-local-diff.txt`
  - `reports/telegram_e2e/`: owner evidence plus bot logs, untracked on purpose
- Never edit:
  - `.cursor/hooks.json` (overlay) or `ahos-guard.py`
  - the Canonical Decision Authority
  - Lane A (`discovery/`, `paper_trading/`, frozen; `freeze_lane_a.py` verifies it)
- No `.env` edits.
- No DB writes, except the chat rows that normal `/api/chat` traffic writes.
- PAPER_ONLY always.
- `scripts/store_ai_key.py` is an **untracked owner script**. Do not commit it, edit it, or run it.

### 0.3 Blocker A (yours, Claude): still open
`tests/test_doc_drift.py::test_canonical_docs_have_zero_real_stale_refs` fails on a clean checkout. Two stale refs in `AHOS_GAP_REGISTER.md` point at **untracked** artifacts:
1. `reports/nightly_backup_series.json` (cited since your `25b33cc`)
2. `reports/validate_imports_run_20260928T045640Z.json` (cited since `7ebea7a`, M-GAP-037)

It passes on the laptop only because those files exist untracked (`scripts/doc_drift.py::_exists` checks the working tree). The same cause makes `tests/test_evidence_package.py::test_package_includes_doc_drift_diagnostic` fail on a clean clone.

Fix (GM-01), choose one:
- (a) commit both artifacts, or
- (b) teach doc_drift "exists but untracked" semantics or an exemption.

Grok did not touch `doc_drift.py`, the artifacts, or the register.

### 0.4 Current process setup (laptop, as of 17:30 Tehran)
**Gateway**
- `next dev --hostname 127.0.0.1 -p 3500`, started manually with `npm run dev -- -p 3500`.
- Node PIDs: 14820 (next), 13120 (server, owns the 3500 listener).
- It hot-reloads TS, so changes to `chat.ts` and similar take effect without a restart.
- **`.env` says port 3000 and nothing listens there.** Choosing the port is OWNER_ACTION (GM-05).

**Telegram bot**
- PID 16548, child 11148, started 16:07:54. Logs: `reports/telegram_e2e/bot_{stdout,stderr}_20261002T123754Z.log`.
- Started hidden with these env vars:
  ```powershell
  cd G:\robat\ahos
  $ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
  $env:PYTHONIOENCODING='utf-8'; $env:PYTHONUNBUFFERED='1'; $env:AHOS_GATEWAY_URL='http://127.0.0.1:3500/api/chat'
  Start-Process -FilePath 'G:\robat\ahos\.venv\Scripts\python.exe' -ArgumentList 'run_bot.py' -WorkingDirectory 'G:\robat\ahos' -WindowStyle Hidden `
    -RedirectStandardOutput "G:\robat\ahos\reports\telegram_e2e\bot_stdout_$ts.log" -RedirectStandardError "G:\robat\ahos\reports\telegram_e2e\bot_stderr_$ts.log" -PassThru
  ```
- Graceful stop: `taskkill /PID <parent>`, **without /F**. The child exits with the parent.
- `telegram_ai/service.py` ignores `AHOS_GATEWAY_PORT`; use `AHOS_GATEWAY_URL`.
- The bot only needs a restart when Python Telegram code changes.

**Gemini phraser:** no separate process. The gateway spawns a short-lived Python helper for each normal chat reply.

**Docker** (from Phase 1): `ahos_postgres_win` healthy; `ahos_runtime_win` unhealthy (config drift); `ahos_n8n_win` up with 0 workflows imported.

### 0.5 Standard Windows commands
```powershell
cd G:\robat\ahos
# Python tests (Python 3.11.9 venv)
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\<file>.py
git checkout -q -- reports/validation_results.json   # pytest rewrites this tracked file; restore it
# TypeScript
npx tsc --noEmit -p .            # expect exit 0
npx eslint <files>
npm run test:<suite>             # see the per-phase lists below
# Import wiring (about 9 min, about 47 min under load)
.venv\Scripts\python.exe scripts\validate_imports.py --imports-only
```

PowerShell 5.1 gotchas:
- `Invoke-RestMethod` mis-decodes UTF-8. Use `Invoke-WebRequest -UseBasicParsing` and `[Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())`.
- Write files with `[IO.File]::WriteAllText(path, text, [Text.UTF8Encoding]::new($false))`.
- Piping Persian through PS stdin turns it into `?`. Write a UTF-8 file and redirect with `cmd /c "... < file"`.

Local authenticated POST (never print the token):
```powershell
$tok = ((Select-String -Path .env -Pattern '^AHOS_WEB_API_TOKEN=').Line -split '=',2)[1].Trim().Trim('"')
$body = [Text.Encoding]::UTF8.GetBytes('{"message":"راهنما","channel":"dashboard"}')
$r = Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:3500/api/chat -Method POST -Body $body -ContentType 'application/json; charset=utf-8' -Headers @{Authorization="Bearer $tok"}
Remove-Variable tok
[Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray())
```

---

## 1. Invariants you must not break

1. **GM-04 gate, changed by the owner authority decision of 2026-10-02 (Phase 7b; pending سپهر/قاسم/رضا review; see GM04 doc §8)**
   - **Non-owners:** `/api/chat` refuses start, stop and paper_buy, and the refusal is audited REFUSED, exactly as in Phase 4.
   - **Owner** (Telegram user_id in `TELEGRAM_ADMIN_USER_IDS` ∪ `TELEGRAM_ALLOWED_CHAT_IDS`, or dashboard channel `web`/`dashboard`): gets a **proposal only**. Execution requires a whole-message `تایید CODE` from the same identity within 5 minutes; the code works once. It then runs through the same functions as the dashboard routes (`chat_actions.ts`).
   - Never add an execute tool for the model. Never let a bare «تایید»/«بله» or any substring confirm anything.
   - No chat path may reach live trading, keys/secrets, constitution/authority settings, or Lane A.
   - Command detection matches the whole message after normalization (NFKC, zero-width and bidi stripping, Arabic→Persian letters). Do not reintroduce substring regexes: "stop loss" used to stop the engine.
   - Refusal, proposal and confirmation texts are `locked: true` and are **never** phrased by an LLM.
2. **Control audit chain**
   - `data/control_audit/chat_control_audit.jsonl` is append-only and hash-chained. `FileAuditSink` isolates a torn tail.
   - Every REFUSED decision (chat), ALLOWED decision (engine route) and Phase 7b `chat_confirm` decision (PROPOSED/CONFIRMED/CANCELLED/EXPIRED/DENIED/FAILED) appends one line. Never rewrite or delete lines.
   - Verify with `npm run audit:control-verify`.
3. **Mission ledger (GM-08)**
   - `architecture/mission/ledger.py`: append-only JSONL, hash chain, no DONE state, `resume()` never resets a checkpoint, secrets redacted before hashing, `authority: "NONE"`.
   - Decision, trading and telegram code must not import it, and it must not import them (static tests pin this).
4. **provider_status (GM-09)**
   - Use the 7-state `AIProviderStatus` and `classify_provider_error` for AI provider errors. Do not invent new status strings.
   - QUOTA_EXHAUSTED and AUTH_FAILED need owner credential action (`persian_new_key_message`).
5. **Composer and phraser validator**
   - Every chat reply goes through `response_composer.ts::finalizeReply`.
   - LLM output is accepted only if `validatePhrased` passes:
     - not empty
     - within the length limit
     - footer «تصمیم نهایی با کاربر است.» exactly once
     - no jargon (GM-xx, canonical, UNKNOWN)
     - **no number that is not in the deterministic draft** (Persian and Arabic digits normalized)
   - Otherwise the deterministic text is used.
   - Phrased HTML is rebuilt from escaped plain text (`phrasedHtml`); phraser HTML is never trusted.
   - The phraser is wording only and has zero authority.
   - **Phase 7b agent** (`chat_agent.ts`): answers are accepted only if `validateAgentAnswer` passes. The checks: no jargon, no execution claims, no TRADE_PICK (leverage or TP/SL figures), and every number from tool output, the user message or earlier assistant turns. One corrective retry is allowed; otherwise the deterministic 7a path runs with an honest note. Read tools return Persian labels only (`faLabel`). Do not widen the tool registry without review.
6. **Gemini key handling**
   - The key lives **only** in Windows Credential Manager: generic target `AHOS/ai/gemini`, user `gemini`, UTF-16-LE blob, stored by the owner.
   - **Never** put it in `.env`, logs, argv, env vars, test files, reports, commits or chat.
   - Only the helper processes `architecture/ai/gemini_phraser.py` and `architecture/ai/gemini_chat.py` call `get_secret`; Node never sees the key. `gemini_phraser.ts::HELPER_MODULES` whitelists the spawnable modules.
   - `wincred_reader.py` is read-only (no CredWrite, CredDelete or CredEnumerate; pinned by a test) and only reads `AHOS/ai/*` targets.
7. **Telegram edge (GM-02)**
   - The replay guard runs before auth, rate-limit and gateway.
   - The audit stores hashed ids and the text length/sha only, never raw text.
   - The allowlist fails closed when empty.
   - Telegram sends HTML only when it is 4096 characters or less and Telegram accepts it; otherwise it sends plain text.
8. **Dashboard truth (GM-03)**
   - Never show a hard-coded green status. Stale data renders as STALE/UNKNOWN, and non-PAPER modes render as VIOLATION.
9. **n8n (GM-06)**
   - `ahos_03_telegram_control.json` is quarantined: do not import it. `ahos_02` has a `Record PENDING (LIVE)` node that needs review before any import.

---

## 2. Per-phase summary

**Newest first: Phase 9.5 + 9.6** — corrective mission closing every finding in
two independent reviews; see its own section below and
`reports/grok/reviews/FIX_MATRIX_PHASE9_5_9_6.md`.

### Phase 1: reality inspection (docs only), `78fa1e2`
- **Built:** `reports/grok/GROK_SESSION_2026-10-02_REALITY_INSPECTION.md`, `TELEGRAM_REALITY_MAP.md`, `DOCKER_N8N_DEPENDENCY_MAP.md`, `DASHBOARD_ONECLICK_REALITY.md`, `MISSION_DISCOVERY_2026-10-02.md` (missions GM-01…GM-12), `GROK_HANDOFF.md`.
- **Findings that drove later phases:**
  - the Telegram free-text start/stop leak (→ GM-04)
  - the empty `user_id` (→ GM-02)
  - ahos_03 SQL interpolation and audit DELETE (→ GM-06)
  - stale green dashboard (→ GM-03)
  - port 3000 vs 3500 (→ GM-05)
  - blocker A

### Phase 2: GM-02, GM-03, GM-05, GM-06, GM-04 design (all pushed)

**GM-02 Telegram offline harness**
- `telegram_ai/envelope.py`: envelope v1, `hash_identifier`, `redact_envelope`, `ReplayGuard`, `TelegramAuditLog`.
- `telegram_ai/bot.py`: optional `replay_guard` / `audit_log`. Every exit path is audited, and `user_id` is forwarded.
- `telegram_ai/adapter.py`: monotonic mock update ids.
- Test: `tests/test_telegram_offline_harness.py`.
- **Why:** prove the edge offline, without the network or the token.

**GM-03 dashboard truth**
- `dashboard_truth.ts` (pure); `snapshot.ts` derives the paper/zero-money status from `state.executionMode`; `CommandCenter.tsx` shows a STALE banner and runs a 15 s freshness clock.
- Tests: `npm run test:dashboard-truth` (34), `tests/test_dashboard_truth_static.py`.

**GM-05 gateway port**
- `scripts/gateway_port.py`: precedence is `AHOS_GATEWAY_URL` > `AHOS_GATEWAY_PORT` > 3000; probes loopback only. Run `.venv\Scripts\python.exe scripts\gateway_port.py --json`.
- Also changed: `scripts/operator_validation_gate.py` and `scripts/windows_run_operator_gate.ps1`.
- Test: `tests/test_gateway_port.py`.
- **Why:** non-breaking; `.env` was deliberately not edited.

**GM-06 n8n governance**
- `tests/validate_n8n.py` `governance_findings`; `QUARANTINED_WORKFLOWS` (exact filename).
- Test: `tests/test_n8n_governance_rules.py`. Doc: `reports/grok/GM06_N8N_QUARANTINE.md`.

**GM-04 design:** `reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`.

### Phase 3: P3-M1, GM-08, GM-09

**P3-M1**
- `tsconfig.json` excludes `docs/archive`, which brought `tsc` from 9 errors to 0.
- Test: `tests/test_tsconfig_archive_exclusion.py`.

**GM-08 ledger (`d1571c4`, local)**
- Code: `architecture/mission/ledger.py`. CLI: `.venv\Scripts\python.exe scripts\mission_ledger.py --help`.
- Storage: `<AHOS data dir>/mission_ledger/mission_ledger.jsonl`. It has not been seeded yet.
- Test: `tests/test_mission_ledger.py` (72).
- **Why JSONL and not the DB:** append-only, crash-safe (O_APPEND + fsync), and no DB writes allowed.
- **Limitation:** a keyless chain cannot detect a whole-file rewrite. Anchor `head_hash` externally (`verify(anchor_hash=...)`).

**GM-09 provider status (`b4e67be`, local)**
- Code: `architecture/ai/provider_status.py`, `architecture/ai/credential_store.py`, `architecture/ai/mission_guard.py`.
- Test: `tests/test_ai_provider_status.py`. Doc: `reports/grok/GM09_PROVIDER_STATUS_AND_CREDENTIAL_STORE.md`.
- **Open:** `guard_provider_call` is not yet wired into `LiveCouncil` or the router (advisory wiring is a recommended next mission).

### Phase 4: GM-04 implementation (`527c433`, local)

**Code**
- `chat_control_gate.ts`: `detectControlCommand`, `looksLikePaperBuy`, `gateChatControl`, `recordControlAudit`, `FileAuditSink`, `defaultAuditPath`. Audit path: `AHOS_CONTROL_AUDIT_PATH`, else `(AHOS_DATA_DIR||./data)/control_audit/chat_control_audit.jsonl`.
- `chat.ts`: the gate runs before any routing. `app/api/engine/route.ts` writes ALLOWED lines.
- `scripts/verify_control_audit.ts`.

**Tests**
- `npm run test:chat-control-gate` (126)
- `npm run audit:control-verify`
- `tests/test_chat_control_gate_static.py`

**Why "always refuse":** `/api/chat` cannot prove the request came from the local dashboard; the body's `channel` field can be spoofed.

**Live:** the owner ran the G11 E2E. Refusals worked and the chain was OK (`reports/telegram_e2e/telegram_e2e_20261002T1221Z.md`, untracked). Runbook: `reports/grok/G11_LIVE_E2E_RUNBOOK.md`.

**Open**
- Independent review by سپهر / قاسم / رضا (GM04 doc §7).
- Any holder of `AHOS_WEB_API_TOKEN` can call `/api/engine`.
- The chat `watch` intent (watchlist write) is ungated.
- `AHOS_CONTROL_AUDIT_PATH` is not in the config-validation scan list.

### Phase 5: reply presentation and shared composer (`7dd075f`, local)

**Code**
- `reply_format.ts`: blocks, `renderPlain`, `renderTelegramHtml`, `escapeHtml`, `safeUrl`, 3600-character budget, `isMostlyPersian`, `faAge`.
- `chat_replies.ts`: pure builders per intent.
- `response_composer.ts`: `RESPONSE_STYLE_FA`, `GroundedDraft`, `ReplyPhraser`, `composeDeterministic`, `validatePhrased`, `finalizeReply`.
- `chat.ts`: routing. «بازار چه خبر؟» → market; new `stop_loss` intent; engine-off note only where relevant.
- Plumbing: `answer_html` through `conversation_gateway.ts` / `types.ts` / `app/api/chat/route.ts`.
- Telegram side: `telegram_ai/service.py` (`text_html`) and `telegram_ai/bot.py` (`parse_mode=HTML`, plain fallback, `clamp_telegram_text`).

**Tests**
- `npm run test:chat-reply-format` (40)
- `tests/test_telegram_reply_presentation.py` (11)

**Why:** one composer for the dashboard and Telegram, so a future LLM can only re-word grounded drafts.

**Known limitation:** plain-text news shows the URL without the source name.

### Phase 6: Gemini phraser (local commit that adds this file)

**Code**
- `architecture/ai/wincred_reader.py`: read-only CredReadW.
- `architecture/ai/credential_store.py`: `WindowsCredentialManagerStore(reader=None)`, `CredentialUnavailable`.
- `architecture/ai/gemini_phraser.py`: helper with entry point `python -m architecture.ai.gemini_phraser`, JSON over UTF-8 stdin and stdout.
- `gemini_phraser.ts`: `GeminiPhraser`, `spawnHelperRunner`, `helperEnv`, `resolvePython`, `getDefaultPhraser`, `cleanModelText`.
- `response_composer.ts`: `phrasedHtml`.
- `chat.ts`: passes the phraser to the normal reply and records `evidence.phraser`.

**Flow:** `chat.ts` → `finalizeReply(draft, getDefaultPhraser())` → `GeminiPhraser.phrase` → spawn `.venv\Scripts\python.exe -m architecture.ai.gemini_phraser` with no shell and a minimal env → the helper reads `AHOS/ai/gemini` → POST to `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` (header `x-goog-api-key`) → text → TS cleans it and appends the footer → `validatePhrased` → accept, or fall back to deterministic.

**Config (env; none are set in `.env`)**

| Variable | Effect |
|---|---|
| `AHOS_PHRASER=off` | disables the phraser |
| `AHOS_GEMINI_MODELS` | default `gemini-flash-lite-latest,gemini-3.5-flash-lite`; max 2 used. `gemini-flash-latest` gave 503 and 2.5-* gave 404 in owner tests |
| `AHOS_PHRASER_TIMEOUT_MS` | default 4000 per attempt; the helper's total budget is 9 s |
| `AHOS_PHRASER_PYTHON` | overrides the Python executable |

**Circuit breaker** (in memory, per gateway process):
- 3 consecutive failures → open for 60 s.
- One failure with AUTH_FAILED, QUOTA_EXHAUSTED, NO_CREDENTIAL, EMPTY_CREDENTIAL, NOT_WINDOWS, READ_FAILED or HELPER_SPAWN_FAILED → open for 10 min.
- While open, the deterministic reply is returned with no added latency.
- Restarting the gateway resets it.

**Skipped drafts:** locked (refusals) and drafts with links (news), because a rewrite could drop or alter source URLs.

**Run and test**
```powershell
npm run test:gemini-phraser                      # 12, fake runner, no network
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_gemini_phraser.py tests\test_ai_provider_status.py
cmdkey /list:AHOS/ai/gemini                      # shows presence only, never the secret
# manual helper run (uses the real key in-process; prints JSON without the key):
[IO.File]::WriteAllText("$env:TEMP\req.json", '{"draft":"وضعیت بازار\n• بیت‌کوین: ۶۴٬۲۰۰ دلار","style":[]}', [Text.UTF8Encoding]::new($false))
cmd /c ".venv\Scripts\python.exe -m architecture.ai.gemini_phraser < %TEMP%\req.json > %TEMP%\out.json"
[IO.File]::ReadAllText("$env:TEMP\out.json",[Text.Encoding]::UTF8)
```

**Observed latency:** model about 1.1 s; end to end from Node about 2.0 s (Python spawn about 0.9 s). A one-off stall of more than 5 s happened on the first connection through the owner's local proxy (`127.0.0.1:10809`, Windows registry proxy that urllib picks up) after idle. That is why the 4 s × 2 / 9 s budget exists.

**Live smoke** (one POST, 17:21 Tehran): the phraser hit the proxy stall (`reason: NETWORK`), and the deterministic reply came back correctly. **A phrased reply via the live gateway is not yet observed**; check `evidence.phraser` on the next chat messages.

**Open items**
- GM-12 independent security review of the Credential Manager read path.
- The breaker state is not persisted or exposed on the dashboard.
- Python spawn adds about 0.9 s per reply on this 8 GB laptop. A long-lived helper would cut that; not done.
- The phraser is not wired into the GM-08 ledger or `mission_guard`; a quota event currently only opens the breaker (no owner message).
- News and replies with links are never phrased.

---

### Phase 7 (2026-10-02, Grok): conversational AI for Telegram and dashboard (Gemini + tools + confirm-gated paper commands)

**Pushes are still paused by the owner: local commits only.** Status: IMPLEMENTED / TESTED (self-tests and a live gateway check). Not independently verified. **The owner's authority decision of 2026-10-02 changes the GM-04 invariant for owners. It is flagged for سپهر/قاسم/رضا review** (see `GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md` §8).

#### 7a: intent router fix (`231e7ac`)
- New pure `chat_intent.ts`: price intent (BTC/ETH/SOL spelling variants, freshness and stale flag, no invented numbers), trade_signal intent (locked PAPER_ONLY policy reply that outranks stop_loss), thanks, greeting-prefix routing, watchlist view checked before watch_add.
- `scripts/chat_intent_selftest.ts`: 52 Persian regression cases (`npm run test:chat-intent`).
- The GM-04 whole-message control detection still runs first.
- 7a is now the **deterministic fallback** under 7b.

#### 7b: owner scope change at 17:35. The chat is a real conversational AI.
The owner asked for free-form, multi-turn Persian chat like ChatGPT/Grok, not keyword intents. The same backend (`chat.ts::handleChat`) serves Telegram (`telegram_ai/service.py` → `/api/chat`, channel `telegram` plus the real user_id) and the dashboard chat panel.

**Flow per message (`chat.ts::handleChat`):**
1. A whole-message `تایید CODE` / `لغو [CODE]` goes to `chat_actions.handleConfirmation` (before any intent detection).
2. `detectIntent` runs, then the GM-04 gate (whole message, so «stop loss» is never a stop).
   - **Non-owner** control intent: REFUSED, audited (unchanged).
   - **Owner** control intent: a confirm-gated proposal. Nothing executes.
3. The snapshot is taken. **`ChatAgent.run` comes first** (Gemini function calling over a whitelisted tool registry, max 4 model steps).
   - On success: the reply is the agent's grounded Persian answer, or the locked proposal/denial text.
   - On failure (provider down, quota, breaker open, validation rejected twice): the deterministic 7a path runs, with an honest note at the top. The note says either «دستیار هوشمند الان در دسترس نیست…» or «پاسخ دستیار هوشمند با داده‌های سیستم تطبیق نداشت…».
4. Memory is updated and the chat rows are written (same `chat_messages` table as before).

**Files:**
- `chat_agent.ts` (new)
  - Tool registry:
    - READ: `get_market`, `list_opportunities`, `explain_token{symbol}`, `get_news{query}`, `get_engine_status`, `get_paper_positions`, `get_watchlist`, `get_system_health`
    - PROPOSE: `propose_engine_start`, `propose_engine_stop`, `propose_paper_buy{symbol,quantity}`, `propose_watch_add{symbol}`
  - `runReadTool` is pure over the existing `commandSnapshot()` read model. It returns Persian labels plus freshness (`updatedAgoFa`, `stale`) and never raw English status codes (`faLabel`). For BTC/ETH/SOL, `explain_token` returns market data and the note "no TP/SL".
  - **Validator** `validateAgentAnswer`. It rejects:
    - EMPTY or TOO_LONG answers
    - JARGON (GM-xx, canonical, UNKNOWN, INSUFFICIENT_EVIDENCE, tool names)
    - CLAIMS_EXECUTION (first-person "I turned it off")
    - **TRADE_PICK** (leverage figures, `20x`, حد ضرر/حد سود/stop loss/take profit followed by a number)
    - **NEW_NUMBER**: every number must appear in tool output, the user message or earlier assistant turns. Persian and Arabic digits and separators are normalized; rounded and هزار/میلیون/میلیارد/تریلیون scaled forms are accepted; 0–10 is always allowed.
  - One corrective round: a rejected draft goes back to the model with an internal Persian reason (`correctionFa`). A second rejection means fallback.
  - Breaker: 3 failures → open 60 s; auth, quota or credential failure → open 10 min.
  - `systemPrompt` (Persian): PAPER_ONLY, tools-first, admit stale data, trading-advice policy (analysis/paper only, not a personal signal, no invented leverage/TP/SL or tokens outside tool output), commands only via `propose_*`, «stop loss» ≠ stop engine, no secrets/authority changes.
- `architecture/ai/gemini_chat.py` (new)
  - One `generateContent` step with `tools.functionDeclarations` and `toolConfig AUTO`. Key read here only (Credential Manager `AHOS/ai/gemini`, read-only), same rules as the phraser.
  - Model parts are relayed verbatim, so Gemini 3 thought signatures survive; `thought` parts are dropped.
  - Two models, 4 s each, 9 s total budget. No retry on AUTH, QUOTA or BLOCKED.
  - `gemini_phraser.py` gained `call_model_payload`. `gemini_phraser.ts` gained `spawnPythonJson`, with a module whitelist `HELPER_MODULES`.
- `chat_actions.ts` (new)
  - Owner check `isOwner`:
    - Telegram user_id must be in `TELEGRAM_ADMIN_USER_IDS` ∪ `TELEGRAM_ALLOWED_CHAT_IDS`. If both are empty, nobody qualifies.
    - Channel `web`/`dashboard` counts as the owner (same bearer token as the dashboard buttons).
    - `api` or any other channel is not the owner.
  - `PendingActionStore`: 6-character code from an unambiguous alphabet, 5-minute TTL, single use, bound to the proposer's identity, in memory.
  - `parseConfirmation`: whole message only. `تایید|تأیید|تائید|confirm|yes CODE` confirms; `لغو|کنسل|cancel|انصراف [CODE]` cancels. A bare «تایید», «بله» or «stop loss» is never a confirmation.
  - `handleConfirmation` checks identity, owner, expiry and single use, then executes through the **same functions as the dashboard routes**:
    - `engine.startEngine` / `stopEngine` (= `/api/engine`)
    - `engine.addWatch`
    - paper buy = `paperAllowedFromCanonical` + `addPaper` (= `/api/paper`; the Canonical Decision Authority still decides)
  - Every step is appended to the hash-chained control audit with surface `chat_confirm`. Decisions: PROPOSED / CONFIRMED / CANCELLED / EXPIRED / DENIED / FAILED.
- `chat_memory.ts` (new): per-conversation memory keyed by `sha256(channel|userId)`. Last 10 exchanges, 6 h TTL, 200 conversations max, secrets redacted (API keys, Telegram tokens, JWTs, private keys, Bearer, PEM, `*_TOKEN=`). In memory only.
- `chat_control_gate.ts`: `Capability` adds `WATCH_WRITE`; the audit gains the `chat_confirm` surface and the new decision values. The gate function and the non-owner refusal are unchanged.
- Plumbing:
  - `ChatResponse.pendingAction` → `conversation_gateway` → `/api/chat` `pending_action {code, kind, summaryFa, expiresAt}`.
  - `CommandCenter.tsx`: multi-turn chat display (unchanged) plus **تایید / لغو buttons** under a proposal. They send `تایید CODE` / `لغو CODE`.
- Tests:
  - `scripts/chat_agent_selftest.ts` (`npm run test:chat-agent`): 23 cases with a fake runner, no network, temp audit path.
  - `tests/test_gemini_chat.py`: 5 cases.
  - `tests/test_gemini_phraser.py` and `tests/test_telegram_reply_presentation.py`: static pins updated.

**Env (none set in `.env`):**
- `AHOS_CHAT_AGENT=off` disables the agent (back to 7a deterministic replies).
- `AHOS_GEMINI_MODELS` is shared with the phraser.
- `AHOS_CHAT_AGENT_TIMEOUT_MS`: per-attempt timeout, default 4000.

**Tests (Windows, 18:00–18:20 Tehran):**
- tsc exit 0; eslint 0 on all touched files.
- npm: chat-agent 23/23; chat-intent 52/52; chat-reply-format 40/40; gemini-phraser 12/12; chat-control-gate 126/126.
- pytest gemini/telegram/canonical/provider set: 230 passed, 2 skipped.

**Live check** via gateway `127.0.0.1:3500/api/chat`, model `gemini-flash-lite-latest`, 2.5–7 s per reply. Verbatim replies are in the final Phase 7 report. Summary:
1. «قیمت بیت کویین الان چقدر هست؟» → `get_market` → BTC ۷۹٬۷۳۲ دلار, +۰٫۱۵٪, «داده‌ها قدیمی هستند… ۳۵ روز پیش».
2. The futures/leverage/TP/SL request → `list_opportunities` → "paper/analysis only, no signal/leverage/TP/SL; no token has an approved verdict", plus a risk warning.
3. A 3-turn free conversation (market mood → lowest-risk opportunity → «چرا؟») was answered from tools with context carried over.
4. «موتور تحلیل رو خاموش کن» → `propose_engine_stop` → proposal with code → «لغو CODE» → «لغو شد… هیچ تغییری اعمال نشد.»
   - Audit lines: PROPOSED, then CANCELLED.
   - The engine was already off; nothing executed.
5. A non-owner Telegram id got «⛔ این دستور فقط برای مالک سیستم مجاز است» (audit DENIED NOT_OWNER).
6. «stop loss بیت کوین رو کجا بذارم؟» was answered as analysis only, with no stop and no number.

**Open items (Phase 7):**
- Telegram has no inline confirm buttons; it confirms by text «تایید CODE». The dashboard has buttons.
- The pending store and memory are in memory, so a gateway reload drops them. This is the safe default; dropped proposals simply expire.
- Anyone holding `AHOS_WEB_API_TOKEN` can claim channel `web` and therefore owner. This is the same exposure as `/api/engine` and `/api/paper`.
- `TELEGRAM_ADMIN_USER_IDS` is empty in `.env`, so Telegram owner identity currently comes from `TELEGRAM_ALLOWED_CHAT_IDS` (the owner's private chat id equals his user id).
- Latency is about 5 s for tool answers (2 model calls plus 2 Python spawns). A long-lived helper would cut about 1 s per call.
- The agent reads the snapshot taken at message time; market data is 35 days old because the engine is off (the model says so).
- GM-04 owner-authority change and GM-12 Credential Manager read path still need **سپهر/قاسم/رضا review**.

**How to continue**
```powershell
npm run test:chat-agent            # 30 (was 23; +7 dev-mission cases), fake Gemini runner, temp audit path
npm run test:chat-intent           # 72 (was 52; +20 dev-mission cases) (deterministic fallback router)
npm run test:dev-missions          # 14 (hash chain, redaction, tamper, fail-closed)
.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_gemini_chat.py tests\test_gemini_phraser.py tests\test_telegram_reply_presentation.py tests\test_canonical_read_model.py
npm run audit:control-verify       # hash chain incl. chat_confirm lines
```
- `evidence.agent` on each `/api/chat` response holds `{ok, reason, toolsUsed, steps, model, latencyMs}`. `evidence.composer` is `gemini_agent` or `deterministic`.
- To add a read tool: add it to `READ_TOOLS` plus a `runReadTool` case (pure, Persian labels, freshness) plus a selftest.
- To add a command: add it to `ActionKind` plus `PROPOSE_TOOLS` plus `CAPABILITY` plus `defaultActionDeps` (must reuse the dashboard route function), plus selftests for confirm/cancel/expiry/non-owner. It must be PAPER_ONLY and needs review.

---

### Phase 8 (2026-10-02, Claude/Atria): dev-mission intake + University/agents discovery

**8a — dev-mission intake, `d10383e` (local).** The chat assistant cannot write code, so when the owner asks for engineering work it now proposes recording a **development mission** through the *same* confirm flow and words as the paper commands: request → PROPOSAL (Persian summary + one-time 6-char code, 5 min, identity-bound) → «تایید <code>» → one QUEUED line appended to a hash-chained append-only JSONL queue → reply «ثبت شد… کاری هنوز انجام نشده است». `list_dev_missions` is an owner-only read tool. Non-owners refused and audited.

New file `dev_missions.ts` (`DevMissionStore`, schema `ahos.dev_missions.v1`, default `<AHOS data dir>/dev_missions/dev_missions.jsonl` or `AHOS_DEV_MISSIONS_PATH`). It reuses `FileAuditSink` / `verifyAuditLines` / `hashId` / `canonicalJson` from `chat_control_gate.ts` (canonicalJson is now exported). Secret-like substrings are redacted **before** hashing/writing, and the replacement marker carries only the rule name — an earlier draft leaked the first 12 chars of the secret into the marker and the self-test caught it. The raw chat message is never stored.

Touched: `chat_actions.ts` (new `dev_mission` kind, `MISSION_WRITE` capability, `EMPTY_SUMMARY` denial, `recordDevMission` dep, warm locked intro «حتماً! من خودم کد نمی‌نویسم…»), `chat_agent.ts` (`submit_dev_mission` propose tool, `list_dev_missions` read tool, `ReadToolCtx { missions?, owner? }`, jargon guard now blocks `submit_*`/`list_*`), `chat_intent.ts` (conservative `dev_mission` intent: needs both a dev topic and a build verb), `chat.ts` (deterministic fallback branch, store injected into `ChatAgent.run`), `package.json` (`test:dev-missions`).

**Tests, all exit 0:** tsc; eslint; `test:dev-missions` 14/14; `test:chat-agent` 30/30 (was 23); `test:chat-intent` 72/72 (was 52); chat-control-gate 126/126; chat-reply-format 40/40; gemini-phraser 12/12; canonical-read-model 13/13; `audit:control-verify` OK; pytest static set 60 passed / 1 skipped; `validate_imports.py --imports-only` exit 0.

**8b — discovery, no code changed.** `reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md` (new). Findings: the University is **docs only** (part1 §21–26, §92–95; no research/skill/failure registry code, though substrates exist in `architecture/cognitive/`, `architecture/evolution/`, `architecture/knowledge/`, `architecture/learning/`); the 19 agents are a **policy model, not a runtime** — `docs/governance/AGENT_TAXONOMY_MAP.md` records five unmerged namespaces and the "agent 01" collision, with all 19 Slice-1 anchors at `MaturityLevel.REGISTERED` (0) below `MINIMUM_MATURITY_FOR_ALLOW = 2`, so none can hold execution authority; the nine teams are names in two documents with no code namespace; `architecture/control_plane.py` has no non-test importer; no Mission Controller exists. Plan: U0 truth baseline → U1 launcher (M10) → U2 evidence + maturity ramp → U3 control-plane service → U4 mission controller / queue consumer (M13) → U5 University (M15) → U6 teams.

**How to continue (Phase 8)**
```powershell
npm run test:dev-missions      # 14
npm run test:chat-agent        # 30
npm run test:chat-intent       # 72
npm run audit:control-verify   # hash chain incl. the new MISSION_QUEUED lines
```
- The queue has a writer and **no reader**. The M13 mission controller is the intended consumer; until it exists the assistant's «کاری هنوز انجام نشده است» is literally true. Do not add a DONE/COMPLETED status — there deliberately is none.
- Deletion of only the *last* line of the queue is invisible to a keyless hash chain (documented limitation, self-tested). Anchor `head_hash` outside the file (handoff doc, commit) as the chain's checkpoint.
- Not verified: no live gateway POST this run. A real «دانشگاه رو بساز» → code → «تایید CODE» → queued line round trip is still unverified. A gateway reload loses only pending proposals, never queued missions (on disk).
- `AHOS_DEV_MISSIONS_PATH` is not in the config-validation scan (same pre-existing gap as `AHOS_CONTROL_AUDIT_PATH`).

---

### Phase 9 (2026-10-03, Claude/Atria): Mission 9 — truth baseline + Remaining Reality Register

**Read this before quoting any readiness claim.** M9 replaced prose-based
readiness with a measured capability graph. Two new standing artifacts:

- **`reports/grok/REMAINING_REALITY_REGISTER.md`** — the Remaining Capability
  Graph per owner directive part1 §76–§80: 33 capability areas (§1–§33) + 5
  cross-cutting findings (CC-1..CC-5), each with ladder state, evidence path,
  dependencies, proof requirement, governance gate. **Where it disagrees with
  an older map, the register wins.** Every live count in it was re-queried,
  not quoted.
- **`reports/m9/BASELINE.md`** — exact pytest / tsc / eslint / self-test
  counts plus the reason for every skip and xfail. Re-run per directory when
  you need a fresh baseline; do not re-run the whole Windows suite in one go.

**Status vocabulary is now the owner's reality ladder**
(PLANNED < PARTIAL < IMPLEMENTED < TESTED < VERIFIED < OPERATIONAL, plus
BLOCKED / UNKNOWN / CONTRADICTED). The guide's own line-5 vocabulary
(IMPLEMENTED / TESTED / VERIFIED / OWNER_ACTION / DESIGN_ONLY) is superseded
for *new* writing; it stays accurate for the Phase 1–8 facts it was written
against. Docs-only caps at PLANNED/DESIGN; self-tests cap at TESTED.

**One real bug fixed — FM-007, `0b878be`.**
`architecture/learning/prediction_lifecycle.py` hard-coded
`eligible_join_pairs_estimate = 0` (the two stores are separate sqlite
connections, so a cross-DB JOIN is unavailable and the original code returned
the sentinel). Fixed by intersecting token-id sets in memory: 19 labeled ∩
20,744 predicted = **10** live. Regression test in
`tests/test_prediction_lifecycle_bridge.py` (6/6). **This resolves the
handoff's unresolved item 7** and the guide's implicit census gap. Units
differ and both are right: the census's 10 = distinct tokens; the calibration
report's 6,037 = (prediction, label) pairs per (horizon, event-class).

**Twelve stale readiness maps bannered** (STALE/SUPERSEDED, pointing at the
register), including `AHOS_PROJECT_STATE_MAP.md`, `reports/PHASE_STATE.md`,
`reports/G2_MISSION_REPORT_20261002.md`. `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`
was corrected, not just bannered. FM-001..FM-007 appended to
`reports/FAILURE_MEMORY.md`. Full M9 narrative: handoff §Phase 9.

**Top 3 next actions, all dependency-safe, none governance-gated**
1. **Wire `paper_trading/cycle.py:run_full_cycle` into the daemon** — the
   register's highest-leverage node; unblocks calibration, outcome tracking,
   the live decision authority, trade-derived learning, accounting. All 19
   `paper_trading.sqlite` tables hold 0 rows today. No new capability needed.
2. **CC-3** — `architecture/ai/debate_council.py::_risk_manager_evaluation`
   annotates a bare `Tuple` it never imports (one-line fix + test).
3. **CC-1** — route the daemon through `ControlPlane` so START/STOP/SAFE_HALT
   are operator-reachable; required by the one-click launcher mission.
   (`assert_safe_environment` *is* wired — this is control parity, not a
   safety hole.)

Also open: CC-4 (`cycle_duration_ms` max 58.6M ms = clock-drift/suspend
contamination, 250/2,644 samples > 60 s) and CC-5 (`chain_id='robinhood'`
labels 3,635 observations but is not a blockchain — correction touches Lane A
semantics, so reviewed migration only).

**How to continue (Phase 9)**
```powershell
cd G:\robat\ahos
git log --oneline -8               # M9 commits: 629e757 3b0da90 0b878be 1834779 f056256 a9a2820 d2aa09b
.venv\Scripts\python.exe tests\test_prediction_lifecycle_bridge.py   # 6/6
```
- Mission plan order is unchanged; `OWNER_DIRECTIVE_MISSION_PLAN.md` gained an
  "M9 outcome" evidence section. Note the plan's internal numbering drift:
  "M12" means *agents* in the 18:47/18:49 owner order but *paper trading* in
  the original list. **Use the 18:49 order.**
- Nothing in M9 created or enabled an execution surface. PAPER_ONLY held;
  Lane A untouched and re-verified; no secrets read or printed; local commits
  only.

---

### Phase 9.5 + 9.6 (2026-10-03, Claude/Atria, 12:14 Tehran): corrective mission — every finding in two independent reviews closed

Two independent reviews of the local commits landed and were worked through to
exhaustion:

- `reports/grok/reviews/REDTEAM_19_LOCAL_COMMITS_20261002-2313.md` — B1, M1–M4, m1–m7
- `reports/grok/reviews/LOCAL_COMMITS_5_HARDMODE_REVIEW.md` — BL-1..3, MJ-1..13, MN-1..12

**Authoritative record: `reports/grok/reviews/FIX_MATRIX_PHASE9_5_9_6.md`** —
one row per finding id → status → commit → the exact test a reviewer re-runs.
No row is NOT FIXED, PARTIAL, or HUMAN-GATED. Full narrative: handoff
§Phase 9.5 + 9.6.

Commits: `0638643` (9.5) and `8e54953`, `832f0ce`, `6b2e0f6`, `5974da0`,
`e22a154`, `da651af`, `c127f68`, `dbc9125` (9.6). All local; pushes still paused.

**What this changed about the chat control path** (the substance, not the
bookkeeping): identity is server-proven or it is nothing — `isOwner` requires
`id.proven` plus `TELEGRAM_ADMIN_USER_IDS`, and the reader allowlist grants read
only; the client-claimed channel is recorded in the audit as a claim and never
consulted for the decision. An EXECUTING audit record is written before anything
runs and a broken sink aborts the action and burns the code. Confirm codes are
single-use, bound to the identity that proposed them, hashed in the queue, and
rate-limited at 5 guesses. Secrets are redacted globally — summary, title, DB
insert, memory copy, and before Gemini. As of `dbc9125` the audit hashes are
HMAC-SHA256 keyed by a local pepper, so Telegram ids are not brute-forceable and
short commands are not dictionary-reversible.

**Verification state (all exit 0)**

| Check | Result |
|---|---|
| `npx tsc --noEmit -p .` | 0 errors |
| `npm run lint` | 0 problems |
| self-test suites | 15/15, 466 tests, 0 failures |
| `pytest tests/test_chat_control_gate_static.py` | 12 passed |

Suite breakdown: chat-control-gate 131, chat-intent 76, chat-reply-format 48,
dashboard-truth 34, chat-agent 30, canonical-security 19, chat-auth 23,
canonical-read-model 13, dev-missions 14, gemini-egress 13, gemini-phraser 12,
chat-actions 18, chat-handlechat 18, alert-banner 8, web-api-auth 9.

**How to continue (Phase 9.5 + 9.6)**
```powershell
cd G:\robat\ahos
git log --oneline -10   # 9.6: dbc9125 c127f68 da651af e22a154 5974da0 6b2e0f6 832f0ce 8e54953; 9.5: 0638643
cat reports/grok/reviews/FIX_MATRIX_PHASE9_5_9_6.md   # re-run any row's test column
npm run test:chat-handlechat      # 18 — DB-free end-to-end gate harness
npm run test:chat-control-gate    # 131 — includes the MN-1 pepper block
.venv\Scripts\python.exe tests\test_chat_control_gate_static.py   # 12
```

- **Reality-ladder cap for this phase: TESTED.** The two reviews were the
  independent pass; the fixes are pinned by self-tests. A third party re-running
  the matrix's test column is what lifts it to VERIFIED — no claim here says
  that has happened.
- Two failures were hit and fixed in-phase (both recorded in the handoff): the
  append-only static pin tripped on the pepper file's `writeFileSync` (re-scoped
  to `FileAuditSink`, the invariant's real subject, and strengthened with a
  `mode: 0o600` assertion), and a stray `data/.id_pepper` written during tests
  (fixed by pinning `AHOS_ID_PEPPER` in every suite that touches the audit path;
  `data/` is gitignored, so nothing was committed).
- No new execution surface; PAPER_ONLY unchanged; Lane A untouched; no secret
  printed or committed (the masked scan of `5974da0` found 0 hits).

---

1. Blocker A (Claude, GM-01).
2. GM-04 independent review, now including the **Phase 7b owner confirm-gated path** (GM04 doc §8); `/api/engine` token exposure (also lets a token holder claim chat owner via channel `web`); `AHOS_CONTROL_AUDIT_PATH` not in the config scan.
3. Port mismatch: `.env` 3000 vs listener 3500 (OWNER_ACTION).
4. GM-12 review (Credential Manager read path, now IMPLEMENTED read-only).
5. GM-09 runtime wiring (council/router → `guard_provider_call`) not done; the ledger is not seeded.
6. `ahos_runtime_win` container config drift; no scheduled nightly backup task; wall-clock items (T+72h labels not before 2026-10-05 06:24 Tehran; soak nights 2–7).
7. Windows `validate_imports` (Phase 5 run) failed its evidence-mutation check because of a timing artefact. Box runs PASS. Re-run on Windows when the laptop is idle.
8. The bot log warns that no proxy is set; Telegram connects anyway.
9. `tests/test_sqlite_backup_restore.py::test_record_test_run_anchors_relative_executable` fails on Linux only (Windows path). Not a Windows issue.
10. Phase 7: Telegram has no inline confirm buttons (it confirms by text); the pending store and memory are in-process; agent latency is about 5 s; `TELEGRAM_ADMIN_USER_IDS` is empty, so owner = allowlisted chat ids.
11. Phase 8: the dev-mission queue has **no consumer** (no mission controller yet); no live gateway round trip verified this run; `AHOS_DEV_MISSIONS_PATH` is outside the config-validation scan; last-line deletion is invisible to the keyless chain (documented). University and the nine teams remain docs-only; all 19 Slice-1 agents sit below the maturity floor, so M11 needs per-agent evidence before any execution authority.
12. Phase 9 (M9): the paper-trading closed loop has never run — all 19 `paper_trading.sqlite` tables hold 0 rows, so calibration, outcome tracking, the live decision authority, trade-derived learning, and accounting all rest on an empty store. CC-3 (`Tuple` NameError in `debate_council.py`, latent), CC-4 (`cycle_duration_ms` clock-drift contamination), CC-5 (`chain_id='robinhood'` on 3,635 observations), and CC-1 (daemon not routed through `ControlPlane`) are open and recorded in `reports/grok/REMAINING_REALITY_REGISTER.md`. Twelve older readiness maps are bannered STALE; quote the register, not them.

