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
| `alerts.ts` | UNKNOWN/INCOMPLETE/STALE security cannot alert; WATCH only after TS gate |
Uploaded Web/3D trees (`advanced-3d-audiovisual-website/`,
`(1)`, `سایت درخت…`, `درخت کاملتر…`) are **preserved** and classified as
separate presentation projects. They are excluded from the Command Center
root `tsconfig.json` / ESLint unit so they cannot compile as a hidden second
brain. Each tree keeps its own `package.json`.

---

## Skills

Canonical Cursor skills: `.cursor/skills/` (eleven).  
Repo-root `slills/` is uploaded third-party SKILL dumps — not the AHOS registry.

---

## PHASE_STATUS (Phase 3)

```
PHASE_STATUS: PARTIAL
PASS_GATES:
  - CanonicalDecisionAuthority wrapping DecisionAdvisor
  - identity + security + pool gates on positive rec / alert / paper
  - AI upgrade blocked on failed gates
  - orchestrator wired; score-alone Telegram bypass closed
  - TS WATCH requires injected canonicalBackend
  - pump_alert UNKNOWN+score bypass closed
  - reasoningEngine classified presentation; web trees preserved
  - uploaded Web/3D trees excluded from Command Center tsconfig/eslint (not deleted)
  - Lane A freeze OK (36)
  - validate_imports PASSED (181 modules)
  - targeted pytest 185 passed (identity/security/advisor/alerts/pipeline/panel/one-brain/cursor + canonical authority)
  - Command Center tsc --noEmit exit 0 after excluding uploaded trees
FAILED_GATES:
  - npm run lint: 1 pre-existing CommandCenter.tsx react-hooks/set-state-in-effect (not introduced here)
  - full pytest: 1598 passed, 3 skipped, 1 failed tests/test_config_validation.py (NEXT_PUBLIC_AHOS_WEB_API_TOKEN scanner; pre-existing, unread by Python scan)
BLOCKERS:
  - PR #63 (Phase 2) still draft; this branch stacks on it
  - GitHub Actions CI workflow still absent (M-GAP-004)
  - Runtime OPERATIONAL not claimed (no live operator daemon / browser session)
  - TS engine.ts still computes local ranks for display (not canonical BUY)
  - npm run lint not green on Command Center
EVIDENCE:
  - docs/engineering/PHASE3_CANONICAL_DECISION.md
  - tests/test_canonical_decision_authority.py
  - python3 -B scripts/freeze_lane_a.py → 36 OK
  - python3 scripts/validate_imports.py → 181 modules
  - pytest targeted 185 passed; full 1598 passed / 1 pre-existing fail
  - npm run typecheck exit 0; npm run test:web-api-auth 9 passed
TEST_RESULTS: TARGETED PASS; FULL SUITE NOT PASS (1 pre-existing config-doc fail)
REGRESSIONS: opportunity alerts now require verified token+pool identity
KNOWN_LIMITATIONS:
  - identity_from_candidate with a single market source is UNRESOLVED (fail-closed)
  - Web Command Center dual-stack display ranks remain until a Python read-model is served
  - Live execution not implemented (PAPER / intelligence first)
  - Browser verification: not executed (no UI claim this phase)
NEXT_UNLOCKED_PHASE: Phase 4 evidence/persistence only after Phase 3 mandatory gates actually pass
```

Do **not** mark COMPLETE from code presence alone.
Do **not** mark OPERATIONAL without a real runtime consumer binding.
