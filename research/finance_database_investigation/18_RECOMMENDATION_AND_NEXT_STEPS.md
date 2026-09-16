# 18 — Recommendation & Next Steps

**Phase 18.** The final judgment, the decision matrix that produced it, and what — if anything —
should happen next.

---

## 18.1 FINAL JUDGMENT

> # **C. RESEARCH-ONLY VALUE**
>
> ### …plus **E. REJECTED** for the cryptocurrency use case that motivated this investigation.
>
> A conditional path to **B. RECOMMENDED WITH STRICT BOUNDARIES** exists **only** for a future
> **non-crypto** reference-catalogue lane, and **only** under separate explicit authorization
> **and** a completed legal review. That lane does not exist today.

**One-sentence version.** FinanceDatabase is a well-engineered, MIT-licensed, genuinely useful
*static TradFi reference catalogue* whose crypto table is a stale ~2020 snapshot with no chain, no
address, no price and no freshness — so it cannot serve AHOS's mission, cannot be integrated as a
provider, and is worth keeping only as a research artifact, an adversarial test corpus, and a
source of ten licence-clean techniques.

---

## 18.2 Decision matrix

Scoring: **0** = disqualifying · **1** = poor · **2** = marginal · **3** = adequate · **4** = good ·
**5** = excellent. Weights reflect AHOS's stated mission (crypto opportunity detection on Solana
and adjacent chains, $0/month, Iran-resilient, offline-auditable, strict `UNKNOWN`, fail-closed,
never a decision authority).

| # | Criterion | Weight | Score | Weighted | Evidence |
|---|---|---:|---:|---:|---|
| 1 | **Cryptocurrency capability** (chain, address, price, volume, liquidity, mcap, security signals, freshness) | **20%** | **0** | **0.00** | EV-CR-01…EV-CR-12: 7 columns only; 14 required fields absent by existence check; `SOL` not in the table; 51 of 73 probed tokens absent; **16 of 16** tasking capabilities = **NO** |
| 2 | **Freshness / staleness** | **12%** | **0** | **0.00** | EV-SCH-08: **zero** timestamp/provenance columns in all seven schemas; crypto table has **no update job** (EV-CR-10); non-US data has **no automated maintenance** (README:467) |
| 3 | **Data integrity & quality** | **10%** | **3** | **0.30** | **Strong:** EV-DQ-01 validator finds **2 invalid of 249,085** (99.9992%); deliberate delisted retention (10,404 rows). **Weak:** EV-SCH-02 emptiness up to 78%; EV-SCH-09 placeholder corruption; EV-DQ-07 `ILA`×560 |
| 4 | **Identity / entity resolution fit** | **10%** | **1** | **0.10** | EV-ID-01…EV-ID-11: no issuer entity; symbol collisions across asset classes (`CHAD`, project test **fails on main**); `BRK-A`/`BRK/A` with contradictory venues; 86/351 crypto↔equity collisions; irreconcilable with `IdentityResolution` |
| 5 | **Query API safety** (fail-closed, `UNKNOWN` discipline) | **8%** | **1** | **0.08** | EV-QE-02 `select()` is excellent and fail-closed. EV-QE-03…EV-QE-05 `search()` is **fail-open**: a mistyped column returns **all 112,690 rows**; the docstring's own example misleads. No `UNKNOWN` concept anywhere |
| 6 | **Reproducibility** | **8%** | **1** | **0.08** | EV-ARCH-01 `DATA_REPO` hardcodes mutable **`main`**; no artifact checksums (EV-SEC-05); release and data versioned independently; EV-DQ-05 the shipped 2.4.0 loader loses ticker `NA` on today's data |
| 7 | **AHOS constraint fit** ($0, offline, sanctions/filtering-resilient, no paid SDK, stdlib-urllib floor) | **8%** | **1** | **0.08** | §14.4: **four hard FAILs** — external API dependency, sanctions/filtering, offline-auditability of data, stdlib-urllib floor; plus **AT RISK** on `pandas>=2.1.0` and identity |
| 8 | **Supply-chain & security posture** | **6%** | **2** | **0.12** | **Good:** EV-SEC-01 **zero** dangerous calls in 1,866 lines; EV-SEC-02 exactly two GETs; EV-SEC-04 pickle deliberately rejected for security. **Bad:** EV-SEC-07 third-party mutable-tag action + push-capable PAT + inline Python; EV-SEC-05 no integrity verification; EV-SEC-09 unlicensed upstream |
| 9 | **Licensing clarity** | **6%** | **2** | **0.12** | EV-LEG-01/02 **code = MIT, clear and permissive**. EV-LEG-03/04/05/07 **dataset = not separately licensed, provenance undocumented**; EV-SEC-09 upstream `license=None`; CUSIP/FIGI/GICS trademark adjacency ⇒ **LEGAL REVIEW REQUIRED** |
| 10 | **Maintenance & project health** | **5%** | **3** | **0.15** | **Good:** 9,116 stars, 941 forks, 35 releases, active Dependabot, 452 CI runs, weekly automation, responsive issue tracker. **Bad:** EV-PIPE-08 GICS check failing 3 consecutive runs and non-blocking; EV-PIPE-09 data commits ungated; EV-ID-04 a failing invariant on `main` |
| 11 | **Dependency footprint** | **4%** | **1** | **0.04** | EV-EXT-01 hard dep on `financetoolkit` but lazy import; EV-EXT-02 `numpy`/`pandas`/`requests` **undeclared**; EV-EXT-05/08 → `yfinance` unpinned + `scikit-learn` + `pandas>=3.0`; EV-EXT-06 CI-tested config ≠ installed config |
| 12 | **Performance & scalability** | **3%** | **2** | **0.06** | EV-PERF-01…EV-PERF-06: adequate for a static catalogue (4.12 s load, 214 MB deep, 273–341 ms `select`). No indexing, no cache, no concurrency control, no serialization (EV-PERF-07). Cost scales with filter count |
| 13 | **AGI/ACI research value** | **Weight not applied — see note** | **4** | — | §15: V-1 real failing entity-resolution corpus, V-2 uncertainty-by-absence, V-6 non-gating validation, V-4 tool-use discrimination surface, plus 43-entry truth table |
| | **TOTAL (weighted criteria 1–12)** | **100%** | | **1.13 / 5.00** | |

