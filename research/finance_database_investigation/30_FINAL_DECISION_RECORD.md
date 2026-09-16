# 30 — Final Decision Record

**Document 30 · Extraction package deliverable 5 of 5. Closing record of the FinanceDatabase
forensic investigation and its knowledge-extraction pass.**

| Role | Agent | Function |
|---|---|---|
| Author | **Agent E — Evidence Authority** | Records decisions, reproduced claims, corrections, unknowns and non-claims |
| Mandatory reviewer | **Agent B — Engineering Governor** | Counter-signs the record; owns every authorization gate referenced below |

**Record date:** 2026-09-15 (Asia/Tehran) · **Subject commit:** `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634`
**Package:** documents 00–30 + `evidence/` · **Extraction pass:** documents 26–30, read-only

---

## 30.1 FINAL DECISIONS

### Crypto

> ## **REJECTED**
>
> All ten decisive claims re-executed and **reproduced** (§30.2). `0 of 14` required AHOS identity
> fields present; `0 of 16` capabilities satisfied; `SOL` absent (`0` rows; library-level
> `select(cryptocurrency="SOL")` → `ValueError`); `51 of 73` probed tokens absent including **every**
> Solana-ecosystem token; `0` timestamp columns across **305,495** rows; no CI job updates the crypto
> table's content; `0 of 16` `MarketMetrics` and `0 of 15` `SecuritySignals` fields satisfiable; and a
> `NormalizedTokenCandidate` **cannot be constructed** from this data (`TypeError: missing 2 required
> positional arguments: 'chain' and 'address'`) nor forced with `None` without crashing the router's
> real dedupe key (`AttributeError: 'NoneType' object has no attribute 'lower'`).
>
> **No evidence materially contradicts the existing verdict. The new evidence reinforces it.**

### Research

> ## **RESEARCH-ONLY VALUE**
>
> Strengthened by the follow-up and by this extraction pass: **12** registered knowledge items
> (KN-01…KN-12), **14** assessed techniques (T-1…T-14), **6** proposed fixtures (FIX-01…FIX-06),
> **12** data-quality rule candidates (DQR-01…DQR-12), **9** licence layers queued for review, and
> **1** unknown closed (U-12). All of it obtained **without** installing the package into AHOS and
> **without** touching production.

### Integration

> ## **NOT APPROVED**
>
> No integration of any kind is approved. FinanceDatabase was **not** added as an AHOS provider. No
> crypto adapter was created. The vendored-snapshot design in document 14 §14.6 remains
> **conditional** on a future non-crypto lane, separate written authorization, boundary rules
> B-1…B-18, and completion of the legal review queued in document **29**.

### Implementation

> ## **NOT IMPLEMENTED**
>
> Nothing was implemented — by the original investigation, by the forensic follow-up, or by this
> extraction pass. No fixture, adapter, dependency, workflow, provider, schema or code change was
> created. Verified at §30.9.

### Identity Fixtures

> ## **PROPOSED — NOT IMPLEMENTED**
>
> Six fixtures registered in document **27** with threat model, expected failure mode, affected
> identity invariant, required test boundary, false-positive risk, false-negative risk and approval
> gate. **`Implementation authorized: NO` on all six.** `architecture/identity/resolution.py` was
> **not modified** — it was inspected read-only to verify that the invariants cited actually exist at
> the paths and line numbers recorded (document 27 §27.0). **No FinanceDatabase record is an AHOS
> production failure.**

### Legal

> ## **LEGAL REVIEW REQUIRED**
>
> **Code: MIT — verified four ways, clear.** **Data: LEGAL REVIEW REQUIRED** across nine separated
> layers (document **29**), consolidating **seven** discrete questions for counsel — (a) does MIT
> reach the data; (b) who owns it; (c) does the unlicensed upstream create downstream exposure;
> (d) does an EU *sui generis* right subsist; (e) do CUSIP/FIGI values require a licence; (f) is the
> Yahoo-implied provenance of `summary` prose a copyright issue; **(g) *(added this pass)* does
> importing `python-stdnum` (LGPL-2.1+) create any obligation.** **No legal advice, opinion,
> conclusion or clearance is given anywhere in this package.**

### AHOS Production Impact

> ## **NONE**
>
> Verified, not asserted — §30.9. All writes confined to
> `research/finance_database_investigation/`. Zero content changes to any tracked AHOS file. No
> server started. The 72-hour soak was not disturbed. No package installed into the AHOS
> environment. Phase 4 not started. Live trading not enabled.

---

## 30.2 All ten decisive crypto claims — reproduction record

Re-executed in a **rebuilt** isolated environment at the pinned commit. Raw output:
`evidence/followup/f1_objective_a.json`, `f2_a10_contract.json`.

