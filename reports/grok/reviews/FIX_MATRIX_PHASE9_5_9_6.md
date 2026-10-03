# Fix matrix — Phase 9.5 + Phase 9.6

Every finding id from the two independent reviews, mapped to its status, the
commit that closed it, and the test a reviewer can re-run. Statuses use the
reality ladder: `FIXED` here means the code change exists **and** a test pins
it — it is still self-test, not independent verification.

Reviews:

- `reports/grok/reviews/REDTEAM_19_LOCAL_COMMITS_20261002-2313.md` (B1, M1–M4, m1–m7)
- `reports/grok/reviews/LOCAL_COMMITS_5_HARDMODE_REVIEW.md` (BL-1..3, MJ-1..13, MN-1..12)

Phase 9.5 = commit `0638643` (part 1). Phase 9.6 = `8e54953`, `832f0ce`,
`6b2e0f6`, `5974da0`, `e22a154`, `da651af`, `c127f68`, `dbc9125` (part 2).

## REDTEAM-19

| Id | Status | Commit | Test (re-run) |
|----|--------|--------|---------------|
| B1 | FIXED | `0638643` | `npm run test:chat-auth` (23) — identity is server-side: Telegram HMAC signature, httpOnly session cookie; an unproven caller is never owner. `isOwner` unproven-claim cases in `scripts/chat_actions_selftest.ts` ("owner identity") |
| M1 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "the reader allowlist no longer grants control" (`isOwner(ADMIN2) === false`) |
| M2 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "secrets in the summary are redacted before the owner sees them"; `npm run test:dev-missions` (14) redacts then derives the title |
| M3 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "the proposal shows the FULL stored summary" + "the pending action binds the exact summary text" (`summaryHash`, 64 hex) |
| M4 | FIXED | `0638643` | `tests/test_chat_control_gate_static.py::test_gateway_forwards_resolved_identity_and_assertion_for_audit_only` (comment text pinned); `conversation_gateway.ts:24-30` |
| m1 | FIXED | `0638643` | `chat_actions.ts:502` passes `confirmCode`; pinned as MN-7 below |
| m2 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "two dashboard sessions get distinct identity keys"; `npm run test:chat-handlechat` (18) |
| m3 | FIXED | `0638643` | `chat.ts::persistChat` — `stripConfirmCodes(redactSecrets(text))` before insert; `tests/test_chat_control_gate_static.py` no-raw-fields pin |
| m4 | FIXED | `0638643` | `chat_memory.ts::stripConfirmCodes` applied to stored memory; covered by `npm run test:chat-handlechat` |
| m5 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "wrong-code lockout (m5)" — 5 attempts, lockout audited, real proposal blocked while locked |
| m6 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "paper quantity cap (m6)" — clamps to `MAX_PAPER_QUANTITY` |
| m7 | FIXED | `0638643` + `dbc9125` | Receipts committed at `reports/m9_6/` and this matrix; counts are self-reported and labelled as such |

## HARDMODE — MAJOR

| Id | Status | Commit | Test (re-run) |
|----|--------|--------|---------------|
| BL-1 | FIXED | `0638643` | `npm run test:dev-missions` — redaction regexes are global; a second secret in one summary survives |
| BL-2 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` dev-mission redaction cases |
| BL-3 | FIXED | `0638643` | same as B1 (`scripts/chat_actions_selftest.ts` identity block) |
| MJ-1 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "executes only when the EXECUTING record is written" (PROPOSED → EXECUTING → CONFIRMED) |
| MJ-2 | FIXED | `0638643` | same file "a broken audit sink aborts the action and burns the code" — nothing runs, code consumed |
| MJ-3 | FIXED | `0638643` | `tests/test_chat_control_gate_static.py::test_gateway_forwards_resolved_identity_and_assertion_for_audit_only` |
| MJ-4 | FIXED | `8e54953` | `tests/test_chat_control_gate_static.py` (12/12) re-pinned to the post-`832f0ce` seam; behavioural gate in every chat suite |
| MJ-5 | FIXED | `0638643` | `npm run test:chat-agent` (30) — the current message is redacted before Gemini |
| MJ-6 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` owner-identity cases; `isOwner` = `TELEGRAM_ADMIN_USER_IDS` only |
| MJ-7 | FIXED | `0638643` | `scripts/chat_actions_selftest.ts` "dev-mission proposal integrity" (full text, bound hash, redaction) |
| MJ-8 | FIXED | `0638643` | `npm run test:dev-missions` — a tampered chain refuses to append (`verify()` try/catch, `MN-6`) |
| MJ-9 | FIXED | `0638643` | Claim corrected, not just re-asserted: `dev_missions.ts` docstring now states plainly that the raw user text remains in `chat_messages` (redacted by `chat.ts::persistChat`) and that only the cleaned, redacted summary is queued. Pinned by the docstring text itself |
| MJ-10 | FIXED | `e22a154` | `git ls-files docs/owner_directives/` — the owner directives, mission plan and orchestration log are now tracked, so the discovery doc's citations resolve on a clean checkout |
| MJ-11 | FIXED | `832f0ce` | `scripts/chat_reply_format_selftest.ts` / `npm run test:chat-reply-format` (48) — `validatePhrased` rejects a flipped direction, out-of-order numbers and added buy advice |
| MJ-12 | FIXED | `832f0ce` | `npm run test:chat-handlechat` (18) — DB-free harness: all channels, owner/non-owner, propose/confirm/replay/wrong-code/lockout/expiry/cancel, foreign code, GM-04 gate, chain verified |
| MJ-13 | FIXED | `0638643` | `node scripts/verify_control_audit.ts` exits non-zero on a missing file and anchors the prefix hash |

