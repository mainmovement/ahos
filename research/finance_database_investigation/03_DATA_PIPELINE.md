# 03 — Data Pipeline Reconstruction

**Phase 3: where does FinanceDatabase data come from, and how does it become queryable?**

Reconstructed from `.github/workflows/database_update.yml` (29,385 B, 627 lines, read in
full), `compression/README.md`, `CONTRIBUTING.md`, `README.md:465-467`, and by direct
inspection of the generated artifacts at commit `a174c97d`.

---

## 3.1 The complete lifecycle

| Stage | Local / Remote | Static / Dynamic | Generated / Downloaded | Mechanism | Evidence |
|---|---|---|---|---|---|
| **1. Source (US equities)** | Remote | Dynamic | Third-party generated | `pd.read_json()` of three URLs on `raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/{nasdaq,nyse,amex}/*_full_tickers.json` — an unpinned `main` branch of a **574-star personal repo with `license = None`** whose commits are literally titled `generated` | `database_update.yml:167,173,179`; GitHub API on `rreichel3/US-Stock-Symbols` (pushed 2026-09-15T00:39:12Z) |
| **1b. Source (everything else)** | — | **Static** | Historical bulk import + community PRs | The pre-existing `database/` CSVs. **No automated source exists** for non-US equities, ETFs, funds, indices, currencies, cryptos or money markets | README:467: *"When companies outside American exchanges undergo changes (migrations, mergers, bankruptcies), we depend on community members to identify and update these entries."* |
| **2. Collection** | Remote→CI | Dynamic | Scheduled | GitHub Actions runner (`ubuntu-latest`), `actions/checkout@v6`, Python 3.13, `pip install "pandas[excel]" financedatabase`, inline script executed by **`jannekem/run-python-script-action@v1.8`** | `database_update.yml:12-26` |
| **3. Transformation** | CI | Dynamic | Generated | Field mapping, hardcoded exchange/market assignment, GICS lookup from an XLSX, **statistical imputation of sector/industry_group by `.mode()[0]`**, market-cap bucketing | `:133-159`, `:169-182`, `:191-194`, `:33-57`, `:76-115` |
| **4. Validation** | CI | Dynamic | Generated | GICS triple `(sector, industry_group, industry)` checked against `compression/categories/categories.json`; identifier checksums via `validation/validate_identifiers.py` | `:582-627`; `testing.yml:36-57` |
| **5. Normalization** | CI | Dynamic | Generated | `dtype=str, keep_default_na=False`; dedupe `index.duplicated(keep='first')`; drop null/empty symbols; `sort_index()` | `:196-206`, `:260-265` |
| **6. Storage (source of truth)** | Repo | Static between runs | Generated | `database/equities/<EXCHANGE>.csv` (85 files) + `database/{etfs,funds}/*.csv` + 4 flat CSVs. **145 MB at HEAD** | `:267-274`; sparse checkout |
| **7. Packaging** | Repo | Static between runs | Generated | `database/*.csv` → `compression/*.bz2` (`index=False`, `compression='bz2'`, sorted by first column). Categories → `compression/categories/*.gzip` with **fixed `mtime=0`** for byte-reproducibility | `:304-339`, `:368-454` |
| **8. Distribution** | Remote | Dynamic | GitHub raw over HTTPS | `raw.githubusercontent.com/JerBouma/FinanceDatabase/**main**/compression/` — no CDN cache-control, no versioned path, no manifest | `helpers.py:12-14` |
| **9. Loading** | Client | Dynamic at runtime | Downloaded | `requests.get(timeout=60)` → `response.content` → `pd.read_csv(BytesIO, compression="bz2", index_col=0)` on **every class instantiation**. No cache. | `helpers.py:65-72` |
| **10. Query** | Client, in-RAM | Dynamic | — | pandas boolean masks over a fully materialised DataFrame | `Equities.py:77-222`, `helpers.py:103-155` |
| **11. User output** | Client | Dynamic | — | `FinanceFrame` (a `pd.DataFrame` subclass) | `helpers.py:155,222`, `:170` |

