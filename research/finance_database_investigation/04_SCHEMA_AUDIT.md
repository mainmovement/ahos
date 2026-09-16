# 04 — Complete Schema Audit

**Phase 4.** Every number below was **measured** from `compression/*.bz2` at commit
`a174c97d3bba96fc1a82b2e1068fb3ec5e02e634` (data generated 2026-09-13), read on 2026-09-15
with `pandas 3.0.5` using `dtype=str, keep_default_na=False` so that "empty" means a genuinely
empty cell rather than a pandas-inferred NaN. Raw output: `evidence/schema_audit.json`.

**Reproducibility note:** read the same files the way the *library* does
(`pd.read_csv(..., index_col=0)`, no dtype coercion) and `symbol` becomes the DataFrame index,
so `df.columns` reports one fewer field than the CSV header. Both views are given.

---

## 4.0 Cross-asset summary

| Asset class | File | bz2 size | Rows | CSV fields | Columns after `index_col=0` | Identifier columns | `delisted` | Any time/provenance column |
|---|---|---:|---:|---:|---:|---|---|---|
| Equities | `equities.bz2` | 15.29 MB | **112,690** | 22 | 21 | `isin, cusip, figi, composite_figi, shareclass_figi` | **Yes** | **NONE** |
| Indices | `indices.bz2` | 1.19 MB | **91,181** | 8 | 7 | none | No | **NONE** |
| Funds | `funds.bz2` | 1.85 MB | **57,853** | 9 | 8 | none | No | **NONE** |
| ETFs | `etfs.bz2` | 1.28 MB | **36,481** | 10 | 9 | `isin` | No | **NONE** |
| Cryptocurrencies | `cryptos.bz2` | 0.03 MB | **3,367** | 7 | 6 | none | No | **NONE** |
| Currencies | `currencies.bz2` | 0.05 MB | **2,556** | 6 | 5 | none | No | **NONE** |
| Money Markets | `moneymarkets.bz2` | 0.02 MB | **1,367** | 6 | 5 | none | No | **NONE** |
| **Total** | | **21.6 MB** | **304,495** | | | | | |

**Finding SC-01 — no timestamp, freshness, provenance, version or source column exists in any
of the seven schemas.** Verified by scanning every column name for
`date|time|updated|asof|as_of|timestamp|snapshot|version|source|provider|retrieved`:

```
equities      time/provenance columns: NONE
etfs          time/provenance columns: NONE
funds         time/provenance columns: NONE
indices       time/provenance columns: NONE
currencies    time/provenance columns: NONE
cryptos       time/provenance columns: NONE
moneymarkets  time/provenance columns: NONE
```

For AHOS this is disqualifying on its own for any decision path: there is **no per-record
`source_ts` or `retrieved_ts`** to compare against a staleness threshold. AHOS's
`IdentitySource` dataclass (`architecture/identity/types.py`) carries both `retrieved_ts` and
`source_ts` and has a `STALE` state; FinanceDatabase cannot populate either. Freshness is
knowable **only** at file granularity, from the git commit date of the artifact.

**Finding SC-02 — all values are text.** The bz2 files are written with `dtype=str,
keep_default_na=False` and no type annotations. On read the library obtains `str` for every
column except `delisted`, which pandas infers as `bool` (`test_invariants.py:125-140` guards
this explicitly). There is no numeric column anywhere: no price, no volume, no market cap
*value*, no share count, no ratio. `zipcode` and `cusip` are deliberately kept as text — the
workflow comment at `:198-201` records that pandas previously mangled them (`"9763" → "9763.0"`,
`"031162100" → "31162100.0"`).

**Finding SC-03 — duplicate symbols: zero in all seven asset classes.** Measured
`duplicated().sum()` on the symbol column: `0` for equities, etfs, funds, indices, currencies,
cryptos, moneymarkets. Uniqueness *within* an asset class holds at HEAD. This is a direct
consequence of the pipeline's global `keep='first'` dedupe (§3.4.3). **Cross-asset** uniqueness
does *not* hold — `CHAD` exists in both equities and ETFs (§5.2).

---

## 4.1 Equities — `equities.bz2`, 112,690 rows

