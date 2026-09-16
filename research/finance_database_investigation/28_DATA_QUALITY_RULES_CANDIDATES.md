# 28 — Data Quality Rules Candidates

**Document 28 · Extraction package deliverable 3 of 5.**

| Role | Agent | Function |
|---|---|---|
| Author | **Agent E — Evidence Authority** | Derives candidate validation rules from located evidence only; states each as a checkable assertion with detection method, severity and false-positive risk |
| Mandatory reviewer | **Agent B — Engineering Governor** | Gate owner. **No candidate below is AHOS policy.** Promotion requires Agent B review plus separate written authorization |

> ## ⚠️ CANDIDATE — NOT AHOS POLICY
>
> **Every rule in this document is marked `CANDIDATE — NOT AHOS POLICY`.** Nothing here has been
> adopted, configured, enabled, coded or scheduled. No validation was added to any AHOS pipeline. No
> AHOS file was modified — including `architecture/`, `architecture/identity/`, scoring, decision
> authority, providers, schemas, paper trading, runtime, `tests/`, `tests2b/`, `requirements.txt`
> and package configuration. `README.md` was not modified. No server was started. The 72-hour soak
> was not disturbed. No package was installed.
>
> **These are rules that a third-party project's failures suggest AHOS may wish to consider.** They
> are not findings that AHOS lacks them, and not findings that AHOS has them. **No AHOS validation
> surface was audited in this pass** — see §28.4.

> **Derivation rule.** Each candidate is derived from a **measured** defect in the FinanceDatabase
> corpus or its CI, cited to a JSON key or file:line. No rule is derived from intuition, from a
> general best-practice list, or from a defect that was not observed. Where a rule generalizes beyond
> the observed case, the generalization is labelled **EXTENSION** and carries lower confidence.

---

## 28.0 Severity and status vocabulary

| Severity | Meaning |
|---|---|
| **S1 CRITICAL** | Silent, undetectable by conventional health checks, and corrupts a key or an identity |
| **S2 HIGH** | Corrupts data or attribution, but produces a visible symptom somewhere |
| **S3 MEDIUM** | Degrades data quality or auditability without corrupting identity |
| **S4 LOW** | Hygiene; improves detectability of the above |

| Field | Meaning |
|---|---|
| **Detection method** | The assertion a validator would evaluate — stated so it is mechanically checkable |
| **Cost** | Relative cost of evaluating the rule on a corpus of this size (305,495 rows) |
| **FP risk** | Probability the rule fires on **correct** data |
| **Status** | Always `CANDIDATE — NOT AHOS POLICY` |

---

## 28.1 The candidates

### DQR-01 · Row-count equivalence is not cell-level equivalence

| Field | Value |
|---|---|
| **Topic** | Row-count vs cell-level equivalence |
| **Derived from** | The `NA` regression. `f3_na_regression.json`: `C5_release_rows=112690`, `C6_main_rows=112690`, `C5_cell_level_divergence_empty=true` — **and yet** `C5_release_index_nan_count=1`, `C5_release_NA_in_index=false`, `C5_release_loc_NA="KeyError: 'NA'"` |
| **Observed defect** | Two readers produced **identical row counts** and **zero cell-level divergence** in the data columns, while one produced an **unaddressable primary key**. Every conventional comparison passed; the record was still broken |
| **Rule statement** | *When comparing two ingest configurations, versions or sources, row-count equality and data-column equality are **necessary but not sufficient**. The comparison must separately assert equality of the **key/index domain**: the set of key values, the count of null keys, and addressability of a sample of keys.* |
| **Detection method** | `assert set(reader_a.index) == set(reader_b.index)`; `assert reader_a.index.isna().sum() == reader_b.index.isna().sum() == 0`; `assert all(k in reader.index for k in sample_keys)`. A diff report must have **three** sections — row count, cell values, **key domain** — and must not summarize them into one number |
| **Severity** | **S1 CRITICAL** |
| **Cost** | Low — one extra set comparison |
| **FP risk** | **LOW.** Key-domain equality is a strict requirement; legitimate differences (a genuinely new record) are expected to appear and *should* be reported |
| **Would apply to** | Any AHOS ingest comparison, version-migration check or provider-swap validation |
| **Confidence** | **HIGH** — the defect is reproduced, and the insufficiency of the conventional check is demonstrated, not argued |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-02 · Post-parse null-key assertion

