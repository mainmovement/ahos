# 08 — Cryptocurrency Subsystem Audit

**Phase 8 — the most important document for AHOS as it exists today.**

Every number here was measured from `compression/cryptos.bz2` at commit `a174c97d`
(data generated 2026-09-13), executed 2026-09-15. Scripts: `evidence/scripts/a2_crypto.py`,
`a3_crypto2.py`, `a6_query_engine.py`.

> ## Verdict up front
> FinanceDatabase's cryptocurrency table is a **static, ~2020-era, Yahoo-Finance-convention
> list of 352 token tickers expressed as 3,367 token×quote-currency price pairs**, carrying
> **seven columns of descriptive metadata and nothing else**. It has **no chain, no contract
> address, no price, no market cap, no volume, no liquidity, no holder data, no security data
> and no timestamp**. It cannot support any part of AHOS's crypto opportunity pipeline.
> **Solana does not appear under the ticker `SOL`.**

---

## 8.1 What a "cryptocurrency record" actually is

**Complete schema — all seven columns:**

```
symbol,name,cryptocurrency,currency,summary,exchange,website
AAVE-CAD,Aave CAD,AAVE,CAD,"Aave (AAVE) is a cryptocurrency and operates on the Ethereum platform.",CCC,https://aave.com/
AAVE-CNY,Aave CNY,AAVE,CNY,"Aave (AAVE) is a cryptocurrency and operates on the Ethereum platform.",CCC,https://aave.com/
AAVE-ETH,Aave ETH,AAVE,ETH,"Aave (AAVE) is a cryptocurrency and operates on the Ethereum platform.",CCC,https://aave.com/
```

| Column | Populated | Distinct | Semantics |
|---|---:|---:|---|
| `symbol` | 3,367 / 3,367 | 3,367 | `<TOKEN>-<QUOTE>`. **3,367 of 3,367 contain `-`; zero do not.** This is the Yahoo Finance crypto pair convention |
| `name` | 3,362 | — | `<Token><Quote>` with spaces stripped (`Aave CAD`) |
| `cryptocurrency` | 3,360 | **352** (incl. one empty string) | The token ticker — **the row is not a token, it is a pair** |
| `currency` | 3,360 | 12 | Quote currency |
| `summary` | 3,361 | — | Prose; **the only place chain information exists** |
| `exchange` | 3,362 | 2 | `CCC` for 3,362 rows, empty for 5 |
| `website` | 3,361 | 350 | Project homepage |

**Finding CR-01 — the unit of the table is a price pair, not a token.**
3,367 rows ÷ 352 distinct token tickers = **9.57 rows per token**. A "cryptocurrency" in this
database is *"token T quoted against currency C"*, which is a market-data-shaped concept with
**none of the market data**.

**Quote-currency distribution:**

| Quote | Rows | | Quote | Rows |
|---|---:|---|---|---:|
| USD | 340 | | CNY | 294 |
| EUR | 328 | | CAD | 286 |
| INR | 325 | | BTC | 113 |
| KRW | 324 | | AUD | 66 |
| GBP | 323 | | *(empty)* | 7 |
| JPY | 321 | | | |
| RUB | 321 | | | |
| ETH | 319 | | | |

The presence of `RUB` (321 rows) and the absence of any stablecoin quote beyond `USDT`/`USDC`
as tokens is further evidence of the snapshot's age.

**Finding CR-02 — provenance is `CCC`.** The single non-empty `exchange` value is `CCC`
(3,362 of 3,367 rows), which is the code Yahoo Finance uses for **CryptoCompare**-sourced
cryptocurrency data. Combined with the `<TOKEN>-<QUOTE>` symbol convention and the
`"X (T) is a cryptocurrency and operates on the Y platform."` summary template, the source is
identified with high confidence as a **Yahoo Finance crypto screener export**. Status:
**PARTIALLY_VERIFIED** — the convention and the `CCC` code are measured; no script in the
repository generates this file, and no document states the origin (**UNVERIFIED**, U-04).

## 8.2 Field-by-field capability check

Each row is an explicit existence check against the loaded DataFrame's columns, not an inference.

