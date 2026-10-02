# GROK HANDOFF (living document) — for Claude Code

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
