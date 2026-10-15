<!-- Tehran: 2026-10-09 16:05 (UTC+3:30) | Version: v2 | Author: Asi (اسی) for AHOS -->
<!-- Reasons v2: all markets, capital allocation, explicit math, permissive licenses only (AGPL backtesting.py + Commons-Clause vectorbt removed).
     Laws: PAPER_ONLY until ≥30 closed paper trades prove it; no profit promises; Lane A frozen; zero cost; two-source; extend existing modules only. -->
# AHOS Trading Skills v2 (institutional grade)

**Caveats:** "Extends" names roles, so Soltan maps them to real modules. Licenses come from memory, so verify (`pip show`, repo LICENSE) before install.
Free data has ToS limits. yfinance is unofficial Yahoo scraping (Apache-2 code), so use it for research/paper only and always pair it with a second source.

## 0. Universe & free data (two-source per asset class)
| Market | Source A | Source B |
|---|---|---|
| Crypto spot/perps | `ccxt` (MIT) exchange 1 | `ccxt` exchange 2 / CoinGecko free |
| DEX tokens | DexScreener API | GeckoTerminal API (+GoPlus, honeypot.is for safety) |
| Gold / Oil | FRED (`fredapi`, Apache-2) / EIA free key | Stooq via `pandas-datareader` (BSD) / yfinance futures (GC=F, CL=F) |
| US/EU/Asia stocks | Stooq | yfinance / Alpha Vantage free tier |
| Forex | ECB reference rates | Stooq / FRED FX |
| Futures | yfinance continuous | Stooq |
| Macro | FRED, ECB SDW, BoJ | official central-bank releases |
Normalize everything to UTC and one OHLCV schema. If A and B disagree by more than a tolerance, the asset is CONFLICT and gets no signal.

## 1. Regime detection
HMM on returns + realized vol; change points via PELT. State k = argmax P(s_t=k | r_1..t) (filtered only, never smoothed, so there is no lookahead).
Libs: `hmmlearn` (BSD), `ruptures` (BSD), `arch` (NCSA). Extends market-context filter. Test: synthetic switches must be detected within N bars.

## 2. Multi-timeframe confluence
Score = Σ w_tf · sign(signal_tf), and it trades only if |Score| ≥ θ and the higher-TF sign matches. Libs: `pandas-ta` (MIT), `TA-Lib` (BSD).
Test: resample uses only closed candles.

## 3. Order flow & liquidity
Imbalance I = (B−A)/(B+A) on top-N depth, spread s = (ask−bid)/mid, and slippage est. = size / depth±1%. Gate: skip if s > s_max or size > k·depth.
Free for crypto only (`ccxt`); for stocks/FX use daily volume/ADV (size ≤ 1% ADV). Extends execution/risk gate.

## 4. Token safety (DEX), hard veto
Sell-tax sim, LP locked %, owner privileges (mint/blacklist/pause/tax-change), top-10 holders %, verified source, contract age.
Needs ≥2 of GoPlus / honeypot.is / explorer read (`web3.py`, MIT) to agree. Missing or conflicting data means a VETO. Shared with نگهبان (M80 B6).

## 5. Volatility-targeted sizing (all assets)
σ̂ = EWMA or GARCH(1,1) daily vol. Units = (Equity · r_trade) / (k · ATR · point_value).
Use point_value/contract multiplier for futures, pip value for FX, and lot rounding (floor). Portfolio target vol: w_i ∝ σ_target / σ̂_i.

## 6. Fractional Kelly (capped)
f* = (p·b − q)/b (binary), or f* = μ/σ² (continuous). Use f = min(c·f*_shrunk, f_cap), c ∈ [0.25, 0.5], f_cap ≈ 1–2% risk.
Shrink p toward 0.5 by sample size (Beta prior), and if n < 30 then f = 0.

## 7. Capital allocation across markets
Hierarchical Risk Parity / equal-risk-contribution, RC_i = w_i(Σw)_i / σ_p, all equal. Covariance via Ledoit-Wolf shrinkage.
Caps: per asset, per asset-class, and per correlated cluster. Rebalance on drift > band, not on a calendar.
Libs: `riskfolio-lib` (BSD-3), `PyPortfolioOpt` (MIT), `scikit-learn` LedoitWolf (BSD). Extends risk manager / allocator.
**Money movement (paper ledger only):** internal transfers between paper sub-accounts with a double-entry ledger (Σ debits = Σ credits test).
No real transfers or exchange withdrawals, ever, in this phase.

## 8. Walk-forward backtesting (permissive licenses only)
Anchored or rolling train/test windows. Report OOS only, with fees + slippage + funding (perps) + swap (FX).
Libs: `zipline-reloaded` (Apache-2, equities/futures), `bt` (MIT, allocation strategies), and AHOS's own NumPy/pandas vectorised engine (preferred; small, testable).
Overfit checks: Deflated Sharpe Ratio and Probability of Backtest Overfitting (CSCV), implemented in-house from López de Prado's formulas. Purged + embargoed K-fold CV.
Tests: shifted-signal lookahead test, deterministic seeds, and fee model unit tests.

## 9. Bayesian / probabilistic ensemble
Stack model outputs, then calibrate (isotonic/Platt) to get P(win). Trade only if EV = P·avgWin − (1−P)·avgLoss − costs > 0.
Libs: `scikit-learn` (BSD), `PyMC` (Apache-2, small models only on 8 GB). Metrics: Brier, log-loss, reliability curve vs. baseline.

## 10. News & sentiment
Score_t = Σ s_j · w_source · e^(−λ(t−t_j)), and an event counts only when corroborated by ≥2 sources. Libs: `vaderSentiment` (MIT), FinBERT (check model license),
Gemini key for summaries. Used as an event-risk filter (reduce or skip), not a standalone predictor. Feeds from دیده‌بان.

## 11. Cross-source price gaps (evidence only)
Gap = |P_A − P_B| / mid − fees. Flag if > x% and both feeds are fresh. Stale-feed gaps are labelled DATA_ERROR. It never auto-trades.

## 12. Risk of ruin & kill-switches
Bootstrap/Monte Carlo the paper trade P&L into P(DD > L) over horizon H. Block new risk if P > 5%.
Hard limits: daily loss, weekly loss, max open risk, max per class, and max correlation-cluster exposure. Kill-switch is fail-closed.

## 13. Performance evals
Sharpe = √N·mean/std, Sortino (downside dev), MaxDD, Calmar, expectancy E = p·W − q·L, profit factor, hit rate, turnover, cost drag.
Report all with bootstrap 95% CIs. Libs: `quantstats` (Apache-2), `empyrical-reloaded` (Apache-2). Tests: hand-computed fixtures to 1e-6.

## Promotion gate (every technique)
PAPER_ONLY. Promote only if: ≥30 closed paper trades, expectancy > 0 after costs with CI lower bound reported, MaxDD ≤ limit,
beats the baseline without the feature on the same period, and DSR > 0.95. Otherwise it is rejected or reworked. No profit claims.

## Build order
13 → 5 → 12 → 4 → 8 → 7 → 1 → 2 → 6 → 3 → 9 → 10 → 11.
