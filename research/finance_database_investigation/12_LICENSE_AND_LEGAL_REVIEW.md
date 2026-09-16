# 12 — Licensing & Legal Compatibility

**Phase 12.** This document identifies questions and evidence. **It does not give legal advice
and does not assert legal certainty.** Where the situation is ambiguous the required verdict is
stated: **LEGAL REVIEW REQUIRED**.

---

## 12.1 Software licence — clear

| Item | Value | Source |
|---|---|---|
| Licence | **MIT** | GitHub API `license` endpoint (`spdx_id: MIT`, `path: LICENSE`); `pyproject.toml:5` `license = {text = "MIT"}`; PyPI `info.license = "MIT"`; classifier `License :: OSI Approved :: MIT License` |
| Copyright line | `Copyright (c) 2023 Jeroen Bouma` | `LICENSE` file, read verbatim |
| Present in the sdist | Yes — `financedatabase-2.4.0/LICENSE` | artifact inspection |
| Present in the wheel | Yes — `financedatabase-2.4.0.dist-info/licenses/LICENSE` | artifact inspection |
| Scope of the grant | *"this software and associated documentation files (the 'Software')"* — use, copy, modify, merge, publish, distribute, sublicense, **sell** | `LICENSE` text |
| Attribution obligation | *"The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software."* | `LICENSE` text |
| Warranty | **Disclaimed in full** — *"WITHOUT WARRANTY OF ANY KIND … INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT"* | `LICENSE` text |