> **Note on criterion 13.** Research value is scored but **not weighted into the total**, because it
> is a *different* question from integration suitability. Including it would let a dataset that
> cannot perform the mission offset that failure by being interesting — which is exactly the kind
> of category error this investigation exists to prevent. It is reported separately and it is the
> reason the judgment is **C** rather than **D** or **E** overall.

### Mapping score → judgment

| Band | Judgment |
|---|---|
| 4.00 – 5.00 | **A. STRONGLY RECOMMENDED** |
| 3.00 – 3.99 | **B. RECOMMENDED WITH STRICT BOUNDARIES** |
| 1.50 – 2.99 | **C. RESEARCH-ONLY VALUE** |
| 0.75 – 1.49 | **D. NOT CURRENTLY JUSTIFIED** |
| 0.00 – 0.74 | **E. REJECTED** |

**Overall weighted score 1.13 ⇒ band D.** But a single aggregate is the wrong instrument here, and
the tasking's evidence doctrine (`Evidence ≠ Score ≠ Decision`) requires saying why the final
judgment is **C, not D**:

- **Criteria 1 and 2 — the two highest-weighted, mission-defining criteria — both score 0.** That
  is not a "weak integration"; that is *no capability at all* for the stated use case. On the
  crypto question in isolation the score is **0.00 ⇒ E. REJECTED**, and that is unambiguous.
- **Criterion 13 (unweighted) scores 4.** The research value is real, specific, and identified
  with measured instances rather than hand-waving (§15.2, §14.8).
- **D. NOT CURRENTLY JUSTIFIED** would understate the research value. **B** would overstate the
  capability. **C. RESEARCH-ONLY VALUE** is the only label that is true on both axes
  simultaneously.

So the judgment is **split by use case, deliberately**:

