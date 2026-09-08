# AHOS Phase 3 — Canonical Decision Authority

**Branch:** `cursor/phase3-canonical-decision-9500`  
**Stacked on:** Phase 2 `cursor/phase2-security-gate-9500` (`711bcd3`, PR #63 draft)  
**Date:** 2026-09-08  
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

* **PR #63** Phase 2 security overlay — OPEN DRAFT, MERGEABLE, head `711bcd3`
* **PR #64** Phase 3 — OPEN DRAFT, stacked on #63 (`711bcd3` is merge-base)
* Phase 3 work on this branch includes Phase 2 commits until #63 merges.
* Do **not** merge #63 or #64 automatically. Validation of #64 does not assume #63 is on `main`.

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
  - CanonicalDecisionAuthority wrapping DecisionAdvisor
  - Python canonical read-model writer + TS presentation overlay
  - Command Center /api/canonical + fail-closed snapshot (DB down still shows Python cards)
  - paper/chat/alerts.ts gated on Python paper_allowed / alerts_allowed
  - engine.ts persists Python displayDecision (not TS WATCH)
TESTED: pending re-run on this revision (see following commit evidence)
VERIFIED:
  - (none this revision until API + browser evidence is recorded)
BLOCKED:
  - PR #63 still draft; do not auto-merge; #64 remains stacked
  - GitHub Actions CI workflow still absent (M-GAP-004)
  - Postgres/DATABASE_URL often unset in agent shell — Command Center opportunity rows ENVIRONMENT
  - Live operator daemon / OPERATIONAL not claimed
PRE-EXISTING:
  - npm run lint: CommandCenter.tsx react-hooks/set-state-in-effect
  - tests/test_config_validation.py NEXT_PUBLIC_AHOS_WEB_API_TOKEN Python-scan miss
PASS_GATES (prior revision, still in tree):
  - identity + security + pool gates on positive rec / alert / paper
  - AI upgrade blocked on failed gates
  - orchestrator wired; score-alone Telegram bypass closed
  - pump_alert UNKNOWN+score bypass closed
  - reasoningEngine classified presentation; web trees preserved and excluded from CC compile
  - Lane A freeze OK (36) before this revision
FAILED_GATES:
  - lint not green (PRE-EXISTING)
  - full pytest not fully green (PRE-EXISTING config-doc fail)
  - browser Command Center with live Postgres opportunity overlay: not yet VERIFIED
EVIDENCE:
  - docs/engineering/PHASE3_CANONICAL_DECISION.md
  - tests/test_canonical_decision_authority.py
  - tests/test_canonical_read_model.py
  - scripts/canonical_read_model_selftest.ts
TEST_RESULTS: see later revision notes after pytest/typecheck/build/browser
KNOWN_LIMITATIONS:
  - identity_from_candidate with a single market source is UNRESOLVED (fail-closed)
  - engine.ts display ranks remain presentation-only
  - Live execution not implemented (PAPER / intelligence first)
NEXT_UNLOCKED_PHASE: Phase 4 evidence/persistence only after Phase 3 mandatory gates actually pass
```

Do **not** mark COMPLETE from code presence alone.
Do **not** mark OPERATIONAL without a real runtime consumer binding.
