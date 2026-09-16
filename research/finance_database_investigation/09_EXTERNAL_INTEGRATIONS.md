# 09 — Finance Toolkit / External Integration Audit

**Phase 9.** The tasking requires a strict separation of capability between FinanceDatabase,
FinanceToolkit, external providers, and AHOS. Nothing below attributes another component's
capability to FinanceDatabase.

---

## 9.1 How the integration is implemented

There is exactly **one** integration point in the entire package: `FinanceFrame.to_toolkit()`,
`helpers.py:179-277`.

```python
class FinanceFrame(pd.DataFrame):                                  # :170
    def to_toolkit(self, api_key=None, start_date=None, end_date=None,
                   quarterly=False, use_cached_data=False, risk_free_rate="10y",
                   benchmark_ticker="SPY", enforce_source=None,
                   convert_currency=None, intraday_period=None, rounding=4,
                   remove_invalid_tickers=False, sleep_timer=None,
                   progress_bar=True):                             # :179-195
        try:
            from financetoolkit import Toolkit                     # :240  LAZY, inside the method
        except ImportError as exc:
            raise ImportError("To use the 'to_toolkit' functionality, it requires "
                              "installation of the FinanceToolkit …") from exc   # :243-247
        if api_key is None:
            print("The parameter api_key is not set. Therefore, using Yahoo Finance as the "
                  "source which is limited to 5 years of fundamental data. Consider obtaining "
                  "a key with the following link: https://www.jeroenbouma.com/fmp"
                  "\nYou can get 15% off by using the above affiliate link …")   # :248-255
        symbols = self[self.index.notna()].index.to_list()          # :257
        toolkit = Toolkit(tickers=symbols, api_key=api_key or "", …)  # :259-275
        return toolkit                                             # :277
```

| Property | Answer | Evidence |
|---|---|---|
| How is integration implemented? | A single method on a `pd.DataFrame` subclass that constructs a `financetoolkit.Toolkit` from the frame's index | `helpers.py:170-277` |
| Which API is used? | `financetoolkit.Toolkit(tickers=…, api_key=…, …)` — 14 forwarded parameters | `:259-275` |
| Is the import lazy? | **Yes** — inside the method body, wrapped in `try/except ImportError` | `:240-247` |
| Does FinanceDatabase fetch market data itself? | **No.** It makes exactly two network calls in its entire codebase, both `requests.get` for static bz2/gzip files (`:65`, `:336`) | grep of all `requests.` uses |
| Does FinanceDatabase only supply identifiers? | **Yes** — it supplies the *symbol list* (`self.index`), nothing else | `:257` |
| Where does market data come from? | FinanceToolkit → **FinancialModelingPrep** (with a key) or **Yahoo Finance** (without) | `:248-255` docstring + printed message |
| Where do fundamentals come from? | Same — FMP or Yahoo, via FinanceToolkit | `:218-219` docstring |
| Are API keys required? | **Not by FinanceDatabase.** `to_toolkit(api_key=None)` works and falls back to Yahoo, "limited to 5 years of fundamental data" | `:248-255` |
| Are rate limits handled? | **Not by FinanceDatabase.** A `sleep_timer` parameter is forwarded to `Toolkit` (`:273`), documented as "auto-determined" | `:227-228`, `:273` |
| Is external-provider failure handled? | **Not by FinanceDatabase.** Only `ImportError` is caught. Any network/rate-limit/auth failure inside `Toolkit` propagates to the caller | `:243-247` |
| Is the integration optional at runtime? | **Yes** — `import financedatabase` and all querying work without `financetoolkit` installed. **Executed proof:** in a venv where `financedatabase` was installed `--no-deps` and `financetoolkit` was absent, `import financedatabase as fd` succeeded, all seven asset classes loaded and answered queries, and `to_toolkit()` raised `ImportError: To use the 'to_toolkit' functionality, it requires installation of the FinanceToolkit…` | runtime |
| Is the integration optional at install time? | **No** — see §9.2 | `pyproject.toml:35-37` |
| Marketing side-effects on the call path? | **Yes.** `api_key=None` triggers a `print()` containing an **affiliate link** and a "15% off" offer | `:248-255` |
| Silent data loss on the call path? | **Yes.** `self[self.index.notna()]` drops NaN index entries — which is exactly what happens to the ticker `NA` under release 2.4.0 read semantics (§7.4) | `:257` |

