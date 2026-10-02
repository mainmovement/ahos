# CLAUDE CONTINUATION GUIDE: Grok session 2026-10-02 (Phases 1–6)

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
| (commit adding this file) | Phase 6 Gemini phraser + read-only Credential Manager backend + this guide | **local only** |

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

1. **GM-04 gate**
   - `/api/chat` **always refuses** start, stop and paper_buy for every channel. The reason is `CHAT_PATH_CANNOT_PROVE_LOCAL_DASHBOARD`, and the body-asserted `channel` is not trusted.
   - Engine control is only possible through `app/api/engine/route.ts` (dashboard buttons).
   - Command detection matches the whole message after normalization (NFKC, zero-width and bidi stripping, Arabic→Persian letters). Do not reintroduce substring regexes: "stop loss" used to stop the engine.
   - Refusal drafts are `locked: true` and are **never** phrased by an LLM.
2. **Control audit chain**
   - `data/control_audit/chat_control_audit.jsonl` is append-only and hash-chained. `FileAuditSink` isolates a torn tail.
   - Every REFUSED decision (chat) and ALLOWED decision (engine route) appends one line. Never rewrite or delete lines.
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
6. **Gemini key handling**
   - The key lives **only** in Windows Credential Manager: generic target `AHOS/ai/gemini`, user `gemini`, UTF-16-LE blob, stored by the owner.
   - **Never** put it in `.env`, logs, argv, env vars, test files, reports, commits or chat.
   - Only `architecture/ai/gemini_phraser.py` (helper process) calls `get_secret`, and Node never sees the key.
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

## 3. Known limitations and open items (all phases)
1. Blocker A (Claude, GM-01).
2. GM-04 independent review; `/api/engine` token exposure; `watch` ungated; `AHOS_CONTROL_AUDIT_PATH` not in the config scan.
3. Port mismatch: `.env` 3000 vs listener 3500 (OWNER_ACTION).
4. GM-12 review (Credential Manager read path, now IMPLEMENTED read-only).
5. GM-09 runtime wiring (council/router → `guard_provider_call`) not done; the ledger is not seeded.
6. `ahos_runtime_win` container config drift; no scheduled nightly backup task; wall-clock items (T+72h labels not before 2026-10-05 06:24 Tehran; soak nights 2–7).
7. Windows `validate_imports` (Phase 5 run) failed its evidence-mutation check because of a timing artefact. Box runs PASS. Re-run on Windows when the laptop is idle.
8. The bot log warns that no proxy is set; Telegram connects anyway.
9. `tests/test_sqlite_backup_restore.py::test_record_test_run_anchors_relative_executable` fails on Linux only (Windows path). Not a Windows issue.
