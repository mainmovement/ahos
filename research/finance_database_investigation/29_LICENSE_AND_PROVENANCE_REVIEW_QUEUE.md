# 29 — License and Provenance Review Queue

**Document 29 · Extraction package deliverable 4 of 5.**

| Role | Agent | Function |
|---|---|---|
| Author | **Agent E — Evidence Authority** | Registers **facts** and **questions**, separated by licence layer. Determines nothing |
| Mandatory reviewer | **Agent B — Engineering Governor** | Routes the queue; blocks any technical action that depends on an unresolved item |
| Required external reviewer | **Qualified legal counsel** | The only party that may resolve any item below. **Not Agent E, not Agent B** |

> ## ⚠️ LEGAL REVIEW REQUIRED — ALL ITEMS
>
> **Every item in this queue is marked `LEGAL REVIEW REQUIRED`.** This document contains **no legal
> conclusion, no legal advice, no clearance, no opinion and no assessment of risk likelihood.** It
> separates verified facts into nine licence layers and states the question each layer raises.
>
> Where a mitigating argument is recorded, it is labelled **ARGUMENT — NOT A FINDING**. Recording an
> argument is not endorsing it, and its presence must never be read as reducing the review
> requirement.
>
> **No AHOS file was modified. No vendoring, mirroring, redistribution, serving or dependency
> addition occurred. `README.md` was not modified. No secret was stored.**

---

## 29.0 Why the layers are separated

A single "what is the licence?" question produces a single wrong answer. This corpus has **nine**
distinct licence/provenance layers with different owners, different instruments and different
consequences, and they do **not** inherit each other's status. The verified headline is:

> **Code: MIT — verified four ways, clear.**
> **Everything else: LEGAL REVIEW REQUIRED.**

The most important structural fact in this document is that **MIT is a copyright licence whose text
grants rights in *"this software and associated documentation files"*** — and a 305,495-row CSV
corpus is neither software nor documentation. Whether it reaches the data is **question LPR-04(a)**,
and it is not answerable by Agent E.

---

## 29.1 Layer 1 — Source-code licence

| Field | Value |
|---|---|
| **Queue ID** | `LPR-01-SOURCE-CODE-LICENCE` |
| **Subject** | The `financedatabase` Python package source code |
| **Verified facts** | `LICENSE` at `a174c97d3bba…` = **MIT**, 21 lines, `Copyright (c) 2023 Jeroen Bouma`. Corroborated **four** independent ways: (1) repository `LICENSE`; (2) `pyproject.toml:5` → `license={text="MIT"}`; (3) PyPI `info.license="MIT"`; (4) present in **both** distribution artifacts — sdist root **and** wheel `dist-info/licenses/`. Grant covers use, copy, modify, merge, publish, distribute, sublicense and **sell**. Condition: notice retention. Warranty: disclaimed in full. Artifact SHA-256 re-hashed this pass and **MATCH** the recorded digests and PyPI's published digests |
| **What is NOT determined** | Whether the grant's subject matter (*"software and associated documentation files"*) extends to the `database/` and `compression/` payloads shipped alongside the code — that is **LPR-04**, not this layer. Whether the warranty disclaimer is effective in all jurisdictions — **LPR-08** |
| **ARGUMENT — NOT A FINDING** | None required; this layer is the clearest in the package |
| **Review question for counsel** | Confirm that MIT as applied to this source imposes no obligation beyond notice retention for **internal research use**, and identify any obligation that would attach if code were vendored |
| **Blocking effect** | **NONE for internal research.** This layer does not block reading, cloning or analysing the source |
| **Status** | **LEGAL REVIEW REQUIRED** (confirmation only) |

---

## 29.2 Layer 2 — Dependency licence