**Header (verbatim):**
```
symbol,name,summary,currency,sector,industry_group,industry,exchange,mic,market,country,state,city,zipcode,website,market_cap,isin,cusip,figi,composite_figi,shareclass_figi,delisted
```

**First data row (verbatim, truncated summary):**
```
000002.SZ,"China Vanke Co., Ltd.","China Vanke Co., Ltd., together with its subsidiaries, engages in the development and sale of properties in the Mainland China…",CNY,Real Estate,Real Estate,Real Estate Management & Development,SHZ,XSHE,Shenzhen Stock Exchange,China,,Shenzhen,518083,http://www.vanke.com,Large Cap,CNE100001SR9,,,BBG006KY4KD6,BBG006KY4KG3,False
```

| # | Column | Type (as read) | Role | Empty | Empty % | Example values | Notes |
|---:|---|---|---|---:|---:|---|---|
| 0 | `symbol` | str (→ **index**) | Listing identifier | 1\* | 0.00% | `000002.SZ`, `PAYX`, `MMM.DE`, `BRK-A` | \*the single "empty" is the `NA`/NaN artifact of [R240] read semantics (§3.4.4). Yahoo-style: bare for US, `<local>.<exchange-suffix>` elsewhere |
| 1 | `name` | str | Issuer/security label | 1,116 | 0.99% | `3M Company`, `Meta Platforms Inc Class A` | Free text. 1,774 values have trailing whitespace; 47,578 lowercase-duplicates; 129 rows are literally `two` |
| 2 | `summary` | str | Prose description | 12,227 | 10.85% | multi-sentence business description | Provenance undocumented; style matches Yahoo Finance profiles. **UNVERIFIED** origin (U-04) |
| 3 | `currency` | str | Trading currency | 2,137 | 1.90% | `EUR` (47,107), `USD` (26,490), `INR` (5,700) | **Contains `ILA` (560 rows) which is not ISO 4217; `ILS` appears once.** Non-standard code, internally inconsistent |
| 4 | `sector` | str | GICS-approximating level 1 | 9,222 | 8.18% | 11 distinct values | See §4.8 |
| 5 | `industry_group` | str | level 2 | 9,501 | 8.43% | 24 distinct | |
| 6 | `industry` | str | level 3 | 40,045 | **35.54%** | 80 distinct | Largest classification gap |
| 7 | `exchange` | str | Venue code | 484 | 0.43% | 84 distinct: `NMS`, `NYQ`, `PNK`, `FRA`, `STU`, `BER`, `SHZ`, `VIE`… | Not an ISO code; project-local. 8,186 rows carry hardcoded values (§3.4.1) |
| 8 | `mic` | str | ISO 10383 MIC | 831 | 0.74% | 71 distinct: `XNYS`, `XNAS`, `XSHE`, `XETR`, `XBER` | `exchange → mic` is 1:1 (0 violations); `mic → exchange` has **4 violations** (`OTCM`→7 codes, `XNAS`→3, `XLON`→2, `XNSE`→2). 3 exchange codes have no MIC |
| 9 | `market` | str | Venue long name | 774 | 0.69% | `New York Stock Exchange`, `XETRA`, `Shenzhen Stock Exchange` | **Semantics inconsistent**: for `NMS`/`ASE` it is a hardcoded market tier; for `SHZ` it is the exchange name |
| 10 | `country` | str | **Issuer/HQ country** | 6,605 | 5.86% | 114 (non-delisted) / 117 (all) | **Not the listing jurisdiction.** 19,413 of 29,984 `United States` rows trade on non-US venues (`FRA` 2,953, `STU` 2,516, `BER` 2,083, `MUN` 1,804, `DUS` 1,114). Confirmed by the workflow comment at `:506-507`. 14 `.SZ` (Shenzhen) rows are labelled `United States` |
| 11 | `state` | str | HQ state/region | 80,725 | **71.63%** | `MA`, `TX`, `NY` | US-centric; mostly empty |
| 12 | `city` | str | HQ city | 43,030 | 38.18% | `Boston`, `Shenzhen` | |
| 13 | `zipcode` | str | HQ postal code | 48,749 | 43.26% | `2210`, `14625-2396` | **Text by design**; previously corrupted to `9763.0` (§3.4.4) |
| 14 | `website` | str | Issuer URL | 46,132 | 40.94% | `http://www.ptc.com` | `http://` scheme, not `https://` |
| 15 | `market_cap` | str | **Derived ordinal bucket** | 36,362 | **32.27%** | `Mega Cap` (641) … `Nano Cap` (22,774) | Not a value. USD thresholds. Never refreshed after first sight (§3.4.2 DP-03) |
| 16 | `isin` | str | ISO 6166 | 82,261 | **73.00%** | `US69370C1009` | Populated for 30,429 rows; only **9,406 unique** ⇒ 21,023 duplicate values |
| 17 | `cusip` | str | CUSIP (ABA/S&P trademark) | 85,404 | **75.79%** | `69370C100` | 27,286 populated; 12,946 unique ⇒ 14,340 dups |
| 18 | `figi` | str | Bloomberg unique FIGI | 54,134 | **48.04%** | `BBG000FC6SC5` | 58,556 populated; **58,232 unique** ⇒ only 324 dups — the best listing-level key present |
| 19 | `composite_figi` | str | Bloomberg composite FIGI | 51,798 | 45.97% | `BBG000FC5PS5` | 60,892 populated; 41,131 unique ⇒ 19,761 dups (**correct** semantics: one per security across listings) |
| 20 | `shareclass_figi` | str | Bloomberg share-class FIGI | 48,700 | 43.22% | `BBG001S6DNK6` | 63,990 populated; 29,164 unique ⇒ 34,826 dups (**correct** semantics: one per share class) |
| 21 | `delisted` | **bool** | Survival flag | 0 | 0.00% | `False` 102,286 · `True` 10,404 | Guarded by `test_delisted_is_strictly_boolean`. Only asset class that has it — open issue **#153** asks for ETFs/Funds |

