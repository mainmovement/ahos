# AHOS Open-Source Capability Matrix (Categories A – T)

This document systematically maps the 20 strategic technology domains against current AHOS capabilities, identifies technical gaps, scores integration priority, and defines the target integration architecture.

---

## 1. Complete Strategic Capability Map

| Cat | Domain Name | Current AHOS State | Leading Open-Source Reference | Capability Gap Identified | Priority Score | Target Tier & Decision |
|---|---|---|---|---|---|---|
| **A** | Crypto Market Intelligence | Basic CoinGecko/DEX scrapers (`architecture/providers/`) | OpenBB, CCXT | Lack of unified multi-provider fallback router, rate-limiting budgets, and standardized ticker models | **P0 (96/100)** | Tier 3 (Reimplement Native Provider Router) |
| **B** | Market Data Infrastructure | SQLite storage + basic Pandas DataFrames | DuckDB, Polars, Apache Arrow | SQLite table locking during large analytical queries; slow Pandas rolling window calculations | **P0 (98/100)** | Tier 1/3 (Native DuckDB OLAP + Polars Engine) |
| **C** | DEX / On-chain Intelligence | Basic DexScreener/DEXTools JSON adapter | DefiLlama, GeckoTerminal SDK | Missing protocol TVL, revenue, yield context, and AMM constant-product reserve tracking | **P1 (95/100)** | Tier 2 (Native DefiLlama & DEX Pool Engine) |
| **D** | Token Discovery & Security | Static heuristic filters (`discovery/security_gate.py`) | GoPlus, RugCheck, Slither patterns | Dynamic honeypot simulation, buy/sell tax verification, and liquidity lock duration checks | **P1 (92/100)** | Tier 3 (Enhanced Security Gate & Liquidity Guard) |
| **E** | Backtesting | Single-pass sequential backtester (`engine/ahos_backtest.py`) | VectorBT, NautilusTrader | Lack of matrix vectorized signal exploration, parameter grids, and realistic fill queue modeling | **P0 (97/100)** | Tier 3 (Hybrid Vectorized + Event Backtester) |
| **F** | Event-driven Simulation | Discrete tick loop in `paper_trading/engine_v3.py` | NautilusTrader, HftBacktest | Simplified slippage; missing limit order book (LOB) queue degradation and latency jitter | **P1 (93/100)** | Tier 3 (Native Microstructure Slippage Model) |
| **G** | Quantitative Research | Basic baseline stats (`research/baseline_stats.py`) | QuantStats, Pyfolio-Reloaded | Missing comprehensive tear-sheet metrics: Sortino, Calmar, Tail Risk, VaR, CVaR, underwater curves | **P0 (96/100)** | Tier 2 (Native Pure-Python QuantStats Engine) |
| **H** | Statistical Analysis | Brier score & reliability curves (`architecture/learning/`) | Scikit-learn, SciPy, Riskfolio-Lib | Lack of Purged K-Fold Cross-Validation, Combinatorial Purged CV, and Ledoit-Wolf covariance shrinkage | **P1 (94/100)** | Tier 3 (Native Purged CV & Risk Formulations) |
| **I** | Machine Learning | Static heuristic scoring weights | River (online-ml), LightGBM | Model parameter staleness; inability to adapt incrementally without full offline retraining | **P1 (91/100)** | Tier 3 (Streaming ADWIN Drift & Incremental Scoring) |
| **J** | Time Series & Regimes | Fixed volatility thresholds | HMMlearn, Statsmodels | Inability to classify non-linear latent market regimes (Bull Trend, Bear Volatile, Neutral Consolidation) | **P1 (92/100)** | Tier 3 (Native Gaussian HMM Regime Engine) |
| **K** | LLM Agents | Single prompt-based LLM queries (`architecture/ai/`) | TradingAgents, LangGraph | Single-perspective bias, vulnerability to model hallucination, lack of Bull/Bear adversarial debate | **P1 (95/100)** | Tier 3 (Structured Multi-Role Debate Council) |
| **L** | Multi-Agent Systems | Sequential agent matrix (`engine/agent_matrix_v2.py`) | LangGraph, AutoGen | Rigid linear pipeline without cyclic feedback, conditional graph branching, or state checkpointing | **P2 (90/100)** | Tier 3 (Stateful Multi-Agent Graph Orchestrator) |
| **M** | MCP / Tool-using Agents | Custom internal Python callers | FastMCP, Model Context Protocol | Lack of standardized tool manifests, JSON-RPC schemas, and strict read-only execution boundaries | **P1 (94/100)** | Tier 3 (Native FastMCP Tool Registry & Sandbox) |
| **N** | RAG / Knowledge Systems | SQLite key-value text store (`architecture/knowledge/`) | LanceDB, ChromaDB | Inability to perform vector similarity search over historical trade outcomes and research lessons | **P2 (89/100)** | Tier 3 (Native Vector Similarity & Knowledge Store) |
| **O** | Local AI & Serving | Basic Ollama HTTP client (`architecture/ai/clients.py`) | LiteLLM, Ollama SDK | Missing multi-tier fallback (Local Ollama -> Free Cloud APIs -> Deterministic Heuristics) and retries | **P0 (96/100)** | Tier 3 (Resilient Tiered AI Router & Circuit Breaker) |
| **P** | Data Engineering | Raw SQLite and CSV files | DuckDB, Polars, Parquet | Uncompressed data sprawl; slow analytical scans across multi-gigabyte historical time series | **P0 (98/100)** | Tier 1/3 (Native Parquet/DuckDB Storage Layer) |
| **Q** | Workflow Automation | `time.sleep()` loop in `architecture/runtime/` | APScheduler, Prefect | Sleep loop drift under load; missing persistent task queues and interval misfire handling | **P1 (92/100)** | Tier 3 (Drift-Compensated Event Loop Engine) |
| **R** | Observability | Basic file logging and metrics snapshot | OpenTelemetry, Structlog | Unstructured text logs; missing tracing spans across data ingestion, scoring, and research runs | **P1 (91/100)** | Tier 3 (Structured JSON Logging & Span Contexts) |
| **S** | Security & Supply Chain | Basic regex secret scan in `validate_imports.py` | Bandit, Safety, Semgrep patterns | Missing AST-based unsafe subprocess detection, dynamic payload validation, and read-only sandboxes | **P0 (97/100)** | Tier 3 (Enhanced Security Gate & Sandbox Validator) |
| **T** | Autonomous Engineering | Manual scripts and validation tests | OpenHands, Aider patterns | Lack of self-testing autonomous test-repair loops with strict Git/evidence commit gates | **P1 (93/100)** | Tier 3 (Autonomous Verification & Evidence Runner) |