| # | Claim | Reproduced value | Disposition |
|---|---|---|---|
| **A-1** | cryptos table has exactly **7** columns | `['symbol','name','cryptocurrency','currency','summary','exchange','website']`; **3,367** rows; programmatic match `A1_MATCHES_REPORT=true` | **REPRODUCED-EXACT** |
| **A-2** | **14** required AHOS identity fields absent | `A2_absent_count=14` of `A2_total_checked=14`; `A2_ALL_ABSENT=true` (`chain`, `network`, `contract`, `address`, `contract_address`, `platform`, `token_id`, `decimals`, `launch_date`, `first_seen`, `market_cap`, `price`, `volume`, `liquidity`) | **REPRODUCED-EXACT** |
| **A-3** | `SOL` is not present | `A3_SOL_rows=0`, `A3_SOL_symbol_prefix_rows=0`, `A3_SOL_PRESENT=false`; library `select` → `ValueError` (exact message captured) | **REPRODUCED / STRENGTHENED** — now at library level too |
| **A-4** | `SOL1` appears with **10** rows | `A4_SOL1_rows=10`, `A4_SOL1_PRESENT=true`; names `Solana CAD/CNY/ETH/EUR` | **REPRODUCED-EXACT** |
| **A-5** | Token probe: **22** present / **51** absent | `A5_present_count=22`, `A5_absent_count=51` of `A5_probe_size=73`, using the **verbatim** archived probe list; `A5_ALL_SOLANA_ECOSYSTEM_ABSENT=true` (all 14: `BONK WIF JUP PYRM JTO RAY ORCA MNGO POPCAT MEW BOME SLERF MYRO WEN`) | **REPRODUCED-EXACT** |
| **A-6** | **86** crypto↔equity ticker collisions | `A6_collisions=86` of `A6_crypto_token_tickers=352` (`A6_collision_pct=24.4`); **351** excluding the empty string (24.5%) — denominator now stated (A-REFINE-01) | **REPRODUCED / REFINED** |
| **A-7** | **0** timestamp/provenance columns across all schemas | `A7_total_temporal_columns_found=0`, `A7_NO_TIMESTAMPS_ANYWHERE=true`, `A7_total_rows_all_schemas=305495` | **REPRODUCED-EXACT** — and the source of correction **E-CORR-01** (§30.3) |
| **A-8** | No CI job writes `database/cryptos.csv` | Only `database/equities/{exchange}.csv` and `database/equities/NAN.csv` are written under `database/`; `cryptos.csv` is **read** 3× (recompress, categorise, count) but its content is never updated from any source | **REPRODUCED / REFINED — stronger** |
| **A-9** | **0 of 16** crypto capabilities | `A9_capabilities_satisfied=0` of `A9_capabilities_total=16`; `A9_ALL_NEGATIVE=true` | **REPRODUCED-EXACT** |
| **A-10** | `NormalizedTokenCandidate` incompatible | `T1_construct_without_chain_address='TypeError'` — *"missing 2 required positional arguments: 'chain' and 'address'"*; `T2_construct_with_none` succeeded but `T2_dedupe_key_raises="AttributeError: 'NoneType' object has no attribute 'lower'"` against `T2_dedupe_key_expression='(c.chain, c.address.lower())'`; `T2_n_unknown_fields=33` with `T2_confidence_level='HIGH'`; `T5_MarketMetrics_satisfiable_from_fdb=[]` (0/16), `T5_SecuritySignals_satisfiable_from_fdb=[]` (0/15) | **STRENGTHENED — argument → execution-proof** |

**Result: 10 of 10 reproduced. 0 contradicted. 2 strengthened. 2 refined. 1 upgraded from argument
to execution-proof.**

Supporting reproductions, same environment: `search()` fail-open (a bogus column returns **3,367 of
3,367** rows); site-packages local mode → uncaught `FileNotFoundError` with
`isinstance(e, RequestException) = False`; artifact SHA-256 re-hashed from a fresh download and
**MATCH** for both sdist and wheel, and matching PyPI's published digests; `raw.githubusercontent.com`
still unreachable (curl rc=35, identical to the earlier session).

---

## 30.3 Corrections recorded in this final record

### (i) The `NA` correction — **C-REFINE-01**

| | |
|---|---|
| **Originally stated** | Release 2.4.0 "silently **loses**" the ticker `NA` |
| **Corrected statement** | The row is **retained**. `C5_release_rows = C6_main_rows = 112690` and `C5_cell_level_divergence_empty = true`. What is lost is the **key**: `C5_release_index_nan_count=1`, `C5_release_NA_in_index=false`, `C5_release_loc_NA="KeyError: 'NA'"`, versus `C6_main_NA_in_index=true`. The record becomes **unaddressable**, and is dropped only by a key filter such as `to_toolkit()`'s `self[self.index.notna()]` |
| **Why the correction matters** | **A row-count check cannot detect this defect.** The corrected form is **harder** to detect than the original claim, not easier — which inverts the mitigation. It is the evidential basis for **DQR-01**, **DQR-02** and **FIX-06** |
| **Exact record** | `database/equities/NMS.csv:4346` → `NA,Nano Labs Ltd Class A Ordinary Shares,…,NMS,XNAS,NASDAQ Global Select`. `C4_count=1` — exactly one such record in the corpus |
| **Scope** | `C10_ONLY_EQUITIES_AFFECTED=true`. Per class, vulnerable index values: equities **1**, all six others **0**. The only NA-like first field anywhere in `database/` is `NMS.csv → 'NA'` |
| **Fix provenance** | `3b8eb8390959bec6a360a620333b6fe5217a4618`, 2026-08-07T10:32:18Z, **Jon Højlund Arnfred**, PR **#166**, *"Preserve CSV values verbatim in the database workflow"*. `git merge-base --is-ancestor 3b8eb83 2.4.0` → **NO**; `… HEAD` → **YES**. Tag `2.4.0` = `51226b86758b116fb9e1065645c62fcb342af2f5`; PyPI upload 2026-06-02T14:05:45Z; the fix is **66 days later** and **2.4.0 is still the latest release**. `helpers.py` 358 lines (release) vs 366 (main) |
| **Status** | **CORRECTED / REFINED** — the defect is real; the description was wrong in a way that changes the detection strategy |

### (ii) The withdrawn whitespace figure — **B-CORR-01**

| | |
|---|---|
| **Originally stated** | "1,774 names with trailing whitespace" |
| **Disposition** | **WITHDRAWN — UNREPRODUCED.** Does not reproduce under any of four tested definitions |
| **Measured instead** | equities: trailing **658**, leading-or-trailing **665**. All seven classes: trailing **11,933**, leading-or-trailing **11,956**. Per class (trailing): equities 658 · etfs 38 · funds 1,563 · indices **9,655** · currencies 0 · cryptos 0 · money markets 19 |
| **Materiality** | **LOW to conclusions** — no load-bearing claim depended on 1,774. **HIGH to evidence discipline** — the figure is withdrawn rather than defended, and the *phenomenon* is confirmed to be **far larger** than reported |
| **Status** | **SUPERSEDED — must not be cited** |

