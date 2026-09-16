# 27 — Identity Fixture Review Queue

**Document 27 · Extraction package deliverable 2 of 5.**

| Role | Agent | Function |
|---|---|---|
| Author | **Agent E — Evidence Authority** | Registers FIX-01…FIX-06 as review items with threat model, failure mode, invariant, test boundary and both error risks |
| Mandatory reviewer | **Agent B — Engineering Governor** | Owns the approval gate. **Nothing in this queue may be implemented until Agent B approves it and separate written authorization exists** |

> ## ⚠️ REVIEW QUEUE — NO IMPLEMENTATION
>
> This document **registers** fixtures. It does not create them. No test file was added to `tests/`
> or `tests2b/`. `architecture/identity/resolution.py` was **not read for modification and not
> changed** — it was inspected read-only to verify that the invariants named below actually exist at
> the paths cited. No AHOS file of any kind was modified. No fixture data was committed.
>
> **Every entry: `Implementation authorized: NO`.**

> ## ⚠️ Attribution boundary — carried into any future implementation
>
> **No FinanceDatabase record is an AHOS production failure.** All six fixtures derive from a
> **third-party** dataset at commit `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634`. They are proposed as
> **adversarial input data** for tests that assert on **existing** AHOS behaviour. AHOS's crypto
> identity domain is `(chain, address)`; FinanceDatabase's TradFi domain is `symbol`. The fixtures
> exercise the *resolver's discipline*, not a claimed defect. If any fixture is ever implemented,
> this paragraph must be reproduced in the test module docstring.

---

## 27.0 Invariants under test — verified to exist

Before queueing fixtures against AHOS invariants, Agent E verified read-only that the named
constructs exist. **No path in this document is invented.**

| Invariant / construct | Verified location | Verified content |
|---|---|---|
| `IdentityState` enumeration | `architecture/identity/types.py:14-20` | `VERIFIED`, `CONFLICT`, `UNRESOLVED`, `INVALID`, `STALE`, `UNSUPPORTED` — **note: there is no `UNKNOWN` member**; the fixtures below must map "unknown" onto `UNRESOLVED` or `UNSUPPORTED`, not invent a state |
| `TokenIdentity.address_canonical` | `architecture/identity/types.py:44` | `str \| None` — the **key** |
| `TokenIdentity.symbol_alias` | `architecture/identity/types.py:47` | `str \| None` — explicitly an **alias** |
| `PoolIdentity.belongs_to_token` | `architecture/identity/types.py:73` | `bool \| None = None` |
| `IdentityResolution.conflicts` | `architecture/identity/types.py:83` | `tuple[str, ...] = ()` — the field that must carry enumerated disagreement |
| `IdentityResolution.policy_version` | `architecture/identity/types.py` (same dataclass) | `"identity-resolution-v1"` — a fixture change must not silently bump this |
| `IdentitySource` provenance | `architecture/identity/types.py:24-33` | `provider`, `chain`, `address`, `retrieved_ts`, `source_ts`, `kind` |
| `resolve_identity()` entry point | `architecture/identity/resolution.py:117` | public resolver |
| `_sources_conflict()` | `architecture/identity/resolution.py:58` | conflict detector |
| `_independent_enough()` | `architecture/identity/resolution.py:46` | corroboration threshold |
| `_belongs()` | `architecture/identity/resolution.py:73` | pool↔token attribution |
| Namespaced composite dedupe key | `architecture/providers/registry.py` | `key = (c.chain, c.address.lower())` |
| `UNKNOWN_VALUE` discipline | `architecture/providers/contracts.py:16` | `UNKNOWN_VALUE = None` |
| Contract law | `architecture/providers/contracts.py:5` | *"Strict UNKNOWN representation: Missing or uncollected data is NEVER guessed."* |
| `confidence_level` default | `architecture/providers/contracts.py:74` | `confidence_level: str = "HIGH"` — see FIX-05 and KN-02 |

**Consequence for the queue:** FIX-01…FIX-04 can be expressed entirely against existing constructs.
FIX-05 requires a decision about how "unknown name" maps onto an `IdentityState` that has no
`UNKNOWN` member — that is an **Agent B design question**, recorded in the FIX-05 approval gate.

---

## 27.1 Queue ordering

Priority is by (a) severity of the failure mode if the invariant does not hold, and (b) cost of the
test. All six are cheap; none requires network, a package install, or a mutable external source.

| Order | Fixture | Severity if invariant fails | Cost | Blocking dependency |
|---:|---|---|---|---|
| 1 | **FIX-06** NA-coercion key loss | **CRITICAL** — silent, undetectable by row count | Very low | None |
| 2 | **FIX-01** Cross-schema symbol collision | **HIGH** — merges distinct entities | Very low | None |
| 3 | **FIX-03** Bare ticker, 4 entities + name variant | **HIGH** — both over-merge and over-split | Low | None |
| 4 | **FIX-05** Compound placeholder/jurisdiction/imputation | **HIGH** — three disciplines at once | Medium | Agent B decision on `UNKNOWN`→`IdentityState` mapping |
| 5 | **FIX-02** Venue contradiction, inverted identifiers | **MEDIUM-HIGH** — conflict recorded vs silently resolved | Medium | None |
| 6 | **FIX-04** Identifier level confusion | **MEDIUM** — wrong hierarchy level as key | Medium | Legal review if ISIN **values** are embedded (document 29) |

