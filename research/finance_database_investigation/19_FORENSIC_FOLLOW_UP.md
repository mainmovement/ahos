# 19 — Forensic Follow-up: Evidence Consolidation & Verification

**Document 19 of the FinanceDatabase investigation package.**
**Follow-up date:** 2026-09-15 (18:25Z – 19:05Z UTC), ~2 h after the original investigation.
**Classification:** `RESEARCH_ONLY`. No AHOS production code, config, data or soak state touched.
**Scope:** focused forensic re-verification of the highest-value findings in documents 00–18.
**This is not a re-run of the investigation.** It is an audit *of the audit*.

---

## 19.0 What happened before anything else: the original environment was gone

The first action of this follow-up was to locate the isolated research workspace referenced by
documents 00–18. It no longer existed.

| Path expected by the original report | State at follow-up start |
|---|---|
| `/tmp/fdb_repo/` (sparse clone @ `a174c97d3b`) | **ABSENT** |
| `/tmp/fdb_venv/` (research virtualenv) | **ABSENT** |
| `/tmp/fdb_dl/` (verified sdist + wheel) | **ABSENT** |
| `/tmp/fdb_lab/` (12 empirical scripts + outputs) | **ABSENT** |
| `research/finance_database_investigation/` (deliverable) | **PRESENT — 20 files + `evidence/`** |

**Cause:** the sandbox persists only files under the workspace root `/home/user`. Everything under
`/tmp` is discarded between turns. The original report's reproduction instructions
(`README.md` §3) point at `/tmp` paths, which are therefore **not durably reproducible** as
written.

**Consequence, stated plainly:** at the start of this follow-up, every claim in documents 00–18
that rested on *execution* was, strictly, **unreproducible from the archived state alone**. The
archived `evidence/` artifacts (JSON/CSV/script sources) survived; the environment that produced
them did not.

**Action taken:** the isolated environment was **rebuilt from scratch** in a new temporary
location (`/tmp/fdb2_*`), and the decisive claims were **re-executed**, not restated. This
document reports the re-execution results and explicitly separates:

- **REPRODUCED** — re-executed in this follow-up, same result;
- **REFINED** — re-executed, result correct but the original statement was imprecise;
- **CORRECTED** — re-executed, original statement materially wrong;
- **UNREPRODUCED** — could not be reproduced; the original figure is withdrawn;
- **HISTORICAL** — true when measured, but about a state that has since changed or cannot be
  re-measured.

> **This is the single most important methodological output of the follow-up.** A report whose
> evidence lives in `/tmp` has a shelf life of one session. §19.7 fixes that.

## 19.1 Rebuilt environment (recorded, not assumed)

| Item | Value | Verification |
|---|---|---|
| Follow-up timestamp | 2026-09-15T18:25Z – 19:05Z | `date -u` |
| Host | Arena.ai agent sandbox, Linux container, 2 cores — **not** the AHOS Windows host | same host class as the original |
| Python | 3.11.2 | `/tmp/fdb2_venv/bin/python -V` |
| pandas / numpy / requests | 3.0.5 / 2.4.6 / 2.34.2 | `pip list` — **identical to the original** |
| `financedatabase` | 2.4.0, installed `--no-deps` from the PyPI wheel | `pip list` |
| `financetoolkit` | **ABSENT** (deliberate — attribution rule) | import probe → `ImportError` |
| Test stack | pytest **9.0.3**, pytest-recording **0.13.4**, pytest-mock 3.15.1, pytest-timeout 2.4.0, vcrpy **8.1.1**, pytest-subtests 0.15.0, python-stdnum **2.2**, tqdm, openpyxl | pinned to match `uv.lock` exactly |
| Repository checkout | `/tmp/fdb2_repo` @ **`a174c97d3bba96fc1a82b2e1068fb3ec5e02e634`**, sparse (`compression/ database/ tests/ .github/ financedatabase/`), 215 MB | `git log -1` |
| sdist SHA-256 | `a2af519e64e68baa52d369b49a8a16b09e77de0f20bb58e37243fbed225f2e87` | **MATCH** vs `evidence/ENVIRONMENT.txt` |
| wheel SHA-256 | `dee02df0fc132a0cbffcef30294216b67655ddba92f1613dd756e06d5e041fd7` | **MATCH** vs `evidence/ENVIRONMENT.txt` |
| Upstream HEAD at follow-up time | **still `a174c97d3bba`**, `pushed_at 2026-09-13T15:10:39Z` | GitHub API |