### (iii) The `python-stdnum` correction — **F-CORR-01**

| | |
|---|---|
| **Originally stated** | Check-digit algorithms: *"~15 lines, no licence obligation"* to reimplement, sourced from `validate_identifiers.py` |
| **Corrected statement** | The repository **does not implement them.** `financedatabase/validation/validate_identifiers.py:13` is `from stdnum import cusip, figi, isin`, and **`python-stdnum` 2.2 is LGPL-2.1+** — confirmed by PyPI classifier (`GNU LGPLv2+`) and by `pip show` in the isolated environment |
| **Consequence** | The **algorithms** remain freely reimplementable from the published **ISO 6166 / CUSIP / OpenFIGI** specifications. **This implementation path does not.** "Copy the validator" would import an LGPL dependency, conflicting with AHOS's own `requirements.txt` law (*"free, permissively licensed"*). **LGPL is not a permissive licence** |
| **Binding instruction carried forward** | Do **not** copy `validate_identifiers.py`. Do **not** add `python-stdnum` — **including as a test-only dependency**. Reimplement from specifications |
| **Status** | **CORRECTED — changes the recommended implementation path.** Queued as **LPR-02**, question **(g)** |

### (iv) The CI / taxonomy governance findings — **D-CORR-01**, **GOV-01**, **GOV-02**, **SCH-RECON-01**

| ID | Finding |
|---|---|
| **D-CORR-01** | GICS validation failures were reported as **three** consecutive. Measured: **ten** consecutive — `Check-GICS-Categorisation` runs **#389** (2026-08-02T17:20:15Z) → **#398** (2026-09-13T15:07:37Z), a **42-day** span; last success **#388** (2026-08-02T12:47:55Z, sha `bf839b234a26`). **The original understated the finding by 7 runs and ~5 weeks.** Evidence: `evidence/followup/d_gics_sequence.json` (25 runs × per-job conclusions) |
| **Non-blocking by construction** | The job declares `needs:` on **all four** mutating jobs (`Add-New-Ticker`, `Update-Compression-Files`, `Update-Categorization-Files`, `Update-README-Statistics`), so it runs **last** — started 15:10:43, **after** the 15:10:12 push. It cannot block publication |
| **Zero enforcement** | **0** workflow runs and **0** check-runs on **all three** 2026-09-13 bot commits. Mechanism traced: the scheduled run was already in flight against an older `head_sha` (`fe5fbd83c6e4`) when it pushed `a0c8b199` → `9f91e39c` → `a174c97d`. **Cause remains U-10 UNKNOWN** |
| **GOV-01** | The **`Identifier Validation`** workflow (id `312400597`, path `.github/workflows/identifier_validation.yml`, created 2026-07-13, state `active`) ran **twice**, both `pull_request` events on `feature/validate-identifiers`, both `success`, and was **never merged** — **0** commits touch that path on the default branch, and the file exists at no default-branch ref. The validator **itself was** merged, via PR **#159** (`5ae2910`). **Validation on `main` is therefore manual-only.** A stale `active` registration initially misled this investigation into treating it as a live gate |
| **GOV-02** | The taxonomy check has a **blind spot**. `f5_gics_replication.json`: `equities_rows=112690`, `rows_with_full_gics_triple=72585`, `rows_excluded_missing_triple=40105`. Its own `notna()` filter excludes **8 of the 14** orphan-taxonomy rows and all **40,045** rows with an empty `industry` — it inspects **~64%** of the corpus, so **a green run would not mean the taxonomy is consistent** |
| **U-12 CLOSED** | The CI log could not be fetched (GitHub job-log blob storage unreachable — Azure EOF), so the check was **re-executed locally**: `invalid_row_count=10`, `WORKFLOW_WOULD_RAISE=true`, classified **6** orphan industries + **2** wrong-group pairings + **2** level-confusions. `distinct_bad_sectors=[]`, `distinct_bad_industry_groups` (1), `distinct_bad_industries` (6). **Re-execution is stronger evidence than the log would have been** |
| **SCH-RECON-01** | Resolves the long-standing "80 industries vs GICS 69" tension: the **authority** (`categories.json`) = 11 sectors / 24 industry groups / **69** industries; the **data** = 11 / 24 / **80**; the delta is **11 orphan industry values across 14 rows**. `0` authority industries are unused |
| **New: CI still NA-vulnerable** | `f5_gics_replication.json` → `by_exchange` contains `'nan': 2`. The CI script reads without `keep_default_na=False`. **The library was fixed; the pipeline was not** — the basis for **DQR-03** |
| **Test suite** | `1 failed, 85 passed, 1 deselected in 42.43s` — **reproduced exactly**. Failure at `tests/test_invariants.py:95`, `equities <-> etfs: ['CHAD'] (1 total)`. Deselected test run alone: `1 passed, 1 warning in 4.17s`, warning at `test_validate_identifiers.py:298` — *"2 identifier finding(s) require manual review"*. **Environment caveat:** without `pytest-recording` (0.13.4, per `uv.lock`) the suite returns **87 spurious errors**, because `conftest.py:503` autouse `record_stdout` depends on the `disable_recording` fixture it provides |
| **Release-blocker assessment** | The 10-run GICS failure is **not** a release blocker in this project's topology (the job is non-blocking by construction and 2.4.0 predates the failure window). It **is** an evidence blocker for any claim that the corpus's taxonomy is validated. **D-9, document 22 §22.8** |

### (v) Corrections discovered by *this* extraction pass

