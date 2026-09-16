# 10 — Performance & Scalability

**Phase 10.** All numbers below were **measured**, not estimated. No benchmark is invented.
Where a benchmark could not be run, the reason is stated.

---

## 10.1 Measurement environment (mandatory context)

| Property | Value |
|---|---|
| Host | Arena.ai agent sandbox — a **Linux container**, *not* the designated AHOS Windows host |
| OS / kernel | Linux 6.1.158+ x86_64 |
| CPU | 2 cores |
| RAM | 3,939 MB total |
| Python | 3.11.2 |
| pandas | **3.0.5** |
| numpy | 2.4.6 |
| requests | 2.34.2 |
| `financetoolkit` | **not installed** (deliberate; see §9.3) |
| `financedatabase` | 2.4.0 wheel, installed `--no-deps`, plus repo-root import for local-data mode |
| Data | `compression/*.bz2` at commit `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634` (generated 2026-09-13) |
| Measured | 2026-09-15 |
| Disk state | Files read from a local sparse clone; OS page cache warm after the first read |

> **Every number in this document is contingent on this environment.** A 2-core container with
> 4 GB RAM is not a Windows laptop and not a production host. Per AHOS doctrine
> (*"Agent-host capability ≠ Designated AHOS Windows-host capability"*), **none of these figures
> may be used to size an AHOS deployment.** They establish *orders of magnitude and mechanism*,
> nothing more.

## 10.2 Dataset size

| File | bz2 size | Rows | Fields | Bytes/row (compressed) |
|---|---:|---:|---:|---:|
| `equities.bz2` | **15.29 MB** | 112,690 | 22 | 136 B |
| `funds.bz2` | 1.85 MB | 57,853 | 9 | 32 B |
| `etfs.bz2` | 1.28 MB | 36,481 | 10 | 35 B |
| `indices.bz2` | 1.19 MB | 91,181 | 8 | 13 B |
| `currencies.bz2` | 0.05 MB | 2,556 | 6 | 18 B |
| `cryptos.bz2` | **0.03 MB** | 3,367 | 7 | 10 B |
| `moneymarkets.bz2` | 0.02 MB | 1,367 | 6 | 15 B |
| **Total distributed** | **21.6 MB** | **304,495** | | |
| Source of truth `database/` (not distributed) | **145 MB** | — | — | plain CSV, 137 files |
| Full repository | **~4.85 GB** (`size: 5088317` KB) | — | — | includes history |

Note the asymmetry that matters for AHOS: the **crypto** file is 33 KB — 0.15% of the
distributed payload and 0.07% of the source-of-truth tree. The effort and bytes in this project
are overwhelmingly in traditional equities.

## 10.3 Load and initialization

| Operation | Measured | Notes |
|---|---:|---|
| `pd.read_csv(equities.bz2, compression="bz2", index_col=0)` | **4.17 s** | bz2 decompression dominates; single-threaded |
| `fd.Equities(use_local_location=True)` end-to-end | **4.12 s** | ≈ the raw read; the class adds no overhead |
| `pd.read_csv(funds.bz2)` | 0.84 s | |
| `pd.read_csv(indices.bz2)` | 0.63 s | |
| `pd.read_csv(etfs.bz2)` | 0.62 s | |
| `pd.read_csv(currencies.bz2)` | 0.02 s | |
| `pd.read_csv(cryptos.bz2)` | **0.01 s** | |
| `fd.Cryptos(use_local_location=True)` | **0.01 s** | |
| `fd.show_options("equities", use_local_location=True)` | **3.92 s** | reads the 810 KB categories gzip |
| **Import time** (`import financedatabase as fd`) | **not separately measured** | Trivial by inspection: 10-line `__init__.py`, no data loaded at import; **VERIFIED** that import performs no I/O and no network call |
| **Remote cold start** | **COULD NOT BE MEASURED** | `raw.githubusercontent.com` is unreachable from this host (TLS reset, `curl` exit 35). The download half of cold start is therefore **UNVERIFIED**. It must be measured on the AHOS Windows host before any conclusion about real-world startup cost |

**Cold vs warm start.** There is **no caching layer of any kind** in the library — no disk cache,
no module-level memoization, no `functools.lru_cache`, no ETag/`If-Modified-Since`. Verified by
grep and by reading `helpers.py:39-79` in full. Therefore:

- A "warm" start is warm only in the **OS page cache**, not in the library.
- Every `fd.Equities()` construction in every process re-decompresses and re-parses 15.29 MB.
- Constructing `Equities()` twice in one process pays the full 4.1 s twice and holds two copies.
- Over the network, every construction re-downloads 15.29 MB.