---

## 27.2 FIX-01 · Cross-schema symbol collision

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-01-CROSS-SCHEMA-SYMBOL-COLLISION` |
| **Source case** | Document 20 CASE 1 — `CHAD`, FinanceDatabase @ `a174c97d3b` |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `CHAD`, `cross_asset_symbol_collisions` (equities↔etfs is the **only** colliding class pair; collision set = `{'CHAD'}`, n=1); corroborated by the upstream project's **own** invariant test failing on this row at `tests/test_invariants.py:95` (`1 failed, 85 passed, 1 deselected in 42.43s`) |
| **Input records** | R1 `{asset_class:"equities", symbol:"CHAD", name:"DeFi Development Corp. Variable Rate Series C Perpetual Preferred Stock", country:"United States", exchange:"NMS", mic:"XNAS", currency:"USD", isin:null, cusip:null, figi:null}`<br>R2 `{asset_class:"etfs", symbol:"CHAD", name:"Direxion Daily CSI 300 China A Share Bear 1X Shares", exchange:"PCX", mic:"ARCX", currency:"USD", isin:null}` |
| **Threat model** | **Namespace collapse.** An adversary (or merely an unlucky corpus) supplies two unrelated instruments sharing one symbol string across two namespaces, with **no identifier on either side** to arbitrate. Any resolver that blocks, joins, caches or deduplicates on the bare symbol merges them. The merger is **silent**: both records are individually valid, so no validation layer objects. Amplified here by the fact that the equity side is a **crypto-adjacent** company (DeFi Development Corp.) — a hypothetical crypto↔TradFi bridge keyed on symbol would collide on exactly the entity class it most wants to find |
| **Expected failure mode** | R1 and R2 collapse into one identity. Downstream effects: one entity inherits two names, two MICs (`XNAS` vs `ARCX`) and two asset classes; metrics from one instrument are attributed to the other; a later query by symbol returns whichever record won the merge, non-deterministically if ordering changes |
| **Affected identity invariant** | **A key is unique only within its namespace.** AHOS side: the composite `(chain, address)` dedupe key in `architecture/providers/registry.py`; the alias/key separation at `architecture/identity/types.py:44` vs `:47` |
| **Required test boundary** | **Unit — resolver only.** Feed both records to `resolve_identity()` (`architecture/identity/resolution.py:117`) as separate inputs. Assert: (1) queried by bare `symbol="CHAD"` with no namespace → **both** candidates returned, state `CONFLICT`, both enumerated in `IdentityResolution.conflicts`; (2) queried by `(asset_class, symbol)` → each resolves `VERIFIED` independently; (3) no record is dropped; (4) `policy_version` unchanged. **Must not** touch network, providers, scoring, decision authority, paper trading, runtime or database state |
| **False-positive risk** | **MEDIUM.** A resolver that *legitimately* returns a single best candidate by design (documented "pick-primary" behaviour) would fail this assertion while behaving as specified. Mitigation: the fixture must assert on **conflict enumeration**, not on the number of returned records — if AHOS's documented contract is "return one, record the conflict", the test must expect exactly that. **Agent B must confirm the intended contract before the assertion is written** |
| **False-negative risk** | **LOW-MEDIUM.** n=1 in the source corpus means the fixture tests one shape of collision. A resolver could pass on `CHAD` and still fail on a collision where the two sides *do* carry identifiers that happen to match, or where the colliding symbol differs only by case or trailing whitespace (19 whitespace-bearing symbols exist in the source). Mitigation: pair with FIX-03 |
| **Approval gate** | **Agent B.** Gate questions: (a) is "return both candidates" or "return one + record conflict" the intended contract? (b) does the fixture directory location avoid `tests/` and `tests2b/` until authorized? (c) is the attribution boundary reproduced in the test docstring? |
| **Implementation authorized** | **NO** |

---

## 27.3 FIX-02 · Same entity, contradictory venues, identifiers on the wrong subset

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-02-VENUE-CONTRADICTION-INVERTED-IDENTIFIERS` |
| **Source case** | Document 20 CASE 2 — Berkshire Hathaway, **7 rows across 4 venues** (expanded from 5 by re-execution) |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `BRK_all_rows`, `BRK_berkshire_rows`, `BRK_distinct_exchanges=['ASE','MEX','NYQ','VIE']`, `BRK_all_isin_empty=true`; root cause verified in source at `.github/workflows/database_update.yml:175-176` (assigns `exchange='ASE'`, `market='NYSE MKT'` wholesale to the NYSE feed) and `:185` (`pd.concat` of three feeds **without** `keys=`); document 03 DP-01/DP-02; document 13 S-07/S-12 |
| **Input records** | 7 records, all `name="Berkshire Hathaway Inc."`, `country="United States"`:<br>`{symbol:"BRK-A", exchange:"NYQ", mic:"XNYS", currency:"USD", figi_present:false}`<br>`{symbol:"BRK-B", exchange:"NYQ", mic:"XNYS", currency:"USD", figi_present:false}`<br>`{symbol:"BRK/A", exchange:"ASE", mic:"XASE", currency:"USD", figi_present:false}`<br>`{symbol:"BRK/B", exchange:"ASE", mic:"XASE", currency:"USD", figi_present:false}`<br>`{symbol:"BRKA.VI", exchange:"VIE", mic:"XWBO", currency:"EUR", figi_present:true}`<br>`{symbol:"BRKB.MX", exchange:"MEX", mic:"XMEX", currency:"MXN", figi_present:false}`<br>`{symbol:"BRKB.VI", exchange:"VIE", mic:"XWBO", currency:"EUR", figi_present:true}`<br>**FIGI values are replaced by a `figi_present` boolean** — see §27.8 |
| **Threat model** | **Corroboration inversion.** The identifier capable of arbitrating exists **only on the secondary listings**. A resolver that treats "identifier present ⇒ resolved" will confidently resolve the two Vienna rows and silently leave the four US rows — the primary ones — ambiguous. Compounding threats: (a) **symbol-convention duplication** (`BRK-A` ≡ `BRK/A`) assigned **contradictory venues** by the pipeline; (b) **currency divergence** (USD/EUR/MXN) for one issuer with no primary-listing marker; (c) an adversary can induce a false merge simply by supplying the identifier on the wrong subset |
| **Expected failure mode** | Two distinct failures available from one input: **over-merge** (`BRK-A` and `BRK/A` treated as one listing, so a venue is silently overwritten and NYSE vs NYSE MKT attribution becomes arbitrary) or **over-split** (treated as two entities, double-counting one share class). Additionally: `figi_present=true` on Vienna rows is mistaken for global resolution success, so **coverage is reported as 100% while 4 of 7 rows remain unresolved** |
| **Affected identity invariant** | **Contradictory corroboration must be recorded, not resolved by preference.** AHOS side: `IdentityState.CONFLICT` (`architecture/identity/types.py:16`), `IdentityResolution.conflicts` (`:83`), `_sources_conflict()` (`architecture/identity/resolution.py:58`), `_independent_enough()` (`:46`) |
| **Required test boundary** | **Unit — resolver only.** Assert: (1) exactly **two share classes** (A, B) are recognized across 7 listings; (2) `BRK-A`/`BRK/A` and `BRK-B`/`BRK/B` are flagged **candidate duplicates**, neither merged nor accepted as distinct without a note; (3) state `CONFLICT` on `exchange`/`mic` with **both** venue values preserved and enumerated in `conflicts`; (4) identifier-based dedup is reported **unavailable** for the four `figi_present:false` rows, and the resolver reports **coverage** (4/7), not just success; (5) currency divergence is preserved per listing — never averaged, never first-picked. **No** provider, network, scoring or state involvement |
| **False-positive risk** | **HIGH — the highest in the queue.** Expecting exactly two share classes encodes a **TradFi domain assumption** (share-class hierarchy) that AHOS's crypto identity model does not have. AHOS's analogue is `token_id` vs `pool_id`, not share class vs listing. A correct AHOS resolver may legitimately produce a different entity count. **Mitigation: Agent B must decide whether this fixture is ported to the crypto domain (e.g. two bridges reporting the same token with conflicting `chain` values and only one carrying an address) or retained as a TradFi-domain test that AHOS's resolver is not expected to satisfy.** Registered as a **design question**, not an assertion |
| **False-negative risk** | **MEDIUM.** With FIGI values replaced by a boolean, the fixture cannot test *identifier mismatch* (two different FIGIs for one entity) — only identifier *absence*. A resolver could pass while still mis-handling genuinely conflicting identifiers. Mitigation: if Agent B wants mismatch coverage, a **synthetic** identifier must be used, never a real third-party value (§27.8) |
| **Approval gate** | **Agent B**, with a mandatory pre-decision: **port to crypto domain, or mark as out-of-domain reference material?** Plus: (a) confirm the `CONFLICT` state is the intended output and that no `UNKNOWN` state is invented; (b) confirm coverage-reporting is an expected resolver output at all — if AHOS's resolver has no coverage concept, this assertion must be dropped rather than forced |
| **Implementation authorized** | **NO** |