| Field | Value |
|---|---|
| **Queue ID** | `LPR-02-DEPENDENCY-LICENCE` |
| **Subject** | Licences of libraries the code **imports**, as distinct from the licence of the file being read |
| **Verified facts** | **`python-stdnum` 2.2 = LGPL-2.1+** (PyPI classifier `GNU LGPLv2+`; home `arthurdejong.org/python-stdnum`), confirmed by `pip show` in the isolated environment. `financedatabase/validation/validate_identifiers.py:13` is `from stdnum import cusip, figi, isin` — the validator **delegates** rather than implementing check digits. Declared dependency: `pyproject.toml:35-37` → `dependencies=["financetoolkit>=2.0.3,<3.0.0"]`; PyPI `requires_dist` identical. `uv.lock` pins re-verified: `financetoolkit 2.0.7`, `pandas 2.3.3` **and** `3.0.3` under separate markers, `pytest 9.0.3`, `pytest-recording 0.13.4`, `vcrpy 8.1.1`. `numpy`, `pandas` and `requests` are imported directly yet **undeclared** |
| **What is NOT determined** | Whether LGPL-2.1+ obligations attach to a use that imports but does not modify or distribute `python-stdnum`; whether AHOS's own licence posture is compatible with an LGPL dependency in any form, including test-only |
| **Material correction carried here** | **F-CORR-01.** Document 14 §14.8 described the check-digit algorithms as *"~15 lines, no licence obligation"* to reimplement. That remains true **of the public standards** — but it is **not** what this repository does. **Any advice to "copy the validator" would import an LGPL dependency**, which conflicts with AHOS's own `requirements.txt` law (*"free, permissively licensed"*). **LGPL is not a permissive licence** |
| **ARGUMENT — NOT A FINDING** | That an unmodified LGPL library used via a normal import triggers no copyleft obligation. **Recorded, not endorsed; this is precisely the question for counsel** |
| **Review question for counsel** | (a) Does importing `python-stdnum` create any obligation for AHOS? (b) Is a **test-only** dependency distinguishable? (c) Is the AHOS `requirements.txt` permissive-only law a binding internal constraint that makes this moot? |
| **Agent E's technical mitigation — offered so the legal question can be avoided entirely** | **Reimplement check-digit validation from the published ISO 6166 / CUSIP / OpenFIGI specifications.** Public standards and public mathematics are the safe harvest under AHOS's own `OSS_HARVEST_LOG.md` rule. **Do not copy `validate_identifiers.py`. Do not add `python-stdnum`, including as a test dependency** |
| **Blocking effect** | **BLOCKS** any reuse path that copies the validator or adds `python-stdnum`. **Does not block** the specification-based reimplementation route |
| **Status** | **LEGAL REVIEW REQUIRED** |

---

## 29.3 Layer 3 — Algorithm / specification provenance

| Field | Value |
|---|---|
| **Queue ID** | `LPR-03-ALGORITHM-SPEC-PROVENANCE` |
| **Subject** | The **provenance of the algorithms themselves**, separate from any implementation of them |
| **Verified facts** | The algorithms in question are check-digit and structure validations for **ISIN (ISO 6166)**, **CUSIP-9**, **FIGI (OpenFIGI/Bloomberg)**, plus **MIC (ISO 10383, SWIFT-administered)** as a code list. All four are **published specifications**. This repository implements none of them directly — it delegates (LPR-02). Document 23 §23.1-23.3 records the algorithmic **concepts** as reusable (T-1, T-2, T-3, T-13) with licence exposure assessed per item |
| **What is NOT determined** | Whether any published specification's terms of availability restrict implementation; whether conformance claims (e.g. "validates to ISO 6166") carry certification or licensing obligations |
| **ARGUMENT — NOT A FINDING** | That implementing a published check-digit algorithm from its specification creates no licence obligation. **Recorded; not a legal conclusion** |
| **Review question for counsel** | (a) Is a from-specification reimplementation clean for ISO 6166, CUSIP-9 and OpenFIGI structures? (b) Does **using** the identifier schemes (as opposed to their values) require permission? (c) May AHOS describe its own validation as "ISO 6166 conformant"? |
| **Distinction that must not be blurred** | **Algorithm provenance ≠ identifier-value rights.** This layer concerns the *mathematics and structure*, which are published. Layer 6 (**LPR-06**) concerns the *values and marks*, which are administered commercially. A clean answer here does **not** imply a clean answer there |
| **Blocking effect** | **BLOCKS** claiming conformance or certification. **Does not block** specification-based reimplementation, subject to counsel |
| **Status** | **LEGAL REVIEW REQUIRED** |

