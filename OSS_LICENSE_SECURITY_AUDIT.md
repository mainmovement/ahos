# AHOS Open-Source License & Security Forensics Audit

This document details the software license compatibility audit, supply chain security analysis, vulnerability assessments, and boundary guardrails for all candidate open-source technologies evaluated for AHOS.

---

## 1. Open-Source License Forensics

AHOS is an open-source autonomous intelligence system designed for perpetual unrestricted deployment on user hardware. To guarantee zero legal liability, zero copyleft pollution, and zero proprietary lock-in, all external code and dependencies are categorized under strict license compliance tiers.

### 1.1 License Classification Matrix

| License Type | Examples Evaluated | AHOS Compatibility | Policy & Integration Action |
|---|---|---|---|
| **Permissive (Tier 1 / Direct)** | MIT, Apache-2.0, BSD-2/3-Clause, ISC | **100% Compatible** | Approved for direct PyPI dependency (`requirements.txt`), native embedding, or clean-room adaptation. Full attribution retained in `NOTICE.md`. |
| **Weak Copyleft (Tier 3 / Pattern)** | LGPL-3.0, MPL-2.0 (e.g. NautilusTrader) | **Restricted / Pattern Only** | NEVER statically link or bundle raw LGPL source code into core AHOS repository. Extract mathematical formulas and architectural patterns only via clean-room re-implementation. |
| **Strong Copyleft (Tier 4 / Reference)** | GPL-3.0, AGPL-3.0 (e.g. Freqtrade, Jesse) | **Taint Risk / Reference Only** | STRICT BAN on importing or copying any GPL/AGPL source code. Reference solely for design concepts, benchmark baselines, and architectural study. |
| **Non-Commercial / Source-Available** | BSL, CC-BY-NC, PolyForm | **Incompatible / Rejected** | Strictly rejected to preserve perpetual commercial freedom and unencumbered open-source distribution. |

### 1.2 Candidate License Forensic Register

| Candidate Project | Repository | Stated License | License Compatibility | Permitted Usage in AHOS |
|---|---|---|---|---|
| **DuckDB** | `duckdb/duckdb` | MIT | Full Pass | Direct PyPI Dependency (`duckdb>=1.0.0`) |
| **Polars** | `pola-rs/polars` | MIT | Full Pass | Direct PyPI Dependency (`polars>=1.0.0`) |
| **VectorBT** | `polakowo/vectorbt` | Apache-2.0 | Full Pass | Clean-room architectural pattern / algorithm adaptation |
| **NautilusTrader** | `nautechsystems/nautilus_trader` | LGPL-3.0 | Conditional | Pattern reference only; clean-room native implementation |
| **HftBacktest** | `nugraph/hftbacktest` | MIT | Full Pass | Microstructure formula adaptation with attribution |
| **QuantStats** | `ranaroussi/quantstats` | Apache-2.0 | Full Pass | Native mathematical module adaptation with attribution |
| **Riskfolio-Lib** | `dcajasn/Riskfolio-Lib` | BSD-3-Clause | Full Pass | Optimization algorithm adaptation with attribution |
| **River** | `online-ml/river` | BSD-3-Clause | Full Pass | ADWIN drift detector adaptation with attribution |
| **HMMlearn** | `hmmlearn/hmmlearn` | BSD-3-Clause | Full Pass | Dependency or clean-room EM Gaussian HMM module |
| **OpenBB Platform** | `OpenBB-finance/OpenBBTerminal` | Apache-2.0 | Full Pass | Router architecture & schema design adaptation |
| **CCXT** | `ccxt/ccxt` | MIT | Full Pass | REST public market data adapter pattern |
| **DefiLlama Adapters** | `DefiLlama/DefiLlama-Adapters` | MIT | Full Pass | Open REST client & TVL data adapter pattern |
| **GeckoTerminal SDK** | `GeckoTerminal Public API` | MIT / Public | Full Pass | Multi-chain DEX pool analytics adapter |
| **TradingAgents** | `TauricResearch/TradingAgents` | MIT | Full Pass | Multi-agent debate council pattern adaptation |
| **LangGraph** | `langchain-ai/langgraph` | MIT | Full Pass | Cyclic state graph engine clean-room implementation |
| **FastMCP** | `jlowin/fastmcp` | MIT | Full Pass | Model Context Protocol tool schema adaptation |
| **Instructor** | `jxnl/instructor` | MIT | Full Pass | Schema extraction & retry guardrail adaptation |
| **LanceDB** | `lancedb/lancedb` | Apache-2.0 | Full Pass | Embedded vector store architecture adaptation |
| **LiteLLM** | `BerriAI/litellm` | MIT | Full Pass | Multi-tier AI fallback router clean-room implementation |
| **APScheduler** | `agronholm/apscheduler` | MIT | Full Pass | Min-heap drift-compensated scheduling engine adaptation |
| **Freqtrade** | `freqtrade/freqtrade` | GPL-3.0 | Incompatible | **REJECTED FROM CODEBASE** (Architecture reference only) |
| **Hummingbot** | `hummingbot/hummingbot` | Apache-2.0 | Heavy | **REJECTED AS DEPENDENCY** (Studied for order state machine) |

