# M42 nightly reconcile

**Verdict: CLEAN**

- ledger entries: 498
- chain head: `801e82f7d01a87d14e47740327263f0be62d12427abc7acb45520a7df018f529`
- paper store anchor: ANCHORED_CLEAN (0 anchored rows)
- paper judge: CLEAN over 490 cycles, 0 finding(s)
- broker concentration: not evaluated
- USDT depeg: ARMED, deviation 0.0929% from $1

## The paper judge's own numbers

- cycles replayed: 490
- closed trades: 4 (3 settled, 1 invalidated)
- gross realized PnL: 0.82 (PAPER)
- equity: 10000.818481471944

## Findings

No discrepancy. Every measured leg agrees: the chain is intact, the anchored store is unchanged, the paper book re-derives from the recorded bytes, no broker exceeds the concentration limit, and the peg is within the threshold.

PAPER_ONLY. This reconcile reports and records; it promotes nothing, and a HALT it records is released only by an entry naming the halt's own hash (`MissionLedger.clear_halt`) with a written reason.
