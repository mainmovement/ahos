# 15 — AGI / ACI Research Value

**Phase 15.** The tasking asks whether FinanceDatabase has value for AGI/ACI research, and
specifically whether it is useful for benchmarking entity resolution, multi-source reconciliation,
data-quality reasoning, uncertainty representation, provenance tracking, or tool-use evaluation.

**Method note.** This section evaluates the artifact against those research questions using the
evidence established in §01–§14. It does **not** evaluate FinanceDatabase as an intelligent
system, because it is not one.

---

## 15.1 What FinanceDatabase is, categorically

| Claim | Assessment |
|---|---|
| Is it an AGI system? | **NO.** 1,866 lines of pandas filtering plus 145 MB of CSV. No learning, no inference, no planning, no model |
| Is it an ACI (agentic computer interface) component? | **NO.** It exposes no tool interface, no capability declaration, no status/error contract, no affordance metadata |
| Does it contain AI? | **NO.** Zero ML imports in the shipped package (the complete import list is `io.BytesIO`, `pathlib.Path`, `typing.Any`, `numpy`, `pandas`, `requests` + one lazy `financetoolkit` import). No `scikit-learn`, no torch, no embeddings |
| Does it *use* AI in its pipeline? | **NO.** The classification job is inline pandas with a `mode()` imputation and a manual-curation disclaimer (CONTRIBUTING:129). No model is invoked |
| Is it autonomous? | **Partially** — three GitHub Actions jobs run on a schedule and push commits to `main` without human review. That automation is a *pipeline*, not agency |
| Does it make decisions? | **NO.** It returns rows. Every decision is the caller's |

**Categorical verdict: FinanceDatabase is a static reference catalogue with a thin query API and an
automated partial-update pipeline.** Any AGI/ACI value it has is *as a research artifact about
data*, not as a component of an intelligent system.

## 15.2 Where it genuinely has research value

This is the honest positive case, and it is real.

### V-1 · A published, real-world, *failing* entity-resolution corpus — **HIGH VALUE**

Most entity-resolution benchmarks are synthetic or cleaned. FinanceDatabase is neither. It is a
**live, maintained, 9,116-star production dataset whose own invariant tests fail on `main`**.

Reusable failure cases, all measured in this investigation:

| Case | Value as a test fixture |
|---|---|
| `CHAD` present in both `equities` (DeFi Development Corp. preferred stock) and `etfs` (Direxion China A Bear 1X) | A **cross-schema blocking failure** — the same key denotes unrelated instruments across asset classes. Directly tests whether a resolver blocks on symbol alone |
| `BRK-A`/`BRK/A` (+ `BRK-B`/`BRK/B`, `BRKA.VI`) — 4 rows, 2 share classes, **contradictory `exchange`**, `isin` empty on all | A **duplicate-detection + conflict-state** test: same entity, different symbol conventions, conflicting attributes, no identifier to arbitrate |
| `META` = Metadium (crypto) vs Meta Platforms (equity); `GO` = GoChain vs Grocery Outlet — **86 of 351** crypto tickers collide with equity tickers | A **cross-domain homograph** corpus at scale, with real names on both sides |
| `COMP1` = CompoundCoin, **not** Compound; `SOL1` = Solana; `BTC2`, 26 Yahoo-suffixed tickers | A **suffix-collision trap** corpus: mechanically disambiguated symbols that look like the famous asset and are not |
| `MMM` ×18 listings, `AIR` ×17, `HAL` ×17, `SAP` ×16 | A **one-to-many entity→listing** expansion test |
| ISIN `FR0013269123` (Rubis) → **57** distinct symbols | An extreme fan-out case for identifier-based grouping |
| 129 rows with `name == 'two'` across `.SZ`, `.KQ`, `.L`, `.IL`, `.BE` venues, all `country='United States'` | A **placeholder-corruption + wrong-attribute** case — a resolver that trusts `name` fails, and one that trusts `country` fails |
| `only_primary_listing=True` drops **87.6%** of Chinese listings including the primary `000002.SZ`, while **retaining** the `BRK-A`/`BRK/A` duplicates | A beautiful **heuristic-that-is-wrong-in-both-directions** case: false negatives *and* false positives from one rule |

