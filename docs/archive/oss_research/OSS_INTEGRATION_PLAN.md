# AHOS Open-Source Intelligence & Capability Integration Plan (Master Plan)

## 1. Executive Summary & Master Vision

The **AHOS (Autonomous Hybrid Opportunity System)** mission is to build a world-class, autonomous, modular, data-first, and evidence-governed intelligence system operating reliably on a standalone Windows laptop with a strict **$0/month infrastructure cost floor**.

This document outlines the master architectural and engineering integration plan derived from comprehensive open-source research across 100+ candidates and a finalized **TOP-20 Open-Source Technology Stack**.

### First Principles
1. **Existing Verified Capability > New Unverified Capability**: No legacy AHOS module, schema, test, or invariant is discarded. All enhancements are additive, modular, and backwards-compatible.
2. **Lane-A Absolute Freeze**: The core discovery and paper-trading scientific surfaces (`discovery/`, `paper_trading/`) remain strictly pinned by SHA-256 integrity hashes (`config/lane_a_freeze.sha256`).
3. **Evidence-Boundary Guarantee**: Intelligence, risk, scoring, and research components never consume untrusted raw data directly. All external data passes through typed schemas, confidence scores, freshness timestamps, provenance tracking, and circuit breakers.
4. **Deterministic Calculation Over LLM Guesswork**: Language models are strictly confined to hypothesis ideation, multi-perspective debate, and research synthesis. LLMs never fabricate prices, compute metrics, bypass risk controls, or execute live financial transactions.
5. **Zero-Cost & Local-First**: 100% of capabilities function locally and offline on consumer Windows hardware (CPU/GPU) with SQLite/DuckDB/Parquet, local Ollama models, and free public APIs with resilient fallbacks.

---

## 2. Capability Integration Tiering Taxonomy

Every external technology is evaluated and assigned to one of four strict integration tiers:

```
+-------------------------------------------------------------------------------+
|                             INTEGRATION TIERS                                 |
+-------------------------------------------------------------------------------+
| [Tier 1] Reusable Dependency  : Direct PyPI dependency (permissive license,   |
|                                 zero-bloat, cross-platform Windows native).    |
| [Tier 2] Reusable Module      : Self-contained module adapted into AHOS       |
|                                 with strict attribution & typed contracts.    |
| [Tier 3] Architectural Pattern: Design pattern or algorithmic concept         |
|                                 re-implemented natively in AHOS clean-room.   |
| [Tier 4] Reference Only       : Studied for insights/benchmarks; NO code      |
|                                 imported into the repository.                 |
+-------------------------------------------------------------------------------+
```

---

## 3. Top-20 Technology Portfolio at a Glance

| # | Project | Category | Tier | License | Primary Contribution to AHOS |
|---|---|---|---|---|---|
| 1 | **DuckDB** | Data Engineering | Tier 1 | MIT | In-process OLAP SQL engine, zero-copy Parquet analytics, out-of-core data processing |
| 2 | **Polars** | Data Engineering | Tier 1 | MIT | Blazing-fast multithreaded SIMD vectorized DataFrames for time-series features |
| 3 | **VectorBT** | Backtesting & Quant | Tier 3 | Apache-2.0 | High-speed vectorized hyper-parameter backtesting & matrix signal evaluation |
| 4 | **NautilusTrader** | Event-Driven Sim | Tier 3 | LGPL-3.0 | Event-driven order matching, queue position, realistic slippage & market impact logic |
| 5 | **HftBacktest** | Microstructure | Tier 3 | MIT | Limit order book (LOB) queue position and latency simulation patterns |
| 6 | **QuantStats** | Quant Analytics | Tier 2 | Apache-2.0 | Comprehensive quantitative tear-sheet analytics (Sharpe, Sortino, Calmar, VaR, CVaR) |
| 7 | **Riskfolio-Lib** | Quantitative Risk | Tier 3 | BSD-3-Clause | Risk parity, Hierarchical Risk Parity (HRP), and coherent risk measure formulations |
| 8 | **River** | Online ML | Tier 3 | BSD-3-Clause | Incremental streaming ML, concept drift detection (ADWIN, Page-Hinkley) for regime shifts |
| 9 | **HMMlearn** | Regime Detection | Tier 1 | BSD-3-Clause | Gaussian & Multinomial Hidden Markov Models for unsupervised market regime segmentation |
| 10 | **OpenBB** | Market Intelligence | Tier 3 | Apache-2.0 | Provider-agnostic router architecture, Pydantic unified financial data models |
| 11 | **CCXT** | Market Data | Tier 3 | MIT | Unified multi-exchange public ticker/OHLCV/orderbook ingestion & rate-limiter patterns |
| 12 | **DefiLlama** | DEX / On-chain | Tier 3 | MIT | Free public TVL, protocol revenue, chain volume, and yield aggregator client patterns |
| 13 | **GeckoTerminal / DexScreener** | DEX Intelligence | Tier 2 | MIT | Multi-chain liquidity pool discovery, reserve ratio tracking, swap volume monitoring |
| 14 | **TradingAgents** | LLM Multi-Agent | Tier 3 | MIT | Multi-role specialist debate protocols (Bull/Bear, Risk, Valuation, Arbitrator) |
| 15 | **LangGraph** | Agent Graph State | Tier 3 | MIT | Cyclic state machine graph execution with deterministic rollback and checkpointing |
| 16 | **FastMCP / MCP** | Tool Context Protocol | Tier 3 | MIT | Standardized Model Context Protocol schemas for tool registration and capability discovery |
| 17 | **Instructor** | Structured LLM Extraction | Tier 3 | MIT | Pydantic-validated JSON extraction from local LLMs with retry guardrails |
| 18 | **LanceDB** | Embedded Vector Store | Tier 3 | Apache-2.0 | Serverless columnar vector knowledge store with zero background daemon overhead |
| 19 | **LiteLLM** | Local AI Routing | Tier 3 | MIT | Multi-provider fallback routing (Ollama Local -> Free Public APIs -> Deterministic Heuristics) |
| 20 | **APScheduler** | Job Scheduling | Tier 3 | MIT | Lightweight in-process interval & cron event loop scheduler with drift compensation |