**Identifier completeness, ranked:** `shareclass_figi` 56.8% > `composite_figi` 54.0% > `figi`
52.0% > `isin` 27.0% > `cusip` 24.2%.

## 4.2 ETFs — `etfs.bz2`, 36,481 rows

```
symbol,name,currency,summary,category_group,category,family,exchange,mic,isin
003D.BE,WISDOMTREE EURO HGD EQ.FD,EUR,"The WisdomTree Euro Hedged Equity Fund aims to provide exposure to European equities while hedging…",Financials,Developed Markets,WisdomTree Asset Management,BER,XBER,
```

| Column | Empty | Empty % | Notes |
|---|---:|---:|---|
| `symbol` | 0 | 0.00% | 92.3% contain a `.` → `only_primary_listing=True` discards almost the whole class |
| `name` | 8 | 0.02% | |
| `currency` | 103 | 0.28% | |
| `summary` | 7,694 | 21.09% | |
| `category_group` | 11,048 | **30.28%** | 313 distinct families / 44 categories per README |
| `category` | 13,735 | **37.65%** | |
| `family` | 9,295 | 25.48% | Issuer/provider — free text |
| `exchange` | 31 | 0.08% | 51 distinct |
| `mic` | 83 | 0.23% | |
| `isin` | 28,549 | **78.26%** | The **only** identifier column; populated for 21.7% |

