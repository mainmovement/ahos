# GROK HANDOFF (living document) — for Claude Code

> **Claude: start with [`reports/grok/CLAUDE_CONTINUATION_GUIDE.md`](CLAUDE_CONTINUATION_GUIDE.md)**. It covers Phases 1–9 (Phase 7 = conversational AI with confirm-gated paper commands, owner authority decision 2026-10-02, pending سپهر/قاسم/رضا review; Phase 8 = dev-mission intake + University/agents discovery; Phase 9 = Mission 9 truth baseline + Remaining Reality Register): what was built, where the code lives, exact Windows commands, invariants, process setup, local-only commits (pushes paused), and blocker A.

<!-- PHASE9:START -->
## Phase 9 (2026-10-03, Claude/Atria): Mission 9 — truth baseline + Remaining Reality Register

Owner-directive mission M9, five parts, all complete. **Grok's source, config,
and runtime state were untouched**; every commit is docs, one Lane-B bug fix,
or a previously untracked evidence file. Pushes still paused — local commits
only. Lane A untouched and verified.

### 9a: Test baseline + import side-effect audit (A, B)

- `reports/m9/BASELINE.md` — exact pytest / tsc / eslint / self-test counts
  with the reason for every skip and xfail. Genuine failures were small and
  root-caused with regression tests; nothing was silently quarantined
  (`629e757`).
- `reports/m9/IMPORT_SIDE_EFFECTS.md` — Mandate §12 item 2: 266 modules in
  `architecture/`, `scripts/`, `src/` audited for network / IO / DB / env /
  thread mutation at import time. **0 confirmed** side effects (`3b0da90`).

### 9b: The one real bug found and fixed (FM-007, `0b878be`)

`architecture/learning/prediction_lifecycle.py` hard-coded
`eligible_join_pairs_estimate = 0`, so the census claimed "no
calibration-eligible join" while the live ledger held thousands of eligible
pairs. Root cause: the two stores are separate sqlite connections, so the
obvious cross-DB JOIN is unavailable and the original code silently returned
the sentinel instead of approximating. Fixed by intersecting the two token-id
sets in memory; verified against the live DBs (19 labeled tokens ∩ 20,744
predicted tokens = **10**) and pinned by a new regression test in
`tests/test_prediction_lifecycle_bridge.py` (6/6). Failure Memory entry
FM-007 appended to `reports/FAILURE_MEMORY.md`.

> **This resolves the handoff's unresolved item 7** ("prediction_lifecycle
> census fix — pending owner approval"). The fix is in `0b878be`; re-derive
> live counts with `scripts/calibration_report.py` rather than quoting the
> old `0`. Note the units differ: the census's **10** is distinct tokens; the
> calibration report's **6,037** is (prediction, label) pairs per
> (horizon, event-class). Both are correct.

### 9c: Remaining Reality Register (C) — the new standing authority

`reports/grok/REMAINING_REALITY_REGISTER.md` — the Remaining Capability Graph
per owner directive part1 §76–§80: **33 capability areas** (§1–§33) plus **5
cross-cutting findings** (CC-1..CC-5), each with ladder state, evidence path,
dependencies, proof requirement, and governance gate. Every live count was
re-queried for the register, not quoted from prose.

Read this file before quoting any readiness claim. Where it disagrees with an
older map, **the register wins**. Headline states: discovery pipeline
`OPERATIONAL`; provider fallback, scoring, Lane-A freeze, calibration and
backup/restore `VERIFIED`; paper trading `PARTIAL` (the loop never closed);
scheduler / runtime / identity / decision authority `TESTED`; n8n
`CONTRADICTED`; live trading `ABSENT BY CONSTRUCTION`.

### 9d: Stale-map banners (D)

Twelve historical readiness maps now carry dated STALE / SUPERSEDED banners
pointing at the register, including `AHOS_PROJECT_STATE_MAP.md` (its A–E
taxonomy and its "Verified = re-checked by automated tooling" definition are
exactly what §76 forbids), `reports/PHASE_STATE.md` (its "first live cycle
executed" is contradicted by `paper_exits = 0` and a 100%-empty
`paper_trading.sqlite`), and `reports/G2_MISSION_REPORT_20261002.md` (its
`pre_soak_entry_ok = TRUE` is transitory; the standing
`reports/PRE_SOAK_STATUS.txt` holds `False` with G2/G3/G10 `NOT_VERIFIED`).
`docs/CANONICAL_IMPLEMENTATION_MATRIX.md` was corrected, not only bannered:
two narrative-intel paths fixed to their `architecture/` roots and its summary
recounted by hand (COMPLETE 17 / PARTIAL 10 / BLOCKED_EXTERNAL 3 /
DEFERRED_BY_DESIGN 2 / NOT_IMPLEMENTED 1 = 33 rows; a prior 29 had drifted).
`reports/FAILURE_MEMORY.md` gained FM-001..FM-007; `reports/nightly_backup_series.json`
was committed as tracked (`1834779`) because four canonical docs cite it and a
clean checkout was failing the doc-drift check.

### 9e: Mission-plan notes (E)

`reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md` gained an "M9 outcome" section.
The owner's binding order is **unchanged**; the section records evidence that
affects later missions. Two things in that plan are inconsistent and a future
mission should reconcile them: the original mission list and the 18:47 owner
update disagree on what "M12" means (agents vs paper trading + learning), and
the 18:49 order follows the 18:47 renumbering while the original list was
never renumbered. **Use the 18:49 order; treat the original list as mission
definitions only.**

### Findings the next mission should act on (all dependency-safe, none gated)

1. **Wire `paper_trading/cycle.py:run_full_cycle` into the daemon.** The
   register's single highest-leverage node: it unblocks calibration, outcome
   tracking, the live decision authority, trade-derived learning, and
   accounting — five capabilities, all currently sitting on a 0-row database.
   No new capability needed, no governance gate, no Lane A write.
2. **CC-3** — `architecture/ai/debate_council.py::_risk_manager_evaluation`
   annotates a bare `Tuple` it never imports. One-line fix plus a test; latent
   `NameError`, never triggered because the council has never run on a real
   token.
3. **CC-4** — `cycle_duration_ms` max is 58,621,870 ms (~16.3 h) on a 60 s
   cadence daemon: clock-drift / suspend contamination, not a real cycle. Any
   latency SLO derived from that column must sanitize it first (250/2,644
   samples exceed 60 s).
4. **CC-5** — `chain_id = 'robinhood'` labels 3,635 observations (3.3%);
   robinhood is not a blockchain. Per-chain stats and identity joins must
   treat it as invalid. Correction touches Lane A semantics → reviewed
   migration, not a drive-by fix.
5. **CC-1** — route the daemon through `ControlPlane` so START/STOP/SAFE_HALT
   are actually reachable by an operator. `assert_safe_environment` *is* wired
   into the live loop, so this is operator-control parity, not a safety hole —
   but the one-click launcher mission cannot deliver clean stop/health without
   it.

### Tests run this phase (Windows, all exit 0)

Targeted only, per the per-directory chunking rule: `tests/test_prediction_lifecycle_bridge.py`
6/6 (incl. the new FM-007 regression test), plus the m9 baseline suites
recorded in `reports/m9/BASELINE.md`. The full suite count is in that file,
not re-run wholesale here.

### Security / governance

PAPER_ONLY held. Lane A untouched and re-verified. No execution surface
created or enabled (`NO_EXECUTION_SURFACE` stands). No secrets printed or
written — the Gemini key stayed in Windows Credential Manager `AHOS/ai/gemini`
and was never read. `.cursor/hooks.json`, `*.local-backup`,
`ahos-hooks-local-diff.txt`, and `reports/pgdump_*.sql` were not touched.
No push; no force, reset, rebase, or history rewrite.
<!-- PHASE9:END -->

<!-- PHASE8:START -->
## Phase 8 (2026-10-02, Claude/Atria): dev-mission intake in the chat assistant + University/agents discovery

Mission 8. The previous Phase 8 run died with an API 400 and produced nothing; this run started clean (nothing was reused). Pushes still paused: **local commits only**. Status: IMPLEMENTED / TESTED (self-tests; no live gateway check this run). Not independently verified.

