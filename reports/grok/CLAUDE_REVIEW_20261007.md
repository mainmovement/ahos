# CLAUDE_REVIEW_20261007

Reviewer: Grok Bot (box executor). Host: Mehrdad laptop. Zone: Asia/Tehran.
Written: 2026-10-07 00:25 Asia/Tehran
Repo: `G:\robat\ahos` branch `ahos` / merge `grok/box-security-merge`. HEAD before merge: `e912fb6`.
Constraints honored: PAPER_ONLY; no push; no secrets; did not kill PID 4708; did not thrash interactive Claude.

## Executive summary

Claude autopilot (Oct 4–7) delivered **M11.1–M11.4** and **M48.1** as DONE with real code + receipts;
**M10.1 is RUNNING but wedged** on `Atria-Dawn-Preview` (`unrecognized_model` + intermittent `429` quota).
HOLD.flag from 2026-10-04 02:45 is empty and **expired** under the 6h rule — continued work was expected, not a hold violation.
Critical gap: laptop lacked the box **REDTEAM-19 security series** (bootstrap `#boot=`, engine propose gate, posix_group_ok, etc.).
This pass **merged those box patches surgically** onto the laptop (Claude launcher M11 kept; security forced present).
Marker: `reports/grok/BOX_PATCHES_MERGED.md`.

## Commit inventory `40cf67e..e912fb6` (28 commits, ~52 ahead of origin — local only)

### M11.1 (launcher finish)
- CODE: `af0070b` `0d93f32` `d0141a9` `44ada75` `863819f` `3107d68` `30cdc32`
- Earlier still relevant (before 40cf67e): `ba4d455` `ed29710` `238b090` `3293b8d` `e4096d0` `ea2419e` `e7aa551`
- Docs/receipts: `eaf43e7` `eef7a8d`

### M11.2 (PS 5.1 log / no double-run)
- CODE: `385a38b` (+ autopilot harness `f6eb34f`)

### M11.3 (gateway identity)
- CODE: `95f1364` `ca0c1bb`
- Autopilot harness fixes exposed by stall: `2001f80` `9b11776` `8f059cd` `2c38549` `a3db6fb`
- Docs: `2c6d90f` `119b3b1` `7abec03` `e8abae2`

### M11.4 (telegram health)
- CODE: `4e1cb91`
- Docs: `82d5b0a`

### M48.1 (Next 16.3.8)
- CODE/deps: `0b9e0d6`
- Docs/gate: `624f025` `7fc7d9d` `e912fb6`

### Autopilot infra (cross-mission)
- `f6eb34f` bounded HasExited poll; `2001f80`/`9b11776` PARTIAL retry; `8f059cd` no end-with-bg-work; `a3db6fb` reload attempt counters.

## Mission verdicts

| Mission | Verdict | Evidence | Keep / Rework |
|---------|---------|----------|---------------|
| M11.1 | **PASS_WITH_GAPS** | Launcher control chain + smoke receipts; dashboard-api route tests in `3107d68`. Gap: pre-merge missing box F1 bootstrap on session path. | Keep Claude launcher. Security gaps closed by this merge. |
| M11.2 | **PASS** | `385a38b` UTF-8-BOM ahos.ps1; tests in `test_phase18_launchers.py`; owner receipt JSON present. | Keep. |
| M11.3 | **PASS** | `95f1364` spawn `node <next cli>` so marker matches; tests pin argv (`ca0c1bb`). | Keep over older box npm-wrapper approaches. |
| M11.4 | **PASS** | `4e1cb91` telegram stability/readiness; unit coverage in orchestrator tests. | Keep. |
| M48.1 | **PASS_WITH_GAPS** | `package.json` next/eslint-config-next **16.3.8**; evidence md + host-header probe script. Full 16 npm suites / live Host evil.example not re-verified in this pass. | Keep pins. Grok: optional re-run audit/build on laptop. |
| M10.1 | **FAIL** (in progress / wedged) | `active.json` mission M10.1; runlog attempt0–9 no AUTOPILOT_RESULT; fail10 `unrecognized_model` Atria-Dawn-Preview + 429 quota. Spec `missions/M10.1-*.md` not implemented in commits yet. | Do not credit DONE. Unblock model env before more attempts. |
| Box security 0001–0023 | **PASS** (merged this pass) | See BOX_PATCHES_MERGED.md live checks all critical YES. | Claude must not redo. |

