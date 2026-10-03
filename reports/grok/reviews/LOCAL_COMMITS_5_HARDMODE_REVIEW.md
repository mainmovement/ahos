# AHOS Agent-16 QA: HARD MODE review of 5 local, unpushed commits

- **Reviewer:** Agent-16 QA (Grok executor). Independent static review. **Strictly read-only** on the laptop.
- **Date:** 2026-10-02, about 23:10 Tehran (UTC+3:30)
- **Repo:** `G:\robat\ahos` (DESKTOP-DH7QOCK), branch `ahos`. Shell was Windows PowerShell 5.1.
- **Evidence level:** L0/L1 only (actual blob and diff lines). Line numbers below refer to the file **as of the named commit**.
- **Commands used on the laptop:** `git log/show/diff/rev-parse/branch/grep/ls-tree/ls-files/diff-tree/check-ignore/status` and `Select-String -Quiet`. Nothing was written, fetched, checked out or run there.
- **Tests:** none were run. Per the brief, the suites write temp files and pytest rewrites `reports/validation_results.json`. Every test count quoted from the commits is therefore **UNVERIFIED by QA**.

## 0. Commit resolution / push state

| Short | Full SHA | On `ahos` | On any remote-tracking branch | Tree mirrored on box |
|---|---|---|---|---|
| 527c433 | 527c43375b487a57225a8b2713abafcad0752ced | yes | **no** | yes: tree 14640cb6… = box `0a8ebc2` |
| 1d72d71 | 1d72d7164ffa557954a7708db67a689510748060 | yes | **no** | yes: tree 26ea7014… = box `0fc84f2` |
| 71fe160 | 71fe160a7784e3019cc8e3675347bd21c0d89d6d | yes | **no** | yes: tree 70f35575… = box `6883453` |
| d10383e | d10383e0438bb24d35d93d48bd381124268ddf85 | yes | **no** | no (read on the laptop) |
| 3eea757 | 3eea757cec88b467a5e76919c87c331279300c6f | yes (HEAD) | **no** | no (read on the laptop) |

- `git branch -a --contains <sha>` lists only `* ahos` for all five.
- `git status -sb` reports `ahos...origin/ahos [ahead 9]`.
- **Caveat:** no `git fetch` was run (read-only rule), so "unpushed" is relative to the last-fetched `origin/ahos`.
- For the first three commits the box mirror's tree hashes match the laptop's exactly, so those blobs were read on the box. This is byte-identical by git hash.

**Access problems:**
- `Read` and `CopyToBox` refuse `G:\robat\ahos\...` ("outside the allowed local-exec root"). Machine Shell works.
- Shell output is truncated at 20,000 characters, so long files were paged.
- No other problems.

---

## 1. Per-commit summary

### 527c433: GM-04 chat control capability gate

**Files changed (12 files, +985/−18):**
- `app/api/engine/route.ts` +12
- `chat.ts` 61
- `chat_control_gate.ts` +298 (new)
- `conversation_gateway.ts` +3
- `package.json` +2
- `reports/grok/G11_LIVE_E2E_RUNBOOK.md` +137
- `GM04_..._PROPOSAL.md` ~93
- `reports/grok/GROK_HANDOFF.md` +81
- `MISSION_DISCOVERY_2026-10-02.md` ±2
- `scripts/chat_control_gate_selftest.ts` +177
- `scripts/verify_control_audit.ts` +28
- `tests/test_chat_control_gate_static.py` +109

**What it does:**
- Removes `startEngine`/`stopEngine` from `chat.ts`.
- Adds whole-message command detection (NFKC, zero-width stripping, Arabic→Persian letters).
- `gateChatControl` refuses start, stop and paper_buy on `/api/chat` for every channel.
- Adds a hash-chained JSONL audit with hashed ids.
- `/api/engine` start/stop now appends an ALLOWED audit line.

**Assessment:**
- The gate is genuinely deny-by-default. The only `allowed: true` path is the non-control early return. Channel is never consulted.
- Negative cases are good: "stop loss", "restart", "استارتاپ" and similar.
- Gaps:
  - The engine-route audit is written *before* the action, ignores audit failure, and never records the outcome.
  - The verifier passes when the file is missing, and tail truncation is undetectable.
  - Ids and messages are hashed without a salt.
  - No integration test of `handleChat`.

