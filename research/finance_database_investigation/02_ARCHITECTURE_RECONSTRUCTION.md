# 02 — Architecture Reconstruction

**Phase 2: source-code forensics.** Every file path, symbol and line range below was read
directly. Nothing is inferred from README examples.

Two versions are distinguished throughout:
- **[R240]** = PyPI release `2.4.0`, sdist/wheel, SHA-256 verified (`evidence/ENVIRONMENT.txt`)
- **[MAIN]** = repo `main` @ `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634` (2026-09-13)

---

## 2.1 Complete file inventory

### [R240] shipped package — 9 modules, ~1,866 lines

| File | Lines | Role |
|---|---:|---|
| `financedatabase/__init__.py` | 10 | Re-exports only |
| `financedatabase/helpers.py` | 358 | Base class, loader, `search`, `FinanceFrame.to_toolkit`, module-level `show_options` |
| `financedatabase/Equities.py` | 316 | `Equities` subclass |
| `financedatabase/ETFs.py` | 244 | `ETFs` subclass |
| `financedatabase/Funds.py` | 239 | `Funds` subclass |
| `financedatabase/Indices.py` | 204 | `Indices` subclass |
| `financedatabase/Currencies.py` | 143 | `Currencies` subclass |
| `financedatabase/Cryptos.py` | 140 | `Cryptos` subclass |
| `financedatabase/Moneymarkets.py` | 122 | `Moneymarkets` subclass |

**Not in the package:** no data files, no `validation/`, no tests, no `compression/`.
`pyproject.toml` `[tool.hatch.build.targets.sdist] include = ["financedatabase/**"]` — so the
sdist deliberately excludes the `database/` and `compression/` trees. The 34 KB wheel is
therefore **code only**; the ~21 MB of data is always remote (or a repo checkout).

### [MAIN] adds

| File | Lines | Role |
|---|---:|---|
| `financedatabase/helpers.py` | 366 | +8 lines: `keep_default_na=False, na_values=[""]` on both `read_csv` calls |
| `financedatabase/validation/__init__.py` | 1 | — |
| `financedatabase/validation/validate_identifiers.py` | 533 | ISIN/CUSIP/FIGI check-digit validation, audit, deterministic repair, CLI |

### Repository (not shipped)

`database/` (145 MB at HEAD; `cryptos.csv`, `currencies.csv`, `indices.csv`, `moneymarkets.csv`,
`equities/` = 85 per-exchange CSVs, `etfs/`, `funds/`) · `compression/` (bz2 artifacts +
`categories/` gzip artifacts + `compression.ipynb` benchmark notebook + `github_exchange_categories.xlsx`)
· `tests/` (10 files, `csv/` and `json/` snapshot dirs) · `.github/workflows/` (3 files) ·
`examples/` · `uv.lock` (428 KB) · `.pre-commit-config.yaml`.

## 2.2 Complete import graph of the shipped package

Enumerated by grep over every `import`/`from` statement in [R240]:

```
stdlib :  io.BytesIO          pathlib.Path          typing.Any
3rd    :  numpy               pandas                requests
lazy   :  financetoolkit.Toolkit      ← imported INSIDE to_toolkit() only (helpers.py:240)
internal:  __init__ → helpers, Cryptos, Currencies, Equities, ETFs, Funds, Indices, Moneymarkets
          each asset module → helpers.FinanceDatabase, helpers.FinanceFrame
```

**Proves:** the package's own runtime needs exactly `numpy + pandas + requests`.
**Does not prove:** that those are declared — they are **not** in `requires_dist`. The only
declared dependency is `financetoolkit`, which is the one thing the code imports *lazily*.
This is an inverted dependency declaration (see §9.2).

**Executed proof:** with `financedatabase` installed `--no-deps` into an isolated venv and
`financetoolkit` absent, `import financedatabase as fd` **succeeded** and all seven asset
classes loaded data and answered queries. `FinanceFrame.to_toolkit()` raised
`ImportError: To use the 'to_toolkit' functionality, it requires installation of the
FinanceToolkit …`. So `financetoolkit` is functionally optional and declaration-mandatory.