| Question | Column / capability | Present? | Evidence |
|---|---|---|---|
| What identifiers exist? | `symbol` (pair), `cryptocurrency` (token ticker), `website` | ✓ | schema |
| **Is there chain information?** | `chain`, `network`, `platform` | **✗ ABSENT** | existence check returned `False` for all three |
| **Are there contract addresses?** | `contract`, `address`, `contract_address`, `token_id` | **✗ ABSENT** | `False` for all four |
| Are token symbols used? | `cryptocurrency` | ✓ — but they are **Yahoo-mangled**, not canonical (§8.4) | 26 suffixed tickers |
| Are exchange listings represented? | Only `exchange = 'CCC'`, a **data-source code**, not a venue | ✗ **no CEX/DEX venue information** | value counts: `CCC` 3,362, empty 5 |
| **Are DEX pools represented?** | — | **✗ ABSENT** | no pool, pair-address, factory, router or DEX concept in any of the 7 schemas |
| Is there token metadata? | `name`, `summary`, `website` only. No `decimals`, no `total_supply`, no `logo`, no socials | **Partial — descriptive only** | `decimals` existence check `False` |
| **Are there prices?** | `price` | **✗ ABSENT** | `False` |
| **Is there market cap?** | `market_cap` | **✗ ABSENT** (note: equities have a `market_cap` *bucket*; cryptos have nothing) | `False` |
| **Is there liquidity?** | `liquidity` | **✗ ABSENT** | `False` |
| **Is there volume?** | `volume` | **✗ ABSENT** | `False` |
| **Is there on-chain data?** | holders, transfers, transactions, TVL, mints/burns | **✗ ABSENT** | no such column in any schema |
| **Is there security data?** | mint authority, freeze authority, honeypot, buy/sell tax, LP lock, top-holder concentration | **✗ ABSENT** | no such column |
| Is token identity canonical? | — | **✗ NO** | §8.4, §8.5 |
| Can multiple tokens share symbols? | — | **✓ YES** | 86 of 351 token tickers are also equity symbols (§5.2) |
| Is there historical token state? | `launch_date`, `first_seen`, any timestamp | **✗ ABSENT** | `False`; no time column in any schema |
| Is new-token discovery possible? | — | **✗ NO** | no update job touches `database/cryptos.csv` (§7.1) |
| Are prelaunch tokens covered? | — | **✗ NO** | no temporal concept |
| Are low-liquidity tokens covered? | — | **✗ NO / unknowable** | no liquidity field, and the list is a large-cap-era snapshot |
| Are memecoins covered? | — | **✗ NO** | §8.3 — zero of the probed memecoins are present |
| Is chain-specific discovery possible? | — | **✗ NO** | no chain field; `Cryptos.select()` accepts only `cryptocurrency` and `currency` (`Cryptos.py:27-31`) |

**Chain information exists only as unstructured prose inside `summary`:**

| Keyword in `summary` | Rows |
|---|---:|
| `ethereum` | 606 |
| `tron` | 24 |
| `bnb` | 12 |
| `polygon` | 12 |
| `solana` | **10** |
| `avalanche` | 10 |
| `cardano` | 10 |
| `binance smart chain` | **0** |
| `arbitrum` | **0** |
| `base` | **0** |

Ten rows mention Solana in prose. **Zero** L2s (Arbitrum, Base, Optimism as a chain) are
represented. Extracting chain from free text would require an NLP pass with no ground truth and
no confidence signal — exactly the kind of inference AHOS doctrine forbids presenting as fact.

## 8.3 Coverage probe — measured

We probed 73 token tickers spanning AHOS's actual operating domain. **22 present, 51 absent.**

**PRESENT (22)** — all pre-2021 assets:
`ACT, DOGE, XRP, ETH, ADA, AVAX, LINK, AAVE, MKR, MATIC, ALGO, FIL, VET, HBAR, XLM, ETC, BCH,
LTC, TRX, XMR, ZEC, DASH`

**ABSENT (51)**:

| Category | Absent tickers |
|---|---|
| **Solana ecosystem (all)** | `BONK, WIF, JUP, PYRM, JTO, RAY, ORCA, MNGO, POPCAT, MEW, BOME, SLERF, MYRO, WEN, PNUT, GOAT, GRIFFAIN, CHILLGUY, MICHI, RETARDIO, NEIRO, MOODENG, GIGA, SPORE, GRASS` |
| **Memecoins (all)** | `PEPE, SHIB, DOGE-adjacent new waves, TRUMP, FARTCOIN, MOODENG` |
| **Modern L1/L2** | `SOL`\*, `SUI, APT, SEI, TIA, INJ, HYPE, ARB, OP, NEAR, ICP, DOT`\*, `ATOM`\*, `QNT` |
| **DeFi blue chips** | `UNI`\*, `LDO, ONDO, AAVE`-adjacent new waves |
| **AI/agent tokens (all)** | `AI16Z, VIRTUAL, ZEREBRO, AIXBT, MOCA` |
| **The reference asset itself** | **`BTC`** — absent as a token; present only as a *quote* currency (113 rows) |
| **Collapsed assets still listed** | `SRM` (Serum) is **PRESENT** and **not flagged** — no delisting concept exists for cryptos; `LUNA`\*, `UST`, `FTT` absent |

\* present only under a Yahoo collision suffix (§8.4).

The full 352-ticker list is dominated by dead 2017–2019 altcoins. A representative sample:
`ABBC, ADK, AION, ALIAS, AMB, AMP1, ARDR, ATB, BCN, BIP, BLK, BURST, BCA, BCD, BTT1, CCXX, CLAM,
CNX, COLX, CTXC, DAG, DCN, DIME, DMD, DNA1, DTEP, EDG, EMC2, ETN, ETP, FAIR, FCT, FLASH, FO,
FRST, FTC, GBYTE, GCC1, GHOST, GLEEC, GO, GRN, HNS, HTDF, HTML, HYC, IDNA, ILC, INSTAR, IOC,
IOST, IRIS, JDC, JUL, KRT, LCC, LOKI, LRG, LYNX, MAID, MARO, MASS, MBC, MED, META, MGO, MHC,
MIDAS, MINT, MIOTA, MOAC, MONA, MOON, MRX, NAS, NAV, NEBL, NIM, NLC2, NLG, NMC, NU, NULS, NVT,
NYE, NYZO, OBSR, OMG, OTO, OURO, OWC, PAC, PAI, PART, PCX, PHR, PI, PIVX, PLC, PMEEER, POA,
POLIS, PPC, PPT, PZM, QASH, QRK, QRL, RBTC, RBY, RDD, REP, RINGX, RSTR, SALT, SAPP, SBD, SCC3,
SCP, SERO, SFT, SKY, SLS, SNGLS, SNM, SONO1, SPHR, SRK, SRM, STEEM, STX1, SUB, TAAS, TOMO, TUBE,
TUSD, TWT, UNO, USNBT, VAL1, VBK, VERI, VEX, VGX, VIA, VIN, VITAE, VLX, VSYS, VTC, WABI, WAN,
WAVES, WAXP, WGR, WICC, WINGS, WOZX, WTC, XAS, XBY, XCP, XDN, XHV, XLQ, XLT, XMC, XMY, XNC,
XNS1, XRC, XSN, XUC, XVG, XWC, YEP, YOYOW, ZANO, ZEL, ZNN, ZVC, ZYN`

Status of the crypto dataset: **STALE**, on the order of five to six years.

## 8.4 Finding CR-03 — token tickers are Yahoo collision-suffixed, not canonical

**26 of 352 tickers carry a numeric disambiguation suffix** that belongs to Yahoo's symbol
namespace, not to the token. Measured:

`AMP1, ATOM1, BTC2, BTT1, CMT1, COMP1, CTC1, DNA1, DOT1, EMC2, GCC1, GHOST1, GRT2, HNT1, LUNA1,
MIR1, MTC2, NLC2, ONE2, SCC3, SOL1, SONO1, STX1, UNI3, VAL1, XNS1`

