# M42 paper judge — M13-GOLD-PAPER

**Verdict: CLEAN**

- ledger entries: 4
- cycles replayed: 3
- chain head: `2763eced0fff07ed95e443d8064e89c2229e2cb97da3213fae9629cf7372a351`

## The judge's own numbers

- closed trades: 0 (0 settled, 0 invalidated)
- wins / losses: 0 / 0
- gross realized PnL: 0.00 (PAPER)
- equity: 10000.0
- cycles with no corroborated price: 0
- witness states: {'VERIFIED': 3}

## Findings

No discrepancy. Every closed trade re-derives from the position and the corroborated price that the ledger records, and the equity curve moves only through recorded realized PnL.

PAPER_ONLY. This judge reports; it does not promote, and it closes nothing.