**Artifact integrity re-verified independently:** the SHA-256 values published by the PyPI JSON API
today match, byte for byte, the values recorded in `evidence/ENVIRONMENT.txt` two hours earlier,
and both match a fresh `sha256sum` of the re-downloaded files. **Artifact identity is confirmed
across two independent sessions.**

**Repository has not moved.** Because HEAD is unchanged, the original findings are **CURRENT, not
HISTORICAL**. Stars drifted 9,116 → 9,119 (cosmetic). This materially simplifies the
historical-vs-current analysis required by Objective D: *nothing in the dataset or the code has
changed between the two investigations.*

**Network re-measured (2 h later):**

| Host | Original | Follow-up |
|---|---|---|
| `pypi.org` | 200 | 200 |
| `github.com` | 200 | 200 |
| `api.github.com` | 200 | 200 |
| `codeload.github.com` | 200 | 301 (redirect — reachable) |
| `files.pythonhosted.org` | 200 | 404 on `/` (reachable; path has no index) |
| **`raw.githubusercontent.com`** | **TLS FAIL, curl rc=35** | **TLS FAIL, curl rc=35 — identical** |
| Azure blob log storage (`productionresultssa12.blob.core.windows.net`) | not tested | **EOF — unreachable** (new) |

The `raw.githubusercontent.com` failure **reproduces exactly**, two hours later, with the same
curl exit code. This strengthens EV-ENV-06 from "observed once" to "observed twice, stable". It
does **not** resolve U-18 (whether the failure is sandbox-specific) — that still requires a test
from the AHOS Windows host. A **new** unreachable host was found: GitHub's Actions log storage,
which is why U-12 could not be closed by fetching the CI log (§22 closes it by re-execution
instead — stronger evidence).

## 19.2 Method

For each claim under test:

1. Locate the original evidence (document + `evidence/` artifact + archived script).
2. Recover the **exact** original input (e.g. the 73-token probe list was copied verbatim out of
   `evidence/scripts/a2_crypto.py`, not re-invented — so results are comparable, not merely similar).
3. Re-execute in the rebuilt environment against the pinned commit.
4. Emit machine-readable JSON to `/tmp/fdb2_lab/` and archive the script under `evidence/scripts/`
   as `f1`…`f5` (the `f` prefix distinguishes follow-up scripts from the original `a`-series).
5. Compare against the original claim and classify REPRODUCED / REFINED / CORRECTED /
   UNREPRODUCED / HISTORICAL.

New follow-up scripts (all archived, all read-only):

| Script | Purpose |
|---|---|
| `evidence/scripts/f1_objective_a_crypto.py` | Objective A — all ten crypto claims, emits `f1_objective_a.json` |
| `evidence/scripts/f2_a10_contract.py` | Objective A claim A-10 — imports the **real** AHOS contract read-only and attempts construction |
| `evidence/scripts/f3_na_regression.py` | Objective C — release-vs-main loader diff, exact source record, all-asset-class scope test |
| `evidence/scripts/f4_identity_fixtures.py` | Objective B — exact source records for all five identity cases |
| `evidence/scripts/f5_gics_replication.py` | Objective D — replicates the CI `Check-GICS-Categorisation` job locally, closing U-12 |

**Safety of `f2`:** `architecture/providers/contracts.py` was imported **read-only** by explicit
file path. It was first confirmed to be stdlib-only (`__future__`, `abc`, `dataclasses`, `time`,
`typing`) so importing it cannot trigger any AHOS side effect. No AHOS file was written. The module
was registered in `sys.modules` of the research process only (required by `dataclasses._is_type`).

---

# OBJECTIVE A — Verification of the decisive crypto verdict

