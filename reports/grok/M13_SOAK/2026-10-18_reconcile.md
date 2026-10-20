# M42 nightly reconcile

**Verdict: UNKNOWN**

- ledger entries: 657
- chain head: `ceec366c5d40a9b2b314a0b039d1b1f269c25453a1dc0952eb44a59befef75fa`
- paper store anchor: ANCHORED_CLEAN (0 anchored rows)
- paper judge: CLEAN over 644 cycles, 0 finding(s)
- broker concentration: not evaluated
- USDT depeg: UNMEASURED, deviation — from $1

## The paper judge's own numbers

- cycles replayed: 644
- closed trades: 5 (3 settled, 2 invalidated)
- gross realized PnL: 0.82 (PAPER)
- equity: 10000.818481471944

## Findings

- **R-DEPEG-UNMEASURED** — only 1 independent quote(s) for the peg asset (['defillama:coins/prices']); the two-source law is not satisfied

PAPER_ONLY. This reconcile reports and records; it promotes nothing, and a HALT it records is released only by an entry naming the halt's own hash (`MissionLedger.clear_halt`) with a written reason.
