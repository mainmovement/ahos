# 24 — AHOS Knowledge Extraction

**Document 24 — Objective G.** A proposed knowledge package: ten lessons extracted from the
FinanceDatabase investigation, each traced to evidence and each assigned a proposed destination
inside AHOS's documentation and governance structure.

> ## ⚠️ PROPOSED — NOT IMPLEMENTED
>
> **Every item in this document is a lesson and a proposal. Nothing has been written into AHOS.**
> No production code, no Lane A, no Lane B, no `CanonicalDecisionAuthority`, no scoring, no
> security module, no identity resolution module, no runtime, no calibration artifact, no
> configuration and no database state was modified. The active 72-hour soak was not disturbed. No
> dependency was installed into the AHOS environment. Phase 4 was not started. No FinanceDatabase
> integration was implemented.
>
> **"Proposed destination" means *where this lesson should be filed if it is accepted* — not that it
> has been filed there.** Acceptance and filing both require separate authorization.

> **Attribution rule carried throughout.** Nothing below is an AHOS production failure. Every lesson
> is derived from a **third-party** dataset and codebase. Where a lesson implies an AHOS-side
> observation, that observation is explicitly labelled as such and is **proposed**, not asserted.

---

## KN-01 · Identity collision lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-01-IDENTITY-COLLISION` |
| **Lesson** | A key that is unique **within** a namespace is not unique **across** namespaces, and the collision will not announce itself. Blocking or joining on an unnamespaced key silently merges distinct entities. Corroborating identifiers are frequently **absent exactly where they are most needed** — in the FinanceDatabase Berkshire case, `figi` was populated on the two *secondary* (Vienna) listings and empty on all four *primary* (US) ones. |
| **Source** | FinanceDatabase @ `a174c97d3b`: `CHAD` (equities ↔ etfs), Berkshire ×7 across 4 venues, `MMM` ×18 / 4 entities |
| **Evidence** | `evidence/followup/f4_identity.json` (`CHAD`, `cross_asset_symbol_collisions` n=1 pair, `BRK_all_rows`, `BRK_distinct_exchanges=['ASE','MEX','NYQ','VIE']`, `BRK_all_isin_empty=true`, `MMM_count=18`); the upstream project's **own** invariant test fails on `CHAD` at `tests/test_invariants.py:95`, reproduced `1 failed, 85 passed, 1 deselected in 42.43s` (`evidence/followup/` + document 22 §22.3); document 20 CASES 1–3 |
| **Confidence** | **HIGH** — execution-verified twice, in two independently built environments, against an unchanged HEAD |
| **AHOS relevance** | **HIGH.** AHOS already does the right thing: `ProviderRouter.discover_candidates()` dedupes on the **namespaced composite** `(c.chain, c.address.lower())`, verified verbatim in `architecture/providers/registry.py`. The lesson is *reinforcement plus a warning*: the composite key is only safe while `chain` and `address` are both non-null — see KN-02 |
| **Proposed destination** | `docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md` (identity section) **and** the adversarial fixture set proposed as FIX-01/FIX-02/FIX-03 in document 20 |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-02 · Symbol-vs-identity lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-02-SYMBOL-IS-NOT-IDENTITY` |
| **Lesson** | A **symbol is an alias, not an identity.** Four distinct failure modes were measured from symbol-as-key use: (a) one symbol → many unrelated entities (`MMM`: 3M Company, Marley Spoon AG, Mining Minerals & Metals plc, Minco Capital Corp.); (b) many symbols → one entity (`MMM` ×14 venues for 3M; ISIN `FR0013269123` → **57** symbols); (c) the symbol and the entity's own prose disagree — `cryptocurrency='SOL1'` while `summary='Solana (SOL) is a cryptocurrency.'`; (d) symbol conventions differ for the same share class (`BRK-A` vs `BRK/A`) and the pipeline assigns them **contradictory venues**. A resolver must therefore treat a symbol as a *search hint* and require a namespaced key plus corroboration before asserting identity. |
| **Source** | FinanceDatabase @ `a174c97d3b`, cryptos + equities tables |
| **Evidence** | `evidence/followup/f4_identity.json` (`MMM_distinct_names` = 5 names / 4 entities, `ISIN_max_fanout=57`, `ISIN_fanout_gt_1=5181`, `distinct_bare_tickers=74690` of 112,690 rows, `bare_tickers_appearing_more_than_once=16251`); `evidence/followup/f1_objective_a.json` (`sample_fdb_cryptos_row` showing the `SOL1`/`SOL` contradiction); `CRYPTO 86 of 351` token↔equity ticker collisions (`META`=Metadium, `GO`=GoChain); document 20 CASES 2–4, document 05 |
| **Confidence** | **HIGH** — every count re-measured |
| **AHOS relevance** | **HIGH.** This is precisely the distinction AHOS already encodes between `TokenIdentity.symbol_alias` (explicitly an alias) and `TokenIdentity.address_canonical` / `token_id` (the key), and between `TokenIdentity` and `PoolIdentity.belongs_to_token`. **Proposed AHOS-side observation (not a defect claim):** `NormalizedTokenCandidate` defaults `confidence_level="HIGH"` while `chain`/`address` are the only required fields — so a candidate constructed with `None` in those two fields reported **`confidence_level='HIGH'` with 33 unknown fields** (`evidence/followup/f2_a10_contract.json`, `T2_confidence_level`, `T2_n_unknown_fields`). Whether the default should be `LOW` is a **design question for the AHOS owner**, recorded here as a proposal and **not** acted upon |
| **Proposed destination** | `docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md`; `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`; fixture FIX-03/FIX-05 |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-03 · Release-vs-`main` lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-03-RELEASE-VERSUS-MAIN` |
| **Lesson** | When **code** is versioned by release but **data** is versioned by branch, pinning the code does **not** pin the system — and can select the *worse* combination. Concretely: the released, hash-verified `financedatabase 2.4.0` has the **defective** loader; the fix exists **only on `main`**. A consumer who does the "safe" thing (install a pinned release) gets the bug; a consumer who tracks an unpinned branch gets the fix. Proven by git ancestry, not inference: `git merge-base --is-ancestor 3b8eb83 2.4.0` → **NO**; `… HEAD` → **YES**. Release 2.4.0 was uploaded **2026-06-02T14:05:45Z**; the fix landed **2026-08-07T10:32:18Z** — **66 days later**, and no release followed. |
| **Source** | PyPI release metadata + git history of `financedatabase/helpers.py` |
| **Evidence** | `evidence/followup/f3_na_regression.json` (`C8_helpers_history`, `C9_commits_introducing_keep_default_na` = exactly one commit, `3b8eb8390959bec6a360a620333b6fe5217a4618`, Jon Højlund Arnfred, PR #166, *"Preserve CSV values verbatim in the database workflow"*); `helpers.py` 358 lines (release) vs 366 (main); `diff -rq` → only `helpers.py` differs plus `validation/` present only in the repo; document 21 §21.8–21.9 |
| **Confidence** | **HIGH** — execution- and git-verified |
| **AHOS relevance** | **HIGH.** Two directly transferable rules: (1) **pin the code AND the data to the same immutable reference** (a commit SHA plus per-file SHA-256), never a branch — this is document 14's boundary rules B-6/B-7; (2) **a release is not a snapshot of the system** — when auditing any dependency, diff the release artifact against the branch that feeds it, because the divergence is where the surprises live. Also: `2.4.0` shipped **without** the `validation/` subpackage that exists on `main`, so release-vs-branch divergence is not limited to the loader |
| **Proposed destination** | `AHOS_UPDATE_POLICY.md`; `docs/OPERATOR_VALIDATION_PROTOCOL.md`; `docs/OSS_HARVEST_LOG.md` |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-04 · Dataset-vs-code licensing lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-04-DATASET-VS-CODE-LICENSING` |
| **Lesson** | **A permissive code licence does not license the data the code serves.** MIT was verified four ways (repo `LICENSE` = *"MIT License / Copyright (c) 2023 Jeroen Bouma"*, 21 lines; `pyproject.toml:5 license={text="MIT"}`; PyPI `info.license="MIT"`; present in both sdist and `dist-info/licenses/`). Yet the MIT text grants rights in *"this software and associated documentation files"* — and a 304,495-row CSV is neither. There is **no** `NOTICE`, `DATA-LICENSE`, ODC/CC0 marker, CLA or DCO anywhere in the tree. Three further layers compound it: the automated upstream (`rreichel3/US-Stock-Symbols`) has **`license = None`**; the bulk provenance of six of seven tables is **undocumented** (Yahoo Finance / CryptoCompare is *inferred* from `CCC` codes and `<TOKEN>-<QUOTE>` symbols, **not verified**); and the identifiers themselves carry trademark adjacency (**CUSIP** = ABA/S&P, **FIGI** = Bloomberg, **GICS®** = MSCI/S&P DJI). A fourth layer was newly identified in this follow-up: the validator's algorithms arrive via **`python-stdnum`, which is LGPL-2.1+ — not permissive**, so even "just copy the MIT validator" is not a clean path. |
| **Source** | Repository licence artifacts, `pyproject.toml`, PyPI metadata, GitHub API on the upstream, `CONTRIBUTING.md:117-119,129`, `validate_identifiers.py:13`, `pip show python-stdnum` |
| **Evidence** | document 19 §19.4–19.6 (all re-verified fresh); upstream `license=None`, 574 stars, `pushed_at 2026-09-15T00:39:12Z`; `CONTRIBUTING.md:129` verbatim MSCI disclaimer (*"No actual data is collected from this source … completely done through manual curation"*); document 23 §23.0; document 12 LEG-01…LEG-04 |
| **Confidence** | **HIGH** for the *facts*; **NONE** asserted for the *legal conclusions* — by design |
| **AHOS relevance** | **HIGH.** Three transferable rules: (1) when harvesting any OSS dataset, record the **code licence and the data licence as separate fields**, and treat a missing data licence as a blocking gap, not a silence; (2) check the **licence of the libraries a technique depends on**, not only the licence of the file you are reading — an MIT file can import an LGPL library; (3) **techniques and public mathematics are the safe harvest**, per AHOS's own `OSS_HARVEST_LOG.md` rule, which this case validates rather than strains. **LEGAL REVIEW REQUIRED** before any vendoring, redistribution or public serving |
| **Proposed destination** | `docs/OSS_HARVEST_LOG.md` (as a worked precedent); a new data-provenance section in `docs/DATA_SOURCE_MATRIX.md` |
| **Status** | **PROPOSED — NOT IMPLEMENTED** · **LEGAL REVIEW REQUIRED** |

## KN-05 · Data pipeline gate lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-05-VALIDATION-MUST-GATE-PUBLICATION` |
| **Lesson** | Validation that runs **after** publication, or that does not run at all, is documentation rather than a control. Four independent gate failures were verified in one project: (a) **data-mutating commits trigger zero runs and zero check-runs** — all three 2026-09-13 bot commits, because the scheduled run was already in flight against an older `head_sha` when it pushed them; (b) the taxonomy check declares `needs:` **all four** mutating jobs, so it starts last (15:10:43, after the 15:10:12 push) and **cannot block**; (c) it has failed on **ten consecutive runs across 42 days** (2026-08-02 → 2026-09-13) with the data published throughout; (d) a purpose-built **`Identifier Validation` workflow ran twice successfully on a feature branch and was never merged** — the validator arrived via PR #159, the automation did not, so validation on `main` is manual-only. Plus a **blind spot**: the taxonomy check's own `notna()` filter excludes 8 of the 14 orphan-taxonomy rows and all 40,045 rows with an empty `industry`, so it inspects ~64% of the corpus and **a green run would not mean the taxonomy is consistent**. |
| **Source** | `.github/workflows/database_update.yml` (`needs:` list, job order), `.github/workflows/testing.yml` (deselect into a side job), GitHub Actions API, local replication of the CI check |
| **Evidence** | `evidence/followup/d_gics_sequence.json` (25 runs × per-job conclusions); `evidence/followup/f5_gics_replication.json` (**10** invalid rows, classified 6+2+2, `WORKFLOW_WOULD_RAISE=true`); workflow API for `Identifier Validation` (id 312400597, 2 runs, both `pull_request` on `feature/validate-identifiers`, both `success`; **0** commits touch that path on the default branch); `git log -- financedatabase/validation` → `5ae2910`, PR #159; document 22 §22.1–22.7 |
| **Confidence** | **HIGH** — every element execution-verified; **U-12 is closed** by re-execution rather than by log retrieval |
| **AHOS relevance** | **HIGH.** Four transferable rules: (1) validate **before** publish and make it **blocking**; (2) run validation **on the data-changing commit itself** — a gate that only fires on code commits is not a data gate; (3) **publish the coverage of an invariant alongside its result** — "0 failures over 64% of rows" is a different claim from "0 failures"; (4) if you build an automation and do not merge it, **delete the registration or merge it** — a stale `active` workflow entry misleads auditors (this follow-up initially treated it as a live gate and had to disprove that). Note the positive counterweight: the project's invariant tests **did** catch `CHAD` and fail loudly and publicly, which is why this investigation could find it at all. **Failing visibly is a transparency credit; not gating is the defect** |
| **Proposed destination** | `docs/OPERATOR_VALIDATION_PROTOCOL.md`; `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md`; `AHOS_LOCAL_PRODUCTION_GATE_REPORT.md` precedent section |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-06 · Missing-data and null semantics lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-06-NULL-SEMANTICS` |
| **Lesson** | Null handling is a **key-integrity** issue, not a cosmetic one, and a system can have **three different nulls** that look identical downstream. Verified: pandas' default NA inference turned the legitimate ticker **`NA`** (Nano Labs Ltd Class A Ordinary Shares) into `NaN` under release-2.4.0 semantics. **Precision matters here:** the row is **not deleted** — row counts are identical (112,690 either way) and cell-level NaN divergence is **empty**; the record survives with a **null primary key**, so `"NA" in index` is `False` and `.loc["NA"]` raises `KeyError`. It is only *dropped* when something filters on the key, which `to_toolkit()` does via `self[self.index.notna()]`. **A row-count check therefore cannot detect this defect** — only a key-nullness assertion can. The same class of bug had already fired twice more per the project's own workflow comment (`"9763"` → `"9763.0"`, `"031162100"` → `"31162100.0"`, which *"dropped that row on every run"*). Separately, the pipeline writes the **literal string** `nan` into 11 fields of new tickers (`np.nan` → CSV), so "empty cell", "literal `nan`" and "true NaN" coexist. And the CI check itself still reads without `keep_default_na=False`, which is why 2 of the 10 failing rows show `exchange='nan'` — **the library was fixed; the pipeline was not.** |
| **Source** | `database/equities/NMS.csv:4346`; release vs `main` `helpers.py`; `database_update.yml:139,148-157,196-202`; dual-read experiment |
| **Evidence** | `evidence/followup/f3_na_regression.json` (`C4_source_records_with_symbol_NA`, `C5_release_rows=112690`, `C6_main_rows=112690`, `C5_release_index_nan_count=1`, `C6_main_index_nan_count=0`, `C5_release_NA_in_index=false`, `C5_release_loc_NA="KeyError: 'NA'"`, `C5_cell_level_divergence={}`, `C10_ONLY_EQUITIES_AFFECTED=true`); `evidence/followup/f5_gics_replication.json` (`by_exchange` includes `'nan': 2`); document 21, document 20 FIX-06 |
| **Confidence** | **HIGH** — reproduced in two independent environments; scope measured across all seven asset classes (equities only, 1 record) |
| **AHOS relevance** | **HIGH — the most immediately actionable lesson in this package.** Four transferable rules: (1) read identifier-bearing text with **`dtype=str, keep_default_na=False, na_values=[""]`** and declare exactly one null token; (2) **assert after parsing that no key column is null** — a row count is not a health check; (3) treat any `notna()`-style filter as **load-bearing** and log what it discards; (4) fix **every** reader, including scripts and CI, not only the library. Maps directly onto AHOS's `UNKNOWN_VALUE = None` discipline and `unknown_fields` in `architecture/providers/contracts.py` — AHOS's contract is *structurally* stronger than this dataset's, which has no `UNKNOWN` concept at all |
| **Proposed destination** | `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md`; `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; fixture FIX-06 |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-07 · Provenance lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-07-PROVENANCE-BY-ABSENCE` |
| **Lesson** | A widely-used, 9,119-star dataset can have **zero** provenance, and its quality can still be high — the two are independent. Verified by a column-name scan for `date|time|updated|asof|timestamp|snapshot|version|source|provider|retrieved` across **all seven** schemas: **0 matches** in **304,495 rows**. There is no way to determine from a record when it was observed, who supplied it, or which version of the corpus it came from; the data is pinned to a **mutable branch** (`DATA_REPO` hardcodes `main`), there are **no artifact checksums**, and no schema-version field. Consequently `STALE ≠ LIVE` cannot be *enforced* on this data — only assumed. The counterweight worth recording: where the project **does** make a provenance-adjacent claim it is excellent — its own validator found **2 invalid values in 249,085 identifiers (99.9992% valid)**, and `mtime=0` gzip makes its artifacts byte-reproducible. **Correctness and traceability are different properties, and a dataset can have one without the other.** |
| **Source** | All seven schemas; `financedatabase/helpers.py:12-14`; the project's validator; the categorization job |
| **Evidence** | `evidence/followup/f1_objective_a.json` (`A7_total_temporal_columns_found=0`, `A7_NO_TIMESTAMPS_ANYWHERE=true`, `A7_total_rows_all_schemas=304495`); `evidence/identifier_issues.csv` (2 rows, both `actionable=False`); `evidence/followup/f5_gics_replication.json`; `database_update.yml:373-377` (`mtime=0` with the project's own rationale comment); document 07, document 19 §A-7 |
| **Confidence** | **HIGH** |
| **AHOS relevance** | **HIGH.** AHOS's contract already requires what this dataset lacks — `source_provider`, `retrieved_ts`, `raw_payload_sha256`, and `IdentitySource(provider, chain, address, retrieved_ts, source_ts, kind)`. Two transferable rules: (1) **provenance must be captured at ingest, because it cannot be reconstructed later** — there is no amount of downstream analysis that recovers a missing timestamp; (2) **synthesize provenance for third-party data that lacks it** (source, commit SHA, artifact hash, ingest time) and mark the record's confidence accordingly, rather than inheriting the source's silence. Also: deterministic artifacts (T-6) are a **precondition** for hash-based provenance — without `mtime=0`, a hash proves nothing |
| **Proposed destination** | `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `docs/DATA_SOURCE_MATRIX.md`; `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-08 · Freshness lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-08-FRESHNESS-MUST-BE-MEASURED-NOT-ASSUMED` |
| **Lesson** | Freshness is a **per-subset** property, and a single update cadence can coexist with permanently frozen subsets. Verified: the pipeline runs **Sunday 12:00 UTC** and updates **US equities only** (three `pd.read_json` calls to `rreichel3/US-Stock-Symbols/main/{nasdaq,nyse,amex}`); README:467 states non-US changes *"depend on community members"*; and **no workflow writes `database/cryptos.csv` at all** — it is read, re-compressed, categorised and counted by three of five jobs, but its **content is never updated from any source**. So the crypto table has the *appearance* of maintenance and none of the substance. Independent evidence of the resulting staleness: **`SOL` is absent** (`select(cryptocurrency="SOL")` → `ValueError`), Solana appears only as **`SOL1`** (10 rows), **51 of 73** probed modern tokens are absent including **every** Solana-ecosystem token, and **`SRM`** (Serum, collapsed 2022) is still present with no delisting flag. A second, subtler freshness trap: the **official website still advertises 158,429 equities** while the data and the auto-generated README both report **112,690** — a 29% divergence in the project's own published freshness signal. |
| **Source** | `.github/workflows/database_update.yml:167,173,179,313,315,379,388,523`; README:465,467; the cryptos table; the project website |
| **Evidence** | `to_csv` target enumeration (only `database/equities/{exchange}.csv` and `database/equities/NAN.csv` are written under `database/`); `evidence/followup/f1_objective_a.json` (`A3_SOL_rows=0`, `A4_SOL1_rows=10`, `A5_present_count=22`, `A5_absent_count=51`, `A5_ALL_SOLANA_ECOSYSTEM_ABSENT=true`, `A9_ALL_NEGATIVE=true`, `A7_cryptos_exchange_counts` CCC-dominant); library-level `ValueError` for `SOL`; document 08, document 19 §A-3/A-4/A-8 |
| **Confidence** | **HIGH** for the mechanism and the absences; **MEDIUM** for the inferred ~2020 vintage of the crypto table (inferred from token composition and `CCC` codes — **not verified**, U-04) |
| **AHOS relevance** | **HIGH.** Three transferable rules: (1) **measure freshness per subset, never per source** — one cadence does not imply uniform currency; (2) **an update job that touches a file is not evidence that the file's content is updated** — verify the *write target*, not the *reference count*; (3) **a source's own published statistics are a freshness signal that must itself be checked** — the website's 158,429 was stale by 29%. For AHOS this maps onto `IdentityState.STALE` and `IdentitySource.source_ts` vs `retrieved_ts`: a record needs **both** an observation time and a source-asserted time, and the absence of either means `STALE`/`UNKNOWN`, never "probably fine" |
| **Proposed destination** | `docs/DATA_SOURCE_MATRIX.md` (freshness column, per subset); `docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md` |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-09 · External provider attribution lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-09-ATTRIBUTION-AND-CAPABILITY-SEPARATION` |
| **Lesson** | Attribute capability to the component that actually provides it, and treat an unattributable measurement as **not evidence**. Three verified cases: (a) **capability mis-attribution** — fundamentals (statements, ratios) belong to **FinanceToolkit / FMP / Yahoo**, not to FinanceDatabase, which calls **no API at all**; its entire network surface is **two** `requests.get` calls for static files, and the shipped package contains **zero** occurrences of `eval`, `exec`, `pickle`, `marshal`, `subprocess`, `os.system`, `socket`, `ctypes` or `open(`. (b) **dependency mis-declaration** — `financetoolkit` is a **hard** declared dependency but is imported **lazily** only inside `to_toolkit()`, while `numpy`, `pandas` and `requests` are imported directly yet **undeclared**; so the versions of the libraries that actually do the work are governed by a *transitive* dependency. (c) **attribution failure as a reason not to measure** — `financetoolkit` was deliberately **not installed**, so `to_toolkit()` end-to-end latency was recorded as **NOT TESTED** rather than reported as a number that would have mixed FinanceDatabase, FinanceToolkit, `yfinance` and network time with no way to separate them. A fourth, newly-sharpened case: (d) **the tested configuration is not the shipped configuration** — CI resolves via `uv sync` to `financetoolkit 2.0.7` + `pandas 2.3.3` on **Python 3.10**, while a fresh `pip install` on Python ≥3.11 resolves to `financetoolkit 2.2.0` + `pandas>=3.0` + an **unpinned `yfinance`**. The 85 passing tests therefore attest to a configuration no user receives. |
| **Source** | `financedatabase/helpers.py:65,336` and full-package grep; `pyproject.toml`; `uv.lock:551,592,1005,1069,1285,1329,2025`; `.github/workflows/testing.yml:27`; PyPI release metadata |
| **Evidence** | document 11 §11.1 (dangerous-call census = **zero**), document 19 §A-11; `uv.lock` pins re-verified this session (`financetoolkit 2.0.7`, `pandas 2.3.3` **and** `pandas 3.0.3` under separate markers, `pytest 9.0.3`, `pytest-recording 0.13.4`, `vcrpy 8.1.1`); `testing.yml` `python-version: '3.10'` read verbatim; PyPI `financetoolkit 2.2.0` (2026-08-18) `requires_python >=3.11,<3.16`, `pandas>=3.0`, `yfinance` unpinned; document 09 EI-01…EI-04 |
| **Confidence** | **HIGH** |
| **AHOS relevance** | **HIGH.** Four transferable rules: (1) **record the capability boundary of every provider explicitly** — AHOS's `BaseMarketProvider.capabilities` list is exactly this instrument, and an honest value for a static catalogue would be `[]`; (2) **a hard dependency that is lazily imported is a packaging defect** — declare what you import, import what you declare; (3) **do not publish a measurement you cannot attribute** — `NOT TESTED` with a reason is more useful than a plausible number, and this investigation used that rule twice (here, and for the decompression-bomb PoC declined as an attack on a third party); (4) **verify that the tested configuration equals the shipped configuration** — a green CI on a lockfile that users do not get is not evidence about what users get. This last rule was **demonstrated live** in this follow-up: with `pytest-recording` absent the suite returned **87 spurious errors**, and only the `uv.lock`-exact stack reproduced `1 failed, 85 passed` |
| **Proposed destination** | `docs/DATA_SOURCE_MATRIX.md`; `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` (provider contracts section) |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

## KN-10 · Research-only integration boundary lessons

| Field | Value |
|---|---|
| **Knowledge ID** | `KN-10-RESEARCH-ONLY-BOUNDARY` |
| **Lesson** | A research investigation can be **completed, decisive and useful while changing nothing** — and the boundary that makes this possible has to be designed, not improvised. Verified practice from this investigation: all work was confined to `research/finance_database_investigation/` and to `/tmp` research environments; the AHOS tree was accessed **read-only**; the one AHOS module that was *imported* (`architecture/providers/contracts.py`) was first confirmed **stdlib-only** so the import could not trigger side effects; the upstream repository was cloned and only read (no push, no `--apply`, the validator run dry-run); and `financetoolkit` was left uninstalled to preserve attribution. A structural boundary also proved its worth: the crypto rejection did **not** rest on a judgement call but on a **type contract** — `NormalizedTokenCandidate` requires `chain` and `address`, FinanceDatabase has neither, so an adapter must fabricate (violating the contract's own stated law, *"Missing or uncollected data is NEVER guessed"*) or pass `None` (which crashes the router's real dedupe key with `AttributeError: 'NoneType' object has no attribute 'lower'`). **A well-designed required-field contract makes an unsound integration impossible to write, which is stronger than any policy document.** |
| **Source** | This investigation's own execution record; `architecture/providers/contracts.py`; `architecture/providers/registry.py`; `evidence/scripts/f2_a10_contract.py` |
| **Evidence** | `evidence/followup/f2_a10_contract.json` (`NTC_required_fields=['chain','address','symbol','name']`, `T1_message="TypeError: … missing 2 required positional arguments: 'chain' and 'address'"`, `T2_dedupe_key_raises="AttributeError: 'NoneType' object has no attribute 'lower'"`, `T3_registry_dedupe_line=["key = (c.chain, c.address.lower())"]`, `T5_MarketMetrics_satisfiable_from_fdb=[]`, `T5_SecuritySignals_satisfiable_from_fdb=[]`); `evidence/ENVIRONMENT.txt` + `evidence/FOLLOWUP_ENVIRONMENT.txt` (isolation record); `git status` verification that the only new files are under `research/finance_database_investigation/`; document 14 §14.2, §14.5 (B-1…B-18), §14.6; document 19 §19.1 |
| **Confidence** | **HIGH** — the boundary was exercised twice, and both times held |
| **AHOS relevance** | **HIGH.** Five transferable rules: (1) **keep research artifacts inside a designated research path** and make "no production file changed" a *verifiable* claim (`git status` + a whitespace-insensitive diff), not an assertion; (2) **before importing any module from a protected tree, confirm it cannot have side effects** — and prefer reading source text to importing; (3) **required-field contracts are a safety mechanism** — making `chain`/`address` non-defaulted is what turned a policy ("never guess") into a `TypeError`; (4) **record declined tests with reasons** (`NOT TESTED` is a result); (5) **an investigation's output may be "do nothing", and that is a complete deliverable** — the judgment here is `C / E / NOT APPROVED / NOT IMPLEMENTED`, and the value delivered is ten reusable techniques, six proposed fixtures and one closed unknown, none of which required touching production. **One durability gap was found and fixed:** the original evidence lived in `/tmp` and did not survive one session, so machine-readable outputs and the environment record are now archived under `evidence/followup/` |
| **Proposed destination** | `docs/architecture/PROCESS_ISOLATED_RESEARCH_WORKER.md`; `docs/architecture/RESEARCH_ANALYST_AGENT.md`; `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `AGENTS.md` (research-safety section) |
| **Status** | **PROPOSED — NOT IMPLEMENTED** |

---

## 24.1 Summary table

| ID | Lesson (short) | Confidence | AHOS relevance | Proposed destination | Status |
|---|---|---|---|---|---|
| **KN-01** | Namespace every key; corroboration is absent where most needed | HIGH | HIGH | AGENT_09 + fixtures FIX-01/02/03 | **PROPOSED — NOT IMPLEMENTED** |
| **KN-02** | A symbol is an alias, not an identity | HIGH | HIGH | AGENT_09, CANONICAL_IMPLEMENTATION_MATRIX | **PROPOSED — NOT IMPLEMENTED** |
| **KN-03** | Pin code **and** data to the same immutable reference; a release is not a system snapshot | HIGH | HIGH | AHOS_UPDATE_POLICY, OPERATOR_VALIDATION_PROTOCOL | **PROPOSED — NOT IMPLEMENTED** |
| **KN-04** | A permissive code licence does not license the data; check transitive licences too | HIGH (facts) | HIGH | OSS_HARVEST_LOG, DATA_SOURCE_MATRIX | **PROPOSED — NOT IMPLEMENTED** · **LEGAL REVIEW REQUIRED** |
| **KN-05** | Validation must gate publication, run on data commits, and publish its coverage | HIGH | HIGH | OPERATOR_VALIDATION_PROTOCOL, AGENT_07 | **PROPOSED — NOT IMPLEMENTED** |
| **KN-06** | Null semantics are key-integrity; row counts cannot detect a null key | HIGH | **HIGH — most actionable** | AGENT_07, AGENT_EVIDENCE_PROTOCOL, FIX-06 | **PROPOSED — NOT IMPLEMENTED** |
| **KN-07** | Provenance must be captured at ingest; it cannot be reconstructed later | HIGH | HIGH | AGENT_EVIDENCE_PROTOCOL, DATA_SOURCE_MATRIX | **PROPOSED — NOT IMPLEMENTED** |
| **KN-08** | Freshness is per-subset; a job touching a file is not evidence its content updates | HIGH / MEDIUM (vintage) | HIGH | DATA_SOURCE_MATRIX, AGENT_08 | **PROPOSED — NOT IMPLEMENTED** |
| **KN-09** | Attribute capability precisely; never publish an unattributable measurement | HIGH | HIGH | DATA_SOURCE_MATRIX, AGENT_EVIDENCE_PROTOCOL, AGENT_07 | **PROPOSED — NOT IMPLEMENTED** |
| **KN-10** | Required-field contracts make unsound integrations unwritable; research can deliver without changing anything | HIGH | HIGH | PROCESS_ISOLATED_RESEARCH_WORKER, RESEARCH_ANALYST_AGENT, AGENT_EVIDENCE_PROTOCOL, AGENTS.md | **PROPOSED — NOT IMPLEMENTED** |

**All ten items: `PROPOSED — NOT IMPLEMENTED`. Implementation authorized: NO.**
**One item (KN-04) additionally requires legal review before any action.**

**Destinations named above are proposals. No file at any of those paths was read for modification or
written to by this investigation.**
