# 26 — AHOS Knowledge Registry

**Document 26 · Extraction package deliverable 1 of 5.**

| Role | Agent | Function in this document |
|---|---|---|
| Author | **Agent E — Evidence Authority** | Registers only knowledge supported by located evidence; classifies status and confidence; refuses to register anything unsupported |
| Mandatory reviewer | **Agent B — Engineering Governor** | Gate owner. **No item in this registry may be promoted to AHOS policy, code, fixture or dependency without Agent B review and separate written authorization** |

> ## ⚠️ REGISTRATION ONLY — NOTHING IMPLEMENTED
>
> This is a **read-only** extraction and registration pass. No fixture, adapter, dependency,
> workflow, provider, schema or code change was created. `architecture/`, `architecture/identity/`,
> scoring, decision authority, providers, schemas, paper trading, runtime, `tests/`, `tests2b/`,
> `requirements.txt` and package configuration were **not modified**. `README.md` was **not
> modified**. No server was started. The 72-hour soak was not disturbed. No package was installed
> into the AHOS environment. FinanceDatabase was **not** added as a provider. No crypto adapter was
> created. FIX-01…FIX-06 were **not** implemented. KN-01…KN-12 were **not** promoted to policy.
> No secret was stored.

---

## 26.0 Registry doctrine — evidence ≠ score ≠ decision ≠ outcome

This distinction is load-bearing and is preserved on **every** row below. The four are different
objects with different owners, and conflating them is how an audit becomes an assertion.

| Term | Definition | Who owns it | What it is **not** |
|---|---|---|---|
| **EVIDENCE** | A located, reproducible observation: command + environment + version + output + limitation | Agent E | Not a judgement. Not a ranking. `"SOL" not in index` is evidence; "crypto data is bad" is not |
| **SCORE** | A derived numeric or ordinal assessment computed **from** evidence under a stated rubric | Rubric owner | Not evidence. Not a decision. The 1.13/5.00 decision matrix in document 00 is a *score*; it does not itself prove anything |
| **DECISION** | An authorization act taken **on** scores and evidence by an accountable owner | AHOS owner / Agent B | Not an outcome. Not a measurement. `Crypto = REJECTED` is a decision; it is not a property of the data |
| **OUTCOME** | What actually happened in production after a decision was enacted | Reality | Not a decision. **A decision can be correct and still produce a bad outcome, and a bad decision can produce a good outcome by luck** |

**Worked example, carried through all four — the `NA` ticker:**

| Layer | Statement |
|---|---|
| **EVIDENCE** | `f3_na_regression.json`: `C5_release_rows = 112690`, `C6_main_rows = 112690`, `C5_cell_level_divergence_empty = true`, `C5_release_index_nan_count = 1`, `C5_release_NA_in_index = false`, `C5_release_loc_NA = "KeyError: 'NA'"` |
| **SCORE** | Severity: **key-integrity defect, silent, undetectable by row count** → high severity, low detectability |
| **DECISION** | Register rule candidate **DQR-04** (document 28) and fixture **FIX-06** (document 27); **do not** implement either. `Implementation authorized: NO` |
| **OUTCOME** | **NONE — no outcome exists.** Nothing was enacted, so nothing can be measured. Any future claim about AHOS behaviour on `NA`-like keys must come from an executed test, not from this row |

**Registry rule derived from this doctrine:** an item may be registered at **VERIFIED** on the
strength of its *evidence* while its *decision* remains **NOT AUTHORIZED** and its *outcome*
remains **UNMEASURED**. Those three fields never inherit each other's value.

### 26.0.1 Second registry rule — no AHOS defect is claimed anywhere

Every item below is derived from a **third-party** dataset and codebase (FinanceDatabase @
`a174c97d3bba96fc1a82b2e1068fb3ec5e02e634`). Where an item implies an AHOS-side observation, that
observation is labelled **AHOS-SIDE OBSERVATION (PROPOSED)** and is never phrased as a failure. No
FinanceDatabase record is an AHOS production failure. AHOS's crypto identity domain is
`(chain, address)`; FinanceDatabase's TradFi domain is `symbol`; they do not overlap.

---

## 26.1 Status vocabulary (mandated)

| Status | Meaning in this registry |
|---|---|
| **VERIFIED** | Re-executed in a rebuilt environment at the pinned commit; result reproduced; evidence located to a file/line/JSON key |
| **PARTIALLY_VERIFIED** | The core claim reproduced, but at least one component rests on inference, on a proxy measurement, or on a scope narrower than stated |
| **UNVERIFIED** | Asserted somewhere in the package but **not** re-executed; no located evidence |
| **UNKNOWN** | Not determinable from outside; recorded in the unknowns ledger (document 25 §25.4) |
| **BLOCKED** | Determination was attempted and prevented by an external constraint (unreachable host, prohibited install, declined test) |
| **STALE** | Was true when measured but the subject has since changed, or the measurement cannot be re-taken |
| **SUPERSEDED** | Replaced by a later correction; retained for audit trail only, must not be cited |
| **PLANNED** | Registered as a proposal awaiting review; no work performed |
| **REJECTED** | Considered and refused; the refusal is itself the record |

## 26.2 Confidence vocabulary