Ten claims were re-tested. **All ten reproduce.** Two are **REFINED** for precision; none is
contradicted. The rejection stands on re-execution.

## A-1 · "The cryptos table has exactly seven columns" — **REPRODUCED / VERIFIED**

| | |
|---|---|
| Source of original claim | `08_CRYPTOCURRENCY_COVERAGE.md`; `evidence/schema_audit.json`; produced by `a2_crypto.py` |
| Re-execution | `f1_objective_a_crypto.py` → `pd.read_csv("compression/cryptos.bz2", dtype=str, keep_default_na=False)` |
| Result | `['symbol','name','cryptocurrency','currency','summary','exchange','website']` — **7**, 3,367 rows |
| Programmatic match vs reported list | `A1_MATCHES_REPORT = true` |
| Version | commit `a174c97d3b`, pandas 3.0.5 |
| Reproducible? | **Yes** — deterministic, offline, from the pinned artifact |
| Limitation | None. **Precision note:** the CSV has 7 columns; the *library* DataFrame has 6 columns plus `symbol` as the index (`index_col=0`), which is why `c.data['symbol']` raises `KeyError`. Both statements are true at different layers and should not be conflated |
| Classification | **VERIFIED** |

## A-2 · "The required AHOS identity fields are absent" — **REPRODUCED / VERIFIED**

Existence check over 14 fields, re-executed:

```
chain  network  contract  address  contract_address  platform  token_id
decimals  launch_date  first_seen  market_cap  price  volume  liquidity
→ present: 0 of 14     A2_ALL_ABSENT = true
```

| | |
|---|---|
| Reproducible? | **Yes** |
| Limitation | Absence of a *column name* is what was tested. Chain information does exist as **free prose** inside `summary` — re-measured: `ethereum` 606 rows, `solana` **10**, `arbitrum` **0**, `base` **0**. Prose is not a queryable field and cannot be joined on, so the verdict holds, but the honest statement is "no structured field", not "no mention anywhere" |
| Classification | **VERIFIED** |

## A-3 · "`SOL` is not present" — **REPRODUCED / VERIFIED** (at both data and library level)

| Layer | Test | Result |
|---|---|---|
| Data | `(cryptocurrency=='SOL').sum()` | **0 rows** — `"SOL" in tickers` → **False** |
| Data | `symbol.str.startswith('SOL-').sum()` | **0** |
| Library (release 2.4.0) | `Cryptos(use_local_location=True).select(cryptocurrency="SOL")` | **`ValueError`: "The cryptocurrency 'SOL' is not available in the database. Please check the available cryptocurrencies using the 'show_options' method."** |

Distinct token tickers: **352** including the empty string, **351** excluding it (7 rows have
`cryptocurrency == ''`). See §19.4 for the 351-vs-352 reconciliation.

Also re-verified: **`BTC` is absent as a token** (0 rows) and present only as a **quote currency**
(**113** rows). Classification: **VERIFIED**.

## A-4 · "`SOL1` appears as reported" — **REPRODUCED / VERIFIED, with a sharpening**

| Layer | Result |
|---|---|
| Data | `cryptocurrency=='SOL1'` → **10 rows** |
| Names | `Solana CAD`, `Solana CNY`, `Solana ETH`, `Solana EUR`, … |
| Library | `select(cryptocurrency="SOL1")` → **10 rows** |
| Sample row | `symbol='SOL1-CAD'`, `name='Solana CAD'`, `cryptocurrency='SOL1'`, `currency='CAD'`, **`summary='Solana (SOL) is a cryptocurrency.'`**, `exchange='CCC'`, `website='https://solana.com'` |

**Sharpening (new).** The sample row's own `summary` says **"Solana (SOL)"** while its
`cryptocurrency` key is **`SOL1`**. So the dataset *contains the correct ticker in prose* and the
*mangled ticker in the key*. Any consumer that greps the summary for `SOL` and any consumer that
queries by `cryptocurrency` get **different answers from the same row**. This is a stronger
illustration of the identity hazard than the original report gave, and it is the basis of fixture
**FIX-05** (§20).