---

## 4. Target Architecture & Integration Topology

```
+-------------------------------------------------------------------------------------------------------+
|                                              AHOS SYSTEM                                              |
+-------------------------------------------------------------------------------------------------------+
                                                   |
                   +-------------------------------+-------------------------------+
                   |                               |                               |
                   v                               v                               v
    +-----------------------------+ +-----------------------------+ +-----------------------------+
    |       DATA SUBSYSTEM        | |    INTELLIGENCE SUBSYSTEM   | |     KNOWLEDGE SUBSYSTEM     |
    | (OpenBB/CCXT/DefiLlama/DEX) | | (TradingAgents/HMM/River/AI)| |    (LanceDB/DuckDB/Memory)  |
    | - Multi-source public poll  | | - Multi-agent debate council| | - Hypotheses & lessons store|
    | - Provenance & confidence   | | - Regime detection (HMM)    | | - Evidence audit ledger     |
    | - Circuit breakers & retry  | | - Drift detection (ADWIN)   | | - Calibration tracking      |
    +-----------------------------+ +-----------------------------+ +-----------------------------+
                   |                               |                               |
                   +-------------------------------+-------------------------------+
                                                   |
                                                   v
                                   +-------------------------------+
                                   |       HIGH-PERFORMANCE        |
                                   |       DATA INTERCHANGE        |
                                   |      (DuckDB / Polars)        |
                                   | - Zero-copy Arrow memory      |
                                   | - Local Parquet / SQLite      |
                                   | - Streaming aggregations      |
                                   +-------------------------------+
                                                   |
                                                   v
                                   +-------------------------------+
                                   |         DECISION CORE         |
                                   |  (Deterministic Scoring & Risk|
                                   |   Riskfolio-Lib Formulations) |
                                   +-------------------------------+
                                                   |
                                                   v
                                   +-------------------------------+
                                   |      QUANT RESEARCH LAB       |
                                   | (VectorBT / NautilusTrader /  |
                                   |  HftBacktest / QuantStats)    |
                                   | - Walk-Forward Optimization   |
                                   | - Purged & Embargoed CV       |
                                   | - Realistic LOB Slippage      |
                                   | - Monte Carlo Stress Tests    |
                                   +-------------------------------+
                                                   |
                                                   v
                                   +-------------------------------+
                                   |     MCP TOOL & GOVERNANCE     |
                                   |   (FastMCP / Sandbox Gate)    |
                                   | - Deterministic tool schemas  |
                                   | - Read-only sandbox boundary  |
                                   | - Autonomous test & commit    |
                                   +-------------------------------+
```

---

## 5. Phased Integration Roadmap

### Phase 1: High-Performance Data & Analytics Layer (P0)
- Integrate embedded DuckDB analytical engine with zero-copy querying over SQLite and Parquet stores.
- Implement Polars-style vector expressions for sub-millisecond feature extraction and rolling window statistics.
- Establish unified data provider interface supporting multi-chain DEX (GeckoTerminal/DexScreener) and public crypto APIs.

### Phase 2: Next-Generation Backtest & Quant Research Lab (P1)
- Implement Event-Driven & Vectorized Hybrid Backtester with realistic queue position, liquidity constraints, and fee modeling.
- Implement Walk-Forward Analysis (WFA) and Purged/Embargoed Cross-Validation (K-Fold Time Series) to eliminate look-ahead bias.
- Implement Comprehensive QuantStats-compatible Tear-Sheet Metrics (Sharpe, Sortino, Calmar, Tail Risk, VaR, CVaR).
- Implement Monte Carlo Permutation & Resampling Stress Tester.

### Phase 3: Resilient Local AI & Multi-Agent Council (P2)
- Implement Tiered AI Provider Router: Ollama Local (Primary) -> Free Public Fallbacks -> Deterministic Heuristic Council.
- Implement TradingAgents-inspired structured specialist roles (Valuation, Sentiment, Momentum, Risk, Bull vs Bear debate).
- Implement Instructor-style Pydantic output validation with automatic schema repair.

### Phase 4: Self-Learning Research Lab & MCP Tool Ecosystem (P2)
- Implement Autonomous Hypothesis Lifecycle (Hypothesis -> Dataset -> Feature Matrix -> Backtest -> Walk-Forward -> Evidence).
- Implement FastMCP-compatible read-only Tool Registry with strict permission sandboxing.
- Expand Evidence Ledger & Brier Score Calibration with regime-conditioned accuracy tracking.

---

## 6. Verification and Acceptance Matrix

Every implemented feature must satisfy:
1. **100% Pass Rate** on full regression test suite (`pytest`).
2. **Lane-A SHA-256 Integrity Verification** (`scripts/validate_imports.py`).
3. **No Network Blockers**: Must execute in offline/local mock mode with zero API key requirement.
4. **Sub-second Performance**: Micro-benchmarks validating speedup over baseline.
5. **Clean Architecture & No Secret Leaks**: Zero unsafe subprocess, zero wallet operations, zero credential exposure.