### 8a: dev-mission intake (`d10383e`)

The chat assistant cannot write code. When the owner asks for engineering work (new features, the university, operationalizing agents), it now proposes recording it as a **development mission**, using **exactly the same confirm flow and words as the paper commands**: model or whole-message request → PROPOSAL (Persian summary + one-time 6-char code, 5 min, bound to the proposer's identity) → «تایید <code>» → one line appended to a hash-chained queue with status QUEUED → reply that it is recorded for the engineering team and that **no work is done**. `list_dev_missions` is a read tool showing queued-mission status. Non-owners are refused and audited.

**Files:**
- `dev_missions.ts` (new): `DevMissionStore`, an append-only JSONL queue (schema `ahos.dev_missions.v1`, default `<AHOS data dir>/dev_missions/dev_missions.jsonl`, or `AHOS_DEV_MISSIONS_PATH`). One record per mission: `seq, ts, id (DM-000001), confirmCode, titleFa, summaryFa, status: "QUEUED", channelClaimed, userIdHash, prev_hash, entry_hash`. It reuses `FileAuditSink` (torn-tail isolation, never rewrites), `verifyAuditLines` (edit/deletion/reorder detection) and `hashId` (sender id hashed, never raw) from `chat_control_gate.ts`. Secret-like substrings in the summary are redacted **before** hashing/writing (`redactMissionSecrets`; the marker carries the rule name only — an earlier draft leaked the first 12 chars of the secret into the marker and the self-test caught it). The raw chat message is never stored: `cleanSummaryFa` keeps the owner's own words but strips greetings, zero-width/bidi marks and newlines, and truncates to 280 chars. No status but QUEUED is writable from the chat path, and the module executes nothing.
- `chat_actions.ts`: `ActionKind` gains `dev_mission`; `ActionParams` gains `missionSummaryFa`; `Capability` gains `MISSION_WRITE` (with a deny-by-default refusal text); `propose()` rejects an empty summary (DENIED `EMPTY_SUMMARY`, audited); `ActionDeps` gains `recordDevMission`, bound in `defaultActionDeps()` to `getDevMissionStore().append()`; `handleConfirmation` appends the QUEUED line and audits `PROPOSED → CONFIRMED` (reason `MISSION_QUEUED`). `proposalTextFa` now emits a warm locked intro for dev missions («حتماً! من خودم کد نمی‌نویسم…») and the header «آماده ثبت است (هنوز ثبت نشده)».
- `chat_agent.ts`: new PROPOSE tool `submit_dev_mission{summaryFa}` and READ tool `list_dev_missions`; `runReadTool` takes an optional `ReadToolCtx { missions?, owner? }` — the read tool is owner-only (non-owners get an empty view with a Persian note); the jargon guard now also blocks `submit_*`/`list_*` tool names in answers; the Persian system prompt tells the model it writes no code, may never claim work is done/started, and must answer warmly before proposing.
- `chat_intent.ts`: new conservative `dev_mission` intent (requires BOTH a development topic and an explicit build verb, so complaints and questions do not match). It is the **deterministic fallback** for when the agent is off/circuit-open; when the agent is up it is never reached (the agent answers first).
- `chat.ts`: passes the store into `ChatAgent.run`; deterministic `dev_mission` branch mirrors the `watch_add` pattern (propose or refuse).
- `chat_control_gate.ts`: `canonicalJson` is now exported (reused by `dev_missions.ts` for the hash chain).

**Tests (Windows, all exit 0):**
- tsc 0; eslint 0 on all touched files.
- `npm run test:dev-missions` (new): 14/14 — hash chain and stable ids, empty-summary refusal, greeting/truncation cleaning, secret redaction, hashed sender id, newest-first Persian age labels, tamper detection (edit / delete-first / reorder), the documented keyless-chain limitation (deleting only the last line is invisible; `head_hash` must be anchored outside the file), fail-closed append.
- `npm run test:chat-agent`: 30/30 (was 23; +7 dev-mission cases: warm locked proposal, non-owner denial, empty summary, owner-only queue read, confirm appends exactly once and audits PROPOSED→CONFIRMED, cancel/wrong-identity never queue, system-prompt pins).
- `npm run test:chat-intent`: 72/72 (was 52; +20 Persian dev-mission cases incl. negatives).
- chat-control-gate 126/126, chat-reply-format 40/40, gemini-phraser 12/12, canonical-read-model 13/13; `npm run audit:control-verify` OK.
- pytest static set (`test_chat_control_gate_static`, `test_gemini_chat`, `test_telegram_reply_presentation`, `test_gemini_phraser`, `test_agent_taxonomy_map`): 60 passed, 1 skipped.

**Not done / open:**
- No live gateway POST this run (the gateway was not restarted; hot-reload picks up the TS on the next request). A live end-to-end «دانشگاه رو بساز» → code → «تایید CODE» → queued line is **unverified**.
- The queue has **no consumer**: nothing reads it yet. The future mission-controller layer (M13, "autonomous engineering core", in the mission plan) is the intended reader; the store's own docstring says so.
- `AHOS_DEV_MISSIONS_PATH` is not in any config-validation scan (same as `AHOS_CONTROL_AUDIT_PATH` — pre-existing gap).
- A gateway reload does not lose queued missions (they are on disk), only pending proposals.
- Recorded missions are never shown as done; there is deliberately no DONE/COMPLETED status.

### 8b: University + agents discovery
See `reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md` (new this phase). Read-only; no code changed.
<!-- PHASE8:END -->


<!-- PHASE7:START -->
## Phase 7 (2026-10-02, Grok): conversational AI for Telegram and dashboard (Gemini + tools + confirm-gated paper commands)

**Pushes are still paused by the owner: local commits only.** Status: IMPLEMENTED / TESTED (self-tests and a live gateway check). Not independently verified. **The owner's authority decision of 2026-10-02 changes the GM-04 invariant for owners. It is flagged for سپهر/قاسم/رضا review** (see `GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md` §8).

### 7a: intent router fix (`231e7ac`)
- New pure `chat_intent.ts`: price intent (BTC/ETH/SOL spelling variants, freshness and stale flag, no invented numbers), trade_signal intent (locked PAPER_ONLY policy reply that outranks stop_loss), thanks, greeting-prefix routing, watchlist view checked before watch_add.
- `scripts/chat_intent_selftest.ts`: 52 Persian regression cases (`npm run test:chat-intent`).
- The GM-04 whole-message control detection still runs first.
- 7a is now the **deterministic fallback** under 7b.

### 7b: owner scope change at 17:35. The chat is a real conversational AI.
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
<!-- PHASE7:END -->

<!-- PHASE6:START -->
## Phase 6 (2026-10-02, Grok): Gemini reply phraser behind the ReplyPhraser seam

**Pushes are still paused by the owner: local commits only.** Full continuation notes for Claude: `reports/grok/CLAUDE_CONTINUATION_GUIDE.md`.

### What was built
- **Read-only Windows Credential Manager backend** (owner-approved; GM-12 independent review still pending):
  - `architecture/ai/wincred_reader.py`: CredReadW, `AHOS/ai/*` targets only, buffer zeroed before CredFree.
  - `architecture/ai/credential_store.py`: `WindowsCredentialManagerStore` now reads instead of raising NotImplementedError; adds `CredentialUnavailable`.
  - Details in the GM09 doc, section "Phase 6 update".
- **`architecture/ai/gemini_phraser.py`:** a Python helper run as `python -m architecture.ai.gemini_phraser`.
  - It reads the key in-process from `AHOS/ai/gemini` and calls `generativelanguage.googleapis.com/v1beta/models/<model>:generateContent` with the `x-goog-api-key` header.
  - It tries at most 2 models, with 4 s per attempt and a 9 s total budget.
  - A follow-up attempt is skipped on AUTH, QUOTA or BLOCKED.
  - Errors are classified through `provider_status.classify_provider_error`.
  - The output JSON on stdout carries no key, and a key literal is scrubbed from any error detail.
- **`gemini_phraser.ts`:** `GeminiPhraser implements ReplyPhraser`.
  - It spawns the helper with no shell and fixed argv. The env is minimal (no `DATABASE_URL` or tokens), with `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`. Stdin and stdout are UTF-8.
  - The circuit breaker opens for 60 s after 3 failures, and for 10 min after one AUTH, QUOTA, NO_CREDENTIAL or NOT_WINDOWS failure.
  - Drafts that contain links (news) are skipped.
  - It strips a model-written footer and markdown, then appends the footer itself.
  - `getDefaultPhraser()` is the singleton.
- **`response_composer.ts`:** `phrasedHtml()`.
  - Accepted phrased text is escaped line by line; the only markup is `<b>` on a short title and `<i>` on the footer.
  - Any HTML supplied by the phraser is ignored.
  - `validatePhrased` is unchanged: no new numbers, no jargon, footer exactly once, length limit.
- **`chat.ts`:**
  - The normal-reply `finalizeReply(..., getDefaultPhraser())` call now gets the phraser.
  - **The GM-04 refusal call is still `locked: true` with no phraser.**
  - Evidence gains `phraser {used, rejected, reason, model, latencyMs}`.
- **Config (env):**
  - `AHOS_PHRASER=off` disables the phraser. The default is on, and it falls back to deterministic text if the key or network is missing.
  - `AHOS_GEMINI_MODELS` (default `gemini-flash-lite-latest,gemini-3.5-flash-lite`; at most 2 are used)
  - `AHOS_PHRASER_TIMEOUT_MS` (default 4000)
  - `AHOS_PHRASER_PYTHON`
  - None of these are in `.env`, and `.env` was not edited.

### Tests (self-tests, not independent verification)

**Windows**
- `tests/test_gemini_phraser.py` + `tests/test_ai_provider_status.py`: 78 passed, 2 skipped (two non-Windows-only tests).
- The earlier set with telegram_reply_presentation, chat_control_gate_static and canonical_read_model: 112 passed, 2 skipped.
- npm selftests:

  | Suite | Result |
  |---|---|
  | `test:gemini-phraser` (new) | 12/12 |
  | chat-reply-format | 40/40 |
  | chat-control-gate | 126/126 |
  | web-api-auth | 9/9 |
  | canonical-read-model | 13/13 |
  | canonical-security | 19/19 |
  | alert-banner | 8/8 |
  | dashboard-truth | 34/34 |

- `tsc --noEmit`: 0 errors. eslint: clean.

**Box**
- Full pytest suite: 2636 passed, 3 failed. All 3 failures are pre-existing or environmental:
  - `test_doc_drift` and `test_evidence_package` doc-drift (blocker A)
  - `test_sqlite_backup_restore::...relative_executable` (a Windows path on Linux)
- Phase 6 tests after the timeout tweak: 80 passed.
- `validate_imports`: PASSED.

### Live evidence (laptop, 2026-10-02, Tehran time)
- **Direct helper:** 3 consecutive calls OK, about 1.1 s model latency each.
  - Example: input draft «📊 وضعیت بازار / • بیت‌کوین: ۶۴٬۲۰۰ دلار (۲۴ساعت: +۱٫۲٪) / • اتریوم: ۳٬۱۰۰ دلار / • حال کلی بازار: نامشخص»
  - Output: «وضعیت بازار ارزهای دیجیتال / • بیت‌کوین: ۶۴٬۲۰۰ دلار (۲۴ساعت: +۱٫۲٪) / • اتریوم: ۳٬۱۰۰ دلار / • حال کلی بازار: نامشخص»
  - All numbers were kept. Persian UTF-8 round-tripped intact.
- **Node-spawned helper** (the same runner the gateway uses): 3/3 OK, about 2.0 s end to end (about 0.9 s is Python spawn).
- **The one live gateway smoke** (17:21 Tehran, POST «بازار چه خبر؟» to 127.0.0.1:3500/api/chat):
  - HTTP 200 in 9.3 s, `intent=market`.
  - Evidence: `phraser {used:false, rejected:NO_OUTPUT, reason:NETWORK, latencyMs:7676}`.
  - The deterministic reply was returned correctly (the fallback worked). It wrote the normal 2 chat rows.
  - Cause: the first connection through the owner's local proxy (`127.0.0.1:10809`, registry proxy) stalled for more than 5 s after an idle period. The first direct run showed the same stall; every later run was about 1.1 s.
  - Mitigation committed: 4 s per attempt and a 9 s total budget, so a stalled first attempt leaves a full second attempt. Attempts now record `error_kind` (exception class only).
  - **A phrased reply through the live gateway has NOT been observed yet** (one-smoke limit). Next chat messages will show `evidence.phraser.used`.
- **Processes:** the gateway was not restarted; Next hot-reloaded `chat.ts` and `gemini_phraser.ts`. The bot was not restarted (no Python Telegram change). The owner's own `scripts/store_ai_key.py` process (PID 15216, untracked owner script) was left alone.
<!-- PHASE6:END -->

<!-- PHASE5:START -->
## Phase 5 (2026-10-02, Grok): Telegram/chat reply presentation cleanup (presentation only)

**Pushes are still paused by the owner: local commits only.**

### Trigger

The owner ran the live G11 test (`reports/telegram_e2e/telegram_e2e_20261002T1221Z.md`). Refusals worked and the audit returned CHAIN_OK, but the replies were cluttered:
- internal "GM-04" text
- a news dump instead of a market summary for «بازار چه خبر؟»
- filler text, «0 حکم BUY کانونیکال»
- the engine-off notice on every reply

### What changed (wording and format only)

**No change to:**
- decision, authority or canonical logic
- the GM-04 gate behaviour (it still always refuses; the selftest is unchanged at 126/126)
- data sources
- PAPER_ONLY

**New modules**
- `reply_format.ts` (pure): block model with `renderPlain`, `renderTelegramHtml` and `escapeHtml`.
  - Only http(s) links are kept.
  - Replies are cut at whole blocks within a 3600-character budget, so they stay under 4096 and the HTML stays balanced.
- `chat_replies.ts` (pure): reply builders.
  - Persian labels replace raw enum codes.
  - Missing values show «نامشخص» or a single «داده کافی نیست» note.
  - No internal ids in user text.

**Routing and notices in `chat.ts`**
- `chat.ts` keeps routing; the pinned function names are kept as thin wrappers.
- «بازار چه خبر؟» now routes to **market**: BTC/ETH/SOL price and 24h change first, then the market mood, fear and greed, and data age with a staleness flag. At most 3 Persian headlines follow.
- News: at most 5 items, one line each, original source plus link.
  - Half-translated titles fall back to the original title, with one note.
  - No English summary, importance or classification dump.
- New `stop_loss` intent (presentation routing only): asks which token, shows only the recorded invalidation condition, never invents a number.
- The general fallback is a short "didn't understand" line plus suggestions; the filler text is gone.
- The engine-off notice now appears only for help/greeting, opportunities, health, or questions that mention the engine.
- The footer «تصمیم نهایی با کاربر است.» appears once per reply.

**Refusal text**
- `chat_control_gate.ts`: refusal text shortened to «⛔ … غیرفعال است. … هیچ تغییری اعمال نشد.» with no "GM-04".

**Telegram HTML path**
- `conversation_gateway.ts`, `types.ts` and `app/api/chat/route.ts` add an optional `answer_html` field.
- The dashboard keeps using plain `reply`/`answer`.

**Telegram bot**
- `telegram_ai/service.py` and `bot.py` send `answer_html` with `parse_mode=HTML`.
- They fall back to plain text when the HTML is missing, longer than 4096, or rejected by Telegram (an HTTP 400 parse error).
- Plain text is clamped to 4096 with the footer kept.
- The gateway-unavailable path is unchanged (plain).

### Shared response composer and the future LLM seam

The owner wants to back replies with a free AI model later, using the same style on Telegram and the Windows dashboard. This phase prepares for that without implementing it.

**One composer for every chat surface: `response_composer.ts`**
- Dashboard chat reads `reply` from `/api/chat`; Telegram reads `answer_html`. Both come from the same `finalizeReply()` call in `chat.ts`.

**Pipeline**
1. Verified snapshot / read-model data.
2. `chat_replies.ts` builders turn it into `ReplyBlock[]` (grounded facts only).
3. These become a `GroundedDraft {intent, blocks, footer, locked?}`.
4. `finalizeReply(draft, phraser?)` produces a `ComposedReply {plain, html, composer}`.

**House style**
- `RESPONSE_STYLE_FA` holds the shared rules. It is meant to become the future LLM prompt's style section, so the deterministic output and any LLM output follow the same rules.

**The seam**
- `interface ReplyPhraser { name; phrase(draft, deterministic, style) }`. **None is configured today**, so the deterministic text is final, and `evidence.composer = "deterministic"`.
- A future phraser may only *rewrite the grounded draft*. Its output is accepted only if `validatePhrased()` passes:
  - not empty and within the length limit
  - footer exactly once
  - no jargon (GM-xx / canonical / UNKNOWN)
  - **no number that is not in the deterministic draft**
- Otherwise the deterministic text is used, and the rejection reason is recorded in `phraserRejected`.
- Phraser output is treated as untrusted: its HTML is rebuilt by escaping.
- `locked: true` drafts (the GM-04 refusals) are never rephrased.
- The phraser never decides anything and never sees credentials.

**To add an LLM later (not done)**
1. Implement `ReplyPhraser` using the GM-09 provider status / credential-store interfaces (free model, with a timeout).
2. Pass it into the two `finalizeReply` calls in `chat.ts`, behind an off-by-default flag.
3. Keep the deterministic composer as the fallback.
4. Add evals.
5. Independent review is required before enabling.

### Tests (self-tests, not independent verification)

**npm selftests**

| Suite | Result |
|---|---|
| `test:chat-reply-format` (new) | 40/40: snapshot, escaping, 4096 limit, jargon scan, no fabricated digits when data is missing, stale flag, intent helpers, composer and phraser-seam guard |
| chat-control-gate | 126/126 |
| web-api-auth | 9/9 |
| canonical-read-model | 13/13 |
| canonical-security | 19/19 |
| alert-banner | 8/8 |
| dashboard-truth | 34/34 |

**Other checks**
- `tsc --noEmit`: 0 errors. eslint on the changed files: clean.
- pytest: the new `tests/test_telegram_reply_presentation.py` (11) plus the static, canonical, config, one-brain, all Telegram, engine-import-safety, web-api-auth and dashboard-truth sets: **281 passed, 1 xfailed**.
- `validate_imports --imports-only`:
  - **Box mirror (identical tree): PASSED**, 242 modules, no evidence mutated.
  - **Windows run: FAILED** its evidence-mutation check. That run started at 12:36:10Z. During it, the bot restart created `reports/telegram_e2e/bot_*_20261002T123754Z.log`, the empty logs from the intermediate start were deleted, and two docs were deployed. The check blamed `telegram_ai.envelope`, which writes no files. This is a timing artefact, not an import side effect.
  - The Windows run was not repeated: it takes about 47 minutes under load.

### Runtime

- The gateway (`next dev`, 127.0.0.1:3500) hot-reloaded. Verified with a local POST «توقف»: the new short refusal came back with `answer_html` and the decision was REFUSED. That POST was refused before any DB access; it appended one audit line.
- **Telegram bot restarted (only the bot):**
  - Old PIDs 13096/8500 were stopped with `taskkill` (non-forced; the parent accepted the signal and the child exited with it).
  - The bot was started hidden via `Start-Process`, with `PYTHONIOENCODING=utf-8`, `PYTHONUNBUFFERED=1` (added so the logs are visible) and `AHOS_GATEWAY_URL=http://127.0.0.1:3500/api/chat`.
  - Logs: `reports/telegram_e2e/bot_{stdout,stderr}_20261002T123754Z.log`.
  - An intermediate start at 12:36:39Z (buffered, empty logs) was stopped and its empty logs removed.
- `.env` unchanged.
<!-- PHASE5:END -->

<!-- PHASE4:START -->
## Phase 4 (2026-10-02, Grok): GM-04 conservative capability gate and G11 live-E2E runbook

**Pushes are still paused by the owner: local commits only.** Claude/reviewers: `git log origin/ahos..ahos`.

### What changed

GM-04 was implemented in its capability-reducing form. It **only removes capability**. Status: IMPLEMENTED/TESTED (self-tests only), **PENDING INDEPENDENT REVIEW by سپهر/قاسم/رضا**.

**Start/stop matching**
- `chat.ts` start/stop detection is now **whole-message explicit commands** (`chat_control_gate.ts` `detectControlCommand`).
- "stop loss", "stoploss", "start-up", "restart", "توقف ضرر" never match.
- `paper_buy` needs an explicit phrase; a bare "paper" no longer counts.

**Refusal on `/api/chat`**
- `/api/chat` refuses `start`, `stop` and `paper_buy` for **every** channel, with a Persian reply.
- The client `channel` field is never a grant: it is recorded as `channel_claimed` only.
- `startEngine`/`stopEngine` were removed from `chat.ts`.
- Reason: the chat path cannot prove the local dashboard (shared bearer, client-asserted channel). See the GM04 doc §7.

**Documented dashboard change**
- Dashboard *chat* typing «شروع/توقف/خریدم» is now refused and points to the buttons. It was equally exposed.
- The dashboard **buttons** (`/api/engine`, `/api/paper`) are unchanged. `/api/engine` start/stop now writes an ALLOWED audit line.

**Audit**
- Append-only, hash-chained JSONL with hashed ids and no raw text.
- Location: `data/control_audit/chat_control_audit.jsonl` (override `AHOS_CONTROL_AUDIT_PATH` / `AHOS_DATA_DIR`).
- Verify with `npm run audit:control-verify`.

**Other**
- `conversation_gateway.ts` forwards `channel`/`user_id` into ChatContext, for the audit only.

### Tests (self-tests, not independent verification)

**On Windows (node 24):**
- npm `test:chat-control-gate`: 126/126. Covers:
  - the negative/positive matrix
  - case, fullwidth (NFKC), zero-width, bidi and Arabic-letter variants
  - Persian phrases
  - spoofed channels (web/local/dashboard/null/injection)
  - replay
  - tamper and deletion detection
  - torn tail
  - sink failure staying fail-closed
- Other npm selftests:

  | Suite | Result |
  |---|---|
  | web-api-auth | 9/9 |
  | canonical-read-model | 13/13 |
  | canonical-security | 19/19 |
  | alert-banner | 8/8 |
  | dashboard-truth | 34/34 |

- `tsc --noEmit`: 0 errors. eslint on the changed files: clean.
- pytest: `test_chat_control_gate_static` plus the canonical, config, one-brain, Telegram (offline harness / adapter / service / launcher / ai / conversational / html / NLU matrix), engine-import-safety, web-api-auth and dashboard-truth sets: **271 passed, 1 xfailed**.
- `scripts/validate_imports.py --imports-only`: **VALIDATION PASSED** (242 modules, no evidence mutated).

**On the box (python 3, bun):** the same pytest sets gave 250 passed, 1 xfailed (subset without canonical/config). The selftest also ran under bun: 126/126.

### Files

| Status | Files |
|---|---|
| New | `chat_control_gate.ts`, `scripts/chat_control_gate_selftest.ts`, `scripts/verify_control_audit.ts`, `tests/test_chat_control_gate_static.py`, `reports/grok/G11_LIVE_E2E_RUNBOOK.md` |
| Modified | `chat.ts`, `conversation_gateway.ts`, `app/api/engine/route.ts`, `package.json`, GM04 doc, MISSION_DISCOVERY |

### Runtime

- No `run_bot.py` is running.
- The gateway (`next dev`, 127.0.0.1:3500) hot-reloads `chat.ts`.
- Live E2E: **OWNER_ACTION_REQUIRED**. Follow `reports/grok/G11_LIVE_E2E_RUNBOOK.md`. Its port override is the bot-session `$env:AHOS_GATEWAY_URL="http://127.0.0.1:3500/api/chat"`; `service.py` ignores `AHOS_GATEWAY_PORT`. `.env` is unchanged.

### Residuals for review

1. Any holder of `AHOS_WEB_API_TOKEN` can still call `/api/engine` (GM-04 phase 2: loopback check / second secret).
2. The chat `watch` intent (watchlist write) is ungated (out of scope).
3. `AHOS_CONTROL_AUDIT_PATH` is not in the config-validation scan list.
4. Blocker A (`test_doc_drift`, Claude) is unchanged.
<!-- PHASE4:END -->

<!-- PHASE3:START -->
## Phase 3 status (Grok, 2026-10-02, foundation missions): read this first

**PUSHES ARE PAUSED BY OWNER INSTRUCTION (2026-10-02 14:52 Tehran).** Everything after `a6638bf` exists **only as local commits** on branch `ahos` in `G:\robat\ahos`; none of it is on GitHub. Claude: review these with `git log origin/ahos..ahos`. Do not assume `origin/ahos` is current, and do not push them yourself unless the owner says so.

Same constraints as Phase 2. Every commit was preceded by a fetch with fast-forward only and staged by explicit path. P3-M1 (`a6638bf`) was pushed and checked for HEAD == @{u}. Later commits are local only.
- PAPER_ONLY.
- Lane A frozen.
- Canonical Decision Authority untouched.
- Hooks overlay and `ahos-guard.py` untouched.
- None of Claude's files touched.
- No `.env` edits.
- No Postgres writes.
- No service started or stopped.

Self-tests are **not** independent verification. The reality ladder for each item is in `reports/grok/PHASE3_ARCHITECTURE_NOTE.md`.

Blocker A (for Claude) is still open. See the Phase 2 note below.

| Mission | Status | Ladder | Commit |
|---|---|---|---|
| P3-M1 tsconfig exclude `docs/archive` | IMPLEMENTED_VERIFIED (self-tests) | TESTED | `a6638bf` (pushed) |
| GM-08 mission/engineering ledger | IMPLEMENTED_VERIFIED (self-tests) | IMPLEMENTED + TESTED (not INTEGRATED) | `d1571c4` (local, not pushed) |
| GM-09 AI provider status model | IMPLEMENTED_VERIFIED (offline self-tests); credential store interface only; Windows Credential Manager backend DESIGN_ONLY | IMPLEMENTED + TESTED (not INTEGRATED) | local commit adding `architecture/ai/provider_status.py` (not pushed) |

### P3-M1: tsconfig
- `tsconfig.json`: `"docs/archive"` was added to `exclude`. That is the only change.
- `tests/test_tsconfig_archive_exclusion.py` checks two things: the exclusion and the existing excludes are still present, and no live TS file imports from `docs/archive`. The negative check was confirmed: a planted import makes the test fail.
- Evidence (Windows, node 24):
  - Before and after, `tsc --listFilesOnly` differs by exactly 7 files, all under `docs/archive/consolidation_2026-09-26/ahos022_divergent/`. No other file changed.
  - `tsc --noEmit`: exit 0, **0 errors** (it was 9).
  - npm selftests: web-api-auth 9/9, canonical-read-model 13/13, canonical-security 19/19, alert-banner 8/8, dashboard-truth 34/34.
  - pytest: tsconfig + canonical_decision_authority, 31 passed.

### GM-08: mission/engineering ledger (`architecture/mission/ledger.py`, CLI `scripts/mission_ledger.py`)
- **Inspected first; no duplicates created:**
  - `scripts/execution_state.py` (M5) is a read-only session-start state recorder. It is not a mission ledger.
  - `ahos_org/audit.py` + `ahos_org/tasks.py` are the hash-chained audit and task lifecycle of the org *policy model*. The ledger reuses their hash convention (sha256 over canonical JSON, a genesis hash of 64 zeros), but does not import from or extend governance.
  - No other ledger, checkpoint or resume code exists.
  - The four agent taxonomies are **referenced, not merged**. `CURRENT_AGENT` must be namespaced as `engineering:*`, `agent:*`, `AG:*`, `AGENT:*`, `agent.org:*` or `M0:*`, and a bare "01" is rejected. Every entry carries `agent_taxonomy_ref = docs/governance/agent_taxonomy_map.json`.
- **Storage:**
  - A local append-only JSONL at `<AHOS data dir>/mission_ledger/mission_ledger.jsonl`, written with O_APPEND + fsync. Database paths are refused.
  - No existing DB is read or written.
  - Resolving the default path creates nothing. The ledger has **not** been seeded on the laptop, so no file exists yet.
- **Fields:** the 13 required fields. Each line is a full state snapshot; unknown fields are rejected.
- **States:** PENDING, RUNNING, PAUSED, WAIT_FOR_AI, BLOCKED, RESUMED, COMPLETED_UNVERIFIED, FAILED, CANCELLED, with a legal-transition table.
  - There is **no DONE or COMPLETED state**. Verification goes in LAST_VERIFICATION.
  - Terminal states cannot be reopened.
- **Checkpoint and resume:**
  - `checkpoint()` stores up to 64 KB of JSON.
  - `pause()` moves to PAUSED, WAIT_FOR_AI or BLOCKED.
  - `resume()` returns the stored checkpoint unchanged and cannot reset it.
  - `start()` refuses an existing id, so a mission is never restarted from zero.
  - After a crash: `resume(crash_recovery=True)`.
  - A torn final line (crash mid-write, including a record cut just before its newline) blocks appends until `recover_torn_tail()` appends a hashed acknowledgement of the torn line's sha256. Nothing is rewritten, and the unconfirmed write is not trusted.
- **Tamper evidence:**
  - `seq` + `prev_hash` + `entry_hash` detect a modified, re-hashed, deleted, swapped, duplicated, blank or garbage line. The ledger never appends onto a broken chain.
  - Limit: a keyless chain cannot detect a *whole-file* rewrite. Record `head_hash` externally and check it with `verify(anchor_hash=...)` or the CLI `--anchor`; this is tested.
- **Secrets:**
  - Secret-looking content in keys and values is redacted **before hashing**. Covered patterns: OpenAI/Anthropic/xAI/Groq/GitHub/Google/AWS/Slack keys, Telegram tokens, JWTs, EVM keys, URL credentials, Bearer tokens, `*_KEY=`/`password:` assignments, and PEM private keys. Redaction is idempotent.
  - `strict=True` rejects the write instead, and writes nothing.
  - A secret-looking MISSION_ID is refused.
  - Over-redaction of benign `token=...` text is possible by design.
- **Not an authority:**
  - `authority: "NONE"` on every entry.
  - Static tests confirm the ledger imports no decision, trading or telegram code, and that nothing in decision/risk/positions/scoring/paper_trading/discovery/engine imports it.
- **Tests:** `tests/test_mission_ledger.py`, 72 cases.
  - Box: 72 passed.
  - Box regression set (architecture graph, zero-money, config validation, boundaries, architecture_p1, engine import safety, agent taxonomy, phase12): 183 passed, 1 xfailed.
  - Box `validate_imports`: PASSED.
  - Windows: `test_mission_ledger` + `test_agent_taxonomy_map`: 92 passed (72 + 20).
- **Next:** wire GM-09 provider status into the ledger (pause with a checkpoint). Optionally, Claude and Grok record missions here.

### GM-09: AI provider status + credential-store abstraction (details: `reports/grok/GM09_PROVIDER_STATUS_AND_CREDENTIAL_STORE.md`)
- **Inspected first:**
  - `architecture/ai/clients.py` (`AIResponse`: OK, DOWN, NO_KEY, SKIPPED_PAID) and `architecture/ai/router.py`.
  - The market-data provider statuses (`types.ts` `PROVIDER_STATUSES`, `architecture/providers`) are a separate vocabulary and were **not changed**.
  - GM-09 is additive.
- **`architecture/ai/provider_status.py`:**
  - The seven-state `AIProviderStatus` and `classify_provider_error`: 401/403 → AUTH_FAILED (geo 403 → BLOCKED); 402/429/quota text → QUOTA_EXHAUSTED (an explicitly transient 429 → DEGRADED); 404/model text → MODEL_UNAVAILABLE; 5xx/timeout/network → UNAVAILABLE.
  - `classify_ai_response` for the existing envelopes.
  - `safe_provider_call`: an outage never crashes the runtime.
  - Error detail is redacted.
- **`architecture/ai/credential_store.py`:**
  - The interface has no raw getter. `SecretValue` never prints its value and cannot be pickled.
  - Null and Fake stores.
  - `WindowsCredentialManagerStore` = DESIGN_ONLY: it refuses every access and imports nothing OS-level.
  - The Persian new-key message tells the owner to use Credential Manager target `AHOS/ai/<provider>`, and never to paste the key in chat, Telegram or .env.
- **`architecture/ai/mission_guard.py`:**
  - QUOTA_EXHAUSTED / AUTH_FAILED → the ledger mission is PAUSED with its checkpoint kept and an owner message is returned.
  - Outage → WAIT_FOR_AI.
  - READY → RUNNING.
- **Tests:** `tests/test_ai_provider_status.py`, 64 cases.
  - Fake providers and fake transports only, with a socket guard.
  - Box: 64 passed. AI/provider regression set: 327 passed, 1 xfailed. `validate_imports`: PASSED.
  - Windows: GM-09 + ledger + ai_council_live + ai_router_and_debate + provider_abstraction: 168 passed. `validate_imports --imports-only`: PASSED.
  - Mutation checks: disabling the credential-pause branch makes 4 tests fail; removing redaction makes 1 fail.

### Remaining blockers (Phase 3)
1. **Blocker A** (Claude): two untracked artifacts are cited by canonical docs, so `test_doc_drift` fails on a clean checkout. Unchanged.
2. **Pushes paused** (owner instruction). Commits `d1571c4` and the GM-09 commit exist only locally.
3. GM-04 still waits for security review. That includes the `stop` regex false positive.
4. The gateway port choice is OWNER_ACTION (.env says 3000, the listener is on 3500). G11 live Telegram E2E is OWNER_ACTION.
5. The Windows Credential Manager backend needs owner + security review (GM-12) before any OS credential access. GM-09 runtime wiring (calling `guard_provider_call` from the council or router) is not done.
6. Wall-clock items are unchanged.

### Next recommended missions
- Wire `guard_provider_call` / `classify_ai_response` into `LiveCouncil` as advisory status reporting.
- Seed the ledger with real Claude and Grok missions; record `head_hash` in the handoff.
- GM-12 review.
- GM-04 implementation after review.
- GM-01 (Claude).
<!-- PHASE3:END -->

<!-- PHASE2:START -->
## Phase 2 status (Grok, 2026-10-02, implementation): read this first

**Note for Claude about blocker A (still open, not touched by Grok):** your commit `25b33cc` makes the canonical docs cite `reports/nightly_backup_series.json`. That file is **untracked** in the working tree on this laptop. `scripts/doc_drift.py::_exists` checks the working tree, so the test passes here.

**Confirmed in Phase 2:** on a clean clone of `origin/ahos` (Grok's box), `tests/test_doc_drift.py::test_canonical_docs_have_zero_real_stale_refs` **FAILS** with 2 stale references in `AHOS_GAP_REGISTER.md`:
1. `reports/nightly_backup_series.json` (25b33cc)
2. `reports/validate_imports_run_20260928T045640Z.json`, cited since `7ebea7a` (M-GAP-037). It is also untracked (`??`) on the laptop.

You need to choose one fix (GM-01):
- (a) commit both artifacts, or
- (b) give doc_drift "exists-but-untracked" semantics or an exemption.

Grok has not touched `scripts/doc_drift.py`, the artifacts, `AHOS_GAP_REGISTER.md`, or any of your dirty or untracked files.

Constraints held in every Phase 2 commit:
- PAPER_ONLY.
- Lane A frozen.
- Canonical Decision Authority untouched.
- `.cursor/hooks.json` overlay and `ahos-guard.py` untouched.
- `.env` and the pgdump file not committed.
- No secrets.
- No DB writes.
- No service started or stopped.
- Files staged by explicit path only.

Self-tests are **not** independent verification.

| Mission | Status | Commit |
|---|---|---|
| GM-02 Telegram offline edge harness | IMPLEMENTED_VERIFIED (offline/self-test only); live E2E = LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED | `552eda7` |
| GM-03 dashboard truthfulness | IMPLEMENTED_VERIFIED (self-tests; presentation only; browser view not visually checked) | `789dfa2` |
| GM-05 gateway port single source + diagnosis | IMPLEMENTED_VERIFIED (self-tests + one real read-only diagnosis run); port choice = OWNER_ACTION_REQUIRED | `06e44e6` |
| GM-06 n8n validator + ahos_03 quarantine | IMPLEMENTED_VERIFIED (static self-tests); ahos_03 QUARANTINED (file kept) | `8e48cf3` |
| GM-04 Telegram control capability gate | DESIGN_ONLY: `reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`, awaiting security review (سپهر/قاسم/رضا) | the docs commit that adds that file |

### GM-02: what changed
- `telegram_ai/envelope.py` (new, pure, no network or authority imports):
  - versioned update envelope `ahos.telegram.update_envelope.v1`
  - `hash_identifier` (sha256 prefix)
  - `redact_envelope` (removes raw chat_id/user_id)
  - `ReplayGuard` (bounded LRU of update_ids: ACCEPT / DUPLICATE / INVALID)
  - `TelegramAuditLog` (in-memory, plus an optional append-only JSONL; hashed ids, length and sha of the text, **never raw text**)
- `telegram_ai/bot.py`:
  - new optional `replay_guard` and `audit_log` constructor arguments. Defaults keep the old behaviour, plus a default in-memory guard and log.
  - Duplicate and invalid update_ids are rejected before auth, rate-limit or gateway are touched.
  - Every exit path is audited: PROCESSED, UNAUTHORIZED, RATE_LIMITED, DUPLICATE_REJECTED, INVALID_UPDATE_REJECTED.
  - The context passed to the service now carries `user_id`. This fixes the empty `user_id` that `service.py:84` forwarded to the gateway; `service.py` itself is unchanged. The caller's dict is not mutated.
- `telegram_ai/adapter.py`: `MockTelegramAdapter` update_ids are now monotonic. Before this, ids restarted at 1 after a poll, which the new replay guard would have rejected.
- `tests/test_telegram_offline_harness.py` (new): 20 test functions, 28 cases.
  - Covers the end-to-end path MockTelegramAdapter → TelegramBotRunner → TelegramDomainService → stub HTTP gateway on 127.0.0.1 (no proxy, no credentials).
  - Checks: envelope contract, sender identity in the gateway body, fail-closed empty allowlist, unauthorized rejection with no gateway call, rate-limit, duplicate and invalid update_id rejection, audit with no raw text and no raw ids, JSONL append-only, offline fallback when the gateway is down, non-PAPER mode not echoed.

### GM-02: tests (Windows `.venv` Python 3.11.9, plus box)
- Telegram suites + `test_run_bot_launcher` + `test_engine_import_safety`: **203 passed, 1 xfailed** (Windows, 255 s; same on box).
- `validate_imports.py --imports-only`: PASSED on Windows. Full `validate_imports.py` PASSED on box (pre-existing orphan warnings only).
- Mutation checks:
  - removing identity propagation → 2 harness tests fail
  - disabling the replay check → 9 fail

### Current reality / blockers / next
- Live Telegram E2E (G11) stays **LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED**. The running bot only picks this up after the owner restarts it; Grok restarted nothing.
- The Telegram → `chat.ts` start/stop free-text control leak is **still open**. See GM-04 (design only).
- Next: GM-03.

### GM-03: what changed (presentation only, no authority)
- `dashboard_truth.ts` (new, pure, no imports):
  - `freshnessStatus`: OK only for a real timestamp within the limit. Missing, NaN or a >1 min future timestamp → UNKNOWN; too old → STALE.
  - `evidenceFreshnessLimitMs`: the larger of 10 min and 3× the engine interval.
  - `executionModeStatus`: PAPER_ONLY → OK, any other value → VIOLATION, empty → UNKNOWN.
  - `paperPortfolioStatus` and `lastCycleStatusHealth`.
  - `deriveViewTruth`: stale on refresh error, a snapshot older than 90 s, or no snapshot.
  - `presentStatus`: a green status becomes STALE when the view is stale.
  - `presentRunning`: UNKNOWN when stale.
- `snapshot.ts`:
  - The hard-coded `"OK"` for پورتفوی کاغذی and صفرپولی (formerly `:161,163`) is gone. Both now derive from the persisted `state.executionMode`.
  - امنیت داده and تازگی شواهد now use the freshness limits.
  - The other dimensions are unchanged.
- `CommandCenter.tsx`:
  - A 15 s clock re-evaluates freshness without a fetch.
  - `bootError` is cleared only after a successful fetch.
  - A red STALE banner shows when a refresh failed or the snapshot is old.
  - The run pill says "وضعیت نامعلوم — STALE" instead of "running".
  - Health pills go through `presentStatus`; VIOLATION renders red.
- `scripts/dashboard_truth_selftest.ts` (new) and npm script `test:dashboard-truth`; `tests/test_dashboard_truth_static.py` (new, wiring pins).

### GM-03: tests (Windows, node 24 / Python 3.11.9)
- `npm run test:dashboard-truth`: 34/34 pass.
- Exit 0: `test:web-api-auth`, `test:canonical-read-model`, `test:canonical-security`, `test:alert-banner`.
- `npx eslint` on the changed files: exit 0.
- `tsc --noEmit`: exit 2, but **all 9 errors are pre-existing ones under `docs/archive/consolidation_2026-09-26/ahos022_divergent/`**. There are 0 errors outside docs/archive. Known debt, not caused by GM-03.
- pytest `test_dashboard_truth_static` + one_brain + alerts_web_banner + canonical_decision_authority + canonical_read_model + web_api_auth_gate: **87 passed**.
- Adversarial: the selftest covers future timestamps, NaN or empty timestamps, the refresh-error-with-fresh-snapshot case, green→STALE, VIOLATION not masked, and non-green statuses passing through unchanged.
- Not verified: how the page actually renders in a browser (no service restart, no screenshot). The Next dev server hot-reloads on its own.
- Next: GM-05.

### GM-05: what changed (non-breaking option; `.env` NOT edited; 3000 NOT mass-replaced)
- `scripts/gateway_port.py` (new, stdlib only, read-only):
  - `resolve_gateway`: precedence is `AHOS_GATEWAY_URL` > `AHOS_GATEWAY_PORT` > `http://127.0.0.1:3000/api/chat`.
  - It warns on an invalid port, on a port that disagrees with the URL, and on an unparseable URL.
  - `diagnose` probes loopback ports only (the configured port plus `AHOS_GATEWAY_CANDIDATE_PORTS`, default 3000,3500). Verdicts: `CONFIGURED_PORT_LISTENING`, `CONFIGURED_PORT_NO_LISTENER` (with an OWNER_ACTION hint), `NO_GATEWAY_LISTENING`, `NON_LOCAL_URL_NOT_PROBED`.
  - CLI: `--json`, `--url-only`, `--env-file`. It never writes anything.
- `scripts/operator_validation_gate.py`:
  - G2's default URL comes from the resolver.
  - `AHOS_GATEWAY_PORT` is loaded from .env.
  - When G2 is not PASS, a `gateway_port_diagnosis` is attached. The **status is unchanged**.
  - The historical .env persistence of the 3000 default happens only when source = DEFAULT, never for a port override.
- `scripts/windows_run_operator_gate.ps1` (BOM and CRLF preserved; parser: 0 errors):
  - It now uses `gateway_port.py --url-only` (same resolution), falling back to 3000.
  - It persists via the ensure script only when no port override is set.
  - It prints the read-only diagnosis.
- `tests/test_gateway_port.py` (new): 26 cases.

### GM-05: tests and real diagnosis
- Windows: `test_gateway_port` + `test_operator_validation_gate` + `test_web_api_auth_gate` + `test_phase18_launchers`: **110 passed**. `validate_imports --imports-only`: PASSED.
- Real run on the laptop, read-only (.env hash unchanged before and after):
  `verdict=CONFIGURED_PORT_NO_LISTENER`, `listening_candidates=3500`. So .env says 3000, and the gateway is actually listening on 3500.
- Mutation checks (each made one test fail):
  - hard-coding 3000 back in G2
  - removing the loopback-only guard
- **OWNER_ACTION_REQUIRED:** choose one:
  - (a) restart the gateway on 3000, or
  - (b) set `AHOS_GATEWAY_PORT=3500` (or `AHOS_GATEWAY_URL`) yourself.

  Grok edited no `.env` and restarted nothing.
- Next: GM-06.

### GM-06: n8n governance rules and ahos_03 quarantine (details: `reports/grok/GM06_N8N_QUARANTINE.md`)
- `tests/validate_n8n.py` gains `governance_findings`. These rules are **errors**:
  - AUDIT_TAMPER (DELETE, TRUNCATE or UPDATE on `agent_audit_trail`)
  - AUTHORITY_BYPASS (`UPDATE trade_decisions … execution_status`)
  - SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER (`{{ }}` in SQL in a telegram, webhook, form or chat triggered workflow)

  These are **warnings**:
  - SQL_INTERPOLATION (internal schedule workflows)
  - DECISION_WRITE_OUTSIDE_CANONICAL_AUTHORITY (`INSERT INTO trade_decisions`)
- `QUARANTINED_WORKFLOWS` = {`ahos_03_telegram_control.json`}, matched by exact filename only. For that file the errors become `QUARANTINED <rule>` warnings, and the CLI prints `[QUARANTINED(do-not-import)]`. G12 stays `STRUCTURAL_VALID` (exit code unchanged). **The file is not deleted or edited.**
- `docs/N8N_OPERATIONAL_PROCEDURE.md`: quarantine banner, and import step 2 now excludes quarantined workflows.
- Tests: `tests/test_n8n_governance_rules.py` has 24 cases, covering positives, benign negatives, disabled nodes, the look-alike filename, ahos_03 failing once un-quarantined, and the CLI.
  - Box: 24 + `test_validate_n8n_utf8` + `test_operator_validation_gate` + `test_ahos -k n8n` all pass.
  - Windows results are in the next commit message / final report.
- Finding: `ahos_02_signal_pipeline.json` has a node **`Record PENDING (LIVE)`** that INSERTs into `trade_decisions`, plus SQL interpolation on an internal schedule. It produces warnings only, and the workflow is dormant (0 imported). Review it before any import.
- Next: GM-04 design doc (`reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`) for review by سپهر/قاسم/رضا.

### GM-04: design only (no code)
- Proposal: `reports/grok/GM04_TELEGRAM_CONTROL_CAPABILITY_GATE_PROPOSAL.md`.
  - an intent → capability map
  - default deny of start/stop/paper_buy from remote channels
  - the body-asserted `channel` is not trusted (two options for reviewers)
  - an optional admin principal plus a single-use confirmation nonce
  - word-boundary intent hardening
  - append-only audit with hashed ids
  - the canonical authority is untouched
- New adversarial finding recorded there: the `chat.ts` `stop` regex `/(توقف|استاپ|stop|خاموش)/` has **no word boundary**, so a message containing "stop loss" or "stoploss" stops the engine (T2). The fix is waiting for the GM-04 review; nothing has been changed.

### Remaining blockers (end of Phase 2)
1. **Blocker A** (Claude): 2 untracked artifacts are cited by canonical docs, and `test_doc_drift` fails on a clean checkout. See the note at the top of this file.
2. Telegram start/stop control leak and the `stop`-substring false positive. Status: DESIGN_ONLY (GM-04), awaiting review.
3. Gateway port: .env says 3000, the listener is on 3500. OWNER_ACTION_REQUIRED (restart on 3000, or set AHOS_GATEWAY_PORT/URL).
4. G11 live Telegram E2E: LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED.
5. `tsc --noEmit` has 9 pre-existing errors under `docs/archive/.../ahos022_divergent/`. Suggestion: exclude `docs/archive` in tsconfig (small and separate; not done).
6. ahos_02 `Record PENDING (LIVE)` node needs review before any n8n import.
7. Wall-clock items unchanged: T+72h labels not before 2026-10-05T02:54Z (06:24 Tehran); soak and nightly backup nights 2–7.

### Next recommended missions
- GM-01 (Claude's call: blocker A).
- GM-04 implementation after review.
- tsconfig exclusion of `docs/archive` (tiny).
- GM-08 (mission ledger schema).
- GM-09 (provider QUOTA_EXHAUSTED state).
- GM-07 after owner approval.

### May Claude safely continue?
**YES.**
- Grok's Phase 2 commits touch only these paths: `telegram_ai/{envelope,bot,adapter}.py`, `dashboard_truth.ts`, `snapshot.ts`, `CommandCenter.tsx`, `package.json` (+1 script), `scripts/{gateway_port.py,dashboard_truth_selftest.ts,operator_validation_gate.py,windows_run_operator_gate.ps1}`, `tests/{validate_n8n.py,test_telegram_offline_harness.py,test_dashboard_truth_static.py,test_gateway_port.py,test_n8n_governance_rules.py}`, `docs/N8N_OPERATIONAL_PROCEDURE.md`, `reports/grok/*`.
- None of your dirty or untracked files were touched.
- Fast-forward `origin/ahos` before your next commit.
<!-- PHASE2:END -->

> Below: Phase 1 handoff (2026-10-02 10:36Z), kept for history.


| Field | Value |
|---|---|
| Timestamp (UTC) | 2026-10-02T10:36Z (14:06 Tehran) |
| Agent | Grok (parallel Autonomous Engineering / Research agent), Phase 1 = reality inspection + mission discovery |
| Mission IDs | GROK-P1-20261002 (inspection); discovered GM-01 … GM-12 (see MISSION_DISCOVERY_2026-10-02.md) |
| Branch | `ahos` |
| Upstream | `origin/ahos` (not origin/main) |
| Starting HEAD | `25b33cceb280b5b3d67bf37586500ba297bdb65f` (== origin/ahos, 0 ahead / 0 behind after `git fetch origin`) |
| Ending HEAD | the single Grok docs commit that adds this file (parent `25b33cc`); message `docs(grok): session 2026-10-02 reality inspection, mission discovery, handoff [PAPER_ONLY]`. If absent from `git log`, the commit/push did not happen — see final Grok report |
| origin/main | `8ae411a` (ahos is 30 ahead / 2 behind main; not merged, not touched) |

## Files changed by Grok
Added only (new files):
- `reports/grok/GROK_SESSION_2026-10-02_REALITY_INSPECTION.md`
- `reports/grok/TELEGRAM_REALITY_MAP.md`
- `reports/grok/DOCKER_N8N_DEPENDENCY_MAP.md`
- `reports/grok/DASHBOARD_ONECLICK_REALITY.md`
- `reports/grok/MISSION_DISCOVERY_2026-10-02.md`
- `reports/grok/GROK_HANDOFF.md`

NOT changed / NOT staged: all source, `.env`, `.cursor/hooks.json` (+ `.local-backup`, `ahos-hooks-local-diff.txt`), Claude's modified `reports/backup_restore_drill.json`, `reports/month1_failure_matrix.json`, `reports/reliability_matrix.json`, Claude's ~40 untracked `reports/*` evidence files, `next-env.d.ts`. No service/container/gateway started, stopped, or restarted. No DB writes (one read-only psql session with `default_transaction_read_only=on`).

## Tests run (all exit 0)
- pytest cognitive set + test_doc_drift: 117 passed (448.7 s)
- pytest Telegram set + test_engine_import_safety: 150 passed, 1 xfailed (387.4 s)
- npm: canonical-read-model 13/13, canonical-security 19/19, web-api-auth 9/9, alert-banner 8/8
- `validate_imports.py --imports-only`: PASSED (236 modules)
- `freeze_lane_a.py` verify: OK (36 files)
Interpreter: `.venv\Scripts\python.exe` (Python 3.11.9).

## Runtime evidence (~10:10–10:34Z)
- Gateway: node PID 13120 LISTEN 127.0.0.1:3500 (manual `npm run dev -- -p 3500`), GET / 200. Port 3000 free.
- Docker Desktop + WSL2 running; `ahos_postgres_win` healthy (pg_isready OK); `ahos_runtime_win` unhealthy (5 s healthcheck timeout, stale container config); `ahos_n8n_win` up, **0 workflows imported**.
- VHDX backups re-hashed by Grok: ext4 + docker_data both match recorded SHA256.
- Nightly backup night 1/7 verified (spot hash); **no scheduled task exists**.
- Native `start_ahos.bat` daemon not running; container `python3 -m architecture.runtime` is the only observer writing `data/` via bind mount.

## Unresolved issues / known regressions
1. **KNOWN REGRESSION (STRONGLY INDICATED): 25b33cc + untracked `reports/nightly_backup_series.json`** — `scripts/doc_drift.py::_exists` checks the working tree; the artifact is untracked (not ignored); canonical docs cite it (`AHOS_GAP_REGISTER.md:24`, `AHOS_LOCAL_ACTIVATION_CHECKLIST.md:131`, `AHOS_OPERATOR_QUICKSTART_WINDOWS.md:206`, `AHOS_SOAK_OPERATOR_START.md:151`). Clean checkout/CI → `test_canonical_docs_have_zero_real_stale_refs` fails. Claude: decide commit-the-artifact vs exemption (GM-01). Grok did not touch it.
2. Telegram → gateway can trigger `startEngine/stopEngine` by free-text regex (`chat.ts:233-234`, `:43-48`) with no capability check/audit; sender `user_id` is sent empty (`telegram_ai/service.py:84`).
3. n8n `ahos_03_telegram_control.json`: SQL interpolation, audit-row DELETE on `/reset`, `/approve` writes `trade_decisions.execution_status` bypassing canonical authority. Dormant (not imported) but target tables exist. Do not import.
4. Dashboard stale-READY: after a successful load, a failed poll keeps old green health (`CommandCenter.tsx:304-306`).
5. Port: `.env:99` = 3000, running gateway = 3500, no tracked reference to 3500; ~40 repo refs to 3000. Not a one-line script drift.
6. `ahos_runtime_win` config drift (created 2026-08-28; healthcheck enabled; port 18000 vs compose 8000).
7. `prediction_lifecycle.py:326` hard-coded `eligible_join_pairs_estimate=0` (Claude finding, Lane B) — pending owner approval.
8. M0 audit report file not found in repo or `G:\AHOS_FORENSIC_REPORT`; Gate 4 cache report not present.
9. `reports/pgdump_ahos_chat_messages_20261002T002200Z.sql` contains operator chat rows — privacy review before anyone commits it.

## OWNER_ACTION items
- G11 Telegram live E2E (archive `reports/telegram_e2e_<UTC>.md`).
- Canonical gateway port decision (restart on 3000, or edit `.env:99` to 3500).
- Scheduled task for nightly backups (nights 2–7) or manual nightly runs.
- Recreate `ahos_runtime_win` from committed compose (service restart).
- Approve `prediction_lifecycle` census fix; decide single runtime owner (container vs native daemon).
- Cleanup of exited legacy containers (`AHOS-N8N`, `ahos-postgres`, `ahos-redis`) — deletion.

## Wall-clock dependencies
- T+72h outcome labels: not before 2026-10-05T02:54:19Z (T0 2026-10-02T02:54:19Z).
- Soak / nightly backup nights 2–7: one per calendar night (2026-10-03 … 2026-10-08 at the earliest).
- Calibration sufficiency: NOT proven; never report CLOSED.

## Security / governance
- Lane A untouched and verified; Canonical Decision Authority untouched; PAPER_ONLY held; no secrets printed or written (Telegram token = CREDENTIAL_PRESENT_BUT_REDACTED; leak scan: 0 real hits, 1 synthetic fixture `tests/test_engine_import_safety.py:101`; git history not scanned).
- `.cursor/hooks.json` failClosed guard (`ahos-guard.py`) preserved, not modified.
- No Credential Manager abstraction exists (DESIGN_ONLY).

## Next recommended mission
GM-01 (doc-drift clean-checkout regression — Claude's call, small) → GM-02 (Telegram offline harness, tests only) → GM-03 (dashboard stale-READY).

## May Claude safely continue?
**YES.** Grok changed no source, no config, no Claude file, and no runtime state; the only repo change is the new `reports/grok/` directory. Claude should pull/fast-forward `origin/ahos` before its next commit if Grok's docs commit was pushed (it only adds `reports/grok/*`, so no conflict is possible with Claude's dirty files). Coordinate before either agent edits `scripts/doc_drift.py`, `telegram_ai/`, `chat.ts`, or `CommandCenter.tsx`.
