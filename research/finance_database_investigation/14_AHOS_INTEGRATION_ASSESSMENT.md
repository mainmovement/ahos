# 14 — AHOS Integration Architecture Assessment

**Phase 14. DESIGN DOCUMENT ONLY.**

> ## ⚠️ NOTHING DESCRIBED HERE HAS BEEN IMPLEMENTED
>
> This document contains **no code changes to AHOS**. No AHOS production file was read for
> modification, only for interface discovery. Nothing was installed into the AHOS environment.
> No Lane A, Lane B, scoring, runtime, Canonical Decision Authority, security gate, identity
> resolution, soak configuration or database state was touched.
>
> The architecture below is **proposed**, conditional on the separate authorization the tasking
> requires. Until that authorization exists, its status is: **NOT APPROVED, NOT IMPLEMENTED.**
>
> **Recommendation of this investigation: do not implement any of it** (§18, judgment
> **C. RESEARCH-ONLY VALUE**). The design is recorded so the decision is made with full
> information, and so that if a future non-crypto lane is authorized, the boundary conditions
> are already written down.

---

## 14.1 The AHOS interfaces this was assessed against

Discovered by reading (read-only) the existing contracts:

| AHOS artifact | What it requires |
|---|---|
| `architecture/providers/contracts.py` — `NormalizedTokenCandidate` | `chain: str` and `address: str` are **required positional fields**, not `None`-defaulted. Optional fields use `UNKNOWN_VALUE = None`. Carries `source_provider`, `retrieved_ts`, `raw_payload_sha256`, `confidence_level ∈ {HIGH, MED, LOW}`, `unknown_fields: list[str]`, plus nested `MarketMetrics` (16 fields) and `SecuritySignals` (15 fields) |
| `architecture/providers/contracts.py` — `BaseMarketProvider` (ABC) | Abstract: `provider_id`, `capabilities: list[str]`, `health_check() -> bool`, `fetch_candidate_tokens(chain, limit) -> ProviderResponse`, `fetch_token_metrics(chain, address) -> ProviderResponse` |
| `architecture/providers/contracts.py` — `ProviderResponse` | `provider_id`, `status ∈ {OK, DOWN, RATE_LIMITED, ERROR}`, `tokens`, `latency_ms`, `http_status`, `error_message`, `raw_payload`, `raw_sha256` |
| `architecture/providers/registry.py` — `ProviderRouter` | Eight adapters: `dexscreener`, `geckoterminal`, `goplus`, `rugcheck`, `coingecko`, `chain_explorer`, `coinmarketcap`, `pumpfun`. `discover_candidates()` uses **only** `dexscreener` + `geckoterminal`; dedupe key is `(c.chain, c.address.lower())`. The rest are *"enrichment-only"* |
| `architecture/identity/types.py` | `IdentityState ∈ {VERIFIED, CONFLICT, UNRESOLVED, INVALID, STALE, UNSUPPORTED}`; `ChainIdentity`, `TokenIdentity` (`address_canonical`, `token_id`, `checksum_ok`), `PoolIdentity`, `DexDeployment`, `IdentityResolution` with `sources`, `conflicts`, `provenance`, `policy_version`, `computed_ts` |
| `requirements.txt` | *"LAW: $0/month cost ceiling. Every package here is free, permissively licensed, and installable offline from a wheel cache. No paid SDK is ever required. Python: 3.11+"*. Floor uses **stdlib `urllib`** for *"ZERO third-party network dependency"*. `pandas>=2.1.0`, `numpy>=1.26.0`, `requests>=2.31.0` (optional collectors only), `PySocks` for Iran resilience |
| `docs/OSS_HARVEST_LOG.md` | Standing rule: techniques and public mathematics may be reimplemented freely; source code is copied only when the licence permits **and** the code survives $0/month, works under sanctions and filtering, no paid API dependency, auditable offline. Otherwise reimplement from first principles |
| `architecture/decision/authority.py`, `architecture/decision/read_model.py`, `architecture/pipeline/orchestrator.py` | Canonical Decision Authority and the pipeline that feeds it — the protected surfaces named in the tasking |

