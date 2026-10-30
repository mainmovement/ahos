# EDGE_REPORT — live paper book (PAPER_ONLY)

Generated: `2026-10-30T00:33:58Z` · Closed trades: **130** · Status: **`UNPROVEN_EDGE`**

## Promotion gate (TS-PG / Master Map)

| Check | Value | Pass threshold |
|-------|-------|----------------|
| Closed trades | 130 | ≥ 30 |
| Expectancy CI95 lower (USD) | -0.0169 | > 0 |
| Deflated Sharpe (DSR) | 0.0 | > 0.95 |
| Live-book PBO | None | < 0.50 (N/A single book) |
| Research PBO (batch8 admitted only) | 0.4889 | advisory, not live book |
| **Eligible** | **False** | all of the above |

## Performance (closed trades, net of fees in `realized_pnl_usd`)

- Hit rate: **0.346**
- Expectancy USD: **-0.0085** (CI95 [-0.0169, -0.001])
- Profit factor: **0.585**
- Sharpe per trade (descriptive, not DSR): **-0.1898**
- Max drawdown on sequence: **1.88%**

## Fee drag

- Close fees USD: **0.906888**
- Open fees USD (all opens): **0.467963**
- Net realized USD: **-1.1026**
- Implied gross (net + close fees): **-0.195712**

## Per-desk PnL (after fees in log)

| Desk | Closes | Realized USD | Action |
|------|--------|--------------|--------|
| ASIA_EQUITIES | 22 | -0.0466 | SHRINK / shadow-only |
| CRYPTO | 40 | -0.5409 | SHRINK / shadow-only |
| EU_EQUITIES | 3 | 0.1351 | keep (monitor) |
| FOREX | 16 | -0.0344 | SHRINK / shadow-only |
| GOLD | 12 | -0.3717 | SHRINK / shadow-only |
| OIL | 21 | -0.239 | SHRINK / shadow-only |
| PB_TOKEN | 13 | -0.0999 | SHRINK / shadow-only |
| US_EQUITIES | 3 | 0.0948 | keep (monitor) |

## Dominant-signal attribution (largest |weight×score| at entry)

| Signal | Closes | Win rate | Realized USD |
|--------|--------|----------|--------------|
| candles | 5 | 0.4 | -0.0359 |
| large_trades | 1 | 0.0 | -0.0147 |
| mtf_trend | 121 | 0.347 | -1.0285 |
| news | 1 | 0.0 | -0.0063 |
| order_flow | 1 | 0.0 | -0.0229 |
| zscore_mr | 1 | 1.0 | 0.0057 |

## Signal × desk × regime (dominant signal at entry)

| Signal | Desk | Regime | Closes | Win rate | Realized USD |
|--------|------|--------|--------|----------|--------------|
| candles | CRYPTO | HIGH | 2 | 0.0 | -0.0445 |
| candles | OIL | LOW | 2 | 1.0 | 0.0412 |
| candles | PB_TOKEN | NORMAL | 1 | 0.0 | -0.0326 |
| large_trades | CRYPTO | UNKNOWN | 1 | 0.0 | -0.0147 |
| mtf_trend | ASIA_EQUITIES | HIGH | 10 | 0.2 | -0.0693 |
| mtf_trend | ASIA_EQUITIES | NORMAL | 12 | 0.417 | 0.0227 |
| mtf_trend | CRYPTO | HIGH | 14 | 0.357 | -0.236 |
| mtf_trend | CRYPTO | LOW | 4 | 0.25 | -0.0433 |
| mtf_trend | CRYPTO | NORMAL | 17 | 0.353 | -0.1732 |
| mtf_trend | EU_EQUITIES | HIGH | 1 | 1.0 | 0.02 |
| mtf_trend | EU_EQUITIES | NORMAL | 2 | 1.0 | 0.1151 |
| mtf_trend | FOREX | HIGH | 3 | 0.333 | -0.0057 |
| mtf_trend | FOREX | LOW | 1 | 0.0 | -0.0054 |
| mtf_trend | FOREX | NORMAL | 12 | 0.25 | -0.0233 |
| mtf_trend | GOLD | HIGH | 5 | 0.4 | -0.1061 |
| mtf_trend | GOLD | LOW | 1 | 1.0 | 0.0359 |
| mtf_trend | GOLD | NORMAL | 6 | 0.0 | -0.3015 |
| mtf_trend | OIL | HIGH | 8 | 0.25 | -0.2963 |
| mtf_trend | OIL | LOW | 1 | 1.0 | 0.0185 |
| mtf_trend | OIL | NORMAL | 9 | 0.444 | -0.0081 |
| mtf_trend | PB_TOKEN | HIGH | 3 | 0.0 | -0.104 |
| mtf_trend | PB_TOKEN | LOW | 1 | 0.0 | -0.0474 |
| mtf_trend | PB_TOKEN | NORMAL | 8 | 0.5 | 0.0841 |
| mtf_trend | US_EQUITIES | HIGH | 2 | 1.0 | 0.0985 |
| mtf_trend | US_EQUITIES | NORMAL | 1 | 0.0 | -0.0037 |
| news | CRYPTO | UNKNOWN | 1 | 0.0 | -0.0063 |
| order_flow | CRYPTO | UNKNOWN | 1 | 0.0 | -0.0229 |
| zscore_mr | OIL | HIGH | 1 | 1.0 | 0.0057 |

## Honesty

- DSR uses cumulative **`n_trials_counted_in_dsr`** from strategy-lab batches and OOS Sharpes stored in M28 research JSON — not a fresh search on these 130 closes.
- Do **not** treat positive closed-trade count or descriptive Sharpe as edge.
- Desks marked **SHRINK** are a paper-only size cap (`effective_desk_notional_mult` merges static haircut with EDGE policy). Shadow-block of opens stays opt-in and off.
- `signal_desk_regime_attribution` partitions each close by its dominant entry signal, desk, and regime. It is a census, not a new fitted weight.
- New opens require two pre-registered independent families (news, macro, whales, candle wicks, research) to agree, plus expected profit ≥ 2× round-trip fees. `mtf_trend` alone does not pass.