| Confidence | Basis |
|---|---|
| **HIGH** | Execution-verified, reproducible offline from a pinned artifact, and independently corroborated (a second measurement, the project's own test, or git provenance) |
| **MEDIUM** | Execution-verified once, or verified but with a stated scope limitation |
| **LOW** | Source-read only, single observation, or dependent on an unverified premise |
| **NONE ASSERTED** | Deliberately withheld — used for legal conclusions, where the package states facts and refuses verdicts |

---

## 26.3 Knowledge registry

Twelve items are registered. **KN-01…KN-10** carry forward from document 24 (Objective G) with
status and confidence assigned here by Agent E rather than inherited. **KN-11 and KN-12 are new to
this pass** — they were discovered while re-reading the machine-readable evidence, and are the
reason a registration pass must re-open the evidence rather than re-open the prose.

---

### KN-01 · Namespace every key; corroboration is absent exactly where it is most needed

| Field | Value |
|---|---|
| **KN-ID** | `KN-01-IDENTITY-COLLISION` |
| **Title** | Unnamespaced keys silently merge distinct entities, and the corroborating identifier is missing on the primary records |
| **Source document** | 24 §KN-01; 20 CASES 1–2; 13 S-01/S-07; 22 §22.3 |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `CHAD`, `cross_asset_symbol_collisions` (n=1 pair), `BRK_all_rows` (7), `BRK_distinct_exchanges=['ASE','MEX','NYQ','VIE']`, `BRK_all_isin_empty=true`; upstream's own invariant test fails on `CHAD` at `tests/test_invariants.py:95`, reproduced `1 failed, 85 passed, 1 deselected in 42.43s`; AHOS counterweight verified read-only at `architecture/providers/registry.py` → `key = (c.chain, c.address.lower())` |
| **Status** | **VERIFIED** |
| **Confidence** | **HIGH** — execution-verified twice in two independently built environments against an unmoved HEAD, and independently corroborated by the upstream project's own failing test |
| **Affected AHOS area** | `architecture/identity/types.py:42-83` (`TokenIdentity`, `IdentityResolution.conflicts`), `architecture/identity/resolution.py:58` (`_sources_conflict`), `architecture/providers/registry.py` (dedupe key). **Read-only inspection; no modification** |
| **Permitted use** | Cite as a design lesson. Use as the basis for **reviewing** whether AHOS's composite key discipline holds under adversarial input. Reference in Agent B discussion of FIX-01/FIX-02 |
| **Prohibited use** | Must **not** be cited as an AHOS defect. Must **not** be used to justify adding a symbol-keyed path. Must **not** be quoted as a benchmark, score or outcome. Must **not** license any change to `registry.py` or `resolution.py` |
| **Reviewer required** | **YES — Agent B (Engineering Governor)** before any promotion. No legal review required (no identifier values are embedded) |

---

### KN-02 · A symbol is an alias, not an identity

| Field | Value |
|---|---|
| **KN-ID** | `KN-02-SYMBOL-IS-NOT-IDENTITY` |
| **Title** | Four measured failure modes of symbol-as-key, and a default-confidence hardening observation |
| **Source document** | 24 §KN-02; 20 CASES 2–4; 19 §A-4 (FOLLOWUP-01); 05 |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `MMM_count=18`, `MMM_distinct_names` (5 strings / 4 entities), `ISIN_max_fanout=57`, `ISIN_fanout_gt_1=5181`, `distinct_bare_tickers=74690`, `bare_tickers_appearing_more_than_once=16251`; `evidence/followup/f1_objective_a.json` → `sample_fdb_cryptos_row` (`cryptocurrency='SOL1'` vs `summary='Solana (SOL) is a cryptocurrency.'`), `A6_collisions=86`; `evidence/followup/f2_a10_contract.json` → `T2_confidence_level='HIGH'`, `T2_n_unknown_fields=33`; AHOS side verified read-only at `architecture/identity/types.py:44` (`address_canonical`) vs `:47` (`symbol_alias`), and `architecture/providers/contracts.py:74` (`confidence_level: str = "HIGH"`) |
| **Status** | **VERIFIED** for the four dataset failure modes · **PARTIALLY_VERIFIED** for the AHOS-side hardening observation (the default is verified as code fact; whether it is a *problem* is a design question, not an evidenced finding) |
| **Confidence** | **HIGH** (dataset) · **MEDIUM** (AHOS-side observation — single code-level observation, no executed failure in AHOS) |
| **Affected AHOS area** | `architecture/providers/contracts.py:74`; `architecture/identity/types.py:44,47`. **AHOS-SIDE OBSERVATION (PROPOSED) — not a defect claim** |
| **Permitted use** | Cite as a lesson on alias-vs-key separation. Raise the `confidence_level` default as a **design question** for the AHOS owner in an Agent B review. Reference in FIX-03/FIX-05 discussion |
| **Prohibited use** | Must **not** be recorded as an AHOS bug, regression or finding. Must **not** be used to change the default without review. Must **not** be presented as evidence that AHOS has mis-resolved any identity |
| **Reviewer required** | **YES — Agent B**, and explicitly the **AHOS owner** for the `confidence_level` design question. Not a legal matter |

---

### KN-03 · Pin code *and* data to the same immutable reference; a release is not a system snapshot

| Field | Value |
|---|---|
| **KN-ID** | `KN-03-RELEASE-VERSUS-MAIN` |
| **Title** | Release/branch divergence can invert the safe choice: the pinned release carried the defect, the unpinned branch carried the fix |
| **Source document** | 24 §KN-03; 21 §21.8–21.9; 25 §25.2 (Objective C) |
| **Evidence reference** | `evidence/followup/f3_na_regression.json` → `C3_line_count_release=358` / `C3_line_count_main=366`, `C3_package_diff`, `C9_commits_introducing_keep_default_na` (exactly one: `3b8eb8390959bec6a360a620333b6fe5217a4618`, 2026-08-07T10:32:18Z, Jon Højlund Arnfred, PR #166); git ancestry `merge-base --is-ancestor 3b8eb83 2.4.0` → **NO**, `… HEAD` → **YES**; tag `2.4.0` = `51226b86758b116fb9e1065645c62fcb342af2f5`; PyPI upload 2026-06-02T14:05:45Z (fix is **66 days later**); artifact SHA-256 re-hashed and **MATCH** |
| **Status** | **VERIFIED** |
| **Confidence** | **HIGH** — git-proven, not inferred; artifact hashes independently re-verified this session |
| **Affected AHOS area** | `AHOS_UPDATE_POLICY.md`; `docs/OPERATOR_VALIDATION_PROTOCOL.md`; `docs/OSS_HARVEST_LOG.md`; dependency-pinning practice generally. **Documents only — none was written to** |
| **Permitted use** | Cite when reviewing any AHOS dependency-pinning or vendoring proposal. Supports boundary rules B-6/B-7 (document 14 §14.5) |
| **Prohibited use** | Must **not** be used to justify installing or vendoring FinanceDatabase. Must **not** be treated as authorization to alter `requirements.txt` or `package.json` |
| **Reviewer required** | **YES — Agent B**, because the lesson implies a policy change to update procedure |

---

### KN-04 · A permissive code licence does not license the data the code serves

| Field | Value |
|---|---|
| **KN-ID** | `KN-04-DATASET-VS-CODE-LICENSING` |
| **Title** | Four-layer licence separation: code / data / upstream / transitive dependency |
| **Source document** | 24 §KN-04; 19 §19.4–19.6; 23 §23.0; 12 LEG-01…LEG-03; **29 (this package) — full review queue** |
| **Evidence reference** | MIT verified four ways (repo `LICENSE` 21 lines `Copyright (c) 2023 Jeroen Bouma`; `pyproject.toml:5`; PyPI `info.license`; both artifacts); absence of `NOTICE`/`DATA-LICENSE`/ODC/CC0/CLA/DCO verified by `find` over the whole tree; upstream `rreichel3/US-Stock-Symbols` `license=None`, 574 stars, `pushed_at 2026-09-15T00:39:12Z`; `CONTRIBUTING.md:129` verbatim MSCI/GICS disclaimer; `financedatabase/validation/validate_identifiers.py:13` → `from stdnum import cusip, figi, isin`; **`python-stdnum` 2.2 = LGPL-2.1+** |
| **Status** | **VERIFIED** (the facts) · **BLOCKED** (the legal conclusions — determination requires counsel, which is outside this pass) |
| **Confidence** | **HIGH** for facts · **NONE ASSERTED** for legal conclusions, by design |
| **Affected AHOS area** | `docs/OSS_HARVEST_LOG.md`; `docs/DATA_SOURCE_MATRIX.md`; `requirements.txt` law (*"free, permissively licensed"*) — **read, not modified** |
| **Permitted use** | Cite the **facts** in a legal-review packet. Use as the precedent case for separating code-licence and data-licence fields at harvest time |
| **Prohibited use** | Must **not** be paraphrased as a legal conclusion, clearance or opinion. Must **not** be used to authorize vendoring, mirroring, redistribution or public serving. Must **not** be cited as evidence that any use is lawful |
| **Reviewer required** | **YES — Agent B AND qualified legal counsel.** Routed as document **29_LICENSE_AND_PROVENANCE_REVIEW_QUEUE.md**, all nine categories `LEGAL REVIEW REQUIRED` |

---

### KN-05 · Validation must gate publication, run on the data-changing commit, and publish its coverage

| Field | Value |
|---|---|
| **KN-ID** | `KN-05-VALIDATION-MUST-GATE-PUBLICATION` |
| **Title** | Four independent gate failures plus one blind spot, in a single actively maintained project |
| **Source document** | 24 §KN-05; 22 §22.1–22.7 (D-1…D-9); 25 §25.2 (Objective D) |
| **Evidence reference** | `evidence/followup/d_gics_sequence.json` (25 runs × per-job conclusions: **10** consecutive `Check-GICS-Categorisation` failures, #389 2026-08-02T17:20:15Z → #398 2026-09-13T15:07:37Z; last success #388 2026-08-02T12:47:55Z); `evidence/followup/f5_gics_replication.json` (`invalid_row_count=10`, `WORKFLOW_WOULD_RAISE=true`, `rows_with_full_gics_triple=72585`, `rows_excluded_missing_triple=40105`); 0 workflow runs and 0 check-runs on all three 2026-09-13 bot commits; `needs:` list in `.github/workflows/database_update.yml` puts the check **last** (started 15:10:43, after the 15:10:12 push); `Identifier Validation` workflow id `312400597`, 2 runs, both `pull_request` on `feature/validate-identifiers`, **0** commits touch that path on the default branch; validator itself merged via PR #159 (`5ae2910`) |
| **Status** | **VERIFIED** |
| **Confidence** | **HIGH** — every element execution- or API-verified; U-12 **closed by re-execution** after the CI log host proved unreachable |
| **Affected AHOS area** | `docs/OPERATOR_VALIDATION_PROTOCOL.md`; `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md`; `AHOS_LOCAL_PRODUCTION_GATE_REPORT.md` precedent section. **None written to** |
| **Permitted use** | Cite when reviewing whether an AHOS data gate is *blocking*, *fires on data commits*, and *reports its own coverage*. The positive counterweight is equally citable: the upstream invariant tests **did** catch `CHAD` and fail loudly in public — **failing visibly is a transparency credit; not gating is the defect** |
| **Prohibited use** | Must **not** be extrapolated into a general claim that CI-based validation is unreliable. Must **not** be used to assert that any AHOS gate is defective. Must **not** allege maintainer negligence — U-19 records the cause as UNKNOWN |
| **Reviewer required** | **YES — Agent B** |

---

### KN-06 · Null semantics are key-integrity; a row count cannot detect a null key

| Field | Value |
|---|---|
| **KN-ID** | `KN-06-NULL-SEMANTICS` |
| **Title** | Three visually identical nulls, and a defect that survives every row-count check |
| **Source document** | 24 §KN-06; 21 (whole); 20 FIX-06; 13 S-13/S-19 |
| **Evidence reference** | `evidence/followup/f3_na_regression.json` → `C4_source_records_with_symbol_NA` (**`database/equities/NMS.csv:4346`**, Nano Labs Ltd Class A), `C4_count=1`, `C5_release_rows=C6_main_rows=112690`, `C5_cell_level_divergence_empty=true`, `C5_release_index_nan_count=1` / `C6_main_index_nan_count=0`, `C5_release_NA_in_index=false`, `C5_release_loc_NA="KeyError: 'NA'"`, `C6_main_NA_in_index=true`, `C10_ONLY_EQUITIES_AFFECTED=true`; `evidence/followup/f5_gics_replication.json` → `by_exchange` contains `'nan': 2` (the CI script still reads without `keep_default_na=False` — **the library was fixed; the pipeline was not**); re-confirmed independently this pass (`'NA' in set(dfault.index.astype(str))` → `False`; row survives `dropna(how='all')`) |
| **Status** | **VERIFIED** |
| **Confidence** | **HIGH** — reproduced in two independent environments; scope measured across all seven asset classes |
| **Affected AHOS area** | Any AHOS ingest of identifier-bearing text; `architecture/providers/contracts.py:5,16` (the *"Missing or uncollected data is NEVER guessed"* law and `UNKNOWN_VALUE = None`) — verified read-only as the **stronger** existing AHOS discipline |
| **Permitted use** | Cite as the evidential basis for rule candidates **DQR-01…DQR-04** (document 28) and fixture **FIX-06** (document 27). **Most immediately actionable lesson in the package** |
| **Prohibited use** | Must **not** be implemented without Agent B authorization. Must **not** be cited as evidence that AHOS ingest is defective — no AHOS ingest path was tested |
| **Reviewer required** | **YES — Agent B** |

---

### KN-07 · Provenance must be captured at ingest; it cannot be reconstructed later

| Field | Value |
|---|---|
| **KN-ID** | `KN-07-PROVENANCE-BY-ABSENCE` |
| **Title** | Zero temporal columns in 305,495 rows — correctness and traceability are independent properties |
| **Source document** | 24 §KN-07; 19 §A-7; 07 |
| **Evidence reference** | `evidence/followup/f1_objective_a.json` → `A7_total_temporal_columns_found=0`, `A7_NO_TIMESTAMPS_ANYWHERE=true`, `A7_total_rows_all_schemas=305495`, per-class rows in `A7_temporal_scan`; column-name scan `date|time|updated|asof|timestamp|snapshot|version|source|provider|retrieved` over all seven schemas; `financedatabase/helpers.py:12-14` (`DATA_REPO` hardcodes `main`); `evidence/identifier_issues.csv` (2 rows, both `actionable=False`); `database_update.yml:373-377` (`mtime=0` gzip, with the project's own rationale comment) |
| **Status** | **VERIFIED** |
| **Confidence** | **HIGH** |
| **Affected AHOS area** | `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `docs/DATA_SOURCE_MATRIX.md`; `architecture/identity/types.py:24-33` (`IdentitySource` with `provider`, `chain`, `retrieved_ts`, `source_ts`, `kind`) — verified read-only as the **stronger** existing AHOS contract |
| **Permitted use** | Cite for the rule that provenance is an ingest-time obligation, and that third-party data lacking it must have provenance **synthesized** (source, commit SHA, artifact hash, ingest time) with confidence marked down — not inherited silently |
| **Prohibited use** | Must **not** be cited as a freshness claim about AHOS data. Must **not** be used to infer the vintage of any FinanceDatabase table (that is **U-04, UNKNOWN**) |
| **Reviewer required** | **YES — Agent B** |

> **Row-count note.** This item's evidence is the origin of correction **E-CORR-01** (§26.5): the
> machine-readable value is **305,495**, while the prose in ten documents states **304,495**. The
> registered value here is the **evidenced** one.

---

### KN-08 · Freshness is a per-subset property; a job touching a file is not evidence its content updates

| Field | Value |
|---|---|
| **KN-ID** | `KN-08-FRESHNESS-MUST-BE-MEASURED-NOT-ASSUMED` |
| **Title** | One weekly cadence coexisting with a permanently frozen table, and a 29% stale self-reported statistic |
| **Source document** | 24 §KN-08; 19 §A-3/A-4/A-8; 08 |
| **Evidence reference** | `evidence/followup/f1_objective_a.json` → `A3_SOL_rows=0`, `A4_SOL1_rows=10`, `A5_present_count=22` / `A5_absent_count=51`, `A5_ALL_SOLANA_ECOSYSTEM_ABSENT=true`, `A9_ALL_NEGATIVE=true` (0 of 16), `A7_cryptos_exchange_counts` (`CCC=3362` of 3367); library-level `select(cryptocurrency="SOL")` → `ValueError`; `to_csv` write-target enumeration (only `database/equities/{exchange}.csv` and `database/equities/NAN.csv`); `database_update.yml:167,173,179` (three `pd.read_json` to `rreichel3/US-Stock-Symbols/main/…`), `README:465,467`; project website advertises **158,429** equities vs **112,690** in data and auto-generated README |
| **Status** | **VERIFIED** (mechanism and absences) · **PARTIALLY_VERIFIED** (the ~2020 crypto vintage — **inferred** from token composition and `CCC` codes; **U-04 remains UNKNOWN**) |
| **Confidence** | **HIGH** (mechanism/absences) · **LOW** (vintage — inference only, explicitly not verified) |
| **Affected AHOS area** | `docs/DATA_SOURCE_MATRIX.md` (freshness column, **per subset**); `docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md`; `architecture/identity/types.py:19` (`IdentityState.STALE`) and `IdentitySource.source_ts` vs `retrieved_ts` |
| **Permitted use** | Cite the three rules: measure freshness **per subset**; verify the **write target**, not the reference count; treat a source's **own published statistics** as a freshness signal that must itself be checked |
| **Prohibited use** | Must **not** state or imply the crypto table's vintage as fact. Must **not** be cited as an AHOS freshness finding |
| **Reviewer required** | **YES — Agent B** |

---

### KN-09 · Attribute capability precisely; never publish a measurement you cannot attribute

| Field | Value |
|---|---|
| **KN-ID** | `KN-09-ATTRIBUTION-AND-CAPABILITY-SEPARATION` |
| **Title** | Four mis-attribution classes, including "the tested configuration is not the shipped configuration" |
| **Source document** | 24 §KN-09; 11 §11.1; 09 EI-01…EI-04; 19 §A-11 |
| **Evidence reference** | Dangerous-call census = **zero** occurrences of `eval`, `exec`, `pickle`, `marshal`, `subprocess`, `os.system`, `socket`, `ctypes`, `open(` in the shipped package; entire network surface = **two** `requests.get` calls for static files; `uv.lock` pins re-verified (`financetoolkit 2.0.7`, `pandas 2.3.3` **and** `3.0.3` under separate markers, `pytest 9.0.3`, `pytest-recording 0.13.4`, `vcrpy 8.1.1`); `.github/workflows/testing.yml` → `uv sync`, `python-version: '3.10'`; fresh `pip install` on ≥3.11 resolves `financetoolkit 2.2.0` + `pandas>=3.0` + **unpinned** `yfinance`; `financetoolkit` declared hard but imported lazily only in `to_toolkit()`, while `numpy`/`pandas`/`requests` are imported directly yet undeclared; **live demonstration this pass**: with `pytest-recording` absent the suite returned **87 spurious errors**, and only the `uv.lock`-exact stack reproduced `1 failed, 85 passed` |
| **Status** | **VERIFIED** · with one explicit **BLOCKED** measurement: `to_toolkit()` end-to-end latency = **NOT TESTED**, because `financetoolkit` was deliberately not installed to preserve attribution |
| **Confidence** | **HIGH** |
| **Affected AHOS area** | `docs/DATA_SOURCE_MATRIX.md`; `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `architecture/providers/contracts.py` (`BaseMarketProvider.capabilities`) — an honest value for a static catalogue would be `[]` |
| **Permitted use** | Cite the four rules, especially: **`NOT TESTED` with a reason is a result**, and is more useful than a plausible number. This investigation applied that rule twice (here, and for the decompression-bomb PoC declined as an attack on a third party) |
| **Prohibited use** | Must **not** be used to certify the package as "secure" — the correct language is **"no issue observed in reviewed scope"**, which is not the same claim. Must **not** publish any latency figure for `to_toolkit()` |
| **Reviewer required** | **YES — Agent B** |

---

### KN-10 · Required-field contracts make unsound integrations unwritable

| Field | Value |
|---|---|
| **KN-ID** | `KN-10-RESEARCH-ONLY-BOUNDARY` |
| **Title** | A type contract is a stronger safety mechanism than a policy document — and research can deliver without changing anything |
| **Source document** | 24 §KN-10; 19 §19.1; 14 §14.2/§14.5 (B-1…B-18)/§14.6 |
| **Evidence reference** | `evidence/followup/f2_a10_contract.json` → `ahos_contracts_is_stdlib_only=true`, `NTC_required_fields=['chain','address','symbol','name']`, `T1_construct_without_chain_address='TypeError'`, `T1_message="NormalizedTokenCandidate.__init__() missing 2 required positional arguments: 'chain' and 'address'"`, `T2_construct_with_None='SUCCEEDED — dataclass does not enforce str at runtime'`, `T2_dedupe_key_expression='(c.chain, c.address.lower())'`, `T2_dedupe_key_raises="AttributeError: 'NoneType' object has no attribute 'lower'"`, `T5_MarketMetrics_satisfiable_from_fdb=[]` (0 of 16), `T5_SecuritySignals_satisfiable_from_fdb=[]` (0 of 15); contract law verified at `architecture/providers/contracts.py:5`; isolation records `evidence/ENVIRONMENT.txt` + `evidence/FOLLOWUP_ENVIRONMENT.txt` |
| **Status** | **VERIFIED** — the boundary was exercised twice (two independently built environments) and held both times |
| **Confidence** | **HIGH** |
| **Affected AHOS area** | `docs/architecture/PROCESS_ISOLATED_RESEARCH_WORKER.md`; `docs/architecture/RESEARCH_ANALYST_AGENT.md`; `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `AGENTS.md` (research-safety section). **All named as proposals; none written to** |
| **Permitted use** | Cite the five rules, especially: make "no production file changed" a **verifiable** claim (`git status` + whitespace-insensitive diff) rather than an assertion; **confirm a module cannot have side effects before importing it** from a protected tree, and prefer reading source text to importing |
| **Prohibited use** | Must **not** be cited as AGI/ACI progress (see the explicit non-claims in document 30). Must **not** be used to claim that any AHOS integration is safe — it establishes only that *this* unsound integration is unwritable |
| **Reviewer required** | **YES — Agent B** |

---

### KN-11 · *(new this pass)* Recompute aggregates; never inherit a total from prose

| Field | Value |
|---|---|
| **KN-ID** | `KN-11-RECOMPUTE-AGGREGATES` |
| **Title** | A reconciliation pass that verifies every component can still propagate a wrong total |
| **Source document** | **26 (this pass)** — discovered by re-reading `evidence/followup/f1_objective_a.json` rather than the prose; registered as **E-CORR-01** (§26.5) |
| **Evidence reference** | `evidence/followup/f1_objective_a.json` → `A7_total_rows_all_schemas = 305495`; `A7_temporal_scan` per-class rows `112690 + 36481 + 57853 + 91181 + 2556 + 3367 + 1367 = **305495**` (recomputed twice this pass, in two independent reads); the figure **304,495** appears **23 times across 10 documents** — `04, 10, 11, 12, 16, 17, 18, 19, 24, 25` — and the correct **305,495** appears in **no** prose document. Verified by `grep -c` and by `grep -o … \| wc -l` |
| **Status** | **VERIFIED** (the discrepancy is measured, not alleged) |
| **Confidence** | **HIGH** — arithmetic; reproducible with one command |
| **Affected AHOS area** | `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md` (aggregate-verification rule). **AHOS-SIDE OBSERVATION (PROPOSED)**: this is a defect **in this investigation's own documentation**, not in AHOS and not in FinanceDatabase's data |
| **Permitted use** | Cite as the reason an evidence registry must recompute aggregates from components. Cite the corrected total **305,495** in any future work. Use as the precedent for registering corrections against one's own prior output |
| **Prohibited use** | Must **not** be cited as a data-quality defect in FinanceDatabase — the seven per-class counts are all correct; only the prose sum was wrong. Must **not** be used to discredit the per-class measurements, all of which reproduced exactly |
| **Reviewer required** | **YES — Agent B.** Agent B should note that document 25's reconciliation verified all seven components **exactly** and still restated the wrong aggregate — the gap is in the reconciliation *method*, not in its diligence |

> **Materiality: LOW to every conclusion, HIGH to method.** No verdict, score or decision in this
> package depends on the total row count. The crypto rejection rests on `0/14` fields, `0/16`
> capabilities, the absence of `SOL`, and the `TypeError`/`AttributeError` proofs — none of which
> involves the aggregate. The correction is registered because the doctrine requires it, not because
> anything turns on it.

---

### KN-12 · *(new this pass)* A populated key does not imply a populated record

| Field | Value |
|---|---|
| **KN-ID** | `KN-12-STRUCTURAL-EMPTINESS` |
| **Title** | 5,108 symbol-only stub rows across the corpus; in `indices` they are 5.32% of the table and are exactly the rows with an empty `exchange` |
| **Source document** | **26 (this pass)** — discovered while verifying what `rows_lost_under_release_semantics` actually measures |
| **Evidence reference** | Measured this pass by reading all seven `compression/*.bz2` artifacts verbatim (`dtype=str, keep_default_na=False`) and counting rows where **every** data column is empty: `equities 0 (0.00%) · etfs 4 (0.01%) · funds 244 (0.42%) · indices 4854 (5.32%) · currencies 0 (0.00%) · cryptos 5 (0.15%) · moneymarkets 1 (0.07%)` → **total 5,108 of 305,495 (1.67%)**. All 5,108 stub rows **do** carry a non-empty key. For `indices`, set equality was proven between the stub rows and the rows with `exchange == ''` (`4,854 == 4,854`, `True`), which independently corroborates `04_SCHEMA_AUDIT.md:165` (`exchange` empty in 4,854 rows = 5.32%). Sample stub keys: `032A.Z`, `032B.Z`, `032D.Z`, `032E.Z`, `05XV.Z`, `0TVB.DE`, `0TVC.DE`, `0TVD.DE`. Cross-check: `f3_na_regression.json` → `C10_per_asset_class.*.rows_lost_under_release_semantics` carries these same seven values |
| **Status** | **VERIFIED** |
| **Confidence** | **HIGH** — exact set equality plus an independent corroboration in a prior document |
| **Affected AHOS area** | Any AHOS ingest that treats "row exists" as "record exists"; rule candidates **DQR-05** and **DQR-06** (document 28) |
| **Permitted use** | Cite as evidence that presence-of-key is not presence-of-data, and that a completeness check must be **cell-level**, not row-level. Cite the `indices` 5.32% stub rate when discussing per-subset quality |
| **Prohibited use** | Must **not** be described as rows "lost to the NA bug" — that is a **misreading of the `f3` field name**, corrected at §26.5 **E-CORR-02**. Must **not** be cited as an AHOS finding |
| **Reviewer required** | **YES — Agent B** |

> **Why this matters evidentially.** The archived field name
> `rows_lost_under_release_semantics` invites exactly the wrong inference. It was verified this pass
> to measure **fully-empty rows** (`len(raw) - len(dfault.dropna(how="all"))`), and it is cited in
> **no prose document** — so no published claim was wrong, but a future reader of the archived JSON
> could have drawn a false one. Registering the correct reading is the purpose of this entry.

---

## 26.4 Technique registry cross-reference

Document 23 assessed fourteen reusable techniques (T-1…T-14). They are **not** re-registered as
knowledge items here; they are engineering candidates and belong to the Agent B implementation
queue. Their registry status is recorded so that the two documents cannot drift apart.

| T-ID | Technique (short) | Licence exposure | Registry status | Priority if ever authorized |
|---|---|---|---|---:|
| **T-11** | Verbatim CSV preservation + null-key assertion | None | **PLANNED** (proposal awaiting Agent B) | **1** |
| **T-4** | `actionable` vs `review-only` repair classification | None | **PLANNED** | 2 |
| **T-6** | `mtime=0` gzip for byte-reproducible artifacts | None | **PLANNED** | 3 |
| **T-8** | Blocking, pre-publication invariant tests | None | **PLANNED** | 4 |
| **T-10** | Fail-closed validated query surface | None | **PLANNED** | 5 |
| **T-12** | Dry-run-by-default destructive CLI | None | **PLANNED** | 6 |
| **T-5** | Precomputed `categories` sidecar (with drift assertion) | None | **PLANNED** — carries a known drift hazard | 7 |
| **T-9** | Deliberate retention of delisted instruments | None | **PLANNED** | 8 |
| **T-14** | Structure-preserving in-place field patching | None | **PLANNED** | 9 |
| **T-3** | FIGI hierarchy *concept* (not the identifier) | None for the concept | **PLANNED** — design idea only | 10 |
| **T-1** | ISIN check-digit validation (ISO 6166) | Algorithm none; **bulk ISIN values yes** | **PLANNED** — only with a TradFi lane | 11 |
| **T-13** | Cross-identifier consistency and derivation | Structural rule none; CUSIP form yes | **PLANNED** | 12 |
| **T-2** | CUSIP-9 check-digit validation | **Highest exposure in the package** | **PLANNED — LOWEST PRIORITY** | 13 |
| **T-7** | Rejecting pickle in favour of CSV+bz2 | None | **PLANNED** | — |

**All fourteen: `APPROVED FOR IMPLEMENTATION = NO`.** Items T-1, T-2, T-3 and T-13 additionally
require the legal review queued in document **29** before any use involving identifier **values**.

**Implementation path correction carried here (from document 23 §23.0 / F-CORR-01):** the
check-digit techniques must be reimplemented from the **published ISO 6166 / CUSIP / OpenFIGI
specifications**. They must **not** be copied from `validate_identifiers.py`, which delegates to
**`python-stdnum` (LGPL-2.1+)** — not a permissive licence, and in conflict with AHOS's own
`requirements.txt` law. `python-stdnum` must **not** be added as an AHOS dependency.

---

## 26.5 Corrections and supersessions carried into this registry

| ID | Superseded statement | Registered replacement | Affected items |
|---|---|---|---|
| **E-CORR-01** *(new this pass)* | "304,495 rows" across all seven schemas — stated **23 times in 10 documents** | **305,495 rows.** The seven per-class counts are each correct and each reproduced exactly; the prose **sum** was wrong by exactly 1,000. The machine-readable evidence always said 305,495 | KN-07, KN-12; documents 04, 10, 11, 12, 16, 17, 18, 19, 24, 25 |
| **E-CORR-02** *(new this pass)* | Archived field `rows_lost_under_release_semantics` (in `f3_na_regression.json`) reads as "rows lost to NA coercion" | It measures **rows whose data columns are entirely empty** under a verbatim read (`len(raw) - len(dfault.dropna(how="all"))`). Verified by exact MATCH in all seven classes. It is **not** NA damage, and it is cited in **no** prose document. **The archived JSON is left unmodified** — evidence is immutable; the interpretation is registered here | KN-06, KN-12 |
| **D-CORR-01** | "GICS validation failing on three consecutive runs" | **Ten** consecutive failures, #389→#398, a 42-day span (document 22 §22.2) | KN-05 |
| **C-REFINE-01** | Release 2.4.0 "silently loses" ticker `NA` | Row **retained** (112,690 both ways, zero cell-level divergence); the **key becomes null** → `KeyError`. Dropped only by a key filter such as `to_toolkit()`'s `index.notna()`. **Undetectable by row count** | KN-06 |
| **B-CORR-01** | "1,774 names with trailing whitespace" | **SUPERSEDED — withdrawn, not reproducible.** Measured: equities 658 trailing / 665 any-side; all classes 11,933 / 11,956 | document 20 CASE 5 |
| **F-CORR-01** | Check digits: "~15 lines, no licence obligation", sourced from the validator | The validator **delegates** to `python-stdnum` (**LGPL-2.1+**). Reimplement from public specifications; do not copy, do not add the dependency | KN-04, T-1/T-2/T-3/T-13 |
| **SCH-RECON-01** | "GICS 11/24/80" | Authority (`categories.json`) = 11/24/**69**; data = 11/24/**80**; delta = **11** orphan industries across **14** rows | KN-05 |
| **ENV-CORR-01** | Reproduction via `/tmp/fdb_repo`, `/tmp/fdb_venv` | Those paths do **not** survive between sessions. Durable record is `evidence/`; see **ENV-DUR-01** | all |

**SUPERSEDED entries must not be cited.** Where a document in the 00–25 range states a superseded
figure, this registry governs. Documents 00–25 were **not** modified to apply these corrections,
because the extraction pass is authorized to create only documents 26–30.

---

## 26.6 Items explicitly NOT registered

An evidence registry is defined as much by its refusals as by its entries. The following were
considered and **REJECTED** for registration, with reasons.

| Candidate | Disposition | Reason for refusal |
|---|---|---|
| "FinanceDatabase crypto data is stale, therefore AHOS crypto coverage is insufficient" | **REJECTED** | Cross-domain non-sequitur. AHOS's crypto identity domain is `(chain, address)`; FinanceDatabase has neither. No AHOS coverage claim follows |
| "The upstream maintainer was negligent about CI" | **REJECTED** | Cause is **U-19, UNKNOWN**. Negligence is a legal/HR characterization, not an evidenced finding, and this package alleges none |
| "0 dangerous calls in the package ⇒ the package is secure" | **REJECTED** | Category error. The correct language is **"no issue observed in reviewed scope"**, which is explicitly **not** a security certification. Registering it as "secure" would violate the precision rule |
| "`to_toolkit()` latency ≈ N ms" | **REJECTED** | **BLOCKED — NOT TESTED.** `financetoolkit` was deliberately not installed to preserve attribution. Any number would mix four components with no way to separate them (KN-09) |
| "Crypto table vintage ≈ 2020" | **REJECTED as a fact; registered as inference only** | **U-04 UNKNOWN.** Retained inside KN-08 at **LOW** confidence, explicitly labelled INFERENCE. Must never be cited as a date |
| "158,429 → 112,690 was caused by commit X" | **REJECTED** | **U-14 UNKNOWN**, never bisected. The shrinkage is measured; the cause is not |
| "AHOS should adopt `confidence_level` default = LOW" | **REJECTED as a decision; registered as a design question** | Inside KN-02 as an **AHOS-SIDE OBSERVATION (PROPOSED)**. The default is a verified code fact; changing it is the AHOS owner's call, not an evidence finding |
| Any item sourced from `JeroenBouma/FinanceDatabase` | **REJECTED** | That path returns **HTTP 404**; the account (id 46189588, 0 public repos) is not the author's working account (id 46355364). Citing it would be citing a non-existent source |
| "The 1,774 trailing-whitespace figure" | **REJECTED — SUPERSEDED** | Does not reproduce under any of four tested definitions (B-CORR-01) |
| "304,495 total rows" | **REJECTED — SUPERSEDED** | Contradicted by its own component measurements (E-CORR-01) |

---

## 26.7 Registry summary

| KN-ID | Title (short) | Status | Confidence | Reviewer | Implementation authorized |
|---|---|---|---|---|---|
| **KN-01** | Namespace every key | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-02** | Symbol is an alias, not an identity | **VERIFIED** / AHOS-side obs. **PARTIALLY_VERIFIED** | HIGH / MEDIUM | Agent B + AHOS owner | **NO** |
| **KN-03** | Pin code *and* data; a release is not a snapshot | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-04** | Permissive code licence ≠ data licence | **VERIFIED** (facts) / **BLOCKED** (conclusions) | HIGH / **NONE ASSERTED** | Agent B **+ LEGAL** | **NO** |
| **KN-05** | Validation must gate publication | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-06** | Null semantics are key-integrity | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-07** | Provenance must be captured at ingest | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-08** | Freshness is per-subset | **VERIFIED** / vintage **PARTIALLY_VERIFIED** | HIGH / LOW | Agent B | **NO** |
| **KN-09** | Attribute capability precisely | **VERIFIED** (one measurement **BLOCKED**) | HIGH | Agent B | **NO** |
| **KN-10** | Required-field contracts make bad integrations unwritable | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-11** | Recompute aggregates *(new)* | **VERIFIED** | HIGH | Agent B | **NO** |
| **KN-12** | A populated key ≠ a populated record *(new)* | **VERIFIED** | HIGH | Agent B | **NO** |

**Registered: 12. VERIFIED: 12 (three with a named partially-verified or blocked component).
UNVERIFIED: 0. REJECTED for registration: 10 (§26.6). SUPERSEDED: 2.**

**All twelve: `PROPOSED — NOT IMPLEMENTED`. Implementation authorized: NO.**
**KN-04 additionally requires legal review — queued in document 29.**

## 26.8 Agent B review gate

| Gate question | Agent E's answer for Agent B to verify |
|---|---|
| Does every registered item cite located evidence? | **YES** — every row names a JSON key, a file:line, or a re-executable command. No item rests on prose alone |
| Is any item an AHOS defect claim? | **NO** — two items carry an **AHOS-SIDE OBSERVATION (PROPOSED)** label (KN-02, KN-11) and neither asserts a failure |
| Does any item require legal review? | **YES — KN-04**, plus T-1/T-2/T-3/T-13 for identifier **values** |
| Was anything promoted to policy? | **NO** |
| Was anything implemented? | **NO** |
| Are the evidence/score/decision/outcome layers kept separate? | **YES** — §26.0, with a worked example; no row inherits another layer's value |
| Are refusals recorded? | **YES** — §26.6, ten entries with reasons |

## 26.9 Reproduction note for the two new items

KN-11 and KN-12 were measured during this pass. To comply with the deliverable constraint
(*create only documents 26–30*), **no new evidence artifact file was written**. Both are reproducible
from the archived pinned artifacts with the following, and Agent B may request that the output be
archived under `evidence/followup/` on authorization:

```
KN-11  sum of A7_temporal_scan[*].rows in evidence/followup/f1_objective_a.json
       compare against A7_total_rows_all_schemas and against grep -c '304,495' *.md

KN-12  for each of the seven compression/*.bz2 artifacts, read verbatim
       (dtype=str, keep_default_na=False, index_col=0) and count rows where every
       data column is empty; for indices, compare that set against rows where
       exchange == ''
```

Environment for this pass: `/tmp/fdb2_repo` @ `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634`,
`/tmp/fdb2_venv` (Python 3.11.2, pandas 3.0.5) — confirmed **ALIVE** at the start of this pass.
Baseline and closing `git` state recorded in document **30 §30.9**.