---

## 29.4 Layer 4 — Dataset licence

| Field | Value |
|---|---|
| **Queue ID** | `LPR-04-DATASET-LICENCE` |
| **Subject** | The 305,495-row corpus in `database/` and `compression/` — seven tables: equities 112,690 · etfs 36,481 · funds 57,853 · indices 91,181 · currencies 2,556 · cryptos 3,367 · money markets 1,367 |
| **Verified facts** | **No dataset licence exists.** Absence verified by `find` over the entire tree at the pinned commit → **only `./LICENSE`**. There is **no** `NOTICE`, **no** `DATA-LICENSE`, **no** `COPYING`, **no** ODC / ODC-BY / ODC-PDDL / CC0 / CC-BY marker, **no** CLA and **no** DCO. The MIT text's grant is limited to *"this software and associated documentation files"*. Repository size ≈ **4.85 GB**; 9,119 stars; 941 forks; HEAD unmoved at `a174c97d3bba…` (2026-09-13T15:10:38Z), so these facts are **current**, not historical |
| **What is NOT determined** | Whether MIT reaches the data. Who holds rights in the data — author, contributors, or upstream. Whether the data is protectable expression, an unprotectable compilation of facts, or something in between |
| **ARGUMENT — NOT A FINDING** | (i) Facts themselves are not copyrightable; (ii) a mechanically assembled list may lack the originality required for compilation copyright. **Both recorded as arguments. Neither is a finding, and neither reduces the review requirement** |
| **Review questions for counsel** | **(a)** Does the root MIT licence cover `database/` and `compression/`? **(b)** Who owns the dataset — the author, the contributors, or the upstream source? **(f)** Is the Yahoo-implied provenance of `summary` prose (**protectable expression, not fact**) a copyright issue? |
| **Interim posture that requires no legal opinion** | **Internal, non-redistributed research use of a snapshot pinned to a specific commit, with provenance recorded.** This is the posture this investigation has taken throughout, and it is why the answer to (a) has not blocked any work in documents 00–28 |
| **Blocking effect** | **BLOCKS** vendoring, mirroring, redistribution, public serving, and any inclusion of corpus rows in an AHOS artifact. **Does not block** internal analysis of a pinned snapshot |
| **Status** | **LEGAL REVIEW REQUIRED** — highest priority in this queue |

---

## 29.5 Layer 5 — Upstream provenance

| Field | Value |
|---|---|
| **Queue ID** | `LPR-05-UPSTREAM-PROVENANCE` |
| **Subject** | (i) The automated equity feed; (ii) the undocumented bulk provenance of the other six tables |
| **Verified facts — (i) automated feed** | `rreichel3/US-Stock-Symbols`: **`license = None`**, 574 stars, `pushed_at 2026-09-15T00:39:12Z` (re-queried this pass). It feeds **all** automated equity updates via three `pd.read_json` calls to the **unpinned** `main` branch (`.github/workflows/database_update.yml:167,173,179` → `{nasdaq,nyse,amex}`). Commits are titled `generated` |
| **Verified facts — (ii) bulk provenance** | **No script generates** `cryptos`, `currencies`, `indices`, `moneymarkets`, `etfs`, `funds`, or non-US `equities`. There is **no** provenance manifest, **no** source column and **no** ingest date — a column-name scan for `date\|time\|updated\|asof\|timestamp\|snapshot\|version\|source\|provider\|retrieved` across all seven schemas returns **0 matches in 305,495 rows** (`A7_total_temporal_columns_found=0`). Stylistic indicators point to Yahoo Finance / CryptoCompare (`CCC` exchange codes — 3,362 of 3,367 crypto rows; `<TOKEN>-<QUOTE>` symbol form; `BASEQUOTE=X`; profile prose). **This is INFERENCE, not verification — U-04 remains UNKNOWN** |
| **What is NOT determined** | Whether the unlicensed upstream creates downstream exposure for a commercial user. Which service(s) the six bulk tables came from, and on what terms. Whether any part originated from a source whose ToS restricts redistribution or commercial reuse — **if Yahoo Finance, that is a different and larger question than MIT** |
| **ARGUMENT — NOT A FINDING** | That an unlicensed, mechanically generated symbol list is not a protected work, so its use creates no exposure. **Recorded; not endorsed** |
| **Review questions for counsel** | **(c)** Does an unlicensed upstream create downstream exposure for a commercial user such as AHOS? Plus: if the bulk tables originate from a service with restrictive ToS, does that govern regardless of the MIT licence on the code? |
| **Blocking effect** | **BLOCKS** any redistribution or commercial use of equity data attributable to the upstream. **BLOCKS** any claim about the corpus's origin. **Does not block** internal analysis |
| **Status** | **LEGAL REVIEW REQUIRED** |

