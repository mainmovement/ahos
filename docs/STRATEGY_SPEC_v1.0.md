# AHOS BASELINE STRATEGY SPEC v1.0 (FROZEN — NO OPTIMIZATION)
# Reconstructed from Phase 1B/2 documents. Parameters fixed BEFORE seeing results.
# Any change requires: Backtest → OOS → Walk-Forward → Monte Carlo → Agent-10 + Human Gate.

## Signal rules (deterministic, no ML, no look-ahead)
- Indicators (computed on closed candles only):
  - EMA20 of close
  - ATR14 (Wilder)
  - SMA20 of volume
- LONG entry when ALL true at candle close t (execute at open of t+1):
  1. close[t] > EMA20[t]
  2. volume[t] > 1.2 × SMA20(volume)[t]
  3. ATR14[t] > 0 and no open position
- SHORT entry mirrors rule 1 (close < EMA20) with same volume filter. (Futures both-sided.)
- Funding filter: if funding data absent (current CSVs), rule is INERT (documented, not hidden).

## Exit rules (intrabar, conservative order)
- SL = entry ± 1.5 × ATR14[signal]  (fixed at entry; never widened)
- TP = entry ∓ 2.0 × ATR14[signal]
- If both SL and TP touched in the same candle → assume SL first (conservative).
- Time stop: close after 72h at market if neither hit.
- Signal-flip stop: opposite entry signal closes current position.

## Cost model (from $10_15_FEASIBILITY.md + EXCHANGE_FACTS.md)
- Taker fee: 0.055% per side (LBank/Bybit documented approx)
- Slippage: 0.02% per side (BTC/ETH high-liquidity assumption)
- Funding: not applied (absent in dataset — documented limitation)

## Risk layer (Agent-08 caps — hard, non-bypassable)
- Leverage: 2x fixed (5x cap absolute; 10x never in micro-capital mode)
- Risk per trade ≤ 2% of equity → notional = (2% equity × SL-distance%⁻¹), capped by leverage
- Max 3 concurrent positions; BTC/ETH/SOL only in micro mode
- Daily loss cap: 10% of equity → halt 24h; Max drawdown cap: 20% → full stop + kill switch
- Min-notional guard: order blocked if below verified exchange minimum (all UNKNOWN until verified)

## Data rule
- Real LBank/Bybit CCXT data only. No synthetic, no interpolation.
- Removed rows (bad OHLCV) are registered, never replaced.
