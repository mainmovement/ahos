# AHOS Phase 3 — Canonical Decision Authority

**Branch:** `cursor/phase3-overlay-python-on-main-9500` (status docs on current `main`)  
**Base:** `origin/main` after PR **#66**, **#67**, and **#68** merge (`0cbe393`). Overlay-v2 already on `main` via **#65**.  
**Date:** 2026-09-09  
**Classification:** `INTEGRATION_READY` (unchanged).  
**Lane A freeze:** must remain 36 files — verify with `python3 -B scripts/freeze_lane_a.py`.

Does **not** edit frozen `discovery/**` or `paper_trading/**`.
Does **not** delete uploaded Web/3D trees or `scoring.ts`.

---

## Canonical authority

**Location:** `architecture/decision/authority.py`  
**Class:** `CanonicalDecisionAuthority`  
**Wraps:** existing `DecisionAdvisor` (not a second brain)

`OpportunityScorer` remains a **score**. Alerts, Telegram, paper eligibility,
and presentation layers consume `CanonicalDecision`.

### Pipeline order

```
IDENTITY
  → EVIDENCE INTEGRITY / FRESHNESS
  → SECURITY overlay (PASS / REJECT / INCOMPLETE / STALE)
  → LIQUIDITY / EXITABILITY
  → DETERMINISTIC OPPORTUNITY SCORING
  → RISK
  → CONFIDENCE  (independent of opportunity_score)
  → OPTIONAL AI CHALLENGE (DOWNGRADE / ABSTAIN only)
  → CANONICAL DECISION
```

### Outcomes

Maps advisor `ENTER` / `WAIT` / `AVOID` onto:

`BUY` / `WATCH` / `SKIP` / `REJECT` / `INSUFFICIENT_EVIDENCE` /
`HIGH_RISK` / `MONITOR_ONLY` / `NO_TRADE`

Positive recommendation (`is_positive` / alerts / paper) **only** when:

* token identity `VERIFIED`
* pool identity `VERIFIED` and bound to the token
* security overlay `PASS`
* advisor action `ENTER`
* no hard vetoes

Verified token + unresolved/missing pool ⇒ `MONITOR_ONLY` (no pool liquidity
claim, no opportunity alert, no paper candidate).

`NO_TRADE` is a valid intelligent outcome.

### Gates

| Gate | Failure ⇒ |
|------|-----------|
| Identity INVALID / CONFLICT / UNSUPPORTED | `REJECT`, no positive |
| Identity UNRESOLVED / MISSING | `INSUFFICIENT_EVIDENCE` |
| Identity STALE | `NO_TRADE` |
| Security REJECT | `REJECT` |
| Security INCOMPLETE | `INSUFFICIENT_EVIDENCE` |
| Security STALE | `NO_TRADE` (cannot look like fresh PASS) |

AI cannot upgrade a closed identity or security gate. AI may downgrade.

---

## Downstream

| Surface | Role after Phase 3 |
|---------|--------------------|
| Orchestrator | Calls authority after scoring; Telegram “فرصت ویژه” requires canonical BUY |
| AlertEngine OPPORTUNITY | Requires `canonical.alerts_allowed` |
| `telegram_ai/pump_alert.py` | Requires `canonicalOutcome=BUY` or `advisor_action=ENTER`; UNKNOWN security cannot alert |
| Paper | Lane A untouched. Lane B `paper_candidate_allowed()` |
| Telegram service | Still must not import OpportunityScorer or instantiate a second authority |
| `scoring.ts` | Presentation. WATCH/PAPER_CANDIDATE blocked unless `canonicalBackend` injected |
| `alerts.ts` | Opportunity alerts require Python `alerts_allowed` (BUY). TS WATCH cannot mint an alert |
| Command Center | Reads Python JSON via `/api/canonical` + snapshot overlay. Missing/stale ⇒ UNAVAILABLE/STALE, never invented BUY |
| `engine.ts` | Injects Python read-model as `canonicalBackend`; persists `displayDecision` from Python, not TS WATCH |
| Paper `/api/paper` + chat | `paperAllowedFromCanonical` — 403 `CANONICAL_PAPER_DENIED` without Python BUY |

Uploaded Web/3D trees (`advanced-3d-audiovisual-website/`,
`(1)`, `سایت درخت…`, `درخت کاملتر…`) are **preserved** and classified as
separate presentation projects. They are excluded from the Command Center
root `tsconfig.json` / ESLint unit so they cannot compile as a hidden second
brain. Each tree keeps its own `package.json`.

---

