# AHOS Quantitative Backtesting & Microstructure Engine Upgrade Plan

This document defines the mathematical, architectural, and algorithmic blueprint for upgrading the AHOS backtesting engine from a basic sequential simulator into an institutional-grade, dual-mode quantitative research suite.

---

## 1. Architectural Blueprint: Dual-Mode Backtest Architecture

```
+---------------------------------------------------------------------------------------------------+
|                                  AHOS QUANT RESEARCH LAB                                          |
+---------------------------------------------------------------------------------------------------+
                                                  |
                 +--------------------------------+--------------------------------+
                 |                                                                 |
                 v                                                                 v
+----------------------------------+                             +----------------------------------+
|      MODE 1: VECTORIZED          |                             |       MODE 2: EVENT-DRIVEN       |
|    (VectorBT Pattern)            |                             |   (NautilusTrader / HftBacktest) |
| - Matrix signal tensor broadcast |                             | - Causal discrete-event queue    |
| - 10,000 parameter sweeps / sec  |                             | - Constant product AMM slippage  |
| - Hyper-surface heatmaps         |                             | - Limit order book queue delay   |
| - Rapid hypothesis screening     |                             | - Exact liquidity consumption    |
+----------------------------------+                             +----------------------------------+
                 |                                                                 |
                 +--------------------------------+--------------------------------+
                                                  |
                                                  v
                                  +---------------------------------+
                                  |    VALIDATION & BIAS DEFENSES   |
                                  |     (De Prado Methodology)      |
                                  | - Purged K-Fold Cross Validation|
                                  | - Embargo Windowing             |
                                  | - Rolling Walk-Forward (WFA)    |
                                  | - Monte Carlo Permutation Tests |
                                  +---------------------------------+
                                                  |
                                                  v
                                  +---------------------------------+
                                  |    QUANTITATIVE TEAR-SHEET      |
                                  |      (QuantStats Pattern)       |
                                  | - Sharpe, Sortino, Calmar, VaR  |
                                  | - Conditional VaR (CVaR)        |
                                  | - Underwater drawdown curves    |
                                  +---------------------------------+
```

---

## 2. Mathematical Formulations & Risk Equations

### 2.1 Non-Linear DEX Slippage & Market Impact (Constant Product AMM)
In decentralized automated market makers (Uniswap V2/V3, Raydium), price impact is governed by the constant-product invariant:
$$x \cdot y = k$$
When buying $\Delta x$ tokens with $\Delta y$ quote currency (e.g. SOL or USDC), the effective execution price $P_{exec}$ deviates non-linearly from the spot price $P_0 = \frac{y}{x}$:
$$P_{exec} = \frac{\Delta y}{\Delta x} = \frac{y + \Delta y \cdot (1 - \phi)}{x - \frac{k}{y + \Delta y \cdot (1 - \phi)}}$$
Where $\phi$ represents the pool swap fee (e.g. $0.3\%$ or $0.25\%$).

The fractional price slippage $S$ is modeled as:
$$S(\Delta y, y) = \frac{\Delta y}{y \cdot (1 - \phi) + \Delta y} + \text{gas\_cost} + \text{queue\_delay\_jitter}$$
This prevents backtests from simulating unrealistic multi-thousand dollar fills in pools with only \$10,000 in liquidity.

---

### 2.2 Purged & Embargoed Cross-Validation (CPCV)
Standard K-Fold Cross-Validation leaks information because financial returns exhibit serial correlation and overlapping holding periods. AHOS implements Marcos Lopez de Prado's Purging and Embargoing:

```
Training Fold 1       |  Purge  |   Validation Fold (Test)   |  Embargo  |      Training Fold 2
======================| [/////] | [========================] | [///////] | ======================
                      | t_start |                            | t_end     |
```

1. **Purging**: Removes training samples whose evaluation windows overlap with the start of the test set.
2. **Embargoing**: Removes training samples immediately following the test set by an embargo window $h$ (typically $1\%$ of the dataset length or the maximum trade holding time) to eliminate autoregressive memory.

---

### 2.3 Comprehensive Risk & Performance Metrics (QuantStats Engine)

| Metric Name | Mathematical Formula | Purpose & Threshold in AHOS |
|---|---|---|
| **Annualized Sharpe Ratio** | $S = \frac{\mu_r - r_f}{\sigma_r} \cdot \sqrt{252}$ | Risk-adjusted return baseline. Gate: $S > 1.2$. |
| **Sortino Ratio** | $Sortino = \frac{\mu_r - r_f}{\sigma_{downside}} \cdot \sqrt{252}$ | Penalizes only negative volatility. Gate: $Sortino > 1.8$. |
| **Calmar Ratio** | $Calmar = \frac{CAGR}{\|MaxDD\|}$ | Return relative to worst drawdown. Gate: $Calmar > 2.0$. |
| **Value at Risk ($VaR_{95}$)** | $VaR_\alpha = - \text{Percentile}(r, 1 - \alpha)$ | Maximum expected loss at $95\%$ confidence level. |
| **Conditional VaR ($CVaR_{95}$)** | $CVaR_\alpha = - \mathbb{E}[r \mid r \le -VaR_\alpha]$ | Expected loss in the worst $5\%$ tail events (Fat Tail Risk). |
| **Omega Ratio** | $\Omega(\tau) = \frac{\int_\tau^\infty (1 - F(r)) dr}{\int_{-\infty}^\tau F(r) dr}$ | Probability weighted ratio of gains vs losses above threshold $\tau$. |
| **Tail Ratio** | $TR = \frac{\|95^{th} \text{ percentile}\|}{\|5^{th} \text{ percentile}\|}$ | Quantifies positive skewness vs downside tail magnitude. |

---

### 2.4 Monte Carlo Permutation & Stationary Bootstrap
To verify that backtest profitability is not the result of random luck or p-hacking:
1. **Trade Permutation Test**: Shuffles the sequence of trade returns 1,000 times without replacement to compute the empirical distribution of Maximum Drawdown.
2. **Stationary Bootstrap (Politis & Romano)**: Resamples blocks of returns with random geometric block lengths to preserve autocorrelation while testing strategy robustness under alternative market histories.
3. **P-Value Acceptance Gate**: Strategy is rejected if $P(\text{Random Sharpe} \ge \text{Observed Sharpe}) > 0.01$.

---

## 3. Data Leakage Defenses Matrix

| Bias Type | Vector of Contamination | AHOS Defense Mechanism |
|---|---|---|
| **Look-Ahead Bias** | Using $t+1$ close price to calculate $t$ indicators | Strict event queue timestamps ($t_{signal} < t_{order} < t_{fill}$) |
| **Survivorship Bias** | Testing only on tokens currently alive | Historical point-in-time universe snapshots including rugged/dead tokens |
| **Data Leakage in Normalization** | Computing Z-score or min-max using global mean/variance | Expanding rolling window normalization; fit only on in-sample fold |
| **Overfitting on Slippage** | Assuming 0% slippage or fixed small spread | Non-linear constant product pool impact + depth constraints |
| **Execution Latency Bias** | Assuming instantaneous fill at trigger tick | Simulated 1-block (Solana: 400ms, EVM: 12s) confirmation latency delay |