---

## 29.6 Layer 6 — Trademark adjacency

| Field | Value |
|---|---|
| **Queue ID** | `LPR-06-TRADEMARK-ADJACENCY` |
| **Subject** | Identifier schemes and taxonomy names appearing in the corpus and its CI |
| **Verified facts** | **CUSIP** — American Bankers Association registered mark, commercially administered. Populated in the corpus; document 19 §19.5 rates it the **most concrete exposure** in the package. **FIGI** — Bloomberg identifier scheme and mark; `figi`, `composite_figi` and `shareclass_figi` columns populated (in the Berkshire case, on the two Vienna rows only). **ISIN** — ISO 6166; **30,429** equity rows populated (**27.0%**), **9,406** distinct. **MIC** — ISO 10383, SWIFT-administered. **GICS®** — registered mark of MSCI / S&P Dow Jones Indices: the CI job is literally named `Check-GICS-Categorisation`; `Equities.py` states the taxonomy is *"adhering to the GICS standard"*; `CONTRIBUTING.md:117-119` says sector / industry_group / industry each *"follows GICS"*. `categories.json` = 11 sectors / 24 industry groups / **69** industries; the data carries **80** industries |
| **Verified fact that narrows this layer** | `CONTRIBUTING.md:129`, read verbatim: *"the sectors, industry groups and industries loosely approximate to the [The Global Industry Classification Standard (GICS®)](https://www.msci.com/our-solutions/indexes/gics) as created by MSCI. **No actual data is collected from this source** … This is **completely done through manual curation**. The actual datasets as curated by MSCI have not been used in the development of any part of this database…"* — so on the project's own explicit statement, **no MSCI data is copied**, which makes this **trademark adjacency and naming**, not data infringement |
| **What is NOT determined** | Whether bulk redistribution or public serving of **CUSIP** or **FIGI** *values* requires a commercial licence. Whether naming a CI job and a code comment after GICS® is a nominative use or requires permission. Whether the 80-vs-69 industry divergence creates any misrepresentation exposure |
| **Review questions for counsel** | **(e)** Do CUSIP/FIGI **values** require a licence to redistribute or to serve publicly? Is nominative reference to GICS® permissible in internal tooling, in documentation, and in any public artifact? |
| **Technical mitigation already applied in this package** | Documents 20 and 27 **exclude CUSIP values entirely** and replace FIGI values with a `figi_present` boolean, so the proposed fixtures carry the structural point without embedding administered identifier values. **Any fixture that embeds real ISIN values makes LPR-06 a precondition** (document 27 §27.8) |
| **Blocking effect** | **BLOCKS** committing, serving or redistributing CUSIP/FIGI values. **BLOCKS** public use of the GICS® name pending review. **Does not block** internal analysis or the boolean-substituted fixture form |
| **Status** | **LEGAL REVIEW REQUIRED** — CUSIP highest urgency; GICS® naming lower urgency |

---

## 29.7 Layer 7 — Database rights

