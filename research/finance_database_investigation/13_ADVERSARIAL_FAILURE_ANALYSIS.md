# 13 — Adversarial Failure Analysis

**Phase 13.** Each of the twenty scenarios in the tasking is assessed against **actual evidence**.
For every scenario: failure mechanism · evidence · impact · detectability · mitigation · whether
AHOS should fail closed · whether the data should be rejected · whether the record should become
`UNKNOWN`.

Severity scale: **CRITICAL** (silently produces a wrong answer) · **HIGH** (produces a wrong
answer that is detectable only with effort) · **MEDIUM** (degrades quality) · **LOW** (cosmetic).

The distinguishing property of this dataset is that **most of its failures are silent**. There is
no status field, no warning object, no confidence value, no logging (the library never imports
`logging`) and no exception on the dangerous paths. Diagnostics are `print()` to stdout.

---

## S-01 · Same symbol, different instrument — **CRITICAL, LIVE**

| | |
|---|---|
| **Failure mechanism** | `symbol` is the primary key within an asset class but **not** across classes, and bare tickers are not unique within a class either |
| **Evidence (live, at HEAD)** | `CHAD` exists in **both** `equities` (*DeFi Development Corp. Variable Rate Series C Perpetual Preferred Stock*, `NMS`) and `etfs` (*Direxion Daily CSI 300 China A Share Bear 1X Shares*, `PCX`). Reproduced by running the project's own suite: `FAILED tests/test_invariants.py::test_no_symbol_collisions_across_asset_classes … equities <-> etfs: ['CHAD'] (1 total)` |
| **Also** | `MMM` → **3M Company** (`MMM`, NYQ, ISIN `US88579Y1010`) *and* **Marley Spoon AG** (`MMM.AX`, ASX, no ISIN) — 18 listings under one bare ticker. `BRK.AX` = **Brookside Energy Ltd** (AU), `BRK.L` = **Brooks Macdonald Group plc** (UK), neither related to Berkshire |
| **Impact** | A join on symbol merges unrelated instruments. Note the irony: the equity side of `CHAD` is a *crypto-adjacent* company, so an AHOS crypto↔TradFi bridge keyed on symbol would collide on exactly the kind of entity it most wants to find |
| **Detectability** | **Low by default.** Nothing at load or query time reports it. Detectable only by an explicit cross-asset set intersection — which the project does have as a test, but which **does not run on data commits** (0 check-runs on `a174c97d`) |
| **Mitigation** | Namespace every key: `fdb:<asset_class>:<symbol>`. Run a cross-asset collision check on every ingest and refuse the snapshot if it is non-empty |
| **AHOS should fail closed?** | **YES** — any multi-asset join must be rejected, not best-effort |
| **Reject the data?** | Reject the *snapshot* if collisions > 0 (the project's own invariant says such a state is a bug) |
| **Record → `UNKNOWN`?** | Both colliding records → `IdentityState.CONFLICT` with the full candidate list |

## S-02 · Same company, multiple listings — **HIGH, BY DESIGN**

| | |
|---|---|
| **Mechanism** | 112,690 equity rows resolve to 74,690 distinct bare tickers; 16,251 bare tickers appear more than once. This is correct modelling of multi-venue listing — but there is **no issuer entity** to group them |
| **Evidence** | `MMM` ×18, `AIR` ×17, `HAL` ×17, `SAP` ×16, `AMD` ×15, `MRK` ×15, `CTO` ×14, `EMR` ×14. ISIN `FR0013269123` (Rubis) → **57** distinct symbols |
| **Impact** | Any count of "companies" from row counts is inflated ~1.5×. Any per-company aggregate computed by grouping on `name` is wrong (`name` has 47,578 lowercase duplicates, 257 rows = `ISHARES`, 129 = `two`) |
| **Detectability** | **Medium** — the FIGI hierarchy (`shareclass_figi` 29,164 unique / `composite_figi` 41,131 / `figi` 58,232) permits grouping, but only for the **52–57%** of rows where it is populated |
| **Mitigation** | Group on `composite_figi` where present; emit `UNKNOWN` issuer where absent. Never group on `name` |
| **Fail closed?** | Yes for issuer-level aggregation without a FIGI |
| **Reject?** | No — reject the *aggregation method*, not the rows |
| **→ `UNKNOWN`?** | Issuer identity `UNKNOWN` for the 43–48% of rows without a FIGI |

## S-03 · Missing identifiers — **CRITICAL, STRUCTURAL**

| | |
|---|---|
| **Mechanism** | Identifier columns exist but are mostly empty; and new tickers are created with **all five identifiers `NaN` and are never revisited** |
| **Evidence** | Coverage: `isin` 27.0%, `cusip` 24.2%, `figi` 52.0%, `composite_figi` 54.0%, `shareclass_figi` 56.8%; ETFs `isin` 21.7%; **funds / indices / currencies / cryptos / money markets: 0% — no identifier columns at all**. Root cause in code: `build_new_ticker` sets `isin/cusip/figi/composite_figi/shareclass_figi = np.nan` (`database_update.yml:153-157`), and the refresh guard `if len(fd_data) == 0 and …` (`:230`) is unreachable for existing rows, so nothing ever fills them in. Measured footprint: **7,425 equity rows (6.59%)** have `isin`, `cusip`, `figi` **and** `summary` all empty simultaneously |
| **Impact** | For ~half the equities and ~78% of ETFs there is **no** identifier-based resolution path. For five of seven asset classes there is **none at all**. Identity reduces to the bare symbol |
| **Detectability** | **High if you look** (a coverage query is trivial), **zero if you don't** — an empty cell is not an error |
| **Mitigation** | Emit `UNKNOWN` explicitly for every absent identifier; never coalesce to `""`, `None` or a plausible default. Report coverage per snapshot as a quality metric |
| **Fail closed?** | **YES** for any identity-resolution step that requires an identifier |
| **Reject?** | No — reject *reliance*, not the record |
| **→ `UNKNOWN`?** | **Yes, always.** `UNKNOWN ≠ SAFE` applies directly |
| **Note** | Where identifiers **are** populated they are excellent: the project's own validator found **2 invalid values in 249,085** (99.9992% valid) |

## S-04 · Stale records — **CRITICAL, UNDETECTABLE FROM THE DATA**

| | |
|---|---|
| **Mechanism** | No timestamp column exists in any of the seven schemas; non-US data has no automated maintenance |
| **Evidence** | Column-name scan for `date\|time\|updated\|asof\|timestamp\|snapshot\|version\|source\|provider\|retrieved` → **`NONE` for all seven**. README:467: *"When companies outside American exchanges undergo changes (migrations, mergers, bankruptcies), we depend on community members to identify and update these entries."* The crypto table has **no update job at all** |
| **Impact** | A record's age is unknowable from the record. `STALE ≠ LIVE` cannot be *enforced* — it can only be *assumed* |
| **Detectability** | **Impossible from the data.** Only at file level, from the git commit date of the artifact |
| **Mitigation** | Synthesize `retrieved_ts` at ingest and `source_ts` from the pinned commit date; mark every record `IdentityState.STALE` unless the snapshot is inside a declared window; never surface a FinanceDatabase value as current |
| **Fail closed?** | **YES** — staleness must be assumed, not disproved |
| **Reject?** | Reject any use as *current* state |
| **→ `UNKNOWN`?** | Freshness → `UNKNOWN`; the value itself may still be usable as a *historical* reference |

## S-05 · Delisted instruments — **MEDIUM (a strength with a trap)**

| | |
|---|---|
| **Mechanism** | Delisted rows are **retained deliberately** (10,404 of 112,690 equities) — good for survivorship bias, bad if a consumer assumes every row is tradable |
| **Evidence** | `delisted` value counts: `False` 102,286, `True` 10,404. README:465: *"Delisted tickers are intentionally retained for historical research purposes."* `test_delisted_is_strictly_boolean` guards the dtype. **Only equities have the flag** — open issue **#153** (2026-06-03) asks for ETFs and Funds |
| **Trap** | `select()` excludes delisted **by default** (102,286 rows); `search()` does **not** (4,559 vs 4,086 for `sector="Energy"` — a 473-row delta). Two APIs, two populations, same criteria |
| **Impact** | Mixing `select` and `search` silently changes the population. For ETFs/funds/indices/cryptos there is **no way** to exclude delisted because the flag does not exist |
| **Detectability** | Medium — only by comparing the two APIs |
| **Mitigation** | Always pass `exclude_delisted` explicitly; for the six classes without the flag, treat liveness as `UNKNOWN` |
| **Fail closed?** | Yes for any "is this tradable" question |
| **→ `UNKNOWN`?** | Liveness `UNKNOWN` for all non-equity asset classes |

## S-06 · Reused symbols — **UNKNOWN (mechanism verified, no instance found)**

| | |
|---|---|
| **Mechanism** | Symbols are the primary key with no epoch, no `valid_from`/`valid_to` and no prior-holder record. A recycled symbol would collide with the historical row and be resolved by `keep='first'` |
| **Evidence** | `database_update.yml:260` `equities = equities[~equities.index.duplicated(keep='first')]`. The survivor depends on `sorted(glob('database/equities/*.csv'))` filename order — i.e. on **exchange-code alphabetical order**, not on data quality |
| **Impact** | A historical row could silently represent a different modern instrument |
| **Detectability** | **None** from the data — no temporal dimension to compare |
| **Mitigation** | Do not rely on symbol stability across snapshots; diff snapshots by commit and treat disappeared/reappeared symbols as suspect |
| **Fail closed?** | Yes for any historical attribution |
| **→ `UNKNOWN`?** | Yes, for any claim that a symbol refers to the same instrument over time. Status of this scenario: **UNKNOWN** (U-16) |

## S-07 · Duplicate records — **CRITICAL, LIVE**

| | |
|---|---|
| **Mechanism** | Two symbol conventions for the same share class are ingested from the same upstream feed and assigned **different hardcoded exchange codes** |
| **Evidence (measured)** | `BRK-A` → Berkshire Hathaway Inc., `NYQ`; `BRK/A` → Berkshire Hathaway Inc., **`ASE`**; `BRK-B` → `NYQ`; `BRK/B` → **`ASE`**; `BRKA.VI` → `VIE`. **Four rows for two share classes, with contradictory venue attribution, and `isin` empty on every one of them.** Mechanism: `database_update.yml:169/175/181` assigns `NMS`/`ASE` wholesale, and `:185` `pd.concat`s three feeds without keys |
| **Impact** | Double counting; contradictory `exchange`/`market` for one instrument; and because `only_primary_listing` keys on the presence of a `.`, **all four survive** the "primary listings only" filter |
| **Detectability** | Low — requires grouping by `shareclass_figi` (empty here) or fuzzy name matching |
| **Mitigation** | Deduplicate on `(name, country)` + identifier where available; treat `/` and `-` share-class variants as one candidate set and emit `CONFLICT` |
| **Fail closed?** | **YES** |
| **Reject?** | Reject one of the pair only with an explicit, logged rule — never by position |
| **→ `UNKNOWN`?** | `IdentityState.CONFLICT` (which for AHOS is a non-actionable state) |

## S-08 · Incorrect country — **HIGH, LIVE**

| | |
|---|---|
| **Mechanism** | `country` is the **issuer/HQ country**, not the listing jurisdiction, and it is not validated against the listing venue |
| **Evidence (measured)** | 29,984 rows have `country='United States'`; **19,413** of them trade on non-US venue codes (`PNK` 4,627, `FRA` 2,953, `STU` 2,516, `BER` 2,083, `MUN` 1,804, `DUS` 1,114, …). Most of those are legitimate secondary listings — **but 14 rows with a `.SZ` (Shenzhen) suffix are labelled `country='United States'`**, which is not legitimate. Separately, **129 rows have `name == 'two'`** spread across `000851.SZ`, `002447.SZ`, `046110.KQ`, `0JUZ.L`, `0OFR.IL`, `0YW.BE`, all labelled `country='United States'` and `industry='Diversified Financial Services'` |
| **Impact** | Any geo-filtered logic — sanctions screening, jurisdictional risk, regional exposure, currency-hedging assumptions — is unreliable. For AHOS's Iran/local-first context, a jurisdiction field that can be wrong in both directions is a **compliance hazard**, not merely a data-quality one |
| **Detectability** | Medium — requires cross-checking `country` against `mic`/`exchange` |
| **Mitigation** | Derive *listing* jurisdiction from `mic` (ISO 10383) and treat `country` as an HQ **hint** with `confidence=LOW`. Never use `country` for any compliance or sanctions decision |
| **Fail closed?** | **YES** — emphatically, for any jurisdiction-sensitive path |
| **Reject?** | Reject the field for compliance use; keep it as a low-confidence hint |
| **→ `UNKNOWN`?** | Jurisdiction → `UNKNOWN` unless corroborated by MIC |

## S-09 · Incorrect industry — **HIGH, STRUCTURAL**

| | |
|---|---|
| **Mechanism** | Sector and industry group for new tickers are **imputed by statistical mode**, not classified |
| **Evidence** | `database_update.yml:87` `return subset['industry_group'].mode()[0] if not subset.empty else np.nan` and `:113` the same for `sector`. Called from `build_new_ticker` (`:134-135`). No confidence, no "inferred" flag, no record that inference occurred. Additionally `industry` is empty for **35.54%** of equities and the taxonomy is **80 industries vs GICS's 69**, i.e. an approximation (CONTRIBUTING:129: *"loosely approximate … completely done through manual curation"*). And the CI job that validates the GICS triple is **failing** on the 2026-09-13, 09-11 and 09-06 runs |
| **Impact** | An imputed-by-popularity classification is indistinguishable in the data from a curated one. Errors propagate: each new row becomes evidence for the next row's mode |
| **Detectability** | **Very low** — no flag distinguishes inferred from curated |
| **Mitigation** | Treat all classification as `confidence=LOW`, source `INFERRED_OR_CURATED_UNKNOWN`. Do not use it as ground truth for any taxonomy-driven decision |
| **Fail closed?** | Yes for any decision keyed on classification |
| **→ `UNKNOWN`?** | Classification provenance → `UNKNOWN` |

## S-10 · Missing currency — **MEDIUM**

| | |
|---|---|
| **Mechanism** | Empty cells plus non-ISO codes |
| **Evidence (measured)** | Equities `currency` empty for **2,137 rows (1.90%)**; indices **18.88%**; ETFs 0.28%; funds 0.44%; cryptos 7 rows. **Non-ISO value: `ILA` appears in 560 equity rows while `ILS` appears in exactly 1** — `ILA` is not an ISO 4217 code (the Israeli new shekel is `ILS`) |
| **Impact** | FX conversion, exposure aggregation and any currency-consistency check break or silently skip rows. `select(currency=…)` can never return a row whose currency is empty (`.str.lower().isin(...)` does not match NaN) |
| **Detectability** | **High** — trivial to detect if checked; **zero** if not |
| **Mitigation** | Validate against the ISO 4217 list on ingest; map `ILA`→`ILS` **only** with an explicit, logged rule; otherwise `UNKNOWN` |
| **Fail closed?** | Yes for any monetary computation |
| **→ `UNKNOWN`?** | Currency → `UNKNOWN` where empty or non-ISO |

## S-11 · Empty metadata — **HIGH**

| | |
|---|---|
| **Mechanism** | Large, uneven emptiness across every descriptive field |
| **Evidence (measured)** | Equities: `state` **71.63%** empty, `zipcode` 43.26%, `website` 40.94%, `city` 38.18%, `industry` 35.54%, `market_cap` 32.27%, `summary` 10.85%. Indices: `mic` **59.80%**, `summary` **53.07%**, `category` 24.72%, `currency` 18.88%, `name` **17.19%**. Money markets: `summary` **49.45%**, `family` 39.58%, `name` 11.56%. Funds: `mic` **54.76%**, `family` 36.43%. ETFs: `isin` **78.26%**, `category` 37.65% |
| **Also** | Placeholder corruption: 129 rows named `two`; 1,774 names with trailing whitespace; 19 symbols with internal whitespace including `'ECC           '` (11 trailing spaces); 4 symbols with leading/trailing whitespace |
| **Impact** | A query filtered on a sparse field silently returns a small, biased subset. **91,181 indices of which 15,677 have no name** cannot be presented to an operator |
| **Detectability** | High if measured per column; zero otherwise |
| **Mitigation** | Compute and record per-column population rates at ingest; refuse to emit records whose *display-critical* fields are empty; trim and normalize all text |
| **Fail closed?** | Yes for presentation and for any field-specific filter |
| **→ `UNKNOWN`?** | Every empty field → `UNKNOWN`, never `""` |

## S-12 · Changed exchange codes — **HIGH, LIVE**

| | |
|---|---|
| **Mechanism** | `exchange` values are **assigned by the pipeline**, not observed, and the assignment is wrong for one whole feed |
| **Evidence** | `database_update.yml:175-176`: `nyse['exchange'] = 'ASE'; nyse['market'] = 'NYSE MKT'` — the **NYSE** dataset is labelled with the **NYSE American/AMEX** code. Measured: all **1,128** `ASE` rows carry exactly one `market` value (`NYSE MKT`) and all **7,058** `NMS` rows carry exactly one (`NASDAQ Global Select`) — zero variance, the signature of assignment. Separately `exchange → mic` is strictly 1:1 (0 violations) but `mic → exchange` has **4 violations**: `OTCM`→7 codes, `XNAS`→3, `XLON`→2, `XNSE`→2; and 3 exchange codes have **no** MIC |
| **Impact** | Venue-based filtering, venue-based identity, and MIC↔exchange joins are all unreliable. `BRK/A` vs `BRK-A` (§S-07) is a direct product of this |
| **Detectability** | Medium — the zero-variance signature is detectable if you look for it |
| **Mitigation** | Prefer `mic` (ISO 10383) over `exchange` where populated; treat `market` as a label, never as a fact; treat the 8,186 `NMS`/`ASE` rows as venue-`UNKNOWN` |
| **Fail closed?** | Yes for venue-sensitive logic |
| **→ `UNKNOWN`?** | Venue → `UNKNOWN` for the hardcoded population |

## S-13 · Dataset update regression — **CRITICAL, LIVE, ALREADY SHIPPED**

| | |
|---|---|
| **Mechanism** | The **released code** and the **served data** are versioned independently, and their parsing semantics have diverged |
| **Evidence (executed)** | Release 2.4.0 `helpers.py:63` uses `pd.read_csv(path, compression="bz2", index_col=0)`; `main` adds `keep_default_na=False, na_values=[""]`. Reading the **same** `equities.bz2` both ways: **release semantics → 1 NaN in the index, `'NA' in index` = `False`, `.loc['NA']` → `KeyError`; main semantics → 0 NaN, `'NA' in index` = `True`.** Cell-level NaN counts were identical, so the damage is confined to the index. The workflow's own comment (`:200-202`) records that this exact bug *"dropped that row on every run"*. `FinanceFrame.to_toolkit()` compounds it: `self[self.index.notna()]` (`:257`) silently discards NaN index entries |
| **Second regression** | The equities count moved from the **158,429** still advertised on the official website to the **112,690** in the data and in the auto-generated README — a **29% reduction**, consistent with the global `keep='first'` dedupe at `:260`. Mechanism **VERIFIED**; the specific commit was **not** bisected (**INFERENCE**, U-14) |
| **Third regression** | `Check-GICS-Categorisation` **failing** on three consecutive runs while the data continued to be committed and pushed |
| **Impact** | Every `pip install financedatabase==2.4.0` user **today** silently loses the ticker `NA` (Nano Labs) and would lose any other symbol pandas treats as NA-like (`NA`, `N/A`, `NULL`, `NaN`, `none`, …). No error is raised |
| **Detectability** | **Very low.** It requires comparing release code against `main` code and then measuring both against the same file — which is exactly what this investigation did and what no ordinary consumer would do |
| **Mitigation** | Never rely on the library's loader. Read a **pinned snapshot** with **AHOS's own** parser and explicit `keep_default_na=False, na_values=[""]`; assert the expected row count and column list; verify a per-file SHA-256 |
| **Fail closed?** | **YES** |
| **Reject?** | **Reject the release's loader path entirely** |
| **→ `UNKNOWN`?** | Any record whose key was subject to NA-coercion → `UNKNOWN` |

## S-14 · External provider unavailable — **CRITICAL, MEASURED**

| | |
|---|---|
| **Mechanism** | The only supported data path is a live HTTPS GET to `raw.githubusercontent.com`. There is no cache, no fallback, no bundled data |
| **Evidence (executed)** | In the audit sandbox, `raw.githubusercontent.com` fails at the TLS layer (`curl` exit 35, `OpenSSL SSL_connect: SSL_ERROR_SYSCALL`) while `github.com`, `api.github.com`, `codeload.github.com` and `files.pythonhosted.org` all return HTTP 200. Consequently `fd.Cryptos()` raised `ValueError: Failed to load data from https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/cryptos.bz2: HTTPSConnectionPool(host='raw.githubuserconten…` |
| **Partial credit** | The failure is **fail-closed** — `raise_for_status()` + `except RequestException → ValueError` (`helpers.py:66,73-79`). No empty frame, no silent degradation. That is the correct posture and it is **VERIFIED** |
| **Impact** | In any network where that host is filtered, throttled or blocked, FinanceDatabase is **100% non-functional**. For AHOS — $0/month, local-first, operating under filtering and sanctions — this is a **structural blocker**, measured rather than predicted |
| **Detectability** | Immediate and loud (an exception). Good |
| **Mitigation** | Vendor a pinned snapshot; make the network path optional and never on the critical path |
| **Fail closed?** | Already does |
| **Reject?** | **Reject as a runtime dependency** |

## S-15 · Network unavailable — **CRITICAL, MEASURED**

Same evidence as S-14, plus:

- **No offline mode for a pip install.** `use_local_location=True` resolves to
  `Path(__file__).parent.parent / "compression"` (`helpers.py:11`), i.e. `site-packages/compression`,
  which does not exist because `pyproject.toml` `[tool.hatch.build.targets.sdist] include =
  ["financedatabase/**"]` excludes it. **Executed proof:** `FileNotFoundError: [Errno 2] No such
  file or directory: '…/site-packages/compression/cryptos.bz2'` — and it is **not** caught by the
  `except requests.exceptions.RequestException` clause, so the raw `FileNotFoundError` escapes.
- **`base_url` cannot be a filesystem path** — it is only ever passed to `requests.get`.
- **No retries, no backoff, no circuit breaker.** One attempt, 60 s timeout, then `ValueError`.
- Workarounds exist (a full repo checkout imported from its root — which is what the project's own
  CI does — or serving the bz2 files from a local HTTP server and passing `base_url`), but neither
  is documented as supported.

**AHOS: fail closed. Reject as a runtime dependency.** An offline-capable AHOS component cannot
depend on this.

## S-16 · Windows path issues — **LOW–MEDIUM, NOT VERIFIED**

| | |
|---|---|
| **Mechanism** | Mixed separator construction and no explicit encoding |
| **Evidence (source)** | `helpers.py:59` `the_path = str(file_path) + "/"` and `:327-328` `the_path += f"/categories/{selection}_categories.gzip"` — producing e.g. `C:\…\compression//categories/equities_categories.gzip`. `file_path` itself uses `pathlib` (OS-correct). `pd.read_csv` is called **without** an explicit `encoding`, so it relies on the platform default while the data contains non-ASCII (`Börslich handelbare Krügerrand`, `S.p.A.`, `Crédit Agricole`) |
| **Impact** | Mixed separators are tolerated by Windows APIs and pandas, so the path risk is **low**. The **encoding** risk is more real: on a Windows host with a non-UTF-8 active code page, default-encoding reads of UTF-8 content can raise `UnicodeDecodeError` or silently mojibake |
| **Detectability** | High if it happens (an exception or visibly wrong text) |
| **Status** | **NOT VERIFIED** — the audit host is Linux. Per AHOS doctrine, *Linux validation ≠ Windows validation*; this must be re-tested on the designated AHOS Windows host before any Windows conclusion is drawn |
| **Mitigation** | If ever consumed on Windows: build paths with `pathlib`, pass `encoding="utf-8"` explicitly, and test with a non-UTF-8 locale |
| **Fail closed?** | Yes on any decode error |

## S-17 · Package version incompatibility — **HIGH, VERIFIED**

| | |
|---|---|
| **Mechanism** | Contradictory Python floors across the dependency graph, plus a tested configuration that differs from the installed one |
| **Evidence** | `financedatabase 2.4.0` declares `requires-python = ">=3.10,<3.16"`; `financetoolkit 2.2.0` (2026-08-18) declares `>=3.11,<3.16` and requires **`pandas>=3.0`**, `scikit-learn>=1.6`, **`yfinance` (unpinned)**. `financetoolkit 2.1.3` (2026-06-27) is the last to allow 3.10. `uv.lock:592-597` pins **`financetoolkit 2.0.7`** and **`pandas 2.3.3`** for `<3.11`, and CI runs **Python 3.10** (`testing.yml:27`). AHOS pins `pandas>=2.1.0` in `requirements.txt` |
| **Impact** | (a) On Python 3.10 the resolver must backtrack to financetoolkit ≤2.1.3; on ≥3.11 it takes 2.2.0 and forces **pandas 3.0** — a major-version bump over AHOS's floor, with observable dtype changes (this audit saw `str` dtype on 20 columns and **zero** `object` columns under pandas 3.0.5). (b) **The 86 passing CI tests exercise financetoolkit 2.0.7 + pandas 2.3.3, which no current `pip install` reproduces.** (c) `numpy`, `pandas` and `requests` are imported but **undeclared**, so their versions are governed entirely by a transitive dependency |
| **Detectability** | At install time (a resolver conflict) or at import time (a dtype surprise) |
| **Mitigation** | Do not install it. If a snapshot is ever vendored, parse it with AHOS's existing `pandas>=2.1` and declare nothing new |
| **Fail closed?** | Yes — refuse to install into the AHOS environment |
| **Reject?** | **Reject as a dependency** |

## S-18 · Schema changes — **HIGH, ALREADY OBSERVED**

| | |
|---|---|
| **Mechanism** | No schema contract is asserted on load, and the schema **has** changed between releases |
| **Evidence** | The official website's sample `select()` output shows **19 columns with no `mic` and no `delisted`**; the current schema has **22 including both**. `conftest.py:38-45` lists `manager_name`/`manager_bio` in the funds skip-set, but those columns are **absent** from the current funds schema — fixture/schema drift. Release 2.4.0's wheel has **no `validation/` subpackage** while `main` does, and `main`'s `helpers.py` differs by 8 lines. There is **no** schema-version field, no expected-column assertion and no migration path |
| **Impact** | A served file that gains, loses or renames a column is accepted silently. `Equities.py:80` (`equities["delisted"]`) would raise `KeyError` if that column vanished; a renamed `country` would make every `select(country=…)` raise `ValueError` from the validator. Neither failure names the real cause |
| **Detectability** | Only via an exception after the fact |
| **Mitigation** | Assert the exact expected column list and row-count range on every ingest; reject on mismatch with an explicit `SCHEMA_MISMATCH` status |
| **Fail closed?** | **YES** |
| **Reject?** | Reject any snapshot whose schema does not match the pinned expectation |

## S-19 · Unexpected nulls — **HIGH**

| | |
|---|---|
| **Mechanism** | Three different null conventions interact: empty CSV cells, the literal string `"nan"` written by `np.nan` in the pipeline, and pandas' NA inference |
| **Evidence** | `build_new_ticker` writes `np.nan` into 11 fields (`:139,148-157`), which serialize as the literal text `nan` in CSV. `database_update.yml:196-202` documents that pandas previously coerced `"NA"` (the Nano Labs ticker) to NaN and mangled `"9763"`→`"9763.0"` and `"031162100"`→`"31162100.0"`. Measured under release-2.4.0 read semantics: **1 NaN in the equities index**. Measured with `keep_default_na=False`: 0. Under the library's own loader, `isin` for all `BRK*` rows reads back as NaN |
| **Impact** | A literal `"nan"` string and a true NaN are indistinguishable to a naive consumer; `str.contains(..., na=False)` silently drops them; `isin` never matches them; `.notna()` filters in `to_toolkit()` discard them without notice |
| **Detectability** | Medium — requires dtype and value inspection |
| **Mitigation** | Read with explicit `dtype=str, keep_default_na=False, na_values=[""]` (AHOS's own parser, not the library's); map empty → `UNKNOWN`; assert that no index value is NaN |
| **Fail closed?** | **YES** |
| **→ `UNKNOWN`?** | Every null → `UNKNOWN`, explicitly |

## S-20 · Misleading cryptocurrency coverage — **CRITICAL**

| | |
|---|---|
| **Mechanism** | The class is *named* `Cryptos`, the project *advertises* "Cryptocurrencies" as an asset class with "352 Categories", and the row count (3,367) looks substantial — but the content is a ~2020-era Yahoo/CryptoCompare **pair** list with no on-chain dimension whatsoever |
| **Evidence** | Seven columns only: `symbol, name, cryptocurrency, currency, summary, exchange, website`. **Absent by explicit existence check:** `chain`, `network`, `contract`, `address`, `contract_address`, `platform`, `token_id`, `decimals`, `launch_date`, `first_seen`, `market_cap`, `price`, `volume`, `liquidity`. 3,367 rows = **352 tickers × 9.57 quote pairs**. `exchange='CCC'` (CryptoCompare) on 3,362 rows. **`SOL` absent** (`select(cryptocurrency="SOL")` → `ValueError`); Solana present only as **`SOL1`**. **`BTC` absent as a token** (present only as a quote currency, 113 rows). **51 of 73** probed modern tokens absent, including **every** Solana-ecosystem token and **every** memecoin. Chain exists only as prose in `summary` (`'ethereum'` 606 rows, `'solana'` **10**, `'arbitrum'` **0**, `'base'` **0**). 26 tickers carry Yahoo collision suffixes, and **`COMP1` is CompoundCoin, not Compound**. `SRM` (Serum, collapsed 2022) is still present with no delisting flag. **No CI job writes `database/cryptos.csv`** — there is no update mechanism at all |
| **Impact** | A superficial integration would conclude "FinanceDatabase covers cryptocurrencies" and wire it into a crypto pipeline. It would then find no Solana tokens, no contracts, no liquidity, no prices and no new listings — and would report `UNKNOWN` for everything, or worse, would silently produce empty candidate lists that look like "no opportunities" rather than "no capability" |
| **Detectability** | High **if** you inspect the schema; **zero** if you trust the asset-class name |
| **Mitigation** | **Exclude the `cryptos` asset class from any AHOS crypto path entirely.** AHOS already has DexScreener, GeckoTerminal, Pump.fun, GoPlus, RugCheck, CoinGecko, DefiLlama, Jupiter and mempool — all of which strictly dominate this table |
| **Fail closed?** | **YES** |
| **Reject?** | **REJECT the crypto subsystem outright** |
| **→ `UNKNOWN`?** | Every crypto-derived field → `UNKNOWN`; and AHOS must distinguish "no opportunities found" from "this source cannot find opportunities" |

---

## 13.1 Consolidated severity table

| # | Scenario | Severity | Live instance observed? | AHOS fail closed? | Record → `UNKNOWN`? |
|---|---|---|---|---|---|
| S-01 | Same symbol, different instrument | **CRITICAL** | **YES** (`CHAD`, `MMM`, `BRK`) | Yes | `CONFLICT` |
| S-02 | Same company, multiple listings | HIGH | Yes (by design) | Yes for aggregation | Issuer `UNKNOWN` w/o FIGI |
| S-03 | Missing identifiers | **CRITICAL** | Yes (73–78% empty; 0% for 5 classes) | Yes | **Always** |
| S-04 | Stale records | **CRITICAL** | Yes (no timestamps at all) | Yes | Freshness `UNKNOWN` |
| S-05 | Delisted instruments | MEDIUM | Yes (10,404 rows; API divergence) | Yes | Liveness `UNKNOWN` off-equities |
| S-06 | Reused symbols | **UNKNOWN** | Mechanism yes, instance not found | Yes | Yes |
| S-07 | Duplicate records | **CRITICAL** | **YES** (`BRK-A`/`BRK/A`, `BRK-B`/`BRK/B`) | Yes | `CONFLICT` |
| S-08 | Incorrect country | HIGH | **YES** (14 `.SZ` rows; 129 `two` rows) | Yes | Jurisdiction `UNKNOWN` |
| S-09 | Incorrect industry | HIGH | Yes (`.mode()[0]` imputation; GICS job failing) | Yes | Provenance `UNKNOWN` |
| S-10 | Missing currency | MEDIUM | Yes (2,137 empty; `ILA`×560) | Yes for money maths | `UNKNOWN` |
| S-11 | Empty metadata | HIGH | Yes (up to 78% per column) | Yes | Per field |
| S-12 | Changed exchange codes | HIGH | **YES** (8,186 hardcoded; NYSE→`ASE`) | Yes | Venue `UNKNOWN` |
| S-13 | Dataset update regression | **CRITICAL** | **YES** (ticker `NA` lost on release 2.4.0 today) | Yes | Yes |
| S-14 | External provider unavailable | **CRITICAL** | **YES** (measured TLS failure) | Already fails closed | Reject as runtime dep |
| S-15 | Network unavailable | **CRITICAL** | **YES** (no offline mode for pip installs) | Yes | Reject as runtime dep |
| S-16 | Windows path issues | LOW–MED | **NOT VERIFIED** (Linux host) | Yes | Retest on Windows |
| S-17 | Package version incompatibility | HIGH | **YES** (py3.10 vs financetoolkit 2.2.0; pandas 2 vs 3) | Yes | Reject as dependency |
| S-18 | Schema changes | HIGH | **YES** (website schema ≠ current; `validation/` absent from release) | Yes | Reject on mismatch |
| S-19 | Unexpected nulls | HIGH | **YES** (three null conventions) | Yes | Every null |
| S-20 | Misleading crypto coverage | **CRITICAL** | **YES** (`SOL` absent; no chain/address/price) | Yes | **Reject outright** |

**8 of 20 scenarios are CRITICAL. 18 of 20 have a live, observed instance in the data at HEAD.**
Only S-06 (symbol recycling) and S-16 (Windows behaviour) lack an observed instance — the first
because it is undetectable without a temporal dimension, the second because the audit host is
Linux.

**The meta-finding:** FinanceDatabase's failure mode is not that it produces errors — it is that
it produces **plausible-looking answers with no error**. `search()` returns the whole universe on
a typo. `select(country="China", only_primary_listing=True)` silently discards 87.6% of Chinese
listings including primary ones. The library never imports `logging`; all diagnostics are
`print()`. There is no status field, no confidence value and no warning object anywhere in the
API. **AHOS must supply all of that structure itself, or not consume this data at all.**
