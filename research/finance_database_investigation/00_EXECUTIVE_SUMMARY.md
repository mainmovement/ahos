# 00 — Executive Summary

**Investigation date:** 2026-09-15 UTC · **Audited commit:** `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634` (2026-09-13) · **Audited release:** PyPI `financedatabase==2.4.0` (2026-06-02)

---

## 1. Bottom line

FinanceDatabase is a **well-known, actively maintained, MIT-licensed static catalogue of
financial listings** with a small, cleanly auditable Python surface. It is **not** a market
data provider, not an on-chain provider, not a crypto discovery engine, and not anything
resembling a signal, risk or scoring system.

For AHOS **as it exists today** (paper-only, crypto, evidence-first, $0/month, local-first,
sanctions-resilient), FinanceDatabase has **no usable production role**:

1. Its cryptocurrency table cannot see AHOS's target domain at all (§8).
2. Its only supported data path is an unpinned HTTP GET to `raw.githubusercontent.com/main/`
   at every object construction, with no integrity check and no cache (§3, §11).
3. Its `search()` API **fails open**: an invalid column name prints one line to stdout and
   returns the entire 112,690-row universe (§6). That is the exact inverse of AHOS doctrine.
4. Its own test suite **fails on its own `main` branch today**, and its data-validation job
   is **failing and non-blocking** (§7, §11).
5. Its declared hard dependency (`financetoolkit`) drags in `yfinance`, `scikit-learn` and
   `pandas>=3.0` — a heavy, Yahoo-coupled tree that AHOS's requirements file explicitly
   forbids by policy (§9).

It nevertheless has **real research value**, in three specific and bounded forms (§15):
a cautionary **identity-resolution corpus**, a **taxonomy seed**, and a **worked example of
how not to version a distributed dataset**.

> ### Judgment: **C. RESEARCH-ONLY VALUE**
> With **E. REJECTED** for the crypto/opportunity-detection use case specifically.

---

## 2. The ten findings that decide the question

Each is verified by source reading, direct data measurement, or executing the project's own
code. Full evidence in the referenced documents and in `evidence/`.