---

## 27.4 FIX-03 · Bare ticker spanning four unrelated entities plus a name variant

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-03-BARE-TICKER-MULTI-ENTITY-PLUS-NAME-VARIANT` |
| **Source case** | Document 20 CASE 3 — `MMM`, **18 rows / 4 entities / 5 name strings** (expanded from 2 entities by re-execution) |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `MMM_rows`, `MMM_count=18`, `MMM_distinct_names` (5), `top_repeated_bare_tickers` (`MMM`×18, `AIR`×17, `HAL`×17, `SAP`×16, `AMD`×15, `MRK`×15, `CTO`×14, `EMR`×14), `distinct_bare_tickers=74690` of 112,690 rows, `bare_tickers_appearing_more_than_once=16251`; document 13 S-02 |
| **Input records** | 18 records in five clusters:<br>**E1** (14 rows) `name="3M Company"`, `country="United States"`, symbols `MMM`, `MMM.BA`, `.BE`, `.DE`, `.DU`, `.F`, `.HA`, `.HM`, `.MU`, `.MX`, `.SN`, `.SW`, `.TI`, `.VI`<br>**E1-variant** (1 row) `symbol="MMM.SG"`, `name="3M Co. Registered Shares DL -,0"`, `country="United States"`, `exchange="STU"`<br>**E2** `symbol="MMM.AX"`, `name="Marley Spoon AG"`, `country="Germany"`, `exchange="ASX"`<br>**E3** `symbol="MMM.L"`, `name="Mining, Minerals & Metals plc"`, `country="United Kingdom"`, `exchange="LSE"`<br>**E4** `symbol="MMM.V"`, `name="Minco Capital Corp."`, `country="Canada"`, `exchange="VAN"` |
| **Threat model** | **Bidirectional identity error from a single input.** One bare ticker maps to `{1 entity × 14 listings} ∪ {3 unrelated entities}`, with a **name variant inside the first set**. Grouping on exact `name` over-splits E1 into two; grouping on bare `symbol` over-merges all four. There is no single-field heuristic that is correct, so any resolver relying on one is exploitable by ordinary data — no adversary required. Scale context: 16,251 of 74,690 bare tickers repeat, so this is the **common** case, not an edge case |
| **Expected failure mode** | **Over-merge:** four unrelated companies (US industrials, German food-tech, UK mining, Canadian capital markets) become one entity; metrics, jurisdiction and sector are cross-contaminated; a position or signal attributed to 3M may originate from Minco Capital. **Over-split:** 3M becomes two entities because the Stuttgart listing uses the German registered-share naming convention; the same instrument is double-counted or half-tracked |
| **Affected identity invariant** | **A symbol is an alias, never an identity.** AHOS side: `TokenIdentity.symbol_alias` (`architecture/identity/types.py:47`) vs `address_canonical` (`:44`); contract law *"Missing or uncollected data is NEVER guessed"* (`architecture/providers/contracts.py:5`) |
| **Required test boundary** | **Unit — resolver only.** Assert: (1) output is **four** entities, not one and not five; (2) `MMM.SG` attaches to **E1** despite the differing name, or — if it cannot — the resolver reports `UNRESOLVED` with the reason, and **never** silently creates a fifth entity; (3) E2/E3/E4 do **not** merge with E1 despite the shared bare ticker; (4) any merge performed without an identifier carries `confidence=LOW` and is **reversible**; (5) no `keep="first"`-style positional tie-breaking; (6) a query by bare `symbol="MMM"` enumerates all four candidates. **Resolver-only; no provider, network, scoring or state** |
| **False-positive risk** | **MEDIUM.** Assertion (2) — that `MMM.SG` *must* attach to E1 — requires domain knowledge (German registered-share naming) that a resolver cannot be expected to have without a name-normalization table. A resolver returning `UNRESOLVED` for `MMM.SG` is **correct behaviour**, not a failure. **Mitigation: assertion (2) must be written disjunctively — attach to E1 OR report UNRESOLVED with reason. Agent B to confirm.** Assertions (1), (3), (5), (6) are unambiguous and carry the fixture's weight |
| **False-negative risk** | **LOW.** This is the strongest fixture in the queue against symbol-as-identity: 18 records, both error directions, and a name variant. Residual gap: it does not test **case-folding** collisions or **whitespace** collisions (19 whitespace-bearing symbols exist in the source, e.g. `'ECC           '`), nor the 47,578 lowercase-duplicate names. Mitigation: a whitespace/case sibling case can be added later if Agent B wants that coverage |
| **Approval gate** | **Agent B.** Gate questions: (a) accept the disjunctive form of assertion (2)? (b) does AHOS's resolver have a confidence concept applicable here (`confidence_level` exists on the provider contract, `architecture/providers/contracts.py:74` — confirm it is the right surface)? (c) is reversibility of a merge an existing guarantee or a new requirement? If new, **this fixture is requesting a feature and must be routed as a design proposal, not a test** |
| **Implementation authorized** | **NO** |

---

## 27.5 FIX-04 · Identifier valid at one hierarchy level, one-to-many at another

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-04-IDENTIFIER-LEVEL-CONFUSION` |
| **Source case** | Document 20 CASE 4 — ISIN fan-out, max **57** |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `ISIN_max_fanout=57`, `ISIN_distinct=9406`, `ISIN_populated_rows=30429` (**27.0%** of 112,690), `ISIN_fanout_gt_1=5181` (**55.1%** of populated ISINs), `ISIN_top_fanout` (`FR0013269123`→57 Rubis; `US6934831099`→47 POSCO; `AU000000BHP4`→35 BHP; `US9286625010`→34 Volkswagen; `FR0000120578`→25 Sanofi across **France and India**); document 04 SC-03; document 13 S-02 |
| **Input records** | Three sub-cases.<br>**F4a (extreme fan-out):** `isin="FR0013269123"`, `name="Rubis"`, `country="France"`, with **57** distinct symbols (a representative subset of ≥8 may be used — Paris, Brussels, Amsterdam and German venue listings).<br>**F4b (cross-country fan-out):** `isin="FR0000120578"`, `name="Sanofi"`, **25** symbols, `country ∈ {"France","India"}`.<br>**F4c (coverage control):** the same issuer with `isin=null` on the majority of listings, mirroring the measured **27.0%** population rate |
| **Threat model** | **Hierarchy-level confusion.** An identifier that is globally unique at level *N* (share class) is one-to-many at level *N+1* (listing). A resolver that keys on it at the wrong level either **multiplies** entities (57 listings → 57 entities) or **collapses** them (57 listings → 1 record, losing 56 venues). The 27.0% population rate makes it worse: the identifier is simultaneously non-unique where present and **absent 73% of the time**, so absence cannot be distinguished from "not yet loaded". F4b adds a jurisdiction trap — one ISIN spanning two countries means `country` cannot be derived from it |
| **Expected failure mode** | **Entity multiplication:** 57 entities for one share class; aggregates inflated ~57×; deduplication statistics meaningless. **Entity collapse:** venue-specific attributes (currency, MIC) overwritten by whichever listing is read last. **Jurisdiction inference:** Sanofi's Indian listings labelled France, or vice versa. **Silent skip:** the 73% of rows with no ISIN are dropped rather than marked unknown |
| **Affected identity invariant** | **An identifier is a key at exactly one hierarchy level.** AHOS side: `TokenIdentity` vs `PoolIdentity` with `PoolIdentity.belongs_to_token` (`architecture/identity/types.py:64,73`); `_belongs()` (`architecture/identity/resolution.py:73`); the `token_id` vs `pair_id` distinction |
| **Required test boundary** | **Unit — resolver only.** Assert: (1) F4a resolves to **one** share-class entity with **many** listings — not 57 entities, not 1 collapsed record; (2) using the identifier as a **listing-level** key is rejected; (3) in F4b, `country` is **not** inferred from the identifier; (4) in F4c, absent identifiers yield `UNRESOLVED`/`UNSUPPORTED` — **never** a guess, never a silent skip, and the skip count is reported; (5) any aggregation states its grouping level explicitly. **Resolver-only** |
| **False-positive risk** | **MEDIUM-HIGH.** Assertion (1) presumes AHOS's resolver models a two-level hierarchy for this input shape. If the fixture is fed as TradFi listings into a crypto-domain resolver, "one entity with many listings" may not be a representable output at all. **Mitigation: Agent B must first decide the domain mapping — the natural AHOS analogue is one `TokenIdentity` with many `PoolIdentity` rows where `belongs_to_token=True`. Written that way, the fixture is domain-correct; written as share-class/listing, it is not.** |
| **False-negative risk** | **MEDIUM.** With a ≥8-symbol subset the fixture cannot detect a resolver that behaves correctly up to *k* listings and degrades beyond it (the real maximum is 57). Also, F4c's control case only tests absence — it does not test a **malformed but non-empty** identifier, which is the more common ingest hazard. Mitigation: a malformed-identifier sibling (synthetic, not real) if Agent B wants that coverage |
| **Approval gate** | **Agent B AND legal (conditional).** Agent B: (a) approve the token/pool domain mapping; (b) approve subset size. **Legal: required if any real ISIN value is embedded** — ISIN is ISO 6166 and the values here are real. Queued in document **29**. **Preferred mitigation: use synthetic ISIN-shaped strings with a valid check digit computed from the public ISO 6166 specification, eliminating the legal dependency entirely** |
| **Implementation authorized** | **NO** |

