# 23 — Reusable Engineering Knowledge

**Document 23 — Objective F.** Which techniques from FinanceDatabase are safe candidates for
**independent reimplementation** by AHOS.

> ## ⚠️ NOTHING HERE IS IMPLEMENTED
> No source code was copied. No proprietary data was copied. No dependency was added. No AHOS file
> was created or modified. Every entry below is marked **APPROVED: NO — PROPOSED** unless a future
> authorization says otherwise. This document is an *assessment of reusability*, not a work order.

> **Governing rule** (`docs/OSS_HARVEST_LOG.md`, quoted in document 14 §14.6):
> *"Techniques and public mathematics may be reimplemented freely. Source code is only copied when
> its licence permits it **and** the code survives our constraints ($0/month, works under sanctions
> and filtering, no paid API dependency, auditable offline). When those conflict, we reimplement
> from first principles and say so here."*

---

## 23.0 The correction that reframes this whole document

The original assessment (document 14 §14.8, items T-1…T-3) described the identifier check-digit
algorithms as *"~15 lines, no licence obligation"* to reimplement, and cited
`validation/validate_identifiers.py` as their source.

**Re-verification found that the repository does not implement those algorithms at all.**

```python
# financedatabase/validation/validate_identifiers.py:13   (at commit a174c97d3b)
from stdnum import cusip, figi, isin
```

```
$ pip show python-stdnum
Name: python-stdnum     Version: 2.2
License: LGPL
Home-page: https://arthurdejong.org/python-stdnum/
PyPI classifier: License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)
```

**Consequences, stated precisely:**

1. **`python-stdnum` is LGPL-2.1+ — a weak-copyleft licence, NOT a permissive one.** AHOS's
   `requirements.txt` law admits only *"free, permissively licensed"* packages. Adding
   `python-stdnum` would **conflict with AHOS's own stated dependency policy**. (Whether LGPL is
   *legally* problematic for a Python import is a separate question and is **not** answered here —
   the point is the **policy** conflict, which is verifiable from AHOS's own file.)
2. **Copying the validator's code would not give AHOS the algorithms.** The code is a thin
   orchestration layer over `stdnum`. Copying it imports an LGPL dependency by the back door while
   the surrounding file is MIT. That is the worst of both worlds.
