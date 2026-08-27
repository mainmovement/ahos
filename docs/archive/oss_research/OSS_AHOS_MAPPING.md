# AHOS Open-Source Capability & Codebase Mapping Dossier

This document provides the exact 1-to-1 capability mapping between external open-source technologies and the AHOS codebase, detailing the gap, native implementation plan, required test suites, and concrete expected benefits.

---

## 1. Comprehensive Capability Mapping Table

```
External Capability ──► AHOS Existing Capability ──► Technical Gap ──► Integration Strategy ──► Tests Required ──► Expected Benefit
```

---

### Mapping 01: In-Process Analytical OLAP (DuckDB)
- **External Capability**: Columnar vector execution engine, out-of-core SQL scans, direct Parquet & SQLite querying without database locks.
- **AHOS Existing Capability**: SQLite storage via `sqlite3` in `architecture/learning/score_ledger.py` and `paper_trading/ledger.py`.
- **Identified Gap**: Heavy analytical queries (e.g. Brier score calibration, multi-month trade metrics, equity curve aggregations) cause SQLite database table locks and slow down the background observation daemon.
- **Candidate Implementation**: `duckdb.connect()` analytical bridge with fallback to standard `sqlite3`.
- **Integration Strategy**: Create `architecture/intel/analytics_bridge.py` and `architecture/knowledge/duck_store.py` providing zero-copy analytical queries over SQLite tables and Parquet files.
- **Tests Required**: `tests/test_analytics_bridge.py` (query correctness, speedup verification, non-blocking concurrent writes, SQLite fallback when DuckDB is absent).
- **Expected Benefit**: 10x-50x faster analytical execution, zero database lock contention on Windows laptops.

---

### Mapping 02: High-Performance Vectorized Time-Series Expressions (Polars)
- **External Capability**: Multithreaded SIMD vectorized DataFrame operations, lazy query optimization, fast rolling window functions.
- **AHOS Existing Capability**: Pandas & NumPy calculations in `architecture/features/extractor.py` and `research/baseline_stats.py`.
- **Identified Gap**: Pandas creates significant memory overhead and high CPU latency during rolling window statistics (e.g. 50-period EMA, Bollinger Bands, ATR) across thousands of tokens.
- **Candidate Implementation**: Polars lazy frame expressions and pure-vectorized NumPy SIMD rolling aggregators.
- **Integration Strategy**: Enhance `architecture/features/extractor.py` and `research/baseline_stats.py` with native vectorized kernel operations.
- **Tests Required**: `tests/test_feature_extractor_vectorized.py` (numerical equivalence between Pandas and Vectorized engines, performance benchmarks).
- **Expected Benefit**: Sub-millisecond feature extraction per token pair, 70% reduction in peak RAM usage on Windows laptops.

---

### Mapping 03: Fast Vectorized Hyperparameter Backtesting (VectorBT)
- **External Capability**: Multi-dimensional tensor signal generation and backtesting over large parameter grids.
- **AHOS Existing Capability**: Sequential loop in `engine/ahos_backtest.py` and `strategy_lab/run_lab.py`.
- **Identified Gap**: Evaluating 100 parameter combinations takes minutes; no matrix tensor evaluation.
- **Candidate Implementation**: Clean-room native vectorized tensor backtester in `strategy_lab/vector_engine.py`.
- **Integration Strategy**: Implement matrix array operations evaluating entry/exit matrices simultaneously across arbitrary parameter ranges.
- **Tests Required**: `tests/test_vector_backtest.py` (matrix signal precision, multi-asset tensor simulation, equivalence against discrete engine).
- **Expected Benefit**: 1,000 parameter combinations evaluated in under 2 seconds.

---

### Mapping 04: Realistic Event-Driven Fill & Microstructure Simulation (NautilusTrader & HftBacktest)
- **External Capability**: Discrete event simulation, limit order book (LOB) queue position degradation, latency jitter, and nonlinear DEX slippage.
- **AHOS Existing Capability**: Linear cost model in `paper_trading/cost_model.py` and sequential fills in `paper_trading/engine_v3.py`.
- **Identified Gap**: Real DEX trades experience non-linear price impact based on constant-product liquidity pool reserves ($x \cdot y = k$) and queue delays.
- **Candidate Implementation**: Native Event-Driven Microstructure Simulator in `engine/event_backtest.py`.
- **Integration Strategy**: Extract NautilusTrader event-queue mechanics and HftBacktest queue degradation formulas into pure-Python native classes.
- **Tests Required**: `tests/test_event_backtest.py` (queue priority ordering, non-linear constant product slippage, partial fill handling).
- **Expected Benefit**: Zero look-ahead bias, realistic DEX fill simulation, prevention of overfitting on illiquid tokens.

---

### Mapping 05: Institutional Quantitative Tear-Sheet Analytics (QuantStats)
- **External Capability**: Sharpe, Sortino, Calmar, Omega, Tail Ratio, Value at Risk (VaR 95/99%), Conditional VaR (CVaR), underwater drawdown curves.
- **AHOS Existing Capability**: Simple win rate, profit factor, and max drawdown in `research/baseline_stats.py`.
- **Identified Gap**: Lack of tail-risk metrics, downside volatility penalization, and institutional risk metrics required for robust strategy acceptance.
- **Candidate Implementation**: Native QuantStats module in `research/quant_metrics.py`.
- **Integration Strategy**: Clean-room implementation of all core financial risk equations with zero external dependencies (pure NumPy).
- **Tests Required**: `tests/test_quant_metrics.py` (mathematical verification of Sharpe, Sortino, CVaR against pinned reference datasets).
- **Expected Benefit**: Complete institutional tear-sheets generated for all strategy lab and paper-trading runs.

