# AHOS Phase 2 — Security gate overlay

**Base:** `origin/main` after PR #62 merge (`9104fdb`) plus later Windows/upload commits.  
**Branch:** `cursor/phase2-security-gate-9500`  
**Date:** 2026-09-08  
**Classification:** `INTEGRATION_READY` (unchanged).  
**Lane A freeze:** 36 files pinned — verified before and after this phase.

Does **not** edit frozen `discovery/security_gate.py` or `paper_trading/security_multi.py`.
Lane A enums remain `SECURITY_VETO` / `PASS_WITH_UNKNOWN` / `PASS`.

---

## Reality notes (this session)

- PR #62 (Phase 0–1) is **MERGED**. Identity overlay is on `main`.
- `G:\robat\ahos\cursor\slills` is **not in this repository**. Inspected: no
  `cursor/slills` path. Canonical skills are `.cursor/skills/` (eleven files).
  The `slills` spelling is a local Windows path typo, not a committed directory.
- `main` also contains uploaded trees `advanced-3d-audiovisual-website/` and
  `advanced-3d-audiovisual-website (1)/` including `src/lib/reasoningEngine.ts`.
  That is a **parallel frontend**, not the Python brain. This phase does not
  wire it as authority and does not delete it.

---

## Scope

- Lane B states: `PASS` / `REJECT` / `INCOMPLETE` / `STALE`
- Mapping: `SECURITY_VETO` → REJECT; `PASS_WITH_UNKNOWN` → **INCOMPLETE** (never PASS)
- Confirmed criticals: honeypot, unsellability, blacklist, mint, freeze,
  extreme sell tax (≥20%), deployer rug, trapped liquidity
- Missing critical evidence → INCOMPLETE
- Stale evidence (default 24h) cannot PASS; confirmed REJECT stays REJECT
- GoPlus missing flags stay `None` (not False); taxes stored as percent
- `DecisionAdvisor` GATE 1 fail-closed: only overlay PASS may ENTER
- Opportunity alerts require overlay PASS
- DEXTools `isBlacklisted` maps to `is_blacklisted`, not freeze

Not in this phase: TypeScript/Telegram bypass closure (Phase 3/9);
orchestrator still does not call DecisionAdvisor; paper_trading Lane A
internal `PASS_WITH_UNKNOWN` vocabulary unchanged.

---

## PHASE_STATUS (Phase 2)

```
PHASE_STATUS: COMPLETE
PASS_GATES:
  - PASS/REJECT/INCOMPLETE/STALE overlay
  - honeypot / unsellable / blacklist / mint / freeze / extreme tax / rug / trapped
  - unknown critical ⇒ INCOMPLETE
  - confirmed critical ⇒ REJECT
  - GoPlus missing is_honeypot is None
  - advisor GATE 1 fail-closed
  - opportunity alerts suppressed without PASS
  - Lane A freeze OK (36)
  - validate_imports PASSED (179 modules)
  - targeted pytest passed (including phase-4 lane isolation)
  - no Lane A files in diff
FAILED_GATES: none for Phase 2 overlay scope
BLOCKERS:
  - TS scoring.ts / uploaded reasoningEngine.ts remain dual-stack (Phase 3/8)
  - paper_trading still speaks Lane A verdict names internally (frozen)
EVIDENCE:
  - docs/engineering/PHASE2_SECURITY_GATE.md
  - pytest tests/test_canonical_security_gate.py + advisor/identity/panel/alerts/pipeline
  - python3 -B scripts/freeze_lane_a.py
  - python3 -B scripts/validate_imports.py
TEST_RESULTS: targeted suites green; see commit message
REGRESSIONS: opportunity-alert fixtures now require full critical coverage
KNOWN_LIMITATIONS:
  - Overlay mirrors Lane A evaluate() without importing discovery (lane isolation)
  - Equivalence is tested against discovery.security_gate.evaluate in pytest
  - UI/Telegram not yet bound to overlay (Phase 3/9)
NEXT_UNLOCKED_PHASE: Phase 3 Canonical Decision Authority
```
