# AHOS Phase 2 — Security gate overlay

**Base (this reconcile):** `origin/main` after PR #64 merge (`e8a775e`).  
**Branch:** `cursor/reconcile-overlay-v2-on-phase3-9500`  
**Supersedes:** PR #63 (`cursor/phase2-security-gate-9500`) which is now CONFLICTING because #64 merged first.  
**HEAD:** see git on this branch (policy `security-overlay-v2`)  
**Classification:** `INTEGRATION_READY` (unchanged).  
**Lane A freeze:** 36 files pinned — verify with `python3 -B scripts/freeze_lane_a.py`.

Does **not** edit frozen `discovery/security_gate.py` or `paper_trading/security_multi.py`.
Lane A enums remain `SECURITY_VETO` / `PASS_WITH_UNKNOWN` / `PASS`.

---

## Reality notes (live, 2026-09-08)

- PR #62 (Phase 0–1) is **MERGED**.
- PR #64 (Phase 3 PARTIAL) is **MERGED** onto `main` **before** the overlay-v2
  closure. `main` therefore had `_lane_a_evaluate` (security-overlay-v1 copy)
  plus Phase 3 canonical decision. That copy is removed on this branch.
- PR #63 is **OPEN / CONFLICTING / SUPERSEDED** by this reconcile. Do not merge #63.
- TypeScript alerts now require **both** Python `alerts_allowed` (BUY) and
  overlay PASS. Paper OPEN requires **both** `paper_allowed` and overlay PASS.
- Uploaded `advanced-3d-audiovisual-website/` remains a parallel frontend.

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
- TypeScript automatic OPPORTUNITY (`alerts.ts` / `processOpportunityAlerts`)
  requires `canonicalSecurityState === PASS` from Python `overlay_query`.
  Local `OBSERVED` / `UNKNOWN` / empty cannot authorize Telegram.
- `POST /api/paper` → `addPaper` requires the same overlay PASS. Client-supplied
  `canonicalSecurityState` is ignored. Missing/malformed/unavailable → 403
  `SECURITY_GATE`.

---

## TypeScript side-effect closure (this revision)

The Python overlay was already fail-closed. The live TypeScript path was not:

```
engine.ts runCycle
  → scoreToken (local securityStatus: HONEYPOT | OBSERVED | UNKNOWN)
  → processOpportunityAlerts(ranked)
  → former securityOk() allowed UNKNOWN+high score, OBSERVED, empty, INCOMPLETE, STALE
  → Telegram + reports/pump_alert_state.json
```

That `securityOk` function is **removed**. `engine.ts` now:

1. `attachCanonicalSecurityStates(ranked)` — spawn Lane B
   `python -m architecture.security.overlay_query` (consumes `evaluate_security`,
   does not copy `evaluate()`).
2. `processOpportunityAlerts` — `canonicalSecurityAllowsSideEffect` is true
   **only** for overlay `PASS`.

Anything else (REJECT, INCOMPLETE, STALE, UNKNOWN, OBSERVED, missing,
malformed, spawn/API unavailable) → no OPPORTUNITY payload and no Telegram send.

`scoring.ts` may still label OBSERVED/UNKNOWN for display. That is analysis,
not authorization.

`POST /api/paper` and chat `paper_buy` call `addPaper`, which queries the same
overlay and throws `PaperSecurityDenied` unless PASS.

Adapter: `architecture/security/overlay_query.py` + `canonical_security.ts`.
The adapter maps JSON booleans onto `SecuritySignals` (strings such as `"YES"`
stay None) and returns `overlay.state`. It does not re-evaluate honeypot/tax/mint.

Typical GoPlus-only TypeScript snapshots remain INCOMPLETE (missing tax, LP lock,
blacklist, deployer). That is fail-closed consumption, not a deleted alert path.
A complete overlay signal set with pool age can still PASS and emit.

---

## Bypass audit (Python Lane B + live TypeScript side effects)

| PATH | AUTHORITY | SECURITY GATE | CAN BYPASS? | RESULT |
|------|-----------|---------------|-------------|--------|
| Advisor ENTER | Python overlay | GATE 1 PASS | No | AVOID otherwise |
| Opportunity alert | Python overlay | `security_allows_alert` | No | no OPPORTUNITY |
| Pipeline «فرصت ویژه» | Python overlay | `evaluate_security_from_candidate` | No | no send |
| Pump Telegram | Python overlay | `securityStatus == PASS` | No | None |
| Paper helper | Python overlay | `security_allows_paper_candidate` | No | helper false |
| Lane A paper_trading | frozen Lane A | `evaluate_entry` treats PASS_WITH_UNKNOWN as QUALIFIED_ENTRY | FROZEN LANE-A LIMITATION | do not edit this phase |
| TS `processOpportunityAlerts` | Python overlay via `overlay_query` | `canonicalSecurityState === PASS` | No (closed this revision) | no Telegram |
| TS `POST /api/paper` / `addPaper` | Python overlay via `overlay_query` | `paperOpenDecision` PASS | No (closed this revision) | 403 SECURITY_GATE |
| TS `scoring.ts` / `council.ts` | local analysis | none (not a side-effect authorizer) | N/A | display only |
| TS `addWatch` / findings OPEN | operator watch / findings | not paper OPEN / not OPPORTUNITY Telegram | N/A | not this bypass |
| SQLite `pair_created_ts` drop | persistence | missing age → overlay INCOMPLETE | No (fail-closed) | do not redesign this phase |
| Score ledger / whales BUY labels | scoring / intel | not a recommendation | N/A | not eligibility |