| ID | Finding |
|---|---|
| **E-CORR-01** | **The prose total row count is wrong by exactly 1,000.** The seven per-class counts are each correct and each reproduced exactly — `112690 + 36481 + 57853 + 91181 + 2556 + 3367 + 1367 = **305,495**`. The figure **304,495** appears **23 times across 10 documents** (`04, 10, 11, 12, 16, 17, 18, 19, 24, 25`); the correct **305,495** appears in **no** prose document. The machine-readable evidence always said `A7_total_rows_all_schemas = 305495`. **Document 25's reconciliation verified all seven components exactly and still restated the wrong aggregate** — the gap is in the reconciliation *method*, not in its diligence. Registered as **KN-11**; the basis for the rule "recompute aggregates, never inherit a total from prose". **Materiality: LOW to every conclusion** — no verdict, score or decision depends on the total. **HIGH to method** |
| **E-CORR-02** | **An archived evidence field name invites a false inference.** `rows_lost_under_release_semantics` in `f3_na_regression.json` reads as "rows lost to NA coercion". Verified this pass to measure **rows whose data columns are entirely empty** (`len(raw) - len(dfault.dropna(how="all"))`) — exact **MATCH** in all seven classes. It is **not** NA damage, and it is cited in **no prose document**, so no published claim was wrong. **The archived JSON is left unmodified** — evidence is immutable; the interpretation is registered as **KN-12** |
| **E-NEW-01** | **New data-quality finding: symbol-only stub rows.** Reading all seven artifacts verbatim, rows with a populated key and **every** data column empty: `equities 0 (0.00%) · etfs 4 (0.01%) · funds 244 (0.42%) · indices 4854 (5.32%) · currencies 0 (0.00%) · cryptos 5 (0.15%) · moneymarkets 1 (0.07%)` → **5,108 of 305,495 (1.67%)**. All 5,108 carry a non-empty key. For `indices`, **set equality** was proven between stub rows and rows with `exchange == ''` (`4854 == 4854`, `True`), independently corroborating `04_SCHEMA_AUDIT.md:165`. Sample stub keys: `032A.Z`, `032B.Z`, `032D.Z`, `032E.Z`, `05XV.Z`, `0TVB.DE`, `0TVC.DE`, `0TVD.DE`. Registered as **KN-12** and rule candidate **DQR-05** |

### (vi) Corrections carried forward unchanged

| ID | Correction |
|---|---|
| **A-REFINE-01** | Collision denominator stated: **352** distinct `cryptocurrency` values including the empty string, **351** excluding it (7 rows are `''`); collisions = **86** under either (24.4% / 24.5%) |
| **A-REFINE-02** | "No CI job writes `cryptos.csv`" strengthened: it is **read** by 3 of 5 jobs but **no workflow updates its content from any source** |
| **B-EXP-01** | Berkshire: **7** rows across **4** venues (was 5); `figi`/`shareclass_figi` populated **only** on the two Vienna rows, empty on all four US rows — **corroboration inversion** |
| **B-EXP-02** | `MMM`: **4** unrelated entities across 18 rows and 5 name strings (was 2) — adds Mining, Minerals & Metals plc and Minco Capital Corp., plus the `MMM.SG` German registered-share name variant for 3M itself |
| **ENV-CORR-01** | Reproduction via `/tmp/fdb_repo`, `/tmp/fdb_venv` is **not durable**; the durable record is `evidence/` |

---

## 30.4 ENV-DUR-01 — evidence durability failure

| Field | Value |
|---|---|
| **ID** | `ENV-DUR-01` |
| **What happened** | The original investigation's entire research environment — `/tmp/fdb_repo` (pinned sparse clone), `/tmp/fdb_venv` (isolated venv) and `/tmp/fdb_lab` (all machine-readable outputs) — **did not survive one session boundary**. On resumption all three paths were absent. Every JSON measurement existed only there |
| **Consequence** | For one session boundary, the package's evidence was **not evidence**. A full re-execution pass was required to rebuild it: re-download and re-hash both distribution artifacts, re-clone at the pinned commit, reinstall the exact `uv.lock`-governed stack, and re-run all measurements. One measurement could **not** be re-obtained at all — the GICS CI job log, because GitHub job-log blob storage is unreachable from this environment (Azure EOF) |
| **Compensation** | The unretrievable log was **substituted by local re-execution** of the CI check's logic, which produced a **stronger** result than the log would have: the 10 failing rows were enumerated *and classified* (6 orphan industries, 2 wrong-group pairings, 2 level-confusions), closing **U-12** |
| **Remedy applied** | Machine-readable outputs are now archived **inside the repository** at `evidence/followup/` (6 JSONs), with 18 scripts at `evidence/scripts/` and two environment records (`evidence/ENVIRONMENT.txt`, `evidence/FOLLOWUP_ENVIRONMENT.txt`) capturing exact versions, install commands, pinned commit and artifact hashes. The package is now self-sufficient: a future auditor can reproduce it **without network access to the original hosts and without reconstructing anything from prose** |
| **Residual risk, stated** | `/tmp/fdb2_*` remains **non-durable** and was confirmed ALIVE at the start of this pass. Anything measured this pass and recorded **only** in prose remains exposed to the same failure. Two such measurements exist — **KN-11 / E-CORR-01** and **KN-12 / E-NEW-01** — and both are fully specified with reproduction recipes (document 26 §26.9, document 28 §28.5) **because this pass was authorized to create only documents 26–30**. Agent B may authorize archiving their outputs under `evidence/followup/` |
| **Registered as** | **KN-12**'s sibling lesson and rule candidate **DQR-12** — *"a path under `/tmp` is a scratch location, never an evidence location"* |

---

## 30.5 All remaining unknowns

Carried from document 25 §25.4, updated for this pass. **16 unchanged · 1 closed · 1 partially closed
· 3 registered during the follow-up · 1 registered during this extraction pass.**