## 2.3 `helpers.py` — the whole architecture in one file

### 2.3.1 Constants (`helpers.py:11-22`)

```python
file_path = Path(__file__).parent.parent / "compression"                      # :11
DATA_REPO = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/")  # :12-14
HEADERS   = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) …Chrome/58.0.3029.110…"} # :18-22
```

| Constant | What it proves | What it does NOT prove |
|---|---|---|
| `file_path` (:11) | Local mode expects a `compression/` directory **two levels above the module**, i.e. the *repository root*, not the package directory. | It does **not** work for a normal `pip install`: `Path(site-packages/financedatabase/helpers.py).parent.parent == site-packages`, and `site-packages/compression` does not exist because the sdist excludes it. **Executed proof:** `fd.Cryptos(use_local_location=True)` from a site-packages install raised `FileNotFoundError: [Errno 2] No such file or directory: '…/site-packages/compression/cryptos.bz2'`. |
| `DATA_REPO` (:12-14) | The data host, owner, repo and **branch (`main`)** are compile-time constants. Data is mutable and unpinnable through the public API. | It does not prove the content is authentic — there is no checksum, signature, ETag or size guard anywhere. |
| `HEADERS` (:18-22) | Every request spoofs a Chrome 58 / Windows 10 browser User-Agent. | It does not prove a ToS problem, but it does mean traffic is not self-identifying, and the spoofed string is hardcoded to *Windows* regardless of the actual OS. |

### 2.3.2 `class FinanceDatabase` (`helpers.py:25-167`) — base controller

`FILE_NAME = ""` (:37) is the only per-class hook for loading. Each subclass sets it:
`equities.bz2`, `etfs.bz2`, `funds.bz2`, `indices.bz2`, `currencies.bz2`, `cryptos.bz2`,
`moneymarkets.bz2`.

**`__init__(base_url=DATA_REPO, use_local_location=False)` — `helpers.py:39-79`**

```python
the_path = str(file_path) + "/" if use_local_location else base_url      # :59
the_path += self.FILE_NAME                                               # :60
try:
    if use_local_location:
        self.data = pd.read_csv(the_path, compression="bz2", index_col=0)          # :63 [R240]
    else:
        response = requests.get(the_path, headers=HEADERS, timeout=60)             # :65
        response.raise_for_status()                                                # :66
        self.data = pd.read_csv(BytesIO(response.content), compression="bz2",
                                index_col=0)                                       # :68-72 [R240]
except requests.exceptions.RequestException as error:
    raise ValueError(f"Failed to load data from {the_path}: {str(error)}.\n"
                     "Ensure you are able to access the file. …")                  # :73-79
```

| Property | Value | Line | Evidence |
|---|---|---|---|
| Eagerly loads the **entire** asset class at construction | Yes | 63/68 | source |
| Reads whole HTTP body into memory (`response.content`) before parsing | Yes — no streaming, no `iter_content` | 68-69 | source |
| Compression | `bz2`, explicitly | 63/70 | source |
| Index | `index_col=0` → the first CSV column (`symbol`) becomes the DataFrame **index**, not a column | 63/71 | source + measured (`eq.data.columns` has 21 entries for a 22-column CSV) |
| Timeout | 60 s connect+read | 65 | source |
| Retries | **None** | — | absence |
| Caching (disk or in-process) | **None.** No module-level cache, no `functools.lru_cache`, no ETag. Every instantiation re-fetches and re-parses | — | absence, confirmed by grep |
| Integrity verification | **None** — no SHA, no signature, no content-type or size check | — | absence |
| Failure mode on network error | `ValueError` with an actionable message → **fail-closed** | 73-79 | source + **executed**: in this sandbox `raw.githubusercontent.com` is unreachable and `fd.Cryptos()` raised `ValueError: Failed to load data from https://raw.githubusercontent.com/…/cryptos.bz2: HTTPSConnectionPool(host='raw.githubuserconten…` |
| Failure mode on a *local* path that is missing | `FileNotFoundError` — **not** caught by the `except RequestException` clause, so it propagates raw | 62-63 | source + **executed** (§2.3.1) |
| `base_url` override | Accepted, but only ever passed to `requests.get` → it must be an HTTP(S) URL. A filesystem path in `base_url` cannot work | 41, 65 | source |
| Concurrency control | **None.** No locks; `self.data` is per-instance, so N instances = N full copies in RAM | — | absence |
| NA semantics **[R240]** | pandas defaults → the strings `NA`, `NaN`, `NULL`, `N/A`, `none`, … are parsed as missing. **This destroys the ticker `NA` (Nano Labs).** | 63/68 | **Executed**: same file, two semantics → release semantics give `1` NaN in the index, `'NA' in index → False`, `.loc['NA'] → KeyError`; `main` semantics give `0` NaN and `'NA' in index → True`. Cell-level NaN counts were **identical** — only the index is affected. |
| NA semantics **[MAIN]** | `keep_default_na=False, na_values=[""]` → only the empty string is missing | diff hunk at :60-77 | source diff |

