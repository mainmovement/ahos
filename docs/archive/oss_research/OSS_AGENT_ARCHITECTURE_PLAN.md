# AHOS Multi-Agent Specialist Ecosystem & MCP Tool Architecture Plan

This document establishes the architecture for AHOS's specialized agent collective, defining strict responsibilities, inputs, outputs, authorities, tool access rights, persistent states, and security boundaries.

---

## 1. Specialist Agent Ecosystem Topology

```
                                  +-------------------------------+
                                  |     AHOS CONTROL PLANE        |
                                  +-------------------------------+
                                                  |
         +--------------------+-------------------+--------------------+--------------------+
         |                    |                   |                    |                    |
         v                    v                   v                    v                    v
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
|   DATA AGENT    |  | DISCOVERY AGENT | | ON-CHAIN AGENT  | | SECURITY AGENT  |  |  REGIME AGENT   |
| (Multi-Provider)|  | (Pair Scanner)  | | (DEX & Holders) | | (Honeypot/Audit)|  | (HMM & Drift)   |
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
         |                    |                   |                    |                    |
         +--------------------+-------------------+--------------------+--------------------+
                                                  |
                                                  v
                                  +-------------------------------+
                                  |     DECISION & RESEARCH LAB   |
                                  +-------------------------------+
                                                  |
         +--------------------+-------------------+--------------------+--------------------+
         |                    |                   |                    |                    |
         v                    v                   v                    v                    v
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
| RESEARCH AGENT  |  | BACKTEST AGENT  | |   RISK AGENT    | | EVIDENCE AGENT  |  |  CRITIC AGENT   |
| (Hypotheses)    |  | (Quant & Sim)   | | (Bankroll/Veto) | | (Audit & Brier) |  | (Bull vs Bear)  |
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
```

---

## 2. Exhaustive Specialist Agent Specifications

### 1. Data Agent
- **Responsibility**: Ingest, normalize, validate, and cache market data across CEX, DEX, and macro providers.
- **Input**: Provider configuration, polling schedules, token address queries.
- **Output**: Typed `DataEnvelope` with timestamp, confidence, latency, and sha256 payload hash.
- **Authority**: Read-only public HTTP/RPC requests. Rate-limit enforcement.
- **Tools**: `market_data_fetch`, `dex_pool_query`, `coingecko_spot_fetch`, `defillama_tvl_fetch`.
- **State**: Provider health table, latency moving averages, circuit breaker states.
- **Tests**: `tests/test_collector_engine.py`, `tests/test_unified_provider_router.py`.

### 2. Discovery Agent
- **Responsibility**: Continuously scan decentralized exchanges for newly launched pairs, liquidity additions, and volume spikes.
- **Input**: DEX factory event logs, GeckoTerminal / DexScreener new pair feeds.
- **Output**: Candidate opportunity records (`TokenIdentity`, initial liquidity, creation timestamp).
- **Authority**: Candidate registration in discovery queue.
- **Tools**: `dex_pair_scanner`, `token_metadata_resolver`.
- **State**: Seen token bloom filter, discovery timestamp index.
- **Tests**: `tests/test_discovery.py`.

### 3. On-Chain Agent
- **Responsibility**: Analyze token holder distribution, smart money wallet flows, and liquidity reserve depth.
- **Input**: Smart contract addresses, pool addresses, blockchain RPC endpoints.
- **Output**: Gini coefficient, top-10 holder concentration percentage, LP token burn/lock status.
- **Authority**: On-chain read-only RPC calls.
- **Tools**: `holder_distribution_query`, `lp_lock_verifier`, `smart_money_tracker`.
- **State**: Tracked whale address database, LP lock verification cache.
- **Tests**: `tests/test_whale_detector.py`, `tests/test_holders.py`.

### 4. Security Agent
- **Responsibility**: Execute honeypot simulations, buy/sell tax verification, and malicious bytecode forensics.
- **Input**: Token contract bytecode, simulation RPC node, security API feeds.
- **Output**: `SecurityScore` ($[0, 100]$), tax percentages, honeypot pass/fail flag, blacklist presence.
- **Authority**: Mandatory **VETO POWER**: Opportunities with Security Score $< 70$ are automatically dropped.
- **Tools**: `honeypot_simulator`, `tax_calculator`, `bytecode_sanitizer`.
- **State**: Known malicious deployer registry, signature blacklist.
- **Tests**: `tests/test_security_engine.py`, `tests/test_security_gate.py`.

