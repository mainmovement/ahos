# 06 — Query Engine Audit

**Phase 6.** Every row of every truth table below was **executed** against the real dataset at
commit `a174c97d`, in the isolated venv described in `evidence/ENVIRONMENT.txt`
(Python 3.11.2, pandas 3.0.5, numpy 2.4.6). Machine-readable form: `evidence/query_truth_table.json`.
Script: `evidence/scripts/a6_query_engine.py` (+ `a7_gaps.py`, `a9_rest.py`, `a10_final.py`, `a12_drift.py`).

Because `raw.githubusercontent.com` is unreachable from the audit host, all library calls used
`use_local_location=True` from a repository checkout — the same configuration the project's own
CI uses (`tests/test_invariants.py:52-63`). The remote path was exercised separately and is
reported in §6.6.

---

## 6.1 The three query surfaces

| Surface | Signature | Location | Matching | Validation | Failure mode |
|---|---|---|---|---|---|
| `select()` | explicit keyword parameters, per asset class | `Equities.py:23-222`, 6 siblings | **Exact** (`str.lower().isin(...)`) | **Yes** — each value checked against live options | `ValueError` → **fail-CLOSED** ✓ |
| `search()` | `**kwargs`, on the base class | `helpers.py:81-155` | **Substring / regex** (`str.contains`) | **None** | `print()` + return **all rows** → **fail-OPEN** ✗ |
| `show_options()` | method (per class) **and** module-level function | `Equities.py:224-316` + `helpers.py:280-358` | n/a | `ValueError` on bad `selection` ✓ | **Two different implementations returning two different schemas** (§6.4) |

There are no other query methods. No `get_by_id`, no `filter`, no `aggregate`, no pagination,
no `limit`, no lazy/iterator API, no async API.

## 6.2 `select()` — measured truth table (Equities)

