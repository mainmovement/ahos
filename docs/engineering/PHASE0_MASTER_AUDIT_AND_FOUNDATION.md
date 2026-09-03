# AHOS Phase 0 — Master audit and engineering foundation

**Baseline:** `f67eb483396eb0808d6fcc8b1b0b322c856b2167` (`main`)  
**Branch:** `cursor/phase0-engineering-foundation-9500`  
**Date:** 2026-09-03  
**Classification:** `INTEGRATION_READY` (agent-host). `OPERATOR_READY` = NOT_VERIFIED.  
**Lane A freeze:** 36 files pinned — verified at audit start.  
**Law:** statuses are repository reality. Phase 0 does not implement identity, security overlay, web locales, market websockets, or Telegram live E2E.

This document is the required pre-implementation audit (sections 1–10) plus the Phase 0 gate record. It does not rewrite historical evidence files.

---

## 1. CURRENT CAPABILITY MATRIX

| Capability | Status | Evidence |
|---|---|---|
| Cursor `AGENTS.md` / `.cursor/**` | **MISSING → this PR** | Absent on `main`; added in Phase 0 |
| Lane A freeze | **EXISTING / FROZEN** | `config/lane_a_freeze.sha256`, `scripts/freeze_lane_a.py` |
| Python intelligence floor | **EXISTING** | `architecture/intelligence/engine.py` |
| Decision advisor (AI downgrade) | **PARTIAL** | `architecture/decision/advisor.py` tested; not wired into `orchestrator.py` |
| TS scoring/council/engine | **DUPLICATED** | `scoring.ts`, `council.ts`, `engine.ts` — second brain |
| Canonical identity types (Chain/Token/Pool/DEX/Resolution + states) | **MISSING** as named model; **PARTIAL** Lane A hashes | `discovery/identity.py` FROZEN |
| Security gate PASS/REJECT/INCOMPLETE/STALE | **PARTIAL** | Lane A `SECURITY_VETO` / `PASS_WITH_UNKNOWN` / `PASS` |
| Independent 0–100 score family (8 series) | **PARTIAL** | Opportunity 0–100 exists; others labels/penalties |
| Evidence raw+provenance Lane A | **EXISTING / FROZEN** | `raw_payloads`, INSERT OR IGNORE |
| Evidence policy version on atoms | **PARTIAL** | On scores/features, not raw atoms |
| Web Command Center (FA/RTL SPA) | **EXISTING** | `CommandCenter.tsx`, `app/page.tsx` |
| `/[locale]/*` bilingual routes | **MISSING** | layout `lang="fa"` only |
| Wise Tree | **MISSING** | no identifiers |
| Environment engine (geo/weather/season) | **MISSING** | |
| WebSocket / L2 / Rust market engine | **MISSING** | H8 DATA-BLOCKED |
| Paper trading Lane A | **EXISTING / FROZEN** | `paper_trading/*.py` |
| Paper trading TS/Telegram | **DUPLICATED** | Postgres `addPaper`; unused Telegram ledger |
| Backtesting / leakage controls | **EXISTING** | `strategy_lab/`, L1–L4, causal candidates |
| AI Council 10 families + 2–4 routing + cache | **PARTIAL** | panel runs all lenses; no evidence-hash cache |
| Telegram gateway W57 | **PARTIAL** | Gateway exists; live E2E **BLOCKED** (token) |
| Telegram HTML escape | **BROKEN** | `alerts.ts` `escapeHtml` is a no-op |
| GoPlus missing fields | **BROKEN** | adapter defaults honeypot missing → False |
| Alerts web UI | **BROKEN** wiring | `/api/alerts` exists; Command Center does not fetch it |
| Calibration measurement | **BLOCKED** | infra exists; no local outcome pairs |
| GitHub Actions | **BLOCKED** | M-GAP-004 workflows permission; template only |
| CI template | **EXISTING** | `deployment/github-actions-ci.yml.template` |
| Real-money execution | **EXISTING disabled** | hygiene veto, `PAPER_ONLY` |
| n8n | **PARTIAL** | JSON valid; runtime **BLOCKED** creds/host |

---

## 2. ARCHITECTURE GAP MATRIX