High opportunity + local OBSERVED/UNKNOWN without overlay PASS cannot produce
a TypeScript OPPORTUNITY Telegram or paper OPEN.

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
  - Python opportunity alerts and pipeline/pump Telegram require PASS
  - TypeScript processOpportunityAlerts requires overlay PASS (no securityOk)
  - POST /api/paper OPEN requires overlay PASS (client state ignored)
  - Lane A freeze OK (36) before and after
  - no Lane A files in diff
FAILED_GATES: none for the overlay + TS side-effect gates of this revision
  (full pytest: 1 PRE-EXISTING config-doc scanner miss, not overlay)
BLOCKERS:
  - none that block this security-closure revision
KNOWN_LIMITATIONS:
  - TS scoring.ts / council.ts remain dual-stack analysis (not security authority)
  - FROZEN LANE-A LIMITATION: paper_trading.entry_rules.evaluate_entry still
    treats PASS_WITH_UNKNOWN as QUALIFIED_ENTRY (do not edit Lane A)
  - SQLite production_observations still does not persist pair_created_ts;
    reload → INCOMPLETE (fail-closed; not redesigned here)
    **SUPERSEDED 2026-09-09:** this limitation was true for Phase 2. PR #77
    persists `pair_created_ts`; PR #78 maps Gecko `pool_created_at`. Full-path
    RUNTIME VERIFIED on `cf7711e` — see
    `docs/engineering/GECKO_PAIR_CREATED_TS_E2E.md` and
    `reports/gecko_pair_created_ts_e2e_RUNTIME_VERIFIED.json`. This PHASE2
    report is otherwise not rewritten.
  - GoPlus-only TS snapshots typically cannot overlay-PASS (missing tax/lock);
    alerts/paper OPEN stay denied until canonical evidence is complete
  - Phase 2 is NOT production-ready merely because this patch passes
EVIDENCE:
  - docs/engineering/PHASE2_SECURITY_GATE.md (this file)
  - architecture/security/gate.py POLICY_VERSION=security-overlay-v2
  - architecture/security/overlay_query.py (JSON adapter)
  - canonical_security.ts / alerts.ts / engine.ts addPaper / app/api/paper
  - pytest tests/test_canonical_security_gate.py + test_overlay_query.py
  - npm run test:canonical-security (Telegram mock side effects)
  - python3 -B scripts/freeze_lane_a.py
  - PYTHONDONTWRITEBYTECODE=1 .venv/bin/python scripts/validate_imports.py
TEST_RESULTS: freeze 36 OK before and after this revision; validate_imports
  PASSED (180 modules, clean tree); targeted overlay/paper/alert tests passed;
  npm run test:canonical-security 15 passed (Telegram mocked + live overlay_query);
  full pytest 1607 passed, 3 skipped, 1 failed
  (PRE-EXISTING: tests/test_config_validation.py::test_documented_keys_are_actually_read_or_legacy
  — NEXT_PUBLIC_AHOS_WEB_API_TOKEN is read in web_api_client.ts; Python scanner
  misses it; not faked in this PR)
  npm run typecheck: PRE-EXISTING failures in uploaded parallel frontends
  (advanced-3d-audiovisual-website*); patched AHOS files are not in that list
REGRESSIONS: TS UNKNOWN/OBSERVED no longer authorize Telegram; paper OPEN
  without overlay PASS returns 403 SECURITY_GATE
NEXT_UNLOCKED_PHASE: Phase 3 remains a separate PR (#64). This document does
  not unlock merge of #63 or start Phase 4.
```

VERIFIED here means the Python overlay plus the TypeScript alert/paper OPEN
boundaries consume canonical PASS and fail closed. It does **not** mean
OPERATOR_READY / PRODUCTION_READY, and it is **not** COMPLETE: frozen
paper_trading internals, pair_created_ts SQLite persistence, and remaining
TypeScript analysis dual-stack are known limitations. This PR stays draft
until human review.

---

## Scope (what this phase owns)

- Lane B states: `PASS` / `REJECT` / `INCOMPLETE` / `STALE`
- Fail-closed mapping and extras
- Provider missing-field normalization on GoPlus / RugCheck / DEXTools
- Advisor GATE 1, AlertEngine, pipeline Telegram, pump_alert PASS requirement
- TypeScript OPPORTUNITY Telegram and API paper OPEN requiring overlay PASS
- Drift tests vs frozen Lane A without editing Lane A

Not in this phase: merging #63/#64; Phase 3 canonical decision authority;
editing frozen `paper_trading`; persisting `pair_created_ts` in SQLite;
regenerating Lane A hashes; claiming production readiness.
