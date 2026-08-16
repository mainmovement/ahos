# AHOS CANONICAL — DISCOVERY (E-01)
Current truth of the Early Token Discovery engine. Detail: docs/mission_v1_1/{B,F,J}; code: discovery/.

## What exists (C Tested, RUNNING)
- Collectors: GeckoTerminal new_pools (primary, 4 chains) + DexScreener profiles→tokens/v1 enrich.
- SNAP schedule: S0,+15m,+1h,+4h,+12h,+24h,+48h,+72h,(+7d) with tolerances; missed slots → gap_register.
- Lifecycle: DISCOVERED→OBSERVING→DEAD(>24h silence)→RESOLVED(T+72h), full event trail.
- Real run: T0=2026-08-11 17:20Z (sandbox). 3 passes day-1 → 88 tokens / 115 obs. Reports: research/experiments/e01_collection_*.

## E-01 = research infrastructure, not a signal
Goal: timestamped, replayable universe of early tokens (INITIAL STATE + TIME SERIES + SECURITY + OUTCOME)
to answer: "which first-24–72h observable features associate with predefined movement events?" (≥8 weeks needed).
Forbidden: PUMP SCORE, numeric probabilities, "will pump" language, promotion before research gate.

## Event grid (pre-registered study grid — NOT signals)
Classes +25/+50/+100/+200% × horizons 15m/1h/4h/12h/24h/72h/7d (liquidity-adjusted variants planned — F-spec).
Baseline-vs-conditioned (lift/precision/Wilson CI/multiplicity) = research/baseline_stats.py + docs mission_v1_1/G-design (wave-6 doc G).

## Exit criteria
Phase-2 exit = 72h continuous pipeline log (sandbox best-effort; guaranteed continuity needs VPS).
Research exit = event-study with ≥pre-registered sample, OOS replication, regime split, search-space registry.