**Verdict: PASS_WITH_GAPS.**

### 1d72d71: Gemini phraser + read-only Windows Credential Manager reader

**Files changed (13 files, +1471/−39):**
- `architecture/ai/credential_store.py` 67
- `architecture/ai/gemini_phraser.py` +198
- `architecture/ai/wincred_reader.py` +102
- `chat.ts` 19
- `gemini_phraser.ts` +286
- `package.json` +1
- `CLAUDE_CONTINUATION_GUIDE.md` +323
- `GM09_...md` 25
- `GROK_HANDOFF.md` +82
- `response_composer.ts` 35
- `scripts/gemini_phraser_selftest.ts` +125
- `tests/test_ai_provider_status.py` 70
- `tests/test_gemini_phraser.py` +177

**What it does:**
- `CredReadW` only, generic type, prefix `AHOS/ai/`. No write, delete or enumerate.
- The key lives only in a short-lived Python child process and goes into the `x-goog-api-key` header.
- Error text is scrubbed. Stdout carries status and reason codes only.
- Node spawns the helper without a shell and with a minimal env (no DATABASE_URL or tokens).
- The output validator checks footer, jargon and "no new number".

**Assessment:**
- Key handling is solid, and the offline tests do assert that the key never appears in output.
- The secret is not logged or printed anywhere. A grep of all five commits found no key patterns.
- Gaps:
  - The real `CredReadW` path has no test; the CLI round trip is skipped on win32, the target OS.
  - `has_credential()` materialises the secret just to answer a yes/no question.
  - "Validator-guarded" is overstated: only set-membership of digits is checked (see MJ-11).
  - Data egress to Gemini is on by default.

**Verdict: PASS_WITH_GAPS.**

### 71fe160: conversational agent + confirm-gated PAPER commands

**Files changed (22 files, +2024/−77):**
- `CommandCenter.tsx` 46
- `app/api/chat/route.ts` +1
- `architecture/ai/gemini_chat.py` +148
- `gemini_phraser.py` 27
- `chat.ts` 148
- `chat_actions.ts` +344 (new)
- `chat_agent.ts` +560 (new)
- `chat_control_gate.ts` 19
- `chat_memory.ts` +82 (new)
- `chat_replies.ts` 4
- `conversation_gateway.ts` +2
- `gemini_phraser.ts` 37
- `package.json` +1
- `CLAUDE_CONTINUATION_GUIDE.md` 131
- `GM04 proposal` 34
- `GROK_HANDOFF.md` 98
- `response_composer.ts` 2
- `scripts/chat_agent_selftest.ts` +319
- `tests/test_gemini_chat.py` +86
- `tests/test_gemini_phraser.py` 7
- `tests/test_telegram_reply_presentation.py` 3
- `types.ts` +2

**What it does:**
- Reverses the GM-04 blanket refusal for "owners". The new flow is: propose → 6-char code (crypto `randomInt`, 31-char alphabet, 5-minute TTL, single use, bound to identity) → whole-message `تایید CODE` → execute through `defaultActionDeps`, the same engine and paper functions the dashboard uses → write a `chat_confirm` audit line.
- Adds a Gemini function-calling agent with read tools and propose tools.
- Adds per-chat in-memory history with secret redaction.

**Assessment:**
- PAPER_ONLY holds. There is no exchange or live API, and paper_buy still requires a canonical BUY.
- Two defects break the owner gate:
  - It fails **open**: a missing `channel` defaults to `"web"`, which is treated as owner.
  - Audit is written only *after* execution and its failure is swallowed.
- Comments still claim channel is "never a grant".
- The GM-04 static pins written to stop exactly this re-enablement do not catch it, because the engine is reached through an indirection.
- The raw current message (possibly containing secrets) is sent to Gemini unredacted.
- No integration test of the chat.ts gate or confirm path.

**Verdict: FAIL.**

### d10383e: dev-mission intake in the Gemini assistant