| Gap | Target phase | Notes |
|---|---|---|
| Cursor engineering system | **0** | This PR |
| Lane B identity resolution overlay | 1 | Wrap frozen `token_id`; do not edit `identity.py` |
| Security overlay + GoPlus UNKNOWN fix | 2 | Do not rename frozen gate enums in Lane A |
| Wire DecisionAdvisor; stop widening TS brain | 3 | One ordered pipeline |
| Unified evidence document + immutability | 4 | |
| Market websocket analytics | 5 | Measure latency; no HFT claim |
| Unify paper surfaces + backtest ledger | 6 | TS paper ≠ Lane A engine |
| Council 2–4 router + cache | 7 | |
| Bilingual routes + chat as client | 8 | Preserve Command Center |
| Telegram parse()+gates+live E2E | 9 | No live claim without live evidence |
| Environment engine | 10 | |
| Wise Tree | 11 | Visualization only |
| 3D/audio/a11y | 12 | Audio off by default |
| Alert dedupe + sound arm | 13 | Canonical events only |
| Calibration from real pairs | 14 | No silent weight mutation |
| Production-readiness | 15 | Requires operator soak/Telegram/CI |

---

## 3. DUPLICATION / CONFLICT MAP

| Pair | Conflict | Rule going forward |
|---|---|---|
| `discovery/identity.py` vs `types.ts` `tokenKey` | Solana lowercased; symbol can be the key | Python `token_id` is canonical |
| Lane A `security_gate` vs Lane B `architecture/security` vs TS `fetchSecurity` | Three verdict vocabularies | Compose; do not add a fourth |
| `IntelligenceEngine` vs `scoring.ts` | Dual numeric engines | Do not grow TS authority |
| `architecture/council.py` vs `council.ts` | Heuristic 100-role UI vs advisory Python | Python advisory; TS display |
| `paper_trading/` vs `engine.ts` `addPaper` vs `telegram_ai/positions.py` | Three paper ledgers | Lane A scientific; others must not bypass gates |
| `alerts.ts` vs `telegram_ai/pump_alert.py` vs `architecture/alerts/engine.py` | Duplicate alert emitters | Canonical decision events only |
| `architecture/intel/whales.py` vs `architecture/intelligence/whales/` | Two whale stacks | Reuse; do not add a third |
| Root `ARCHITECTURE.md` vs `docs/canonical/ARCHITECTURE.md` | Split docs | Canonical dir wins |
| PR #17 env setup vs this `.cursor/environment.json` | Conflicting, unsafe start/install | **Do not merge PR #17 as written** |

---

## 4. DEPENDENCY GRAPH

```
Phase 0 foundation
  → Phase 1 identity (Lane B overlay)
    → Phase 2 security overlay (needs identity states)
      → Phase 3 canonical decision (needs identity+security)
        → Phase 4 evidence/ops
          → Phase 5 market engine (optional parallel after 3 for analytics-only)
          → Phase 6 paper/backtest (needs decision+security)
            → Phase 7 AI council (needs immutable evidence packet)
            → Phase 8 web (needs canonical read model)
              → Phase 9 Telegram (needs gateway + identity UX)
              → Phase 10 environment (web)
              → Phase 11 Wise Tree (needs evidence graph)
              → Phase 12 visual/audio (web)
              → Phase 13 alerts/monitoring
                → Phase 14 calibration (needs outcomes)
                  → Phase 15 production-readiness
```

Phase 5 may be prototyped after Phase 3 but must not emit paper/alerts before Phase 6 gates.

---

## 5. SECURITY / GOVERNANCE RISKS

| Risk | Severity | Phase 0 treatment |
|---|---|---|
| Lane A silent edit | Critical | Rule + hook deny + freeze test; hooks are not a boundary |
| TS second brain | High | Recorded; not fixed in Phase 0 (keeps PR reviewable) |
| GoPlus fail-open | High | Recorded; fix in Phase 2 |
| Telegram HTML injection | High | Recorded; fix with alerts work (Phase 8/9/13) |
| `NEXT_PUBLIC_AHOS_WEB_API_TOKEN` | High | Contract forbids new client secrets |
| PR #17 drizzle push / `.env` copy / postgres password | High | New environment.json forbids those actions |
| Empty VM DB filed as soak | High | AGENTS.md + start.sh never init stores |
| GitHub workflow permission | Med | CI file not added (would block push); template remains |
| CODEOWNERS without branch protection | Med | File is documentation until protection is enabled |
| Hook regex bypass | Med | Stated in AGENTS.md |

Forbidden plugins remain uninstalled: Superpowers, ralph-loop, Continual Learning.

---