**Runtime-dependent stages:** 8, 9, 10, 11 — i.e. everything the user experiences depends on
a live HTTPS GET to a mutable branch, unless a full repository checkout is present.

## 3.2 Trigger model

```yaml
# database_update.yml:1-8
name: Database Update
on:
  push:
    branches: [ 'main' ]
  schedule:
    - cron: '0 12 * * SUN'
```

- **Scheduled:** Sunday 12:00 UTC.
- **Also on every push to `main`** — including pushes made by the workflow itself. Observed
  behaviour at HEAD shows this does not produce an infinite loop; whether that is due to
  GitHub's recursion guard, the `git diff-index --quiet HEAD ||` guard at `:281`, or the
  identity used for the push, is **UNKNOWN** (U-11). The commits are authored
  `GitHub Action <action@github.com>` and pushed with `secrets.PAT`.
- Observed data-commit dates: **2026-08-25, 08-30, 09-06, 09-11, 09-13** — i.e. the weekly
  Sunday cadence plus extra runs triggered by merged community PRs (e.g. #170, 2026-09-11).
- README:465 corroborates: *"For American exchanges, the database automatically updates every
  Sunday."* **VERIFIED** against both the cron expression and the commit log.

## 3.3 Job graph

```
Add-New-Ticker ──► Update-Compression-Files ──► Update-Categorization-Files ──► Update-README-Statistics ──► Check-GICS-Categorisation
   (:11)                  (:287)                        (:352)                        (:468)                        (:582)
   commits+pushes         commits+pushes                commits+pushes                commits+pushes                VALIDATES ONLY
   "Update database       "Update Compression           "Update Categorization        "Update README                raises ValueError
    with new tickers"      Files"                        Files"                        statistics"                 on invalid GICS
   (:275-282)             (:340-347)                    (:455-462)                    (:574-580)                    (:619-627)
```

Every job: `runs-on: ubuntu-latest`, `actions/checkout@v6`, `git pull https://${{secrets.PAT}}@github.com/…`,
`actions/setup-python@v6` (3.13 for job 1; **3.10** for jobs 2-5), `pip install "pandas[excel]" financedatabase`,
then inline Python via `jannekem/run-python-script-action@v1.8`, then commit-and-push.

> **Structural consequence:** validation is the **last** job. By the time
> `Check-GICS-Categorisation` runs, the data has already been committed and pushed to `main`
> three times over. Its `raise ValueError` (`:626-627`) fails the *job*; it cannot roll back
> the *data*. Every consumer downloading from `main` already has the unvalidated content.

**Observed run status at HEAD** (run id 34764660277, 2026-09-13T15:07, event `schedule`,
conclusion `failure`):

| Job | Conclusion |
|---|---|
| Add-New-Ticker | **success** |
| Update-Compression-Files | **success** |
| Update-Categorization-Files | **success** |
| Update-README-Statistics | **success** |
| **Check-GICS-Categorisation** | **failure** (failed step: `Check GICS Categorisation`) |

The same pattern — four successes then a `Check-GICS-Categorisation` failure — is present on
the **2026-09-11** and **2026-09-06** runs. So the dataset currently on `main` **does not
satisfy the project's own GICS invariant**, and has not for at least three consecutive
update cycles. Which rows are invalid was **not obtainable** (the job log was not retrieved;
see U-12).

## 3.4 Transformation logic in detail (job 1, `:28-274`)

### 3.4.1 Hardcoded exchange attribution (`:166-185`)

```python
nasdaq = pd.read_json("…/nasdaq_full_tickers.json").set_index('symbol')
nasdaq['exchange'] = 'NMS';  nasdaq['market'] = 'NASDAQ Global Select'      # :169-170
nyse   = pd.read_json("…/nyse_full_tickers.json").set_index('symbol')
nyse['exchange']   = 'ASE';  nyse['market']   = 'NYSE MKT'                  # :175-176
amex   = pd.read_json("…/amex_full_tickers.json").set_index('symbol')
amex['exchange']   = 'ASE';  amex['market']   = 'NYSE MKT'                  # :181-182
exchange_data = pd.concat([nasdaq, nyse, amex])                             # :185
```

**Finding DP-01 — NYSE listings are labelled `ASE` / `NYSE MKT`.** Line 175 assigns the
*NYSE American* (AMEX) code to the **NYSE** dataset. The comment at `:178` explains the AMEX
assignment ("acquired by NYSE, same exchange/market") but nothing justifies applying it to
NYSE. Measured consequence in the shipped data:

| `exchange` | rows | distinct `market` values |
|---|---:|---|
| `ASE` | 1,128 | exactly one: `NYSE MKT` |
| `NMS` | 7,058 | exactly one: `NASDAQ Global Select` |

Every `ASE` and `NMS` row carries a single hardcoded market string. There is no variation,
which is the signature of assignment rather than measurement. Any AHOS reasoning that treats
`exchange`/`market` as observed venue data will be wrong for these 8,186 rows.

**Finding DP-02 — `pd.concat` without `keys=`.** NASDAQ, NYSE and AMEX frames are
concatenated flat. A symbol present in more than one feed appears twice in `exchange_data`.
The code tolerates this only by later deduplication with `keep='first'` (`:260`), i.e. the
surviving row depends on feed order — an arbitrary, silent identity collapse.

### 3.4.2 Derived fields

**`market_cap` (`:33-57`, `:224`)** — not a value, a **bucket label**:

```python
MARKET_CAP_THRESHOLDS = {'Mega Cap':200e9,'Large Cap':10e9,'Mid Cap':2e9,
                         'Small Cap':300e6,'Micro Cap':50e6,'Nano Cap':0}
def calculate_market_cap(value):
    if pd.isna(value) or not value: return np.nan
    for label, threshold in MARKET_CAP_THRESHOLDS.items():
        if float(value) >= threshold: return label
    return np.nan
```

Computed from `row.get('marketCap')` in the third-party JSON — a point-in-time figure,
converted to a coarse ordinal, in USD, with no timestamp recorded. Measured distribution:

| `market_cap` | rows | share |
|---|---:|---:|
| *(empty)* | 36,362 | 32.27% |
| Nano Cap | 22,774 | 20.21% |
| Small Cap | 16,172 | 14.35% |
| Micro Cap | 15,649 | 13.89% |
| Mid Cap | 10,838 | 9.62% |
| Large Cap | 10,254 | 9.10% |
| Mega Cap | 641 | 0.57% |

**Finding DP-03 — `market_cap` is never refreshed for existing tickers (dead-code bug).**

```python
# :223-235
for index, row in exchange_data.iterrows():
    market_cap = calculate_market_cap(row.get('marketCap'))
    try:
        fd_data = equities.loc[index]
        # Update market_cap only when it has changed and the new value is valid
        if len(fd_data) == 0 and fd_data['market_cap'] != market_cap and pd.notna(market_cap):
            ticker_dict[index] = {'symbol': index, **fd_data.to_dict(), 'market_cap': market_cap}
        continue
    except KeyError:
        ticker_dict[index] = build_new_ticker(...)
```

For an existing symbol, `equities.loc[index]` returns a **Series of length 21** (the column
count), so `len(fd_data) == 0` is **False** for every normal row. The `and` therefore short-
circuits to False, `ticker_dict` is never populated for existing rows, and `continue` always
executes. Consequently:

- the intended "update market_cap when it changed" branch is **unreachable**;
- the downstream `existing_indices` / `equities.update(...)` block at `:251-253` is **dead
  code** — `updated_companies` can only ever contain brand-new tickers;
- **README:465's claim that the process "includes checks for market cap changes" is not
  realised by the code at HEAD.**

Status: **VERIFIED by source reading.** The logic is unambiguous. It was **not** verified by
observing a market-cap change fail to land across two runs (that would need two weekly
snapshots — see U-13). Note also the guard would be wrong even if reachable: if a symbol were
duplicated, `.loc` returns a DataFrame and `len()` is the row count, not 0.

**`sector` / `industry_group` / `industry` (`:60-115`, `:133-135`)** — three-stage lookup:

```python
industry       = lookup_industry(row['industry'], fd_industries)          # XLSX label map, KeyError -> np.nan
industry_group = lookup_industry_group(industry, equities)                # MOST COMMON value among existing rows
sector         = lookup_sector(industry, industry_group, equities)        # MOST COMMON value among existing rows
```

`lookup_industry_group` / `lookup_sector` end in `subset[…].mode()[0] if not subset.empty else np.nan`
(`:87`, `:113`).

**Finding DP-04 — GICS classification of new tickers is a statistical mode, not a
classification.** A new ticker's sector and industry group are whatever is *most frequent*
among already-classified rows sharing its industry label. This is imputation by popularity. It
propagates existing errors, silently degrades as the mix shifts, and produces no confidence
value, no "inferred" flag and no record that inference occurred. The resulting row is
indistinguishable from a curated one.

**`build_new_ticker` (`:117-159`)** — every field a new ticker receives:

```python
{'name': row['name'], 'summary': np.nan, 'currency': 'USD',            # ← hardcoded
 'industry': industry, 'industry_group': industry_group, 'sector': sector,
 'exchange': row['exchange'], 'mic': exchange_to_mic.get(row['exchange'], np.nan),
 'market': row['market'], 'country': row['country'],
 'state': np.nan, 'city': np.nan, 'zipcode': np.nan, 'website': np.nan,
 'market_cap': market_cap,
 'isin': np.nan, 'cusip': np.nan, 'figi': np.nan,
 'composite_figi': np.nan, 'shareclass_figi': np.nan,
 'delisted': False}
```

**Finding DP-05 — newly discovered tickers are permanently identifier-less.** All five
identifier fields (`isin`, `cusip`, `figi`, `composite_figi`, `shareclass_figi`) plus `summary`,
`state`, `city`, `zipcode` and `website` are set to `NaN`, and `currency` is hardcoded to
`USD`. Because of DP-03, **no later run ever revisits an existing row**, so these fields stay
empty forever unless a human opens a PR. Measured signature in the shipped data:

| Signature | Rows | Share of equities |
|---|---:|---:|
| `isin`, `cusip`, `figi` **and** `summary` all empty simultaneously | **7,425** | **6.59%** |

That 6.6% is the observable footprint of the automated pipeline since it was introduced. It is
also the population for which **no identity resolution beyond the bare symbol is possible**.

`mic` for new rows comes from `exchange_to_mic`, derived at `:210-215` by
`drop_duplicates('exchange')` over rows that already have a MIC — self-referential, and
yielding `np.nan` for any exchange code not already present.

### 3.4.3 Merge-back and re-sharding (`:241-274`)

```python
updated_companies = pd.DataFrame.from_dict(ticker_dict, orient='index')
updated_companies.index.name = 'symbol'
updated_companies = updated_companies.drop(columns=['symbol'], errors='ignore')   # :245
…
equities = equities[~equities.index.duplicated(keep='first')]                     # :260
equities = equities[equities.index.notna() & (equities.index != '')]              # :264
equities = equities.sort_index()                                                  # :265
for f in glob.glob('database/equities/*.csv'): os.remove(f)                       # :267-268
unknown_exchange = equities['exchange'].isna() | (equities['exchange'] == '')
for exchange, group in equities[~unknown_exchange].groupby('exchange'):
    group.to_csv(f'database/equities/{exchange}.csv')                             # :271-272
if unknown_exchange.any(): equities[unknown_exchange].to_csv('database/equities/NAN.csv')
```

Three consequences, all **verified in the data**:

1. **`:260` global dedupe `keep='first'`** — the dataset is now **one row per symbol
   globally**. Any secondary listing that once shared a symbol with another row is gone, and
   *which* row survived depends on the sorted order of `database/equities/*.csv` filenames at
   the time. This is the most plausible mechanism for the equities count moving from the
   **158,429** still advertised on the official website to the **112,690** in the data (§1.4),
   though the exact commit was **not** bisected (U-14) — status **INFERENCE**.
2. **`:267-268` delete-then-rewrite of all 85 shard files** — a full re-shard every run. If a
   run fails partway after `os.remove`, the working tree loses equity data; recovery depends
   on git. `test_equities_read_rewrite_is_byte_identical` (`test_invariants.py:14-49`) exists
   precisely to keep this rewrite a no-op for untouched rows, and it **passes**.
3. **Filename injection surface:** `f'database/equities/{exchange}.csv'` interpolates a value
   read from the third-party JSON directly into a filesystem path. A `exchange` value
   containing `/` or `..` would write outside the intended directory. It is constrained in
   practice because `exchange` is *assigned* by the workflow (`:169,175,181`), not taken from
   the JSON — so the value is always one of `NMS`/`ASE`. Status: **no issue observed in
   reviewed scope**; the constraint is incidental, not defensive.

### 3.4.4 Known historical defects encoded in comments

The workflow carries three comments describing bugs already encountered (`:196-202`):

> *"dtype=str stops pandas inferring numeric-looking columns such as zipcode and cusip as
> float64 ("9763" -> "9763.0", "031162100" -> "31162100.0"). keep_default_na=False stops it
> reading the symbol "NA" (Nano Labs) as a missing value, **which dropped that row on every
> run**."*

These are project-owned admissions of three real, shipped data-corruption defects. Two
(`9763.0`, `031162100`) are fixed in the *pipeline*; the third (the `NA` symbol) is fixed in
the pipeline **and on `main`**, but **not in release 2.4.0** — which is why a `pip install`
user reading today's data still loses the row (§2.3.2, §13 S-13). Measured divergence:

| Read semantics | index NaN count | `'NA' in index` | `.loc['NA']` |
|---|---:|---|---|
| **[R240]** `pd.read_csv(..., index_col=0)` | **1** | **False** | **KeyError** |
| **[MAIN]** `+ keep_default_na=False, na_values=[""]` | 0 | True | row returned |

Cell-level NaN counts were identical between the two — the damage is confined to the index.

## 3.5 Packaging and categorization jobs

**Compression (`:304-339`)** — Python **3.10**, `read = dict(dtype=str, keep_default_na=False)`:

```python
equities = pd.concat([pd.read_csv(f, **read) for f in sorted(glob.glob('database/equities/*.csv'))], ignore_index=True)
equities = equities.sort_values(equities.columns[0]).reset_index(drop=True)
equities.to_csv('compression/equities.bz2', index=False, compression='bz2')
```

Note `index=False` combined with `pd.read_csv` **without** `index_col=0`: `symbol` stays an
ordinary column, so the bz2 files carry `symbol` as column 0 — which the library then re-reads
with `index_col=0`. Verified: the on-disk header is
`symbol,name,summary,currency,…,delisted` (22 fields) and `eq.data.columns` has 21 entries.

**Categorization (`:368-454`)** — Python **3.10**, and critically a **different** read
configuration:

```python
gzip = {'method': 'gzip', 'mtime': 0}                                  # :377  byte-reproducible ✓
equities = pd.concat([pd.read_csv(f, index_col=0, dtype=str) for f in …])   # :401  ← NO keep_default_na=False
for column in equities:
    if column in ['name','summary','website','delisted']: continue     # :404
    equities_categories[column] = sorted(equities[column].dropna().unique(), key=str)
```

**Finding DP-06 — the two generated artifact families are built with inconsistent parsers.**
Compression uses `keep_default_na=False`; categorization does not. They also differ in whether
`index_col=0` is applied, and categorization excludes `delisted` from the option lists. The
`mtime=0` gzip setting is genuinely good practice (unchanged content ⇒ byte-identical artifact
⇒ clean diffs).

The measurable consequence of this split is documented in §6.4: `fd.show_options("equities")`
advertises **117** countries while `Equities().show_options()["country"]` yields **114**, and
three advertised values are unreachable through `select()`.

**README statistics (`:484-573`)** — recomputes counts from `database/` and regex-substitutes
three Markdown tables. `_n()` formats with a dot thousands separator (`112.690`). This is why
the repo README matched our measurements exactly while the website did not.

## 3.6 Format survey (as required by the tasking)

| Format | Where | Used for | Present in the query path? |
|---|---|---|---|
| **CSV (plain)** | `database/**.csv` (145 MB, 137 files) | Source of truth; human-editable by design (CONTRIBUTING:4) | No — not shipped, not fetched |
| **CSV + bz2** | `compression/*.bz2` (7 files, ~21 MB total) | The distributed dataset | **Yes** — the only data path |
| **CSV + gzip** | `compression/categories/*.gzip` (7 files) | Precomputed option lists for `show_options` | **Yes** — second data path |
| **JSON** | `compression/categories/categories.json` (37,928 B) | GICS `sector → industry_group → industry` hierarchy used by the validation job | No — CI only |
| **XLSX** | `compression/categories/github_exchange_categories.xlsx` (21,578 B) | Exchange → sector/industry_group/industry label mapping for new tickers | No — CI only |
| **JSON (remote)** | `rreichel3/US-Stock-Symbols/**/*.json` | Upstream US ticker feed | No — CI only |
| **Jupyter notebook** | `compression/compression.ipynb` (82,049 B) | The benchmark that chose bz2 | No |
| **SQLite** | — | — | **Absent** |
| **Parquet** | — | — | **Absent** |
| **Pickle** | — | — | **Absent by deliberate decision.** `compression/README.md`: *"Pickle (xz) results in the most efficient loading. However, to solve the vulnerability issue that arises with loading with Pickles I've decided to take the next best thing, this is the CSV BZ2 option."* |
| **HDF5** | — | Evaluated in `compression.ipynb`, rejected | **Absent** |
| External APIs | — | None in the library | **Absent** — the library makes no API calls, only two `requests.get` for files |
| Scraping | — | None in the library; the *upstream* repo is described as "powered by GitHub Actions" | Not in scope of the shipped package |

**Distribution size budget:** `equities.bz2` 15.29 MB, `funds.bz2` 1.85 MB, `etfs.bz2` 1.28 MB,
`indices.bz2` 1.19 MB, `currencies.bz2` 0.05 MB, `cryptos.bz2` 0.03 MB, `moneymarkets.bz2`
0.02 MB. Loading *all seven* means ~21.6 MB of transfer per cold start, per process, with no
cache.

## 3.7 Pipeline findings summary

| ID | Finding | Severity for AHOS | Status |
|---|---|---|---|
| DP-01 | NYSE listings hardcoded to `exchange='ASE'`, `market='NYSE MKT'`; all `NMS` rows hardcoded to `NASDAQ Global Select` (8,186 rows) | High — venue fields are assigned, not observed | VERIFIED (source + data) |
| DP-02 | `pd.concat` of three feeds without keys; duplicates resolved by `keep='first'` in feed order | High — arbitrary identity collapse | VERIFIED (source) |
| DP-03 | `len(fd_data) == 0` guard makes the market-cap refresh unreachable; `equities.update()` is dead code | High — README claim unrealised; fields frozen at first sight | VERIFIED (source); cross-run confirmation U-13 |
| DP-04 | `sector`/`industry_group` imputed by `.mode()[0]` with no inference flag | High — silent statistical guess presented as classification | VERIFIED (source) |
| DP-05 | New tickers get `NaN` for all 5 identifiers + summary/state/city/zipcode/website, `currency='USD'` hardcoded, and are never revisited (7,425 rows = 6.59%) | Critical for identity work | VERIFIED (source + data) |
| DP-06 | Compression and categorization jobs use inconsistent `read_csv` options, producing drifting option lists | Medium | VERIFIED (source + measured drift) |
| DP-07 | Validation is the last job and cannot block already-pushed data; `Check-GICS-Categorisation` failing on 3 consecutive runs | Critical for trust | VERIFIED (CI observation) |
| DP-08 | Bot data commits trigger **0** workflow runs and **0** check runs | Critical for trust | VERIFIED (GitHub API) |
| DP-09 | Data pinned to mutable `main`; code pinned to a release tag ⇒ irreproducible (code, data) pairs | Critical for reproducibility | VERIFIED |
| DP-10 | Upstream feed is an unlicensed, single-maintainer, unpinned `main` branch of a scraper repo | High — supply chain + legal | VERIFIED |
| DP-11 | Automated updates cover **US exchanges only** | High — non-US data has no maintenance mechanism | VERIFIED (source + README:467) |