| Use case | Judgment | Confidence |
|---|---|---|
| **Crypto opportunity detection / identity / enrichment / risk** — AHOS's actual mission | **E. REJECTED** | **HIGH** — 16/16 required capabilities verified absent |
| **Runtime provider adapter in `ProviderRouter`** | **E. REJECTED** | **HIGH** — structurally impossible (§14.2): `chain` and `address` are required fields with no source |
| **Install as a package into the AHOS environment** | **E. REJECTED** | **HIGH** — four hard constraint FAILs (§14.4) |
| **Live market/on-chain data source of any kind** | **E. REJECTED** | **HIGH** — no prices, no timestamps, no update job for crypto |
| **Research artifact, adversarial test corpus, technique source** | **C. RESEARCH-ONLY VALUE** | **HIGH** — §15.2, §14.8, §16 |
| **Vendored TradFi reference catalogue for a *future* non-crypto lane** | **D → conditionally B** | **MEDIUM** — requires B-1…B-18 **and** the §12 legal review **and** separate authorization |
| **Overall package judgment** | **C. RESEARCH-ONLY VALUE** | **HIGH** |

## 18.3 What was verified vs what is assumed

The tasking forbids treating FinanceDatabase as a live market data provider, on-chain data
provider, crypto opportunity detector, security analysis engine, trading signal engine, risk
engine, decision authority, paper-trading engine, or AGI system **without evidence**. The evidence
position on each:

| Role | Evidence | Verdict |
|---|---|---|
| Live market data provider | **No** price, volume, liquidity or timestamp field exists (EV-CR-02, EV-SCH-08). No API is called; two static file GETs only (EV-SEC-02) | **REFUTED — it is not one** |
| On-chain data provider | **No** chain, address, contract, decimals or block field exists (EV-CR-02) | **REFUTED** |
| Crypto opportunity detector | 16/16 required capabilities absent (EV-CR-12); `SOL` not in the table (EV-QE-10) | **REFUTED** |
| Security analysis engine | Zero security-related columns; no scoring, no model, no ML import (EV-SEC-01) | **REFUTED** |
| Trading signal engine | No time series, no signals, no returns | **REFUTED** |
| Risk engine | No risk fields, no volatility, no exposure data | **REFUTED** |
| Decision authority | Returns rows. The library never imports `logging`; all diagnostics are `print()` | **REFUTED** |
| Paper-trading engine | No execution, order, position or fill concept | **REFUTED** |
| AGI / ACI system | 1,866 lines of pandas filtering; no learning, inference, planning or model (§15.1) | **REFUTED** |
| Static TradFi reference catalogue | 304,495 rows across 7 schemas, measured (EV-SCH-01); identifiers 99.9992% valid where present (EV-DQ-01) | **CONFIRMED — this is what it is** |
| Research artifact with adversarial value | 18 of 20 failure scenarios have live observed instances (§16.14); 43-entry query truth table archived | **CONFIRMED** |

**Nothing in this package is assumed where it could be measured.** Where a fact could not be
verified it is written **UNVERIFIED** or **UNKNOWN** and registered in §17. Where an inference was
made it is labelled **INFERENCE** — there are exactly five (§16.17).

## 18.4 Recommended next steps

### Tier 0 — Do now (no authorization needed, no risk, no code changes)

| # | Action | Effort | Value |
|---|---|---|---|
| **0.1** | **Close this investigation. Take no integration action.** The deliverable is complete at `research/finance_database_investigation/` | — | Prevents an uninformed integration |
| **0.2** | Add one entry to `docs/OSS_HARVEST_LOG.md` recording: FinanceDatabase evaluated 2026-09-15 at commit `a174c97d3b`; judgment **C** (crypto **E**); **no code copied**; ten techniques identified for future reimplementation; dataset licence **LEGAL REVIEW REQUIRED** | 10 min | Satisfies AHOS's own standing rule; creates the audit trail |
| **0.3** | Record the verdict in `docs/DATA_SOURCE_MATRIX.md` as **EVALUATED — REJECTED for crypto; RESEARCH-ONLY otherwise**, so the question is not re-litigated | 10 min | Prevents duplicate work |
| **0.4** | Archive `evidence/` alongside this report and never delete it — the pinned commit + SHA-256s + 43-entry truth table are the reproducibility guarantee | 0 min (already done) | Reproducibility |

### Tier 1 — Recommended, cheap, high value (research-only; requires no production change)