## Code quality notes (CODE commits)

### Launcher / chat_auth / dashboard control (M11.1)
- Matches mission intent: single icon / zero consoles / status-stop-restart / own-gateway recognition.
- `30cdc32` SIGBREAK immunity for stop() is valuable on Windows; retained beside box posix_group_ok.
- Pre-merge session route was still loopback-only issuance without `#boot=` — **did not** match box REDTEAM-19 F1; fixed in merge.
- PAPER_ONLY / no push: no evidence of push or live trading in these commits.

### Next 16.3.8 (M48.1)
- Exact pin update appropriate for advisory; rollback path documented in mission evidence file.
- Did not expand unrelated deps (good).

### Autopilot runner
- Harness fixes are real and necessary (unbounded Wait, PARTIAL clear wiping result, attempt budget load-once).
- Double-run risk: watchdog `10452` + autopilot `10488` — designed pair; HOLD expired so not blocked. Child `14364` still WAITING on M10.1.

## Box-debug security series (requested checklist)

| Item | Before | After this merge |
|------|--------|------------------|
| one-time dashboard bootstrap (`dashboard_boot` / `#boot=`) | MISSING | **PRESENT** |
| CSRF mandatory (header echo) | PARTIAL (cookie fallback possible) | **PRESENT** header-only |
| chat JSON.parse fix | BROKEN (`JSON.parse(raw).catch`) | **PRESENT** (`parseChatBody`) |
| pglite absolute path | PARTIAL/MISSING POSIX abs | **PRESENT** (db + `pglite_data_dir`) |
| process-group kill safety (`posix_group_ok`) | MISSING | **PRESENT** |
| engine propose→confirm (F2) | MISSING (direct start/stop) | **PRESENT** |

## M10.1 status & safe fix proposal

- Runner productive? **No — wedged.** Heartbeat WAITING_FOR_CHILD ~45+ min; 10 attempts without AUTOPILOT_RESULT.
- Env (names only): `ANTHROPIC_BASE_URL=https://api.atria-asi.ai`, `ANTHROPIC_MODEL=Atria-Dawn-Preview`.
- Errors: `claude-code:unrecognized_model` for `Atria-Dawn-Preview`; also `429 Token quota exhausted`.
- **Do not invent credentials.** No clearly documented alternate Atria model name found in project docs during this pass.
- Recommended safe actions for Grok/owner (apply only with owner OK):
  1. Pause/skip M10.1 in queue until model works (or set mission PARTIAL) — avoid burning quota.
  2. Unset `ANTHROPIC_MODEL` **or** set it to a model name the Atria gateway actually accepts (confirm via Atria docs/UI — not guessed here).
  3. Keep `ANTHROPIC_BASE_URL` if that gateway is intentional; fixing model alone may be enough.
  4. Do **not** kill PID 4708 / owner interactive Claude; if stopping the wedged autopilot child, target only the autopilot runner after owner approval.

## Autopilot health / HOLD

- `HOLD.flag` exists, length 0, mtime **2026-10-04 02:45** Asia/Tehran.
- `claude_autopilot.ps1`: `$HOLD_HOURS = 6` — hold active only while `(now - mtime) < 6h`.
- Therefore HOLD **expired ~2026-10-04 08:45**; continued missions are consistent with design.
- Watchdog + autopilot both running (PIDs 10452 / 10488) — normal pair, not a double mission launcher by itself.

## What to keep / revert / rework

### Keep
- All M11.1–M11.4 and M48.1 commits on `ahos`.
- This security merge commit + `BOX_PATCHES_MERGED.md`.

### Do not revert
- Box F1/F2/F3 security files (`chat_auth.ts`, session route, engine route, processkit posix_group_ok).

### Rework / next Grok actions
1. **Unblock M10.1 model** (owner-confirmed model name or unset) — then let autopilot retry M10.1 (pglite init in launcher).
2. Optional: run `npm run test:chat-auth` / launcher pytest subset on laptop to harden merge.
3. Optional: finish any PARTIAL patch notes (0003 documented as superseded by Claude identity work).
4. Do **not** push; remain ~52+ commits ahead locally until owner asks.
5. M53 still PENDING — fine.

## Paths note

`chat_auth.ts` and `web_api_client.ts` live at **repo root** (not `lib/`).