| Field | Value |
|---|---|
| **Queue ID** | `LPR-07-DATABASE-RIGHTS` |
| **Subject** | EU *sui generis* database right, Directive **96/9/EC** |
| **Verified facts — candidate investment indicators, all present** | The Directive protects **substantial investment** in obtaining, verifying or presenting contents. Every indicator is verified in this corpus: a **weekly automated update** pipeline (Sunday 12:00 UTC); a **checksum identifier validator** that examined **249,085** identifiers and found **2** invalid, both classified `actionable=False` (`evidence/identifier_issues.csv`; **99.9992% valid**); a **CI consistency job**; **four invariant tests**; documented **community curation** (`CONTRIBUTING.md`); and **305,495** rows. The author appears **Netherlands-based** — relevant to LPR-08 |
| **Verified fact that limits this layer** | **MIT is a copyright licence. It does not clearly waive database rights**, which are a distinct instrument |
| **What is NOT determined** | Whether the right **subsists** in this database. Whether it is **licensed** by anything in the repository. Whether AHOS's intended use would amount to **substantial extraction and re-utilization** |
| **The specific exposure, stated as a fact about scale rather than a legal conclusion** | Vendoring the corpus would mean handling ≈ **4.85 GB** across **305,495** rows — on its face the shape of activity the Directive's extraction and re-utilization concepts address. **Whether that triggers the right is a legal question, not a measurement** |
| **ARGUMENT — NOT A FINDING** | That investment in *automated* collection is not the kind of investment the Directive protects, or that the right does not subsist where contents are largely factual and mechanically gathered. **Recorded; not endorsed** |
| **Review question for counsel** | **(d)** Does an EU *sui generis* database right subsist in this corpus, and if so is it licensed by anything present? Does internal research use differ from vendoring in this respect? |
| **Blocking effect** | **BLOCKS** vendoring, mirroring or extracting the corpus into an AHOS artifact pending review. **Does not block** internal analysis of a pinned snapshot |
| **Status** | **LEGAL REVIEW REQUIRED** |

---

## 29.8 Layer 8 — Jurisdiction-specific review

| Field | Value |
|---|---|
| **Queue ID** | `LPR-08-JURISDICTION` |
| **Subject** | Which jurisdictions' law governs, and where the analysis must be repeated |
| **Verified facts** | Author appears **Netherlands-based** (relevant to EU database right, LPR-07). Upstream `rreichel3/US-Stock-Symbols` is a **US**-namespaced corpus of **US** exchange symbols (relevant to US copyright and to CUSIP administration). Identifier schemes are administered by **US** bodies (ABA for CUSIP; Bloomberg for FIGI) and **international** standards bodies (ISO for ISIN 6166 and MIC 10383, SWIFT-administered). The taxonomy mark is held by **MSCI / S&P Dow Jones Indices**. The corpus itself is **multi-jurisdictional** in content — verified listings span the US, Germany, France, Austria, Mexico, South Korea, China, India, Japan, Australia, the UK, Canada, Brazil, Belgium, the Netherlands, Spain, Switzerland, Ireland, Taiwan, Hong Kong, Saudi Arabia, Thailand, Vietnam, Indonesia, Israel and others, with **`country` unreliable as a jurisdiction signal** (the 129 `two` rows are all labelled `United States` while listing on Shenzhen, KOSPI, London, Berlin and Tel Aviv venues) |
| **What is NOT determined** | Which law governs any of layers 1–7 and 9. Whether the MIT warranty disclaimer is effective in each relevant jurisdiction. Whether AHOS's own jurisdiction of operation changes any answer. Whether the *content's* multi-jurisdictional scope creates obligations in the jurisdictions whose securities are described |
| **ARGUMENT — NOT A FINDING** | None offered — jurisdiction is not a layer where a technical argument substitutes for counsel |
| **Review question for counsel** | Which jurisdiction's law governs each of LPR-01…LPR-07 and LPR-09? Is a single review sufficient, or must the EU database-right question (LPR-07) and the US trademark/CUSIP question (LPR-06) be reviewed separately? |
| **A caution Agent E must register** | **`country` in this corpus is not a reliable jurisdiction field** — it is wrong for at least 129 verified rows and is imputed rather than observed (KN-06, KN-08, DQR-08). **Any jurisdictional analysis that uses the corpus's own `country` column as an input is built on a defective field.** Jurisdiction should be derived from `mic` where a jurisdiction signal is needed at all |
| **Blocking effect** | **BLOCKS** assuming a single-jurisdiction answer covers all layers. **Does not block** internal analysis |
| **Status** | **LEGAL REVIEW REQUIRED** |