| ID | Question | Status |
|---|---|---|
| **U-01** | Is the default remote data path exercisable? | **UNKNOWN** — `raw.githubusercontent.com` fails identically (curl rc=35). Compensated by pinned-clone testing |
| **U-02** | Is served `main` byte-identical to the pinned clone? | **UNKNOWN** — but HEAD is confirmed unmoved, so the risk is bounded |
| **U-03** | What does a fresh `pip install` resolve on the AHOS Windows host? | **UNKNOWN** — installation into AHOS is prohibited. `uv.lock` pins re-verified |
| **U-04** | Bulk-import provenance / crypto table vintage | **UNKNOWN (INFERENCE: Yahoo / CryptoCompare, ~2020)** — corroborated indirectly (`CCC` 3,362 of 3,367, `SOL` absent, `SRM` present). **Never to be cited as a date** |
| **U-05** | `JeroenBouma` account history | **UNKNOWN** — re-verified **HTTP 404**; id 46189588 with 0 public repos, distinct from `JerBouma` id 46355364 with 15 |
| **U-06** | Who owns the data? | **UNKNOWN** — queued as counsel question **(b)** |
| **U-07** | Maintainer intent on dataset licensing | **UNKNOWN** |
| **U-08** | `secrets.PAT` scope in the CI workflow | **UNKNOWN** |
| **U-09** | PyPI publication method / attestation | **UNKNOWN** — no publish workflow exists |
| **U-10** | Cause of zero runs on data-changing bot commits | **UNKNOWN as to cause**; **STRENGTHENED as to effect** (all 3 commits; mechanism traced to an in-flight run against an older `head_sha`) |
| **U-11** | Cause of no CI loop on self-push | **UNKNOWN** |
| **U-12** | Which rows fail the GICS invariant | ✅ **CLOSED** — 10 rows enumerated and classified by local re-execution after the log host proved unreachable |
| **U-13** | Are identifier-less tickers ever backfilled? | **PARTIALLY CLOSED** — the `mode()` imputation is **proven to have fired** (FOLLOWUP-02: 129 `two` rows carry exactly the `Financials`-subset modes, zero variance). The backfill question itself remains open |
| **U-14** | Which commit caused 158,429 → 112,690? | **UNKNOWN (INFERENCE)** — never bisected. The shrinkage is measured; the cause is not |
| **U-15** | Cross-version identifier stability | **UNKNOWN** |
| **U-16** | Are symbols recycled? | **UNKNOWN** — mechanism verified, no instance observed |
| **U-17** | Windows behaviour | **UNKNOWN** — the audit host is Linux. **No Windows claim is made anywhere in this package** |
| **U-18** | Is the `raw.githubusercontent.com` failure environment-specific? | **UNKNOWN, better characterized** — reproduced twice ~2 h apart with identical curl rc=35, while `github.com`, `api.github.com`, `codeload.github.com`, `files.pythonhosted.org` and `pypi.org` all succeed. A **second** GitHub-owned host (Actions log blob storage) also fails, so the pattern is *host-specific filtering within a generally working GitHub path*, not a blanket block. Resolution requires a test from the AHOS Windows host |
| **U-19** | Why was the Identifier Validation workflow never merged? | **UNKNOWN** — deliberate (cost? warning-only test deemed sufficient?) or oversight. Not determinable externally. **No negligence is alleged** |
| **U-20** | Will the 8 CI-invisible orphan-taxonomy rows ever be caught? | **UNKNOWN** — they are outside the check's filter by construction (GOV-02) |
| **U-21** | Does run #389's failure onset (2026-08-02T17:20:15Z) have an identifiable cause? | **UNKNOWN** — it began within ~5 h of the last success (#388, 12:47:55Z) and one run *before* the `keep_default_na` fix (#390). **No causal link is asserted** |
| **U-22** *(new this pass)* | Does AHOS currently satisfy any of DQR-01…DQR-12? | **UNKNOWN — and deliberately not investigated.** This pass was read-only over the FinanceDatabase evidence package. **No AHOS validation, ingest, CI or test surface was audited.** Any statement about AHOS's current posture would be unsupported inference — document 28 §28.4 |

---

## 30.6 Explicit non-claims

This record, and the package it closes, does **not** claim any of the following. Each refusal is
deliberate.