**`search(**kwargs)` — `helpers.py:81-155`** — full behavioural analysis in
[`06_QUERY_ENGINE_AUDIT.md`](06_QUERY_ENGINE_AUDIT.md). Structurally:

```
:103   data_filter = self.data.copy()                       # shallow-ish copy of the frame
:105-109  case_sensitive = bool(kwargs["case_sensitive"] in [True, "True"])
:111   for key, value in kwargs.items():
:112-117     only_primary_listing → keep rows whose INDEX has no "."   (regex r"\.", na=False)
:118-125     index → list ⇒ isin(value);  str ⇒ index.str.contains(value, na=False)   # REGEX
:126-128     exclude_delisted → applied ONLY IF value is True AND "delisted" in columns
:129-130     elif key not in data_filter.columns:  print(f"{key} is not a valid column.")   # ← FAIL OPEN
:131-149     elif isinstance(value, list):  substring any() match, case-folded
:150-153     else:  data_filter[key].str.contains(value, case=case_sensitive, na=False)     # ← REGEX
:155   return FinanceFrame(data_filter)
```

The four structural defects, each **executed**:

1. **Fail-open on unknown columns (:129-130).** `print` instead of `raise`. An invalid filter
   silently yields the *unfiltered universe*. `eq.search(symbl="AAPL")` → 112,690 rows.
2. **`exclude_delisted` has no default (:126-128).** The docstring at :97-98 says
   "Defaults to True." The code applies it only if the caller passes `True`. Since `search`
   uses bare `**kwargs` there is no default injection. Measured: `search(sector="Energy")`
   returns 4,559 rows of which **473 are delisted**, while `select(sector="Energy")` returns
   4,086. **The docstring is false.**
3. **Regex by default (:150-153).** pandas `str.contains` defaults to `regex=True` and the
   value is not escaped. `name="(unclosed"` raises an uncaught `re.error`. `name="C++"`
   returns **82,603 rows (73.3% of the database)** because Python ≥3.11 treats `C++` as a
   possessive quantifier and `case=False` matches every name containing `c`.
4. **`case_sensitive` coercion (:106).** `bool(x in [True,"True"])` means `"true"` → `False`
   (measured: 48 rows, the case-insensitive answer) while `"True"`, `True` and `1` → `True`
   (measured: 11 rows). `1` works only because `1 == True` in Python.

**`show_options(self)` — `helpers.py:157-167`.** The base implementation returns
`self.data.columns` and its docstring warns that subclasses override it. **Every** subclass
does override it, so the base body is dead code in practice.

### 2.3.3 `class FinanceFrame(pd.DataFrame)` — `helpers.py:170-277`

A pandas subclass whose single addition is `to_toolkit()`. Full analysis in §9. Notable
structural points:

- `:238-247` lazy `from financetoolkit import Toolkit` inside a `try/except ImportError`.
- `:248-255` if `api_key is None`, `print()` a multi-line notice that includes an **affiliate
  link** (`https://www.jeroenbouma.com/fmp`, "15% off") — i.e. a marketing side-effect on a
  library call path.
