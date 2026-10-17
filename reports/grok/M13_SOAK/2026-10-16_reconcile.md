# M42 nightly reconcile

**Verdict: UNKNOWN**

- ledger entries: 484
- chain head: `8ba4521448f0e09b9ae4c9d2b096c9269671f15e56ea20fb18e8213763720995`
- paper store anchor: ANCHORED_CLEAN (0 anchored rows)
- paper judge: CLEAN over 477 cycles, 0 finding(s)
- broker concentration: not evaluated
- USDT depeg: UNMEASURED, deviation — from $1

## The paper judge's own numbers

- cycles replayed: 477
- closed trades: 4 (3 settled, 1 invalidated)
- gross realized PnL: 0.82 (PAPER)
- equity: 10000.818481471944

## Findings

- **R-DEPEG-UNMEASURED** — the independent quotes disagree by 99.4600% (['coingecko:simple/price', 'defillama:coins/prices']), wider than the 1.00% agreement band; the level is not measured and the peg is not certified

PAPER_ONLY. This reconcile reports and records; it promotes nothing, and a HALT it records is released only by an entry naming the halt's own hash (`MissionLedger.clear_halt`) with a written reason.