## 14.2 The decisive structural finding

**A FinanceDatabase→AHOS crypto provider adapter is not merely inadvisable. It is structurally
impossible without fabrication.**

`NormalizedTokenCandidate.__init__` requires `chain` and `address`. The FinanceDatabase `cryptos`
table has neither — verified by explicit existence check across `chain`, `network`, `contract`,
`address`, `contract_address`, `platform`, `token_id`, `decimals` (§8). `chain` appears only as
free prose inside `summary`, for **10 rows** out of 3,367.

Therefore any adapter would have to either:

1. **Fabricate** `chain` and `address` — a direct violation of AHOS's founding law
   *"Missing or uncollected data is NEVER guessed"* (`contracts.py:6`) and of the tasking's
   `UNKNOWN ≠ SAFE`; or
2. **Emit `None`** into two required `str` fields — violating the type contract and poisoning
   `ProviderRouter.discover_candidates()`'s dedupe key `(c.chain, c.address.lower())`, which would
   raise `AttributeError` on `None.lower()`; or
3. **Refuse to emit any candidate** — which is honest, and which makes the adapter a no-op.

Option 3 is the only admissible one, and it is indistinguishable from not integrating at all.

The same analysis applies to `BaseMarketProvider`'s abstract methods:

| Abstract method | Could FinanceDatabase satisfy it? |
|---|---|
| `fetch_candidate_tokens(chain, limit)` | **NO.** Cannot filter by chain (no chain field). Cannot rank by anything (no price, volume, liquidity, market cap, creation time). Returns a static ~2020-era list of 352 tickers |
| `fetch_token_metrics(chain, address)` | **NO.** Cannot look up by address. All 16 `MarketMetrics` fields would be `UNKNOWN` |
| `health_check()` | Only partially — it would probe `raw.githubusercontent.com`, which was **measured unreachable** from this environment (§11, S-14) |
| `capabilities` | The honest value is `[]` — an empty capability list |
| `provider_id` | Would have to be something like `financedatabase_static_catalogue`, which misrepresents it as a *provider* |

**Conclusion: FinanceDatabase cannot be registered in `ProviderRouter.providers`.** Doing so would
add a ninth adapter whose every field is `UNKNOWN`, whose dedupe key is unusable, and whose
`status` would be `OK` while conveying no information — the exact inversion of AHOS's design
intent.

## 14.3 Where it *could* attach, and what that would actually buy

Stripping away the crypto lane (rejected, §14.2 and §8), one hypothetical non-crypto lane remains:
**a static reference catalogue for TradFi securities**, used for *context and validation*, never
for opportunity discovery. Even that lane must answer three questions before it is worth building.

### What it would provide

| Capability | Real value | Already available in AHOS? |
|---|---|---|
| Ticker ↔ company-name ↔ country ↔ industry mapping for ~112,690 equity listings | **Genuine**, if a TradFi lane ever exists | **No** — AHOS has no TradFi catalogue today |
| ISIN/CUSIP/FIGI cross-reference for ~25–57% of listings | **Genuine but partial** | No |
| MIC (ISO 10383) exchange-code list, 71 entries | Small, and ISO publishes it directly | No — but trivially obtainable from ISO, not from this repo |
| Delisted-instrument history for US equities (10,404 rows) | **Genuine** anti-survivorship-bias value for backtesting | No |
| Check-digit validation algorithms (ISO 6166 ISIN, CUSIP, OpenFIGI) | **Genuine technique** — reimplement from the published standards | No |
| Crypto anything | **None** | Yes, and better — 8 existing adapters |
| Prices, volume, liquidity, market cap, on-chain state, security signals | **None** | Yes — `MarketMetrics` + `SecuritySignals` from live providers |

### What it would cost