### 5. Market Regime Agent
- **Responsibility**: Infer latent market regimes (Bull Trend, Bear Volatile, Neutral Chop) and detect distribution drift.
- **Input**: Multi-asset return time series, realized volatility, ADWIN streaming statistics.
- **Output**: `RegimeState` (state id, state probabilities, drift alert flag).
- **Authority**: Sets active strategy regime filters in Decision Core.
- **Tools**: `hmm_regime_estimator`, `adwin_drift_detector`.
- **State**: HMM transition matrix, Gaussian emission parameters, ADWIN histogram memory.
- **Tests**: `tests/test_drift_and_regimes.py`.

### 6. Research Agent
- **Responsibility**: Formulate new quantitative hypotheses and strategy parameter candidates.
- **Input**: Market regime state, historical failure lessons, feature correlations.
- **Output**: Structured `HypothesisProposal` (entry conditions, exit conditions, parameter bounds).
- **Authority**: Submits proposals to Research Lab.
- **Tools**: `hypothesis_generator`, `feature_correlation_matrix`.
- **State**: Hypothesis registry, search space exploration state.
- **Tests**: `tests/test_strategy_lab_hypotheses.py`.

### 7. Backtest Agent
- **Responsibility**: Execute vectorized parameter sweeps and event-driven backtests with realistic slippage.
- **Input**: `HypothesisProposal`, historical OHLCV/tick dataset, fee/slippage parameters.
- **Output**: `BacktestResult` (equity curve, trade log, Sharpe, Sortino, MaxDD, CVaR).
- **Authority**: Quantitative backtesting execution.
- **Tools**: `vector_backtest_runner`, `event_backtest_runner`, `purged_cv_evaluator`.
- **State**: Dataset cache, backtest run index.
- **Tests**: `tests/test_event_backtest.py`, `tests/test_vector_backtest.py`.

### 8. Risk Agent
- **Responsibility**: Compute position sizing, portfolio risk parity, and portfolio-level drawdown limits.
- **Input**: Candidate opportunity scores, covariance matrices, current bankroll exposure.
- **Output**: Position sizing fraction ($f \in [0.0, 0.05]$), stop-loss levels, portfolio exposure limits.
- **Authority**: Mandatory **VETO POWER**: Can reduce position size to 0 or block trade proposals.
- **Tools**: `risk_parity_solver`, `kelly_calculator`, `drawdown_guard`.
- **State**: Open paper positions, current peak equity, cumulative exposure ledger.
- **Tests**: `tests/test_risk_engine.py`, `tests/test_bankroll.py`.

### 9. Evidence Agent
- **Responsibility**: Record predictions, observe actual forward outcomes, calculate Brier scores, and maintain calibration curves.
- **Input**: System predictions, forward token price observations ($t+1h, t+24h, t+7d$).
- **Output**: Immutable Evidence Records, Brier score, reliability bin calibration metrics.
- **Authority**: Ledger write authorization for calibration events.
- **Tools**: `evidence_logger`, `brier_score_calculator`, `calibration_plotter`.
- **State**: SQLite / DuckDB evidence ledger, calibration bin histograms.
- **Tests**: `tests/test_evidence_common.py`, `tests/test_calibration_report.py`.

### 10. Critic Agent (Adversarial Debate Council)
- **Responsibility**: Conduct structured Bull vs Bear debates, stress-test logic, and identify hidden risks.
- **Input**: Full opportunity context, on-chain metrics, technical indicators.
- **Output**: `DebateSynthesis` (Bull arguments, Bear counter-arguments, dissent notes, consensus score).
- **Authority**: Recommends score penalties to Decision Advisor.
- **Tools**: `ai_debate_runner`, `counter_hypothesis_builder`.
- **State**: Debate transcript archive, model calibration bias ledger.
- **Tests**: `tests/test_debate_council.py`.

---

## 3. FastMCP Tool Interface & Sandboxing Guardrails

All tools provided to agents conform to the **Model Context Protocol (MCP)** JSON-RPC specification.

### 3.1 Security Boundary Matrix

```
+-------------------------------------------------------------------------------+
|                             SECURITY SANDBOX GATES                            |
+-------------------------------------------------------------------------------+
|  PERMITTED (Read-Only & Compute)        |  STRICTLY FORBIDDEN (Denied)        |
|-----------------------------------------+-------------------------------------|
|  [✓] Query SQLite & DuckDB analytical   |  [✗] Shell / Subprocess arbitrary   |
|      databases                          |      execution                      |
|  [✓] Query public REST & RPC endpoints  |  [✗] Private key or wallet signing  |
|  [✓] Read repository source & docs      |  [✗] Destructive filesystem deletes |
|  [✓] Run vectorized & event backtests   |  [✗] Network connections to secret  |
|  [✓] Compute statistical risk metrics   |      or credential endpoints        |
+-------------------------------------------------------------------------------+
```