3. **The algorithms themselves remain freely reimplementable** — they are published in ISO 6166
   (ISIN), the CUSIP mod-10 scheme, and OpenFIGI's public check-digit specification
   (`openfigi.com/docs/figi-check-digit.pdf`, cited by the project's own validator). Those are
   **public specifications**, and implementing from a specification is not copying an LGPL library.

> **Revised guidance.** Reimplement from the **published standards**, not from this repository and
> not via `python-stdnum`. The technique is clean; *this* implementation path is not.

A second, independent reason to reimplement rather than copy: the validator is **only on `main`**,
not in any release (document 21 §21.4 — `diff -rq` shows `validation/` present only in the repo).
There is no versioned, hash-pinnable artifact containing it.

## 23.1 Assessment matrix

Legend for **Approved**: `NO — PROPOSED` = assessed as safe and valuable, awaiting separate
authorization. Nothing in this document is self-authorizing.

### T-1 · ISIN check-digit validation (ISO 6166)

| | |
|---|---|
| **General engineering concept** | Mod-10 (Luhn-variant) check digit over a 12-character alphanumeric code: 2-letter country prefix + 9-character NSIN + 1 check digit; letters mapped to digits (A=10 … Z=35), then doubled-alternately from the right |
| **Why useful** | Detects transcription errors in the most widely used security identifier. Cheap, deterministic, offline |
| **Depends on third-party data?** | **No** — pure function of the string |
| **Depends on proprietary identifiers?** | The *algorithm* is public (ISO 6166). **Using ISIN values at scale** may implicate National Numbering Agency positions — see document 19 §19.5 row 4 |
| **Implementable from public standards?** | **Yes** — ISO 6166 is a published standard; the check-digit procedure is widely documented |
| **Legal review needed?** | **No** for the algorithm. **Yes** if AHOS stores or redistributes ISIN *values* in bulk |
| **AHOS relevance** | **MEDIUM** — AHOS's crypto domain uses `(chain, address)`, not ISIN. Relevant only to a future TradFi lane, and to validating any ISIN received from a third-party provider |
| **Approved for implementation?** | **NO — PROPOSED** |

### T-2 · CUSIP-9 check-digit validation

| | |
|---|---|
| **General engineering concept** | Mod-10 with alternating doubling over 9 characters (letters mapped 10–35, `*`=36, `@`=37, `#`=38); the check digit is `(10 - sum mod 10) mod 10` |
| **Why useful** | Same as T-1, for North American securities |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **Yes — this is the sharpest case.** CUSIP is a **registered trademark of the American Bankers Association**, and CUSIP numbers are administered and licensed commercially (CUSIP Global Services / S&P). The *checksum* is public mathematics; the *number space* is commercially controlled |
| **Implementable from public standards?** | **Yes** — the algorithm is public and widely published |
| **Legal review needed?** | **Yes for any use of CUSIP values.** The algorithm: no. Document 19 §19.5 rates CUSIP the **highest** concrete legal exposure in the dataset |
| **AHOS relevance** | **LOW** — no crypto application |
| **Approved for implementation?** | **NO — PROPOSED**, and the **lowest-priority** item in this document. Implement the checksum only if a TradFi lane needs to *validate* a CUSIP received from elsewhere; do **not** build a CUSIP corpus |

### T-3 · FIGI check-digit validation (OpenFIGI)

| | |
|---|---|
| **General engineering concept** | 12-character alphanumeric FIGI with a check digit defined in OpenFIGI's public specification; the project's validator cites `openfigi.com/docs/figi-check-digit.pdf` directly |
| **Why useful** | FIGI is the only identifier in this dataset with >50% coverage, and its three-level hierarchy (`shareclass_figi` → `composite_figi` → `figi`) is the only issuer-grouping mechanism available |
| **Depends on third-party data?** | **No** for the checksum |
| **Depends on proprietary identifiers?** | **Yes** — FIGI is a **Bloomberg** scheme and trademark, distributed via OpenFIGI under its own terms (free to use, but terms apply) |
| **Implementable from public standards?** | **Yes** — OpenFIGI publishes the check-digit specification freely |
| **Legal review needed?** | **Yes for bulk FIGI values** (MEDIUM–HIGH per document 19). No for the algorithm |
| **AHOS relevance** | **LOW–MEDIUM** — the hierarchy concept (share class → composite → global) is genuinely interesting as a model for AHOS's own token→pool→dex grouping, and can be adopted as a **design idea** with zero licence exposure |
| **Approved for implementation?** | **NO — PROPOSED**. Recommended: adopt the **hierarchy concept**, skip the identifier |

### T-4 · `actionable` vs `review-only` repair classification

| | |
|---|---|
| **General engineering concept** | Partition data-repair findings into (a) those with a **deterministic, evidence-backed** fix that may be applied automatically, and (b) those that are **ambiguous** and must be left for human adjudication — and *report both*, changing only (a) |
| **Why useful** | This is the single most transferable idea in the repository. It is the correct answer to "how do you auto-repair data without making things worse". Verified logic (`validate_identifiers.py:246-250`):<br>`actionable = (field != "cusip") or (replacement is not None) or isin_precludes_cusip(values.get("isin",""))`<br>i.e. a finding is auto-repairable only when a corroborated replacement exists, or when a *valid* ISIN positively excludes the recorded CUSIP. Otherwise: `review-only`, left unchanged, **reported** |
| **Depends on third-party data?** | **No** — it is a policy pattern |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | It is not a standard; it is a **design pattern**, freely adoptable |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH.** Directly applicable to any AHOS data-repair, provider-disagreement or canonicalization queue. The measured outcome validates it: **2 findings of 249,085 identifiers, 0 actionable, 2 review-only** — the automation changed nothing and surfaced two items for a human. That is exactly the `UNKNOWN ≠ SAFE` posture expressed as a repair policy |
| **Approved for implementation?** | **NO — PROPOSED — highest priority in this document** |

### T-5 · Precomputed `categories` sidecar

| | |
|---|---|
| **General engineering concept** | Materialize the **distinct values of each queryable column** into a small sidecar artifact, so that option validation and `show_options()` need never load the large table |
| **Why useful** | Measured: `compression/categories/` is **2.0 MB** while `compression/equities.bz2` alone is **15 MB**. Validation of a filter value therefore costs ~13% of a full load. It is also what makes `select()` **fail closed** — an unknown value can be rejected *before* touching the data |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | Standard practice (materialized dimension/lookup index) |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH** for any large AHOS reference table or allowlist. Also a **cautionary** example: the sidecar can **drift** from the data — document 06 found 3 "phantom countries" that the sidecar offered but the live data could not return (delisted rows). **Any sidecar must be regenerated in the same atomic step as the data, and drift must be asserted against** |
| **Approved for implementation?** | **NO — PROPOSED**, with the drift assertion as a mandatory part of the design |

### T-6 · `mtime=0` gzip for byte-reproducible artifacts

| | |
|---|---|
| **General engineering concept** | Zero the embedded timestamp in a compressed artifact so that identical uncompressed content produces **byte-identical** output, making content hashing and diffing meaningful |
| **Why useful** | Verified in the workflow with the project's own explanatory comment (`database_update.yml:373-377`):<br>`# dtype=str keeps numeric-looking fields (zipcode, cusip) as text, so the generated option lists hold "9763" rather than "9763.0".`<br>`# A fixed mtime keeps the gzip artifacts byte-identical when their uncompressed content has not changed.`<br>`gzip = {'method': 'gzip', 'mtime': 0}`<br>Without this, every regeneration produces a different hash and **no snapshot can be pinned or diffed** |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | It is a documented parameter of the gzip format / pandas' compression options |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH and immediately applicable.** This is the enabling control for document 14's boundary rules **B-6/B-7** (per-file SHA-256 manifests, hash-pinned snapshots) and for the `raw_payload_sha256` field AHOS's own contract already requires. Without deterministic artifacts, provenance hashing is noise |
| **Approved for implementation?** | **NO — PROPOSED — second-highest priority** |

### T-7 · Rejecting pickle in favour of CSV+bz2 on security grounds

| | |
|---|---|
| **General engineering concept** | When choosing a serialization format for **remotely-fetched** data, prefer a **non-executable** format even at a measurable performance cost, because deserialization of untrusted binary is a code-execution vector |
| **Why useful** | The project benchmarked the alternatives, found **pickle(xz) fastest**, and **rejected it anyway** — documented in its own `compression/README.md`: *"to solve the vulnerability issue that arises with loading with Pickles I've decided to take the next best thing, this is the CSV BZ2 option which is about the same in terms of loading."* The methodology is preserved in `compression/compression.ipynb`. Result verified: **zero** `pickle`/`marshal`/`eval`/`exec` occurrences in the shipped package (document 11 §11.1) |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | It is a **policy**, not an algorithm |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH as corroboration.** AHOS already holds this posture; an independent, popular project reaching the same conclusion *after benchmarking* is useful external evidence for `OSS_HARVEST_LOG.md` and for any future debate about caching formats. **Adopt as a documented decision rule, with the benchmark requirement** — i.e. record what was given up |
| **Approved for implementation?** | **NO — PROPOSED** (documentation/decision-rule, not code) |

### T-8 · Invariant tests — the pattern is right, the placement is the lesson

| | |
|---|---|
| **General engineering concept** | Assert **cross-file / cross-schema invariants** (e.g. "no symbol appears in two asset classes", "the taxonomy triple is consistent") as first-class tests, separate from unit tests |
| **Why useful — and why it is a cautionary tale** | The project has exactly this: `tests/test_invariants.py`, and it **works** — it caught `CHAD` and fails loudly on `main` (document 22 §22.3). But three placement defects neuter it: (a) the CI **deselects** the live-database identifier test into a side job where it passes with a *warning*; (b) the taxonomy job runs **last**, after all four data-mutating jobs have pushed, so it cannot block (verified `needs:` list); (c) **data-changing commits trigger zero runs at all** (document 22 §22.1). Net effect: 10 consecutive taxonomy failures over 42 days, published throughout |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | Design pattern |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH — as an anti-pattern with a concrete fix.** Adopt the invariant-test idea; **invert the placement**: validate **before** publish, make it **blocking**, run it **on the data commit itself**, and let a failing invariant **quarantine the snapshot** rather than annotate it. Also adopt the corollary from document 22 §22.7: an invariant whose filter excludes 36% of rows is **not** a corpus-wide guarantee, and must not be reported as one |
| **Approved for implementation?** | **NO — PROPOSED — third-highest priority** |

### T-9 · Deliberate retention of delisted instruments

| | |
|---|---|
| **General engineering concept** | Keep delisted/dead entities in the corpus with an explicit boolean flag, so historical analysis is not distorted by survivorship bias |
| **Why useful** | Verified: **10,404** of 112,690 equities (9.23%) carry `delisted=True`, and README:465 states they are *"intentionally retained for historical research purposes."* A dtype-invariant test (`test_delisted_is_strictly_boolean`) guards the flag |
| **Depends on third-party data?** | **No** (concept) |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | Design pattern |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH for backtesting.** AHOS's crypto domain has the identical hazard — rugged, delisted and migrated tokens vanishing from provider lists would silently inflate backtest performance. **Note the limitation, verified:** the flag exists for **equities only**; open issue **#153** (2026-06-03) asks for ETFs and Funds. So even upstream this is a **partial** solution, and `exclude_delisted` is applied by `select()` but **not** by `search()` — two APIs, two populations |
| **Approved for implementation?** | **NO — PROPOSED** |

### T-10 · Fail-closed validated query surface (`select()`)

| | |
|---|---|
| **General engineering concept** | Validate every filter's **column name** and **value** against a known option set before querying; raise a `ValueError` naming the valid options on mismatch. Fail **closed** |
| **Why useful** | Verified at library level with the release-2.4.0 wheel: `Cryptos.select(cryptocurrency="SOL")` → `ValueError: "The cryptocurrency 'SOL' is not available in the database. Please check the available cryptocurrencies using the 'show_options' method."` An impossible query is **refused with guidance** rather than returning empty or everything |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | Design pattern (depends on T-5 for the option set) |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH.** The best idea in the codebase. **Adopt together with the counter-example:** the same library ships a *second*, **fail-open** API beside it — `search()`, which does not validate columns and returned **3,367 of 3,367** rows on a mistyped column name (re-verified, document 19 §A-11), and does not escape regex. **A fail-closed API next to a fail-open one is worse than two fail-closed ones**, because callers pick the permissive one. If AHOS adopts T-10, it must adopt it **exclusively** |
| **Approved for implementation?** | **NO — PROPOSED**, with the exclusivity condition |

### T-11 · Verbatim CSV preservation (`dtype=str, keep_default_na=False, na_values=[""]`)

| | |
|---|---|
| **General engineering concept** | Read identifier-bearing CSV as **text**, disable pandas' default NA-string inference, and declare exactly which token means null — so that a legitimate value like the ticker `NA` or the zipcode `9763` is not silently transformed |
| **Why useful** | This is the fix at the centre of document 21, and its necessity is **proven by execution**: without it, `"NA"` becomes `NaN` and the record's key is destroyed; the project's own workflow comment records two further casualties (`"9763"` → `"9763.0"`, `"031162100"` → `"31162100.0"`) which *"dropped that row on every run"*. **Scope measured: equities only, 1 record today — but the mechanism is general** |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | It is documented pandas behaviour, not a proprietary technique |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH — and the most immediately actionable item in this document.** Any AHOS ingest of CSV/TSV from any provider needs this, plus a **post-parse assertion that no key column is null**. Fixture **FIX-06** (document 20) is the proposed test. Note the corollary from document 22 §22.6: the upstream project fixed the **library** but left its **CI script** vulnerable (2 of the 10 failing rows show `exchange='nan'`) — fixing one reader is not fixing the system |
| **Approved for implementation?** | **NO — PROPOSED — highest practical priority** |

### T-12 · Dry-run-by-default destructive CLI

| | |
|---|---|
| **General engineering concept** | A data-mutating command-line tool defaults to **audit/report**; mutation requires an explicit opt-in flag; findings are also written to a machine-readable report file |
| **Why useful** | Verified in `validate_identifiers.py`: `--apply` is `action="store_true"` (so absence = dry run), described as *"Repair deterministic damage and clear other invalid identifiers"*; a separate `--report-file` writes the findings CSV; test names confirm the contract — `test_main_is_a_dry_run_by_default`, `test_apply_preserves_quoting_and_line_endings`, `test_main_apply_leaves_consistency_issues_for_manual_review`, `test_main_writes_post_cleanup_findings_to_csv_report` |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | Design pattern |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **HIGH.** This investigation was able to run the project's validator against live data **safely** precisely because dry-run is the default — that is the pattern working as intended. Adopt for any AHOS data-repair or migration tool, together with T-4 |
| **Approved for implementation?** | **NO — PROPOSED** |

### T-13 · Cross-identifier consistency and derivation

| | |
|---|---|
| **General engineering concept** | When two identifiers for the same entity are related by construction, **derive one from the other** and **assert consistency**, rather than validating each in isolation |
| **Why useful** | Verified: `validate_isin_cusip_consistency(isin, cusip)` applies only where `isin[:2] in {"US","CA"}` and checks `isin[2:11] != cusip`; `cusip_from_authoritative_isin` extracts `isin_value[2:11]` and re-validates it; `_repair_cusip_from_isin` additionally tolerates float-mangled input via `cusip_value.removesuffix(".0")` and a leading-zero-insensitive comparison. For US/Canadian ISINs the CUSIP is **embedded** in characters 3–11, so a valid ISIN can *corroborate* or *refute* a recorded CUSIP — which is exactly the deterministic evidence T-4 requires before auto-repair |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **Yes** — CUSIP (see T-2). The *relationship* is structural and public; the *values* are commercially controlled |
| **Implementable from public standards?** | **Yes** — the ISIN structure is ISO 6166 |
| **Legal review needed?** | **Yes** if CUSIP values are stored or served (T-2). No for the structural rule |
| **AHOS relevance** | **MEDIUM as a pattern.** The transferable idea is broader than identifiers: **when two fields are related by construction, cross-check them — a corroborated repair is safe, an uncorroborated one is not.** That is a general AHOS data-fusion principle and maps directly onto multi-provider corroboration in `ProviderRouter` |
| **Approved for implementation?** | **NO — PROPOSED** (as the general cross-field corroboration principle; the CUSIP-specific form is low priority) |

### T-14 · Structure-preserving in-place field patching

| | |
|---|---|
| **General engineering concept** | When repairing one field of a large CSV, rewrite **only that field**, preserving quoting, delimiters and line endings — so the diff contains the repair and nothing else |
| **Why useful** | Verified: `_replace_csv_field(record, field_index, replacement)` operates on the raw record string with `_column_index(header, name)` locating the field, and `test_apply_preserves_quoting_and_line_endings` guards it. The alternative — `pd.read_csv` → mutate → `to_csv` — silently reformats the entire file (quoting, float coercion, line endings, column order), producing an unreviewable diff and risking exactly the `"9763"` → `"9763.0"` class of damage |
| **Depends on third-party data?** | **No** |
| **Depends on proprietary identifiers?** | **No** |
| **Implementable from public standards?** | Design pattern |
| **Legal review needed?** | **No** |
| **AHOS relevance** | **MEDIUM–HIGH.** Applies to any AHOS curated dataset that humans review via diff. Pairs naturally with T-6 (deterministic artifacts) — together they make data changes **auditable**, which is a precondition for the evidence doctrine AHOS operates under |
| **Approved for implementation?** | **NO — PROPOSED** |

## 23.2 Explicitly **excluded** from reuse

| Item | Why excluded |
|---|---|
| **Any copy of `validate_identifiers.py`** | MIT-licensed, so copying is *permitted* — but it `from stdnum import …`, which drags an **LGPL** dependency into a codebase whose stated law admits only permissive licences. Reimplement from the standards instead (§23.0) |
| **Adding `python-stdnum` to `requirements.txt`** | **LGPL-2.1+ is not permissive.** Policy conflict with `requirements.txt`. If anyone wishes to reconsider, that is a **LEGAL REVIEW REQUIRED** item, not an engineering decision |
| **Any FinanceDatabase data values** (identifiers, names, summaries, taxonomy) | Dataset licence unresolved; CUSIP/FIGI/GICS trademark adjacency; possible EU *sui generis* right — document 19 §19.5. **LEGAL REVIEW REQUIRED** before any vendoring |
| **The `search()` API design** | Fail-open, unvalidated, unescaped-regex. Adopt T-10 **exclusively** instead |
| **The `financetoolkit` / FMP / Yahoo integration path** | Undeclared cost, unpinned `yfinance`, affiliate-linked upsell, pandas≥3.0 conflict (documents 09, 11) |
| **The remote-loader architecture** | Single mutable host, no checksum, no cache, no offline mode; the host was measured unreachable twice (documents 11, 19) |
| **The CI job ordering** | Validation after publication, non-blocking (T-8's cautionary half) |
| **`mode()`-based classification imputation** | Produces imputations indistinguishable from curated values. Proven to have fired: the 129 `two` rows all carry exactly the `Financials` modes (document 20 CASE 5). **Anti-pattern — do not adopt** |

## 23.3 Priority ordering, if authorization is ever granted

| Rank | Item | Rationale |
|---:|---|---|
| 1 | **T-11** verbatim CSV preservation + null-key assertion | Cheapest, most broadly applicable, and its necessity is *proven by execution* (document 21). Zero licence exposure |
| 2 | **T-4** actionable vs review-only repair split | The most conceptually valuable pattern; embodies `UNKNOWN ≠ SAFE` as a repair policy. Zero licence exposure |
| 3 | **T-6** `mtime=0` deterministic artifacts | Prerequisite for hash-pinned provenance, which AHOS's contract already requires (`raw_payload_sha256`). Zero licence exposure |
| 4 | **T-8** blocking, pre-publication invariant tests | Converts a real upstream failure mode into an AHOS control. Zero licence exposure |
| 5 | **T-10** fail-closed validated queries (exclusive) | Good API discipline; depends on T-5. Zero licence exposure |
| 6 | **T-12** dry-run-by-default CLIs | Safety pattern; enabled this investigation. Zero licence exposure |
| 7 | **T-5** categories sidecar (with drift assertion) | Performance + fail-closed enabler; carries a known drift hazard |
| 8 | **T-9** delisted retention | Valuable for backtest integrity; upstream itself is only partial |
| 9 | **T-14** structure-preserving patching | Auditability; niche |
| 10 | **T-3** FIGI hierarchy *concept* (not the identifier) | Design idea only |
| 11 | **T-1** ISIN check digit | Only with a TradFi lane |
| 12 | **T-13** cross-field corroboration principle | General principle; the CUSIP-specific form is low priority |
| 13 | **T-2** CUSIP check digit | **Lowest.** Highest legal exposure, no crypto application |

**All thirteen: `APPROVED FOR IMPLEMENTATION = NO — PROPOSED`.** Items 1–6 have **zero** licence
exposure and **zero** dependency cost, and are recommended for authorization on their merits; items
11–13 should not be authorized without the legal review in document 19 §19.5.

**No code was copied to produce this document. No dependency was added. No AHOS file was modified.**