| Cost | Evidence |
|---|---|
| A dependency on `financetoolkit ≥2.0.3` → `yfinance` (unpinned) + `scikit-learn` + `pandas>=3.0` | §9 EI-01…EI-04, §11.4 |
| Conflict with AHOS's `pandas>=2.1.0` floor and its "stdlib urllib, zero third-party network dependency" deterministic floor | `requirements.txt`, §9.4 |
| A mandatory live fetch from `raw.githubusercontent.com`, **measured unreachable** from this environment | §11 S-14/S-15 |
| An unverified-licence dataset with CUSIP/FIGI/GICS trademark adjacency and possible EU *sui generis* exposure | §12 LEG-01…04 |
| An identity model that cannot be reconciled with `IdentityResolution` (no issuer entity, symbol collisions, contradictory venues) | §5, §13 S-01/S-07/S-12 |
| Ingest-side engineering: schema assertion, hash pinning, null normalization, collision detection, MIC-based jurisdiction derivation | §13 S-03…S-19 |
| Maintenance: the dataset's non-US portion has **no automated maintenance** and its crypto portion has **no update job at all** | §7, README:467 |

### Verdict on the hypothetical non-crypto lane

**Not justified at present.** AHOS has no TradFi lane today, so there is nothing to attach to.
If and when one is authorized, the correct approach is **not** a FinanceDatabase adapter — it is
a **vendored, hash-pinned snapshot parsed by AHOS's own code** (§14.6), with the check-digit
algorithms **reimplemented from the published ISO/OpenFIGI standards** per
`docs/OSS_HARVEST_LOG.md`, rather than imported from this repository. That route captures 100% of
the real value at a fraction of the coupling, and it is the route this investigation recommends if
the lane is ever opened.

## 14.4 Constraint-by-constraint verdict

| AHOS constraint | Verdict | Evidence |
|---|---|---|
| **$0/month** | **PASS** | MIT, no API key, no paid tier. The only network calls are two `requests.get` to a public host |
| **No external API dependency** | **FAIL** | The default path requires a live HTTPS fetch. There is no bundled data and no offline mode for pip installs (`FileNotFoundError` on `site-packages/compression`, §11) |
| **No external API *key*** | **PASS** | No key anywhere in the package |
| **Works under sanctions and filtering** | **FAIL** | Depends on a US-hosted CDN path measured unreachable under this environment's filtering; no proxy configuration is honoured beyond ambient env vars; a spoofed Chrome-on-Windows User-Agent is hardcoded (§11.3 SEC-03) |
| **Offline-auditable** | **PARTIAL** | The package is auditable offline (1,866 lines, zero dangerous calls). The **data** is not obtainable offline without a prior full clone |
| **Deterministic floor uses stdlib `urllib` only** | **FAIL** | Adds `requests` (already optional in AHOS) plus `numpy`/`pandas` (already present) plus the `financetoolkit` tree (not present, and heavy) |
| **`pandas>=2.1.0` floor** | **AT RISK** | Transitively forces `pandas>=3.0` via `financetoolkit 2.2.0` on Python ≥3.11 (§9.3 EI-04). Observable dtype changes measured in this audit |
| **Python 3.11+** | **PASS** (barely) | Package declares `>=3.10,<3.16`; the CI-tested config is 3.10 which is *below* AHOS's floor and cannot be what AHOS would get (§9.3 EI-02/EI-03) |
| **Strict `UNKNOWN`, never guess** | **FAIL as shipped** | FinanceDatabase has no `UNKNOWN` concept: empty cells, absent columns and fail-open queries are all silently equivalent. AHOS would have to supply the entire layer (§14.6 rule 6) |
| **Provable source provenance (`source_provider`, `retrieved_ts`, `raw_payload_sha256`)** | **FAIL as shipped** | No timestamp, no source, no version column in any of the seven schemas (§7, §13 S-04). AHOS would have to synthesize all three at ingest |
| **Fail-closed on rate-limit / connection / schema error** | **MIXED** | `select()` is fail-closed (`ValueError`). `search()` is **fail-open** — an unknown column returns all 112,690 rows. Connection failure is fail-closed (`ValueError`). Local-file failure is **fail-open in the wrong way** — an uncaught `FileNotFoundError` |
| **Must not become a decision authority** | **ENFORCEABLE** | Requires an explicit boundary (§14.5) |
| **Must not modify Canonical Decision Authority** | **SATISFIED** | Nothing here proposes any change to `architecture/decision/authority.py` |
| **Must not affect scoring** | **SATISFIED, if bounded** | Requires that no FinanceDatabase-derived field ever enters `scoring.ts` / `architecture/scoring/` |
| **Must not affect security gates** | **SATISFIED, if bounded** | Requires that no FinanceDatabase-derived field ever enters `canonical_security.ts` / `architecture/security/` |
| **Must not affect existing identity resolution** | **AT RISK** | The two identity models are **unreconcilable** (§5.6). Any bridge must be adapter-only and one-directional |
| **Must not affect soak configuration or existing database state** | **SATISFIED** | A vendored read-only snapshot in a separate location touches neither |

