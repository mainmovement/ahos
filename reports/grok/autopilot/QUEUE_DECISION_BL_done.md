# Queue decision: BL — verification complete, one sub-item owner/permission-gated

Same shape as `QUEUE_DECISION_M48_1_done.md`: the mission's deliverables are
committed, but a STATUS-only edit is needed so the runner does not re-execute
the row and duplicate the work. Recorded here as a traceable act, per the owner's
standing instruction to continue the sequence.

## What BL asked for

`Close open BL/MJ items and all QA (16) BLOCKERs listed in reports/grok
(GROK_HANDOFF, ORCHESTRATION_LOG, remaining-work inventory)`.

The "16" is an aggregate, not one list: BL-1..3 + MJ-1..13 from the Agent-16
HARDMODE review, i.e. the two reviews' BL + MJ ranges. Strictly BLOCKER-severity
findings across both reviews number 4 (B1, BL-1, BL-2, BL-3).

## Outcome: everything closed and independently verified

The `FIX_MATRIX_PHASE9_5_9_6.md` claims every review finding FIXED. That is a
claim, so the four BLOCKERs were re-verified against current code rather than
quoted:

| Item | Claimed | Verified at code level |
|---|---|---|
| B1 / BL-3 (client-asserted `channel`/`user_id` was owner) | FIXED `0638643` | **yes** — `chat_auth.ts` resolves identity only from a Telegram HMAC (`verifyTelegramIdentity`) or an httpOnly session cookie + bound CSRF header (`verifyDashboardSession`); `chat_actions.ts:128-137` `isOwner` returns false unless `id.proven`, and Telegram then requires membership of `TELEGRAM_ADMIN_USER_IDS`. No `"web"`-channel or bearer-token grant path exists |
| BL-1 (`titleFa` cut from the unredacted summary → secret in plaintext) | FIXED `0638643` | **yes** — `dev_missions.ts:250-256` cleans, then redacts, then derives `titleFa` from the redacted text; comment names BL-1 |
| BL-2 (every `SECRET_RULES` regex lacked `g`, so a second key survived) | FIXED `0638643` | **yes** — all eleven rules at `dev_missions.ts:99-115` carry `g` |
| MJ-1..13, MN-1..12, M1-M4, m1-m7 | FIXED (matrix L20-69) | matrix inspected: no NOT FIXED / PARTIAL / HUMAN-GATED row; cited tests re-runnable |

## Two genuine defects found while verifying (both fixed)

The reviews' own fix claims had masked two real problems, neither of which was a
review finding:

1. **`isLoopbackRequest` did not exist** (`b9eba89`). `0638643` defined it,
   `d9492cb` deleted the definition while keeping `app/api/launcher/route.ts`,
   which imports it at both gates. Every launcher request threw on import, so
   the loopback guard never ran. `f6c4f20` restored six sibling orphans from
   that merge and filed the resulting tsc error as "pre-existing unrelated" —
   it was the same defect, seventh of seven, and it was live-red
   (`npm run test:launcher-route` failed outright). Restored against the
   contract its own probe documents, with two upward deviations: the anchored
   `LOOPBACK_HOST` regex instead of `startsWith` (so `127.0.0.1.evil.example`
   is refused, the rebinding domain `checkSessionIssuance` names), and no
   `x-forwarded-for` read (the module's REDTEAM-19 F1 posture). `npx tsc
   --noEmit` is now exit 0 — the repo's last known tsc error is gone.

2. **Blocker A / GM-01 was already closed** (`7436aca`). The handoff and the
   continuation guide repeatedly reported it open. Proven resolved by a fresh
   `git clone` of HEAD running `scan_docs()` from inside the clone: 95 canonical
   docs, ZERO stale references. `reports/nightly_backup_series.json` is tracked
   as of `1834779`, and the still-untracked
   `reports/validate_imports_run_20260928T045640Z.json` is cited only by two
   non-canonical `reports/grok/` docs. This also reconciles the contradiction
   against `BOX_PATCHES_MERGED.md` patches 0007/0021.

## The one sub-item that is not closed, and why that is correct

`source-map-js@1.2.1` (GHSA-68fv-2mgg-jv7q, high, `effects: []`) is fully
prepared — three hash-pinned lockfile lines, `package.json` untouched, integrity
queried live — but the `npm install` that would sync `node_modules` was **denied
by the session's safety classifier**, so nothing was committed and the lockfile
edit was reverted to keep the tree self-consistent. See
`reports/grok/M48_SOURCE_MAP_JS_BLOCKER.md` for the verbatim blocked command, the
rollback, and the exact split between what was verified and what was not.

This is an M48-class dependency update that the M48.1 register assigned to the BL
open-items list. It is owner action (approve the install, or run the one command
plus a `next build`), not more agent work.

## Verification for this decision

- full pytest suite (background): 2932 passed, 1 failed, 4 skipped; the failure
  is the pre-existing 0-byte `ahos_cognitive_memory.sqlite` Lane-B case, and
  there are **zero** doc-drift failures
- `npm run test:chat-auth` 47/47 (was 47 with 6 new), `test:launcher-route` 4/4
  (was 0/1), `m481_host_header_probe.mjs` 4/4
- `npx tsc --noEmit` exit 0; `npx eslint` on touched files clean
- `test:web-api-auth` 9/9, `test:chat-handlechat` 21/21, `test:chat-agent` 30/30
- pytest `test_web_api_auth_gate` + `test_launcher_orchestrator` +
  `test_deployment_config`: 179 passed, 1 skipped
- `test_doc_drift` 11/11, `test_evidence_package` 7/7
- `test_canonical_docs_have_zero_real_stale_refs` proven clean in a fresh clone

## Decision

**BL → DONE.** Every review finding is closed and the four BLOCKERs are
re-verified at code level; the two real defects the reviews' fix claims were
masking are fixed; Blocker A is proven resolved. The source-map-js bump is
isolated in its own blocker doc as owner action and does not hold this row —
it is M48's deliverable shape, and M48 remains PENDING for exactly this class
of change.

Commits: `b9eba89` (restore `isLoopbackRequest`), `2a1f6d4` (correct the M48.1
carry diagnosis), `9d5e210` (source-map-js blocker record), `7436aca` (close
Blocker A). No push.
