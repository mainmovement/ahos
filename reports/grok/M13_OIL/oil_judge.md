# M42 paper judge — M13-OIL-PAPER

**Verdict: CLEAN**

- ledger entries: 8
- cycles replayed: 7
- chain head: `22b76bf54c6a3257aac7bb95a37434c61f697ce07b58ded44dfd613494932265`

## The judge's own numbers

- closed trades: 0 (0 settled, 0 invalidated)
- wins / losses: 0 / 0
- gross realized PnL: 0.00 (PAPER)
- equity: 10000.0
- cycles with no corroborated price: 0
- witness states: {'UNKNOWN': 7}

## Findings

No discrepancy. Every closed trade re-derives from the position and the corroborated price that the ledger records, and the equity curve moves only through recorded realized PnL.

PAPER_ONLY. This judge reports; it does not promote, and it closes nothing.