---

## 29.9 Layer 9 — Redistribution rights

| Field | Value |
|---|---|
| **Queue ID** | `LPR-09-REDISTRIBUTION` |
| **Subject** | Whether AHOS may vendor, mirror, serve, publish or redistribute any part of the corpus or the code |
| **Verified facts** | **Code: redistribution is expressly granted** by MIT — including the right to *sell* — subject to notice retention. **Data: unstated.** There is no redistribution grant, no restriction and no licence for the data at all (LPR-04). Two further verified facts bear on it: the shipped package contains **zero** occurrences of `eval`, `exec`, `pickle`, `marshal`, `subprocess`, `os.system`, `socket`, `ctypes` or `open(`, and its entire network surface is **two** `requests.get` calls for static files — so redistribution of the **code** carries no embedded exfiltration or telemetry concern in the reviewed scope. And `to_toolkit()` prints an **affiliate upsell** linking FinanceToolkit/FMP, which is a **disclosure observation about a commercial relationship**, not a licence term |
| **What is NOT determined** | Whether AHOS may vendor a snapshot internally. Whether AHOS may mirror it. Whether AHOS may serve any part of it, publicly or to authenticated users. Whether **derived** content (a transformed subset, a fixture built from real rows, a report quoting rows) is redistribution. Whether the affiliate relationship implies any obligation on a downstream user |
| **The sharpest open question for this package specifically** | **Do the fixtures in document 27 constitute redistribution?** FIX-01, FIX-02, FIX-03, FIX-05 and FIX-06 embed **real rows** from the corpus as literal test data inside the AHOS repository. FIX-04 embeds **real ISIN values**. Documents 20 and 27 already mitigate this — CUSIP values excluded entirely, FIGI values replaced by a boolean — but **mitigation is not clearance**, and whether the residue is redistribution is a legal question |
| **ARGUMENT — NOT A FINDING** | That a handful of rows used as adversarial test input is de minimis and not a redistribution. **Recorded; not endorsed** |
| **Review questions for counsel** | **(a)** Does MIT reach the data? **(e)** Do CUSIP/FIGI values require a licence to redistribute or serve? Plus: does embedding a small number of real rows in a private test fixture constitute extraction, re-utilization or redistribution? Would **synthetic** fixtures resolve the question entirely? |
| **Agent E's preferred technical answer, offered to make the legal question disappear** | **Use synthetic fixtures.** Every identity property that FIX-01…FIX-06 tests — namespace collision, inverted corroboration, multi-entity bare ticker, identifier fan-out, placeholder name with imputed classification, NA-shaped key — is a **structural** property that can be expressed with invented symbols, invented names and ISIN-shaped strings carrying check digits computed from the published specification. **A fully synthetic fixture set requires no dataset licence, no upstream licence, no database-right analysis and no identifier-value licence.** Agent E recommends Agent B request that form if the fixtures are ever authorized |
| **Blocking effect** | **BLOCKS** committing fixtures containing real corpus rows or real identifier values. **BLOCKS** all vendoring, mirroring and serving. **Does not block** internal analysis, and **would not block** a fully synthetic fixture set |
| **Status** | **LEGAL REVIEW REQUIRED** |

---

## 29.10 The six questions for counsel, consolidated

Carried from document 19 §19.5 row 10, now mapped to layers so that each can be answered
independently.

| # | Question | Layer | Blocks what |
|---|---|---|---|
| **(a)** | Does the root MIT licence cover `database/` + `compression/`? | LPR-04, LPR-09 | Vendoring, mirroring, fixtures from real rows |
| **(b)** | Who owns the dataset — author, contributors, or upstream? | LPR-04, LPR-05 | Any use requiring a grant |
| **(c)** | Does the unlicensed upstream create downstream exposure for a commercial user? | LPR-05 | Commercial use of equity data |
| **(d)** | Does an EU *sui generis* database right subsist, and is it licensed? | LPR-07, LPR-08 | Extraction of ≈4.85 GB / 305,495 rows |
| **(e)** | Do CUSIP/FIGI values require a licence to redistribute or serve publicly? | LPR-06, LPR-09 | Committing or serving identifier values |
| **(f)** | Is the Yahoo-implied provenance of `summary` prose (protectable expression, not fact) a copyright issue? | LPR-04, LPR-05 | Reuse of profile prose |

