# AHOS Open-Source Integration Backlog

This document defines the actionable, phased engineering backlog for integrating top-ranked open-source capabilities into the AHOS repository. Every task includes strict acceptance criteria, dependency requirements, and rollback strategies.

---

## 1. Phased Priority Master Backlog

```
+---------------------------------------------------------------------------------------+
| P0 (Core Foundation)      : Data Layer (DuckDB/Polars), AI Router, Import Integrity   |
| P1 (Quant & Intelligence) : Backtest Upgrade, QuantStats Metrics, DefiLlama, Regimes |
| P2 (Agents & Knowledge)   : Debate Council, FastMCP Tools, Drift Detection, Lab Engine|
| P3 (Observability & CLI)  : Structured Logging Spans, Benchmarks, Documentation       |
+---------------------------------------------------------------------------------------+
```

---

### Phase 0: Foundations & Data Infrastructure (P0)

#### Task OSS-001: High-Performance Analytics & DuckDB Bridge
- **Priority**: `P0`
- **Target Module**: `architecture/intel/analytics_bridge.py` & `architecture/knowledge/duck_store.py`
- **Objective**: Implement an embedded OLAP analytical query engine using DuckDB with zero-copy queries over SQLite databases and Parquet files, with pure-Python SQLite fallback.
- **Acceptance Criteria**:
  1. Executes complex aggregations (Brier score calibration, trade ledgers) 5x+ faster than standard SQLite.
  2. Never acquires exclusive write locks on SQLite databases.
  3. Gracefully falls back to standard `sqlite3` if DuckDB is unavailable.
  4. 100% test pass on Windows and Linux without background server processes.
- **Dependencies**: `duckdb>=1.0.0` (optional/graceful), `sqlite3`.
- **Rollback Strategy**: Point query interface directly to SQLite DAO.

#### Task OSS-002: Resilient Multi-Tier AI Provider Router & Schema Guard
- **Priority**: `P0`
- **Target Module**: `architecture/ai/router.py` & `architecture/ai/schema_guard.py`
- **Objective**: Implement LiteLLM/Instructor-inspired tiered model routing (Local Ollama -> Free Cloud APIs -> Deterministic Heuristics) and Pydantic JSON schema extraction with retry loops.
- **Acceptance Criteria**:
  1. Automatically routes to deterministic fallback when Ollama is offline or times out.
  2. Guarantees 100% valid JSON conforming to target schemas via automatic retry with error feedback.
  3. Strict zero-cost floor: never requires paid API keys.
  4. Unit tests pass with simulated provider timeouts, 500 errors, and malformed JSON.
- **Dependencies**: `contracts/`, `architecture/ai/clients.py`.
- **Rollback Strategy**: Revert to existing `architecture/ai/clients.py` heuristic council.

---

### Phase 1: Quantitative Research & Backtesting Lab (P1)

#### Task OSS-003: Institutional Quantitative Tear-Sheet & Risk Metrics Engine
- **Priority**: `P1`
- **Target Module**: `research/quant_metrics.py` & `research/baseline_stats.py`
- **Objective**: Adapt QuantStats/Pyfolio mathematical formulas into a clean-room, pure-NumPy statistical module calculating Sharpe, Sortino, Calmar, Omega, Tail Ratio, VaR 95/99%, and CVaR.
- **Acceptance Criteria**:
  1. Computes full quantitative tear-sheets for any equity or return series.
  2. Numerically matches benchmark formulas within $10^{-6}$ precision.
  3. Zero external C-library or paid SDK dependencies (runs purely on NumPy/Pandas).
  4. Integrated into AHOS backtest and strategy lab reports.
- **Dependencies**: `numpy`, `pandas`.
- **Rollback Strategy**: Revert `research/baseline_stats.py` to baseline win-rate/drawdown calculations.

#### Task OSS-004: Next-Generation Hybrid Event-Driven & Microstructure Backtester
- **Priority**: `P1`
- **Target Module**: `engine/event_backtest.py` & `strategy_lab/vector_engine.py`
- **Objective**: Implement a dual-mode backtesting system combining VectorBT-style fast matrix tensor parameter sweeps with NautilusTrader/HftBacktest-style event-driven queue position, liquidity consumption, and fee modeling.
- **Acceptance Criteria**:
  1. Vector mode evaluates 1,000 parameter combinations in under 2 seconds.
  2. Event mode models non-linear constant-product AMM slippage ($x \cdot y = k$) and latency delays.
  3. Zero look-ahead bias enforced through strict causal event queues.
  4. Full validation on historical multi-pair datasets.
- **Dependencies**: `numpy`, `pandas`, `research/quant_metrics.py`.
- **Rollback Strategy**: Retain existing `engine/ahos_backtest.py` as legacy fallback.

#### Task OSS-005: Walk-Forward Optimization & Purged Cross-Validation Engine
- **Priority**: `P1`
- **Target Module**: `strategy_lab/validation_engine.py`
- **Objective**: Implement Marcos Lopez de Prado's Purged & Embargoed K-Fold Cross-Validation and rolling Walk-Forward Optimization (WFA) to eliminate data leakage and overfitting.
- **Acceptance Criteria**:
  1. Implements Purged K-Fold CV with configurable embargo window preventing serial correlation leakage.
  2. Implements Rolling Walk-Forward Optimization with train/test splits.
  3. Generates Out-of-Sample (OOS) efficiency ratios ($OOS_{Sharpe} / IS_{Sharpe}$).
  4. Fully covered by unit tests with synthetic non-stationary time series.
- **Dependencies**: `numpy`, `research/quant_metrics.py`.
- **Rollback Strategy**: Revert to single in-sample train/test splits.