| Ticker in the database | Actual `name` | Actual `summary` | Real-world token |
|---|---|---|---|
| **`SOL1`** | `Solana CAD` | *"Solana (SOL) is a cryptocurrency."* | **Solana — but the ticker is `SOL1`, not `SOL`** |
| `DOT1` | `Polkadot AUD` | *"Polkadot (DOT) is a cryptocurrency."* | Polkadot |
| `UNI3` | `Uniswap CAD` | *"Uniswap (UNI) is a cryptocurrency and operates on the Ethereum platform."* | Uniswap |
| `LUNA1` | `Terra CAD` | *"Terra (LUNA) is a cryptocurrency."* | Terra (pre-collapse) |
| `ATOM1` | `Cosmos CAD` | *"Cosmos (ATOM) is a cryptocurrency."* | Cosmos Hub |
| **`COMP1`** | **`CompoundCoin BTC`** | *"Compound Coin (COMP) is a cryptocurrency…"* | **NOT Compound.** A different, obscure coin |
| `COMP` | `Compound EUR` | *"Compound (COMP) is a cryptocurrency and operates on the Ethereum platform."* | Compound — **only 2 rows** |
| `BTC2` | `Bitcoin2 CAD` | *"Bitcoin 2 (BTC2) is a cryptocurrency."* | A Bitcoin clone, **not** Bitcoin |

**This is the single most dangerous trap in the dataset for an automated consumer.** A naive
lookup table mapping `SOL → Solana` fails; a fuzzy match from `SOL` lands on `SOL1` (correct)
but a fuzzy match from `COMP` or `BTC` can land on `COMP1` (CompoundCoin) or `BTC2` (Bitcoin2)
— **wrong instruments with near-identical tickers**. Executed proof:

```
Cryptos().select(cryptocurrency="SOL")   -> ValueError: The cryptocurrency 'SOL' is not available in the database.
Cryptos().select(cryptocurrency="SOL1")  -> OK, 10 rows, name = ['Solana CAD', 'Solana CNY', …]
Cryptos().select(cryptocurrency="BTC")   -> ValueError: The cryptocurrency 'BTC' is not available in the database.
Cryptos().select(cryptocurrency="ETH")   -> OK, 5 rows
Cryptos().select(cryptocurrency="META")  -> OK, 10 rows, name = ['Metadium CAD', …]   # not Meta Platforms
Cryptos().select(cryptocurrency="Metadium") -> ValueError   # names are not queryable
Cryptos().select(cryptocurrency="sol")   -> ValueError   # exact match after lowercasing the OPTIONS, not fuzzy
```

Note `ETH` has only **5** rows despite `ETH` being the second-most common *quote* currency
(319 rows). The token-side coverage is a small, arbitrary subset of the pair matrix.

## 8.5 Finding CR-04 — token tickers collide with equity symbols at scale

**86 of 351 non-empty crypto token tickers (24.5%) are also equity symbols.** Worked examples:

| Ticker | In `cryptos` | In `equities` |
|---|---|---|
| `META` | **Metadium** — 10 rows (`META-CAD`, `META-CNY`, …) | **Meta Platforms Inc Class A** — `NMS`, United States |
| `GO` | **GoChain** — `GO-CAD`, `GO-CNY`, `GO-ETH` | **Grocery Outlet Holding Corp.** — `NMS`, United States |
| `COMP` | Compound — 2 rows | a listed company |
| `ETH`, `BCH`, `DASH`, `EOS`, `BAND`, `CEL`, `FET`, `FUN`, `GAME`, `ENJ`, `LINK`, `MATIC`, `ACT`, `ADX`, `AR`, `AVA`, `BNT`, `CRU`, `ETN`, `FCT`, `FRST`, `GRC`, `ACH`, `AE`, `AIB`, `ATRI`, `BDX`, `BHP`, `BIP`, `BLK`, `BRC`, `BST`, `BTG`, `BTM`, `BTX`, `CET`, `CHI`, `CNX`, `CPS` … | tokens | listed companies |

The project's own `test_no_symbol_collisions_across_asset_classes` compares **full symbols**
(`META-CAD` vs `META`), so it **cannot detect this class of collision by construction**. Any
AHOS-side join on a bare ticker would silently merge a token with a listed company.

## 8.6 Explicit answers to the tasking's questions