**Implication for AHOS:** MIT is maximally permissive and fully compatible with AHOS's stated
policy (`requirements.txt`: *"free, permissively licensed"*; `docs/OSS_HARVEST_LOG.md`: *"Source
code is only copied when its licence permits it"*). Copying or vendoring **code** requires only
retaining the copyright and permission notices. Commercial use is permitted. The warranty
disclaimer means **no fitness representation exists** — which aligns with, and legally reinforces,
AHOS's own `UNKNOWN ≠ SAFE` posture.

The copyright year (2023) predates substantial 2025–2026 development; whether the notice should
list additional years or contributors is a housekeeping question, **not** a defect.

## 12.2 Dataset licence — the actual problem

**Finding LEG-01 — the dataset has no separate licence, and the repository's MIT notice does not
clearly cover it.**

| Observation | Evidence |
|---|---|
| The data lives in the same MIT-licensed repository (`database/`, `compression/`) | Repository tree |
| There is **no** `NOTICE` file, no `DATA-LICENSE`, no `ODC-By`/`ODC-BL`/`CC0`/`CC-BY` marker anywhere in the tree | Full listing of the repo root: `.github`, `.gitignore`, `.pre-commit-config.yaml`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `compression/`, `database/`, `examples/`, `financedatabase/`, `pyproject.toml`, `tests/`, `uv.lock` |
| The MIT text grants rights in *"this software and associated documentation files"* — a **CSV of 304,495 financial listings is neither software nor documentation** | `LICENSE` text |
| `compression/README.md` discusses the data only in terms of file format and download cost, never licence | read in full |
| `CONTRIBUTING.md` discusses contribution mechanics and identifier validation, never data licensing or contributor copyright assignment | grep for `license`/`attribution` |
| No CLA / DCO configuration was found in the reviewed scope | absence in the repo root and `.github/` |

So the ~145 MB dataset is, on the face of the repository, **covered by an MIT notice that was
written for code**. MIT is a copyright licence; whether it effectively licenses a large curated
factual dataset — and whether it can waive the *sui generis* database right that may subsist in
it — is a genuine legal question.

**Finding LEG-02 — the upstream source for all automated equity updates has NO licence.**

`database_update.yml:167,173,179` reads three JSON files from
`github.com/rreichel3/US-Stock-Symbols`. GitHub API on that repository:

```
full_name      = rreichel3/US-Stock-Symbols
description    = "Full lists of US Securities on the NASDAQ, NYSE, and AMEX powered by GitHub Actions"
license        = None            ← no licence at all
stars          = 574
created_at     = 2021-01-30
pushed_at      = 2026-09-15T00:39:12Z
recent commits = "generated", "generated", "generated"
```

Under the Berne Convention default, an unlicensed work is **all rights reserved**. The
FinanceDatabase pipeline copies fields from it (`name`, `marketCap`, `industry`, `country`,
`market` — see `build_new_ticker`, `database_update.yml:137-159`) into an MIT-licensed repository
that is then redistributed to the public and to PyPI users.

Two mitigating considerations, both of which are *legal arguments we are not qualified to make*:
(i) the copied content may be **facts** (a company name, a market capitalization) rather than
protectable expression, and facts are generally not copyrightable; (ii) a symbol *list* generated
mechanically from exchange data may lack the originality required for protection. Neither
consideration resolves the question, and neither is our call.

> ### **LEGAL REVIEW REQUIRED** — upstream provenance
> Specifically: whether incorporating fields from an unlicensed scraped-symbol repository into a
> redistributed MIT dataset creates an obligation or an exposure for a downstream commercial user
> such as AHOS.

**Finding LEG-03 — the origin of the bulk of the dataset is undocumented.**
No script in the repository generates `database/cryptos.csv`, `currencies.csv`, `indices.csv`,
`moneymarkets.csv`, `etfs/`, `funds/`, or the non-US `equities/` shards. README:467 attributes
ongoing maintenance to community contributions, and CONTRIBUTING:4 says the project *"relies on
involvement from the community to update, edit and remove tickers over time"*. But the **original
bulk import** has no recorded provenance. The style of `summary` prose, the `CCC`/`CCY` exchange
codes and the `<TOKEN>-<QUOTE>` / `BASEQUOTE=X` symbol conventions all point to **Yahoo
Finance**, and `CCC` specifically to **CryptoCompare** — this is **INFERENCE from convention, not
verified provenance** (U-04).

Yahoo Finance data is generally made available under terms of service that restrict
redistribution and commercial reuse. If any part of the 304,495 rows originated there, the
redistribution question is materially different from the MIT question.

> ### **LEGAL REVIEW REQUIRED** — bulk dataset provenance

## 12.3 Identifier-specific and trademark-specific exposure

| Element | Present in the data | Third-party rights question | Severity for a public AHOS product |
|---|---|---|---|
| **CUSIP** | 27,286 populated equity values | CUSIP is a **registered trademark of the American Bankers Association**, and CUSIP numbers are administered/licensed commercially (CUSIP Global Services / S&P). Bulk redistribution of CUSIPs is a well-known commercial-licensing flashpoint | **HIGH** — the single most concrete legal exposure identified |
| **FIGI / composite FIGI / shareclass FIGI** | 58,556 / 60,892 / 63,990 populated | FIGI is a **Bloomberg** identifier scheme distributed via OpenFIGI under its own terms; `FIGI` is a Bloomberg trademark. OpenFIGI usage is free but carries terms, and the validator in this repo cites `openfigi.com/docs/figi-check-digit.pdf` | **MEDIUM–HIGH** |
| **ISIN** | 30,429 populated | **ISO 6166** standard; ISINs are issued by National Numbering Agencies. Widely treated as facts, but some NNAs assert rights, and the ISO standard text itself is copyright | **MEDIUM** |
| **MIC** | 71 distinct | **ISO 10383**, administered by SWIFT. The code list is published; usage terms apply | **LOW–MEDIUM** |
| **GICS®** | 11 sectors / 24 industry groups / 80 industries; a CI job named `Check-GICS-Categorisation`; `Equities.py:18` says *"adhering to the GICS standard"* | **GICS® is a registered trademark of MSCI Inc. and S&P Dow Jones Indices LLC.** CONTRIBUTING:129 is careful and explicit: the categories *"loosely approximate"* GICS, *"No actual data is collected from this source"*, and classification is *"completely done through manual curation"* — so **no MSCI data is copied**. But the *name* GICS appears in code and CI, and a derivative product marketing "GICS classification" would raise trademark-adjacency questions | **MEDIUM** — mitigated by the project's own explicit disclaimer |
| **Company names, tickers, websites** | Throughout | Generally facts / nominative use; low risk individually | **LOW** |
| **`summary` prose** | 100,463 populated equity rows (89.15%), plus other classes | **Descriptive prose is protectable expression.** If sourced from Yahoo Finance profiles, wholesale redistribution is a copyright question, not a facts question | **MEDIUM–HIGH** (contingent on LEG-03) |
| **Exchange names / market names** | `New York Stock Exchange`, `NASDAQ Global Select`, `XETRA` | Nominative use; trademarks of the respective exchanges | **LOW** |

## 12.4 EU *sui generis* database right

Directive 96/9/EC creates a database right protecting the **investment in obtaining, verifying
and presenting** the contents of a database, independent of copyright in the contents. A curated
304,495-row financial database with:

- a weekly automated verification/update pipeline,
- an ISO/FIGI checksum validator,
- a CI job enforcing GICS-triple consistency,
- four invariant tests, and
- documented manual curation by a community,

is a plausible candidate for *sui generis* protection in the EU/EEA. **MIT is a copyright licence
and does not clearly waive database rights.** If the right subsists and is not licensed,
substantial extraction and re-utilization — which is exactly what vendoring 145 MB of CSV into
AHOS would be — could require permission that MIT does not obviously grant.

The author appears to be Netherlands-based (the README examples use `country='Netherlands'`,
Euronext Amsterdam, and the project's own docs are Dutch-market-flavoured), which makes the
EU database-right question **more**, not less, relevant.

> ### **LEGAL REVIEW REQUIRED** — EU database right
> Whether vendoring, redistributing or publicly serving derived content from this dataset in or
> to the EU/EEA requires a licence beyond MIT.

## 12.5 Redistribution, commercial use and derivative databases

| Right | Position under the MIT notice | Position in reality |
|---|---|---|
| Commercial use | **Granted** | Contingent on LEG-01…04 — the *code* is clearly commercial-safe; the *data* is not clearly licensed |
| Redistribution of the code | **Granted**, with notice retention | Clear |
| Redistribution of the dataset | Ambiguous | **LEGAL REVIEW REQUIRED** |
| Creating a derivative database | Ambiguous | **LEGAL REVIEW REQUIRED** — and note the derivative would inherit the upstream questions (CUSIP, FIGI, Yahoo-derived prose, unlicensed upstream JSON) |
| Sublicensing / selling | **Granted** by MIT text | Same contingency |
| Attribution requirements | Retain the MIT copyright + permission notice in all copies or substantial portions | If AHOS vendors data, best practice is to attribute `JerBouma/FinanceDatabase` **and** record the source commit SHA — this is also an evidentiary control, not just a legal one |
| Data ownership | Unstated | **UNKNOWN** |
| Data provenance obligations | **None recorded anywhere.** No machine-readable provenance manifest exists | Verified absence |
| API-provider terms (FMP / Yahoo via FinanceToolkit) | Not governed by FinanceDatabase's licence at all | FinancialModelingPrep and Yahoo Finance each have their own terms; the affiliate link at `helpers.py:248-255` implies a commercial relationship between the author and FMP |

## 12.6 Compatibility with AHOS's own licensing policy

AHOS's `docs/OSS_HARVEST_LOG.md` sets a standing rule:

> *"Techniques and public mathematics may be reimplemented freely. Source code is only copied
> when its licence permits it **and** the code survives our constraints ($0/month, works under
> sanctions and filtering, no paid API dependency, auditable offline). When those conflict, we
> reimplement from first principles and say so here."*

Applied to FinanceDatabase:

| Component | Licence permits copying? | Survives AHOS constraints? | Recommended treatment under AHOS's own rule |
|---|---|---|---|
| **Techniques** — bz2-compressed CSV catalogue; validated `select` with fail-closed `ValueError`; a precomputed `categories` sidecar so option lists load without the big file; ISO 6166 / CUSIP / OpenFIGI check-digit validation; the `actionable` vs `review-only` repair distinction; `mtime=0` gzip for byte-reproducible artifacts; invariant tests for cross-file key collisions | **Yes** — public mathematics and standard technique | **Yes** | **Reimplement from first principles**, and log it in `OSS_HARVEST_LOG.md`. The check-digit algorithms are published standards (ISO 6166, OpenFIGI's public PDF), so AHOS can implement them directly with no licence obligation |
| **Source code** — the 1,866-line package | **Yes** (MIT, with notice) | **No** — requires a live fetch from a mutable branch on a host measured unreachable, and drags `financetoolkit` → `yfinance` + `scikit-learn` + `pandas>=3.0` | **Do not copy.** Per AHOS's own rule, reimplementation is the correct call, and the reason is operational, not legal |
| **Dataset** — 145 MB / 304,495 rows | **Ambiguous** (LEG-01…04) | **Yes**, if vendored at a pinned commit | **LEGAL REVIEW REQUIRED before any vendoring, redistribution or public serving.** Internal, non-redistributed research use at a pinned commit is the lowest-risk posture, and even that should be reviewed before AHOS becomes a public product |

## 12.7 Summary

| Question | Answer | Status |
|---|---|---|
| Software licence | **MIT**, clear, permissive, commercial-friendly, warranty-disclaimed, present in both artifacts | **VERIFIED** |
| Dataset licence | **Not separately stated**; MIT notice covers "software and documentation" | **VERIFIED absence** ⇒ **LEGAL REVIEW REQUIRED** |
| Third-party source licences | Upstream `rreichel3/US-Stock-Symbols` has **`license = None`**; bulk-import provenance **undocumented**; Yahoo Finance / CryptoCompare strongly implied by convention | **VERIFIED** (upstream) + **INFERENCE** (bulk) ⇒ **LEGAL REVIEW REQUIRED** |
| Attribution requirements | MIT notice retention for code; no data-attribution mechanism exists | **VERIFIED** |
| Redistribution rights | Clear for code; **ambiguous for data** | **LEGAL REVIEW REQUIRED** |
| Commercial-use restrictions | None in MIT; possible upstream/implied restrictions on data | **LEGAL REVIEW REQUIRED** |
| Derivative database restrictions | Unaddressed; EU *sui generis* right may apply | **LEGAL REVIEW REQUIRED** |
| API provider terms | FMP / Yahoo terms apply to `to_toolkit()` paths and are **not** governed by this licence | **VERIFIED** (separation) |
| Data ownership | **UNKNOWN** | U-06 |
| Data provenance obligations | **None recorded** | **VERIFIED absence** |
| Trademark exposure | **CUSIP (ABA/S&P) HIGH**, **FIGI (Bloomberg) MEDIUM–HIGH**, **GICS® (MSCI/S&P) MEDIUM**, ISIN/MIC MEDIUM/LOW | Identified, **not** assessed legally |

**Overall legal verdict for AHOS:** the **code** is unambiguously MIT and safe to learn from,
reimplement, or copy with attribution. The **data** is not clearly licensed for redistribution,
carries concrete identifier-trademark exposure (CUSIP above all), may attract an EU database
right, and derives in part from an unlicensed upstream. Before AHOS becomes a public product,
or before any dataset is vendored, mirrored, served or redistributed:

> ## **LEGAL REVIEW REQUIRED**

Until that review happens, the only defensible posture is **internal, non-redistributed research
use of a snapshot pinned to a specific git commit, with the provenance recorded in AHOS's
evidence register** — which is exactly what this investigation did, and exactly what the
**C. RESEARCH-ONLY VALUE** judgment in §18 implies.