- `:257` `symbols = self[self.index.notna()].index.to_list()` — silently **drops NaN index
  entries**, which is exactly what happens to the ticker `NA` under [R240] semantics.
- `:259-275` constructs `Toolkit(...)` forwarding 14 parameters, including
  `benchmark_ticker="SPY"` and `risk_free_rate="10y"` defaults.
- Subclassing `pd.DataFrame` without defining `_constructor` is fragile; **not tested here**
  (we did not exercise slicing/`groupby` return types). Status: **NOT VERIFIED**.

### 2.3.4 `show_options(selection, base_url, use_local_location)` — `helpers.py:280-358`

A **module-level** function, entirely separate from the method of the same name:

```python
:307-315  selection_values = ["equities","etfs","funds","indices","currencies","cryptos","moneymarkets"]
:316-325  raise ValueError if selection is None or not in selection_values      # fail-CLOSED ✓
:327-328  the_path  = (local dir or base_url) + f"/categories/{selection}_categories.gzip"
:331-344  read_csv(compression="gzip", index_col=0, low_memory=False)
:345-351  except RequestException -> ValueError                                 # fail-CLOSED ✓
:353-356  return {index: categories_df.loc[index].dropna().to_numpy() for index in categories_df.index}
```

Two observations:

- `:327-328` concatenates onto a `base_url` that already ends in `/`, producing a
  **double slash** (`…/compression//categories/equities_categories.gzip`). It works on
  `raw.githubusercontent.com` (verified by the project's own CI and docs) but it is sloppy
  URL construction and would break on a stricter host or a path-normalising proxy.
- It reads a **different file** from the asset classes. That file is generated by a different
  CI job with **different `read_csv` options**, which produces a measurable divergence —
  see §6.4 (`country`: 117 advertised vs 114 reachable).

## 2.4 The seven asset-class subclasses

All seven follow an identical template. `Equities.py` is the fullest; the rest are strict
subsets.

| Class | File | `FILE_NAME` | `select()` parameters | `show_options()` `selection_values` | `exclude_delisted` param | `only_primary_listing` param |
|---|---|---|---|---|---|---|
| `Equities` | `Equities.py:8-316` | `equities.bz2` (:21) | `country, sector, industry_group, industry, currency, exchange, mic, market, market_cap` (:25-33) | `currency, sector, industry_group, industry, exchange, mic, market, country, market_cap` (:278-288) | **Yes**, default `True` (:35) | **Yes** (:34) |
| `ETFs` | `ETFs.py:8-244` | `etfs.bz2` (:23) | `category_group, category, family, currency, exchange, mic` | `currency, category_group, category, family, exchange, mic` (:212-218) | No | Yes (:157) |
| `Funds` | `Funds.py:8-239` | `funds.bz2` (:21) | `category_group, category, family, currency, exchange, mic` | same set (:208-214) | No | Yes (:151) |
| `Indices` | `Indices.py:8-204` | `indices.bz2` (:22) | `category_group, category, currency, exchange, mic` | `category_group, category, currency, exchange, mic` (:175-180) | No | **No** |
| `Currencies` | `Currencies.py:8-143` | `currencies.bz2` (:20) | `base_currency, quote_currency` | `base_currency, quote_currency` (:123) | No | **No** |
| `Cryptos` | `Cryptos.py:8-140` | `cryptos.bz2` (:25) | `cryptocurrency, currency` (:29-30) | `cryptocurrency, currency` (:120) | No | **No** |
| `Moneymarkets` | `Moneymarkets.py:8-122` | `moneymarkets.bz2` (:20) | `currency, family` | `currency, family` (:105) | No | **No** |

**The `select()` template** (identical in all seven; `Equities.py:81-206` shows nine copies):

```python
equities = self.data.copy(deep=True)                                   # :77
if exclude_delisted: equities = equities[~equities["delisted"]]         # :79-80  (Equities only)
if country:
    countries       = [country] if isinstance(country, str) else country
    countries_lower = [c.lower() for c in countries]
    options_lower   = [o.lower() for o in self.show_options(selection="country")]   # :84-86
    for cl, ca in zip(countries_lower, countries):
        if cl not in options_lower:
            raise ValueError(f"The country '{ca}' is not available in the database. …")  # :89-92
    equities = equities[equities["country"].str.lower().isin(countries_lower)]           # :93
… repeat for each parameter …
if only_primary_listing:
    only = equities[~equities.index.str.contains(r"\.", na=False)]      # :208-211
    if only.empty: print("No primary listings found. Returning all …")  # :213-217  ← FAIL-OPEN fallback
    else: equities = only
return FinanceFrame(equities)                                           # :222
```

| Property | Proven by | Note |
|---|---|---|
| Matching is **exact** (`isin`), case-insensitive | `Equities.py:93` and 8 siblings | Not substring. Measured: `select(industry="Bank")` → `ValueError` because only `Banks` exists. |
| Values are **validated** against live options → `ValueError` | `Equities.py:87-92` | **Fail-closed** — the correct posture, and the opposite of `search()`. |
| Combination is **AND** across parameters, **OR** within a list | `:93`, `:106`, … chained boolean masks; `isin(list)` | Measured: `country="United States" AND sector="Energy"` → 1,116 rows; `country=["United States","Canada"]` → 34,455. |
| Validation is computed from **live data**, per call | `:84-86` calls `self.show_options(selection=…)`, which at `:296-307` calls `self.select(...)` | **Recursion into a full-frame pass for every parameter.** Measured cost: 1 param 0.17 s → 2 params 0.283 s. Cost scales with parameter count, not with selectivity. |
| Deep copy per call | `:77` `copy(deep=True)` | Safe against caller mutation (measured) but expensive: 214 MB frame copied per `select()`. |
| `only_primary_listing` is a **syntactic heuristic** on the symbol | `:210` `index.str.contains(r"\.")` | Not a data field. There is no `is_primary` column anywhere. Measured consequences in §5.4 and §6.3. |
| `only_primary_listing` **fails open when empty** | `:213-217` | If the filter would return nothing it prints a notice and returns **everything** matching the other criteria. A caller cannot distinguish "no primary listings" from "primary listings returned". |
| `show_options(selection=…)` returns unique values of a **filtered** frame | `:296-316` | `dropna().sort_values().unique()` — so `NaN`-only columns silently yield an empty array rather than an error. |
| No regex, no fuzzy matching, no pagination, no `limit` | absence | The full result set is always materialised. |

## 2.5 `validation/validate_identifiers.py` **[MAIN only, 533 lines]**

Public API (from the source's own `def`/`class` listing):

```
:20  class IdentifierIssue      (path, line, symbol, field, value, reason, actionable, replacement)
:34  class AuditResult          (issues, files_scanned, identifiers_checked, relationships_checked)
:44  class CleanupResult        (.changed -> int at :51)
:56  _validate_standard_number(...)
:71  validate_isin(value) -> str | None            # ISO 6166 check digit
:80  validate_cusip(value) -> str | None
:89  validate_figi(value) -> str | None            # OpenFIGI check digit
:98  validate_isin_cusip_consistency(isin, cusip)  # US/CA: ISIN must embed the CUSIP
:109 cusip_from_authoritative_isin(isin)           # middle 9 characters
:117 isin_precludes_cusip(isin)
:140 _canonical_value(field, value)
:148 _repair_cusip_from_isin(...)
:166 repair_identifier(field, value, row_values)   # deterministic repair only
:181 discover_csv_files(paths)
:201 audit_identifiers(paths) -> AuditResult
:293 _replace_csv_field(record, field_index, replacement)
:319 apply_identifier_cleanup(path) -> CleanupResult
:403 build_parser() -> ArgumentParser              # paths*, --apply, --report-file
:494 main(argv=None) -> int
```

Design properties worth noting (all read from source):

- **Checksums are genuinely implemented** for all three identifier families, plus a
  cross-field ISIN↔CUSIP consistency rule for US/CA ISINs, with the ISIN treated as
  authoritative because "the CUSIP is just its middle 9 characters" (CONTRIBUTING:59-61).
- **Repairs are restricted to deterministic evidence** (`repair_identifier` handles case,
  surrounding whitespace, and Excel float damage like `US0378331005.0` / `194162103.0`).
  Anything ambiguous is classified `actionable=False` → *review-only*, never auto-fixed.
  This is exactly the epistemic discipline AHOS requires, and it is the strongest positive
  finding in the whole codebase.
- The CLI defaults to **read-only audit**; mutation requires an explicit `--apply`.
- It operates on `database/*.csv` via the stdlib `csv` module, preserving row order and
  formatting — not via pandas — so it cannot introduce dtype damage.

**We executed it** (read-only, no `--apply`) against the project's own `database/` tree:

```
Checked 249085 populated identifiers and 14804 US/Canadian ISIN-CUSIP pairs in 137 CSV
files; found 2 invalid values (0 repairable, 0 removable, 2 review-only) and 0 consistency
issues.
```

The two findings (`evidence/identifier_issues.csv`):

| file | line | symbol | field | value | problem | actionable |
|---|---:|---|---|---|---|---|
| `database/equities/NMS.csv` | 5316 | `QVCGB` | cusip | `74915L301` | checksum mismatch | False |
| `database/equities/PNK.csv` | 5982 | `KMGH` | cusip | `483325109` | checksum mismatch | False |

**Interpretation:** of the identifiers that are *populated*, 249,083 / 249,085 (**99.9992%**)
are internally valid. The identifier problem in this dataset is **coverage, not correctness**
(§5.3). This is a materially more precise statement than "the identifiers are unreliable",
and it is the kind of distinction AHOS doctrine demands.

Also executed: `tests/test_validate_identifiers.py::test_database_identifiers_have_no_actionable_issues`
→ **1 passed**, emitting `UserWarning: 2 identifier finding(s) require manual review …`. This
explains why CI deselects it from the main job into its own `validate-identifiers` job
(`testing.yml:34`, `:54-57`) — it is a warn-don't-fail check by design.

## 2.6 Tests and CI (what is verified, and what is not)

`tests/`: `conftest.py` (20,017 B — includes a snapshot-comparison harness credited to
OpenBB Terminal at lines 14-22), `test_equities.py` (12,332 B), `test_validate_identifiers.py`
(10,878 B), `test_invariants.py` (5,042 B), `test_etfs.py`, `test_funds.py`, `test_cryptos.py`,
`test_currencies.py`, `test_indices.py`, `test_moneymarkets.py`, plus `tests/csv/` and
`tests/json/` snapshot directories per asset class.

`test_invariants.py` defines four genuine invariants:

| Test | Lines | Invariant |
|---|---|---|
| `test_equities_read_rewrite_is_byte_identical` | :14-49 | The workflow's read→rewrite must be a no-op for untouched files; explicitly asserts `"NA" in equities.index` (:35) — the Nano Labs regression guard |
| `test_no_symbol_collisions_across_asset_classes` | :66-100 | A `symbol` must belong to at most one asset class. Docstring: "almost always a data-quality bug … This invariant catches such drift before it lands on `main`." |
| `test_no_isin_collisions_across_asset_classes` | :103-122 | An `isin` must not appear in both equities and etfs |
| `test_delisted_is_strictly_boolean` | :125-140 | `delisted` must be real `bool`, because `select()` uses `~equities["delisted"]` |

`conftest.py:34-45` documents the categorization skip-columns and which assets are split
per-exchange, and states it "Must stay in sync with the `Update-Categorization-Files` job" —
an explicit, human-maintained coupling between test fixtures and CI YAML.

`.github/workflows/`: `database_update.yml` (29,385 B), `testing.yml` (1,518 B), `linting.yml` (954 B).

**Executed result of the project's own suite** (isolated venv, repo cwd, commit `a174c97d`):

```
FAILED tests/test_invariants.py::test_no_symbol_collisions_across_asset_classes
E   AssertionError: Symbols appear in more than one asset-class file:
E       equities <-> etfs: ['CHAD'] (1 total)
1 failed, 85 passed, 1 deselected in 46.44s
```

**The invariant test that exists specifically to stop this from landing on `main` is failing
on `main`.** The mechanism (CI does not run on bot commits) is in §3.5 and §7.

## 2.7 Architecture map (reconstructed from code, not from docs)

```
                        ┌──────────────────────────────────────────────┐
                        │  PyPI: financedatabase 2.4.0  (34 KB wheel)  │
                        │  9 modules · no data · no validation/        │
                        └───────────────────────┬──────────────────────┘
                                                │ import
   ┌────────────────────────────────────────────▼───────────────────────────────────────────┐
   │ __init__.py  →  helpers.show_options  +  7 asset classes                               │
   │                                                                                        │
   │  helpers.FinanceDatabase (base)                                                        │
   │    FILE_NAME hook ──► __init__(): requests.get(DATA_REPO + FILE_NAME, timeout=60)      │
   │                          │                     ▲                                       │
   │                          │            raw.githubusercontent.com/JerBouma/              │
   │                          │            FinanceDatabase/**main**/compression/*.bz2       │
   │                          ▼            (no checksum · no cache · no pin · no retry)     │
   │                     pd.read_csv(bz2, index_col=0)  →  self.data (in-RAM DataFrame)     │
   │                                                                                        │
   │    search(**kwargs)   : substring/REGEX · unvalidated · FAIL-OPEN (print + all rows)   │
   │    show_options()     : base = self.data.columns  (always overridden)                  │
   │                                                                                        │
   │  7 subclasses: select(...) exact+validated+ValueError (FAIL-CLOSED)                    │
   │                show_options(selection=...) → unique() of the filtered frame            │
   │                                                                                        │
   │  helpers.FinanceFrame(pd.DataFrame)                                                    │
   │    .to_toolkit(api_key=…) ──lazy import──► financetoolkit.Toolkit                      │
   │                                              └──► FinancialModelingPrep (key) OR Yahoo  │
   │                                                                                        │
   │  helpers.show_options(selection)  ──► compression/categories/<sel>_categories.gzip     │
   │                                        (a DIFFERENT file, a DIFFERENT CI job,          │
   │                                         DIFFERENT read_csv options → measurable drift) │
   └────────────────────────────────────────────────────────────────────────────────────────┘

   ┌── repo-only, not shipped ──────────────────────────────────────────────────────────────┐
   │ database/*.csv  (145 MB, 85 per-exchange equity files)  ← source of truth              │
   │   ▲  written weekly by .github/workflows/database_update.yml                           │
   │   │   upstream: raw.githubusercontent.com/rreichel3/US-Stock-Symbols (US only,         │
   │   │             NO LICENSE, commits titled "generated")                                │
   │ compression/*.bz2, compression/categories/*.gzip  ← generated from database/           │
   │ financedatabase/validation/validate_identifiers.py  ← [MAIN only] ISO/FIGI checksums   │
   │ tests/ (86 tests)  ← run on PRs and human pushes; NOT run on bot data commits          │
   └────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2.8 What the architecture does **not** contain (verified by absence)

Confirmed by grep across the shipped package and by reading every module:

- No caching layer, no on-disk store, no SQLite/parquet/pickle path
- No background thread, no `asyncio`, no scheduler, no polling
- No logging (`logging` is never imported; all diagnostics are `print`)
- No metrics, no tracing, no health check
- No retry/backoff, no circuit breaker, no rate limiting
- No checksum, signature, ETag or version manifest
- No abstraction for alternate providers — `DATA_REPO` is a module constant
- No `Protocol`/ABC/interface layer; the base class is concrete
- No incremental/delta loading — always the full asset class
- No price, volume, market-cap *value*, fundamental, or time-series concept anywhere
- No security/honeypot/liquidity/holder concept anywhere
- No chain or contract-address concept anywhere