## Python → Command Center read model

**Not a second brain.** Python `CanonicalDecisionAuthority` writes
`reports/canonical_decision_read_model.json` (override:
`AHOS_CANONICAL_READ_MODEL`). TypeScript only parses and presents.

| File | Role |
|------|------|
| `architecture/decision/read_model.py` | Writer + fail-closed loader (missing/corrupt/stale) |
| `architecture/pipeline/orchestrator.py` | Persists after each decide loop |
| `canonical_read_model.ts` | Parser, overlay, `presentCanonicalDecisions` |
| `app/api/canonical/route.ts` | Auth-gated GET of the Python file |
| `snapshot.ts` | Loads Python model **before** Postgres; on DB failure still returns canonical cards |
| `CommandCenter.tsx` | Renders Python cards; WATCH/NO_TRADE/MONITOR_ONLY are amber, not green |

Fail-closed rules:

* Missing/corrupt file ⇒ `UNAVAILABLE`, empty decisions, no paper, no alerts
* Older than 24h ⇒ `STALE`; `is_positive` / `paper_allowed` / `alerts_allowed` stripped
* Unmatched Command Center token ⇒ display `UNAVAILABLE` (not TS WATCH)
* Postgres down ⇒ empty opportunity rows + Python cards if the file is present (not invented BUY)

---

## Phase dependency (do not auto-merge)

Live GitHub truth as of 2026-09-09:

* **PR #62** Phase 0–1 identity overlay — **MERGED**
* **PR #64** Phase 3 Canonical Decision Authority — **MERGED** first (stacked only on overlay commit `711bcd3`)
* **PR #65** overlay-v2 reconcile onto merged Phase 3 — **MERGED**
* **PR #66** config-doc scanner (`web_api_client.ts`) — **MERGED**
* **PR #67** Command Center set-state-in-effect — **MERGED**
* **PR #68** overlay pythonBin NFT / `next build` panic — **MERGED**
* **PR #63** Phase 2 original overlay-v2 branch — still **OPEN**, **CONFLICTING**, **SUPERSEDED**. Do **not** merge #63.
* Phase 3 remains **PARTIAL**. Do **not** start Phase 4. Do **not** auto-merge.

---

## Bypass audit (this revision)

Searched Python, TypeScript Command Center, Telegram, alerts, paper, pump alerts,
AI council, API routes, `reasoningEngine.ts`, `scoring.ts`, `engine.ts`,
orchestrator, uploaded Web trees.

| Path | Result |
|------|--------|
| Python AlertEngine OPPORTUNITY | Gated on `canonical.alerts_allowed` |
| Orchestrator Telegram “فرصت ویژه” | Gated on `top_canonical.alerts_allowed` |
| `telegram_ai/pump_alert.py` | Requires BUY/ENTER; UNKNOWN security cannot alert |
| `scoring.ts` | Cannot emit WATCH without injected `canonicalBackend` |
| `alerts.ts` | **Fixed this revision:** was alerting on TS WATCH after injection; now requires Python `alerts_allowed` |
| `engine.ts` persist | **Fixed this revision:** stores Python `displayDecision`, not TS WATCH |
| `/api/paper` + chat paper | Requires Python `paper_allowed` |
| Command Center | Overlays Python; unavailable ⇒ UNAVAILABLE |
| `reasoningEngine.ts` + uploaded trees | Preserved presentation; excluded from CC compile unit |
| Council votes WATCH | Advisory display only |

Remaining dual-stack: `engine.ts` still computes **display ranks** (`rankScore`).
Those ranks are not BUY/WATCH authority. Command Center labels display rank as
non-canonical.

---

## Evidence classes

Use these labels only as defined:

* **IMPLEMENTED** — code is in the tree
* **TESTED** — named command was executed in this environment
* **VERIFIED** — TESTED plus the actual consumer path (API/UI/runtime) was observed
* **BLOCKED** — cannot proceed without an external dependency
* **PRE-EXISTING** — failure also present on parent / not introduced here

Do not convert IMPLEMENTED into VERIFIED without evidence.

---

## Skills

Canonical Cursor skills: `.cursor/skills/` (eleven).  
Repo-root `slills/` is uploaded third-party SKILL dumps — not the AHOS registry.

---

## PHASE_STATUS (Phase 3)

