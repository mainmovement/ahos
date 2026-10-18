# M42 nightly reconcile

**Verdict: UNKNOWN**

- ledger entries: 601
- chain head: `1556fb2edb34dae9f26f6b444ce28aa249863bf90b2a7ef6ad1bf5fa63e971d0`
- paper store anchor: ANCHORED_CLEAN (0 anchored rows)
- paper judge: CLEAN over 589 cycles, 0 finding(s)
- broker concentration: not evaluated
- USDT depeg: UNMEASURED, deviation — from $1

## The paper judge's own numbers

- cycles replayed: 589
- closed trades: 4 (3 settled, 1 invalidated)
- gross realized PnL: 0.82 (PAPER)
- equity: 10000.818481471944

## Findings

- **R-DEPEG-UNMEASURED** — only 1 independent quote(s) for the peg asset (['defillama:coins/prices']); the two-source law is not satisfied

PAPER_ONLY. This reconcile reports and records; it promotes nothing, and a HALT it records is released only by an entry naming the halt's own hash (`MissionLedger.clear_halt`) with a written reason.