#### Task OSS-006: DefiLlama & Multi-Chain DEX Public Intelligence Providers
- **Priority**: `P1`
- **Target Module**: `architecture/providers/defillama.py` & `architecture/providers/dex_pools.py`
- **Objective**: Implement zero-cost, unauthenticated public adapters for DefiLlama protocol fundamentals (TVL, volume, fees) and GeckoTerminal/DexScreener multi-chain DEX pool reserves.
- **Acceptance Criteria**:
  1. Queries public endpoints with built-in token-bucket rate limiting and circuit breakers.
  2. Normalizes all responses into typed Pydantic/dataclass models with confidence & freshness stamps.
  3. Complete offline mock fixtures for automated testing.
  4. Iranian network resilience via SOCKS5 proxy support.
- **Dependencies**: `requests` / `urllib`, `architecture/collector/circuit_breaker.py`.
- **Rollback Strategy**: Fallback to mock provider stubs in offline environments.

---

### Phase 2: Autonomous Multi-Agent & Knowledge Layer (P2)

#### Task OSS-007: Structured Multi-Role Adversarial Debate Council
- **Priority**: `P2`
- **Target Module**: `architecture/ai/debate_council.py`
- **Objective**: Adapt TradingAgents-inspired structured multi-agent debate protocols into the AHOS AI subsystem, featuring Bull Researcher, Bear Researcher, Risk Manager veto, and Council Arbitrator.
- **Acceptance Criteria**:
  1. Executes 2-round adversarial debate between Bull and Bear personas.
  2. Risk Manager holds unilateral veto power over high-risk or low-exitability opportunities.
  3. Operates seamlessly with local Ollama models or offline deterministic heuristics.
  4. Emits structured JSON audit trails with full reasoning and dissent records.
- **Dependencies**: `architecture/ai/router.py`, `architecture/ai/schema_guard.py`.
- **Rollback Strategy**: Fallback to standard `architecture/council.py`.

#### Task OSS-008: Native FastMCP Tool Registry & Sandbox Security Boundary
- **Priority**: `P2`
- **Target Module**: `architecture/tools/mcp_registry.py` & `architecture/tools/sandbox.py`
- **Objective**: Implement an MCP-compliant tool registration and execution gateway exposing AHOS market intelligence, backtesting, and data querying tools with strict read-only sandboxing.
- **Acceptance Criteria**:
  1. Standard Model Context Protocol (MCP) tool schema reflection (`tools/list`, `tools/call`).
  2. Strict read-only enforcement: rejects file write, shell exec, or trade execution commands.
  3. Standardized parameter validation and JSON-RPC 2.0 response formatting.
  4. Comprehensive unit tests verifying sandbox breach denial.
- **Dependencies**: `contracts/`, `architecture/security/hygiene.py`.
- **Rollback Strategy**: Disable external tool endpoint.

#### Task OSS-009: Streaming Concept Drift Detection & HMM Regime Engine
- **Priority**: `P2`
- **Target Module**: `architecture/learning/drift.py` & `architecture/intel/regimes.py`
- **Objective**: Adapt River's ADWIN drift detection and HMMlearn Gaussian regime classification into the AHOS learning and decision subsystem.
- **Acceptance Criteria**:
  1. ADWIN detects variance shifts and structural mean breaks on streaming token scores.
  2. 2-state and 3-state Gaussian HMM models categorize regimes (Bull Trending, Bear Volatile, Chop).
  3. Sub-millisecond compute overhead per observation tick.
  4. Fully covered by unit tests.
- **Dependencies**: `numpy`, `scipy` (or pure-Python Baum-Welch/Viterbi fallback).
- **Rollback Strategy**: Fallback to static score thresholds.

#### Task OSS-010: Autonomous Research Lab Hypothesis Lifecycle Engine
- **Priority**: `P2`
- **Target Module**: `strategy_lab/hypothesis_engine.py` & `strategy_lab/evidence_recorder.py`
- **Objective**: Implement an end-to-end automated research lab executing: Hypothesis -> Dataset Selection -> Feature Matrix -> Vectorized Backtest -> Walk-Forward Validation -> Monte Carlo Stress Test -> Evidence Recording -> Knowledge Store.
- **Acceptance Criteria**:
  1. Autonomous evaluation of hypothesis candidates with zero human intervention.
  2. Automatic rejection of hypotheses failing Sharpe > 1.2, MaxDD < 25%, or OOS Efficiency < 0.6.
  3. Records immutable evidence snapshots to `research/experiments/`.
  4. 100% reproducible and auditable.
- **Dependencies**: `strategy_lab/vector_engine.py`, `strategy_lab/validation_engine.py`, `research/quant_metrics.py`.
- **Rollback Strategy**: Revert to manual `strategy_lab/run_lab.py`.

---

### Phase 3: Observability, Hygiene & Benchmarks (P3)

#### Task OSS-011: Structured Tracing, Benchmarks & Validation Gates
- **Priority**: `P3`
- **Target Module**: `architecture/observability.py` & `scripts/benchmark_performance.py`
- **Objective**: Implement structured JSON logging spans across data, backtest, and intelligence pipelines; add comprehensive performance benchmarks validating speedup on Windows.
- **Acceptance Criteria**:
  1. Benchmarks quantify runtime, memory, throughput, and backtest speed.
  2. All 1,159+ legacy tests plus new test suites pass with 100% success rate.
  3. Lane-A integrity SHA-256 remains strictly un-drifted (`validate_imports.py` PASS).
- **Dependencies**: Full AHOS codebase.