| # | Action | Effort | Value |
|---|---|---|---|
| **1.1** | **Reimplement the three check-digit validators** (ISO 6166 ISIN, CUSIP-9, OpenFIGI) from the **published standards**, not from this repo's code — plus the `actionable` vs `review-only` repair split (T-1…T-4) | ~2 h | Licence-clean, dependency-free, immediately useful for any AHOS identifier handling. **No legal exposure**: the algorithms are public mathematics |
| **1.2** | **Adopt the fail-closed query discipline** (T-10): validated option lists, `ValueError` on unknown column/value — and explicitly avoid FinanceDatabase's mistake of shipping a second, fail-open API beside it | Design only | Directly improves any AHOS query surface |
| **1.3** | **Adopt `mtime=0` gzip and per-file SHA-256 manifests** (T-6) for every AHOS-generated artifact | ~1 h | Makes snapshots diffable and pinnable — the control §14.6 depends on |
| **1.4** | **Build the adversarial identity fixture set** (R-1): encode `CHAD`, `BRK-A`/`BRK/A`, `META`/`GO` collisions, `COMP1`, `MMM`×18, ISIN `FR0013269123`→57, the `two`×129 rows and the `only_primary_listing` double failure as parametrized pytest cases with expected `IdentityState` outcomes | ~4 h | **The single highest-value output of this investigation.** Free, real, published, permanently reproducible failure cases for AHOS's own resolver |
| **1.5** | **Reuse the 43-entry query truth table** (R-3) as a tool-use discrimination eval | ~1 h | Already built |
| **1.6** | **Run AHOS's `UNKNOWN` discipline as a negative control** (R-2): assert that ingesting FinanceDatabase-shaped input yields explicit `UNKNOWN` for every absent field, never a default | ~2 h | Exercises AHOS's founding contract against a real worst case |

**Tier 1 totals ≈ 10 hours, installs nothing, modifies no production path, and captures most of the
value this dataset has to offer.**

### Tier 2 — Only if a non-crypto TradFi lane is ever authorized

| # | Action | Precondition |
|---|---|---|
| **2.1** | **Complete the legal review** (§12): dataset licence (LEG-01), upstream `license=None` provenance (LEG-02), bulk-import provenance (LEG-03), EU *sui generis* right (§12.4), CUSIP/FIGI/GICS trademark adjacency (§12.3) | **Blocking.** Ask maintainer questions 1–3 from §17.3 first |
| **2.2** | Close **U-04, U-06, U-07** (provenance and ownership) | Blocking for 2.1 |
| **2.3** | Close **U-17** on the AHOS Windows host before making any Windows claim | Blocking for any Windows deployment |
| **2.4** | Implement **§14.6 only** — vendored, hash-pinned, AHOS-parsed snapshot; never the package, never an adapter, never the network path | B-1…B-18 enforced **and tested** |
| **2.5** | Close **U-12** (which rows fail GICS) and **U-15** (identifier stability) before relying on classification or identifiers | Non-blocking but cheap |
| **2.6** | Re-run the whole assessment if the maintainer answers §17.3 questions 1–3 favourably | — |

### Tier 3 — Explicitly NOT recommended

| # | Action | Why not |
|---|---|---|
| **3.1** | ~~Register a `financedatabase` adapter in `ProviderRouter`~~ | **Structurally impossible** (§14.2). `chain` and `address` are required; the source has neither. Any implementation would fabricate or emit `None` into a dedupe key |
| **3.2** | ~~`pip install financedatabase` into the AHOS environment~~ | Four hard constraint FAILs (§14.4); drags `financetoolkit` → `yfinance` (unpinned) + `scikit-learn` + `pandas>=3.0` over AHOS's `pandas>=2.1.0` floor |
| **3.3** | ~~Use the `cryptos` table for anything~~ | **E. REJECTED.** §8: 16/16 capabilities absent. Strictly dominated by AHOS's existing 8 adapters |
| **3.4** | ~~Call `to_toolkit()` / FinanceToolkit / FMP / Yahoo~~ | Outside scope, undeclared cost, unpinned `yfinance`, affiliate-linked upsell (§9) |
| **3.5** | ~~Use `search()` in any automated path~~ | Fail-open: a typo returns all 112,690 rows (EV-QE-03). Use `select()` semantics reimplemented AHOS-side |
| **3.6** | ~~Poll `main` on a schedule as a live source~~ | Reintroduces every problem the vendored approach solves, with no integrity check (§11.7) |
| **3.7** | ~~Let any FinanceDatabase value reach scoring, security gates, or `CanonicalDecisionAuthority`~~ | **PROHIBITED** by B-1. Nothing in this report authorizes it |
| **3.8** | ~~Bridge FinanceDatabase symbols into `architecture/identity/resolution.py`~~ | The two identity models are **unreconcilable** (§5.6, §14.7). Adapter-only, one-directional, never authoritative — and even that is Tier 2, not now |