Also re-verified: `COMP1` = **CompoundCoin** (10 rows) while `COMP` = **Compound** (2 rows) — the
suffix trap is real and the two coexist. `SRM` (Serum, collapsed 2022) present, 9 rows, no
delisting flag. Classification: **VERIFIED**.

## A-5 · "The reported token probe results" — **REPRODUCED EXACTLY / VERIFIED**

The **verbatim** 73-token probe list was lifted from `evidence/scripts/a2_crypto.py` and re-run:

| Metric | Original report | Follow-up | Match |
|---|---|---|---|
| Probe size | 73 | **73** | ✓ |
| Present | 22 | **22** | ✓ |
| Absent | 51 | **51** | ✓ |
| All 14 Solana-ecosystem tokens absent | yes | **`A5_ALL_SOLANA_ECOSYSTEM_ABSENT = true`** | ✓ |

Absent list includes `BONK WIF JUP PYRM JTO RAY ORCA MNGO POPCAT MEW BOME SLERF MYRO WEN …
PEPE SHIB BTC ARB OP SUI APT SEI TIA INJ ONDO …` — i.e. **every** Solana-ecosystem token probed,
plus every post-2021 major asset.

Classification: **VERIFIED — exact reproduction.**

## A-6 · "The reported ticker collision results" — **REPRODUCED / REFINED**

| Metric | Original | Follow-up | Note |
|---|---|---|---|
| Crypto↔equity ticker collisions | 86 | **86** | ✓ |
| Denominator | "86/351" | 86 of **351** non-empty tickers (**24.5%**); 86 of **352** including `''` (**24.4%**) | see §19.4 |
| `META` | Metadium vs Meta Platforms | **confirmed** | crypto rows + equity rows captured in `f1_objective_a.json` |
| `GO` | GoChain vs Grocery Outlet | **confirmed** | same |

Classification: **VERIFIED**, denominator **REFINED** (351 is the filtered count; 352 is the raw
`nunique()` including the empty string — both are defensible, and the report should state which).

## A-7 · "The absence of timestamps" — **REPRODUCED / VERIFIED**

Column-name scan for `date|time|updated|asof|timestamp|snapshot|version|source|provider|retrieved`
(case-insensitive) across **all seven** schemas:

```
A7_total_temporal_columns_found = 0        A7_NO_TIMESTAMPS_ANYWHERE = true
A7_total_rows_all_schemas       = 304,495
```

Per-class row counts re-measured and identical to the original: equities 112,690 · etfs 36,481 ·
funds 57,853 · indices 91,181 · currencies 2,556 · cryptos 3,367 · money markets 1,367.

Provenance signal re-measured: `exchange='CCC'` (CryptoCompare) dominates the cryptos table.
Classification: **VERIFIED**. This is the finding that makes `STALE ≠ LIVE` **unenforceable** rather
than merely inconvenient.

## A-8 · "The reported lack of crypto data CI coverage" — **REPRODUCED / REFINED (stronger)**

The original claim was "no CI job writes `database/cryptos.csv`". Re-verified by enumerating every
`to_csv` target in all three workflows:

| `to_csv` targets in `.github/workflows/` | Count |
|---|---|
| `database/equities/{exchange}.csv` | 1 |
| `database/equities/NAN.csv` | 1 |
| `compression/*.bz2` (7 files, incl. `cryptos.bz2`) | 7 |
| `compression/categories/*_categories.gzip` (7 files, incl. `cryptos_categories.gzip`) | 7 |

**Under `database/`, the only write targets are equities shards.** `database/cryptos.csv` appears in
the workflows **three times, always as a read**:

- `:313` `cryptos = pd.read_csv('database/cryptos.csv', **read)` → `:315` re-compress to `compression/cryptos.bz2`
- `:379` read → `:388` build `cryptos_categories.gzip`
- `:523` `("Cryptocurrencies", "cryptos.csv", "cryptocurrency", "Cryptocurrencies")` → README row count

Upstream fetches are **three** `pd.read_json` calls, all to
`raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/{nasdaq,nyse,amex}/*_full_tickers.json`
(`:167,173,179`) — **US equities only**. Terms `bitcoin`, `solana`, `token`, `CCC` appear **0**
times in any workflow.