**Files changed (10 files, +688/−20):**
- `chat.ts` 22
- `chat_actions.ts` 46
- `chat_agent.ts` 49
- `chat_control_gate.ts` 6
- `chat_intent.ts` +23
- `dev_missions.ts` +241 (new)
- `package.json` +1
- `scripts/chat_agent_selftest.ts` +138
- `scripts/chat_intent_selftest.ts` +23
- `scripts/dev_missions_selftest.ts` +159 (new)

**What it does:**
- Adds the propose tool `submit_dev_mission`. After confirmation, `DevMissionStore.append` writes one QUEUED line to a hash-chained JSONL file.
- Adds `list_dev_missions`, an owner-only read tool.
- Adds a deterministic `dev_mission` intent for when the agent is off.

**Assessment:**
- **Secret leakage to disk:**
  - `titleFa` is derived from the **unredacted** summary.
  - The redaction regexes are non-global, so only the first match of each rule is redacted.
  - Both were reproduced with a PoC on the box using verbatim function copies and a synthetic key.
- **Confirmation integrity:** the owner sees only 80 characters of the summary in the proposal, but up to 280 are stored.
- **Claims not backed by code:**
  - "Never the raw message" is false: the summary *is* the cleaned raw message.
  - "Fail-closed" is false: after tampering, append keeps writing with duplicate ids.
  - "confirmCode (audit link)" is never populated.

**Verdict: FAIL.**

### 3eea757: University + agents discovery report (docs only)

**Files changed (3 files, +272/−4):**
- `CLAUDE_CONTINUATION_GUIDE.md` +34
- `GROK_HANDOFF.md` +39
- `UNIVERSITY_AND_AGENTS_DISCOVERY.md` +203 (new)

**What it does:** read-only discovery covering the University, the 19 agents and the teams, plus a phased plan.

**Assessment:**
- Tone is commendably honest:
  - Ladder states are used.
  - "Not a claim that AGI/ACI is delivered."
  - The University is called PLANNED.
- Verified true:
  - `MINIMUM_MATURITY_FOR_ALLOW = 2` (`ahos_org/policy.py:104`) and `advance_maturity` (`ahos_org/registry.py:227`).
  - `architecture/control_plane.py` is imported only by `tests/test_control_plane_soak.py` and `tests/test_runtime_w11.py` (plus a `doc_drift` string reference).
  - No University code exists.
- Problems:
  - Primary sources are **untracked** files (`docs/owner_directives/*`, `reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md`), so the citations cannot be checked on a clean checkout.
  - It misattributes `CANONICAL_AGENT_IDS` and `AgentRegistry` to `architecture/registry.py`; they are in `ahos_org/registry.py:14,177`.
  - The guide and handoff repeat d10383e's false claims as fact: redacted before writing, never the raw message, fail-closed.
  - Test-pass claims have no committed evidence.

**Verdict: CHALLENGE.**

---

## 2. Prioritized findings

### BLOCKER

**BL-1: d10383e, `dev_missions.ts:185-186` (title from unredacted summary)**
- **Problem:**
  - `titleFa: titleFromSummaryFa(summary)` is computed from the *unredacted* summary. Only `summaryFa` is redacted.
  - A secret in the first clause (up to 60 characters, split only on `.!?،,؛;:`) is written to `data/dev_missions/dev_missions.jsonl` in plaintext.
  - It is also returned by `list_dev_missions` and so sent to Gemini.
  - PoC (`reviews/poc/dm_poc.mjs`, synthetic key): `"کلید گوگل AIza<35> رو ذخیره کن"` gives `titleFa leaks key: true`.
  - The self-test only passes because its fixture has a colon (`کلید گوگل: AIza…`), which ends the title before the key.
  - This contradicts the doc claim (line 22) that secrets "never reach disk".
- **Fix:**
  - Redact first, then derive both fields: `const red = redactMissionSecrets(summary); titleFa = titleFromSummaryFa(red); summaryFa = red`.
  - Add a test with a no-punctuation fixture asserting the raw file has no `AIza`.

**BL-2: d10383e, `dev_missions.ts:76-91, 96-103` (only the first match is redacted)**
- **Problem:**
  - Every `SECRET_RULES` regex lacks the `g` flag, so `String.replace` redacts only the **first** match per rule.
  - A second key or token survives to disk. PoC: `second key survives redaction: true`.
  - `chat_memory.ts` uses `/g` correctly; this module does not.