## 10.4 Memory

| Measurement | Value |
|---|---:|
| `Equities` DataFrame, `memory_usage(deep=True).sum()` | **214.0 MB** |
| Expansion factor vs the 15.29 MB bz2 | **14.0×** |
| Peak RSS after loading Equities + Cryptos | **209.8 MiB** |
| Peak RSS after loading all seven asset classes | **331.1 MiB** |
| Peak RSS in a single-asset (equities) session | 234.3 MiB |
| dtypes observed (pandas 3.0.5) | `str` × 20, `bool` × 1 — **zero** `object` columns |

**Scaling implications for AHOS:**

1. A ~215 MB resident frame is **large for a 4 GB host** and would compete directly with an
   active soak process. On the designated AHOS Windows host this must be re-measured —
   **NOT VERIFIED** here.
2. Memory scales **per instance**, not per process. `ProviderRouter`-style patterns that
   construct adapters per call would multiply this. There are no locks and no shared state, so
   concurrency is "safe" only in the sense that it is *unsynchronised and memory-multiplying*.
3. Every `select()` does `self.data.copy(deep=True)` (`Equities.py:77`) — a **second ~215 MB
   allocation per call**, transient. With nine filter parameters each triggering a nested
   `show_options → select`, peak transient allocation is materially higher than steady state.
   We did not instrument peak transient RSS during a nine-parameter `select()`: **NOT VERIFIED**.

## 10.5 Query latency

| Operation | min | median | max | n |
|---|---:|---:|---:|---:|
| `select(country="United States", sector="Energy")` | **273.6 ms** | **283.5 ms** | **340.8 ms** | 20 |
| `search(name="Apple")` | **63.9 ms** | **69.7 ms** | **72.5 ms** | 10 |
| `select()` (no arguments — full deep copy) | — | **37.7 ms** | — | 1 |
| `Equities().show_options(selection="country")` | — | **98.1 ms** | — | 1 |
| `Equities().show_options()` (all nine dimensions) | — | **505.1 ms** | — | 1 |
| `select(country="Netherlands")` | — | **183 ms** | — | 1 |
| `select(country="United States", sector="Energy")` (single shot) | — | **283 ms** | — | 1 |
| `search(nonexistent_column="x")` → returns all 112,690 rows | — | **15 ms** | — | 1 |

**Why `select()` is slower than `search()` despite doing less work.** Each validated parameter
calls `self.show_options(selection=…)`, which calls `self.select(…)` again
(`Equities.py:84-86, 296-307`). So an *n*-parameter `select()` performs roughly *n* extra
full-frame passes. Measured confirmation: one parameter ≈ 170–183 ms, two parameters ≈ 283 ms.
Cost scales with **the number of filters named**, not with result size or selectivity. This is
the single most important performance property of the query engine, and it is a design
consequence, not a data-size consequence.

**Repeated-query behaviour:** identical queries return identical results and cost the same each
time — there is no memoization. Determinism was verified explicitly (§6.3).

## 10.6 Indexing, concurrency, serialization

| Property | Finding | Status |
|---|---|---|
| Indexing | **None** beyond pandas' hash table on the DataFrame index. Every column filter is a full scan. No inverted index, no categorical dtype, no precomputed bitmap | **VERIFIED** (source) |
| Use of pandas `category` dtype | **None** — all columns are `str`, despite `sector` having 11 values and `market_cap` having 6. A categorical encoding would cut the 214 MB substantially | **VERIFIED** — an obvious, unexploited optimization |
| Concurrent access | No locks, no shared mutable state, no thread-safety guarantees. Each instance holds a private frame ⇒ N threads = N × 215 MB | **VERIFIED** (source); **NOT TESTED** under real concurrency |
| Repeated-query behaviour | No caching; identical cost each time | **VERIFIED** |
| Cache behaviour | **No cache exists** at any layer | **VERIFIED** |
| Serialization cost | Not applicable in the shipped path — data is never written by the library. There is no `to_pickle`, `to_parquet`, `save` or `dump` method anywhere | **VERIFIED** (grep) |
| Deserialization | `pd.read_csv(..., compression="bz2")` only. **No pickle** — deliberately rejected for security (`compression/README.md`) | **VERIFIED** |
| Failure behaviour under load | Not tested (no load harness in scope) | **NOT VERIFIED** |

## 10.7 Platform and version compatibility

