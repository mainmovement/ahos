# EDGE_REPORT — live paper book (PAPER_ONLY)

Generated: `2026-10-29T20:32:20Z` · Closed trades: **123** · Status: **`UNPROVEN_EDGE`**

## Promotion gate (TS-PG / Master Map)

| Check | Value | Pass threshold |
|-------|-------|----------------|
| Closed trades | 123 | ≥ 30 |
| Expectancy CI95 lower (USD) | -0.0166 | > 0 |
| Deflated Sharpe (DSR) | 0.0 | > 0.95 |
| Live-book PBO | None | < 0.50 (N/A single book) |
| Research PBO (batch8 admitted only) | 0.4889 | advisory, not live book |
| **Eligible** | **False** | all of the above |

## Performance (closed trades, net of fees in `realized_pnl_usd`)

- Hit rate: **0.333**
- Expectancy USD: **-0.0096** (CI95 [-0.0166, -0.0027])
- Profit factor: **0.544**
- Sharpe per trade (descriptive, not DSR): **-0.2174**
- Max drawdown on sequence: **1.88%**

## Fee drag

- Close fees USD: **0.868794**
- Open fees USD (all opens): **0.457176**
- Net realized USD: **-1.1857**
- Implied gross (net + close fees): **-0.316906**

## Per-desk PnL (after fees in log)

| Desk | Closes | Realized USD | Action |
|------|--------|--------------|--------|
| ASIA_EQUITIES | 21 | -0.0334 | SHRINK / shadow-only |
| CRYPTO | 37 | -0.6759 | SHRINK / shadow-only |
| EU_EQUITIES | 3 | 0.1351 | keep (monitor) |
| FOREX | 15 | -0.0361 | SHRINK / shadow-only |
| GOLD | 11 | -0.3506 | SHRINK / shadow-only |
| OIL | 20 | -0.2197 | SHRINK / shadow-only |
| PB_TOKEN | 13 | -0.0999 | SHRINK / shadow-only |
| US_EQUITIES | 3 | 0.0948 | keep (monitor) |

## Dominant-signal attribution (largest |weight×score| at entry)

| Signal | Closes | Win rate | Realized USD |
|--------|--------|----------|--------------|
| candles | 5 | 0.4 | -0.0359 |
| large_trades | 1 | 0.0 | -0.0147 |
| mtf_trend | 114 | 0.333 | -1.1116 |
| news | 1 | 0.0 | -0.0063 |
| order_flow | 1 | 0.0 | -0.0229 |
| zscore_mr | 1 | 1.0 | 0.0057 |

## Honesty

- DSR uses cumulative **`n_trials_counted_in_dsr`** from strategy-lab batches and OOS Sharpes stored in M28 research JSON — not a fresh search on these 123 closes.
- Do **not** treat positive closed-trade count or descriptive Sharpe as edge.
- Desks marked **SHRINK** lost after fees with ≥3 closes; disable or cap size in paper only after owner review (no live path).
