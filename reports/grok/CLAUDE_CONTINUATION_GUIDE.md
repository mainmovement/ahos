Governance: Lane A untouched (nothing under `discovery/` or `paper_trading/`
modified; the store is opened read-only; `freeze_lane_a.verify()` clean); no
gate, hygiene rule, policy, registry, authority surface or risk cap touched; no
push; secrets never written.

## Phase 13: M43 Decision records + per-market tier state

**Status:** TESTED — Unit tests passing (28/28) for decision record logic, tier promotion, expiry handling, and signer validation. The system implements:

- Decision records with format `DECISION_ID, MARKET, FROM/TO_TIER, EVIDENCE_REFS, VERIFICATION_ID, CHALLENGE_ID, SIGNERS, CAPS, EXPIRY, ROLLBACK_PLAN, TRIGGER` stored in `docs/governance/decisions/` on the single ledger (`architecture/mission/ledger.py`).
- Per-market `AUTONOMY_TIER_CURRENT` tracking (T0 today) with tier progression rules.
- Promotion requires multi-signer validation per tier (T0→T1: 1 owner + 3 gate agents; higher tiers add more signers).
- Tier skip rejection: only sequential promotions allowed (FROM_TIER + 1 == TO_TIER).
- Expiry → auto-downgrade with configurable durations per tier.
- Fail-closed design: `trading.live` remains denied in `ahos_org/policy.py` (global deny list); no live trading enabled.
- Human-only component registration: documented in `docs/governance/decisions/README.md` (no automation).

**Files created/changed:**
- `architecture/mission/ledger.py` (add `KIND_DECISION` evidence kind)
- `architecture/markets/tier_state.py` (DecisionRecord, DecisionStore, TierState)
- `scripts/m43_tier_state.py` (CLI tool for tier management)
- `tests/test_m43_tier_state.py` (28 test cases, all passing)
- `docs/governance/decisions/README.md` (format documentation)
- `docs/governance/decisions/AUTONOMY_TIER_CURRENT.md` (current tier state file)

**Agent reviews and sign-offs:** See `reports/grok/autopilot/M43_review.md` for Architektur (Arash), domain specialist (Prompt/Spec Clarity), governance (Giti), QA (Ghasem), red team (Reza), and evidence (Erfan) reviews.

**Next in order:** M41 (broker key-permission self-check) per owner plan "M42, M43 → M41 → M39 → M38 → M40".

---