| Field | Value |
|---|---|
| **Topic** | Null / key preservation |
| **Derived from** | Same evidence as DQR-01, plus `C10_per_asset_class` (measured across all seven classes) and `C10_ONLY_EQUITIES_AFFECTED=true` |
| **Observed defect** | A primary key became null after parsing. Nothing raised. The row was retained but unaddressable, and was dropped only later by a `notna()` key filter (`to_toolkit()` → `self[self.index.notna()]`) at an arbitrary distance from the cause |
| **Rule statement** | *Immediately after parsing any identifier-bearing source, assert that **no key column contains a null**. A null key is a **hard failure**, not a warning, and must be reported with the source file, line number and raw value.* |
| **Detection method** | `assert not df.index.isna().any()`, and the same for every column declared as an identity component. On failure, report `file:line` and the raw pre-parse string — the evidence that made this diagnosable was `database/equities/NMS.csv:4346` |
| **Severity** | **S1 CRITICAL** |
| **Cost** | Very low |
| **FP risk** | **LOW**, with one caveat: a corpus with **legitimately** keyless rows (e.g. a staging table) would fail. Mitigation: the rule applies to any table declared to have a primary key, and the declaration is what makes it checkable |
| **Would apply to** | AHOS ingest of any keyed source; provider payload normalization |
| **Confidence** | **HIGH** |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-03 · Declare exactly one null token; read identifiers as text