---

### Mapping 06: Machine Learning Regime & Drift Detection (River & HMMlearn)
- **External Capability**: ADWIN adaptive windowing for concept drift, Hidden Markov Models (HMM) for discrete market regime classification.
- **AHOS Existing Capability**: Static score thresholds in `architecture/scoring/engine.py` and heuristic regimes in `architecture/decision/advisor.py`.
- **Identified Gap**: Inability to detect when underlying market dynamics have structurally shifted (e.g. regime shift from low-volatility trend to high-volatility chop).
- **Candidate Implementation**: Native ADWIN Drift Detector (`architecture/learning/drift.py`) and Gaussian HMM Regime Classifier (`architecture/intel/regimes.py`).
- **Integration Strategy**: Integrate streaming drift monitoring into observation loop and regime state conditioning into decision advisor.
- **Tests Required**: `tests/test_drift_and_regimes.py` (drift detection on synthetic step changes, HMM regime transitions, state persistence).
- **Expected Benefit**: Automated model recalibration triggers when market conditions change; regime-specific strategy activation.

---

### Mapping 07: Unified Public Market & DEX Data Providers (OpenBB, CCXT, DefiLlama, GeckoTerminal)
- **External Capability**: Multi-provider fallback routing, unified ticker/OHLCV/TVL data models, automatic rate-limiting budgets.
- **AHOS Existing Capability**: Basic separate provider scripts in `architecture/providers/`.
- **Identified Gap**: Fragmented provider interfaces without unified schema contracts, centralized rate-limit budgets, or multi-hop fallbacks.
- **Candidate Implementation**: Unified Provider Router & DEX Client in `architecture/providers/router_v2.py` and `architecture/providers/defillama.py`.
- **Integration Strategy**: Implement OpenBB-style provider router with CCXT-compatible normalization and DefiLlama protocol intelligence.
- **Tests Required**: `tests/test_unified_provider_router.py` (multi-provider fallback, rate limit queuing, schema conformance, offline mock validation).
- **Expected Benefit**: 100% reliable public data ingestion, multi-chain protocol revenue and TVL intelligence at $0 cost.

---

### Mapping 08: Multi-Agent Role Specialization & Debate Council (TradingAgents & LangGraph)
- **External Capability**: Role-specialized agents (Fundamental, Technical, Sentiment, Risk, Bull vs Bear debate, Arbitrator synthesis), cyclic state machines.
- **AHOS Existing Capability**: Simple sequential prompt in `architecture/ai/council_live.py`.
- **Identified Gap**: LLM hallucinations and single-perspective cognitive bias in trading opportunity evaluations.
- **Candidate Implementation**: Multi-Perspective Adversarial Debate Council in `architecture/ai/debate_council.py`.
- **Integration Strategy**: Implement structured Bull/Bear adversarial debate rounds with explicit Risk Manager veto authority and Arbitrator consensus.
- **Tests Required**: `tests/test_debate_council.py` (debate convergence, risk veto enforcement, deterministic heuristic fallback).
- **Expected Benefit**: Drastic reduction in LLM hallucinations; balanced, auditable reasoning with evidence attribution.

---

### Mapping 09: Structured LLM Extraction & Multi-Provider AI Routing (Instructor & LiteLLM)
- **External Capability**: Pydantic schema-enforced output extraction with retry loops; universal tiered provider routing (Ollama Local -> Free Cloud -> Heuristics).
- **AHOS Existing Capability**: Raw JSON parsing in `architecture/ai/clients.py` with failure vulnerability.
- **Identified Gap**: Occasional malformed JSON from small local LLMs causing runtime crashes; reliance on single Ollama endpoint.
- **Candidate Implementation**: Resilient AI Router & Schema Guard in `architecture/ai/router.py` and `architecture/ai/schema_guard.py`.
- **Integration Strategy**: Wrap all model calls in automatic validation loops that feed error traces back to the model for instant repair; route failures to deterministic fallback.
- **Tests Required**: `tests/test_ai_router_and_guard.py` (malformed JSON recovery, tiered provider failover, 100% offline heuristic execution).
- **Expected Benefit**: Zero crash rate from LLM responses; seamless operation whether Ollama is active, offline, or using free cloud endpoints.

---

### Mapping 10: Model Context Protocol Tool Registry & Read-Only Sandbox (FastMCP)
- **External Capability**: Standardized JSON-RPC tool manifests, automatic schema generation, strict security sandboxing.
- **AHOS Existing Capability**: Internal direct Python function calls.
- **Identified Gap**: No standardized tool interface for external or autonomous engineering agents; lack of formal capability discovery.
- **Candidate Implementation**: Native FastMCP Tool Registry in `architecture/tools/mcp_registry.py`.
- **Integration Strategy**: Expose AHOS analytical, backtesting, and data querying capabilities via standardized MCP tool contracts with strict read-only enforcement.
- **Tests Required**: `tests/test_mcp_registry.py` (tool registration, schema reflection, invocation dispatch, security boundary denial of unsafe operations).
- **Expected Benefit**: Seamless interoperability with MCP clients, autonomous agents, and IDEs while ensuring zero risk of accidental trade execution or file deletion.
