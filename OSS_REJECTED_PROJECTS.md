# AHOS Evaluated and Rejected / Reference-Only Projects Register

In adherence to the **No Feature Bloat** and **License Forensics** principles, AHOS enforces a rigorous selection filter. This document registers all evaluated open-source projects that were **REJECTED** from direct codebase inclusion or classified strictly as **TIER 4 (Reference Only)**, along with comprehensive engineering justifications.

---

## 1. Summary of Evaluated Candidates

```
+-------------------------------------------------------------------------------+
| Total Candidates Evaluated   : 65+ Projects                                   |
| Selected for Top-20 Stack    : 20 Projects (Tiers 1, 2, 3)                    |
| Classified as Reference Only : 18 Projects (Tier 4)                           |
| Strictly Rejected            : 27+ Projects                                   |
+-------------------------------------------------------------------------------+
```

---

## 2. Detailed Register of Rejected & Reference-Only Projects

| # | Project / Repository | Stated License | Primary Domain | Evaluation Verdict | Concrete Technical & Architectural Reason for Rejection / Exclusion |
|---|---|---|---|---|---|
| 1 | **Freqtrade** (`freqtrade/freqtrade`) | **GPL-3.0** | Crypto Trading Bot | **REJECTED (Codebase Ban) / Reference Only (Tier 4)** | **License Taint Risk**: GPL-3.0 license copyleft restrictions pose a severe legal risk of tainting AHOS's permissive architecture. Furthermore, Freqtrade is tightly coupled to real trade execution on centralized exchanges, conflicting with AHOS's observation-first, paper-trading, and intelligence philosophy. Studied solely for dry-run state machine ideas. |
| 2 | **Hummingbot** (`hummingbot/hummingbot`) | Apache-2.0 | Market Making Engine | **REJECTED AS DEPENDENCY / Tier 4 Reference** | **Heavy Weight & Execution Coupling**: Hummingbot requires heavy Cython compilations, active wallet connections, and 2GB+ memory baselines designed for high-frequency CEX/DEX arbitrage bots. Introducing it would cause dependency bloat on consumer Windows laptops. |
| 3 | **Backtrader** (`mementum/backtrader`) | GPL-3.0 / Legacy | Backtesting | **REJECTED** | **Unmaintained & License Risk**: Unmaintained since 2018; pure Python event loops in Backtrader are 50x-100x slower than VectorBT/Polars; lacks native support for modern DEX constant-product liquidity models. |
| 4 | **Jesse** (`jesse-ai/jesse`) | MIT / Custom | Crypto Backtesting | **REJECTED** | **Monolithic Opinionated Framework**: Tight coupling to PostgreSQL and custom frontend GUI; rigid strategy interfaces incompatible with AHOS's modular intelligence pipeline. |
| 5 | **LEAN Engine** (`QuantConnect/Lean`) | Apache-2.0 | Multi-Asset Engine | **REJECTED AS DEPENDENCY / Tier 4 Reference** | **C# / .NET Heavy Ecosystem**: Written in C#/.NET, requiring massive cross-runtime CLR bridges (Python.NET) that degrade performance and complicate single-click Windows laptop installation. Studied solely for cross-validation architectures. |
| 6 | **vLLM** (`vllm-project/vllm`) | Apache-2.0 | High-Throughput LLM Serving | **REJECTED FOR CORE** | **Linux / Heavy GPU Constraint**: vLLM is strictly optimized for Linux datacenter servers with multi-GPU CUDA clusters (Triton/PagedAttention). It does not provide zero-config execution on standard Windows consumer laptops. **Ollama / llama.cpp** is the superior local AI choice for AHOS. |
| 7 | **LangChain Monolith** (`langchain-ai/langchain`) | MIT | LLM Framework | **REJECTED** | **Massive Dependency Bloat & API Churn**: The core LangChain package pulls in dozens of transient dependencies, experiences frequent breaking API changes, and introduces unnecessary abstraction layers. AHOS uses lightweight native Pydantic schemas and FastMCP instead. |
| 8 | **CrewAI** (`joaomdmoura/crewAI`) | MIT | Multi-Agent Framework | **REJECTED** | **High Token Overhead & Prompt Verbosity**: Highly verbose multi-agent prompt loops that quickly exhaust context windows and CPU tokens on small local 3B-7B models without improving financial decision accuracy. |
| 9 | **AutoGen (Full Monolith)** (`microsoft/autogen`) | MIT | Agent Conversational Framework | **REJECTED (Framework) / Pattern Reference Only** | **Heavy Multi-Turn Overhead**: Default conversational loops lead to endless dialogue loops without deterministic convergence. AHOS adopts structured 2-round Bull/Bear debate patterns natively. |
| 10 | **ChromaDB** (`chroma-core/chroma`) | Apache-2.0 | Vector Database | **REJECTED AS CORE DEPENDENCY** | **Heavy Native Build Dependencies**: Requires SQLite version upgrades, Rust/C++ compilation on certain Windows environments, and running background telemetries. Replaced by lightweight zero-dependency DuckDB vector extensions and LanceDB patterns. |
| 11 | **TA-Lib (C-Library Wrapper)** (`mrjbq7/ta-lib`) | BSD | Technical Indicators | **REJECTED AS DEPENDENCY** | **Windows Installation Friction**: Requires pre-compiled C-binaries and MSVC build tools on Windows, causing frequent installation failures for end users (`pip install ta-lib` error: `vcvarsall.bat missing`). Replaced by pure NumPy/Polars vectorized vector calculations. |
| 12 | **CCXT Pro** (`ccxt/ccxt`) | Commercial | Fast WebSocket Feeds | **REJECTED** | **Paid License ($0 Cost Floor Violation)**: Violates the fundamental AHOS rule of 100% free, open-source, and unencumbered deployment. AHOS uses public unauthenticated REST/WebSocket endpoints. |
| 13 | **Etherscan / BscScan Paid Tiers** | Proprietary | Blockchain Explorers | **REJECTED AS MANDATORY** | **API Rate Limits & Key Requirement**: Single point of failure if user lacks paid API key. Retained only as optional fallback; public RPCs and DefiLlama preferred. |
| 14 | **Optuna (Full Distributed Suite)** | MIT | Hyperparameter Optimization | **REJECTED AS CORE / Tier 4 Reference** | **Heavy Optimization Overhead**: Standard grid search and Latin Hypercube sampling in pure NumPy deliver sub-second results for AHOS strategy spaces without pulling in heavy SciPy/Optuna relational database backends. |
| 15 | **Ray / Dask Distributed** | Apache-2.0 | Distributed Computing | **REJECTED** | **Overkill for Standalone Laptop**: Complex cluster orchestration and distributed memory managers designed for cloud clusters. AHOS runs on DuckDB/Polars multithreaded single-node execution. |

---

## 3. Rejection Guidelines & Boundary Rules

To protect the purity, velocity, and reliability of AHOS, any future pull request proposing external libraries must pass the following non-negotiable checklist:

1. **Does it require MSVC C++ compilation on Windows?** $\rightarrow$ If YES, **REJECT**.
2. **Is it licensed under GPL, AGPL, or non-commercial source-available licenses?** $\rightarrow$ If YES, **REJECT**.
3. **Does it require paid API subscriptions to function?** $\rightarrow$ If YES, **REJECT**.
4. **Does it pull in more than 5 transient third-party packages?** $\rightarrow$ If YES, evaluate clean-room native implementation instead.
5. **Does it contain live wallet transaction signing code?** $\rightarrow$ If YES, **REJECT**.
