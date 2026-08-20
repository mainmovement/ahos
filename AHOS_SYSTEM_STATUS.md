# AHOS — Canonical System Status & Reality Audit Report

**Date of Audit:** 2026-08-19  
**System Identity:** AHOS (Autonomous Hybrid Opportunity System)  
**Repository:** `https://github.com/mainmovement/ahos`  
**Current Branch:** `arena/01a01b0c-ahos` (Pull Request #10)  
**Operating Target:** Windows 11 Laptop (PowerShell 7+, Python 3.11+, SQLite, Offline-First)  

---

## 1. System Identity & Current Architecture

AHOS is an **Event-Driven Autonomous Crypto Opportunity Intelligence System**. It operates strictly in **READ / ANALYZE / SCORE / LEARN / PAPER-TRADE ONLY** mode. It is **NOT** an automated trade-execution bot and contains zero private key signing or real exchange order execution capabilities.

### Topology Overview

```
                                      +------------------------------------+
                                      |         AHOS CONTROL PLANE         |
                                      +------------------------------------+
                                                        |
                    +-----------------------------------+-----------------------------------+
                    |                                   |                                   |
                    v                                   v                                   v
    +------------------------------+    +------------------------------+    +------------------------------+
    |        DATA SUBSYSTEM        |    |    INTELLIGENCE & SCORING    |    |      KNOWLEDGE & MEMORY      |
    | (Public DEX / CEX / Llama)   |    | (Regimes / Drift / Council)  |    | (DuckDB / Ledger / Evidence) |
    +------------------------------+    +------------------------------+    +------------------------------+
                    |                                   |                                   |
                    +-----------------------------------+-----------------------------------+
                                                        |
                                                        v
                                        +------------------------------+
                                        |      QUANT RESEARCH LAB      |
                                        | (VectorBT + Nautilus Sim +   |
                                        |  Purged CV & Monte Carlo)    |
                                        +------------------------------+
                                                        |
                                                        v
                                        +------------------------------+
                                        |      FAST-MCP SANDBOX GATE   |
                                        | (Read-Only Tool Dispatcher)  |
                                        +------------------------------+
```

---

## 2. Current Verified Capabilities

1. **Analytical Data Layer (DuckDB & Columnar Knowledge Store)**:
   - In-process OLAP execution over SQLite tables and Parquet files (`architecture/intel/analytics_bridge.py`, `architecture/knowledge/duck_store.py`).
   - Sub-millisecond aggregation of Brier score calibration bins and hypothesis logs without SQLite write-lock contention.
2. **Institutional Quantitative Risk Engine (QuantStats Pattern)**:
   - Pure-NumPy implementation of Sharpe Ratio (Annualized), Sortino Ratio (Downside), Calmar Ratio, Omega Ratio, Tail Ratio, $VaR_{95/99}$, $CVaR_{95/99}$ (Expected Shortfall), Payoff Ratio, and Kelly Fraction (`research/quant_metrics.py`).
3. **Dual-Mode Hybrid Backtester (VectorBT & Nautilus Patterns)**:
   - Vectorized parameter grid engine evaluating 1,400+ parameter combinations per second (`strategy_lab/vector_engine.py`).
   - Causal discrete-event microstructure simulator modeling constant-product AMM slippage ($x \cdot y = k$) and queue latency delays (`engine/event_backtest.py`).
4. **Purged & Embargoed Cross-Validation (De Prado Methodology)**:
   - Combinatorial Purged K-Fold Cross-Validation (CPCV) with 2% embargo windowing to prevent serial correlation leakage (`strategy_lab/validation_engine.py`).
   - Rolling Walk-Forward Analysis (WFA) with Out-of-Sample (OOS) efficiency calculation and Monte Carlo trade permutation tests.
5. **Multi-Tier AI Provider Router & Adversarial Debate Council**:
   - Tiered model routing: Local Ollama (Primary) $\rightarrow$ Free Cloud $\rightarrow$ Deterministic Heuristic Council (`architecture/ai/router.py`).
   - Multi-role adversarial Bull vs. Bear debate with unilateral **Risk Manager Veto** (`architecture/ai/debate_council.py`).
   - $0/month cost floor: Runs 100% offline with zero required API keys.
6. **Streaming Concept Drift & Market Regime Classifier**:
   - Adaptive Windowing (ADWIN) streaming drift detection (`architecture/learning/drift.py`).
   - 3-State Gaussian Hidden Markov Model (HMM) regime segmentation: Bull Trend, Bear Volatile, Neutral Chop (`architecture/intel/regimes.py`).
7. **FastMCP Tool Registry & Security Sandbox**:
   - Model Context Protocol JSON-RPC schema compliance (`architecture/tools/mcp_registry.py`).
   - Sandboxed read-only security boundary preventing arbitrary shell execution or destructive file operations (`architecture/tools/sandbox.py`).
8. **Autonomous Research Lab Hypothesis Lifecycle**:
   - Automated hypothesis pipeline: Hypothesis $\rightarrow$ Vectorized Sweep $\rightarrow$ Purged CV $\rightarrow$ QuantStats $\rightarrow$ Monte Carlo $\rightarrow$ Acceptance Gating $\rightarrow$ Knowledge Store (`strategy_lab/hypothesis_engine.py`).
9. **Zero-Money Paper Trading & Ledger Safety**:
   - Strict separation between observation/scoring and financial execution. Verified zero real exchange order placement paths.

---

## 3. Verified Test & Import State

- **Pytest Suite:** **1,187 passed** in 152.98s (100% pass rate, 0 failures, 0 errors).
- **Import Validation (`scripts/validate_imports.py`):** **160 modules imported cleanly** in fresh interpreters.
- **Lane-A Scientific Freeze (`config/lane_a_freeze.sha256`):** **36 files verified** with 0 unauthorized drift.
- **Security Audit:** **0** hardcoded API keys/secrets, **0** dangerous `eval()`/`exec()` calls in non-test runtime modules.

---

## 4. Current Runtime & Scheduler State

- **Local Observation Daemon:**
  - Launchable via `python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local`.
  - Windows 11 Launchers: `start_ahos.ps1` and `start_ahos.bat`.
  - Single cycle test: **PASS** (`status: SUCCESS`, structured JSON logs emitted).
- **In-Process Scheduler (`architecture/scheduling/engine.py`):**
  - Drift-compensated min-heap priority scheduler executing periodic discovery, feature extraction, and outcome labeling tasks.

---

## 5. Current AI & Data Provider Status

| Subsystem | Provider | Mode / Tier | Cost | Rate Limit | Authentication | Status |
|---|---|---|---|---|---|---|
| **AI Subsystem** | Ollama Local | Tier 1 (Primary) | $0.00 | Unlimited | None | **OPERATIONAL** |
| **AI Subsystem** | Groq / Gemini | Tier 2 (Cloud Free) | $0.00 | Free Tiers | Optional API Key | **OPERATIONAL** |
| **AI Subsystem** | Deterministic Heuristic | Tier 3 (Floor) | $0.00 | Infinite | None | **OPERATIONAL (Always Available)** |
| **Market Data** | GeckoTerminal | REST Pool API | $0.00 | 30 req/min | None | **OPERATIONAL** |
| **Market Data** | DexScreener | REST Pair API | $0.00 | 60 req/min | None | **OPERATIONAL** |
| **Protocol Fundamentals**| DefiLlama | TVL & Coin API | $0.00 | 120 req/min | None | **OPERATIONAL** |
| **CEX Spot Market** | CoinGecko / Public CEX | REST API | $0.00 | 10-30 req/min | None | **OPERATIONAL** |

---

## 6. Windows, Docker, n8n & Telegram Status

- **Windows Laptop Native Mode (Primary):**
  - **100% Verified**: Virtual environment creation, paths normalization, SQLite database bootstrap, and daemon loop.
  - Path unification: Replaced legacy string literal fallbacks with dynamic `ROOT_DIR` resolution in `strategy_lab/run_lab.py`, `engine/data_audit.py`, `engine/dryrun_simulation.py`, and `engine/run_validation.py`.
- **Docker Desktop Mode (Optional):**
  - `Dockerfile` and `docker-compose.windows.yml` validated and present. Docker is optional and not required for native execution.
- **n8n Automation (Optional):**
  - 6 workflow JSON definitions validated via `tests/validate_n8n.py` (All PASS).
- **Telegram Intelligence Bot:**
  - Persian NLU intent parsing verified for system health and token status. Runs in read-only paper-trading mode.

---

## 7. Current Limitations & Constraints

1. **Calibration Sample Size (Month 1):**  
   The calibration harness returns `INSUFFICIENT_DATA` until the local observation daemon runs for 168+ continuous hours to collect real forward outcomes ($t+1h, t+24h, t+7d$). This is scientifically correct.
2. **Network Filtering in Iran:**  
   External public APIs require SOCKS5 proxy (`ALL_PROXY=socks5://127.0.0.1:10808`) when deployed in restricted networks. Built-in circuit breakers fall back to cached data during outages.

---

## 8. Operational Roadmap & Soak Protocol

1. **Step 1:** Run `.\install_windows.ps1` (or `python scripts/init_databases.py --with-guards`).
2. **Step 2:** Run `.\start_ahos.ps1` to launch the 168-hour continuous observation daemon.
3. **Step 3:** Inspect local logs and health via `python -m architecture.runtime --single-cycle`.
4. **Step 4:** Generate empirical calibration reports after 168 hours via `python scripts/calibration_report.py`.