**Four hard FAILs, two AT RISK, one MIXED.** Under AHOS's own `OSS_HARVEST_LOG` rule — *"When
those conflict, we reimplement from first principles and say so here"* — the correct disposition is
**reimplementation of the technique, not integration of the package**.

## 14.5 Boundary rules (mandatory if ever authorized)

These are the guardrails that would have to be *enforced and tested*, not merely documented.

| # | Rule | Enforcement mechanism |
|---|---|---|
| **B-1** | FinanceDatabase data may **never** reach `CanonicalDecisionAuthority`, `read_model`, `scoring`, `canonical_security`, `architecture/security/`, or any gate | No import path; a test asserting that no module under `architecture/decision`, `architecture/scoring`, `architecture/security` transitively imports the reference-catalogue module |
| **B-2** | It may **never** be registered in `ProviderRouter.providers` | A test asserting the adapter dict keys are exactly the current eight |
| **B-3** | It may **never** emit a `NormalizedTokenCandidate` | Type-level: the catalogue returns its own frozen dataclass, not the provider contract's |
| **B-4** | The `cryptos` asset class is **excluded entirely** from any AHOS path | The ingest allowlist contains only explicitly permitted asset classes; `cryptos` is absent from it |
| **B-5** | Every value is **untrusted text**: trim, case-normalize defensively, map empty → `UNKNOWN` | Ingest-side normalization, unit-tested against the measured pathological values (`'ECC           '`, `'two'`, `ILA`, `nan`) |
| **B-6** | Every emitted record carries `source="financedatabase"`, `source_commit=<sha>`, `artifact_sha256=<hash>`, `ingest_ts`, and a per-field `confidence` defaulting to `LOW` | Ingest contract, verified by test |
| **B-7** | The snapshot is **pinned by git commit SHA and per-file SHA-256**; ingest refuses any file not on the allowlist | Loader precondition |
| **B-8** | Schema is **asserted on ingest** (exact expected column list per asset class, row-count range); mismatch ⇒ reject the whole snapshot with `SCHEMA_MISMATCH` | Loader precondition |
| **B-9** | The source URL is **hardcoded**; `base_url` is never exposed to config, env, or any caller | No parameter surface |
| **B-10** | Cross-asset symbol collisions are **detected on ingest**; a non-empty result ⇒ `CONFLICT`, never silent merge | Collision check mirroring the project's own failing invariant test |
| **B-11** | `country` is **never** used for jurisdiction, sanctions, or compliance decisions; listing jurisdiction is derived from `mic` (ISO 10383) with `confidence=LOW` | Explicit field-usage policy + test |
| **B-12** | `exchange`/`market` for the 8,186 hardcoded `NMS`/`ASE` rows are emitted as venue-`UNKNOWN` | Ingest rule |
| **B-13** | The catalogue is **read-only** and lives **outside** the runtime path — no writes to AHOS database state, no soak-config interaction | Directory + permissions |
| **B-14** | No FinanceDatabase-derived value may be surfaced to an operator as *current*; every display path must carry the snapshot date | UI contract |
| **B-15** | The `financedatabase` package is **never installed** into the AHOS environment; if the data is used, AHOS parses raw CSV with its own code | `requirements.txt` unchanged; a CI check that `financedatabase` is not importable in the AHOS env |
| **B-16** | Any use of `search()`-style unescaped regex is **prohibited**; AHOS query paths escape all user-derived strings | Code review + test |
| **B-17** | Legal review of the dataset licence (§12) is **completed and recorded** before any vendoring, mirroring, redistribution or public serving | Gate on the `OSS_HARVEST_LOG.md` entry |
| **B-18** | The whole lane is **disabled by default** and requires an explicit operator opt-in | Feature flag, default off |