| Operation | Input | Expected | **Actual (measured)** | Evidence |
|---|---|---|---|---|
| select | `country="Netherlands"` | exact, case-insensitive | **OK, 845 rows, 0.183 s** | `Equities.py:81-93` + runtime |
| select | `country="netherlands"` (lowercase) | should still match | **OK, 845 rows** — identical ✓ | runtime |
| select | `country="Netherland"` (typo) | rejected | **`ValueError`: "The country 'Netherland' is not available in the database…"** ✓ fail-closed | runtime |
| select | `sector="Energy"` | exact | **OK, 4,086 rows, 0.170 s** | runtime |
| select | `sector="ener"` (partial) | **no** substring support | **`ValueError`** ✓ — substring is rejected, unlike `search` | runtime |
| select | `country="United States", sector="Energy"` | AND | **OK, 1,116 rows, 0.283 s** — AND confirmed | runtime |
| select | `country=["United States","Canada"]` | OR within parameter | **OK, 34,455 rows** — OR confirmed | runtime |
| select | `market_cap="Mega Cap"` | bucket filter | **OK, 627 rows** (of 641 total Mega Cap; the difference is delisted rows) | runtime |
| select | `exchange="NMS"` | filter | **OK, 5,050 rows** (of 7,058 `NMS` total; rest delisted) | runtime |
| select | `mic="XNAS"` | filter | **OK, 5,605 rows** | runtime |
| select | *(no arguments)* | all non-delisted | **OK, 102,286 rows, 0.036 s** | runtime |
| select | `exclude_delisted=False` | include delisted | **OK, 112,690 rows** (+10,404 delisted) | runtime |
| select | `country="China", only_primary_listing=True, exclude_delisted=False` | keep Chinese primary listings | **OK, 866 of 6,961 rows — drops 6,095 (87.6%). `000002.SZ` (China Vanke, PRIMARY Shenzhen listing, ISIN `CNE100001SR9`) is DROPPED.** ✗ | runtime + `Equities.py:208-211` |
| select | `only_primary_listing=True` (all) | — | **OK, 25,468 of 112,690** — retains only dotless symbols, incl. duplicates `BRK-A`/`BRK/A`/`BRK-B`/`BRK/B` ✗ | runtime |
| select | `industry="Bank"` | — | **`ValueError`** — only `Banks` exists. Exact matching confirmed | runtime |
| select | `country="Falkland Islands"` | advertised by `fd.show_options` | **`ValueError`** — unreachable even with `exclude_delisted=False` ✗ (§6.4) | runtime |
| select | *(return type)* | DataFrame | **`FinanceFrame`**, a `pd.DataFrame` subclass | `Equities.py:222` |
| select | *(ordering)* | — | **source order** = sorted by `symbol` (imposed by the compression job's `sort_values`), *not* re-sorted by `select()` | runtime: `['000002.SZ','000004.SZ','000005.SZ']` |
| select | *(duplicates)* | — | none possible within an asset class (0 measured) | §4.0 SC-03 |

**Parameter inventory by asset class** (from source; `select` signatures):

| Class | Parameters | `only_primary_listing` | `exclude_delisted` |
|---|---|---|---|
| `Equities` | `country, sector, industry_group, industry, currency, exchange, mic, market, market_cap` | ✓ | ✓ default `True` |
| `ETFs` | `category_group, category, family, currency, exchange, mic` | ✓ | ✗ |
| `Funds` | `category_group, category, family, currency, exchange, mic` | ✓ | ✗ |
| `Indices` | `category_group, category, currency, exchange, mic` | ✗ | ✗ |
| `Currencies` | `base_currency, quote_currency` | ✗ | ✗ |
| `Cryptos` | `cryptocurrency, currency` | ✗ | ✗ |
| `Moneymarkets` | `currency, family` | ✗ | ✗ |

**Accepted types:** `str`, `list[str]`, or `None`. A tuple is **not** handled (`isinstance(x, str)`
fails and a tuple is then passed to `isin`, which would work by accident) — **NOT VERIFIED**.
An `int`/`float` would raise `AttributeError` on `.lower()` — **NOT VERIFIED**.

**Hidden cost of validation.** Every validated parameter calls `self.show_options(selection=…)`,
which at `Equities.py:296-307` calls `self.select(...)` again. So each parameter triggers an
extra full-frame copy + boolean pass. Measured: 1 parameter → 0.170 s; 2 parameters → 0.283 s.
With all nine parameters, cost grows ~9×. This is a **correctness-preserving but
performance-hostile** design and it means `select()` latency depends on *how many filters you
name*, not on how selective they are.

## 6.3 `search()` — measured truth table (Equities, 112,690 rows)

| Operation | Input | Expected | **Actual (measured)** | Evidence |
|---|---|---|---|---|
| search | `name="Apple"` | substring, case-insensitive | **OK, 48 rows, 0.064 s** | `helpers.py:150-153` + runtime |
| search | `name="APPLE", case_sensitive=True` | case-sensitive | **OK, 11 rows** ✓ | runtime |
| search | `name="APPLE", case_sensitive="True"` | — | **OK, 11 rows** — the string `"True"` is accepted | `helpers.py:106` |
| search | `name="APPLE", case_sensitive="true"` | ambiguous | **OK, 48 rows ⇒ treated as `False`.** `"true" not in [True,"True"]` ✗ silent misparse | runtime |
| search | `name="APPLE", case_sensitive=1` | ambiguous | **OK, 11 rows ⇒ treated as `True`**, only because `1 == True` in Python ✗ accidental | runtime |
| search | **`symbol="TSLA"`** — *the library's own docstring example* (`helpers.py:90`) | filter by symbol | **OK, returns ALL 112,690 rows** and prints `symbol is not a valid column.` ✗✗ `symbol` is the **index**, not a column | runtime + `helpers.py:90,129-130` |
| search | `nonexistent_column="x"` | error | **OK, returns ALL 112,690 rows**, prints `nonexistent_column is not a valid column.` ✗✗ **FAIL-OPEN** | runtime |
| search | `symbl="AAPL"` *(operator typo)* | 0 rows or error | **OK, returns ALL 112,690 rows** ✗✗ | runtime |
| search | `index="AAPL"` *(the correct parameter)* | AAPL listings | **OK, 12 rows** `['AAPL','AAPL.BA','AAPL.MI','AAPL.MX','AAPL.SN','AAPL.VI','AAPL34.SA','AAPLB.BA','AAPLC.BA','AAPLCL.SN','AAPLD.BA','HARIAAPL.BO']` — note `HARIAAPL.BO` is a **substring false positive** | runtime |
| search | `index="BTC"` | — | **OK, 31 rows** on Equities (regex substring over the index) | runtime |
| search | `index=["AAVE-USD","ETH-USD"]` | exact `isin` on the index | **OK, 0 rows** on Equities (correct — those are crypto symbols); list branch uses `isin`, **not** regex | `helpers.py:118-121` |
| search | `industry="Bank"` (scalar) | substring | **OK, 2,685 rows** → matches `Banks` | runtime |
| search | `industry=["Bank"]` (list) | substring `any()` | **OK, 2,685 rows** → identical; both branches are substring | `helpers.py:131-149` |
| search | `sector="Energy"` | — | **OK, 4,559 rows — of which 473 are `delisted=True`** ✗ | runtime |
| search | `sector="Energy", exclude_delisted=True` | — | **OK, 4,086 rows** — matches `select` exactly | runtime |
| search | *(docstring claim `helpers.py:97-98`: "exclude_delisted … Defaults to True")* | delisted excluded by default | **FALSE.** `helpers.py:126-128` applies it only `if value is True`, and `**kwargs` supplies no default. Measured delta: **+473 delisted rows** | source + runtime |
| search | `exclude_delisted=True` (explicit) | — | **OK, 102,286 rows** ✓ | runtime |
| search | `only_primary_listing=True` | — | **OK, 25,468 rows** (dotless only) | runtime |
| search | `name="AT&T"` | `&` is regex-safe | **OK, 15 rows** | runtime |
| search | `name="C++"` | should be an error or a literal | **OK, 82,603 rows = 73.3% of the database.** Python ≥3.11 parses `C++` as a *possessive quantifier*, and `case=False` matches every name containing `c`/`C` ✗✗ silent semantic explosion | runtime; `re.compile("C++")` succeeds on 3.11 |
| search | `name="(unclosed"` | invalid regex | **`re.error: missing ), unterminated subpattern at position 0`** — **uncaught**, leaks pandas internals ✗ | runtime |
| search | `name="(a+)+$"` | pathological | **OK, 3,968 rows, 0.19 s** + `UserWarning: This pattern is interpreted as a regular expression, and has match groups…` (emitted by pandas at `helpers.py:160`) | runtime |
| search | `name="(a|a)*$"`, `"^(a+)+b$"`, `"(x+x+)+y"` | pathological | **111,574 / 0 / 3 rows in 0.17 / 0.06 / 0.11 s.** **No catastrophic backtracking observed in reviewed scope** | runtime |
| search | `country="United States", sector="Energy"` | AND | **OK, 1,297 rows** (vs `select`'s 1,116 — the delta is delisted rows, since `search` does not exclude them) | runtime |
| search | *(return type)* | — | **`FinanceFrame`** | `helpers.py:155` |
| search | *(determinism)* | identical on repeat | **✓ `a.index.equals(b)` and `a.equals(b)` both `True`** across two identical calls | runtime |
| search | *(mutation isolation)* | caller cannot corrupt source | **✓** dropping 5 rows from the result left `self.data` at 112,690 rows (copy at `helpers.py:103`) | runtime |
| search | *(ordering)* | — | source order preserved; **not** sorted by relevance or score | runtime |

### 6.3.1 The four `search()` defects, ranked by AHOS impact

| # | Defect | Line | AHOS impact |
|---|---|---|---|
| 1 | **Fail-open on unknown columns.** `print()` instead of `raise`; the unfiltered universe is returned. | `helpers.py:129-130` | **Critical.** Violates `UNKNOWN ≠ SAFE` at the API level. A single typo turns a targeted query into "everything matches". There is no status field, no warning object, no way for a caller to detect it programmatically short of capturing stdout. |
| 2 | **Regex by default, unescaped.** Special characters silently change semantics (`C++` → 73.3% of the database) or raise an uncaught `re.error`. | `helpers.py:150-153` | **High.** Untrusted or user-supplied query text is compiled as a regular expression against 112,690 rows. Also **Python-version dependent**: possessive quantifiers exist only in ≥3.11, so `search(name="C++")` behaves differently on 3.10 (declared supported) than on 3.11+. Status: 3.11 **VERIFIED**; 3.10 **PARTIALLY_VERIFIED / inference** (no 3.10 interpreter on the audit host). |
| 3 | **`exclude_delisted` docstring is false.** Default is *not* applied. | `helpers.py:97-98` vs `:126-128` | **High.** `select()` and `search()` return **different populations for the same criteria** (4,086 vs 4,559). Any code that mixes the two will silently include delisted securities. |
| 4 | **`case_sensitive` coercion via `in [True,"True"]`.** `"true"` → False; `1` → True by numeric coincidence. | `helpers.py:106` | **Medium.** Silent, untestable-from-the-outside behaviour flip. |

## 6.4 `show_options()` — three incompatible behaviours

| Call | Returns | Measured |
|---|---|---|
| `Equities().show_options()` | `dict` of **9** keys (`selection_values`) | `['currency','sector','industry_group','industry','exchange','mic','market','country','market_cap']` |
| `Equities().show_options(selection="country")` | 1-D `ndarray` of unique values of the **filtered, non-delisted** frame | **114** values, 0.109 s, `['Afghanistan','Anguilla','Argentina','Australia',…]` |
| `Equities().show_options(selection="bogus")` | — | **`ValueError`** ✓ fail-closed |
| `fd.show_options("equities", use_local_location=True)` | `dict` of **17** keys, read from a **different file** (`categories/equities_categories.gzip`) | `['currency','sector','industry_group','industry','exchange','mic','market','country','state','city','zipcode','market_cap','isin','cusip','figi','composite_figi','shareclass_figi']`, 3.92 s |
| `fd.show_options("bogus")` / `fd.show_options(None)` | — | **`ValueError`** ✓ fail-closed |
| `FinanceDatabase.show_options()` (base, `helpers.py:157-167`) | `self.data.columns` | **dead code** — every subclass overrides it |

Note the base class's `show_options()` and the module-level `fd.show_options()` have the **same
name, different signatures and different return types**. `__init__.py:3` exports the
module-level one, so `fd.show_options` is the function; the method is reachable only through an
instance.

### 6.4.1 Measured drift between the two option sources

| Dimension | `fd.show_options("equities")` (categories file) | `Equities().show_options()` (live data) | only in categories | only in live |
|---|---:|---:|---:|---:|
| `country` | **117** | **114** | **3** | 0 |
| `sector` | 11 | 11 | 0 | 0 |
| `industry_group` | 24 | 24 | 0 | 0 |
| `industry` | 80 | 80 | 0 | 0 |
| `exchange` | 84 | 84 | 0 | 0 |
| `mic` | 71 | 71 | 0 | 0 |
| `currency` | 37 | 37 | 0 | 0 |
| `market_cap` | 6 | 6 | 0 | 0 |
| cryptos `cryptocurrency` | 351 | 351 | 0 | 0 |
| cryptos `currency` | 12 | 12 | 0 | 0 |

**Finding QE-01 — three advertised `country` values are unreachable through `select()`:**

| Phantom value | Rows in data | `delisted` | Symbol |
|---|---:|---|---|
| `Falkland Islands` | 1 | **True** | `ARG.L` |
| `Ivory Coast` | 1 | **True** | `FORE.PA` |
| `Mozambique` | 1 | **True** | `AGTA.L` |

Executed proof:

```
select(country='Falkland Islands')                        -> ValueError: The country 'Falkland Islands' is not available in the database…
select(country='Falkland Islands', exclude_delisted=False) -> ValueError  (same)
select(country='Ivory Coast')                              -> ValueError
select(country='Mozambique')                               -> ValueError
```

**Mechanism (fully established):** the categorization CI job builds `equities_categories.gzip`
from **all** `database/equities/*.csv` rows with `pd.read_csv(..., index_col=0, dtype=str)` and
no `keep_default_na=False` (`database_update.yml:401-410`), i.e. including delisted rows.
`Equities.show_options()` derives its values from `self.select(...)`, which applies
`exclude_delisted=True` **by default** (`Equities.py:236`, `:296-307`), and `select()` validates
user input against *that* list (`Equities.py:84-92`). Therefore:

> the documented, README-featured `fd.show_options("equities")` advertises options that
> `select()` **rejects under every parameter combination**, because the validator itself
> defaults to excluding delisted rows.

This is a self-inconsistency between two generated artifacts of the same pipeline, and it is
**invisible** unless both are compared. It also means the categories file is a **second,
independently generated source of truth** that can drift arbitrarily from the first.

## 6.5 `Cryptos.select()` — measured

| Input | Result |
|---|---|
| `cryptocurrency="SOL"` | **`ValueError`: The cryptocurrency 'SOL' is not available in the database.** |
| `cryptocurrency="sol"` | **`ValueError`** |
| `cryptocurrency="SOL1"` | **OK, 10 rows**, `name` = `Solana CAD`, `Solana CNY`, … |
| `cryptocurrency="BTC"` | **`ValueError`** — Bitcoin is not a token in this database |
| `cryptocurrency="ETH"` | **OK, 5 rows** — Ethereum has only five quote pairs |
| `cryptocurrency="META"` | **OK, 10 rows**, `name` = `Metadium CAD`, … (not Meta Platforms) |
| `cryptocurrency="Metadium"` | **`ValueError`** — names are not accepted, only tickers |
| `currency="USD"` | OK — filters by quote currency |

See [`08_CRYPTOCURRENCY_COVERAGE.md`](08_CRYPTOCURRENCY_COVERAGE.md).

## 6.6 Loading behaviour — measured

| Configuration | Result |
|---|---|
| **Default (remote)** `fd.Cryptos()` | **RAISED `ValueError`: "Failed to load data from https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/cryptos.bz2: HTTPSConnectionPool(host='raw.githubuserconten…"** — because `raw.githubusercontent.com` is unreachable from the audit host (TLS reset, `curl` exit 35). **Fail-closed ✓** — no empty frame, no silent degradation |
| **`use_local_location=True` from a repo checkout** | **OK.** `Equities` 112,690 rows × 21 cols in **4.12 s**; `Cryptos` 3,367 rows in **0.01 s** |
| **`use_local_location=True` from a pip (site-packages) install** | **RAISED `FileNotFoundError: [Errno 2] No such file or directory: '…/site-packages/compression/cryptos.bz2'`** — because `helpers.py:11` resolves to `site-packages/compression`, which does not exist (the sdist excludes it). **Not caught** by the `except requests.exceptions.RequestException` clause, so the raw `FileNotFoundError` escapes |

**Consequence:** a normal `pip install financedatabase` has **exactly one working data path** —
a live HTTPS GET to a mutable `main` branch. There is no offline mode, no cache directory, no
`XDG_DATA_HOME`, no environment variable. The only workarounds are (a) a full repository
checkout imported from its root, or (b) serving the bz2 files over a local HTTP server and
passing `base_url=`. Neither is documented as supported.

For AHOS — whose constraints are $0/month, local-first, and operation under filtering and
sanctions — this is a **structural blocker**, independently of anything else in this report. It
was not predicted from documentation; it was observed.

## 6.7 Determinism, ordering, duplicates, failure behaviour

| Property | Finding | Status |
|---|---|---|
| Determinism of `search()` | Identical index and identical values across repeated calls | **VERIFIED** |
| Determinism of `select()` | Deterministic given the same file; ordering is the file's order | **VERIFIED** |
| Determinism **across time** | **NO.** Data is fetched from mutable `main`; two runs on different days can return different row sets, different option lists and different counts | **VERIFIED** (mechanism), magnitude **UNKNOWN** |
| Ordering | Source order = `sort_values(symbol)` imposed by the compression job (`database_update.yml:322`). Not relevance- or score-ordered | **VERIFIED** |
| Duplicate handling | None needed within an asset class (0 duplicates); **no cross-asset deduplication exists** (`CHAD`) | **VERIFIED** |
| Null handling in `select()` | `.str.lower().isin(...)` — `NaN` never matches, so rows with an empty filter column are silently excluded | **VERIFIED** by source; consequence measured (e.g. `industry` 35.5% empty ⇒ `select(industry=X)` can never return those rows) |
| Null handling in `search()` | `na=False` in `str.contains` — nulls excluded, no error | **VERIFIED** |
| `show_options` null handling | `.dropna()` — a column that is entirely empty returns an empty array, not an error | **VERIFIED** by source |
| Failure on network error | `ValueError`, fail-closed | **VERIFIED (executed)** |
| Failure on missing local file | `FileNotFoundError`, uncaught | **VERIFIED (executed)** |
| Failure on invalid `select` value | `ValueError`, fail-closed | **VERIFIED (executed)** |
| Failure on invalid `search` column | `print` + **full result set**, fail-open | **VERIFIED (executed)** |
| Failure on invalid regex | `re.error`, uncaught | **VERIFIED (executed)** |
| Unsupported filter types (tuple, int, NaN) | Would raise `AttributeError` on `.lower()` or behave accidentally | **NOT VERIFIED** |
| `FinanceFrame` slicing/`groupby` return-type fidelity (no `_constructor` defined) | Unknown | **NOT VERIFIED** |
| Concurrent access from multiple threads | No locks; each instance holds a private copy ⇒ memory multiplies; `pd.read_csv` thread-safety not exercised | **NOT VERIFIED** |
| Behaviour on Python 3.10 (regex possessive quantifiers absent) | Expected divergence for patterns like `C++` | **NOT VERIFIED** — no 3.10 interpreter on the audit host |
| Behaviour on Windows | Path built with `str(file_path) + "/"` (`helpers.py:59,327`); `pathlib` is OS-correct; mixed separators tolerated by Windows APIs | **NOT VERIFIED** — Linux container only |

## 6.8 Performance summary (see [`10_PERFORMANCE_AND_SCALABILITY.md`](10_PERFORMANCE_AND_SCALABILITY.md) for the full environment)

| Operation | Measured |
|---|---|
| `Equities(use_local_location=True)` full load | **4.12 s** |
| `Cryptos(use_local_location=True)` | **0.01 s** |
| `select(country, sector)` ×20 | min **273.6 ms** / median **283.5 ms** / max **340.8 ms** |
| `select()` no-args | **37.7 ms** |
| `search(name="Apple")` ×10 | min **63.9 ms** / median **69.7 ms** / max **72.5 ms** |
| `Equities().show_options()` (all 9) | **505.1 ms** |
| `Equities().show_options(selection="country")` | **98.1 ms** |
| `fd.show_options("equities", local)` | **3.92 s** |
| Peak RSS (Equities + Cryptos) | **209.8 MiB** |
| Peak RSS (all seven assets) | **331.1 MiB** |
| Equities DataFrame deep memory | **214.0 MB** = **14.0×** the 15.29 MB bz2 |

**Indexing: none.** There is no index structure beyond pandas' hash table on the DataFrame
index. Every filter is a full column scan; every validated parameter triggers an additional
full-frame pass through `show_options → select`. Repeated queries are **not** memoised — there
is no cache at any layer, so a "warm" start is only warm in the OS page cache, not in the
library.
