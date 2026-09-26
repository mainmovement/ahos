# AHOS MASTER CANONICAL CONSOLIDATION — FINAL REPORT

**Date:** 2026-09-26
**Scope:** read/inspect/reconcile/consolidate pass over `G:\robat\ahos` and all
external AHOS copies.
**Status:** `COMPLETE` for the reconciliation scope; `PARTIAL` for owner-side
gates (unchanged by this mission — see Q).
**Safety:** Lane A untouched. No external directory modified. Nothing committed
— every change below sits in the working tree for review.

---

## A. CANONICAL ROOT

`G:\robat\ahos` — confirmed canonical. All other copies are historical/external
(see E).

## B. ACTIVE BRANCH

`ahos` (local development branch — this is the correct working branch).

## C. CURRENT HEAD

`4b37be3` (2026-09-24, PR #115).

**Note:** `origin/main` advanced to `8ae411a` mid-session (+2 commits,
PR #116), so `ahos` is now **2 commits behind** `origin/main`. Not pulled —
auto-merge is forbidden by mission rules and by `AGENTS.md`.

## D. TRUTH DOCUMENT CHAIN (verified; every referenced file exists)

`docs/DOC_TRUTH_MAP.md` → `docs/canonical/MASTER_DIRECTIVE_v1.md` +
`master_directive_registry.json` → `docs/canonical/MASTER_DIRECTIVE_W43.md` →
`docs/canonical/PROJECT_STATE.md` → `reports/PHASE_STATE.md` →
`AHOS_GAP_REGISTER.md` → `AHOS_ISSUE_REGISTER.md` →
`AHOS_LOCAL_PRODUCTION_GATE_REPORT.md` →
`docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md` → `AGENTS.md`.

Zero broken pointers in `README.md` or the truth map.
**New:** `docs/CANONICAL_COMMAND_REFERENCE.md` inserted as the single command
authority.

## E. EXTERNAL AHOS COPIES (8 found; all left untouched)

| Path | Classification | Unique value |
|---|---|---|
| `G:\robat\ahos-agent-org\ahos_org` | **DUPLICATE** | None — byte-identical to canonical `ahos_org/`; CRLF/LF-only difference (verified with `diff --strip-trailing-cr`: zero differences) |
| `G:\robat\ahos022\ahos-main` | **SUPERSEDED** | 0 unique files vs canonical working tree; snapshot of the `main@f273feb` era; carries the older `DEVELOPMENT_READY` label and lacks all 2026-09-09 addenda |
| `G:\robat\ahos-push-staging` | **SUPERSEDED** | Strict ancestor of `origin/main` (0 unique commits, 25 behind); remote `github.com/mainmovement/ahos` |
| `G:\robat\ahos-transfer` (git bundle) | **HISTORICAL** | Commit `5e9daf5` is already an ancestor of `origin/main` — PR #93 already merged |
| `G:\Robot_Project\AHOS_BACKUP_2026-08-19` | **HISTORICAL** (backup) | 3 zips, 208 MB; not inspected byte-for-byte; left as owner-held backup |
| `G:\Robot_Project\ahos-grok` | **CONFLICTING** | Divergent parallel TS implementation (`nextjs-postgresql-template`, 648-line `CommandCenter.tsx` vs canonical 1,072-line). **Not imported** — a second brain surface violates `AGENTS.md` |
| `G:\home\user\ahos` | **HISTORICAL** | Legacy Linux data root: 2 tiny SQLite files (16 KB + 0 bytes) |
| `G:\n8n\AHOS` | **SUPERSEDED** | July 2026 docker/n8n stack; zero filename overlap with canonical `n8n/workflows/` |

**Bonus discovery:** `G:\n8n\سند و کتابچه راهبردی` (Persian standards booklet)
held **100 non-empty files (~2.7 MB) of pre-canonical specifications with zero
canonical equivalents** (verified by name search across `docs/`). The only
genuinely unique material found anywhere outside the canonical root.

## F. CONSOLIDATED ARTIFACTS

`docs/CANONICAL_COMMAND_REFERENCE.md` — the ONE canonical command list. Every
command verified against the tree at `4b37be3`: entrypoints exist, documented
flags match the implemented CLI parsers, npm scripts confirmed.

## G. ARCHIVED ARTIFACTS

`docs/archive/consolidation_2026-09-26/` — 106 files: the booklet's standards,
strategic specifications (AECS, AES, DDS, FRS, AIP, SAO, AWC), the
Architecture Bible v4.x archive, ADER/SDR daily reports, and pre-reset n8n
exports; plus `PROJECT_BIBLE.md`. Full provenance in its `MANIFEST.md`
(SOURCE_PATH / SOURCE_DATE / SOURCE_GIT_STATE / REASON_PRESERVED /
CLASSIFICATION).

**Honesty guard embedded in the manifest (binding):** archived titles such as
*"AHOS Architecture Bible v4.1 — Production Lock Edition"* are July 2026
**documentation-freeze** titles, not validated production states. Under
`docs/DOC_TRUTH_MAP.md` §D no readiness claim is current truth without a linked
artifact in `AHOS_GAP_REGISTER.md`; none of these documents is one. The current
honest classification remains `INTEGRATION_READY` (agent-host);
`PRODUCTION_READY` is a forbidden claim. The booklet's "Architecture Freeze
v1.1" is also **not** the operative freeze — the binding freeze is Lane A:
`config/lane_a_freeze.sha256` + `scripts/freeze_lane_a.py` (36 files).

## H. CONFLICTS RESOLVED

1. **The branch discrepancy** — root-caused and closed. The supervision
   documents were **correct**: they refer to GitHub's `main`, which does
   contain `6f61656` (W2, PR #95). The local `main` ref was simply stale
   (0 unique commits, 133 behind; reflog shows it had always been maintained
   by `pull --ff-only origin main`). **Action taken:** a pure fast-forward,
   `git fetch origin main:main`, → `main` == `origin/main` == `8ae411a`. No
   merge, no checkout, no rebase, no force-push. Prior SHA `f273feb` remains
   reachable via `git reflog main`. **No documentation needed correction for
   this item** — the docs were right; the local ref was stale.
2. **W44 naming gap** — `README.md` headlines "W44 Intelligence Tier" but the
   truth map never mentioned it; W44 has a report but no directive. Clarified
   in `docs/DOC_TRUTH_MAP.md` §A that W43 remains the governing directive.
3. **Apparent `architecture.runtime` drift** — investigated and cleared.
   `architecture/runtime` is a package containing `__main__.py`, so
   `python -m architecture.runtime` resolves, and every documented flag
   (`--single-cycle`, `--daemon`, `--observation-cycle`, `--probe-providers`,
   `--snapshot-interval-hours`, `--evidence-source`, …) is implemented.

## I. CONFLICTS REMAINING

- `ahos` is 2 commits behind `origin/main` (PR #116) — intentionally not
  pulled.
- `G:\Robot_Project\ahos-grok` remains an un-reconciled parallel
  implementation, deliberately left external.
- P5 `GOVERNANCE_STATUS=CONTRADICTORY` — unchanged; requires human governance
  ratification, not a code fix.

## J. PATHS NORMALIZED

**None required.** Every `/home/user/ahos` reference falls into one of three
safe categories:

1. **Historical evidence JSON** (`reports/*.json`, `research/experiments/*.json`,
   `docs/mission_v1_1/*`) — records where data lived on the original Linux
   host. Rewriting historical evidence is forbidden; left untouched.
2. **Self-documenting comments** (`config/paths.py`, `engine/doc_hygiene.py`)
   that describe their own path-portability fix.
3. **The one live reference**, `tests/test_ahos.py:22`
   (`UPLOAD_BTC = Path("/home/user/uploads/…")`) — already safely guarded:
   `BTC = str(UPLOAD_BTC if UPLOAD_BTC.exists() else RESEARCH_BTC)`, so it
   falls back to the repo-relative path and is not a live dependency. Left
   unchanged; documented as safe in §9 of the command reference.

## K. COMMANDS NORMALIZED

Consolidated into `docs/CANONICAL_COMMAND_REFERENCE.md`: developer gates,
runtime daemon, scheduler watchdog, Windows operator sequence, soak/backup
tooling, web surface, and git hygiene. The 10 `.bat` operator scripts are
classified as historical convenience wrappers (their tip branch
`cursor/windows-evidence-notify-retarget-4bde` still exists), and their binding
`STATE B: never db:migrate / db:push` rule is carried forward into §0 of the
reference.

## L. DOCUMENTATION UPDATED

| File | Change |
|---|---|
| `docs/DOC_TRUTH_MAP.md` | 4 edits: command-reference rows (§A, §E), archive row (§E), W43/W44 clarification (§A) |
| `README.md` | Canonical-commands row added to the docs table |
| `docs/CANONICAL_COMMAND_REFERENCE.md` | New |
| `docs/archive/consolidation_2026-09-26/MANIFEST.md` | New |

## M. TESTS RUN

| Gate | Result |
|---|---|
| `scripts/freeze_lane_a.py` (verify-only) | **PASS** — Lane-A integrity OK (36 files pinned) |
| `scripts/validate_imports.py` | **FAIL — pre-existing, not caused by this work.** 38 FAIL lines, all `__pycache__/` build artifacts; all gitignored; 0 in `git status`. No source defect. |
| `tests/test_doc_drift.py` | **PASS** 9/9 (re-run after the truth-map edits) |
| `tests/test_one_brain_architecture.py`, `test_paths_and_cross_platform.py`, `test_runtime_lifecycle.py`, `test_runtime_verification_layer.py`, `test_cursor_hook_guard.py` | **PASS** 26/26 |
| `tests/test_observation_runtime.py`, `test_forensic_observability_hardening.py` | **PASS** 43/43 |
| `python -m architecture.runtime --help` | **PASS** — CLI parser and all documented flags verified |
| Secret scan of the imported archive | **CLEAN** — only literal `Bearer <token>` placeholders; no credentials |

## N. GIT STATUS

```
 M .cursor/hooks.json                     (pre-existing, not mine)
 M README.md
 M docs/DOC_TRUTH_MAP.md
?? docs/CANONICAL_COMMAND_REFERENCE.md
?? docs/CONSOLIDATION_REPORT_2026-09-26.md
?? docs/archive/consolidation_2026-09-26/
?? .cursor/hooks.json.local-backup       (pre-existing, not mine)
?? ahos-hooks-local-diff.txt              (pre-existing, not mine)
```

## O. FILES CHANGED

3 modified, 3 new (106 files inside the archive directory).
**Nothing committed** — all changes remain in the working tree for review.

## P. FILES NOT CHANGED FOR SAFETY

- Lane A (`discovery/**`, `paper_trading/**`) — verified untouched.
- All 8 external directories — untouched, in place.
- `G:\n8n\data` runtime SQLite — deliberately not copied into the tree.
- The pre-existing `.cursor/hooks.json` Windows portability fix
  (`python3` → `.venv\Scripts\python.exe` in the guard hooks) — left as found;
  it is not part of this mission.
- Superseded documents — preserved and classified, never deleted.

## Q. REMAINING BLOCKERS

1. `ahos` is 2 commits behind `origin/main` — owner should run
   `git pull --ff-only origin main`.
2. **M-GAP-003** 168h soak (~84H28M evidenced < 168H); **M-GAP-008** scoring
   calibration (0 joined pairs); **M-GAP-009** live Telegram (token rotation
   S-01); Windows operator gates (no
   `reports/operator_validation_report_windows_*.json`). All owner-side;
   unchanged by this mission.
3. `OPERATOR_READY` remains `NOT_VERIFIED`; `PRODUCTION_READY` remains a
   forbidden claim.

---

## NEXT DEVELOPMENT START POINT

**Immediate hygiene (one command):** `git pull --ff-only origin main` on the
`ahos` branch to absorb PR #116 (`deprecate compose_evidence_graph dossier=
kwarg`). The tree is 2 commits behind and that deprecation directly touches the
dossier/evidence-graph surface the next task builds on.

**Then the single highest-value development task — D1: W1.3 identity spoof
hardening + test.**

*Why this one:* the current build directive
(`docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`; council `MONITOR`, build
agent `FIX_BEFORE_CONTINUE`) authorizes Phase 1 only. Of its four items, D2
(merge W2 / #95) is already `COMPLETE` on `main`, and D3/D4 are documentation.
**D1 is the sole incomplete Phase-1 item** — and it is the one the truth model
explicitly flags as "Still verify — not in #95 merge diff". It is purely
build-side, touches no frozen Lane-A code, needs no external service, and is a
security-hardening task, matching `AGENTS.md`'s rule that identity/security work
gets the strongest models plus an independent security reviewer.

**Runs in parallel (owner, not build):** Phase 0 Windows read-only primary
export, per `docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md` v1.2 ONE BEST PATH —
export `opportunity_score_ledger`, `scheduler_runs`,
`canonical_decision_read_model.json`, and the `paper_trading.sqlite` census from
the laptop, then classify the ~2,965 unmatched production rows by `token_id`.
This is the binding constraint on every readiness gate in Q; no amount of build
work substitutes for it.

---

*This report is a consolidation record, not a readiness claim. Canonical truth
remains `docs/DOC_TRUTH_MAP.md`; open gaps remain `AHOS_GAP_REGISTER.md`.*