```
PHASE_STATUS: PARTIAL
IMPLEMENTED:
  - CanonicalDecisionAuthority wrapping DecisionAdvisor (not a second brain)
  - Pipeline: IDENTITY → EVIDENCE → SECURITY → LIQUIDITY/EXITABILITY → SCORE → RISK → CONFIDENCE (independent) → optional AI DOWNGRADE → CANONICAL DECISION
  - Python JSON read-model writer (orchestrator persist)
  - Command Center /api/canonical + snapshot overlay + fail-closed snapshot when Postgres is down
  - paper/chat require Python paper_allowed (403 CANONICAL_PAPER_DENIED)
  - alerts.ts requires Python alerts_allowed (TS WATCH cannot mint opportunity alerts)
  - engine.ts persists Python displayDecision, not TS WATCH
TESTED:
  - python3 -B scripts/freeze_lane_a.py → Lane-A integrity OK (36 files) before and after this revision
  - npm run test:canonical-security → 16 passed (Telegram mocked + live overlay_query spawn)
  - npm run typecheck → exit 0
  - npx eslint . --max-warnings 0 → exit 0 (#67 closed CommandCenter set-state-in-effect on main)
  - npm run build → exit 0; routes ƒ /api/canonical and ƒ /api/paper present
  - prior #66: tests/test_config_validation.py 3 passed; full pytest 1648 passed / 3 skipped / 0 failed
VERIFIED (narrow, prior #64/#65 environment; not re-claimed here):
  - GET /api/canonical + GET /api/command with fixture: AVAILABLE, 5 Python outcomes (BUY, MONITOR_ONLY, NO_TRADE, REJECT, INSUFFICIENT_EVIDENCE), 0 DB opportunity rows, no invented BUY
  - POST /api/paper unmatched/STALE/UNAVAILABLE → 403 CANONICAL_PAPER_DENIED
  - POST /api/paper fixture BUY → canonical gate passed, then 500 DATABASE_URL (ENVIRONMENT)
  - Browser Command Center dash + فرصت‌ها: Python cards rendered; empty DB copy; BUY green; MONITOR_ONLY/NO_TRADE/INSUFFICIENT_EVIDENCE amber; REJECT rose; UNAVAILABLE banner when file missing
NOT VERIFIED:
  - Command Center overlay of live Postgres opportunity rows from a running observation daemon
  - Browser STALE banner (STALE proven via API only)
  - Isolated loading-flash screenshot (page loaded before capture)
  - OPERATIONAL product runtime (no Postgres, start.sh does not start Next)
BLOCKED:
  - GitHub Actions CI workflow absent (M-GAP-004) — GitHub App lacks `workflows` permission
  - DATABASE_URL unset in this agent shell — paper persist + DB opportunity overlay ENVIRONMENT
  - PR #63 remains OPEN/CONFLICTING/SUPERSEDED — do not merge; overlay-v2 already on main via #65
PRE-EXISTING:
  - Next Turbopack NFT warning tracing canonical_read_model.ts / process.cwd() (warning, not the former python symlink panic)
NEW failures this revision:
  - none
ENVIRONMENT:
  - validate_imports ARTIFACTS fail when .pytest_cache exists after pytest; clean tree + PYTHONDONTWRITEBYTECODE passes
  - Next Turbopack NFT warning on canonical_read_model.ts filesystem path
FAILED_GATES (phase cannot be VERIFIED/COMPLETE):
  - no GitHub CI
  - live daemon + Postgres Command Center overlay missing
CLOSED on main / this revision:
  - #66 SCAN_TS_FILES includes web_api_client.ts; full pytest 0 failed
  - #67 Command Center set-state-in-effect; eslint exit 0 on this tree
  - #68 next build no longer panics on overlay python interpreter symlink
EVIDENCE:
  - docs/engineering/PHASE3_CANONICAL_DECISION.md
  - canonical_security.ts pythonBin()
  - tests/test_config_validation.py
TEST_RESULTS: freeze 36 OK; canonical-security 16 passed; typecheck 0; eslint 0; next build 0. Phase 3 stays PARTIAL.
KNOWN_LIMITATIONS:
  - identity_from_candidate with a single market source is UNRESOLVED (fail-closed)
  - engine.ts display ranks remain presentation-only (labeled غیرکانونیکال)
  - Live execution not implemented (PAPER / intelligence first)
  - FROZEN paper_trading.entry_rules still treats PASS_WITH_UNKNOWN as QUALIFIED_ENTRY
NEXT_UNLOCKED_PHASE: Phase 4 must not start. Phase 3 is PARTIAL, not VERIFIED. Merging #66/#67 and greening next build does not make the phase VERIFIED.
```

Do **not** mark COMPLETE from code presence alone.
Do **not** mark OPERATIONAL without a real runtime consumer binding.
