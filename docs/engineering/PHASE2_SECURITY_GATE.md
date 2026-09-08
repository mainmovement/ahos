# AHOS Phase 2 — Security gate overlay

**Base:** `origin/main` after PR #62 merge plus later Windows/upload commits.  
**Branch:** `cursor/phase2-security-gate-9500`  
**PR:** #63 (OPEN / DRAFT; do not merge from this session)  
**HEAD at this revision:** see git on the branch (policy `security-overlay-v2`)  
**Classification:** `INTEGRATION_READY` (unchanged).  
**Lane A freeze:** 36 files pinned — verified before and after this revision.

Does **not** edit frozen `discovery/security_gate.py` or `paper_trading/security_multi.py`.
Lane A enums remain `SECURITY_VETO` / `PASS_WITH_UNKNOWN` / `PASS`.

---

## Reality notes (this session)

- PR #62 (Phase 0–1) is **MERGED**. Identity overlay is on `main`.
- PR #64 (Phase 3) depends on this overlay historically; this task does **not**
  modify or merge #64.
- `G:\robat\ahos\cursor\slills` is **not in this repository**. Canonical skills
  are `.cursor/skills/`.
- Uploaded `advanced-3d-audiovisual-website/` on `main` is a parallel frontend,
  not wired as authority.
- An earlier Phase 2 draft copied `evaluate()` into `_lane_a_evaluate()` and
  claimed COMPLETE. That copy is **removed**. Status below is re-evaluated.

---

## Architecture (binding)

Lane A remains the frozen evidence-producing security layer:

- registry: `discovery.security_gate.VETO_REGISTRY`
- evaluator: `discovery.security_gate.evaluate`
- LP compound check: `discovery.security_gate.lp_fresh_pool_check`

Lane B is the decision-facing overlay (`architecture/security/gate.py`):

1. Project `SecuritySignals` onto Lane-A **CRITICAL** check keys.
2. Call frozen `evaluate(rows)`.
3. Map verdicts:
   - `SECURITY_VETO` → `REJECT`
   - `PASS_WITH_UNKNOWN` → `INCOMPLETE`
   - `PASS` → `PASS` only if overlay extras also resolve
4. Overlay extras may only **tighten** (cannot_sell_all True → REJECT;
   cannot_sell_all None → INCOMPLETE; exitability TRAPPED → REJECT;
   stale evidence → STALE unless already REJECT).

`POLICY_VERSION = security-overlay-v2`

### CRITICAL vs HIGH (do not confuse the registry)

Frozen `VETO_REGISTRY` has **10** keys. Only **7** are CRITICAL (veto):

- `honeypot`
- `sell_tax_extreme`
- `blacklist_function`
- `mint_authority_active`
- `freeze_authority_active`
- `lp_not_locked_fresh_pool`
- `deployer_prior_rug`

HIGH (not veto; overlay must not invent a veto):

- `proxy_risk_upgradeable`
- `ownership_renounced_absent`
- `holder_concentration_high`

Lane B projects all seven CRITICAL keys. Expanding projection to HIGH would
invent a new policy.

### Why Lane B may import `discovery.security_gate`

Same composition pattern as `architecture/identity` wrapping
`discovery.identity`. This is **one security policy**, not a second brain.
`architecture/security/gate.py` may import **only** `discovery.security_gate`.
Other experiment packages remain forbidden under `architecture/security/`.

Direct import is the adapter/contract boundary. Copying `evaluate()` was the
divergence risk; it is gone (`test_no_copied_lane_a_evaluator_in_overlay`).

### Drift protection (without editing Lane A)

- Overlay imports live `CRITICAL` / `VETO_REGISTRY` / `evaluate`.
- `SIGNAL_CRITICAL_PROJECTION` must equal the live CRITICAL set
  (`test_critical_set_is_frozen_lane_a_not_the_full_registry`).
- A future CRITICAL key not projected is omitted from rows → frozen
  `evaluate()` treats a missing row as UNKNOWN → `PASS_WITH_UNKNOWN` →
  overlay `INCOMPLETE` (`test_future_unprojected_critical_cannot_pass`).
- Missing pool age uses Lane A's `lp_fresh_pool_check` (UNKNOWN), not a
  Lane-B reinterpretation of locked-without-age as FALSE.