| Field | Value |
|---|---|
| **Topic** | dtype preservation · sentinel values such as `NA` |
| **Derived from** | `C1_release_has_keep_default_na=false` vs `C2_main_has_keep_default_na=true`; `C10_pandas_default_na_strings` (**19** magic tokens); the upstream workflow's own comment recording two prior instances of the same class — `"9763"` → `"9763.0"` and `"031162100"` → `"31162100.0"`, which *"dropped that row on every run"* |
| **Observed defect** | Two distinct coercions from one root cause: (a) **string→null** for 19 magic tokens including the legitimate ticker `NA`; (b) **string→float** for numeric-looking identifiers, changing `"9763"` to `"9763.0"` so it no longer matched its own source. The fix landed in the library (`helpers.py:63-69`) but **not** in the CI script — `f5_gics_replication.json` shows `by_exchange` containing `'nan': 2`, i.e. **the library was fixed and the pipeline was not** |
| **Rule statement** | *Identifier-bearing text must be read with an explicit, minimal null declaration — `dtype=str`, `keep_default_na=False`, `na_values=[""]` (or a strict-typed reader's equivalent). Exactly **one** null token may be recognized, and it must be declared. No reader anywhere in the system — library, script, notebook or CI — may use a parser's implicit magic-string set.* |
| **Detection method** | Two checks. (1) **Configurational:** enumerate every CSV/TSV read call in the codebase and assert each carries an explicit null declaration — a grep-auditable property. (2) **Behavioural:** round-trip a canary record set containing all 19 default-NA tokens plus numeric-looking identifiers, and assert every value survives byte-exact. Check (2) is the one with power; check (1) is the one that finds the *unfixed second reader* |
| **Severity** | **S1 CRITICAL** |
| **Cost** | Low for (2); medium for (1) — it requires enumerating read sites |
| **FP risk** | **LOW.** The round-trip canary is deterministic. The configurational check may flag a reader that legitimately wants NA inference (e.g. numeric metrics columns) — **scope it to identifier columns only** |
| **Would apply to** | Every AHOS text ingest path, **including CI and one-off scripts** — the observed defect's most transferable lesson is that fixing the library is not fixing the system |
| **Confidence** | **HIGH** — both coercions are reproduced; the unfixed-second-reader case is observed, not hypothesized |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-04 · Sentinel-value registry with per-column semantics

| Field | Value |
|---|---|
| **Topic** | Sentinel values such as `NA` |
| **Derived from** | The coexistence of **three visually identical nulls** in one corpus: an empty cell `''`, the literal string `nan` written by the pipeline into 11 fields of new tickers (`np.nan` → CSV), and a true `NaN` from parsing. Plus `C10_pandas_default_na_strings` |
| **Observed defect** | Downstream consumers cannot distinguish "not collected" from "collected as empty" from "the pipeline wrote the word nan". No column carried a declared sentinel vocabulary, so all three states collapsed into one ambiguous representation |
| **Rule statement** | *Each identifier and enum column must declare its **sentinel vocabulary**: the exact set of strings that mean "absent", and the exact single representation used when writing. A value that is a sentinel in one column must not be silently a valid value in another (`NA` is a null token to a parser and a legitimate ticker to the exchange).* |
| **Detection method** | (1) Assert the written representation of absence is **one** token per column, and count violations. (2) Assert no column contains a literal `'nan'`/`'NaN'`/`'None'` **string** where the declared sentinel is `''` — i.e. detect serialization leakage. (3) Cross-check each declared sentinel against the parser's magic-token list and fail if they intersect a valid-value domain |
| **Severity** | **S2 HIGH** |
| **Cost** | Medium — requires a per-column declaration to exist first |
| **FP risk** | **MEDIUM.** A column may legitimately contain the string `"None"` as data (e.g. a place name). Mitigation: the rule fires only where the column's **declared** sentinel vocabulary conflicts, so an undeclared column is a separate finding |
| **Would apply to** | AHOS ingest and egress; provider payload normalization; any CSV artifact AHOS writes |
| **Confidence** | **HIGH** for the observed three-null coexistence; **MEDIUM** for the generalization (**EXTENSION**) |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-05 · Structural emptiness: a populated key does not imply a populated record

| Field | Value |
|---|---|
| **Topic** | Duplicate and collision detection · completeness |
| **Derived from** | **NEW measurement taken during this pass (KN-12).** Reading all seven `compression/*.bz2` artifacts verbatim and counting rows where every data column is empty: `equities 0 (0.00%) · etfs 4 (0.01%) · funds 244 (0.42%) · indices 4854 (5.32%) · currencies 0 (0.00%) · cryptos 5 (0.15%) · moneymarkets 1 (0.07%)` → **5,108 of 305,495 rows (1.67%)**. All 5,108 carry a non-empty key. Sample `indices` stub keys: `032A.Z`, `032B.Z`, `032D.Z`, `032E.Z`, `05XV.Z`, `0TVB.DE`, `0TVC.DE`, `0TVD.DE` |
| **Observed defect** | 5,108 records exist as **keys with no content**. In `indices`, these stubs are **exactly** the rows with an empty `exchange` — set equality proven (`4854 == 4854`, `True`), independently corroborating `04_SCHEMA_AUDIT.md:165` (`exchange` empty in 4,854 rows = 5.32%). A row-count or key-uniqueness check reports this corpus as healthy; **5.32% of one table is placeholder** |
| **Rule statement** | *Completeness must be measured at **cell level per record**, not at row level per table. Any record whose key is populated but whose required content fields are **all** empty must be classified a **stub**, counted, and reported as a percentage of its table. Stub rate is a per-table metric and must be published alongside the row count.* |
| **Detection method** | `stub_mask = df[required_cols].replace('', NA).isna().all(axis=1)`; report `stub_mask.sum()`, `stub_mask.sum()/len(df)`, and a sample of stub keys. Publish **per table**, never corpus-wide only — the corpus rate (1.67%) conceals the `indices` rate (5.32%) |
| **Severity** | **S2 HIGH** |
| **Cost** | Low |
| **FP risk** | **LOW-MEDIUM.** A sparse table where most fields are legitimately optional would report a high stub rate without being defective. Mitigation: the rule uses a **declared required-content list** per table, not "all columns" |
| **Would apply to** | Any AHOS catalog-style ingest; provider candidate enumeration (a token with an address but no metrics is the crypto analogue of a stub) |
| **Confidence** | **HIGH** — measured this pass, exact set equality, corroborated against a prior document |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-06 · Duplicate and collision detection across namespaces

| Field | Value |
|---|---|
| **Topic** | Duplicate and collision detection |
| **Derived from** | `f4_identity.json`: `cross_asset_symbol_collisions` (equities↔etfs, set `{'CHAD'}`, n=1); `distinct_bare_tickers=74690` of 112,690 rows; `bare_tickers_appearing_more_than_once=16251`; `MMM_count=18` across 4 entities; `ISIN_fanout_gt_1=5181`, `ISIN_max_fanout=57`; 47,578 lowercase-duplicate names; 19 whitespace-bearing symbols; `f1_objective_a.json` `A6_collisions=86` of 352 crypto tickers (**24.4%**) |
| **Observed defect** | Collisions exist at **five** distinct levels in one corpus — cross-schema (`CHAD`), intra-schema repeated key (16,251 tickers), identifier fan-out (5,181 ISINs → up to 57 symbols), case-folding (47,578), and whitespace (19). A single "check for duplicates" pass detects at most one of them |
| **Rule statement** | *Collision detection must be run **per namespace pair and per normalization level**, and each level reported separately: (a) exact key within a table; (b) exact key **across** tables; (c) case-folded key; (d) whitespace-trimmed key; (e) identifier fan-out (one identifier → many keys); (f) key fan-in (one entity → many keys). A report stating only "N duplicates found" is not actionable.* |
| **Detection method** | Six separate counts, each with examples and each with its denominator stated. Cross-table collisions require the **pairwise** matrix, not a merged frame — merging first destroys the very information being sought. Fan-out must report the **maximum** and the **distribution**, not just the count |
| **Severity** | **S2 HIGH** |
| **Cost** | Medium — six passes, but all vectorizable |
| **FP risk** | **MEDIUM.** Levels (c) and (d) will flag legitimate distinct entities that differ only by case or whitespace in some markets. Mitigation: report them as **candidate** collisions requiring corroboration, never as errors — which is exactly the `actionable` vs `review-only` split from technique **T-4** |
| **Would apply to** | AHOS identity resolution; provider registry dedupe; any cross-provider candidate merge |
| **Confidence** | **HIGH** |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-07 · Publish the coverage of an invariant alongside its result

| Field | Value |
|---|---|
| **Topic** | Filtered-row coverage |
| **Derived from** | `f5_gics_replication.json`: `equities_rows=112690`, `rows_with_full_gics_triple=72585`, `rows_excluded_missing_triple=40105`, `invalid_row_count=10`. The CI check's own `notna()` filter excludes 8 of the 14 orphan-taxonomy rows and all 40,045 rows with an empty `industry` |
| **Observed defect** | A check reporting "0 failures" (or, here, "10 failures") was evaluated over **~64%** of the corpus. **A green run would not have meant the taxonomy was consistent.** The unpublished denominator made the result unreadable — and this pass initially had to disprove the assumption that the check covered the table |
| **Rule statement** | *Every invariant check must publish, with its result: rows examined, rows **excluded**, the exclusion predicate, and the coverage percentage. A result without a denominator is not a result. Any `notna()`, `dropna()`, `isna()` or boolean-mask filter applied **before** an assertion must be treated as load-bearing and logged.* |
| **Detection method** | The check's report carries four mandatory fields — `examined`, `excluded`, `exclusion_predicate`, `coverage_pct` — and fails closed if any is missing. Additionally: assert that the **union** of examined and excluded equals the table's row count, so silent double-exclusion is impossible |
| **Severity** | **S1 CRITICAL** for auditability — a check whose coverage is unknown cannot be relied upon, and cannot be shown to be unreliable either |
| **Cost** | Very low — it is a reporting requirement, not a computation |
| **FP risk** | **NONE.** It cannot fire on correct data; it can only make an existing result interpretable |
| **Would apply to** | Every AHOS invariant test, validation gate and CI check; every entry in `docs/OPERATOR_VALIDATION_PROTOCOL.md` |
| **Confidence** | **HIGH** |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-08 · Zero-variance imputation signature

| Field | Value |
|---|---|
| **Topic** | Zero-variance imputation |
| **Derived from** | **FOLLOWUP-02**, closing U-13 from the data side. `f4_identity.json`: `TWO_count=129`, `TWO_symbol_suffixes=29`, `TWO_distinct_countries` — all 129 rows carry `country="United States"`, `sector="Financials"`, `industry_group="Diversified Financials"`, `industry="Diversified Financial Services"` with **zero variance**, matching `mode()` of the `sector=='Financials'` subset exactly. Mechanism verified in source at `.github/workflows/database_update.yml:87,113` (`return subset['industry_group'].mode()[0] …`) |
| **Observed defect** | A statistical mode was written into 129 unrelated records spanning 29 venues, 5+ currencies and 4 continents, with **no field marking the values as imputed**. The imputation is indistinguishable from observation in the data. Independently: 40,045 rows have an empty `industry`, so imputation was applied **selectively** — some records got a guess, others got nothing |
| **Rule statement** | *Imputed values must carry an explicit provenance marker and reduced confidence at write time. Where a corpus lacks such a marker, an **imputation signature** must be tested for: a categorical field with zero variance across a subset that is heterogeneous on independent dimensions (venue, currency, jurisdiction) is presumptively imputed, not observed.* |
| **Detection method** | For each categorical field, group by an independent dimension and compute variance. Flag groups where `nunique() == 1` while `n >= threshold` **and** the group spans ≥2 values of an independent dimension. **Threshold matters:** at n=6 (the FIX-05 fixture size) zero variance is unremarkable and this check **will** false-positive; at n=129 across 29 venues it is anomalous. Report as **review-only**, never `actionable` (T-4) |
| **Severity** | **S3 MEDIUM** as a detection rule · **S2 HIGH** as a write-time requirement |
| **Cost** | Low-Medium |
| **FP risk** | **HIGH at small n — the highest in this document.** Legitimate homogeneity exists (all Nasdaq listings really are US). Mitigation: (a) minimum group size; (b) require heterogeneity on an independent dimension; (c) classify as review-only; (d) never auto-correct. **This rule must not be made blocking without Agent B setting the thresholds** |
| **Would apply to** | AHOS enrichment and any fallback/default logic in provider normalization; the `confidence_level` question raised in KN-02 |
| **Confidence** | **HIGH** that the observed case is imputation (proven twice — mechanism in source, fingerprint in data); **MEDIUM** that the detection heuristic generalizes (**EXTENSION**) |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-09 · Timestamp and freshness validation per subset

| Field | Value |
|---|---|
| **Topic** | Timestamp / freshness validation |
| **Derived from** | `f1_objective_a.json`: `A7_total_temporal_columns_found=0`, `A7_NO_TIMESTAMPS_ANYWHERE=true`, `A7_total_rows_all_schemas=305495` — a column-name scan for `date\|time\|updated\|asof\|timestamp\|snapshot\|version\|source\|provider\|retrieved` over all seven schemas. `financedatabase/helpers.py:12-14` (`DATA_REPO` hardcodes `main`). Update cadence: Sunday 12:00 UTC, **US equities only** (`database_update.yml:167,173,179`). **No workflow writes `database/cryptos.csv`** — it is read, re-compressed, categorised and counted by 3 of 5 jobs but its content is never updated. Independently: the project website advertises **158,429** equities vs **112,690** in data (**29% stale self-report**) |
| **Observed defect** | Freshness is **undeterminable** from any record, and the single update cadence coexists with a **permanently frozen** table that shows every outward sign of maintenance. A source's own published statistic was stale by 29% |
| **Rule statement** | *Three requirements. (1) **Every record must carry an observation timestamp and a source-asserted timestamp** — absence of either means `STALE`/`UNKNOWN`, never "probably fresh". (2) **Freshness must be measured per subset, never per source** — one cadence does not imply uniform currency. (3) **A job that references a file is not evidence the file's content is updated** — freshness must be verified against the **write target**, not the reference count. (4) **EXTENSION:** a source's own published statistics are themselves a freshness signal and must be checked against the data.* |
| **Detection method** | (1) Schema assertion: temporal columns exist and are non-null for ≥ a declared percentage. (2) Per-subset age report: for each subset, `max(observation_ts)` and the delta to now. (3) Write-target enumeration: statically list every path a pipeline **writes**, and assert each subset's freshness claim maps to a writer — a subset with no writer is **frozen by construction** and must be labelled so. (4) Reconcile any published count against the measured count and report the delta |
| **Severity** | **S2 HIGH** |
| **Cost** | Low for (1), (2), (4); medium for (3) — it requires reading pipeline definitions |
| **FP risk** | **LOW** for (1)-(3). (4) may flag a legitimately rounded marketing figure — report the delta, do not fail on it |
| **Would apply to** | `docs/DATA_SOURCE_MATRIX.md` (per-subset freshness column); every AHOS provider; `architecture/identity/types.py:19` (`IdentityState.STALE`) and `IdentitySource.source_ts` vs `retrieved_ts` — AHOS's contract already requires both timestamps, which is why this dataset fails the check and AHOS's schema does not |
| **Confidence** | **HIGH** for (1)-(3); **MEDIUM** for (4) (**EXTENSION**) |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-10 · Default-branch CI enforcement on data-changing commits

| Field | Value |
|---|---|
| **Topic** | Default-branch CI enforcement |
| **Derived from** | **0** workflow runs and **0** check-runs on **all three** 2026-09-13 bot commits (verified per commit). `Check-GICS-Categorisation` failed on **10 consecutive runs**, #389 (2026-08-02T17:20:15Z) → #398 (2026-09-13T15:07:37Z), a **42-day** span; last success #388 (2026-08-02T12:47:55Z). The job declares `needs:` on **all four** mutating jobs, so it starts **last** (15:10:43, after the 15:10:12 push) and **cannot block**. `Identifier Validation` workflow (id `312400597`) ran **twice**, both `pull_request` on `feature/validate-identifiers`, both `success`, and was **never merged** — `0` commits touch that path on the default branch; the validator itself arrived via PR #159 (`5ae2910`) |
| **Observed defect** | Four independent gate failures: data-mutating commits trigger nothing; the one consistency check runs too late to block; it has been red for 42 days with data published throughout; and a purpose-built validation workflow was tested, left unmerged, and left registered as `active` — which misled this investigation into initially treating it as a live gate |
| **Rule statement** | *Four requirements. (1) Validation must run **on the data-changing commit itself** — a gate that fires only on code commits is not a data gate. (2) Validation must **gate publication**: a check that runs after the write, or that `needs:` the writing jobs, cannot block and must not be described as a gate. (3) A **consecutive-failure count and its age** must be tracked and escalated — 10 failures over 42 days is a different fact from "the check failed". (4) A workflow that is registered `active` but has never run on the default branch is a **false gate** and must be either merged or de-registered.* |
| **Detection method** | (1) For each commit that modifies a data path, assert ≥1 workflow run and ≥1 check-run exists against that SHA; report commits with zero. (2) Static analysis of workflow topology: any check whose `needs:` includes a data-writing job is **non-blocking by construction** — flag it. (3) Query run history and compute the current consecutive-failure streak and the timestamp of the last success. (4) For each registered workflow, count runs on the default branch; **zero ⇒ false gate** |
| **Severity** | **S1 CRITICAL** for (1) and (2) — the combination means published data can be invalid with no signal |
| **Cost** | Low — all four are API or static-analysis queries, no data processing |
| **FP risk** | **LOW-MEDIUM.** (1) will flag commits legitimately skipped by a path filter — the rule must read the workflow's `on.paths` before concluding a gate is missing. (3) will flag a check that is intentionally advisory — hence (2) must classify blocking vs advisory **first** |
| **Would apply to** | Any AHOS repository that stores or generates data; `docs/OPERATOR_VALIDATION_PROTOCOL.md`; AHOS's own CI topology |
| **Confidence** | **HIGH** — every element API- or source-verified. **U-19 records the cause of the unmerged workflow as UNKNOWN; no negligence is alleged** |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-11 · Release / tag ancestry verification

| Field | Value |
|---|---|
| **Topic** | Release / tag ancestry verification |
| **Derived from** | `git merge-base --is-ancestor 3b8eb83 2.4.0` → **NO**; `… HEAD` → **YES**. Tag `2.4.0` = `51226b86758b116fb9e1065645c62fcb342af2f5`. Fix `3b8eb8390959bec6a360a620333b6fe5217a4618` (2026-08-07T10:32:18Z, PR #166). PyPI upload of 2.4.0: 2026-06-02T14:05:45Z — the fix is **66 days later**, and no release followed; 2.4.0 is still latest. `git log -S 'keep_default_na'` returns **exactly one** commit. Release artifact lacks the `validation/` subpackage present on the branch. Artifact SHA-256 re-hashed and **MATCH** |
| **Observed defect** | The released, hash-verified artifact carried the **defect**; the fix existed **only** on the branch. A consumer doing the "safe" thing (pin the release) got the bug. Release and branch had also diverged in **package contents**, not only in the loader |
| **Rule statement** | *For any dependency, a fix or feature must be verified as **present in the artifact actually consumed**, by git ancestry against the release tag — not by its presence in the repository, its merge date, or a changelog entry. Additionally: pin the **code and the data to the same immutable reference** (commit SHA plus per-file SHA-256), never to a branch; and diff the release artifact against the branch that feeds it, because divergence is where surprises live.* |
| **Detection method** | (1) `git merge-base --is-ancestor <fix> <tag>` for every fix claimed to be included. (2) Compare `tag_date` to `fix_date`; a fix newer than the tag is **not** in it, regardless of claims. (3) `diff -rq` the installed artifact against the tagged tree and report every differing path — here that surfaced `helpers.py` **and** the missing `validation/`. (4) Re-hash artifacts and compare against registry-published digests |
| **Severity** | **S1 CRITICAL** — it determines whether a believed fix exists in the running system |
| **Cost** | Low |
| **FP risk** | **LOW.** Ancestry is decidable. The only subtlety is a **backported** fix (different SHA, same content) — hence check (3), content diff, alongside check (1), ancestry |
| **Would apply to** | `AHOS_UPDATE_POLICY.md`; `docs/OPERATOR_VALIDATION_PROTOCOL.md`; `docs/OSS_HARVEST_LOG.md`; every dependency audit |
| **Confidence** | **HIGH** — git-proven |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

### DQR-12 · Reproducibility environment retention

| Field | Value |
|---|---|
| **Topic** | Reproducibility environment retention |
| **Derived from** | **ENV-DUR-01.** The original investigation's environment (`/tmp/fdb_repo`, `/tmp/fdb_venv`, `/tmp/fdb_lab`) **did not survive one session** and had to be rebuilt from scratch as `/tmp/fdb2_*`. Every machine-readable output lived only in `/tmp`. Durable copies now exist under `evidence/followup/` (6 JSONs) with two environment records (`evidence/ENVIRONMENT.txt`, `evidence/FOLLOWUP_ENVIRONMENT.txt`) and 18 scripts (`evidence/scripts/`) |
| **Observed defect** | Evidence stored only in a temporary environment was, for one session boundary, **not evidence**. The rebuild cost a full re-execution pass, and one measurement (the GICS CI log) could not be re-obtained at all because its host was unreachable — it was substituted by local re-execution |
| **Rule statement** | *An investigation is not complete until its evidence is **durable**: (1) machine-readable outputs archived inside the repository, not in a temporary path; (2) an environment record capturing exact versions, install commands, pinned commit and artifact hashes; (3) the scripts that produced each output; (4) an explicit statement of which measurements **could not** be preserved and why. A path under `/tmp` is a scratch location, never an evidence location.* |
| **Detection method** | At close-out, assert for every cited evidence reference that the artifact **exists in the repository** and is readable without network access or a rebuilt environment. Any reference resolving only to a temporary path fails the check. Record declined/unpreservable measurements explicitly — `NOT TESTED` with a reason is a result |
| **Severity** | **S2 HIGH** for auditability · **S3 MEDIUM** for the investigation itself |
| **Cost** | Low — it is a close-out checklist, not a runtime control |
| **FP risk** | **NONE** for the existence check. One caveat: archiving large artifacts conflicts with repository-size discipline, so the rule must permit **derived** archives (JSON measurements) in place of **primary** ones (a 4.85 GB corpus) — which is exactly what this package does |
| **Would apply to** | `docs/protocols/AGENT_EVIDENCE_PROTOCOL.md`; `docs/architecture/PROCESS_ISOLATED_RESEARCH_WORKER.md`; `docs/architecture/RESEARCH_ANALYST_AGENT.md` |
| **Confidence** | **HIGH** — the failure occurred and was observed directly, twice |
| **Status** | **CANDIDATE — NOT AHOS POLICY** |

---

## 28.2 Candidate summary

| ID | Topic | Rule (short) | Severity | Cost | FP risk | Confidence | Status |
|---|---|---|---|---|---|---|---|
| **DQR-01** | Row-count vs cell-level | Compare the **key domain** separately from rows and cells | **S1** | Low | LOW | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-02** | Null / key preservation | Assert no null key immediately after parsing | **S1** | Very low | LOW | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-03** | dtype · sentinel `NA` | One declared null token; identifiers read as text; **fix every reader incl. CI** | **S1** | Low-Med | LOW | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-04** | Sentinel values | Per-column sentinel vocabulary; detect serialization leakage | S2 | Med | MED | HIGH/MED | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-05** | Completeness *(new)* | Count **stub** records (key populated, content empty) per table | S2 | Low | LOW-MED | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-06** | Duplicate / collision | Six collision levels, each reported with denominator and examples | S2 | Med | MED | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-07** | Filtered-row coverage | Publish `examined / excluded / predicate / coverage_pct` with every invariant | **S1** | Very low | **NONE** | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-08** | Zero-variance imputation | Mark imputed values at write time; detect the signature at review-only severity | S2/S3 | Low-Med | **HIGH at small n** | HIGH/MED | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-09** | Timestamp / freshness | Two timestamps per record; freshness **per subset**; verify the **write target** | S2 | Low-Med | LOW | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-10** | Default-branch CI | Validate on the data commit; gate before publish; track streaks; no false gates | **S1** | Low | LOW-MED | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-11** | Release / tag ancestry | Verify a fix is in the **consumed artifact** by git ancestry + content diff | **S1** | Low | LOW | HIGH | **CANDIDATE — NOT AHOS POLICY** |
| **DQR-12** | Reproducibility retention | Evidence is durable only when archived in-repo with its environment record | S2 | Low | NONE | HIGH | **CANDIDATE — NOT AHOS POLICY** |

**Registered: 12. Five at S1 CRITICAL (DQR-01, 02, 03, 07, 10, 11 — six including 11). Adopted: 0.**

**All twelve: `CANDIDATE — NOT AHOS POLICY`. Implementation authorized: NO.**

**If Agent B ever authorizes a subset, Agent E's recommended order** — by (severity × low FP risk ×
low cost), which is deliberately **not** the same as importance:

1. **DQR-07** — zero false-positive risk, near-zero cost, and it makes every *other* check
   interpretable. Adopting nothing else, adopt this.
2. **DQR-02** — one assertion, S1, deterministic.
3. **DQR-11** — decidable, low cost, and it answers "is the fix we believe in actually running?"
4. **DQR-01** — the direct lesson of the reproduced regression.
5. **DQR-12** — a close-out checklist; costs nothing at runtime.
6. **DQR-03** — highest value, but requires enumerating every read site.
7. **DQR-05**, **DQR-09**, **DQR-10**, **DQR-06**, **DQR-04** — each needs a declaration
   (required-content list, subset map, workflow topology, namespace map, sentinel vocabulary) to
   exist **before** the rule can fire.
8. **DQR-08 last, and only with Agent B-set thresholds.** Its false-positive rate at small *n* is
   the highest in this document, and it must never be blocking.

---

## 28.3 What these candidates are **not**

| Non-claim | Explanation |
|---|---|
| Not a finding that AHOS lacks these controls | **No AHOS validation surface was audited in this pass.** Several are plausibly already satisfied — `architecture/providers/contracts.py:5,16` already encodes a strict-UNKNOWN law, and `architecture/identity/types.py:24-33` already requires two timestamps per source, which is precisely DQR-09's core requirement |
| Not a certification that AHOS data is clean | Absence of an observed defect in a reviewed scope is **not** cleanliness |
| Not a benchmark | No rule was executed against AHOS data. Every measurement in this document is of the **FinanceDatabase** corpus |
| Not policy | Promotion requires Agent B review and separate written authorization |
| Not a prioritization of AHOS work | The order in §28.2 is Agent E's recommendation **on the evidence**, offered for Agent B to accept, amend or reject |

## 28.4 Scope limitation, stated explicitly

This pass was **read-only over the FinanceDatabase evidence package**. It did **not**:

- audit any AHOS validation, ingest, CI or test surface for the presence or absence of these rules;
- execute any candidate rule against AHOS data;
- measure whether any AHOS pipeline has a null-key, stub-record, coverage-reporting or ancestry gap.

**Any statement about AHOS's current posture with respect to DQR-01…DQR-12 is therefore UNKNOWN and
must not be inferred from this document.** Establishing it would require a separate, authorized audit
of the AHOS validation surface — which Agent E does not recommend undertaking while the 72-hour soak
is active.

## 28.5 Reproduction note

All twelve candidates derive from measurements reproducible from artifacts archived under
`evidence/`, plus one new measurement (DQR-05 / KN-12) taken during this pass from the pinned
`/tmp/fdb2_repo` corpus. To comply with the deliverable constraint (*create only documents 26–30*),
**no new evidence artifact file was written**; the DQR-05 measurement is fully specified in §28.1 and
in document 26 §26.9, and Agent B may authorize archiving its output under `evidence/followup/`.

**No AHOS file was created or modified by this document. No server was started. The 72-hour soak was
not disturbed. No package was installed into the AHOS environment.**