**Why this matters for AHOS specifically:** AHOS's `architecture/identity/resolution.py` and
`IdentityState` enum (`VERIFIED / CONFLICT / UNRESOLVED / INVALID / STALE / UNSUPPORTED`) must make
exactly these judgements on adversarial crypto data. FinanceDatabase supplies **free, real,
published, citable** instances of every failure class — with a git SHA, so the fixture is
reproducible forever. That is a legitimately useful adversarial test corpus, and it is the single
strongest research value identified.

### V-2 · A concrete case study in **uncertainty representation by absence** — **HIGH VALUE**

AHOS's founding contract (`architecture/providers/contracts.py:6`) is *"Strict UNKNOWN
representation: Missing or uncollected data is NEVER guessed"*, implemented as
`UNKNOWN_VALUE = None`, `unknown_fields: list[str]`, and `confidence_level ∈ {HIGH, MED, LOW}`.

FinanceDatabase is the **structural opposite**: it has *no* representation of uncertainty at all.
Empty cell, absent column, unpopulated identifier, imputed classification, fail-open query result
and genuinely-unknown value are all **the same thing** — a NaN, or nothing.

That makes it an excellent **negative control** and a teaching artifact:

- 73% of equity `isin` values are absent, with no field distinguishing "not looked up", "does not
  exist", "delisted before assignment" and "upstream feed didn't provide it".
- New tickers get `sector`/`industry_group` from `.mode()[0]` — a **statistical imputation
  indistinguishable in the data from a curated classification** (`database_update.yml:87,113`).
- `search()` on a mistyped column returns **all 112,690 rows** rather than an error — a
  fail-open that presents total ignorance as a complete answer.

A researcher building or evaluating an uncertainty-aware system can use this dataset to test
whether their system **detects** unrepresented uncertainty, which is a harder and more valuable
property than handling declared uncertainty.

### V-3 · A provenance-tracking **anti-pattern** reference — **MEDIUM–HIGH VALUE**

| Provenance property | AHOS `IdentitySource` / `NormalizedTokenCandidate` | FinanceDatabase |
|---|---|---|
| `provider` / `source_provider` | Required | **Absent** |
| `retrieved_ts` | Required | **Absent** |
| `source_ts` | Present | **Absent** |
| `raw_payload_sha256` | Required | **Absent** |
| `kind` (market/onchain/explorer) | Present | **Absent** |
| Dataset version | — | **Absent** (data pinned to mutable `main`) |
| Per-record ingest date | — | **Absent** |

Verified by a column-name scan across all seven schemas for
`date|time|updated|asof|timestamp|snapshot|version|source|provider|retrieved` → **zero matches**.

This is a clean, extreme, *real* example of a widely-used dataset with **no provenance layer
whatsoever**. For research on data lineage, reproducibility, or "can an agent establish where a
fact came from", it is a useful worst case — and the fact that it is otherwise well-engineered
(good validator, good compression benchmark, deliberate security choice) makes the contrast
instructive rather than trivial.

### V-4 · A tool-use / function-calling evaluation surface — **MEDIUM VALUE, with a trap**

The API has exactly two query entry points with **opposite failure semantics**:

| | `select(**kwargs)` | `search(**kwargs)` |
|---|---|---|
| Matching | exact / case-insensitive | unescaped **regex** |
| Column validated? | **Yes** — against a precomputed `categories` sidecar | **No** |
| Unknown column | `ValueError` (fail-closed) | returns **all rows** (fail-open) |
| Unknown value | `ValueError` listing valid options | empty result |
| `exclude_delisted` default applied? | **Yes** | **No** (+473 rows delta measured) |
| Invalid regex | n/a | uncaught `re.error` |
| Type coercion | strict | `case_sensitive="true"` → `False`; `1` → `True` |
| Docstring accuracy | accurate | **The documented example `search(name='TSLA')`-style usage does not do what a reader expects** |

An LLM agent asked to "find all technology companies in the Netherlands" must discover which of
two similar-looking methods to use, that one of them silently returns everything on a typo, that
`Cryptos.select(cryptocurrency="SOL")` raises while `SOL1` returns 10 rows, and that
`only_primary_listing` is a trap. **This is a genuinely good tool-use discrimination test** — and
the trap-richness is unintentional, which is what makes it realistic.

A complete **43-entry query truth table** with `op / input / expected / actual / evidence` is
included at `evidence/query_truth_table.json` and can be reused directly as an evaluation suite.