## HARDMODE — MINOR

| Id | Status | Commit | Test (re-run) |
|----|--------|--------|---------------|
| MN-1 | FIXED | `dbc9125` | `npm run test:chat-control-gate` (131) — describe block "MN-1: ids and message digests are peppered": not the unsalted digest, different peppers differ, UNKNOWN preserved, short commands not dictionary-reversible, file fallback persists and reloads (0600). Static gate now scopes the append-only ban to `FileAuditSink` |
| MN-2 | FIXED | `0638643` | `tests/test_ai_provider_status.py::test_windows_backend_is_read_only_and_injectable` — `CredentialStore.has_credential` returns `bool \| None`, never the value |
| MN-3 | FIXED | `0638643` | `tests/test_ai_provider_status.py::test_windows_backend_off_windows_reports_unknown` |
| MN-4 | FIXED | `6b2e0f6` | `npm run test:gemini-egress` (13) — Gemini egress is an explicit, file-backed owner approval, default-on with a documented kill switch (`AHOS_GEMINI_EGRESS`) |
| MN-5 | FIXED | `0638643` | `npm run test:dev-missions` — `URL_CREDENTIALS` captures the scheme in a group, so `https://user:pass@host` redacts to a scheme-prefixed mask |
| MN-6 | FIXED | `0638643` | `npm run test:dev-missions` — `verify()` is try/catch and reports the first bad line instead of throwing |
| MN-7 | FIXED | `0638643` | `chat_actions.ts:502` (`confirmCode: a.code`) → `dev_missions.ts:255` stores `hashId("confirm_code", …)`, never the raw code; covered by `npm run test:dev-missions` |
| MN-8 | FIXED | `c127f68` | `scripts/chat_actions_selftest.ts` "parseConfirmation anchors on the whole message" — `confirm ABC123` / `yes ABC123` now return null (Persian and explicit only) |
| MN-9 | FIXED | `da651af` | `reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md` now cites `ahos_org/registry.py` (`CANONICAL_AGENT_IDS` line 14, `AgentRegistry` line 177, "verified at 3eea757"); handoff corrected to M13 |
| MN-10 | FIXED | `0638643` + `e22a154` | Receipts committed: `reports/m9_6/pytest_95_static.txt`, `reports/m9_6/receipts_95.txt`; 9.6 counts are in the handoff and this matrix, labelled self-reported |
| MN-11 | FIXED | `5974da0` | `git ls-files scripts/store_ai_key.py store_gemini_key.bat` — tracked, and a masked scan of the diff for `AIza…`, bot tokens, `sk-`, `ghp_`, PEM and 16+ char `key=<…>` found 0 hits |
| MN-12 | FIXED | `da651af` | `npm run test:chat-intent` (76) — `DEV_NEGATIVE_RE` keeps "سیستم رو چک کن" / "agents رو بررسی کن" out of `dev_mission` while real build requests still route there |

## Human-gated / out of scope

None of the findings were left to a human decision. The review's own "attacks
that HOLD" list (no real secrets in the commits, Credential Manager key path,
gitignored `data/`) was re-checked and still holds.

## Verification after the last fix (`dbc9125`)

- `npx tsc --noEmit -p .` → 0 errors.
- 15/15 self-test suites pass, 414 tests, 0 failures: web-api-auth 9,
  canonical-read-model 13, canonical-security 19, alert-banner 8,
  dashboard-truth 34, chat-reply-format 48, chat-intent 76, chat-control-gate
  131, chat-agent 30, dev-missions 14, gemini-phraser 12, chat-auth 23,
  chat-actions 18, chat-handlechat 18, gemini-egress 13.
- `pytest tests/test_chat_control_gate_static.py` → 12 passed.
- `eslint` → 0 problems (run in Phase 9.5; no linted file changed since except
  for the re-scoped static gate test, which is Python).
- Lane A untouched; no secret printed or committed; PAPER_ONLY unchanged.