- **Fix:** add `g` to every pattern (or use `replaceAll` with global regexes), and add a two-secret test per rule.

**BL-3: 71fe160 (still at HEAD), missing channel is treated as owner (fail-open)**
- **Where:**
  - `app/api/chat/route.ts:51`: `channel: body.channel ?? "web"`
  - `chat.ts:98`: `channel: ctx.channel ?? "web"`
  - `chat_actions.ts:81`: `String(id.channel ?? "web")` and `:87`: `return ch === "web" || ch === "dashboard"`
- **Problem:**
  - Any `/api/chat` caller that omits `channel` is treated as owner and can propose and confirm engine start/stop, paper_buy, watch_add and dev_mission.
  - That includes integrations such as n8n, scripts, or any future client.
  - All anonymous web callers also share identity `web:`.
  - Criterion 2 explicitly forbids defaults that fail open.
- **Fix:**
  - Treat a missing or unknown channel as non-owner. No default to "web".
  - Require an explicit dashboard-only proof for owner on web, for example a separate dashboard session token or CSRF-bound nonce, not the shared `AHOS_WEB_API_TOKEN`.
  - Add tests: `isOwner({channel:null})===false`, `isOwner({channel:undefined})===false`, and a `handleChat` test showing that a body with no channel is refused.

### MAJOR

**MJ-1: 71fe160, `chat_actions.ts:308-336` + `chat_control_gate.ts:268-279` (no audit before execution)**
- **Problem:**
  - The `chat_confirm` audit is written only **after** `startEngine`/`stopEngine`/`addWatch`/`paperBuy` runs.
  - `recordControlAudit` swallows all errors and returns `null`, and the return value is ignored.
  - So an action can execute with **no audit line**: disk full, permissions, or a crash between execute and audit.
  - The tests inject an audit fn that always returns `null` and still expect execution, which pins the fail-open behaviour.
- **Fix:**
  - Write an `EXECUTING` record first (write-ahead) and abort with a refusal if it returns `null`.
  - Then write `CONFIRMED`/`FAILED`.
  - Add a test: a broken sink means nothing executes.

**MJ-2: 527c433, `app/api/engine/route.ts:13-23` (engine audit written before the action, failure ignored)**
- **Problem:**
  - ALLOWED is recorded *before* start/stop. Its failure is ignored, and the outcome (success or exception) is never recorded.
  - The chain therefore says ALLOWED even when the action failed, and nothing when the audit failed.
- **Fix:** write-ahead plus abort on audit failure, then an outcome record (`EXECUTED`/`FAILED`).

**MJ-3: 71fe160 (still at HEAD 3eea757), stale security comments contradict the code**
- **Where:**
  - `conversation_gateway.ts:27`: "forwarded for the audit only; never used as a grant"
  - `chat.ts:91`: "NEVER a grant (GM-04)"
  - `chat_control_gate.ts:10`: "REFUSED on the chat path for EVERY channel, including 'web'"
- **Problem:** the code does the opposite. `chat.ts:122` `if (gate.controlled && !isOwner(identity))` uses channel as the grant. Reviewers reading the security module are misled.
- **Fix:** rewrite these comments to describe the owner-confirm model, or move the owner decision into `gateChatControl` so the module is the single source of truth.

**MJ-4: 71fe160, `tests/test_chat_control_gate_static.py:19-22, 25-37` (static pins bypassed)**
- **Problem:**
  - These pins were written to stop a later edit from "silently re-enabling engine start/stop or paper_buy from the chat path".
  - 71fe160 re-enables both through `chat_actions.ts` (`defaultActionDeps` → `await import("./engine")`), and the pins still pass.
  - `startEngine` is no longer named in `chat.ts`, and `'decision: "REFUSED"'` is still present.
  - The file was not updated in 71fe160.
- **Fix:**
  - Pin the new contract statically: chat.ts may only reach the engine via `handleConfirmation`; `handleConfirmation` must check `isOwner`, expiry and identity, and call `take()` before executing.
  - Add a behavioural `handleChat` test using a fake engine.