### V-5 · A multi-source reconciliation case study — **MEDIUM VALUE**

The pipeline reconciles three upstream feeds (NASDAQ, NYSE, AMEX JSON files from
`rreichel3/US-Stock-Symbols`) plus a hand-curated existing corpus, via `pd.concat` **without
`keys=`** and a global `drop_duplicates(keep='first')` whose survivor depends on **glob filename
order** (`database_update.yml:185,260`). Measured consequences: a 29% row reduction versus the
count still advertised on the official website; contradictory venue assignment
(`BRK-A`→`NYQ` vs `BRK/A`→`ASE`); 8,186 rows whose `market` has **zero variance** because it was
assigned wholesale.

Useful for research on **lossy reconciliation**: what happens when a merge strategy is
position-dependent, unlogged and unversioned. Note the limitation — the *inputs* to the
reconciliation are not preserved, so the case is only partially reproducible (U-13).

### V-6 · A data-quality-governance case study — **MEDIUM VALUE**

An unusually complete natural experiment in **what happens when validation exists but is not
gating**:

- The identifier validator is genuinely excellent: **2 invalid values in 249,085** (99.9992%
  valid), with a principled `actionable` vs `review-only` split.
- Yet `Check-GICS-Categorisation` has **failed on three consecutive update runs**
  (2026-09-06, 09-11, 09-13) and is placed **last**, so it is **non-blocking**.
- Bot data commits have **0 workflow runs and 0 check-runs** — the invariant tests never see the
  data they exist to protect.
- The project's own test suite reports `1 failed, 85 passed` on `main`, and CI **deselects** the
  failing identifier test into a separate job so the main job stays green.

This is a rare, documented, real-world instance of **green-CI-with-failing-invariants**. For
research on automated data governance, CI as an epistemic instrument, or "what does a passing
build actually attest to", it is materially more informative than a synthetic example.

### V-7 · A reproducibility failure case — **MEDIUM VALUE**

`DATA_REPO` hardcodes the **`main`** branch (`helpers.py:12-14`). Combined with an unpinned
`base_url`, a bot that commits weekly, zero artifact checksums and a release cadence decoupled
from the data cadence, the result is that **no two runs of the same library version are guaranteed
to see the same data**. Demonstrated concretely by S-13: release 2.4.0's loader drops the ticker
`NA` on today's data, while `main`'s loader does not.

A clean case study for research on **scientific reproducibility of data-dependent software**.

## 15.3 Where it has **no** research value

| Question | Verdict |
|---|---|
| Is it a benchmark for *financial prediction*? | **NO.** No prices, no returns, no time series, no timestamps. Nothing to predict from or against |
| Is it a benchmark for *market efficiency* or alpha research? | **NO.** Same reason, plus structural look-ahead bias: the catalogue is a current snapshot, so backtesting against it uses today's membership for yesterday's universe (§7) |
| Is it a benchmark for *crypto* anything? | **NO.** §8: 16 of 16 required capabilities absent. `SOL` is not in the table. No chain, no address, no price, no liquidity |
| Does it benchmark *retrieval-augmented generation*? | **Weakly.** The `summary` field (100,463 populated equity rows) is prose, but it is unattributed, undated and of undocumented provenance — a poor RAG corpus because grounding cannot be established |
| Is it a *reasoning* benchmark? | **NO.** No questions, no labels, no gold answers. The 43-entry truth table produced by this investigation is a *derived* artifact, not a property of the dataset |
| Does it evaluate *agent planning* or multi-step tool use? | **Only as V-4** — a discrimination test between two methods, not a planning benchmark |
| Is it a *ground-truth* source for anything? | **NO.** It has no truth claims, no validation against an authority, and two of its own invariants fail on `main` |
| Does it advance AGI capability? | **NO.** It is a dataset and a filter API |
| Does it advance ACI design? | **Only negatively** — as an example of an interface with no capability declaration, no status contract and no uncertainty representation |

## 15.4 Comparison with what AHOS already has

