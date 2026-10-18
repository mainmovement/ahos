# CRITIQUE — scratch round-trip, replay gate inputs, HALT latch drill (2026-10-18)

## Step 3 scratch
`scripts/scratch_gold_roundtrip.py` refuses the live default ledger path. One cycle on a temp file records `oms=ACCEPTED_PAPER` and judge is not BROKEN_CHAIN. Evidence: `tests/test_scratch_roundtrip.py`.

## Step 6 replay inputs
`architecture/markets/gate_inputs.py` feeds `declared_cost_model`, `walk_forward_evidence`, and `backtest_max_drawdown_pct` into the tier gate from `reports/grok/M13_SOAK/tier_gate_replay_inputs.json`. Labels stay REPLAY_NOT_LIVE. `cost_model` and `walk_forward` are no longer unmeasurable when the file is present. Promotion stays false.

## Step 7 latch (copy only)
`tests/test_soak_halt_latch.py` runs the soak loop in a temp dir: one real `_cycle` call, then a skipped cycle while `health.latched` is true and `entries_allowed` is false. The live PID 10564 was not restarted.

## Not proven
- Live soak still runs old code until owner restart.
- Lessons are not read back before the next entry.
- Full 25-item completion checklist is not closed.