**MJ-5: 71fe160, `chat_agent.ts:459` (raw current message sent to Gemini)**
- **Problem:**
  - The current user message goes to Gemini (a third party, free tier) **unredacted**: `parts: [{ text: input.text }]`.
  - Only stored memory is redacted (`chat_memory.ts:58-62`). A key pasted into chat leaves the machine.
  - Proposal texts containing confirm codes also go into memory and are sent on the next turn.
- **Fix:**
  - Apply `redactSecrets` to `input.text` before building `contents`.
  - Strip `تایید XXXXXX` codes from memory.
  - Add a test that the request handed to the runner has no secret.

**MJ-6: 71fe160, `chat_actions.ts:85` (chat allowlist becomes owner authority)**
- **Problem:**
  - Owner = `TELEGRAM_ADMIN_USER_IDS ∪ TELEGRAM_ALLOWED_CHAT_IDS`, so anyone allowed to *chat* with the bot gets *control* authority.
  - `TELEGRAM_ADMIN_USER_IDS` is empty in `.env` (guide §2), so owner rests entirely on the chat allowlist.
- **Fix:** owner = `TELEGRAM_ADMIN_USER_IDS` only. An empty admin list means nobody. Add a test that an id only in `ALLOWED_CHAT_IDS` is not owner.

**MJ-7: d10383e, `chat_actions.ts:108-111` vs `dev_missions.ts:40,125` (owner confirms less than is stored)**
- **Problem:**
  - The proposal shows `s.slice(0, 80)`, but up to 280 characters are stored. The owner confirms text they never saw.
  - In the agent path, `summaryFa` is **model-authored** (`chat_agent.ts` `params.missionSummaryFa = args.summaryFa`). It can differ from what the owner asked, including through prompt injection from news or token text fed in by tools.
- **Fix:**
  - Show the full stored summary (already capped at 280) in the proposal.
  - Bind a hash of it into the pending action and re-check that hash at confirm time.
  - In the agent path, also show the owner's original request next to the model summary.

**MJ-8: d10383e, `dev_missions.ts:158-164, 177, 190` (keeps writing after tampering)**
- **Problem:**
  - After tampering, `records()` returns `[]`, so `append` restarts at `seq=0` and **duplicate `DM-000001` ids** appear.
  - It keeps appending to the broken chain. This contradicts the "fail-closed" and "unique within the file" claims (lines 48, 173; handoff Phase 8).
- **Fix:** in `append`, refuse (return null) when `verify().ok === false`. Add a test: tamper, then append returns null, and ids stay unique.

**MJ-9: d10383e, commit message, `dev_missions.ts:20`, handoff ("never the raw message")**
- **Problem:**
  - `chat_intent.ts` `extractDevMissionSummary(text) = cleanSummaryFa(text)` is the raw message with whitespace normalised, greetings stripped and length truncated.
  - Separately, `chat.ts` `persistChat` stores the raw user text in the `chat_messages` DB on every path, including dev_mission.
  - The claim is not backed by code. The self-test "never stores the raw user message" only checks greeting stripping.
- **Fix:** correct the claim (for example: "stores the owner's cleaned request text, redacted"), or genuinely summarise. Document that raw text is still in `chat_messages`.

**MJ-10: 3eea757, `UNIVERSITY_AND_AGENTS_DISCOVERY.md:17,33,37,49` (untracked sources)**
- **Problem:**
  - Primary citations (`docs/owner_directives/owner_directive_part1.txt`, `part2`, `reports/grok/OWNER_DIRECTIVE_MISSION_PLAN.md`) are **untracked**: `git ls-files` returns nothing for them.
  - On a clean checkout the evidence does not exist. This is the same failure class as the guide's own Blocker A (doc_drift).
- **Fix:** commit the owner directives (if the owner allows) or cite only tracked files. Add the report to the doc_drift scan.

**MJ-11: 1d72d71, `response_composer.ts:87-96` (`validatePhrased`) (validator claim overstated)**
- **Problem:**
  - "Validator-guarded" checks only that each digit-run token exists *somewhere* in the draft (a set).
  - The phraser can swap numbers between assets, flip "up"/"down", or add trade advice ("بخر") without digits, and still pass.
  - Tests only cover new-number and jargon cases.