---

## 2. Capability Gap Analysis & Solution Architecture

### 2.1 Category B & P: Data Layer & Analytics Upgrade
- **Current State**: SQLite handles both OLTP operational state and heavy analytical OLAP queries. When running long-range backtests or calculating score ledger calibration curves across 100,000+ rows, SQLite read-locks block background daemons.
- **Identified Gap**: Lack of high-speed columnar analytical storage and vector query execution.
- **Solution Architecture**:
  - Deploy **DuckDB** in-process query engine for all analytical scans, aggregating SQLite tables and Parquet archives directly in memory.
  - Implement zero-copy Apache Arrow data interchange between Python, SQLite, DuckDB, and Polars.
  - Retain SQLite as the bulletproof ACID operational store (Lane-A invariant preserved).

### 2.2 Category E & F: Backtesting & Microstructure Upgrade
- **Current State**: Sequential iteration in `engine/ahos_backtest.py` with static slippage percentages and no out-of-sample validation.
- **Identified Gap**: Susceptibility to look-ahead bias, lack of Walk-Forward Optimization (WFA), absence of Purged/Embargoed Cross-Validation, and unrealistic fill assumptions in thin liquidity pools.
- **Solution Architecture**:
  - Implement a **Hybrid Backtesting Engine**:
    1. *Vectorized Phase (VectorBT pattern)*: Rapidly sweeps hyper-parameter grids over matrix tensors.
    2. *Event-Driven Phase (NautilusTrader/HftBacktest pattern)*: Simulates discrete time events with order queue position degradation, liquidity consumption, fee tiers, and latency jitter.
    3. *Validation Phase (De Prado Quant Pattern)*: Executes Walk-Forward Optimization, Purged K-Fold Cross-Validation, and Combinatorial Embargoed Cross-Validation.

### 2.3 Category G & H: Quantitative Tear-Sheet & Risk Engine
- **Current State**: Basic profit/loss, win rate, and drawdown metrics in `research/baseline_stats.py`.
- **Identified Gap**: Institutional metrics missing: Sharpe ratio (annualized), Sortino ratio (downside deviation), Calmar ratio, Omega ratio, Value at Risk (VaR 95/99%), Conditional Value at Risk (CVaR / Expected Shortfall), and Kelly criterion fractioning.
- **Solution Architecture**:
  - Integrate a **Pure-Python QuantStats & Riskfolio Engine**:
    - Calculates complete statistical tear-sheets for all backtests and paper-trading runs.
    - Implements Ledoit-Wolf covariance matrix shrinkage for robust multi-asset risk parity.

### 2.4 Category K & O: Resilient Local AI Router & Debate Council
- **Current State**: Single Ollama HTTP request that fails outright if Ollama is not running or model times out.
- **Identified Gap**: AI single point of failure; lack of multi-model perspective; JSON hallucination risks.
- **Solution Architecture**:
  - Implement **LiteLLM-Inspired Multi-Tier AI Provider Router**:
    - Tier 1: Local Ollama (e.g. `llama3.2:3b`, `qwen2.5:7b`, `mistral`).
    - Tier 2: Free Cloud / Public Endpoints with rate-limit circuit breakers.
    - Tier 3: Deterministic Rule-Based Heuristic Council (Guaranteed $0 offline fallback).
  - Implement **TradingAgents-Inspired Structured Debate**:
    - Specialist roles: Valuation Analyst, Technical Analyst, On-Chain Analyst, Risk Manager, Bull Researcher, Bear Researcher, Council Arbitrator.
  - Implement **Instructor-Inspired Pydantic Guardrails**:
    - Validates all AI outputs against strict schemas with automatic error feedback retry loops.

### 2.5 Category M & S: MCP Tool Boundary & Sandbox Security
- **Current State**: Internal python function calls without formal interface boundaries.
- **Identified Gap**: No standardized tool interface for external or autonomous engineering agents; risk of unsafe file or network execution.
- **Solution Architecture**:
  - Implement **FastMCP-Compatible Tool Registry**:
    - Clean JSON-RPC tool declarations with typed Pydantic parameters.
    - Read-only sandbox enforcement: tools can inspect data, run backtests, and evaluate scores, but cannot delete files, expose private keys, or initiate real transactions.