| # | Finding | Evidence class | Doc |
|---|---|---|---|
| F-01 | **The crypto table is a ~2020-era Yahoo/CryptoCompare *pair* list.** 3,367 rows = 352 token tickers × up to 12 quote currencies. Columns are exactly `symbol, name, cryptocurrency, currency, summary, exchange, website`. No chain, no contract address, no price, no market cap, no volume, no liquidity, no decimals, no launch date. | Dataset inspection | §8 |
| F-02 | **Solana is absent under its own ticker.** `Cryptos().select(cryptocurrency="SOL")` raises `ValueError: The cryptocurrency 'SOL' is not available in the database`. Solana exists only as `SOL1` (Yahoo collision suffix), name `"Solana CAD"`. **Bitcoin (`BTC`) is absent entirely** as a token — it appears only as a quote currency. | Test result (executed) | §8 |
| F-03 | **51 of 73 probed modern tokens are absent**, including every Solana-ecosystem token (BONK, WIF, JUP, PYRM, JTO, RAY, ORCA, POPCAT), every memecoin (PEPE, SHIB, DOGE-adjacent), and L1s SUI/APT/SEI/TIA/INJ. Present tokens are dominated by dead 2017–2019 altcoins (BURST, DIME, GBYTE, MAID, NYZO, PZM, YOYOW…). | Dataset inspection | §8 |
| F-04 | **No record in any of the 7 asset classes carries a timestamp, freshness field or provenance field.** Column-name scan across all 7 schemas returned `NONE`. `STALE ≠ LIVE` is therefore not even *evaluable* from the data; freshness is only inferable from the git commit date of the file. | Dataset inspection | §4, §7 |
| F-05 | **`search()` fails open.** `eq.search(symbl="AAPL")` (a typo) → prints `symbl is not a valid column.` → returns **all 112,690 rows**. The library's *own docstring example*, `search(symbol="TSLA")`, does the same, because `symbol` is the DataFrame index, not a column. No exception, no status field, no empty result. | Source + test result | §6 |
| F-06 | **The project's own test suite fails on its own `main` today.** Reproduced in an isolated venv: `1 failed, 85 passed` — `test_no_symbol_collisions_across_asset_classes` → `equities <-> etfs: ['CHAD']`. `CHAD` is simultaneously *DeFi Development Corp. Series C Perpetual Preferred* (equities, NASDAQ) and *Direxion Daily CSI 300 China A Share Bear 1X* (ETFs, PCX). | Test result (executed) | §7, §13 |
| F-07 | **Data commits are not gated by CI.** Bot commit `a174c97d` has **0 workflow runs and 0 check runs**. The last successful `Run Tests` was on a human PR commit (2026-09-11). The `Check-GICS-Categorisation` job has **failed** on the 2026-09-13, 09-11 and 09-06 runs — and it runs *last*, after the data is already committed and pushed, so it cannot block anything. | Repository + CI observation | §3, §7, §11 |
| F-08 | **Released code and served data are version-decoupled.** `DATA_REPO` is hardcoded to the **`main`** branch, but the last release is 2.4.0 (2026-06-02) — 3.5 months behind `main`. `main` already changed `read_csv` semantics (`keep_default_na=False, na_values=[""]`); release 2.4.0 did not. Measured consequence: a `pip install financedatabase==2.4.0` user reading today's data **silently loses the ticker `NA`** (Nano Labs) to NaN — `'NA' in index → False`, `.loc['NA'] → KeyError`. There is no way to pin the data version. | Source diff + test result | §1, §3, §13 |
| F-09 | **Identifier coverage is low even though identifier *validity* is high.** Equities: `isin` 27.0% populated, `cusip` 24.2%, `figi` 52.0%, `composite_figi` 54.0%, `shareclass_figi` 56.8%. ETFs `isin` 21.7%. Funds/Indices/Currencies/Cryptos/Moneymarkets have **no identifier columns at all**. But the project's own validator, run by us against 137 CSVs / 249,085 populated identifiers / 14,804 ISIN-CUSIP pairs, found only **2 invalid values** (both CUSIP checksum mismatches) and 0 consistency issues. | Dataset inspection + tool run | §5, §12 |
| F-10 | **`only_primary_listing=True` destroys non-US primary listings.** The heuristic is `~index.str.contains(r"\.")`. For China it keeps 866 of 6,961 rows (**drops 87.6%**), including deleting `000002.SZ` — the *primary* Shenzhen listing of China Vanke. Across ETFs, 92.3% of symbols contain a dot. Meanwhile it *retains* genuine duplicates: `BRK-A`, `BRK/A`, `BRK-B`, `BRK/B` are all dotless and all survive. | Source + test result | §5, §6, §13 |

---

## 3. Answers to the questions AHOS actually asked

Direct answers, no hedging where the evidence is conclusive.

