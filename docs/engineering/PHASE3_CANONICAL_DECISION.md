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
| `reasoningEngine.ts` | Uploaded 3D tree — presentation over stored rows; preserved; not Python brain |
| Web trees | Preserved (`advanced-3d-audiovisual-website/`, `(1)`, other uploaded trees) |

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
  - TS WATCH/PAPER_CANDIDATE require injected canonicalBackend
  - pump_alert UNKNOWN+score bypass closed
  - reasoningEngine classified presentation; web trees preserved
  - Lane A not edited
FAILED_GATES: (fill after verification commands)
BLOCKERS:
  - PR #63 (Phase 2) still draft; this branch stacks on it
  - GitHub Actions CI workflow still absent (M-GAP-004)
  - Runtime OPERATIONAL not claimed (no live operator daemon in this environment)
  - TS engine.ts still computes local ranks for display (not canonical BUY)
EVIDENCE:
  - docs/engineering/PHASE3_CANONICAL_DECISION.md
  - tests/test_canonical_decision_authority.py
TEST_RESULTS: see commit / agent report (targeted vs full suite)
REGRESSIONS: opportunity alerts now require verified token+pool identity
KNOWN_LIMITATIONS:
  - identity_from_candidate with a single market source is UNRESOLVED (fail-closed)
  - Web Command Center dual-stack display ranks remain until a Python read-model is served
  - Live execution not implemented (PAPER / intelligence first)
NEXT_UNLOCKED_PHASE: Phase 4 evidence/persistence only after Phase 3 mandatory gates actually pass
```

Do **not** mark COMPLETE from code presence alone.
Do **not** mark OPERATIONAL without a real runtime consumer binding.
