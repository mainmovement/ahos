# Critique — Step 8 oil judge + tier (scratch)

Date: 2026-10-18 (Tehran). PAPER_ONLY; oil process **not** attached to gold soak PID.

## Change
- Oil checkpoints declare `cycle`, bankroll/equity identity fields for M42.
- `scripts/oil_stack_drill.py`: 7-cycle cadence → judge → tier gate (`market=oil`).

## Proof
```
pytest tests/test_oil_judge.py tests/test_oil_margin.py -q  → passed
python scripts/oil_stack_drill.py --cycles 7  → judge CLEAN, tier T0, replay_verdict NO_PROVEN_EDGE
Safety subset (tier, gold_judge, soak, zero_money): 87 passed
```

## Gaps
- No closed oil trades; tier mostly UNMEASURABLE (honest).
- Live 7-day OS scheduler not created (owner/logon).
- Gold soak restart still owner action for new gold wiring.

## Verdict
Step 8 **PARTIAL**: judge-clean oil track on dedicated ledger proven; profitability still unproven.