| Question | Answer | Confidence |
|---|---|---|
| Can it detect a newly launched Solana token? | **No.** It has no Solana token discovery, no chain field, no launch date, and no `SOL` entry at all. It is a weekly-updated *US equities* pipeline; the crypto file is a static snapshot with no update job anywhere in the workflow. | VERIFIED — conclusive |
| Can it detect a newly created liquidity pool? | **No.** No pool concept exists in any schema. | VERIFIED — conclusive |
| Can it verify token sellability / detect honeypots / inspect liquidity locks / detect whale concentration? | **No.** Zero security fields, zero holder data, zero on-chain data. | VERIFIED — conclusive |
| Can it provide real-time DEX order flow? | **No.** No time series of any kind. | VERIFIED — conclusive |
| Can it provide an evidence-grade opportunity signal? | **No.** It contains no observation, no measurement, no score and no timestamp. | VERIFIED — conclusive |
| Is it a live market data provider? | **No.** Prices, volumes and market caps are absent from every schema. `market_cap` in equities is a *derived bucket label* (Mega/Large/Mid/Small/Micro/Nano Cap), 32.3% empty, and per a dead-code bug in the pipeline it is **never refreshed for existing tickers**. | VERIFIED |
| Is it an on-chain data provider? | **No.** | VERIFIED — conclusive |
| Is it a financial taxonomy source? | **Partially, and usefully.** 11 sectors / 24 industry groups / 80 industries with a `categories.json` hierarchy and a CI job that validates the triple. But CONTRIBUTING states it "loosely approximate[s]" GICS® and is "completely done through manual curation" — it is **not** authoritative GICS, and GICS® is an MSCI/S&P trademark. | VERIFIED (scope-limited) |
| Is it an instrument-discovery source? | **For US-listed equities/ETFs: yes, with caveats.** For everything non-US: only as a static historical snapshot with **no automated maintenance** (README states this explicitly). For crypto: **no**. | VERIFIED (per asset class) |
| Is it a knowledge-graph input? | **Plausibly, at low confidence edges.** It supplies a partial 3-level FIGI hierarchy (share class → security → listing), ISIN/CUSIP, MIC/exchange, and a sector→industry_group→industry ontology — but coverage is 24–57% and issuer identity is only approximated by free-text `name` (which contains 257 rows literally named `ISHARES` and 129 named `two`). | PARTIALLY_VERIFIED |
| Is it safe as a production dependency? | **No, not as distributed.** Unpinned mutable data source, no integrity check, fail-open query API, failing CI, heavy undeclared-adjacent dependency tree. | VERIFIED |
| Is isolated adapter integration justified **now**? | **No.** There is no current AHOS lane that consumes equity instruments. Adopting it now is scope creep during an active soak. | Judgment on verified facts |

---

## 4. What is genuinely good (stated for balance)

An evidence-first review must report favourable evidence too.

- **Tiny, auditable code surface.** 9 modules, ~1,866 lines in the released wheel. Grep across the shipped package found **zero** occurrences of `eval`, `exec`, `pickle`, `marshal`, `subprocess`, `os.system`, `socket`, `ctypes`, `open(`, `shutil`, `yaml.load` or `compile(`. Exactly two network call sites, both `requests.get(..., timeout=60)` with `raise_for_status()`. (§11)
- **Deliberate, documented rejection of pickle.** `compression/README.md` records that pickle-xz benchmarked best and was rejected "to solve the vulnerability issue that arises with loading with Pickles", choosing CSV+bz2 instead. That is real security engineering. (§11)
- **Fail-closed on network errors.** Unreachable data raises `ValueError` with an actionable message; it does not return an empty frame. Verified live in this sandbox. (§6)
- **`select()` is well designed.** Exact matching, case-insensitive, validated against live options, raises `ValueError` on unknown values, AND across parameters, OR within a list parameter, and deterministic. (§6)
- **Delisted instruments are intentionally retained** (10,404 of 112,690 equities) and README states this is "for historical research purposes" — a genuine anti-survivorship-bias property, unique among free datasets of this size. (§7)
- **Real invariant tests exist**, including cross-asset symbol collision, cross-asset ISIN collision, `delisted` dtype strictness, and byte-identical read/rewrite of the equity CSVs. They caught a real defect (`CHAD`). They are simply not run against automated data commits. (§7)
- **A real identifier validator exists** (`financedatabase/validation/validate_identifiers.py`, 533 lines) implementing ISO 6166 ISIN, CUSIP and OpenFIGI check digits plus ISIN↔CUSIP consistency, with deterministic repair and review-only classification. (§5)
- **Reproducible artifacts.** The categorization job writes gzip with a fixed `mtime=0` so unchanged content is byte-identical. (§3)
- **Healthy project.** 9,116 stars, 941 forks, 126 subscribers, 452 workflow runs, data commits as recent as 2026-09-13, only 4 open issues/PRs. (§1)

---

## 5. The single most important lesson for AHOS

FinanceDatabase is a **live demonstration of every identity failure mode AHOS's doctrine was
written to prevent** — in a mature, popular, MIT-licensed project:

- `symbol` is not identity: `META` is Metadium *and* Meta Platforms; `MMM` is 3M *and* Marley
  Spoon AG; `GO` is GoChain *and* Grocery Outlet; `BRK.AX` is Brookside Energy, not Berkshire.