| Question | Answer | Why — exact mechanism |
|---|---|---|
| **Can FinanceDatabase detect a newly launched Solana token?** | **NO** | (1) No update job writes `database/cryptos.csv` — the table is a static snapshot (§7.1). (2) There is no chain field, so "Solana token" is not a queryable concept; `Cryptos.select()` accepts only `cryptocurrency` and `currency`. (3) **`SOL` itself is absent** — Solana exists only as `SOL1`. (4) Zero of 25 probed Solana-ecosystem tokens are present. (5) No `launch_date`/`first_seen`, so "newly launched" is not expressible. |
| **Can it detect a newly created liquidity pool?** | **NO** | No pool concept exists in any of the seven schemas. No `pair_address`, `factory`, `router`, `dex_id`, `tvl` or `liquidity` column anywhere. |
| **Can it verify token sellability?** | **NO** | No security fields, no on-chain state, no simulation capability. Sellability requires a chain RPC call or a simulator; this is a CSV of names. |
| **Can it detect honeypots?** | **NO** | No buy/sell tax, no transfer-restriction, no mint/freeze authority, no blacklist field. |
| **Can it inspect liquidity locks?** | **NO** | No liquidity field, no lock/escrow concept, no LP-token holder data. |
| **Can it detect whale concentration?** | **NO** | No holder data of any kind. AHOS already computes Gini/CV over holder balances in `architecture/intel/forensics.py` from live chain data; FinanceDatabase offers no input to that. |
| **Can it provide real-time DEX order flow?** | **NO** | No time series, no timestamps, no order/trade/swap concept. The library makes no API calls — only two `requests.get` for static files (`helpers.py:65`, `:336`). |
| **Can it provide an evidence-grade opportunity signal?** | **NO** | It contains no observation and no measurement. There is nothing from which a signal could be derived, and no `source_ts` against which evidence could be dated. Under AHOS doctrine it can only ever yield `UNKNOWN`. |

**Do not assume that a cryptocurrency category means on-chain intelligence.** It does not. The
`cryptos` asset class here is a *naming and categorization catalogue* for a small set of
large-cap, mostly-obsolete tokens, expressed in Yahoo Finance's pair-symbol convention.

## 8.7 Comparison with AHOS's existing crypto capability

AHOS already obtains everything FinanceDatabase lacks, from live providers
(`architecture/providers/registry.py`, `README.md`):

| Capability | AHOS today | FinanceDatabase `cryptos` |
|---|---|---|
| Token discovery on a chain | DexScreener, GeckoTerminal, Pump.fun (keyless) | ✗ |
| Contract address / canonical token id | ✓ (`TokenIdentity.address_canonical`, `keccak256`, `resolution.py`) | ✗ |
| Pool identity | ✓ (`PoolIdentity.pair_address`, `pair_id`, `dex_id`, `factory`, `router`) | ✗ |
| Liquidity / volume / price | ✓ (market adapters) | ✗ |
| Security gate | ✓ GoPlus (non-Solana), RugCheck (Solana) | ✗ |
| Holder forensics (Gini, CV, round-number clustering) | ✓ `architecture/intel/forensics.py` | ✗ |
| Freshness (`retrieved_ts`, `source_ts`, `STALE` state) | ✓ `IdentitySource`, `IdentityState` | ✗ |
| Chain coverage incl. Solana | ✓ | ✗ (`SOL` absent) |

**There is no capability that FinanceDatabase's crypto table adds to AHOS.** It is strictly
dominated. The correct decision for the crypto lane is unambiguous: **REJECTED**.

## 8.8 The one narrow thing the crypto table could be used for

Stated honestly, so the rejection is not over-broad:

- As a **historical artefact** — a snapshot of which ~352 tokens Yahoo Finance/CryptoCompare
  considered notable around 2020. Useful for research into *narrative drift* and *asset-class
  survivorship*, never for current decisions.
- As an **adversarial test corpus for identity resolution**: `SOL`/`SOL1`, `COMP`/`COMP1`,
  `BTC`/`BTC2`, `META` (Metadium vs Meta Platforms), `GO` (GoChain vs Grocery Outlet) are
  ready-made collision cases for exercising AHOS's `IdentityState.CONFLICT` / `UNRESOLVED`
  paths **offline, in research, with no provider involvement**.

Both uses are research-only, offline, and require the snapshot to be pinned by git SHA and
bz2 SHA-256 (§14). Neither touches Lane A, scoring, security gates or the runtime.