| Dimension | Finding | Status |
|---|---|---|
| **Windows paths** | `helpers.py:11` uses `pathlib.Path` → OS-correct. But `:59` and `:327` concatenate with a hardcoded forward slash: `str(file_path) + "/"` and `the_path += f"/categories/…"`, yielding e.g. `C:\…\compression//categories/equities_categories.gzip`. Windows APIs and pandas tolerate mixed separators, so this is **low risk but sloppy**. No `os.sep`, no `Path` joining at those two sites | **INFERENCE** from source; **NOT VERIFIED** on Windows |
| **Windows line endings / encoding** | The bz2 files are UTF-8 with `\n`. Verified content includes non-ASCII (`Börslich handelbare Krügerrand`, `S.p.A.`, `Crédit Agricole`). `pd.read_csv` is called **without** an explicit `encoding` → it relies on the platform default. On a Windows host with a non-UTF-8 locale this is a **real risk** | **PARTIALLY_VERIFIED** — non-ASCII content confirmed present; failure mode **NOT TESTED** |
| **Long paths** | 85 per-exchange CSVs in `database/equities/`; the distributed path is a single flat file per asset class, so no deep-path exposure at runtime | **VERIFIED** |
| **Python version** | Declares `>=3.10,<3.16`; classifiers list 3.10–3.14. **Tested here on 3.11.2 only.** Behavioural divergence is *known* at 3.10 vs 3.11+: possessive regex quantifiers (`C++`) exist only in ≥3.11, so `search(name="C++")` returns 82,603 rows on 3.11 and would raise `re.error` on 3.10 | 3.11 **VERIFIED**; 3.10 **NOT VERIFIED** (no 3.10 interpreter on the audit host) |
| **pandas version** | Tested on **3.0.5**. `financetoolkit 2.2.0` requires `pandas>=3.0`, but CI tests against `pandas 2.3.3`. So the package is exercised on pandas 2 and shipped to users on pandas 3 | **VERIFIED** (metadata + `uv.lock`); pandas 2.x behaviour **NOT TESTED** by us |
| **32-bit / low-memory hosts** | A 214 MB deep-memory frame plus a transient deep copy per `select()` makes this unsuitable for constrained hosts | **INFERENCE** |

## 10.8 What could not be benchmarked, and why

| Benchmark | Why not run |
|---|---|
| **Remote download latency / cold start over the network** | `raw.githubusercontent.com` is unreachable from the audit host (TLS reset). This is the *most* important number for AHOS and it is **UNVERIFIED**. It must be measured on the designated AHOS Windows host, from the actual deployment network, including under any filtering/proxy in force |
| **Windows-host timings** | Linux container only. Per AHOS doctrine, Linux validation ≠ Windows validation |
| **Python 3.10 behaviour** | No 3.10 interpreter available in the sandbox |
| **pandas 2.x behaviour** | Only pandas 3.0.5 installed; installing 2.x would have required a second venv and changes no finding |
| **Real concurrency (threads/processes)** | Out of scope for a read-only investigation; no thread-safety contract exists to test against |
| **`to_toolkit()` end-to-end latency** | Requires installing `financetoolkit` + `yfinance` + `scikit-learn` and making live calls to Yahoo/FMP. That would add a network dependency to the research venv, and any resulting number would measure **FinanceToolkit and the external provider, not FinanceDatabase** — which the tasking forbids attributing |
| **Peak transient RSS during a nine-parameter `select()`** | Not instrumented |
| **Load-shedding / backpressure behaviour** | No such mechanism exists to test |

## 10.9 Summary judgment

| Question | Answer |
|---|---|
| Is it fast enough for interactive research? | **Yes** on a workstation — 4 s to load equities, 60–290 ms per query. Acceptable for a human analyst |
| Is it fast enough for an automated cycle? | **No, not as designed.** A ~70 s AHOS cycle cannot absorb a 4.1 s cold parse per asset class per cycle with no cache — and over a network it would be worse and unverifiable from here |
| Is it memory-appropriate for the AHOS host? | **Unknown — must be re-measured on Windows.** 215 MB resident plus a transient deep copy per call is significant against a 4 GB reference host |
| Is the query engine indexed? | **No.** Full scans, plus a nested full-frame pass per validated filter |
| Is there a cache? | **No — at any layer.** This is the single largest scalability defect |
| Would it scale to more asset classes or larger data? | Linearly in memory and parse time, with no mechanism to avoid re-paying either. A 10× larger equities file means a ~2 GB resident frame |