### Answers to the architecture questions

| Q | Answer |
|---|--------|
| A. Consume frozen evaluator without violating isolation? | Yes: import/call `discovery.security_gate`, as identity already does. Isolation test was narrowed to that one module. |
| B. Adapter boundary? | Lane B projects signals → check rows; Lane A evaluates; Lane B maps + extras. |
| C. If mirroring required? | Mirroring `evaluate()` is **not** required and was removed. |
| D. All Lane-A CRITICAL checks? | Yes, all **CRITICAL** (7). Not all registry keys (10). |
| E. Future new CRITICAL? | Unprojected key → missing row → INCOMPLETE. Equality test fails until projection is updated under a freeze exception. |
| F. Lane-B PASS while a Lane-A CRITICAL is unresolved? | No. Missing/UNKNOWN critical → PASS_WITH_UNKNOWN → INCOMPLETE. |
| G. Downgrade SECURITY_VETO? | No. extras/stale cannot turn REJECT into PASS. |

---

## Security behavior

| Overlay | Meaning | Positive eligibility |
|---------|---------|----------------------|
| PASS | All CRITICAL resolved FALSE and extras resolved | Allowed (still subject to identity/exitability/score) |
| REJECT | Confirmed critical / unsellable / trapped | Never |
| INCOMPLETE | Missing object, UNKNOWN critical, missing extras | Never |
| STALE | Evidence older than 24h and not already REJECT | Never |

UNKNOWN critical evidence is never treated as safe.
Missing security object → INCOMPLETE.
Confirmed honeypot / unsellable / trapped → REJECT.
Stale does not wash out REJECT.

AI council cannot upgrade REJECT or INCOMPLETE.
Frontend / Telegram / alerts / paper helper cannot override this overlay
on Python Lane B paths.

---

## Provider normalization

Fail-closed: missing boolean security fields stay `None` (UNKNOWN). Missing
must not become `False`.

- **GoPlus:** `_tri_bool` / `_maybe_tax_pct`; missing `is_honeypot` stays None;
  taxes as percent; ownership from `can_take_back_ownership` (None stays None);
  mint `is_mintable`; freeze `transfer_pausable` / `is_freezable`; blacklist
  `is_blacklisted` / `is_in_blacklist`; `cannot_sell_all`; proxy `is_proxy`.
- **RugCheck:** missing `risks` ⇒ `is_honeypot=None` (not inferred from `[]`);
  empty `risks: []` ⇒ honeypot False (explicit empty list); mint/freeze only
  from `mintAuthority` / `freezeAuthority` keys (absent ⇒ None).
- **DEXTools:** `_flag` yes/no/unknown; proxy does **not** invent
  `is_ownership_renounced`; taxes normalized to percent.

---

## Decision / alert / paper eligibility

- `DecisionAdvisor` GATE 1: `security_allows_positive_eligibility`; AVOID if
  not PASS. AI ratchet-down only after gates.
- `AlertEngine` OPPORTUNITY: requires `security_allows_alert`.
- Pipeline Telegram «فرصت ویژه»: requires overlay PASS (score ≥ 75 is not enough).
- `telegram_ai/pump_alert.py`: `securityStatus` must be PASS; score cannot
  substitute UNKNOWN.
- `security_allows_paper_candidate` is the Lane B helper (PASS only). Frozen
  `paper_trading/**` still uses Lane A verdict names internally and is not
  edited.

---

## Bypass audit (Python Lane B)

| PATH | SOURCE | SECURITY GATE | CAN BYPASS? | RESULT |
|------|--------|---------------|-------------|--------|
| Advisor ENTER | `architecture/decision/advisor.py` GATE 1 | overlay PASS | No | AVOID otherwise |
| Opportunity alert | `architecture/alerts/engine.py` | `security_allows_alert` | No | no OPPORTUNITY |
| Pipeline «فرصت ویژه» | `architecture/pipeline/orchestrator.py` | `evaluate_security_from_candidate` | No (fixed this revision) | no send |
| Pump Telegram | `telegram_ai/pump_alert.py` | `securityStatus == PASS` | No (fixed this revision) | None |
| Paper helper | `security_allows_paper_candidate` | PASS only | No | helper false |
| Lane A paper_trading | frozen internals | Lane A evaluate | N/A (frozen; not Lane B authority) | documented limitation |
| TS `scoring.ts` / `alerts.ts` / Command Center | dual-stack presentation | not Python overlay | Classified **non-authoritative**; do not widen (Phase 3+) | not a Phase 2 merge of #64 |
| Score ledger / whales BUY labels | scoring / intel | not a recommendation | N/A | not eligibility |

