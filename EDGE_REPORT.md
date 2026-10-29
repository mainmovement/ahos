# EDGE_REPORT — live paper book (PAPER_ONLY)

Generated: `2026-10-29T19:56:42Z` · Closed trades: **122** · Status: **`UNPROVEN_EDGE`**

## Promotion gate (TS-PG / Master Map)

| Check | Value | Pass threshold |
|-------|-------|----------------|
| Closed trades | 122 | ≥ 30 |
| Expectancy CI95 lower (USD) | -0.0172 | > 0 |
| Deflated Sharpe (DSR) | 0.0 | > 0.95 |
| Live-book PBO | None | < 0.50 (N/A single book) |
| Research PBO (batch8 admitted only) | 0.4889 | advisory, not live book |
| **Eligible** | **False** | all of the above |

## Performance (closed trades, net of fees in `realized_pnl_usd`)

- Hit rate: **0.328**
- Expectancy USD: **-0.01** (CI95 [-0.0172, -0.0033])
- Profit factor: **0.529**
- Sharpe per trade (descriptive, not DSR): **-0.2265**
- Max drawdown on sequence: **1.88%**

## Fee drag

- Close fees USD: **0.861363**
- Open fees USD (all opens): **0.457176**
- Net realized USD: **-1.2244**
- Implied gross (net + close fees): **-0.363037**

## Per-desk PnL (after fees in log)

| Desk | Closes | Realized USD | Action |
|------|--------|--------------|--------|
| ASIA_EQUITIES | 21 | -0.0334 | SHRINK / shadow-only |
| CRYPTO | 37 | -0.6759 | SHRINK / shadow-only |
| EU_EQUITIES | 3 | 0.1351 | keep (monitor) |
| FOREX | 15 | -0.0361 | SHRINK / shadow-only |
| GOLD | 11 | -0.3506 | SHRINK / shadow-only |
| OIL | 19 | -0.2584 | SHRINK / shadow-only |
| PB_TOKEN | 13 | -0.0999 | SHRINK / shadow-only |
| US_EQUITIES | 3 | 0.0948 | keep (monitor) |

## Dominant-signal attribution (largest |weight×score| at entry)

| Signal | Closes | Win rate | Realized USD |
|--------|--------|----------|--------------|
| candles | 5 | 0.4 | -0.0359 |
| large_trades | 1 | 0.0 | -0.0147 |
| mtf_trend | 113 | 0.327 | -1.1503 |
| news | 1 | 0.0 | -0.0063 |
| order_flow | 1 | 0.0 | -0.0229 |
| zscore_mr | 1 | 1.0 | 0.0057 |

## Honesty

- DSR uses cumulative **`n_trials_counted_in_dsr`** from strategy-lab batches and OOS Sharpes stored in M28 research JSON — not a fresh search on these 122 closes.
- Do **not** treat positive closed-trade count or descriptive Sharpe as edge.
- Desks marked **SHRINK** lost after fees with ≥3 closes; disable or cap size in paper only after owner review (no live path).