- `CHAD` is two unrelated instruments in two asset classes **on `main` right now**.
- 86 of 351 crypto token tickers (24.5%) are also equity symbols.
- 26 crypto tickers are Yahoo collision-suffixed (`SOL1`, `DOT1`, `UNI3`, `LUNA1`, `COMP1`),
  and `COMP1` is *CompoundCoin*, **not** Compound.
- One ISIN maps to up to 57 symbols; one MIC maps to up to 7 exchange codes.
- A filter typo returns the whole universe instead of nothing.

AHOS's `architecture/identity/` already models `TokenIdentity ≠ PoolIdentity ≠ ChainIdentity`
with an explicit `IdentityState` enum (`VERIFIED / CONFLICT / UNRESOLVED / INVALID / STALE /
UNSUPPORTED`). FinanceDatabase models none of this. **It is therefore valuable to AHOS
precisely as an adversarial test corpus for that machinery — consumed offline, in research,
never as a live provider.** That is the recommendation in §14 and §18.

---

## 6. Adversarial self-review (required by §22 of the tasking)

| # | Question | Answer |
|---|---|---|
| 1 | Which claims rest only on documentation? | Row counts and taxonomy shape on the **official website** (158,429 equities) — **rejected as stale**; the repo README's numbers were independently confirmed by measurement. GICS adherence — from CONTRIBUTING, marked as an *approximation*, not verified against MSCI. |
| 2 | Which rest on source code? | Architecture (§2), pipeline (§3), fail-open `search` (§6), `only_primary_listing` heuristic (§6), `DATA_REPO` pinning to `main` (§3), dead-code market-cap bug (§7). All cite file + line. |
| 3 | Which were actually tested? | 60+ query-engine cases, all 7 schemas, duplicate/identity analysis, the crypto probe, the release-vs-main NA divergence, the `show_options` drift, performance timings, the project's own pytest suite, and the project's own identifier validator. All in `evidence/`. |
| 4 | Which are historical? | The crypto snapshot (~2020 era), the 158,429 website figure, release 2.4.0's `read_csv` semantics. Each is labelled as historical where used. |
| 5 | Which are current? | All row counts, schemas, CI status, test results and identifier stats are as of commit `a174c97d` (2026-09-13), measured 2026-09-15. |
| 6 | What remains UNKNOWN? | 14 items in [`17_UNKNOWNS_AND_OPEN_QUESTIONS.md`](17_UNKNOWNS_AND_OPEN_QUESTIONS.md) — notably remote-download latency (host blocked), Windows behaviour, real concurrency, the exact origin of the pre-2023 bulk import, and whether `github.com/JeroenBouma` was ever the project's home. |
| 7 | Did we attribute external-provider capability to FinanceDatabase? | **No.** §9 separates FinanceDatabase / FinanceToolkit / FMP / Yahoo / CryptoCompare capability explicitly. Nothing here credits FinanceDatabase with market data. |
| 8 | Did we imply real-time capability anywhere? | **No.** The words "real-time" and "live data" appear only in negative findings. |
| 9 | Did we confuse symbol with identity? | **No** — this was the central object of study (§5). |
| 10 | Did we propose changes to protected AHOS areas? | **No.** §14 is a sketch; Lane A, Decision Authority, scoring, security gates, identity resolution, runtime, calibration and the soak are all explicitly out of scope and untouched. |
| 11 | Did we invent any source, path, benchmark or test result? | **No.** Every file path and line number was read; every number in §10 was measured on the stated host; every "test result" comes from a script preserved in `evidence/scripts/`. |
| 12 | Are facts, inferences, recommendations and open questions separated? | **Yes** — by document, and by the `Status` column of the evidence register (§16). |

**One correction made during this investigation:** the tasking and much third-party
documentation point at `github.com/JeroenBouma/FinanceDatabase`. That URL returns **404**.
The authoritative repository is `github.com/**JerBouma**/FinanceDatabase`, and
`github.com/JeroenBouma` is a *distinct* GitHub account (different user ID, 0 public repos).
See §1.3 — this is itself a supply-chain observation.