## 9.2 Finding EI-01 — the dependency declaration contradicts the code

`pyproject.toml:35-37` (and PyPI `requires_dist`):

```toml
dependencies = [
    "financetoolkit>=2.0.3,<3.0.0",
]
```

That is the **only** declared runtime dependency — and it is the one thing the code imports
*lazily and optionally*. Meanwhile the modules the code actually imports at load time are
**not declared at all**:

| Imported by the shipped package | Declared in `requires_dist`? |
|---|---|
| `numpy` | **No** |
| `pandas` | **No** |
| `requests` | **No** |
| `io`, `pathlib`, `typing` (stdlib) | n/a |
| `financetoolkit` (lazy, one method) | **Yes — as a hard requirement** |

The dependency tree is therefore **inverted**: an optional feature is mandatory, and the
mandatory runtime is implicit (satisfied only transitively, through `financetoolkit`).

Consequences:

1. `pip install financedatabase` installs `financetoolkit` whether or not `to_toolkit()` is ever
   called — pulling a large, network-coupled tree into any environment that only wanted a CSV
   reader.
2. `pandas`, `numpy` and `requests` versions are **not constrained by `financedatabase` at all**.
   They are whatever `financetoolkit` happens to require. If `financetoolkit` ever dropped
   `pandas`, `financedatabase` would break with no version constraint of its own to catch it.
3. A consumer cannot express "I want the database, not the toolkit" through normal packaging.
   The only route is `pip install --no-deps financedatabase` plus manually providing
   `pandas`/`numpy`/`requests` — which is what we did for this audit, and which worked.

## 9.3 What `financetoolkit` drags in (measured from PyPI metadata)