- **Fix:**
  - Compare digit sequences in order (or per line).
  - Block buy/sell imperatives and direction-word changes.
  - Add adversarial tests for swapped numbers, negation and added advice.

**MJ-12: 71fe160 / d10383e (tests), no integration test of the real gate path**
- **Problem:**
  - No test drives `handleChat` for owner vs non-owner, missing channel, confirm/cancel, or audit-sink failure.
  - The agent tests use a fake runner, fake deps, and an audit fn returning `null`.
  - The owner-identity tests never cover `channel: null/undefined`.
- **Fix:** add a DB-free `handleChat` harness (inject snapshot, store and audit sink) covering the BL-3, MJ-1 and MJ-6 cases.

**MJ-13: 527c433, `scripts/verify_control_audit.ts:11-14` (verifier accepts a deleted audit)**
- **Problem:**
  - A missing audit file prints `NO_AUDIT_FILE` and exits **0**.
  - Deleting the audit, or truncating trailing lines, verifies as OK. There is no external anchor of the head hash.
- **Fix:**
  - Exit non-zero when the file is missing, unless `--allow-empty` is passed.
  - Periodically anchor `head_hash` and line count in a separate store and check monotonic growth.

### MINOR

**MN-1: 527c433, `chat_control_gate.ts:140-143, 260-261` (weak hashing)**
- **Problem:** `hashId` is unsalted sha256 truncated to 16 hex. Telegram ids (about 10 digits) can be brute-forced in minutes. `message_sha256` of short commands ("stop", "تایید ABC123") is dictionary-reversible.
- **Fix:** use HMAC with a local secret pepper stored outside the repo.

**MN-2: 1d72d71, `architecture/ai/credential_store.py` `has_credential` + `wincred_reader.py:78-80` (secret read for a status check)**
- **Problem:** a status check reads and decodes the full secret blob. `memset` zeroes the OS buffer only; the Python `bytes` copy persists.
- **Fix:** implement `has_credential` with `CredReadW` and immediate `CredFree` without `string_at`, and correct the docstring.

**MN-3: 1d72d71, tests (real Windows path untested)**
- **Problem:** the real `CredReadW` / ctypes struct path is never exercised. `test_cli_round_trip_persian_bytes_without_credential` is skipped on win32, the only target OS.
- **Fix:** add a Windows-only test against a throwaway `AHOS/ai/test-<uuid>` credential created by the test's own fixture (owner-approved), or a ctypes mock of advapi32.

**MN-4: 1d72d71 / 71fe160, `gemini_phraser.ts:272-285`, `chat_agent.ts:546-559` (egress on by default)**
- **Problem:** the phraser and agent are **on by default** (opt-out env), sending market, portfolio and chat data to the Gemini free tier.
- **Fix:** make them opt-in (`AHOS_CHAT_AGENT=on`) or record the owner's data-egress approval explicitly in config.

**MN-5: d10383e, `dev_missions.ts:100` (`URL_CREDENTIALS` replacement bug)**
- **Problem:** the replacement uses `args[0]`, but this pattern has no capture group, so `args[0]` is the match offset. Output is `0[REDACTED:URL_CREDENTIALS]@host` (PoC). It does not leak, but it is wrong.
- **Fix:** capture the scheme in a group.

**MN-6: d10383e, `dev_missions.ts:169` (`verify()` throws)**
- **Problem:** `verify()` runs `JSON.parse` on the last line and throws on a torn tail, despite returning a status object everywhere else.
- **Fix:** wrap it in try/catch and report `ok:false`.

**MN-7: d10383e, `dev_missions.ts:50-51` vs `chat_actions.ts` `recordDevMission` (`confirmCode` never set)**
- **Problem:** `confirmCode` is documented as the "audit link" but is never passed, so it is always `null`.
- **Fix:** store a hash of the code, or a pending-action id, and drop the misleading comment.