## 6. IMPLEMENTATION ORDER

Executed now: **Phase 0 only**.  
Next unlocked after Phase 0 `COMPLETE`: **Phase 1 Canonical Identity (Lane B overlay)**.  
Do not skip to web locales, websockets, or Telegram live work.

---

## 7. EXACT FILES / MODULES TO CHANGE (Phase 0)

Added: `AGENTS.md`, `.cursor/**` (rules, agents, 11 skills, hooks, worktrees, environment, install/start), `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, `tests/test_cursor_*.py`, `scripts/verify_cursor_foundation.py`, this document.

Modified: `.gitignore`, `docs/DOC_TRUTH_MAP.md` (pointer row only).

Later phases (not this PR): `architecture/` identity/security/decision modules, `types.ts` tokenKey bridge, `adapters.py` GoPlus UNKNOWN, `alerts.ts` escapeHtml, `app/[locale]/…`, market websocket package, etc.

---

## 8. EXACT FILES THAT MUST REMAIN FROZEN

All paths in `config/lane_a_freeze.sha256` (36 files), generated from:

- `discovery/*.py`
- `discovery/schema_sqlite.sql`
- `discovery/providers.yaml`
- `paper_trading/*.py`
- `paper_trading/schema.sql`
- `paper_trading/schema_v2.sql`
- `paper_trading/schema_v3.sql`

Also do not mutate: `docs/canonical/MASTER_DIRECTIVE_v1.md`, existing `reports/**` evidence, operator `.env`, SQLite stores under `data/`.

`paper_trading/strategies.json` is not hash-pinned; still not silently promoted.

---

## 9. TEST PLAN (Phase 0)

- `python3 -B scripts/freeze_lane_a.py`
- `python3 -m pytest tests/test_cursor_engineering_foundation.py tests/test_cursor_hook_guard.py`
- `python3 scripts/verify_cursor_foundation.py`
- `python3 scripts/validate_imports.py` when feasible (clean-tree import/secrets/freeze)

Not in Phase 0: browser flows (no UI change), Telegram live E2E, soak, full pytest of unrelated suites unless freeze/import requires it.

---

## 10. ACCEPTANCE CRITERIA (Phase 0)

COMPLETE only if:

1. `AGENTS.md` exists and pins One-Brain / freeze / PAPER_ONLY / hook limitation.
2. Lane A rule exists; freeze verification passes.
3. Eleven Skills and four subagents exist.
4. Worktree + environment scripts exist and do not init DBs or drizzle-push.
5. PR template + CODEOWNERS exist.
6. No forbidden automation enabled.
7. Foundation tests pass.
8. No Lane A file in the diff.
9. No secrets committed.

GitHub Actions workflow copy remains **BLOCKED** (M-GAP-004) unless `workflows` permission is granted.

---

## PHASE_STATUS (Phase 0)

```
PHASE_STATUS: COMPLETE
PASS_GATES:
  - AGENTS.md authoritative contract
  - Lane A freeze CLI OK (36 files)
  - 11 Skills + 4 subagents + 4 rules + hooks + worktrees + environment
  - PR template + CODEOWNERS
  - foundation pytest 11 passed
  - validate_imports PASSED (171 imports, freeze, secrets)
  - no Lane A paths in diff
  - historical reports restored after import side-effects
FAILED_GATES: none for Phase 0 scope
BLOCKERS:
  - .github/workflows/ci.yml not added (M-GAP-004 GitHub App workflows permission)
  - CODEOWNERS unenforced until branch protection requires it
EVIDENCE:
  - docs/engineering/PHASE0_MASTER_AUDIT_AND_FOUNDATION.md
  - pytest tests/test_cursor_engineering_foundation.py tests/test_cursor_hook_guard.py
  - python3 -B scripts/freeze_lane_a.py
  - python3 -B scripts/validate_imports.py
TEST_RESULTS: 11 passed / 0 failed (foundation); validate_imports VALIDATION PASSED
REGRESSIONS: none. validate_imports import probes can rewrite reports/*.json via
  module import side-effects; those files were restored and are not in this commit.
KNOWN_LIMITATIONS:
  - Hooks are defense-in-depth, not a filesystem boundary
  - TypeScript second brain / GoPlus fail-open / Telegram HTML escape unchanged
  - PR #17 must not be merged as written
NEXT_UNLOCKED_PHASE: Phase 1 Canonical Identity (Lane B overlay; Lane A frozen)
```