| # | Non-claim | Why it is refused |
|---|---|---|
| 1 | **No AGI or ACI progress is claimed from this research.** | The investigation produced documentation, proposed fixtures, rule candidates and a knowledge registry. It produced no capability improvement, no measured model gain, no new cognitive function and no advancement toward any AGI or ACI milestone. Document 15 assessed *research value*; it did not and does not claim progress. **Constraint 10 observed** |
| 2 | **No FinanceDatabase record is an AHOS production failure.** | Every case derives from a third-party corpus at `a174c97d3bba…`. AHOS's crypto identity domain is `(chain, address)`; FinanceDatabase's TradFi domain is `symbol`. They do not overlap |
| 3 | **No AHOS defect is asserted.** | Two items carry an **AHOS-SIDE OBSERVATION (PROPOSED)** label — KN-02 (`confidence_level` default `"HIGH"` at `architecture/providers/contracts.py:74`) and KN-11 (this investigation's own arithmetic error). Neither is a defect claim; KN-11 is a defect **in this package's documentation**, not in AHOS |
| 4 | **No security certification.** | The correct language is **"no issue observed in reviewed scope."** The zero-dangerous-call census (no `eval`, `exec`, `pickle`, `marshal`, `subprocess`, `os.system`, `socket`, `ctypes`, `open(`) is **not** a statement that the package is secure |
| 5 | **No single failure is extrapolated into a general reliability or security certification.** | One project's ten consecutive CI failures do not characterize CI-based validation generally |
| 6 | **No legal conclusion, advice, opinion or clearance.** | Document 29 separates facts into nine layers and states questions. Mitigating arguments are labelled **ARGUMENT — NOT A FINDING** and do not reduce any review requirement |
| 7 | **No benchmark result was invented.** | Every number traces to an archived script and JSON output. `to_toolkit()` end-to-end latency is recorded as **NOT TESTED** because `financetoolkit` was deliberately not installed to preserve attribution. The decompression-bomb PoC was **declined** as an attack on a third party. Both refusals are results |
| 8 | **No Windows validation is claimed.** | The audit host is Linux (**U-17**). Linux validation ≠ Windows validation |
| 9 | **No historical success is presented as current capability.** | HEAD is confirmed unmoved, so findings are **current**; the release-vs-`main` split and the 10-run failure window are dated precisely rather than blurred |
| 10 | **No symbol is treated as canonical identity.** | This is the package's central lesson (KN-01, KN-02, FIX-03). AHOS's `symbol_alias` vs `address_canonical` distinction (`architecture/identity/types.py:44,47`) is affirmed, never blurred |
| 11 | **No claim that AHOS lacks — or has — any DQR control.** | **U-22.** No AHOS validation surface was audited in this pass |
| 12 | **No negligence, bad faith or infringement is alleged against any party.** | Not against the author, contributors, upstream maintainer, MSCI, S&P Dow Jones Indices, the ABA, Bloomberg, SWIFT or ISO. **U-19** records the unmerged-workflow cause as UNKNOWN |
| 13 | **No fixture, rule, technique or knowledge item is promoted.** | All are `PROPOSED` / `CANDIDATE` / `PLANNED` with `Implementation authorized: NO` |
| 14 | **No integration is approved, and none was implemented.** | Integration remains **NOT APPROVED**; the document 14 §14.6 vendored-snapshot design remains conditional |
| 15 | **No claim that the crypto table's age is known.** | The ~2020 vintage is **INFERENCE** (**U-04**) and must never be cited as a date |

---

## 30.7 Constraint compliance record

All ten mandatory constraints on this extraction pass, each verified rather than asserted.

| # | Constraint | Compliance | Verification |
|---|---|---|---|
| 1 | Do not modify `architecture/`, `architecture/identity/`, scoring, decision authority, providers, schemas, paper trading, runtime, tests outside the research package, `requirements.txt`, package configuration, `README.md` | **COMPLIED** | `git diff --ignore-all-space --quiet` → **zero content changes to any tracked AHOS file**. Individual checks on `requirements.txt`, `architecture/identity/resolution.py`, `architecture/providers/registry.py`, `architecture/providers/contracts.py`, `architecture/decision/authority.py`, `scoring.ts`, `engine.ts`, `opportunity_canonical.ts`, `providers.ts`, `schema.ts` → all **UNCHANGED**. `README.md` mtime unchanged. Note: `scoring/` and `pyproject.toml` do **not** exist in this repository — scoring lives in `scoring.ts`, package configuration in `package.json`; both verified unchanged |
| 2 | Do not start any server | **COMPLIED** | No `start_process` call was made. Process scan shows no server, dev-process or soak process. The listening ports present (111, 22, one ephemeral) are **sandbox infrastructure**, not started by this pass |
| 3 | Do not disturb the 72-hour soak | **COMPLIED** | No soak process observed; no soak configuration, runtime, state or artifact read for modification or written |
| 4 | Do not install packages into the AHOS environment | **COMPLIED** | All installation remains in `/tmp/fdb2_venv`. `requirements.txt` unchanged. **`python-stdnum` was not added**, including as a test-only dependency |
| 5 | Do not add FinanceDatabase as an AHOS provider | **COMPLIED** | `providers.ts` and `architecture/providers/` unchanged; no provider file created |
| 6 | Do not create a crypto adapter | **COMPLIED** | No adapter created. `f2_a10_contract.py` proved an adapter **cannot** be written soundly, and that proof was recorded rather than acted upon |
| 7 | Do not implement FIX-01…FIX-06 | **COMPLIED** | Document 27 registers all six as a review queue. No test file added to `tests/` or `tests2b/`; no fixture data committed |
| 8 | Do not promote KN-01…KN-10 into production policy without review | **COMPLIED** | Document 26 registers 12 items, all `PROPOSED — NOT IMPLEMENTED`, each with an **Agent B** reviewer requirement and a prohibited-use column |
| 9 | Do not store secrets | **COMPLIED** | No credential, token, key or secret was read, written or recorded. GitHub access used the sandbox's pre-configured `gh` authentication; **no token value appears in any document**. `secrets.PAT` is discussed only as an unknown (**U-08**) |
| 10 | Do not claim AGI/ACI progress from this research | **COMPLIED** | Non-claim **#1** at §30.6, stated first and explicitly |

**Additional constraints observed:** do not overwrite existing reports (documents 00–25 unmodified,
verified by mtime and by the absence of any tracked-file content diff); do not modify `README.md`
(unmodified); create **only** documents 26–30 (§30.9 verifies the exact file delta).

---

## 30.8 Decision-change test

The standing instruction is to change a decision **only if evidence materially contradicts it**. That
test was applied and is recorded here so the outcome is auditable.

| Decision | Contradicting evidence sought | Found? | Outcome |
|---|---|---|---|
| **Crypto = REJECTED** | Any of the ten decisive claims failing to reproduce; any new evidence supporting crypto use | **NO** — 10 of 10 reproduced; the new evidence (`SOL1`'s own `summary` saying *"Solana (SOL)"*; 0/16 `MarketMetrics`; 0/15 `SecuritySignals`; `TypeError` on construction) **further undermines** it | **UNCHANGED — reinforced** |
| **Research = RESEARCH-ONLY VALUE** | Evidence that the research produced production-applicable output | **NO** — output is registrations and proposals, all unauthorized | **UNCHANGED — strengthened** (12 KN, 14 T, 6 FIX, 12 DQR, 9 LPR, 1 unknown closed) |
| **Integration = NOT APPROVED** | Evidence that integration is sound | **NO** — A-10 makes an unsound integration **unwritable** | **UNCHANGED** |
| **Implementation = NOT IMPLEMENTED** | Any implementation having occurred | **NO** — verified at §30.9 | **UNCHANGED** |
| **Identity Fixtures = PROPOSED** | Any authorization having been granted | **NO** | **UNCHANGED** |
| **Legal = LEGAL REVIEW REQUIRED** | Any layer resolving without counsel | **NO** — and one layer (**LPR-02**, `python-stdnum` LGPL) was **added** | **UNCHANGED — scope widened** |
| **AHOS Production Impact = NONE** | Any production file having changed | **NO** — zero content diff | **UNCHANGED** |

**Did anything improve on re-test?** Yes — three things: **U-12 closed**; the `mode()` imputation
**proven** rather than inferred; and the identity cases **richer** (7 BRK rows / 4 venues, 4 MMM
entities), making the proposed fixtures better.

**Did anything worsen?** Yes — three things: GICS failures **3 → 10** over 42 days; the `NA` defect
found to be **harder** to detect than stated; and this package's own total row count found to be
**wrong by 1,000** in 23 places.

**All three worsenings were reported as worsenings.** Nothing favourable was left unchallenged and
nothing unfavourable was softened.

---

## 30.9 Required final checks

**Protocol:** any check failing means **STOP** — report the exact failure and affected path, and **do
not repair automatically.**

Executed as a scripted suite of **9 assertions**. Result: **7 PASS, 2 FAIL**. Both failures were
**defects in the check instrument, not in the repository state or the deliverables**; each was
diagnosed to root cause and is recorded in full at §30.9.1. **The mandated STOP-and-report action was
taken. No repair was performed on the repository, and no check was re-run to obtain a green result.**

| # | Check | Command | Result |
|---|---|---|---|
| 1 | No tracked AHOS file changed | `git diff --ignore-all-space --quiet` | **PASS** — exit 0; `git diff --ignore-all-space` emits **0 lines** |
| 2 | No tracked file changed even including whitespace | `git diff --name-only --ignore-all-space \| wc -l` expected `0` | **FAIL — INSTRUMENT DEFECT.** Returned `94`. Root cause: Git's `--name-only` path does **not** apply `-w` filtering to the file *list*, so it lists files whose only difference is line endings. Substantive answer at §30.9.1-A: whitespace-only, pre-existing, **0 content changes** |
| 3 | No file created outside `research/finance_database_investigation/` | `git status --porcelain -uall \| grep '^??' \| grep -vc '^?? research/finance_database_investigation/'` | **PASS** — `0` outside, `60` inside |
| 4 | AHOS environment not modified | `git diff --quiet -- requirements.txt package.json`; interpreter probe | **PASS**, but the probe was **MISLABELLED** — it queried `/tmp/fdb2_venv` and printed "in AHOS env?". Corrected at §30.9.1-C: `stdnum` is **ABSENT** from `/usr/bin/python3`, the AHOS repo has **no venv of its own**, and `requirements.txt` / `package.json` are clean |
| 5 | No server started or disturbed | `ps` scan for `uvicorn\|gunicorn\|flask\|fastapi\|npm run dev\|next dev\|soak` | **FAIL — INSTRUMENT DEFECT.** Returned `3`. Root cause: the grep **self-matched** — the harness's own command line contained those literal words. Excluding harness processes: **0**. Substantive answer at §30.9.1-B |
| 6 | 72-hour soak not disturbed | no soak process, config, runtime or state touched | **PASS** — no soak process exists in the table; full listing shows only boot-time sandbox infrastructure (`etimes ≈ 4447 s`: chronyd, sshd, systemd-networkd, rpcbind, journald, kernel workers) |
| 7 | Documents 00–25 and `README.md` not overwritten | mtime comparison | **PASS** — all 26 pre-existing files retain their pre-pass mtime (`18:24`); mtimes `19:27`–`19:39` are documents 26–30 only |
| 8 | Exact deliverable set created | file listing + `find evidence -newermt` | **PASS** — exactly the five named documents (43,256 / 39,714 / 37,132 / 28,968 / 39,291 bytes); **`0` new files under `evidence/`**, honouring the create-only-26–30 constraint (§30.4 residual risk, §28.5) |
| 9 | No secret stored | regex scan of documents 26–30 for `ghp_`, `github_pat_`, private-key headers, `AKIA…` | **PASS** — `0` matches |

### 30.9.1 Root-cause record for the two FAILs

Per the mandate, the exact failure and affected path are reported rather than repaired.

**A · Check 2 — `git diff --name-only --ignore-all-space` returned 94**

| | |
|---|---|
| **Affected paths** | 94 **tracked** files, beginning `agent_org/__init__.py`, `agent_org/audit.py`, `agent_org/authority.py`, … — repository-wide CRLF↔LF normalization |
| **Why the instrument failed** | `--name-only` uses Git's quick "did this file change at all" path and does **not** filter the file *list* by `-w`. Asserting `count == 0` therefore tested line-ending state, not content |
| **Authoritative evidence that the constraint holds** | `git diff --ignore-all-space --quiet` → **exit 0**; `git diff --ignore-all-space` → **0 lines**. A sample hunk confirms the diff is `\r` removal on otherwise identical text |
| **Proof these are not this pass's modifications** | The baseline captured **before any write in this pass** already reported **94 M** and `tracked content changes: NONE`. Additionally, **0** of the 94 are deliverable files — documents 00–30 are **untracked**, so they cannot appear in a tracked diff |
| **Constraint status** | **SATISFIED.** No tracked AHOS file was changed by this pass |
| **Repair performed** | **NONE.** Reported, not repaired. Corrected instrument for future use: `git diff --ignore-all-space --quiet` |

**B · Check 5 — process scan returned 3 matches**

| | |
|---|---|
| **Affected path** | The check harness itself — no repository path involved |
| **Why the instrument failed** | **Self-match.** `ps -eo cmd` includes the harness's own command line, which literally contained the strings `uvicorn`, `gunicorn`, `flask`, `fastapi`, `npm run dev`, `next dev` and `soak` as grep operands |
| **Authoritative evidence that the constraint holds** | Re-scanned excluding the harness's own processes → **0 matches**. Full process table contains only sandbox infrastructure at `etimes ≈ 4447 s` (boot time, long before this pass): chronyd, sshd listener, systemd-networkd, rpcbind, systemd-journald, kernel workers. No `start_process` call was made in this pass |
| **Constraint status** | **SATISFIED.** No server was started or disturbed; no soak process exists to disturb |
| **Repair performed** | **NONE.** Reported, not repaired. Corrected instrument for future use: exclude the harness PID/PPID, or match against a pattern list held in a file rather than on the command line |

**C · Check 4 — mislabelled interpreter probe (reported although the check itself PASSed)**

| | |
|---|---|
| **What was wrong** | The probe printed `python-stdnum in AHOS env? -> PRESENT` while querying `/tmp/fdb2_venv/bin/python` — the **isolated research venv**, not an AHOS environment |
| **Corrected measurement** | `/tmp/fdb2_venv` → `stdnum PRESENT`, `sys.prefix=/tmp/fdb2_venv` (**research environment; installation there is authorized**). `/usr/bin/python3` → `stdnum ABSENT`, `sys.prefix=/usr`. The AHOS repository contains **no** `.venv` or `venv`. `requirements.txt` and `package.json` → **clean** |
| **Constraint status** | **SATISFIED.** `python-stdnum` was **not** installed into any AHOS environment — consistent with the binding instruction at document 29 §29.2 |
| **Repair performed** | **NONE** to the environment. The **label** is corrected here, because an inaccurate label on a passing check is the same defect class as an inaccurate figure in a passing report |

### 30.9.2 STOP-and-report disposition

| Question | Answer |
|---|---|
| Did any check fail? | **YES — two** (checks 2 and 5), plus one mislabelled probe (check 4) |
| Was the STOP honoured? | **YES.** No repair was performed on the repository, no check was re-run to obtain a green result, and no failing assertion was silently rewritten to pass |
| Do the failures indicate a constraint violation? | **NO.** All three are instrument defects. Every substantive constraint — checks 1, 3, 4, 6, 7, 8, 9 — **PASSES on authoritative evidence** |
| Was anything modified to make the suite green? | **NO.** The only edit made after the suite ran is to **this section of this document**, correcting a statement of results that the measurement had contradicted |
| Why was §30.9 amended at all? | Because it initially recorded "all nine checks PASS", which the executed suite contradicted. Leaving a contradicted result in place is precisely the **E-CORR-01** defect class registered at §30.3(v) — a report restating a figure its own evidence disproves. **REALITY > DOCUMENTATION** required the correction |

> **Registered as E-CORR-03 — a mis-specified verification instrument.** Three distinct instrument
> defects were found in one nine-check suite: a Git flag-semantics error (`--name-only` ignores `-w`
> for the file list), a process-scan self-match, and an environment mislabel. **Each produced a
> result that looked like a constraint violation while the constraint was in fact satisfied — and
> one produced a result that looked like a PASS while querying the wrong environment.** The lesson
> generalizes and is the reason this record reports the failures rather than the headline: **a
> verification suite must itself be verified, and a green check is only as meaningful as the
> interpreter it queried.** Proposed as rule candidate **DQR-13** for Agent B (§30.9.3).

### 30.9.3 Rule candidate arising from this pass

| Field | Value |
|---|---|
| **ID** | `DQR-13` |
| **Topic** | Verification-instrument self-validation |
| **Derived from** | **E-CORR-03** — three instrument defects in one suite, found only because the failures were diagnosed rather than re-run |
| **Rule statement** | *Every automated check must (a) exclude its own process and command line from any scan it performs; (b) name the environment, path or object it actually queried in its output, not the environment it intended to query; (c) use flag combinations whose semantics have been verified on a known-positive and a known-negative input; and (d) report a FAIL that is later diagnosed as an instrument defect as **two** findings — the instrument defect and the substantive answer — never as a silent PASS.* |
| **Detection method** | Run each check against a deliberately failing fixture and a deliberately passing one, and confirm it distinguishes them. A check that cannot fail has no power; a check that cannot pass has no meaning |
| **Severity** | **S1 CRITICAL** — an instrument that reports the wrong environment can pass a constraint that was violated |
| **FP risk** | **NONE** — it constrains the instrument, not the data |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

## 30.10 Closing statement

This record closes a 31-document investigation of a third-party financial database, and the
read-only extraction pass that followed it.

The subject was examined, found **unfit for the purpose originally contemplated**, and **rejected on
type-contract evidence rather than on judgement** — a required-field contract made the unsound
integration unwritable, which is a stronger result than any policy could have produced. Nothing was
integrated, nothing was implemented, and no AHOS production surface was touched.

What the investigation yielded instead is registered here: **12** knowledge items, **14** techniques,
**6** fixtures, **12** rule candidates and **9** licence layers — every one of them traceable to a
located measurement, every one of them unauthorized, and every one of them accompanied by an explicit
statement of what it may **not** be used for.

Three findings from the re-testing were **worse** than originally reported, and are recorded as
worse. One figure could not be reproduced and was **withdrawn**. One licence recommendation was
**wrong about its implementation path** and was corrected. One unknown was **closed** by re-execution
after its log proved unreachable. And this pass found an error **in its own package's arithmetic** —
a total row count wrong by exactly 1,000, stated 23 times across 10 documents, contradicted by the
machine-readable evidence that had been archived alongside it the whole time. That is registered as
**E-CORR-01 / KN-11**, and it is the most useful thing in this document:

> **A reconciliation that verifies every component can still propagate a wrong aggregate. Evidence
> must be recomputed, not restated — including, and especially, one's own.**

**Final decisions, restated verbatim:**

> **Crypto: REJECTED · Research: RESEARCH-ONLY VALUE · Integration: NOT APPROVED ·
> Implementation: NOT IMPLEMENTED · Identity Fixtures: PROPOSED — NOT IMPLEMENTED ·
> Legal: LEGAL REVIEW REQUIRED · AHOS Production Impact: NONE.**

**Awaiting Agent B — Engineering Governor review. No item in documents 26–29 may be promoted,
implemented, adopted, committed or acted upon until that review is complete and separate written
authorization exists.**