**MN-8: 71fe160, `chat.ts` `persistChat`, `chat_actions.ts:163-174` (code exposure, no attempt limits)**
- **Problem:**
  - Proposal text containing the live code is persisted to `chat_messages` and memory.
  - Failed confirm attempts are neither audited nor rate-limited.
  - `yes CODE` / `confirm CODE` are accepted as confirmation words.
- **Fix:** mask codes before persisting, audit failed attempts and lock out after N, and keep the confirmation words Persian and explicit.

**MN-9: 3eea757, `UNIVERSITY_AND_AGENTS_DISCOVERY.md:94,116` (wrong file attribution)**
- **Problem:**
  - It attributes `CANONICAL_AGENT_IDS` to `architecture/registry.py`; they are at `ahos_org/registry.py:14`. That file is the AG-* YAML builder.
  - `AgentRegistry` is at `ahos_org/registry.py:177`.
  - The handoff says the queue consumer is "M12"; the report says M13.
- **Fix:** correct the paths and milestone, and label the section "verified at <sha>".

**MN-10: 3eea757 / d10383e, guide and handoff test claims (no committed evidence)**
- **Problem:** "All exit 0", 14/30/72/126 counts, "pytest 60 passed" and "validate_imports exit 0" have no committed evidence. The receipts are untracked (`reports/validate_imports_run_20261002_phase8.txt` etc.).
- **Fix:** commit test receipts, or label the counts as self-reported.

**MN-11: Working tree, outside the 5 commits (accidental-commit risk)**
- **Problem:**
  - Untracked `store_gemini_key.bat` and `scripts/store_ai_key.py` are not git-ignored.
  - A pattern scan found no literal Google key in either (values not printed), but they sit beside the repo and could be committed by accident.
- **Fix:** add both to `.gitignore`.

**MN-12: d10383e, `chat_intent.ts` `DEV_TOPIC_RE` (overly broad topic match)**
- **Problem:** the topic list includes very broad words ("سیستم", "agents", "update"), so ordinary requests can be hijacked into dev-mission proposals.
- **Fix:** narrow the topic list and add negatives such as "سیستم رو چک کن".

---

## 3. Criteria scorecard

| Criterion | Result |
|---|---|
| 1. No claims without evidence | **FAIL**: MJ-3, MJ-9, MJ-8 ("fail-closed"), MJ-10, MJ-11 ("validator-guarded"), MN-7, MN-10. The docs avoid AGI/ACI or readiness inflation, which is good. |
| 2. Owner gate / audit chain unbypassable | **FAIL**: BL-3 (fail-open default), MJ-1/MJ-2 (audit skippable, swallowed), MJ-6, MJ-13. |
| 3. PAPER_ONLY | **PASS**: no exchange, order or live code in any diff (grep for ccxt/binance/createOrder/LIVE flags: none). paper_buy still needs a canonical BUY. |
| 4. No secret leakage | **FAIL**: BL-1, BL-2 (to disk), MJ-5 (to Gemini). The Credential Manager reader itself does not leak; MN-2 is the only reader concern. |
| 5. Tests cover behaviour | **FAIL**: MJ-4 (pins bypassed), MJ-12 (no integration tests; fake audit returns null), BL-1 test passes by fixture luck, MN-3. |

## 4. Verdicts

| Commit | Verdict |
|---|---|
| 527c433 GM-04 control gate | **PASS_WITH_GAPS** |
| 1d72d71 Credential Manager reader + phraser | **PASS_WITH_GAPS** |
| 71fe160 PAPER commands with code confirmation | **FAIL** |
| d10383e Dev-mission intake | **FAIL** |
| 3eea757 University / agents report | **CHALLENGE** |
| **OVERALL** | **FAIL**: do not push until BL-1..3 and MJ-1, MJ-3..MJ-9 are fixed and re-reviewed. |

## 5. PoC artefact
`/workspace/ahos-orient/reviews/poc/dm_poc.mjs`:
- Verbatim copies of `redactMissionSecrets` / `titleFromSummaryFa` from `d10383e:dev_missions.ts`.
- Synthetic keys only.
- Output:
  - `titleFa leaks fake key: true`
  - `summaryFa leaks fake key: false`
  - `second key survives redaction: true`
  - `URL_CREDENTIALS output: 0[REDACTED:URL_CREDENTIALS]@host/db`