## 14.6 The only defensible architecture (if ever authorized)

**Not an adapter. Not a provider. A pinned, parsed, provenance-stamped reference catalogue.**

```
   ┌─────────────────────────────────────────────────────────────────────┐
   │  OFFLINE, MANUAL, HUMAN-IN-THE-LOOP  — never in the runtime path     │
   │                                                                      │
   │  1. git clone JerBouma/FinanceDatabase  (owner id 46355364 verified)  │
   │  2. git checkout <COMMIT_SHA>            ← pinned, never `main`       │
   │  3. sha256sum database/*/*.csv  →  SNAPSHOT_MANIFEST.json            │
   │  4. [GATE] legal review per §12 signed off  → OSS_HARVEST_LOG.md      │
   │  5. copy into  research/vendor/fdb/<COMMIT_SHA>/   (read-only, 0444)  │
   └───────────────────────────────┬──────────────────────────────────────┘
                                   │  file boundary — no network, no package
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  AHOS-SIDE INGEST (new module, AHOS code only — pandas>=2.1 already   │
   │  in requirements.txt; NO financedatabase, NO financetoolkit)          │
   │                                                                      │
   │  a. verify each file against SNAPSHOT_MANIFEST.json  → else ABORT     │
   │  b. assert exact column list + row-count range       → else ABORT     │
   │     (SCHEMA_MISMATCH, fail closed)                                    │
   │  c. pd.read_csv(dtype=str, keep_default_na=False, na_values=[""])     │
   │     ← AHOS's own reader; the library's reader is rejected (S-13)      │
   │  d. asset-class ALLOWLIST; `cryptos` is NOT on it      (B-4)          │
   │  e. normalize: trim, case rules, empty → UNKNOWN       (B-5)          │
   │  f. derive listing jurisdiction from `mic`, never `country` (B-11)    │
   │  g. detect cross-asset symbol collisions → CONFLICT    (B-10)         │
   │  h. stamp source / source_commit / artifact_sha256 / ingest_ts /      │
   │     confidence=LOW                                     (B-6)          │
   │  i. write  research/vendor/fdb/<SHA>/normalized.parquet  (read-only)  │
   └───────────────────────────────┬──────────────────────────────────────┘
                                   │  frozen dataclasses, AHOS-owned types
                                   ▼
   ┌─────────────────────────────────────────────────────────────────────┐
   │  CONSUMERS — reference lookup ONLY                                    │
   │                                                                      │
   │  ✓ a research notebook asking "does this ISIN exist?"                 │
   │  ✓ an offline backtest needing a delisted-universe list               │
   │  ✓ an adversarial test corpus for AHOS identity resolution            │
   │  ✗ CanonicalDecisionAuthority / read_model            (B-1)          │
   │  ✗ scoring.ts / architecture/scoring                  (B-1)          │
   │  ✗ canonical_security.ts / architecture/security      (B-1)          │
   │  ✗ ProviderRouter.providers                           (B-2)          │
   │  ✗ NormalizedTokenCandidate emission                  (B-3)          │
   │  ✗ architecture/identity/resolution.py — no merge, adapter-only       │
   │  ✗ any operator-facing surface as *current* data      (B-14)         │
   └─────────────────────────────────────────────────────────────────────┘
```

