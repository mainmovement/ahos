# AHOS Comprehensive Data Provider & Market Intelligence Map

This document establishes the official data provider architecture for AHOS, specifying zero-cost public endpoints, rate-limiting budgets, failure states, fallback matrices, provenance tracking, and censorship-resilient proxy configurations.

---

## 1. Zero-Cost Data Provider Topology

```
                                  +-------------------------------+
                                  |     AHOS DATA ROUTER V2       |
                                  +-------------------------------+
                                                  |
         +--------------------+-------------------+--------------------+--------------------+
         |                    |                   |                    |                    |
         v                    v                   v                    v                    v
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
|   DEX POOLS &   |  |   CEX PUBLIC    | |   ON-CHAIN &    |  |  MACRO ECONOMIC |  | SOCIAL & NEWS   |
|   LIQUIDITY     |  |   MARKET DATA   | | PROTOCOL FUNDAM.|  |   INTELLIGENCE  |  |   SENTIMENT     |
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
| - GeckoTerminal |  | - Binance Pub   | | - DefiLlama     |  | - Yahoo Finance |  | - CryptoPanic   |
| - DexScreener   |  | - Bybit Pub     | | - Public EVM RPC|  | - FRED Open API |  | - Reddit Public |
| - Raydium Pools |  | - CoinGecko     | | - Solana RPC    |  | - CoinMarketCap |  | - GitHub Open   |
| - Uniswap Pools |  | - CoinCap Open  | | - Blockchair    |  |   Free Public   |  |   Commit Feeds  |
+-----------------+  +-----------------+ +-----------------+  +-----------------+  +-----------------+
```

---

## 2. Exhaustive Data Provider Specifications

| # | Provider Name | Category | Primary Endpoints / Methods | Authentication | Free Tier Rate Limit | Failure State & Fallback Target | Provenance Key |
|---|---|---|---|---|---|---|---|
| 1 | **GeckoTerminal** | DEX Pools | `/api/v2/networks/{network}/pools/{pool_address}`, `/tokens/{token}` | None (Public) | 30 req / min | Circuit breaker open $\rightarrow$ Fallback to DexScreener | `geckoterminal:dex:pool` |
| 2 | **DexScreener** | DEX Pairs | `https://api.dexscreener.com/latest/dex/tokens/{address}` | None (Public) | 60 req / min | Circuit breaker open $\rightarrow$ Fallback to GeckoTerminal | `dexscreener:pair:token` |
| 3 | **DefiLlama Core** | Protocol TVL | `https://api.llama.fi/protocols`, `https://api.llama.fi/summary/dexs` | None (Public) | 120 req / min | Rate limit 429 $\rightarrow$ Cache replay / CoinGecko | `defillama:protocol:tvl` |
| 4 | **DefiLlama Coins** | Token Prices | `https://coins.llama.fi/prices/current/{chain}:{address}` | None (Public) | 120 req / min | Timeout $\rightarrow$ Fallback to DexScreener / CoinGecko | `defillama:token:price` |
| 5 | **CoinGecko Open** | Spot CEX/DEX | `https://api.coingecko.com/api/v3/simple/price`, `/coins/markets` | None (Demo Key opt) | 10-30 req / min | HTTP 429 $\rightarrow$ Fallback to CoinCap / Binance Pub | `coingecko:spot:price` |
| 6 | **CoinCap Public** | Spot Tickers | `https://api.coincap.io/v2/assets`, `/rates` | None (Public) | 100 req / min | HTTP 500 $\rightarrow$ Fallback to Binance Public REST | `coincap:market:assets` |
| 7 | **Binance Public** | CEX Ticker | `https://api.binance.com/api/v3/ticker/24hr`, `/api/v3/klines` | None (Public) | 1200 weight/min | IP Block $\rightarrow$ Route via SOCKS5 proxy / Bybit Pub | `binance:cex:ticker` |
| 8 | **Bybit Public** | CEX Ticker | `https://api.bybit.com/v5/market/tickers`, `/kline` | None (Public) | 120 req / min | Timeout $\rightarrow$ Fallback to OKX / Binance Public | `bybit:cex:ticker` |
| 9 | **Public EVM RPC** | Blockchain RPC | `eth_blockNumber`, `eth_call`, `eth_getBalance` | None (Public nodes) | 25 req / sec (shared)| Node error $\rightarrow$ Round-robin fallback to Ankr/Cloudflare | `evm:rpc:state` |
| 10 | **Public Solana RPC** | Solana Chain | `getLatestBlockhash`, `getTokenAccountBalance` | None (Public nodes) | 10 req / sec | 429 $\rightarrow$ Fallback to public backup nodes | `solana:rpc:state` |
| 11 | **Yahoo Finance** | Macro Indices | `https://query1.finance.yahoo.com/v8/finance/chart/{symbol}` | None (Public) | 60 req / min | User-Agent block $\rightarrow$ Rotation / FRED Open API | `yfinance:macro:chart` |
| 12 | **FRED Open API** | Macro Rates | `https://api.stlouisfed.org/fred/series/observations` | Free API Key | 120 req / min | Key missing $\rightarrow$ Fallback to static macro presets | `fred:macro:rates` |
| 13 | **CryptoPanic RSS** | News & Sentiment | `https://cryptopanic.com/news/rss/` | None (Public RSS) | 30 req / min | Network filter $\rightarrow$ Route via SOCKS5 / Reddit RSS | `cryptopanic:news:rss` |
| 14 | **Reddit Public RSS** | Social Sentiment | `https://www.reddit.com/r/cryptocurrency/hot.json` | None (Custom UA) | 30 req / min | HTTP 429 $\rightarrow$ Fallback to GitHub commit tracker | `reddit:social:sentiment` |
| 15 | **GitHub Public API**| Developer Acts | `https://api.github.com/repos/{owner}/{repo}/commits` | None (Unauth 60/hr)| 60 req / hr | Rate limit $\rightarrow$ Fallback to cached developer score | `github:dev:activity` |

