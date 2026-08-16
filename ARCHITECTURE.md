# AHOS System Architecture Specification

## 1. Architectural Principles
- **Dual-Lane Modularity:**
  - **Lane A (Runtime Intelligence):** Real-time opportunity collector, deterministic scorer, alert engine, paper trading manager, and Telegram interface.
  - **Lane B (Development Intelligence):** Offline research lab, 10 expert lens data cards, K-04 OSS pipeline, multi-mind council, and controlled self-evolution.
- **Deterministic Floor:** System operates completely without AI API keys at $0 cost ceiling.
- **Fail-Closed & Circuit Breaker:** Triple-state circuit breakers protect all external provider calls.

## 2. End-to-End Pipeline
```
[Market Data Providers] (DexScreener, GeckoTerminal, GoPlus, RugCheck)
           │
           ▼
[Collector Engine] ──> (Circuit Breakers & Exponential Retry)
           │
           ▼
[Candidate Normalization] (Strict UNKNOWN Preservation)
           │
           ▼
[Opportunity Scoring Engine] (8-Stage Pipeline: DATA -> SIGNALS -> EVIDENCE -> FEATURES -> RISK -> OPP -> CONFIDENCE -> INVALIDATION)
           │
           ├────────────────────────────┐
           ▼                            ▼
[Deterministic Alert Engine]   [Telegram Domain Service]
  (WHY-Law Mandated)             (Persian NLU & Section X Cards)
           │                            │
           ▼                            ▼
[User Telegram Alerts]         [Persian Opportunity Cards]
```

## 3. Storage Architecture
1. `data/e01_discovery.sqlite`: Discovered pairs, token metadata, raw payloads, snapshot observations, gap register.
2. `data/paper_trading.sqlite`: Event-sourced paper trades, position decisions, realizable PnL, post-trade lessons.
3. `data/ahos_local.sqlite`: Scheduler runs, atomic lease locks, heartbeats, operational metrics.
4. `data/ahos_knowledge.sqlite`: Versioned knowledge claims, evidence links, contradiction graphs.