**Refined statement (stronger and more precise than the original):**

> `database/cryptos.csv` is **read, re-compressed, categorised and counted** by CI on every run —
> but its **content is never updated by any workflow, from any source**. The automation gives the
> crypto table the *appearance* of maintenance (it is touched by three of the five jobs) while
> providing **none of the substance**. No upstream feed, no update logic, no freshness mechanism.

Classification: **VERIFIED, REFINED.**

## A-9 · "The reported negative capability assessment" — **REPRODUCED / VERIFIED**

16-capability matrix re-evaluated programmatically:

```
chain_field false · contract_address_field false · price_field false · volume_field false
liquidity_field false · market_cap_field false · fdv_field false · launch_or_first_seen false
decimals_field false · timestamp_field false · security_signal_fields false
solana_token_present false · post_2021_assets_present false · automated_update_job false
delisted_flag_for_crypto false · identifier_for_join false

A9_capabilities_satisfied = 0 / 16        A9_ALL_NEGATIVE = true
```

Classification: **VERIFIED — 0 of 16, exact reproduction.**

## A-10 · "The `NormalizedTokenCandidate` compatibility argument" — **REPRODUCED / UPGRADED from argument to proof**

The original §14.2 *argued* this from reading the dataclass. The follow-up **executed** it against
the real AHOS module (imported read-only; confirmed stdlib-only first).

| Test | Result |
|---|---|
| AHOS contract imports | `['__future__','abc','dataclasses','time','typing']` → `ahos_contracts_is_stdlib_only = true` |
| Contract law text (verbatim from the module docstring) | *"Strict UNKNOWN representation: Missing or uncollected data is NEVER guessed."* · *"Provable Source Provenance: Every datapoint carries source provider ID, timestamp, and SHA-256 raw digest."* · *"Fail-Closed: Rate limit, connection, or schema errors return normalized error envelopes."* |
| `UNKNOWN_VALUE` | `None` |
| **Required (no-default) fields of `NormalizedTokenCandidate`** | **`['chain','address','symbol','name']`** |
| **T1** — construct from a real FinanceDatabase cryptos row without chain/address | **`TypeError: NormalizedTokenCandidate.__init__() missing 2 required positional arguments: 'chain' and 'address'`** |
| **T2** — construct with `chain=None, address=None` | Succeeds (dataclasses do not enforce `str` at runtime) |
| T2 → `identify_unknowns()` | **33** unknown fields |
| T2 → `confidence_level` | **`HIGH`** (the dataclass default) |
| **T2 → the router's real dedupe key** `(c.chain, c.address.lower())` | **`AttributeError: 'NoneType' object has no attribute 'lower'`** |
| T3 — dedupe expression confirmed in source | `architecture/providers/registry.py` contains verbatim: `key = (c.chain, c.address.lower())` |
| T3 — discovery providers | `for pid in ["dexscreener", "geckoterminal"]:` — only these two feed `discover_candidates` |
| T4 — `BaseMarketProvider` abstract surface | `['capabilities','fetch_candidate_tokens','fetch_token_metrics','health_check','provider_id']`; both fetch methods take `chain` (and `address`) as required parameters |
| **T5** — of 16 `MarketMetrics` fields, how many could FinanceDatabase populate? | **0** |
| **T5** — of 15 `SecuritySignals` fields, how many? | **0** |