## 18.5 Conditions that would change this judgment

| Change in evidence | New judgment |
|---|---|
| Maintainer confirms the dataset is MIT-licensed **and** documents provenance **and** AHOS opens a TradFi lane | **B** for that lane only (with B-1…B-18 enforced and tested). Crypto remains **E** |
| A `chain`/`address`/price/liquidity crypto schema appears with an automated update job | Re-investigate from scratch. Current **E** is a verdict on the artifact as measured on 2026-09-15, not on the project forever |
| The `CHAD` collision and the GICS invariant are fixed **and** CI gates data commits **and** the release loader gains `keep_default_na=False` | Criterion 3 → 4, criterion 6 → 3, criterion 10 → 4; overall ≈ 1.4. **Still C** — criteria 1 and 2 remain 0 |
| `raw.githubusercontent.com` proves reachable from the AHOS Windows host (U-18) | Weakens S-14/S-15 from *measured* to *untested-under-target-network*. **Does not change the judgment** — the architectural dependency is verified from source independently |
| Evidence emerges that the dataset contains material AHOS cannot lawfully use | **E** across the board, including research use. This is the only realistic path to a worse verdict |

## 18.6 Statement of compliance with the tasking's constraints

| Constraint | Status |
|---|---|
| No AHOS production code, Lane A, Lane B, scoring, runtime, Canonical Decision Authority, security gates, identity resolution, soak config or database state modified | **SATISFIED** (EV-AHOS-09) — all AHOS-side access was read-only; all writes confined to `research/finance_database_investigation/` |
| No integration implemented | **SATISFIED** — §14 is a design document, explicitly marked NOT APPROVED / NOT IMPLEMENTED |
| No packages installed into the AHOS environment | **SATISFIED** (EV-AHOS-10) — all installation occurred in the isolated research venv `/tmp/fdb_venv` |
| FinanceDatabase not treated as a live market/on-chain provider, opportunity detector, security engine, signal engine, risk engine, decision authority, paper-trading engine or AGI system without evidence | **SATISFIED** — every such role is **REFUTED** with evidence in §18.3 |
| REALITY > DOCUMENTATION; EVIDENCE > ASSUMPTION; TEST > CLAIM | **SATISFIED** — where the website, docstrings and README disagreed with measurement, measurement won and the disagreement became a finding (EV-SRC-04, EV-QE-05) |
| UNKNOWN ≠ SAFE; STALE ≠ LIVE | **SATISFIED** — 18 unknowns registered in §17, none treated as favourable; staleness recorded as a **0** score, not a caveat |
| Prediction ≠ Fact; Simulation ≠ Execution; Documentation ≠ Proof | **SATISFIED** — no benchmark, test result or behaviour is reported that was not executed |
| Historical success ≠ Current capability | **SATISFIED** — 9,116 stars and 35 releases did not offset measured absence of crypto capability |
| Linux validation ≠ Windows validation | **SATISFIED** — no Windows claim is made; U-17 registered as open |
| If a fact cannot be verified, write UNVERIFIED | **SATISFIED** — 4 UNVERIFIED, 4 UNKNOWN, 3 NOT TESTED, 5 INFERENCE, all labelled |
| Never invent file paths, line numbers, benchmarks, test results or repository details | **SATISFIED** — §16 registers 131 evidence items with method and artifact for every substantive claim |
| No "real-time" claim without proof; no "accurate" claim without a defined validation method | **SATISFIED** — "accurate" is used only with the validator's method stated (99.9992% of 249,085 identifiers pass ISO/CUSIP/OpenFIGI checksums). "Real-time" is **never** claimed; the opposite is proven |
| Precise security language | **SATISFIED** — §11 uses *"no issue observed in reviewed scope"* throughout and states explicitly that this is **not** equivalent to *"secure"* |
| Ambiguous licence ⇒ state LEGAL REVIEW REQUIRED | **SATISFIED** — four separate LEGAL REVIEW REQUIRED verdicts in §12; no legal certainty asserted anywhere |
| Separate facts, inferences, recommendations and open questions | **SATISFIED** — §16 (facts), the five labelled INFERENCEs, §18.4 (recommendations), §17 (open questions) |
| Produce all 19 artifact files | **SATISFIED** — README + 00…18, listed below |
| Optimize for truth, reproducibility, technical depth, architectural correctness, evidence quality and explicit uncertainty — not for pleasing the user | **SATISFIED** — the answer is "no, and here is precisely why", with the crypto subsystem **REJECTED** despite the project's popularity and despite the investigation's own cost |