High opportunity + low risk without security PASS cannot produce ENTER,
OPPORTUNITY, or the special Telegram card on Python paths.

---

## PHASE_STATUS (Phase 2)

```
PHASE_STATUS: VERIFIED
PASS_GATES:
  - overlay calls frozen evaluate(); no _lane_a_evaluate copy
  - CRITICAL projection == live Lane A CRITICAL (7 keys; HIGH excluded)
  - mapping SECURITY_VETO→REJECT, PASS_WITH_UNKNOWN→INCOMPLETE, PASS→PASS
  - extras/stale tighten only; veto cannot be downgraded
  - unknown / missing critical / missing object / missing pool age → INCOMPLETE
  - honeypot / unsellable / blacklist / mint / freeze / extreme tax / rug / trapped → REJECT
  - GoPlus missing is_honeypot stays None; RugCheck missing risks stays None
  - DEXTools proxy does not invent ownership_renounced
  - collector observation hop preserves `pair_created_ts` in memory so Lane A
    LP age is not silently dropped (missing age remains INCOMPLETE)
  - opportunity alerts and pipeline/pump Telegram require PASS
  - Lane A freeze OK (36) before and after
  - no Lane A files in diff
FAILED_GATES: none for the Python overlay scope of this revision
  (full pytest: 1 PRE-EXISTING config-doc scanner miss, not overlay)
BLOCKERS:
  - none that block overlay VERIFIED
KNOWN_LIMITATIONS:
  - TS scoring.ts / engine.ts / council.ts / alerts.ts remain dual-stack
    (non-authoritative presentation; not closed in this PR)
  - paper_trading still speaks Lane A verdict names internally (frozen)
  - security_allows_paper_candidate is the Lane B helper; not spliced into
    frozen paper_trading
  - npm typecheck/lint/build not a merge gate (no canonical web change)
EVIDENCE:
  - docs/engineering/PHASE2_SECURITY_GATE.md (this file)
  - architecture/security/gate.py POLICY_VERSION=security-overlay-v2
  - pytest tests/test_canonical_security_gate.py (adversarial + provider)
  - advisor / alerts / pipeline / isolation / provider resilience tests
  - python3 -B scripts/freeze_lane_a.py
  - PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_imports.py
TEST_RESULTS: freeze 36 OK; validate_imports PASSED (179 modules, clean tree);
  targeted 239 passed; full pytest 1593 passed, 3 skipped, 1 failed
  (PRE-EXISTING: tests/test_config_validation.py::test_documented_keys_are_actually_read_or_legacy
  — NEXT_PUBLIC_AHOS_WEB_API_TOKEN is read in web_api_client.ts; Python scanner
  misses it; not faked in this PR)
REGRESSIONS: pipeline fixtures require overlay PASS for فرصت ویژه;
  RugCheck empty risks no longer infers mint/freeze False
NEXT_UNLOCKED_PHASE: Phase 3 remains a separate PR (#64). This document does
  not unlock merge of #63 or start Phase 4.
```

VERIFIED here means the Python overlay architecture, fail-closed semantics,
lane isolation, drift tests, and verification commands support the claim.
It does **not** mean OPERATOR_READY / PRODUCTION_READY, and it is **not**
COMPLETE: dual-stack TS and frozen paper_trading internals remain, and this
PR stays draft until human review.

---

## Scope (what this phase owns)

- Lane B states: `PASS` / `REJECT` / `INCOMPLETE` / `STALE`
- Fail-closed mapping and extras
- Provider missing-field normalization on GoPlus / RugCheck / DEXTools
- Advisor GATE 1, AlertEngine, pipeline Telegram, pump_alert PASS requirement
- Drift tests vs frozen Lane A without editing Lane A

Not in this phase: merging #63/#64; Phase 3 canonical decision authority;
TypeScript dual-stack closure; regenerating Lane A hashes.