**Why this shape and not an adapter:**

| Property | Adapter/provider | Vendored snapshot |
|---|---|---|
| Network at runtime | Required (and measured unreachable) | **None** |
| New packages in the AHOS env | `financedatabase` + `financetoolkit` + `yfinance` + `scikit-learn` + pandas 3 | **None** |
| Integrity verification | None available | Per-file SHA-256 |
| Reproducibility | Impossible (`main` moves) | Exact (commit SHA) |
| Schema stability | None | Asserted at ingest |
| Legal surface | Redistribution + runtime dependency | Snapshot at a pinned commit; still **LEGAL REVIEW REQUIRED** (§12) |
| Blast radius on failure | Any lane that consumes the router | The reference catalogue only |
| Reversibility | Low | **Complete** — delete a directory |

## 14.7 Identity bridging — the hardest part, and the answer is "don't"

§5.6 established that the two identity models are **unreconcilable**:

| Dimension | AHOS `IdentityResolution` | FinanceDatabase |
|---|---|---|
| Primary key | `(chain, address)` — cryptographic, checksummed | `symbol` within an asset class — an exchange-assigned string |
| Entity notion | Token → Pool → DEX deployment | Listing row. **No issuer entity at all** |
| States | `VERIFIED / CONFLICT / UNRESOLVED / INVALID / STALE / UNSUPPORTED` | **None.** No state concept exists |
| Provenance | `IdentitySource(provider, chain, address, retrieved_ts, source_ts, kind)` | **None.** No timestamp, no source, no version |
| Conflict record | `conflicts: tuple[str, ...]` | **None.** Duplicates are silent (`BRK-A`/`BRK/A`) |
| Uniqueness guarantee | Enforced by dedupe on `(chain, address.lower())` | **Violated on `main`** — the project's own invariant test fails (`CHAD`) |
| Nearest usable key | — | `figi`, at **52.0%** coverage |

**Design decision: no identity bridge. Adapter-only, one-directional, non-authoritative.**

If a lookup is ever needed, the only admissible pattern is:

```
AHOS TokenIdentity  ──(symbol string, case-folded)──►  FinanceDatabase listing rows
                                                              │
                     ◄── returns 0..N candidate rows ─────────┘
                     ◄── AHOS decides: 0 → UNSUPPORTED
                                        1 → still LOW confidence, cross-check ISIN/FIGI
                                        N → CONFLICT, never auto-pick
```

- **Direction is one-way.** FinanceDatabase never writes into AHOS identity state.
- **The join key is the weakest possible** (a bare symbol), so the result is *always* at most
  `confidence=LOW`, and *always* corroborated against an identifier before use.
- **N candidates ⇒ `CONFLICT`**, mirroring AHOS's existing semantics. Never `keep='first'`.
- **The 86 measured crypto↔equity ticker collisions** (`META` = Metadium vs Meta Platforms,
  `GO` = GoChain vs Grocery Outlet, …) are exactly the failure this rule prevents — and they are
  the reason the `cryptos` class is excluded outright (B-4).
- **No `financedatabase` import inside `architecture/identity/`.** The identity module stays
  frozen; a separate reference-catalogue module owns the mapping and exposes only pure functions.

## 14.8 What AHOS should take instead: techniques, not code

Per `docs/OSS_HARVEST_LOG.md`, techniques and public mathematics may be reimplemented freely. The
genuinely valuable, licence-clean, dependency-free transferable ideas from this investigation:

| # | Technique | Source in FinanceDatabase | AHOS reimplementation note |
|---|---|---|---|
| T-1 | **ISO 6166 ISIN check digit** | `validation/validate_identifiers.py` (cites the standard) | Public algorithm. Implement directly from ISO 6166; ~15 lines; no licence obligation |
| T-2 | **CUSIP-9 check digit (mod 10, doubled digits)** | same file | Public algorithm. Note the **CUSIP trademark/licensing** question (§12.3) attaches to *using CUSIP numbers*, not to implementing the checksum |
| T-3 | **OpenFIGI check digit** | same file (cites `openfigi.com/docs/figi-check-digit.pdf`) | Public algorithm from a public spec |
| T-4 | **`actionable` vs `review-only` repair classification** | same file — 2 invalid CUSIPs of 249,085, **0 actionable**, 2 review-only | Excellent pattern for AHOS's own data-repair queues: never auto-fix an identifier that a human must adjudicate |
| T-5 | **Precomputed `categories` sidecar** so option lists load without the big file | `compression/categories/*.gzip`, loaded at `helpers.py:327-343` | Directly applicable to any large AHOS reference table |
| T-6 | **`mtime=0` in gzip for byte-reproducible artifacts** | the categorization job's inline script | Adopt for every AHOS generated artifact — makes snapshot diffing and hash pinning possible |
| T-7 | **Rejecting pickle in favour of CSV+bz2 on security grounds**, with the benchmark preserved | `compression/README.md` + `compression.ipynb` | Matches AHOS's existing posture; worth citing in `OSS_HARVEST_LOG.md` as external corroboration |
| T-8 | **Invariant tests as a separate CI job that deselects slow identifier checks** | `testing.yml` + `tests/test_invariants.py` | The *pattern* is good; the *placement* is the bug (validation runs last and is non-blocking, §7 DQ-03/DQ-04). AHOS should run invariants **before** publishing, and make them **blocking** |
| T-9 | **Retaining delisted instruments deliberately** to avoid survivorship bias | README:465 + 10,404 `delisted=True` rows | Valuable for AHOS backtesting; but note it is **equities-only** (open issue #153) — a partial solution |
| T-10 | **A `show_options` validator that makes `select()` fail closed** | `helpers.py:282-343` + `Equities.py` | This is the single best idea in the codebase. AHOS's own query surfaces should adopt the same discipline — and should avoid FinanceDatabase's mistake of having a *second*, fail-open API (`search()`) beside it |

**Ten techniques, zero lines of copied code, zero new dependencies, zero licence obligation.**
This is the highest-value, lowest-risk outcome of the entire investigation, and it is available
**regardless** of whether any data is ever consumed.

## 14.9 Integration decision summary

| Integration mode | Verdict |
|---|---|
| Register as a `ProviderRouter` adapter | **REJECTED — structurally impossible** (§14.2) |
| Use as a crypto opportunity source | **REJECTED** (§8, §13 S-20) |
| Use as a crypto identity/enrichment source | **REJECTED** (§5.6, §14.7) |
| Install the package into the AHOS environment | **REJECTED** (§14.4 — four hard FAILs) |
| Call its live remote loader at runtime | **REJECTED** (§11 S-14/S-15 — host measured unreachable) |
| Use `to_toolkit()` / FinanceToolkit / FMP | **REJECTED** — outside scope, undeclared cost, unpinned `yfinance`, affiliate-linked (§9) |
| Feed any value into scoring / security gates / Canonical Decision Authority | **PROHIBITED** (B-1) |
| Vendored, hash-pinned, AHOS-parsed reference snapshot for a **future non-crypto lane** | **CONDITIONALLY POSSIBLE** — requires B-1…B-18, the §12 legal review, and separate explicit authorization. **Not recommended now** (no TradFi lane exists) |
| Reimplement the ten techniques (T-1…T-10) from first principles | **RECOMMENDED** — licence-clean, dependency-free, and valuable regardless of the data decision |
| Keep it as an adversarial test corpus for AHOS identity resolution | **RECOMMENDED (research-only)** — the `CHAD` collision, the `BRK-A`/`BRK/A` duplicate, the 86 crypto↔equity ticker collisions, the `ILA`/`ILS` currency error and the `NA`-ticker loss are *free, real, published* failure cases that AHOS's own resolver should be tested against |
