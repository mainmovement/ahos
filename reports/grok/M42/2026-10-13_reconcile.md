# M42 nightly reconcile

**Verdict: UNKNOWN**

- ledger entries: 106
- chain head: `625baf948d964ddaafe9b5e01d01b0e29c100dcdb0ca6f222b43b91e1627be20`
- paper store anchor: ANCHORED_CLEAN (0 anchored rows)
- paper judge: CLEAN over 102 cycles, 0 finding(s)
- broker concentration: UNMEASURED (worst broker None)
- USDT depeg: ARMED, deviation 0.0799% from $1

## The paper judge's own numbers

- cycles replayed: 102
- closed trades: 1 (1 settled, 0 invalidated)
- gross realized PnL: -6.19 (PAPER)
- equity: 9993.808025058514

## Findings

- **R-COUNTERPARTY** — the counterparty statement carries no fills and no exposure; the leg is unmeasured (no broker is declared — owner gate §11.0.3, M41 owns the key self-check)

PAPER_ONLY. This reconcile reports and records; it promotes nothing, and a HALT it records is released only by an entry naming the halt's own hash (`MissionLedger.clear_halt`) with a written reason.