**Absent vs equities:** no `country`, no `sector`/`industry`, no `market`, no `market_cap`, no
CUSIP, no FIGI family, **no `delisted`** (issue #153). The official website's "295 Sectors ·
22 Industries" for ETFs describes columns that **do not exist** (§1.4).

## 4.3 Funds — `funds.bz2`, 57,853 rows

```
symbol,name,currency,summary,category_group,category,family,exchange,mic
0GKA.SG,Börslich handelbare Krügerrand,EUR,"The exchange-traded Krugerrand (1oz) Gold Bond is a financial product…",Commodities,Commodities Broad Basket,,STU,XSTU
```

| Column | Empty | Empty % |
|---|---:|---:|
| `symbol` | 0 | 0.00% (45.7% dotted) |
| `name` | 1,416 | 2.45% |
| `currency` | 253 | 0.44% |
| `summary` | 9,734 | 16.83% |
| `category_group` | 4,991 | 8.63% |
| `category` | 7,298 | 12.61% |
| `family` | 21,075 | **36.43%** |
| `exchange` | 244 | 0.42% (33 distinct) |
| `mic` | 31,680 | **54.76%** |

**No identifier column at all.** `conftest.py:38-45` lists `manager_name` / `manager_bio` in the
funds skip-set, implying those columns existed or were planned; they are **absent** from the
current schema — a small fixture/schema drift.

## 4.4 Indices — `indices.bz2`, 91,181 rows

```
symbol,name,currency,summary,category_group,category,exchange,mic
000008.SS,SSE Conglomerates Index,CNY,"The SSE Conglomerates Index aims to reflect the overall performance of companies listed on the Shanghai Stock Exchange…",Equities,Equities,SHH,XSHG
```

| Column | Empty | Empty % |
|---|---:|---:|
| `symbol` | 0 | 0.00% (31.9% dotted) |
| `name` | 15,677 | **17.19%** |
| `currency` | 17,211 | **18.88%** |
| `summary` | 48,391 | **53.07%** |
| `category_group` | 18,594 | 20.39% |
| `category` | 22,544 | 24.72% |
| `exchange` | 4,854 | 5.32% (63 distinct) |
| `mic` | 54,526 | **59.80%** |

The largest class by row count and the sparsest by content: over half the rows have no
description, one in six has no name. No identifier column. `Indices.select()` has **no**
`only_primary_listing` parameter — correct, since the dot heuristic is meaningless for indices.

## 4.5 Currencies — `currencies.bz2`, 2,556 rows

```
symbol,name,base_currency,quote_currency,summary,exchange
AED=X,USD/AED,USD,AED,"The exchange rate between the United States Dollar (USD) and the United Arab Emirates Dirham (AED)…",CCY
```

| Column | Empty | Empty % | Notes |
|---|---:|---:|---|
| `symbol` | 0 | 0.00% | Yahoo FX convention `BASEQUOTE=X`; 0% dotted |
| `name` | 0 | 0.00% | **`AED=X` is named `USD/AED`** — the name does not match the symbol's base currency. Semantic inconsistency in the very first row |
| `base_currency` | 0 | 0.00% | |
| `quote_currency` | 0 | 0.00% | 175 distinct |
| `summary` | 499 | 19.52% | |
| `exchange` | 0 | 0.00% | Constant `CCY` |

The **most complete** schema — and the only one where every field is populated. It is also the
only one with a genuine two-sided key (`base_currency`/`quote_currency`), which is why
`Currencies.select()` takes those two parameters rather than a single `currency`.

## 4.6 Cryptocurrencies — `cryptos.bz2`, 3,367 rows

```
symbol,name,cryptocurrency,currency,summary,exchange,website
AAVE-CAD,Aave CAD,AAVE,CAD,"Aave (AAVE) is a cryptocurrency and operates on the Ethereum platform.",CCC,https://aave.com/
```

| Column | Empty | Empty % | Notes |
|---|---:|---:|---|
| `symbol` | 0 | 0.00% | **3,367 of 3,367 contain `-`; 0 do not.** Format `<TOKEN>-<QUOTE>` |
| `name` | 5 | 0.15% | `<Token> <Quote>` concatenation, spaces stripped (`Aave CAD`) |
| `cryptocurrency` | 7 | 0.21% | **352 distinct** (incl. one empty string) ⇒ 3,367 / 352 = **9.57 rows per token** |
| `currency` | 7 | 0.21% | Quote: `USD` 340, `EUR` 328, `INR` 325, `KRW` 324, `GBP` 323, `JPY` 321, `RUB` 321, `ETH` 319, `CNY` 294, `CAD` 286, `BTC` 113, `AUD` 66, empty 7 |
| `summary` | 6 | 0.18% | **The only place chain information exists**, as prose |
| `exchange` | 5 | 0.15% | `CCC` for 3,362 rows — the CryptoCompare code used by Yahoo Finance. This is the *only* provenance signal in the entire schema |
| `website` | 6 | 0.18% | 350 distinct |

**Finding SC-04 — a "cryptocurrency record" is a token×quote-currency *price pair*, not a
token.** The unit of the table is the Yahoo Finance crypto pair symbol. There is no row that
represents "Solana" as an entity; there are ten rows representing `SOL1-<quote>`.

**Columns verified ABSENT** (explicit existence check, all `False`): `chain`, `network`,
`contract`, `address`, `contract_address`, `platform`, `token_id`, `decimals`, `launch_date`,
`first_seen`, `market_cap`, `price`, `volume`, `liquidity`.

Full analysis in [`08_CRYPTOCURRENCY_COVERAGE.md`](08_CRYPTOCURRENCY_COVERAGE.md).

## 4.7 Money Markets — `moneymarkets.bz2`, 1,367 rows

```
symbol,name,currency,summary,family,exchange
AABXX,SEI Daily Income Trust Government Fund,USD,"SEI Daily Income Trust Government Fund is a money market fund that invests primarily in U.S. government securities…",,NAS
AAFXX,American Funds U.S. Government ,USD,"American Funds U.S. Government is a money market fund offered by American Funds…",,NAS
```

| Column | Empty | Empty % |
|---|---:|---:|
| `symbol` | 3 dotted (0.2%) | 0.00% |
| `name` | 158 | **11.56%** |
| `currency` | 3 | 0.22% |
| `summary` | 676 | **49.45%** |
| `family` | 541 | **39.58%** |
| `exchange` | 1 | 0.07% (2 distinct) |

US money-market funds (`XXXXX` five-character convention). Half have no description; two-fifths
have no family. Row 2 shows `name` = `"American Funds U.S. Government "` — **trailing
whitespace in a name field**. No identifier column.

## 4.8 The classification taxonomy (measured)

`Equities.show_options()` returns a dict of nine keys. Measured cardinalities from live data:

| Dimension | Distinct values (non-delisted rows) | Distinct (all rows, via `fd.show_options`) |
|---|---:|---:|
| `sector` | 11 | 11 |
| `industry_group` | 24 | 24 |
| `industry` | 80 | 80 |
| `country` | **114** | **117** |
| `currency` | 37 | 37 |
| `exchange` | 84 | 84 |
| `mic` | 71 | 71 |
| `market` | — | — |
| `market_cap` | 6 | 6 |

The 11 sectors are the GICS sectors: `Communication Services, Consumer Discretionary, Consumer
Staples, Energy, Financials, Health Care, Industrials, Information Technology, Materials, Real
Estate, Utilities` (verbatim from the official page's `show_options` sample and consistent with
11 measured).

**Real GICS** has 11 sectors, 24 industry groups and **69** industries (2023 revision).
FinanceDatabase has 11 / 24 / **80**. So sectors and industry groups align, but the industry
level has **11 more values than GICS**. This matches CONTRIBUTING:129 exactly:

> *"the sectors, industry groups and industries **loosely approximate** to the GICS® as created
> by MSCI. **No actual data is collected from this source** and this database merely tries to
> reflect the sectors and industries as best as possible. This is completely done through
> **manual curation**."*

A CI job (`Check-GICS-Categorisation`, `:582-627`) enforces internal consistency of the
`(sector, industry_group, industry)` triple against `compression/categories/categories.json` —
so the taxonomy is **internally validated** but **externally non-authoritative**. And that job
is **currently failing** (§3.3).

## 4.9 Schema-presence vs. value-quality matrix

The tasking requires this distinction explicitly. A column existing proves nothing about its
values.

| Column | Schema present | Populated | Current | Verified | Historical | Derived | User-facing label |
|---|---|---|---|---|---|---|---|
| `symbol` (all) | ✓ | ✓ 100% | ✓ | Internally unique per asset class | — | — | ✓ |
| `name` | ✓ | 97–100% | Mostly | ✗ (129 rows = `two`, 1,774 trailing spaces) | — | — | ✓ |
| `summary` | ✓ | 47–99% | **Unknown** | ✗ | Likely for the static classes | Possibly generated prose | ✓ |
| `currency` | ✓ | 98% (eq) | ✓ | ✗ (`ILA` is not ISO 4217; 560 rows) | — | — | ✓ |
| `sector` / `industry_group` / `industry` | ✓ | 64–92% | ✓ for US (weekly); **stale for non-US** | CI-validated internally, **currently failing** | — | **Partly derived by `.mode()[0]`** | ✓ |
| `exchange` | ✓ | 99.6% | ✓ | ✗ (8,186 rows hardcoded, NYSE→`ASE`) | — | — | ✓ |
| `mic` | ✓ | 99.3% (eq) / 40–45% (funds, indices) | ✓ | Format-consistent; not validated against ISO 10383 registry | — | Partly derived from existing rows | ✓ |
| `market` | ✓ | 99.3% | ✓ | ✗ semantics vary by row | — | Partly hardcoded | ✓ |
| `country` | ✓ | 94.1% | **Stale for non-US** | ✗ (14 `.SZ` rows = `United States`) | — | — | ✓ (HQ, **not** listing venue) |
| `state` / `city` / `zipcode` | ✓ | 28% / 62% / 57% | **Stale** | ✗ | — | — | ✓ |
| `website` | ✓ | 59% | **Unknown** | ✗ (`http://` scheme) | — | — | ✓ |
| `market_cap` | ✓ | 67.7% | **Frozen at first sight** | ✗ | — | **Yes — bucketed from a third-party point-in-time value** | ✓ |
| `isin` | ✓ | **27.0%** | **Stale** | ✓ **checksum-valid** (validator: 0 ISIN issues) | — | — | ✓ |
| `cusip` | ✓ | **24.2%** | **Stale** | ~✓ (2 checksum mismatches in 27,286) | — | — | ✓ |
| `figi` / `composite_figi` / `shareclass_figi` | ✓ | 52% / 54% / 57% | **Stale** | ✓ checksum-valid (0 FIGI issues) | — | — | ✓ |
| `delisted` | ✓ equities only | 100% | ✓ for US; **stale for non-US** | dtype-guarded by a test | **Retains history** | — | ✓ |
| `base_currency` / `quote_currency` | ✓ currencies | 100% | ✓ | Format-consistent | — | — | ✓ |
| `cryptocurrency` | ✓ cryptos | 99.8% | **~2020 snapshot** | ✗ (Yahoo collision suffixes: `SOL1`, `DOT1`, `UNI3`) | **Stale** | Derived by splitting `symbol` on `-` | ✓ |
| any timestamp / provenance | **✗ ABSENT** | — | — | — | — | — | — |

## 4.10 Data-quality limitations (consolidated)

1. **No temporal dimension at all.** Nothing can be time-series joined, backtested point-in-time,
   or staleness-checked per record.
2. **Identifier coverage 24–57%**, and structurally 0% for funds, indices, currencies, cryptos
   and money markets. Open issue **#78** ("How can we contribute ISIN codes?", open since
   2024-03-28) confirms this is known and unresolved.