---

## 2. Supply Chain & Code Security Audit

Security in AHOS is non-negotiable. Because AHOS analyzes financial markets and token contracts, it operates in an adversarial environment where malicious smart contracts, untrusted API responses, and poisoned packages are common.

### 2.1 Threat Modeling & Attack Vectors

```
+---------------------------+       +---------------------------+       +---------------------------+
|    THREAT VECTOR 1        |       |    THREAT VECTOR 2        |       |    THREAT VECTOR 3        |
|  Supply Chain Poisoning   |       |  Malicious API Payloads   |       |  Unsafe Subprocess / Exec |
| (Malicious PyPI packages) |       | (Exploit unvalidated JSON)|       | (Arbitrary command inject)|
+---------------------------+       +---------------------------+       +---------------------------+
              |                                   |                                   |
              v                                   v                                   v
+---------------------------+       +---------------------------+       +---------------------------+
|    DEFENSE MECHANISM      |       |    DEFENSE MECHANISM      |       |    DEFENSE MECHANISM      |
| Pin SHA-256 dependencies, |       | Strict Pydantic schemas,  |       | Zero shell=True,          |
| minimal dependency tree,  |       | boundary sanitizer,       |       | read-only sandboxes,      |
| zero compiled C binaries. |       | typed data converters.    |       | AST code hygiene scanner. |
+---------------------------+       +---------------------------+       +---------------------------+
```

### 2.2 Security Audits by Category

#### A. Deserialization & Memory Safety
- **Risk**: Python's `pickle`, `yaml.unsafe_load`, and unvalidated `eval()` can execute arbitrary code upon deserializing untrusted state files or model weights.
- **AHOS Enforcement**:
  - **Zero Pickle Policy**: `pickle.load()` is strictly prohibited across the entire repository.
  - Safe Serialization: All state, evidence, and configuration files must use `json.loads()`, `yaml.safe_load()`, or native `DuckDB/Parquet/SQLite` tables.
  - AST Scanner: `scripts/validate_imports.py` and `architecture/security/hygiene.py` scan the entire codebase to guarantee zero `eval()`, `exec()`, or `pickle` calls.

#### B. Subprocess & Shell Execution Safety
- **Risk**: Unsanitized parameters passed to `subprocess.Popen(..., shell=True)` can lead to remote code execution (RCE).
- **AHOS Enforcement**:
  - `shell=True` is strictly forbidden in runtime modules.
  - Any necessary sub-command execution must use argument lists (`['git', 'status']`) with strict timeouts and path validation.

#### C. Credential & Private Key Isolation
- **Risk**: Financial bots often leak private keys, exchange API secrets, or seed phrases through crash logs or error reports.
- **AHOS Enforcement**:
  - **Zero Real Wallet Execution**: AHOS core contains NO private key generation, NO wallet signing, and NO live CEX/DEX trade execution endpoints.
  - Secret Pattern Scanner: Non-test source files are automatically scanned during every CI and local validation run for private key patterns, AWS keys, Telegram tokens, and exchange secrets.
  - Environment Isolation: All optional API keys (e.g. Etherscan, CoinGecko Pro) are loaded exclusively via local environment variables (`.env`) and never printed in logs or exception traces.

#### D. Network Resilience & Rate Limit Shielding
- **Risk**: Distributed denial of service (DDoS) blocks, IP blacklisting, or Iran internet filtering disrupting market data collectors.
- **AHOS Enforcement**:
  - Circuit Breakers: Exponential backoff with jitter and circuit breakers on all external HTTP requests (`architecture/collector/circuit_breaker.py`).
  - SOCKS5 Proxy Support: Universal `ALL_PROXY=socks5://127.0.0.1:10808` proxy support for environments under severe network filtering.
  - Offline Mock Mode: Every data provider and AI council module has an offline deterministic mock mode to ensure 100% offline unit and integration test execution.

---

## 3. Verification Protocol

1. Run `python scripts/validate_imports.py` before every commit to enforce:
   - Secret-free source files.
   - Clean imports without cyclic dependencies.
   - Lane-A SHA-256 invariant pinning.
   - Zero uncommitted cache artifacts.
2. Run automated test suite with timeout limits: `pytest --timeout=60`.