---

## 3. Data Integrity & Provenance Contract

Every data packet ingested into AHOS must be wrapped in a typed `DataEnvelope` containing mandatory audit metadata before it can be consumed by any feature extractor or intelligence agent.

```json
{
  "provenance": {
    "provider_id": "defillama:protocol:tvl",
    "endpoint": "https://api.llama.fi/protocols",
    "fetched_at_utc": "2026-08-19T17:30:00.000Z",
    "latency_ms": 142.5,
    "confidence_score": 0.98,
    "freshness_sec": 12.0,
    "is_cached": false,
    "sha256_payload": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "payload": {
    "protocol": "uniswap",
    "tvl_usd": 5420000000.0,
    "chain_tvls": {
      "Ethereum": 4100000000.0,
      "Arbitrum": 680000000.0,
      "Polygon": 320000000.0
    }
  }
}
```

### 3.1 Confidence Scoring Formulation
The confidence score $C \in [0.0, 1.0]$ is dynamically computed as:
$$C = C_{base} \times (1 - \lambda \cdot \Delta t) \times (1 - P_{failure})$$
Where:
- $C_{base}$: Inherent source trust level (e.g. On-Chain RPC = 1.0, Public DEX = 0.95, Social RSS = 0.60).
- $\lambda$: Half-life decay factor per second of staleness.
- $\Delta t$: Age of data in seconds since recorded exchange timestamp.
- $P_{failure}$: Historical rolling 24-hour error rate of the provider.

---

## 4. Iran-Resilience & Proxy Routing Architecture

Due to strict regional internet censorship and selective API IP blocks, AHOS incorporates automatic SOCKS5 proxy routing:
- **Default Behavior**: Direct HTTPS connection.
- **Trigger**: 2 consecutive connection resets (`ECONNRESET`) or timeouts (`ETIMEDOUT`).
- **Action**: Seamlessly routes requests through the local proxy environment variable:
  ```bash
  ALL_PROXY=socks5://127.0.0.1:10808
  HTTPS_PROXY=http://127.0.0.1:10809
  ```
- **Fallback**: If proxy is unreachable, data router switches to local cached snapshots to ensure zero daemon crashes.