3. **Classification gaps**: `industry` empty for 35.5% of equities; `category` empty for 37.7%
   of ETFs and 24.7% of indices.
4. **Text hygiene**: 4 symbols with leading/trailing whitespace, 19 with internal whitespace
   (including `'ECC           '` with 11 trailing spaces, `'AUS B.ST'`, `'BQI RT WI'`,
   `'GRH PR C'`), 1,774 names with trailing whitespace.
5. **Placeholder corruption**: 129 equity rows have `name == 'two'`, spread across exchanges
   (`000851.SZ`, `002447.SZ`, `046110.KQ`, `0JUZ.L`, `0OFR.IL`, `0YW.BE`), all labelled
   `country='United States'` and `industry='Diversified Financial Services'`.
6. **Non-standard codes**: `currency='ILA'` (560 rows) alongside `ILS` (1 row).
7. **Mixed symbol semantics**: 503 of 1,356 `.VI` (Vienna) symbols match an ISIN pattern
   (`AT0000A288S5.VI`), while others are local codes (`1COV.VI`, `A2A.VI`). The `symbol` field
   is not one kind of thing.
8. **Country mislabels**: 14 Shenzhen (`.SZ`) rows carry `country='United States'`.
9. **Duplicate-risk fields**: `isin` 21,023 duplicate values, `cusip` 14,340, `shareclass_figi`
   34,826, `composite_figi` 19,761 — semantically *expected* for multi-listing data, but fatal
   if any of these is mistaken for a primary key (§5.3).
10. **Ambiguity risk**: 47,578 lowercase-duplicate `name` values; `name` is the only
    issuer-like field and it is free text.
