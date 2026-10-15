<!-- Tehran: 2026-10-09 15:50 (UTC+3:30) | Version: v1 | Author: Asi (اسی) for AHOS -->
<!-- Reasons: free, open-source, 8 GB-friendly techniques that add measurable, testable edge to AHOS's decision brain.
     Laws: PAPER_ONLY until 30 closed paper trades prove it; no profit promises; Lane A frozen; zero cost; two-source rule; extend, never parallel. -->
# AHOS Trading Skills v1

**Note:** module names in "Extends" are roles. Soltan should map each to the real AHOS agent/file. Licenses are from memory, and maintenance
status was not re-checked live (moderate budget), so verify `pip show`/GitHub activity before adopting. ⚠ marks a license caveat.

**Shared validation rule (applies to every item):** PAPER_ONLY. Promote only after ≥30 closed paper trades with positive expectancy
after fees and slippage, max DD within the risk limit, and a result no worse than the baseline without the feature (A/B on the same period).

## 1. Market-regime detection
- **What:** HMM / change-point labelling of trend, range and high-vol states. **Edge:** switch or disable strategies per regime; this cuts the losses that come from trading in the wrong regime.
- **Libs:** `hmmlearn` (BSD), `ruptures` (BSD), `arch` GARCH vol (NCSA).
- **Extends:** brain's market-context / signal filter. **Data:** OHLCV from 2 exchanges via `ccxt` (MIT), which must agree within tolerance.
- **Tests:** synthetic series with known regime switches, where the detector must flag them within N bars, plus a no-lookahead test (fit only on past data).

## 2. Multi-timeframe signals
- **What:** a signal counts only if higher TF (4h/1d) bias agrees with lower TF (15m/1h) entry. **Edge:** fewer false entries.
- **Libs:** `pandas-ta` (MIT), `TA-Lib` (BSD; on Windows use the prebuilt wheel).
- **Extends:** existing signal agent (add TF-confluence score). **Data:** same 2-source OHLCV, resampled.
- **Tests:** resampling alignment (no future candle leaks), plus a confluence score unit test.

## 3. Order-flow & liquidity
- **What:** order-book imbalance, spread, depth at ±1%, and volume delta. **Edge:** avoids illiquid fills, and imbalance is a short-horizon tilt.
- **Libs:** `ccxt` order book + trades (MIT, free public endpoints).
- **Extends:** execution/risk gate (skip if depth < size×k or spread > x). **Data:** order books from 2 venues.
- **Tests:** a recorded-snapshot replay, and a gate that blocks a thin-book fixture.

## 4. On-chain / DEX token safety
- **What:** rug/honeypot sim, LP lock %, owner privileges (mint, blacklist, tax), and top-10 holder concentration. **Edge:** avoids total-loss tokens, which is the biggest DEX risk.
- **Sources (free tiers):** GoPlus Security API, honeypot.is, DexScreener API, and a block-explorer free key (Etherscan/BscScan). `web3.py` (MIT) for direct reads.
- **Extends:** token-screening gate (hard veto). **Data:** ≥2 of the above must agree, and if they disagree the token is UNSAFE.
- **Tests:** fixtures of known-scam and known-safe contracts, and a missing-data case that defaults to veto.

## 5. Volatility-adjusted position sizing
- **What:** size = risk_budget / (ATR×k) or target-vol scaling. **Edge:** keeps risk per trade constant across regimes.
- **Libs:** `pandas-ta` ATR, `arch`. **Extends:** risk manager. **Tests:** size shrinks as vol doubles, and never exceeds the max-position cap.

## 6. Fractional Kelly with caps
- **What:** f* = edge/odds from paper stats, used at ¼–½ Kelly with a hard cap (e.g. ≤1–2% risk). **Edge:** grows risk only when edge is proven.
- **Libs:** plain NumPy. **Extends:** risk manager (multiplier on #5). **Data:** own closed paper trades only (need ≥30).
- **Tests:** negative or unknown edge gives 0 size, the cap is never exceeded, and small samples are shrunk toward 0.

## 7. Walk-forward backtesting
- **What:** rolling train→test windows, out-of-sample results only, with fees and slippage. **Edge:** exposes overfitting before paper.
- **Libs:** `backtesting.py` (⚠ AGPL, fine for private use), `vectorbt` (⚠ Apache-2 + Commons Clause, no reselling), `backtrader` (GPL-3, old).
- **Extends:** existing backtest/eval module. **Data:** 2-source historical OHLCV.
- **Tests:** a lookahead-bias check (shifted signals must degrade), and deterministic re-runs.

## 8. Probabilistic / Bayesian ensembles
- **What:** combine signals as calibrated probabilities (logistic stacking, Bayesian model averaging). **Edge:** better-calibrated confidence, so it trades only above a threshold.
- **Libs:** `scikit-learn` (BSD, CalibratedClassifierCV), `PyMC` (Apache-2; heavy, so use small models on 8 GB).
- **Extends:** decision brain's final scorer. **Tests:** Brier score and a reliability curve on out-of-sample data, beating a single-signal baseline.

## 9. News & sentiment scoring
- **What:** headline/post sentiment with decay and source weight. **Edge:** event-risk filter, more than a predictor.
- **Libs:** `vaderSentiment` (MIT, tiny), FinBERT `ProsusAI/finbert` (HF model, CPU OK; check its license). Free sources: RSS, CryptoPanic free tier, Gemini key for summaries.
- **Extends:** context/news agent. **Data:** an event must appear in ≥2 sources before it counts.
- **Tests:** a labelled headline set with an accuracy floor, and duplicate/recycled-news dedupe.

## 10. Cross-source price-gap alerts (evidence only)
- **What:** flag when the same asset differs by more than fees + x% across 2+ venues. **Edge:** data-error detection, and arbitrage *evidence* only (no auto-trade).
- **Libs:** `ccxt`. **Extends:** data-quality / alert module. **Tests:** a stale-feed fixture must be flagged as bad data, not as an opportunity.

## 11. Risk-of-ruin limits
- **What:** Monte Carlo of paper trade outcomes giving P(drawdown > limit), plus daily loss and max-concurrent caps. **Edge:** survival first.
- **Libs:** NumPy. **Extends:** risk manager (kill-switch). **Tests:** the switch trips at the limit, and a ruin probability above threshold blocks new trades.

## 12. Performance evals
- **What:** Sharpe, Sortino, max DD, expectancy, win rate, profit factor, Calmar. **Edge:** objective promote/reject decisions.
- **Libs:** `quantstats` (Apache-2), `empyrical-reloaded` (Apache-2).
- **Extends:** existing eval/report module (dashboard reads it). **Tests:** hand-computed fixtures must match to 1e-6.

## Build order (cheap → valuable)
12 → 5 → 11 → 4 → 7 → 1 → 2 → 6 → 3 → 8 → 9 → 10.

## Rejected
Paid data feeds, paid signal APIs, GPU-only deep models, and anything that auto-trades live or touches Lane A.