| financetoolkit version | Released | `requires_python` | Runtime dependencies |
|---|---|---|---|
| **2.2.0** (latest) | 2026-08-18 | **`>=3.11, <3.16`** | `openpyxl>=3.1`, **`pandas>=3.0`**, `pyyaml>=6.0`, `requests>=2.32`, **`scikit-learn>=1.6`**, **`yfinance` (unpinned)** |
| 2.1.3 | 2026-06-27 | `>=3.10, <3.16` | (earlier set) |
| 2.1.2 / 2.1.1 / 2.1.0 | 2026-06 | `>=3.10, <3.16` | |
| 2.0.7 | 2026-03-14 | `>=3.10, <3.14` | |
| 2.0.5 | 2025-09-10 | `>=3.10, <3.14` | |
| 2.0.3 (the floor in `financedatabase`'s constraint) | 2025-05-01 | `>=3.10, <3.14` | |

Optional extras on 2.2.0: `econometrics` → `linearmodels>=6.0`, `statsmodels>=0.14`;
`mcp` → `fastmcp>=3.4.2`, `linearmodels`, `mcp[cli]>=1.27.0`, `python-dotenv`, `rich`,
`statsmodels`, `tabulate`.

**Finding EI-02 — a Python-version contradiction in the published metadata.**
`financedatabase 2.4.0` declares `requires-python = ">=3.10, <3.16"` and depends on
`financetoolkit>=2.0.3,<3.0.0`. But `financetoolkit 2.2.0` requires `>=3.11,<3.16`. On
**Python 3.10**, no `financetoolkit` in `[2.0.3, 3.0.0)` that supports 3.10 is newer than
2.1.3, so a resolver must backtrack to **≤2.1.3**. On **Python ≥3.11**, it resolves to
**2.2.0**, which forces **`pandas>=3.0`** and installs **`yfinance`** and **`scikit-learn`**.
So the environment you get depends on your interpreter version — and the package's own
classifiers advertise 3.10–3.14 support while its dependency's newest release excludes 3.10.

**Finding EI-03 — the tested configuration is not the installed configuration.**

| | `financetoolkit` | `pandas` | Python |
|---|---|---|---|
| **CI** (`testing.yml:27,30` → `uv sync` with `uv.lock`) | **2.0.7** (pinned) | **2.3.3** (marker `python_full_version < '3.11'`) | **3.10** |
| **A user today** (`pip install financedatabase`) | **2.2.0** | **≥3.0** | ≥3.11 |
| **This audit** | *not installed* (`--no-deps`, deliberate) | **3.0.5** | 3.11.2 |

`uv.lock:3` states `requires-python = ">=3.10, <3.16"` with seven resolution markers;
`uv.lock:592-597` pins `financetoolkit` **2.0.7** and `pandas` **2.3.3** for `<3.11`.
So the project's 86 passing tests exercise a dependency set that **no current `pip install`
reproduces**. That is a real reproducibility gap between "tested" and "shipped", distinct from
the code/data gap in §7.4.

*Audit note:* we deliberately did **not** install `financetoolkit`, `yfinance` or
`scikit-learn`. Installing them would have added ~hundreds of MB and a live Yahoo dependency to
the research venv without changing any finding — every FinanceDatabase code path we needed was
exercisable without them, as the `--no-deps` import test proves. This is recorded rather than
left implicit.

## 9.4 Capability separation (required by the tasking)

| Capability | **FinanceDatabase** | **FinanceToolkit** | **External provider (FMP / Yahoo)** | **AHOS** |
|---|---|---|---|---|
| Static catalogue of listings (symbol, name, sector, country, identifiers) | **✓ owns this** | ✗ | ✗ | ✗ (not needed for crypto) |
| `select` / `search` / `show_options` over that catalogue | **✓ owns this** | ✗ | ✗ | ✗ |
| GICS-approximating taxonomy | **✓ owns this** (approximation, manually curated) | ✗ | ✗ | ✗ |
| ISIN/CUSIP/FIGI checksum validation | ✓ (**`main` only**, not in release 2.4.0) | ✗ | ✗ | ✗ |
| Historical & fundamental financial statements | ✗ | ✓ orchestrates | **✓ supplies** | ✗ |
| Ratios, metrics, models, technical indicators | ✗ | **✓ owns this** | ✗ | partial (own `research/quant_metrics.py`) |
| Prices, OHLCV, intraday | ✗ | ✓ orchestrates | **✓ supplies** | ✓ (own crypto providers) |
| Rate limiting / retry / caching of provider calls | ✗ | ✓ (`sleep_timer`, `use_cached_data`) | n/a | ✓ (`http.ts`, provider adapters) |
| Authentication / API keys | ✗ (forwards `api_key`) | ✓ | **✓ requires** | own key handling |
| Cryptocurrency prices, pools, on-chain data | **✗** | **✗** (equity/fund oriented) | **✗** (FMP/Yahoo are TradFi) | **✓** (DexScreener, GeckoTerminal, GoPlus, RugCheck, Pump.fun, CoinGecko, DefiLlama, Jupiter, mempool) |
| Token/contract/pool identity | **✗** | **✗** | **✗** | **✓** (`architecture/identity/`) |
| Security gating (honeypot, mint/freeze authority, LP lock) | **✗** | **✗** | **✗** | **✓** (GoPlus, RugCheck) |
| Opportunity scoring | **✗** | **✗** | **✗** | **✓** (`scoring.ts`, `architecture/scoring/`) |
| Decision authority | **✗** | **✗** | **✗** | **✓** (`architecture/decision/authority.py`) — frozen |

**Attribution discipline:** nothing in the left-hand column beyond row 4 is a FinanceDatabase
capability. Any statement of the form "FinanceDatabase gives you fundamentals/prices/ratios"
is a statement about **FinanceToolkit plus FinancialModelingPrep or Yahoo Finance**, and must be
recorded as such.

## 9.5 Compatibility with AHOS's stated constraints

AHOS's `requirements.txt` states its law explicitly:

> *"LAW: $0/month cost ceiling. Every package here is free, permissively licensed, and
> installable offline from a wheel cache. No paid SDK is ever required. Python: 3.11+"*
> and *"the runtime core deliberately uses stdlib urllib so the deterministic floor has ZERO
> third-party network dependency."*

| AHOS constraint | FinanceDatabase + financetoolkit | Verdict |
|---|---|---|
| **$0/month** | `financedatabase` itself is free. `to_toolkit()` without a key falls back to Yahoo (free, 5-year limit) and *prints an affiliate upsell*. Full capability requires a **paid FinancialModelingPrep key** | **Partial** — the database is $0; the integration path is monetized |
| **Installable offline from a wheel cache** | The 34 KB wheel is trivially cacheable — **but it contains no data**. The data path is a live HTTPS GET to `raw.githubusercontent.com/main/`. `use_local_location=True` fails for a pip install (§6.6) | **FAIL** |
| **No paid SDK ever required** | Not required for the database itself | Pass (for the database only) |
| **ZERO third-party network dependency in the deterministic floor** | `requests` is mandatory and the only data path is remote | **FAIL** |
| **Python 3.11+** | Declares `>=3.10,<3.16`; `financetoolkit 2.2.0` needs `>=3.11` | Pass on 3.11, but see EI-02 |
| **Iran-resilience / operation under filtering** | Requires reachability of `raw.githubusercontent.com` (data) and, for `to_toolkit`, Yahoo/FMP. **`raw.githubusercontent.com` was unreachable from the audit host** — a measured TLS failure, not a prediction | **FAIL — measured** |
| **Existing dependency set** (`PyYAML, numpy, pandas>=2.1, requests, urllib3, PySocks, pytest, pytest-timeout`) | Adding `financedatabase` pulls `financetoolkit` → **`pandas>=3.0`** (a major-version bump over AHOS's `pandas>=2.1.0`), **`scikit-learn>=1.6`**, **`yfinance` (unpinned)**, `openpyxl`, `pyyaml` | **FAIL — conflict risk with the existing pandas floor and a large new surface** |

**Finding EI-04 — `pandas>=3.0` is a breaking-change boundary.** AHOS pins `pandas>=2.1.0` and
its research lane (`research/baseline_stats.py`, `research/quant_metrics.py`) runs on it.
`financetoolkit 2.2.0` requires `pandas>=3.0`. pandas 3.0 changed default string dtype
behaviour — observable in this audit: `eq.data.dtypes` reported `str` for 20 columns and `bool`
for 1, with **zero** `object` columns, which is pandas 3 semantics. Any AHOS code that assumes
`object` dtype for text columns would behave differently. Installing `financedatabase` with
default resolution would therefore force a pandas major upgrade on the whole AHOS environment.
Status: version conflict **VERIFIED** from metadata; impact on AHOS code **NOT TESTED** (we did
not install anything into AHOS, by instruction).

## 9.6 Is it safe for a local-first AHOS?

**No, not as distributed.** The binding reasons, in order of severity:

1. **The only supported data path is a live network fetch from a mutable branch** on a host that
   was measurably unreachable from our audit environment. There is no cache, no offline mode and
   no pinning (§6.6, §7.4).
2. **Installation drags in `yfinance` + `scikit-learn` + `pandas>=3.0`** through a dependency the
   code does not need at import time (§9.2, §9.3, EI-04).
3. **The monetized path prints an affiliate offer** on a library call (§9.1) — unacceptable in an
   AHOS operator surface.
4. `yfinance` is **unpinned** in `financetoolkit 2.2.0`, so a Yahoo-side or yfinance-side change
   can break the tree without any version movement in `financedatabase`.

**What *would* be safe** (design only — not implemented, not authorized): consume the
`database/*.csv` files from a **pinned git commit**, vendored into an isolated research area with
a recorded SHA-256, parsed by **AHOS's own code** using the already-present `pandas>=2.1` — with
**no** `financedatabase` install, **no** `financetoolkit`, **no** `yfinance`, and **no** runtime
network dependency at all. The library's ~1,900 lines are MIT-licensed and simple enough to
reimplement or bypass entirely; the *data* is the part with value, and the data is plain CSV.
This matches the standing rule already recorded in AHOS's `docs/OSS_HARVEST_LOG.md`:
*"Techniques and public mathematics may be reimplemented freely."* See §14.