| Capability | FinanceDatabase | AHOS existing stack |
|---|---|---|
| Live token discovery | ✗ | ✓ DexScreener, GeckoTerminal, Pump.fun |
| Chain + contract address | ✗ | ✓ required fields of `NormalizedTokenCandidate` |
| Price / volume / liquidity / FDV / mcap | ✗ | ✓ 16 `MarketMetrics` fields |
| Honeypot / tax / mint / freeze / renounce | ✗ | ✓ 15 `SecuritySignals` fields via GoPlus, RugCheck |
| Holder concentration, deployer history | ✗ | ✓ |
| Multi-provider corroboration | ✗ (single static file) | ✓ `ProviderRouter` with 8 adapters and dedupe on `(chain, address)` |
| Provenance + SHA-256 | ✗ | ✓ `raw_payload_sha256`, `IdentitySource` |
| Uncertainty representation | ✗ | ✓ `UNKNOWN_VALUE`, `unknown_fields`, `confidence_level` |
| Fail-closed error envelopes | Partial | ✓ `ProviderResponse.status ∈ {OK, DOWN, RATE_LIMITED, ERROR}` |
| TradFi security catalogue | **✓ — the one thing AHOS lacks** | ✗ |
| Delisted-instrument history | **✓ (US equities only)** | ✗ |
| Identifier check-digit validation | **✓ (technique)** | ✗ |

**AHOS's existing stack dominates FinanceDatabase on every dimension that matters for its mission,
and FinanceDatabase dominates AHOS on exactly one dimension (a TradFi reference catalogue) that
AHOS does not currently need.** That asymmetry is the whole of the integration argument, and it
points to **C. RESEARCH-ONLY VALUE**.

## 15.5 Recommended research uses (all offline, all non-production)

| # | Use | Why it is safe | Value |
|---|---|---|---|
| R-1 | **Adversarial fixture corpus** for `architecture/identity/resolution.py`: encode V-1's eight cases as pytest parametrizations with expected `IdentityState` outcomes | Read-only fixtures; no runtime path; no dependency installed | **HIGH** — tests the resolver against real published failures rather than synthetic ones |
| R-2 | **Negative control** for AHOS's `UNKNOWN` discipline: assert that AHOS's ingest of a FinanceDatabase-shaped input produces explicit `UNKNOWN` for every absent field, never a default | Pure unit test | **HIGH** — directly exercises the founding contract |
| R-3 | **Tool-use evaluation suite** from `evidence/query_truth_table.json` (43 entries): can a model choose `select` vs `search` correctly and predict the failure mode? | Standalone eval, no AHOS coupling | **MEDIUM** |
| R-4 | **Provenance-absence case study** for documentation: cite as the counter-example in AHOS's data-governance docs | Documentation only | **MEDIUM** |
| R-5 | **CI-governance case study**: cite the green-CI-with-failing-invariants pattern when designing AHOS's own ingest gates | Documentation only | **MEDIUM** |
| R-6 | **Technique extraction** (T-1…T-10 of §14.8): reimplement the three check-digit algorithms and the `actionable`/`review-only` repair split | Licence-clean public mathematics; no code copied | **HIGH** |
| R-7 | **Reproducibility study**: diff two pinned commits to quantify dataset drift over time | Requires only two archived snapshots | **LOW–MEDIUM** |

**All seven are research-only. None requires installing the package, calling its network path, or
touching any protected AHOS surface.** Each is consistent with boundary rules B-1…B-18 (§14.5).

## 15.6 Verdict

| Dimension | Rating |
|---|---|
| Value as an AGI/ACI **component** | **NONE** — it is not an intelligent system and has no agent interface |
| Value as an AGI/ACI **research artifact** | **MODERATE–HIGH**, concentrated in V-1 (real failing entity-resolution corpus), V-2 (uncertainty-by-absence), V-6 (non-gating validation) |
| Value as a **benchmark** | **LOW** as published; **MEDIUM** if AHOS derives labelled fixtures from it (R-1, R-3) — and the labels would be AHOS's work, not the dataset's |
| Value as a **technique source** | **HIGH** and licence-clean (§14.8) |
| Value for AHOS's **crypto mission** | **NONE** |
| Value for a **hypothetical future TradFi lane** | **MODERATE**, contingent on the §12 legal review |

**Overall: research-only value.** The most defensible sentence about this artifact is:

> FinanceDatabase is not a capability AHOS lacks. It is a **well-documented, publicly reproducible
> specimen of how a real, popular, actively-maintained financial dataset fails** — and that
> specimen is worth more to AHOS as a test corpus and as a set of ten reimplementable techniques
> than it is worth as a data source.