**Plus one question this pass added:**

| # | Question | Layer | Blocks what |
|---|---|---|---|
| **(g)** | Does importing `python-stdnum` (LGPL-2.1+) create any obligation for AHOS, and is a **test-only** dependency distinguishable? | LPR-02 | Any reuse path that copies the validator or adds the dependency |

---

## 29.11 Queue summary

| Queue ID | Layer | Verified? | Concluded? | Blocking effect | Status |
|---|---|---|---|---|---|
| **LPR-01** | Source-code licence | **YES** — 4 ways | **NO** | None for internal research | **LEGAL REVIEW REQUIRED** |
| **LPR-02** | Dependency licence | **YES** — LGPL-2.1+ confirmed | **NO** | Blocks copying the validator / adding `python-stdnum` | **LEGAL REVIEW REQUIRED** |
| **LPR-03** | Algorithm / spec provenance | **YES** — published specs | **NO** | Blocks conformance claims | **LEGAL REVIEW REQUIRED** |
| **LPR-04** | Dataset licence | **YES** — absence verified | **NO** | Blocks vendoring, mirroring, serving | **LEGAL REVIEW REQUIRED** — highest priority |
| **LPR-05** | Upstream provenance | **YES** (`license=None`) / **NO** (bulk origin) | **NO** | Blocks redistribution and origin claims | **LEGAL REVIEW REQUIRED** |
| **LPR-06** | Trademark adjacency | **YES** — marks identified | **NO** | Blocks committing/serving CUSIP/FIGI values | **LEGAL REVIEW REQUIRED** |
| **LPR-07** | Database rights | **YES** — indicators present | **NO** | Blocks extraction of the corpus | **LEGAL REVIEW REQUIRED** |
| **LPR-08** | Jurisdiction | **YES** — parties located | **NO** | Blocks single-jurisdiction assumption | **LEGAL REVIEW REQUIRED** |
| **LPR-09** | Redistribution | **YES** (code) / **NO** (data) | **NO** | Blocks fixtures from real rows; all vendoring | **LEGAL REVIEW REQUIRED** |

**Registered: 9 layers. Concluded: 0. All nine: `LEGAL REVIEW REQUIRED`.**

## 29.12 Explicit non-claims

This document does **not**:

- provide legal advice, a legal opinion, or a legal conclusion of any kind;
- assert that any use of this corpus is lawful, or unlawful;
- assert that any right subsists, or does not subsist;
- assess the likelihood or magnitude of any legal risk;
- clear any item for use;
- treat the presence of a mitigating **ARGUMENT** as reducing any review requirement;
- characterize any party's conduct — no negligence, bad faith or infringement is alleged against the
  author, the contributors, the upstream maintainer, MSCI, S&P, the ABA, Bloomberg, SWIFT or ISO;
- resolve **U-04** (bulk provenance), **U-05** (`JeroenBouma` account history — re-verified as
  **HTTP 404**, user id 46189588 with 0 public repos, distinct from the author's working account
  `JerBouma`, id 46355364 with 15 public repos), **U-06** (data ownership), **U-07** (maintainer
  intent) or **U-19** (why the Identifier Validation workflow was never merged).

**Technical verdict and legal review are kept separate throughout this package.** The technical
rejection of FinanceDatabase for crypto use (document 30) rests on **schema and contract evidence**
— `0 of 14` required identity fields, `0 of 16` capabilities, the absence of `SOL`, and the
`TypeError` / `AttributeError` execution proofs — and would be **unchanged even if every item in this
queue were cleared**. Conversely, no item in this queue is resolved by the technical verdict.

**No AHOS file was created or modified by this document. No secret was stored. No server was
started. The 72-hour soak was not disturbed. No package was installed into the AHOS environment.**