---

## 27.6 FIX-05 · Compound failure: placeholder name + wrong jurisdiction + imputed classification

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-05-COMPOUND-PLACEHOLDER-JURISDICTION-IMPUTATION` |
| **Source case** | Document 20 CASE 5 — `two`, **129 rows across 29 venue suffixes**, plus the `SOL1`/`SOL` prose-vs-key sibling |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `TWO_rows`, `TWO_count=129`, `TWO_distinct_countries`, `TWO_symbol_suffixes=29`; **FOLLOWUP-02**: all 129 rows carry `sector="Financials"`, `industry_group="Diversified Financials"`, `industry="Diversified Financial Services"` with **zero variance**, matching `mode()` of the `sector=='Financials'` subset exactly — the imputation mechanism at `.github/workflows/database_update.yml:87,113` is **proven to have fired**, closing U-13 from the data side; `evidence/followup/f1_objective_a.json` → `sample_fdb_cryptos_row` (`cryptocurrency='SOL1'`, `summary='Solana (SOL) is a cryptocurrency.'`); `architecture/providers/contracts.py:74` (`confidence_level` default `"HIGH"`) |
| **Input records** | A representative subset of ≥6 of the 129, all `name="two"`, `country="United States"`, `sector="Financials"`, `industry_group="Diversified Financials"`, `industry="Diversified Financial Services"`, `isin=null`:<br>`{symbol:"000851.SZ", exchange:"SHZ", mic:"XSHE", currency:"CNY"}`<br>`{symbol:"002447.SZ", exchange:"SHZ", mic:"XSHE", currency:"CNY"}`<br>`{symbol:"046110.KQ", exchange:"KOE", mic:"XKOS", currency:"KRW"}`<br>`{symbol:"0JUZ.L", exchange:"LSE", mic:"XLON", currency:"USD"}`<br>`{symbol:"0OFR.IL", exchange:"IOB", mic:"XLON", currency:"PLN"}`<br>`{symbol:"0YW.BE", exchange:"BER", mic:"XBER", currency:"EUR"}`<br>**Plus the sibling case:** `{symbol:"SOL1-CAD", cryptocurrency:"SOL1", name:"Solana CAD", summary:"Solana (SOL) is a cryptocurrency."}` — **the key says `SOL1`, the prose says `SOL`** |
| **Threat model** | **Compound silent corruption.** One record is simultaneously (a) **unnameable** — `name="two"` is a corrupted placeholder, not an entity; (b) **mis-jurisdictioned** — Shenzhen, KOSPI, London, Berlin and Tel Aviv listings all labelled `United States`; (c) **mis-classified by imputation** — the sector/industry triple is a statistical mode, not an observation, with **no field marking it as such**. Every defect is invisible because the source schema has **no confidence and no provenance field**. The `SOL1`/`SOL` sibling adds a fourth threat: **prose contradicts the identity key**, and a resolver that trusts free text over the key will mis-attribute Solana data |
| **Expected failure mode** | (1) 129 unrelated listings grouped into one entity named "two"; (2) jurisdiction taken from `country` rather than `mic`, so Chinese, Korean, British, German and Israeli listings are all treated as US; (3) imputed classification propagated at **full confidence** — the exact shape of the `confidence_level="HIGH"` default observation (KN-02); (4) prose-vs-key inversion: `SOL1` treated as `SOL` because the summary says so, mis-attributing a quote-currency pair to a token |
| **Affected identity invariant** | **Three at once:** (i) placeholder values must resolve to **unknown**, never to an entity; (ii) jurisdiction must derive from the **authoritative** field (`mic`), not a convenient one (`country`); (iii) imputed or inferred data must carry **reduced confidence and explicit provenance**. Plus (iv) **the key governs identity; prose is untrusted text**. AHOS side: `UNKNOWN_VALUE = None` (`architecture/providers/contracts.py:16`), the contract law at `:5`, `confidence_level` at `:74`, `IdentitySource` provenance at `architecture/identity/types.py:24-33` |
| **Required test boundary** | **Unit — resolver and ingest validation only.** Assert three **independent** gates each fire: (1) placeholder-name rejection → `UNRESOLVED`, and the 129 rows are **not** grouped; (2) `country` vs `mic` contradiction **detected and reported** (`XSHE`→CN, `XKOS`→KR, `XLON`→GB, `XBER`→DE, none US); (3) **zero-variance classification across unrelated records detected as an imputation signature** → `confidence=LOW`, `provenance=INFERRED_UNKNOWN`; (4) for the sibling, the **key** governs identity and `summary` is treated as untrusted — never the reverse; (5) **no record is emitted as actionable**. **Must not** involve providers, network, scoring, decision authority, paper trading, runtime or soak |
| **False-positive risk** | **MEDIUM.** Gate (3) — detecting an imputation signature from zero variance — is a **statistical heuristic**, not a deterministic rule. Legitimate data can have zero variance across a small subset (6 records sharing a sector is unremarkable). At n=6 this gate **will** produce false positives. **Mitigation: gate (3) must be tested at the corpus level (n=129, where zero variance across 29 venues and 5+ currencies is genuinely anomalous), not at the 6-record fixture level — or it must be asserted as a warning, not a failure. Agent B to decide.** Gates (1), (2), (4), (5) are deterministic and carry the fixture's weight |
| **False-negative risk** | **MEDIUM.** The `mic`→jurisdiction mapping in gate (2) presumes AHOS has such a mapping. If it does not, the gate cannot fire and the fixture passes vacuously — a **false negative by omission**. Also, with a ≥6 subset the fixture cannot detect a resolver that groups at 129 but not at 6. Mitigation: assert the mapping's **existence** as a precondition, so absence fails loudly rather than silently |
| **Approval gate** | **Agent B — highest scrutiny in the queue.** Gate questions: (a) how does "unknown name" map onto an `IdentityState` that has **no `UNKNOWN` member** (`architecture/identity/types.py:14-20`)? `UNRESOLVED` or `UNSUPPORTED` — **Agent B must choose; the fixture must not invent a state**; (b) is gate (3) a failure or a warning at fixture scale? (c) does a `mic`→jurisdiction mapping exist in AHOS, and if not, is this fixture requesting one (i.e. a feature, not a test)? (d) does the `SOL1`/`SOL` sibling belong in an identity fixture or in a crypto-ingest fixture? |
| **Implementation authorized** | **NO** |

---

## 27.7 FIX-06 · NA-coercion key loss

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-06-NA-COERCION-KEY-LOSS` |
| **Source case** | Objective C — the `NA` ticker regression, verified in document 21; **new fixture proposed as a by-product** |
| **Evidence reference** | `evidence/followup/f3_na_regression.json` → `C4_source_records_with_symbol_NA` (**`database/equities/NMS.csv:4346`**, `NA,Nano Labs Ltd Class A Ordinary Shares,…,NMS,XNAS,NASDAQ Global Select`), `C4_count=1`, `C5_release_rows=112690`, `C6_main_rows=112690`, `C5_cell_level_divergence_empty=true`, `C5_release_index_nan_count=1`, `C6_main_index_nan_count=0`, `C5_release_NA_in_index=false`, `C5_release_loc_NA="KeyError: 'NA'"`, `C6_main_NA_in_index=true`, `C10_pandas_default_na_strings` (19 tokens), `C10_ONLY_EQUITIES_AFFECTED=true`; fix provenance `3b8eb839…` (2026-08-07, PR #166) **not** an ancestor of tag `2.4.0`; upstream's own workflow comment records two prior instances of the same class (`"9763"`→`"9763.0"`, `"031162100"`→`"31162100.0"`, which *"dropped that row on every run"*); re-confirmed independently this pass |
| **Input records** | Primary: `{symbol:"NA", name:"Nano Labs Ltd Class A Ordinary Shares", country:"China", exchange:"NMS", mic:"XNAS", market:"NASDAQ Global Select", currency:"USD", sector:"Information Technology", isin:null}` — the exact record at `NMS.csv:4346`<br>**Plus ten adversarial siblings** drawn from the verified pandas default-NA list: `N/A`, `NULL`, `NaN`, `None`, `nan`, `null`, `<NA>`, `#N/A`, `-nan`, `1.#IND`<br>**Plus two numeric-coercion siblings** from the upstream workflow's own comment: `"9763"` and `"031162100"` |
| **Threat model** | **Silent key annihilation at the ingest boundary.** A library's *convenience* default (interpreting 19 magic strings as missing) converts a **legitimate primary key** into null. No layer raises: the file parses, the row is present, the row count is unchanged, and cell-level comparison shows **zero** divergence. The record simply becomes **unaddressable** — and is dropped later, at an arbitrary distance from the cause, by any `notna()`-style key filter. This is the most dangerous shape of defect in the package because **every conventional health check passes**. It is also **not hypothetical**: it fired three times in this one project, and the released version of the library still has it |
| **Expected failure mode** | `"NA"` becomes `NaN`; `"NA" in index` → `False`; `.loc["NA"]` → `KeyError`; a downstream `notna()` filter silently removes the row. Numeric-coercion variant: `"9763"` becomes `"9763.0"`, so an identifier no longer matches its own source string and joins fail. **In all variants the row count is unchanged, so a count-based check reports health** |
| **Affected identity invariant** | **A key must survive ingest byte-exact and remain addressable.** AHOS side: the `UNKNOWN_VALUE = None` discipline (`architecture/providers/contracts.py:16`) and the contract law *"Missing or uncollected data is NEVER guessed"* (`:5`) — the converse must also hold: **present data must never be silently converted to unknown** |
| **Required test boundary** | **Unit — ingest/parsing only.** Assert: (1) all eleven NA-shaped symbols survive as **literal strings**; (2) each remains **addressable by key** (lookup succeeds, no `KeyError`); (3) **no key column is null** after parsing — an explicit post-parse assertion; (4) the two numeric-looking identifiers are **not** float-coerced (`"9763"` stays `"9763"`); (5) a reader configured with default NA inference **fails** this test — i.e. the fixture must be able to distinguish the two configurations, proving it has power; (6) nothing is dropped by any `notna()`-style filter, and if a filter exists it **logs what it discards**. **No** provider, network, scoring, decision authority, paper trading, runtime, soak or database-state involvement |
| **False-positive risk** | **LOW — the lowest in the queue.** Every assertion is deterministic and binary: either `"NA"` is addressable or it is not. The only risk is asserting on a *specific* reader configuration that AHOS legitimately does not use (e.g. if AHOS ingest is not pandas-based). **Mitigation: write assertions (1)-(4) and (6) against behaviour, not against a library API, so they hold for any reader.** Assertion (5) is the power check and must be retained |
| **False-negative risk** | **LOW-MEDIUM.** The eleven tokens are pandas' list; another reader may have a different or larger magic-string set, and a fixture covering only these eleven would miss it. **Mitigation: the fixture should additionally assert that the reader is configured to have NO implicit magic strings at all** (an explicit empty-NA-token declaration), which generalizes beyond any particular list |
| **Approval gate** | **Agent B — recommended first in the queue.** Gate questions: (a) which AHOS ingest paths read identifier-bearing text, and are they all in scope? (b) does an explicit post-parse null-key assertion already exist? If yes, this fixture **verifies** it; if no, the fixture **requests** it and must be routed as a design proposal; (c) confirm assertion (5) is acceptable as a negative control. **No legal review required — contains no third-party identifier values** |
| **Implementation authorized** | **NO** |

---

## 27.8 Third-party identifier handling in fixtures

Two source cases involve populated third-party identifiers. The queue adopts the following rules,
which Agent B should treat as binding on any implementation.

| Rule | Rationale |
|---|---|
| **CUSIP values are never embedded in a fixture** | CUSIP is an ABA registered mark, commercially administered, and document 19 §19.5 rates it the **highest** concrete legal exposure in the package |
| **FIGI values are replaced by a `figi_present` boolean** (FIX-02) | Preserves the structural point (identifier present on the wrong subset) without embedding Bloomberg-scheme values |
| **ISIN values in FIX-04 should be synthetic** — ISIN-shaped strings with a check digit computed from the public ISO 6166 specification | Removes the legal dependency entirely while keeping the fixture faithful. If real ISINs are used instead, **document 29 legal review is a precondition** |
| **Check-digit logic must be reimplemented from published specifications**, never copied from `validate_identifiers.py` | That file delegates to **`python-stdnum` (LGPL-2.1+)**, which is not permissive and conflicts with AHOS's `requirements.txt` law (F-CORR-01, KN-04) |
| **`python-stdnum` must not be added as a dependency, including as a test-only dependency** | Same conflict. A test-only install is still an install into the AHOS environment, which is prohibited by this pass's constraints |
| **Fixtures must not require the FinanceDatabase package, network access, or any mutable external source** | Document 20 §20.3 verified all three: fixtures are literal input records parsed by AHOS's own test code |
| **The attribution boundary (§27.0 preamble) must be reproduced in any implemented test module** | Prevents a future reader mistaking third-party data properties for AHOS production failures |

---

## 27.9 Queue summary

| Fixture | Threat model (one line) | Primary invariant | FP risk | FN risk | Approval gate | Authorized |
|---|---|---|---|---|---|---|
| **FIX-01** | Namespace collapse across asset classes | Key uniqueness is namespace-scoped | MEDIUM | LOW-MED | Agent B | **NO** |
| **FIX-02** | Corroboration inversion — identifier on the wrong subset | Contradictory corroboration is recorded, not resolved by preference | **HIGH** (domain assumption) | MEDIUM | Agent B + domain-mapping decision | **NO** |
| **FIX-03** | Bidirectional identity error from one input | Symbol is an alias, never an identity | MEDIUM | **LOW** | Agent B | **NO** |
| **FIX-04** | Hierarchy-level confusion | An identifier is a key at exactly one level | MED-HIGH | MEDIUM | Agent B **+ legal if real ISINs** | **NO** |
| **FIX-05** | Compound silent corruption + prose-vs-key inversion | Placeholder→unknown; authoritative field for jurisdiction; imputed→low confidence; key governs over prose | MEDIUM (gate 3 statistical) | MEDIUM | Agent B — highest scrutiny | **NO** |
| **FIX-06** | Silent key annihilation at the ingest boundary | A key survives ingest byte-exact and stays addressable | **LOW** | LOW-MED | Agent B | **NO** |

**Registered: 6. Implemented: 0. `Implementation authorized: NO` on all six.**

**Agent B attention flags — the three items that are not pure tests:**

1. **FIX-02** encodes a TradFi share-class hierarchy AHOS may not model. Port to the crypto domain
   (one token, conflicting chain reports, address present on only one) or mark as out-of-domain
   reference material.
2. **FIX-05** requires an `UNKNOWN`→`IdentityState` mapping decision, because `IdentityState`
   (`architecture/identity/types.py:14-20`) has **no `UNKNOWN` member**. The fixture must not invent
   one.
3. **FIX-03** assertion (4) and **FIX-06** assertion (3) may request capabilities AHOS does not
   currently guarantee (merge reversibility; explicit post-parse null-key assertion). Where a fixture
   requests a **feature** rather than verifying **behaviour**, it must be routed as a design proposal
   and must not be written as a failing test against current code.

**No AHOS file was created or modified by this document. No fixture data was committed. No server
was started. The 72-hour soak was not disturbed.**