**The argument is now a proof.** An adapter must either fabricate `chain`/`address` (violating the
contract's own stated law, quoted verbatim above), or pass `None` — which survives construction but
**crashes `ProviderRouter.discover_candidates()` at the dedupe key** with `AttributeError`. There is
no third option, because there is no third source of those values.

**New finding (FOLLOWUP-01), not in the original report.** A `None`-filled candidate reports
**`confidence_level = "HIGH"`** by default while carrying **33** unknown fields. The default is
optimistic: AHOS's own contract would let a content-free candidate self-declare high confidence
unless the producer explicitly downgrades it. This is an **AHOS-side hardening observation** —
recorded as knowledge item **KN-06** (§24), flagged **PROPOSED — NOT IMPLEMENTED**, and explicitly
**not** a change request to any protected surface.

Classification: **VERIFIED — upgraded from INFERENCE/argument to EXECUTION-PROOF.**

## A-11 · Library-level fail-open behaviour (supporting) — **REPRODUCED**

Two supporting behaviours were re-executed with the **release 2.4.0 wheel** against the pinned data:

| Test | Result |
|---|---|
| `search(nonexistent_column_typo="anything")` on Cryptos | prints `nonexistent_column_typo is not a valid column.` and returns **3,367 of 3,367 rows** → **FAIL-OPEN** |
| `Cryptos(use_local_location=True)` with no local data present (wheel as installed) | **`FileNotFoundError: [Errno 2] No such file or directory: '/tmp/fdb2_venv/lib/python3.11/site-packages/compression/cryptos.bz2'`**, and `isinstance(e, requests.exceptions.RequestException)` → **False** (so the library's own handler does not catch it) |

Both reproduce EV-QE-03 and EV-QE-12 exactly. Classification: **VERIFIED**.

## 19.3 Objective A verdict

| Claim | Classification |
|---|---|
| A-1 seven columns | **VERIFIED** (reproduced) |
| A-2 required fields absent | **VERIFIED** (0/14; prose caveat noted) |
| A-3 `SOL` absent | **VERIFIED** (data + library `ValueError`) |
| A-4 `SOL1` present | **VERIFIED** (10 rows; summary/key contradiction sharpened) |
| A-5 probe 22/51 | **VERIFIED** (exact) |
| A-6 collisions 86 | **VERIFIED / REFINED** (denominator 351 vs 352 stated) |
| A-7 no timestamps | **VERIFIED** (0 across all 7 schemas, 304,495 rows) |
| A-8 no crypto CI coverage | **VERIFIED / REFINED — stronger** |
| A-9 0/16 capabilities | **VERIFIED** (exact) |
| A-10 contract incompatibility | **VERIFIED — upgraded to execution-proof** |

> ## The crypto rejection is **not** disturbed by this follow-up.
> Every decisive claim re-executed to the same result, against the same pinned commit, in a
> rebuilt environment, with two claims strengthened and one upgraded from argument to proof.
> **No evidence materially contradicts the existing verdict.**

---

# OBJECTIVE E — Legal / licensing evidence normalization

Kept **separate** from the technical verdict, as required. All facts re-verified fresh at the
pinned commit unless marked otherwise. **This section identifies questions and evidence. It is not
legal advice and asserts no legal certainty.**

## 19.4 Re-verified legal facts

| Fact | Evidence | Status |
|---|---|---|
| `LICENSE` = MIT, `Copyright (c) 2023 Jeroen Bouma`, 21 lines | read at `a174c97d3b` | **VERIFIED** |
| `pyproject.toml`: `name="financedatabase"`, `version="2.4.0"`, `license={text="MIT"}`, `requires-python=">=3.10, <3.16"`, `dependencies=["financetoolkit>=2.0.3,<3.0.0"]` | read lines 2, 3, 5, 35–37 | **VERIFIED** |
| PyPI: license `MIT`, `requires_python <3.16,>=3.10`, `requires_dist ['financetoolkit<3.0.0,>=2.0.3']`, **35 releases**, latest **2.4.0** | PyPI JSON, re-fetched | **VERIFIED** |
| **No** `NOTICE`, `DATA-LICENSE`, `COPYING`, ODC/CC0 marker anywhere | `find` over the tree → only `./LICENSE` | **VERIFIED (absence)** |
| `CONTRIBUTING.md:117-119` — sector / industry_group / industry each *"follows GICS"* | read | **VERIFIED** |
| `CONTRIBUTING.md:129` — *"the sectors, industry groups and industries loosely approximate to the [The Global Industry Classification Standard (GICS®)](https://www.msci.com/our-solutions/indexes/gics) as created by MSCI. **No actual data is collected from this source** … This is **completely done through manual curation**. The actual datasets as curated by MSCI have not been used in the development of any part of this database…"* | read verbatim | **VERIFIED** |
| Upstream `rreichel3/US-Stock-Symbols`: **`license = None`**, 574 stars, `pushed_at 2026-09-15T00:39:12Z` | GitHub API, re-queried | **VERIFIED** |
| `JeroenBouma` (id **46189588**, 0 public repos, created 2018-12-27) ≠ `JerBouma` (id **46355364**, 15 public repos, 1,548 followers); `JeroenBouma/FinanceDatabase` → **HTTP 404** | GitHub API, re-queried | **VERIFIED** |
| **NEW:** the identifier check-digit logic is **not** hand-written — `financedatabase/validation/validate_identifiers.py:13` is `from stdnum import cusip, figi, isin`, and **`python-stdnum` 2.2 is licensed `LGPL` (LGPLv2+)** | read + `pip show` + PyPI classifier | **VERIFIED** |

The last row is a **material correction to document 23's predecessor** (§14.8 of document 14), which
described the check-digit algorithms as "~15 lines, no licence obligation" to reimplement. That
remains true *of the public standards* — but it is **not** what this repository does, and any advice
to "copy the validator" would import an **LGPL** dependency, which conflicts with AHOS's own
`requirements.txt` law (*"free, permissively licensed"*). LGPL is **not** a permissive licence.
Handled in detail in **document 23**.

## 19.5 Legal evidence matrix

| Subject | Observed evidence | Confirmed? | Legal significance | Requires legal review? |
|---|---|---|---|---|
| **1. Software licence** | MIT; `Copyright (c) 2023 Jeroen Bouma`; present in sdist root **and** `dist-info/licenses/`; grants use/copy/modify/merge/publish/distribute/sublicense/**sell**; notice-retention condition; warranty disclaimed in full | **YES** (re-verified) | Permissive; compatible with AHOS policy; commercial use allowed; **no fitness representation exists** | **NO** — clear |
| **2. Dataset licence** | No separate licence. MIT text covers *"this software and associated documentation files"*. 304,495 rows of CSV is neither. No `NOTICE`, no ODC/CC0/CC-BY, no CLA/DCO | **YES** (absence verified) | MIT is a **copyright** licence; whether it reaches a curated factual dataset is unresolved | **YES — LEGAL REVIEW REQUIRED** |
| **3. Upstream source licences** | `rreichel3/US-Stock-Symbols` → **`license = None`**; feeds **all** automated equity updates via 3 `pd.read_json` calls to unpinned `main`; commits titled `generated` | **YES** (re-verified) | Unlicensed ⇒ all-rights-reserved by default. Mitigating *arguments* exist (facts vs expression; mechanically generated lists lack originality) but they are **legal arguments, not findings** | **YES — LEGAL REVIEW REQUIRED** |
| **4. Third-party identifiers** | Populated counts re-verified: `isin` 30,429 equity rows (27.0%), `cusip`/`figi`/`composite_figi`/`shareclass_figi` per document 04. CUSIP = ABA registered mark, commercially administered; FIGI = Bloomberg scheme/mark; ISIN = ISO 6166; MIC = ISO 10383 (SWIFT-administered) | **YES** (counts) / **NO** (rights) | **CUSIP is the most concrete exposure.** Whether bulk redistribution of CUSIP/FIGI values requires a licence is a commercial-licensing question | **YES — LEGAL REVIEW REQUIRED** |
| **5. Taxonomy / trademark** | `categories.json` = 11 sectors / 24 industry groups / **69 industries**; data carries **80** industries; CI job literally named `Check-GICS-Categorisation`; `Equities.py` says *"adhering to the GICS standard"*; CONTRIBUTING:129 disclaims copying MSCI data | **YES** (both counts re-measured) | GICS® is a registered MSCI / S&P Dow Jones Indices mark. **No MSCI data is copied** (project's own explicit disclaimer) — so this is **trademark adjacency and naming**, not data infringement | **YES — but lower urgency** |
| **6. Data provenance** | **No script generates** `cryptos`, `currencies`, `indices`, `moneymarkets`, `etfs`, `funds`, or non-US `equities`. No provenance manifest, no source column, no ingest date (0 temporal columns — A-7). Style points to Yahoo Finance / CryptoCompare (`CCC` codes, `<TOKEN>-<QUOTE>`, `BASEQUOTE=X`, profile prose) | **Absence YES**; origin **NO** | If any part originated from Yahoo Finance, its ToS restrict redistribution/commercial reuse — a **different and larger** question than MIT | **YES — LEGAL REVIEW REQUIRED** (this is U-04) |
| **7. Redistribution rights** | Clear for **code** (MIT). For **data**: unstated | Code **YES** / data **NO** | Determines whether AHOS may vendor, mirror, serve or publish derived content | **YES — LEGAL REVIEW REQUIRED** |
| **8. Commercial use** | MIT grants it for code. `to_toolkit()` prints an **affiliate upsell** linking FinanceToolkit/FMP, implying a commercial relationship between author and FMP — but FMP/Yahoo terms govern that path, **not** this licence | Code **YES** | AHOS's $0/month law makes the FMP path moot; the affiliate link is a disclosure observation, not a licence term | **NO** for code; **YES** if the data is commercialized |
| **9. EU database right** | Directive 96/9/EC *sui generis* right protects investment in obtaining/verifying/presenting. Candidate indicators all present and verified: weekly automation, a checksum validator, a CI consistency job, four invariant tests, documented community curation, 304,495 rows. MIT is a copyright licence and does not clearly waive database rights. Author appears Netherlands-based | **Facts YES**; subsistence **NO** (legal question) | If the right subsists and is unlicensed, **substantial extraction and re-utilization** — precisely what vendoring 145 MB would be — may require permission MIT does not grant | **YES — LEGAL REVIEW REQUIRED** |
| **10. Questions for counsel** | (a) Does root MIT cover `database/`+`compression/`? (b) Who owns the dataset — author, contributors, upstream? (c) Does unlicensed upstream create downstream exposure for a commercial user? (d) Does an EU database right subsist, and is it licensed? (e) Do CUSIP/FIGI values require a licence to redistribute or serve publicly? (f) Is the Yahoo-implied provenance of `summary` prose (protectable expression, not fact) a copyright issue? | — | Six discrete questions | **YES — all six** |

## 19.6 Legal verdict (unchanged, and now better evidenced)

> **Code: MIT — clear, permissive, commercial-safe, no legal review needed.**
> **Data: LEGAL REVIEW REQUIRED.** Unlicensed dataset, unlicensed upstream, undocumented bulk
> provenance, CUSIP/FIGI trademark-adjacency, possible EU *sui generis* right.
> **New:** the validator's algorithms arrive via an **LGPL** library, so "copy the validator" is
> **not** a licence-clean path — implement from the public ISO/OpenFIGI specifications instead
> (document 23).

No legal certainty is asserted anywhere in this package. The interim posture that requires no
legal opinion is the one already taken: **internal, non-redistributed research use of a snapshot
pinned to a specific commit, with provenance recorded.**

## 19.7 Durability fix (arising from §19.0)

Because `/tmp` does not survive, the following are now archived **inside** the deliverable so the
package is self-sufficient:

- `evidence/ENVIRONMENT.txt` — original environment record (already present).
- `evidence/FOLLOWUP_ENVIRONMENT.txt` — **new**: the rebuilt environment, re-measured network
  state, and the artifact hash re-match.
- `evidence/followup/f1_objective_a.json`, `f2_a10_contract.json`, `f3_na_regression.json`,
  `f4_identity.json`, `f5_gics_replication.json`, `d_gics_sequence.json` — **new**: raw
  machine-readable output of every re-execution.
- `evidence/scripts/f1…f5*.py` — **new**: the re-verification scripts.

Documents 00–18 are **not** overwritten. The reproduction instructions in `README.md` §3 should be
read as pointing at *a* temporary location; the durable record is `evidence/`.

**Navigation:** Objective B → **document 20** · Objective C → **document 21** · Objective D →
**document 22** · Objective F → **document 23** · Objective G → **document 24** ·
final reconciliation, corrections register and decision format → **document 25**.
