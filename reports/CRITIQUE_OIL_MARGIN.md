# CRITIQUE — oil paper cycle and margin cap (2026-10-18)

Oil writes mission `M13-OIL-PAPER` only. A missing source does not enter. `trades` stays false even when the paper OMS accepts the notional. Gold's latest row is absent on a fresh ledger.

Margin above 2x is `LIQUIDATION` and `live` is false. There is no futures exchange and no financing model. The numbers are the inputs the caller supplies.

`pytest tests/test_oil_margin.py` is the evidence. This does not start an oil process beside the gold soak.