## 18.7 Deliverable inventory — 19 files

| File | Phase |
|---|---|
| `README.md` | Index, reproduction instructions, environment record |
| `00_EXECUTIVE_SUMMARY.md` | Executive summary and final judgment |
| `01_SOURCE_AND_REPOSITORY.md` | 1 · Repository Discovery |
| `02_ARCHITECTURE_RECONSTRUCTION.md` | 2 · Source-Code Forensics |
| `03_DATA_PIPELINE.md` | 3 · Data Pipeline Reconstruction |
| `04_SCHEMA_AUDIT.md` | 4 · Complete Schema Audit |
| `05_IDENTITY_AND_ENTITY_RESOLUTION.md` | 5 · Identity / Entity Resolution Audit |
| `06_QUERY_ENGINE_AUDIT.md` | 6 · Query Engine Audit |
| `07_DATA_QUALITY_AND_FRESHNESS.md` | 7 · Data Quality / Freshness / Trust |
| `08_CRYPTOCURRENCY_COVERAGE.md` | 8 · Cryptocurrency Subsystem Audit |
| `09_EXTERNAL_INTEGRATIONS.md` | 9 · Financial Toolkit / External Integration Audit |
| `10_PERFORMANCE_AND_SCALABILITY.md` | 10 · Performance / Scalability |
| `11_SECURITY_AND_SUPPLY_CHAIN.md` | 11 · Security / Supply-Chain Review |
| `12_LICENSE_AND_LEGAL_REVIEW.md` | 12 · Licensing / Legal Compatibility |
| `13_ADVERSARIAL_FAILURE_ANALYSIS.md` | 13 · Adversarial Failure Analysis |
| `14_AHOS_INTEGRATION_ASSESSMENT.md` | 14 · AHOS Integration Architecture (**design only, not implemented**) |
| `15_AGI_ACI_RESEARCH_VALUE.md` | 15 · AGI / ACI Research Value |
| `16_EVIDENCE_REGISTER.md` | Evidence Register (131 items) |
| `17_UNKNOWNS_AND_OPEN_QUESTIONS.md` | Unknowns (U-01…U-18) + deliberate non-tests |
| `18_RECOMMENDATION_AND_NEXT_STEPS.md` | Decision Matrix + Recommendation (this file) |

Plus `evidence/`: `ENVIRONMENT.txt`, `schema_audit.json`, `query_truth_table.json` (43 entries),
`identifier_issues.csv`, and `scripts/a1…a12*.py` (12 archived, re-runnable scripts).

## 18.8 Closing statement

The most useful thing this investigation produced is **not** a data source. It is a precise,
measured, reproducible account of the gap between what a popular financial dataset *appears* to
offer and what it *actually* contains — established by execution rather than by reading its
documentation, and recorded so that the same question does not have to be asked twice.

FinanceDatabase is good software. It is a well-maintained, honestly-documented, security-conscious
project with 9,116 stars and a real community. It is also, for AHOS's purposes, **the wrong
artifact**: it has no chain, no address, no price, no liquidity, no timestamp and no crypto update
job, and it cannot be installed without dragging an unpinned `yfinance` and a pandas major-version
bump across a $0/month, offline-auditable, sanctions-resilient floor.

> **Final judgment: C. RESEARCH-ONLY VALUE — and E. REJECTED for the cryptocurrency use case.**
>
> Take the ten techniques (§14.8). Build the adversarial fixture set (§18.4, action 1.4). Log the
> evaluation in `OSS_HARVEST_LOG.md`. Install nothing. Integrate nothing. Revisit only if a
> non-crypto lane is authorized and the legal review in §12 comes back clear.
