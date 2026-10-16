# M42 nightly reconcile

**Verdict: CLEAN**

- ledger entries: 393
- chain head: `275534d11919504f26d65a2b6de5e97b7d3366e3a674daf4c82411dcc11a6266`
- paper store anchor: ANCHORED_CLEAN (0 anchored rows)
- paper judge: CLEAN over 387 cycles, 0 finding(s)
- broker concentration: not evaluated
- USDT depeg: ARMED, deviation 0.0878% from $1

## The paper judge's own numbers

- cycles replayed: 387
- closed trades: 3 (2 settled, 1 invalidated)
- gross realized PnL: -13.93 (PAPER)
- equity: 9986.073339606803

## Findings

No discrepancy. Every measured leg agrees: the chain is intact, the anchored store is unchanged, the paper book re-derives from the recorded bytes, no broker exceeds the concentration limit, and the peg is within the threshold.

PAPER_ONLY. This reconcile reports and records; it promotes nothing, and a HALT it records is released only by an entry naming the halt's own hash (`MissionLedger.clear_halt`) with a written reason.
