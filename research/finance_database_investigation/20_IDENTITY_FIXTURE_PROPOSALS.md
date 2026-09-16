# 20 — Identity Fixture Proposals

**Document 20 — Objective B.** Identity edge cases re-verified against actual source records, and
a proposed adversarial fixture specification for AHOS identity resolution.

> ## ⚠️ PROPOSED — NOT IMPLEMENTED
>
> **Every fixture in this document is a proposal. Nothing has been implemented.**
> `architecture/identity/resolution.py` was **not** read for modification and **not** changed. No
> AHOS file of any kind was modified. No test was added to `tests/` or `tests2b/`. No Lane A,
> Lane B, scoring, security, runtime, calibration or soak artifact was touched.
>
> **Implementation is NOT authorized.** See the authorization column in §20.4.

> ## ⚠️ Attribution boundary
>
> **None of these records is an AHOS production failure.** Every case below is a property of a
> *third-party dataset* (FinanceDatabase at commit `a174c97d3b`). They are proposed as **input
> fixtures** — adversarial test data — not as evidence that AHOS has ever mis-resolved anything.
> AHOS's crypto identity domain is `(chain, address)`; FinanceDatabase's TradFi domain is
> `symbol`. The two do not overlap, and nothing here claims otherwise.

---

## 20.1 Verification method

`evidence/scripts/f4_identity_fixtures.py` was executed against the pinned commit in the rebuilt
isolated environment. It pulls the **actual rows** for each reported case rather than restating
prose. Raw output: `evidence/followup/f4_identity.json`.

## 20.2 Case-by-case verification

### CASE 1 · `CHAD` cross-asset collision — **VERIFIED, exact records captured**

| Asset class | Verified record |
|---|---|
| `equities` | `symbol='CHAD'`, `name='DeFi Development Corp. Variable Rate Series C Perpetual Preferred Stock'`, `country='United States'`, `exchange='NMS'`, `mic='XNAS'`, `market='NASDAQ Global Select'`, `currency='USD'`, **`isin=''`, `cusip=''`, `figi=''`** |
| `etfs` | `symbol='CHAD'`, `name='Direxion Daily CSI 300 China A Share Bear 1X Shares'`, `exchange='PCX'`, `mic='ARCX'`, `currency='USD'`, **`isin=''`** |

**Exact ambiguity:** one symbol string denotes two unrelated instruments in two asset classes, with
**different MICs** (`XNAS` vs `ARCX`), and **no identifier on either side** to arbitrate.

**Census re-run:** `equities <-> etfs` is the **only** asset-class pair with any full-symbol
collision, and the collision set is exactly `{'CHAD'}` — **n = 1**. Confirmed independently by the
project's own test suite, which fails on this row (§22).

**Identity property:** *symbol is not a global key; blocking on symbol alone merges distinct
entities across schemas.*

**AHOS relevance: HIGH.** AHOS's `ProviderRouter.discover_candidates()` dedupes on
`(c.chain, c.address.lower())` — a **namespaced composite** key, which is precisely the discipline
this case shows is necessary. The fixture tests that AHOS's resolver never degrades to
symbol-only blocking. Note the irony worth recording: the equity side of `CHAD` is a
**crypto-adjacent** company (DeFi Development Corp.), so a hypothetical crypto↔TradFi bridge keyed
on symbol would collide on exactly the kind of entity it most wants to find.

### CASE 2 · `BRK-A` / `BRK/A` venue contradiction — **VERIFIED and EXPANDED (7 rows, 4 venues)**

The original report listed 5 rows. Re-execution found **7 Berkshire Hathaway rows** across **4
distinct venues**:

| `symbol` | `exchange` | `mic` | `market` | `currency` | `isin` | `cusip` | `figi` | `shareclass_figi` |
|---|---|---|---|---|---|---|---|---|
| `BRK-A` | `NYQ` | `XNYS` | New York Stock Exchange | USD | `''` | `''` | `''` | `''` |
| `BRK-B` | `NYQ` | `XNYS` | New York Stock Exchange | USD | `''` | `''` | `''` | `''` |
| `BRK/A` | **`ASE`** | **`XASE`** | **NYSE MKT** | USD | `''` | `''` | `''` | `''` |
| `BRK/B` | **`ASE`** | **`XASE`** | **NYSE MKT** | USD | `''` | `''` | `''` | `''` |
| `BRKA.VI` | `VIE` | `XWBO` | Vienna Stock Exchange | EUR | `''` | `''` | **`BBG00KTDTPS8`** | **`BBG001S902J2`** |
| `BRKB.MX` | `MEX` | `XMEX` | Mexico Stock Exchange | MXN | `''` | `''` | `''` | `''` |
| `BRKB.VI` | `VIE` | `XWBO` | Vienna Stock Exchange | EUR | `''` | `''` | **`BBG00KTDTPN3`** | **`BBG001S90346`** |

All seven have `name='Berkshire Hathaway Inc.'` and `country='United States'`.
`BRK_VENUE_CONTRADICTION = true` (`['ASE','MEX','NYQ','VIE']`). `BRK_all_isin_empty = true`.

**Exact ambiguity — three distinct defects in one case:**

1. **Symbol-convention duplication.** `BRK-A` and `BRK/A` are the *same share class* under two
   conventions, assigned **contradictory venues** (`NYQ`/`XNYS` vs `ASE`/`XASE`). Root cause is
   verified in the pipeline: `database_update.yml:175-176` assigns `exchange='ASE'`,
   `market='NYSE MKT'` wholesale to the NYSE feed, and `:185` `pd.concat`s three feeds without
   `keys=`.
2. **Identifier coverage is inverted.** The two **Vienna** listings carry `figi` and
   `shareclass_figi`; the four **US** listings — the primary ones — carry **nothing**. So
   identifier-based deduplication works for the secondary listings and **fails for the primary
   ones**.
3. **Currency divergence.** USD / EUR / MXN for one issuer, with no field indicating which is the
   primary listing.

**Identity property:** *the same entity can be represented by N records with mutually
contradictory attributes, and the identifier that could arbitrate is present on the wrong subset.*

**AHOS relevance: HIGH.** This is the canonical "corroborating sources disagree" case. AHOS's
`IdentityState.CONFLICT` exists exactly for it, and `IdentityResolution.conflicts: tuple[str, ...]`
is the field that should carry the disagreement. The fixture tests that AHOS **records** a conflict
rather than silently picking one.

### CASE 3 · `MMM` repeated ticker — **VERIFIED and EXPANDED (4 distinct entities, not 2)**

**18 rows**, `MMM_count = 18`. The original report named two entities (3M Company, Marley Spoon AG).
Re-execution shows **five distinct `name` values resolving to four unrelated entities**:

| `symbol` | `name` | `country` | `exchange` |
|---|---|---|---|
| `MMM` | 3M Company | United States | NYQ |
| `MMM.BA` `.BE` `.DE` `.DU` `.F` `.HA` `.HM` `.MU` `.MX` `.SN` `.SW` `.TI` `.VI` | 3M Company | United States | BUE BER GER DUS FRA HAN HAM MUN MEX SGO EBS TLO VIE |
| `MMM.SG` | **3M Co. Registered Shares DL -,0** | United States | STU |
| `MMM.AX` | **Marley Spoon AG** | **Germany** | ASX |
| `MMM.L` | **Mining, Minerals & Metals plc** | **United Kingdom** | LSE |
| `MMM.V` | **Minco Capital Corp.** | **Canada** | VAN |

**Exact ambiguity — three layers at once:**

1. **Multi-listing (legitimate):** 14 rows are the same entity (3M) on 14 venues.
2. **Name variant for the same entity:** `MMM.SG` is *"3M Co. Registered Shares DL -,0"* — the
   German registered-share naming convention for the **same** 3M. A resolver grouping on exact
   `name` would split 3M into two entities.
3. **Different entities sharing the ticker:** Marley Spoon AG (DE), Mining Minerals & Metals plc
   (UK), Minco Capital Corp. (CA) are **unrelated** to 3M and to each other. A resolver grouping on
   `symbol` prefix would merge four entities.

**Identity property:** *one bare ticker ⇒ {1 entity × N listings} ∪ {M unrelated entities}, with a
name variant inside the first set. Both over-merging and over-splitting are available from the
same input.*

**AHOS relevance: HIGH.** This is the sharpest available test of the distinction AHOS already
encodes between `TokenIdentity.symbol_alias` (an **alias**, explicitly non-authoritative) and
`TokenIdentity.address_canonical` (the **key**). The fixture asserts that a symbol is treated as an
alias and never as an identity.

**Context re-measured:** 112,690 equity rows → **74,690** distinct bare tickers; **16,251** bare
tickers appear more than once. Top fan-out: `MMM`×18, `AIR`×17, `HAL`×17, `SAP`×16, `AMD`×15,
`MRK`×15, `CTO`×14, `EMR`×14.

### CASE 4 · ISIN → many symbols — **VERIFIED, quantified**

| Metric | Value |
|---|---|
| Equity rows with a populated `isin` | **30,429** (**27.0%**) |
| Distinct ISINs | **9,406** |
| ISINs mapping to **more than one** symbol | **5,181** (**55.1%** of populated ISINs) |
| Maximum fan-out | **57** |

Top fan-out, exact records:

| ISIN | symbols | `name` | countries |
|---|---:|---|---|
| `FR0013269123` | **57** | Rubis | France |
| `US6934831099` | **47** | POSCO | South Korea |
| `AU000000BHP4` | **35** | BHP Group | Australia |
| `US9286625010` | **34** | Volkswagen AG | Germany |
| `FR0000120578` | **25** | Sanofi | **France, India** |

**Exact ambiguity:** an ISIN identifies a **share class**, not a listing. 57 symbols for one ISIN is
correct data modelling — but it means an ISIN cannot be used as a listing-level primary key, and
`FR0000120578` spanning two countries shows that even the country cannot be derived from it.
Combined with 73% of rows having **no** ISIN at all, the identifier is simultaneously
non-unique where present and absent most of the time.

**Identity property:** *a globally unique identifier at one level of the hierarchy is a one-to-many
key at another level. Choosing the wrong level silently multiplies or collapses entities.*

**AHOS relevance: MEDIUM–HIGH.** Directly analogous to AHOS's `token_id` vs `pair_id` distinction
(`TokenIdentity` vs `PoolIdentity`, with `PoolIdentity.belongs_to_token`). The fixture tests that
AHOS never treats a token-level identifier as a pool-level key or vice versa.

### CASE 5 · `two` placeholder records — **VERIFIED, and it proves the imputation mechanism**

**129 rows** with `name == 'two'`, spread across **29 exchange suffixes**
(`AQ AS AX BE BK BO CM CN DE DU F HA HM IL JO KQ L MU MX NS NZ SA SG ST SZ T TA TI VI`).

Every one of the 129 rows carries:

| Field | Value (zero variance) |
|---|---|
| `name` | `two` |
| `country` | **`United States`** |
| `sector` | **`Financials`** |
| `industry_group` | **`Diversified Financials`** |
| `industry` | **`Diversified Financial Services`** |
| `isin` | `''` |
| `currency` | **varies** — `CNY`, `KRW`, `USD`, `PLN`, `EUR`, … |

Sample verified records: `000851.SZ` (SHZ/XSHE, CNY), `002447.SZ` (SHZ/XSHE, CNY), `046110.KQ`
(KOE/XKOS, KRW), `0JUZ.L` (LSE/XLON, USD), `0OFR.IL` (IOB/XLON, PLN), `0YW.BE` (BER/XBER, EUR).

**NEW RESULT (FOLLOWUP-02) — this case empirically proves the `mode()` imputation.**
The original report established the *mechanism* from source (`database_update.yml:87` and `:113`,
`return subset['industry_group'].mode()[0] …`) but recorded cross-run confirmation as **UNKNOWN
(U-13)**. Re-execution closes that gap from the data side:

```
mode of industry_group within sector=='Financials'  ->  'Diversified Financials'
mode of industry      within that subset            ->  'Diversified Financial Services'
```

The 129 `two` rows carry **exactly the modes**, with **zero variance** across 129 records spanning
29 venues, 5+ currencies and (per `country`) a single wrong value. Statistical imputation is the
only mechanism that produces identical classification for 129 unrelated listings on four
continents. **The imputation did not merely exist in the code — it fired, and this is its
fingerprint.**

**Exact ambiguity:** a corrupted placeholder `name`, a `country` that is wrong for essentially all
129 rows (Shenzhen, KOSPI, London, Berlin listings labelled `United States`), and a classification
that is **imputed rather than observed** with no field marking it as such.

**Identity property:** *an entity can be simultaneously unnameable, mis-jurisdictioned and
mis-classified, with every defect invisible because no confidence or provenance field exists.*

**AHOS relevance: HIGH** — and the highest of the five, because it is a **compound** failure. It
tests three independent AHOS disciplines at once: `UNKNOWN` for a placeholder name, MIC-derived
(not `country`-derived) jurisdiction, and `confidence=LOW` for imputed classification.

**Additional verified context:** `name` value counts across equities — `''` **1,116**, `ISHARES`
**257**, `two` **129**, `Rubis` **57**, `Credit Agricole S.A.` **48**. Lowercase-duplicate names:
**47,578**. Symbols containing whitespace: **19** (e.g. `'ECC           '` with 11 trailing
spaces, `'AUS B.ST'`, `'BQI RT WI'`).

**Whitespace census — a discrepancy, registered honestly.** The original report stated *1,774 names
with trailing whitespace*. That figure **does not reproduce** under any definition tested:

| Scope | Definition | Measured |
|---|---|---:|
| equities only | trailing | **658** |
| equities only | leading **or** trailing | **665** |
| all 7 asset classes | trailing | **11,933** |
| all 7 asset classes | leading **or** trailing | **11,956** |

Per class (trailing): equities 658 · etfs 38 · funds 1,563 · indices **9,655** · currencies 0 ·
cryptos 0 · money markets 19.

**Classification: UNREPRODUCED.** The original figure `1,774` is **withdrawn**. The *phenomenon* is
confirmed and is in fact **far larger** than reported (11,933 across all classes; indices alone has
9,655). No load-bearing conclusion depended on `1,774`, but the correction is recorded rather than
silently dropped — see document 25, corrections register.

## 20.3 Can these be safely represented as AHOS adversarial fixtures?

| Property | Assessment |
|---|---|
| Are the records real and citable? | **Yes** — pinned to commit `a174c97d3b`, with file/line for the `NA`-adjacent cases and exact row content for all five |
| Are they reproducible? | **Yes** — `f4_identity_fixtures.py` regenerates them offline from the pinned artifact |
| Do they contain proprietary data? | **Partially** — they contain CUSIP/FIGI/ISIN *values* in some rows. **The fixtures below deliberately exclude all identifier values except ISIN/FIGI where structurally necessary, and include no CUSIP.** See the legal caveat |
| Do they require the FinanceDatabase package? | **No** — fixtures are literal input records, parsed by AHOS's own test code |
| Do they require network access? | **No** |
| Do they touch a protected AHOS surface? | **No** — they would live in a test fixture directory, consumed by new tests, and assert on **existing** behaviour |
| Could they be mistaken for AHOS production failures? | **Only if mislabelled** — hence the attribution boundary at the top of this document, which must be carried into any implementation |

**Legal caveat (carried from document 19 §19.5).** Two of the five cases involve rows whose
`figi`/`shareclass_figi` values are populated (CASE 2). FIGI is a Bloomberg identifier scheme. The
proposed fixtures therefore **include only the fields structurally required to reproduce the
ambiguity** (`symbol`, `name`, `country`, `exchange`, `mic`, `currency`, and a boolean
`figi_present` flag **instead of the FIGI value**). This keeps the fixture faithful while avoiding
embedding third-party identifier values in the AHOS tree. **Legal review is still required before
any fixture containing identifier values is committed** — flagged in §20.4.

## 20.4 Proposed fixture specification

> **All entries: `PROPOSED — NOT IMPLEMENTED`. Implementation authorized: NO.**

---

### FIX-01 · Cross-schema symbol collision

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-01-CROSS-SCHEMA-SYMBOL-COLLISION` |
| **Source case** | CASE 1 — `CHAD`, FinanceDatabase @ `a174c97d3b` |
| **Input records** | R1: `{asset_class:"equities", symbol:"CHAD", name:"DeFi Development Corp. Variable Rate Series C Perpetual Preferred Stock", country:"United States", exchange:"NMS", mic:"XNAS", currency:"USD", isin:null, cusip:null, figi:null}`<br>R2: `{asset_class:"etfs", symbol:"CHAD", name:"Direxion Daily CSI 300 China A Share Bear 1X Shares", exchange:"PCX", mic:"ARCX", currency:"USD", isin:null}` |
| **Expected resolution behaviour** | R1 and R2 resolve to **two distinct entities**. Symbol-only blocking must **not** merge them. If a caller requests resolution by `symbol="CHAD"` without an asset class, the resolver must return **both** candidates, not one |
| **Expected safety behaviour** | State = **`CONFLICT`** when queried by bare symbol; **`VERIFIED`** for each record when queried with `(asset_class, symbol)`. Never silently pick one. The conflict must be recorded in `IdentityResolution.conflicts` with both candidates enumerated |
| **Rationale** | Tests that AHOS's namespaced composite key discipline (`(chain, address)`) generalizes: a symbol is a key only **within** a namespace. Also the exact defect that makes the upstream project's own invariant test fail (§22) |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `CHAD`, `cross_asset_symbol_collisions`; `evidence/scripts/f4_identity_fixtures.py`; document 13 S-01; document 22 (pytest reproduction) |
| **Implementation authorized?** | **NO — PROPOSED** |

---

### FIX-02 · Same entity, contradictory venues, identifiers on the wrong subset

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-02-VENUE-CONTRADICTION-INVERTED-IDENTIFIERS` |
| **Source case** | CASE 2 — Berkshire Hathaway, 7 rows / 4 venues |
| **Input records** | 7 records, `name="Berkshire Hathaway Inc."`, `country="United States"` throughout:<br>`{symbol:"BRK-A", exchange:"NYQ", mic:"XNYS", currency:"USD", figi_present:false}`<br>`{symbol:"BRK-B", exchange:"NYQ", mic:"XNYS", currency:"USD", figi_present:false}`<br>`{symbol:"BRK/A", exchange:"ASE", mic:"XASE", currency:"USD", figi_present:false}`<br>`{symbol:"BRK/B", exchange:"ASE", mic:"XASE", currency:"USD", figi_present:false}`<br>`{symbol:"BRKA.VI", exchange:"VIE", mic:"XWBO", currency:"EUR", figi_present:true}`<br>`{symbol:"BRKB.MX", exchange:"MEX", mic:"XMEX", currency:"MXN", figi_present:false}`<br>`{symbol:"BRKB.VI", exchange:"VIE", mic:"XWBO", currency:"EUR", figi_present:true}`<br>**Note:** FIGI *values* are replaced by a `figi_present` boolean — see the legal caveat in §20.3 |
| **Expected resolution behaviour** | Recognize **two share classes** (A and B) across 7 listings. `BRK-A` ≡ `BRK/A` and `BRK-B` ≡ `BRK/B` must be flagged as **candidate duplicates**, not accepted as distinct entities and not silently merged |
| **Expected safety behaviour** | State = **`CONFLICT`** on `exchange`/`mic` for the A and B pairs (`XNYS` vs `XASE`). The conflict must be **enumerated**, with both venue values preserved. Identifier-based deduplication must be reported as **unavailable for the primary listings** (`figi_present:false` on all four US rows) rather than assumed successful. Currency divergence (USD/EUR/MXN) must not be averaged or first-picked |
| **Rationale** | The hardest realistic case: the corroborating identifier exists **only on the secondary listings**. A resolver that trusts "identifier present ⇒ resolved" will resolve the Vienna rows and silently leave the New York rows ambiguous. Tests that AHOS reports *coverage*, not just *success* |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `BRK_all_rows`, `BRK_berkshire_rows`, `BRK_distinct_exchanges`, `BRK_all_isin_empty`; root cause `database_update.yml:175-176,185` (document 03 DP-01/DP-02); document 13 S-07/S-12 |
| **Implementation authorized?** | **NO — PROPOSED** |

---

### FIX-03 · Bare ticker spanning four unrelated entities plus a name variant

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-03-BARE-TICKER-MULTI-ENTITY-PLUS-NAME-VARIANT` |
| **Source case** | CASE 3 — `MMM`, 18 rows / 4 entities / 5 name strings |
| **Input records** | 18 records. Four entity clusters:<br>**E1** (14 rows) `name="3M Company"`, `country="United States"`, symbols `MMM`, `MMM.BA`, `MMM.BE`, `MMM.DE`, `MMM.DU`, `MMM.F`, `MMM.HA`, `MMM.HM`, `MMM.MU`, `MMM.MX`, `MMM.SN`, `MMM.SW`, `MMM.TI`, `MMM.VI`<br>**E1-variant** (1 row) `symbol="MMM.SG"`, `name="3M Co. Registered Shares DL -,0"`, `country="United States"`, `exchange="STU"`<br>**E2** `symbol="MMM.AX"`, `name="Marley Spoon AG"`, `country="Germany"`, `exchange="ASX"`<br>**E3** `symbol="MMM.L"`, `name="Mining, Minerals & Metals plc"`, `country="United Kingdom"`, `exchange="LSE"`<br>**E4** `symbol="MMM.V"`, `name="Minco Capital Corp."`, `country="Canada"`, `exchange="VAN"` |
| **Expected resolution behaviour** | Resolve to **four** entities, not one and not five. `MMM.SG` must attach to **E1** despite the differing `name` (it is the German registered-share convention for 3M). E2/E3/E4 must **not** merge with E1 despite the shared bare ticker |
| **Expected safety behaviour** | Grouping on exact `name` → **over-splits** E1 (must be detected and reported). Grouping on bare `symbol` → **over-merges** all four (must be rejected). Any merge performed without an identifier must carry `confidence=LOW` and be reversible. No `keep="first"`-style positional tie-breaking |
| **Rationale** | The only case in the set that offers **both** failure directions from one input. Directly tests AHOS's existing separation of `TokenIdentity.symbol_alias` (alias, non-authoritative) from `address_canonical` (key). A resolver that passes this cannot be treating symbol as canonical identity |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `MMM_rows`, `MMM_count`, `MMM_distinct_names`, `top_repeated_bare_tickers`, `distinct_bare_tickers` (74,690), `bare_tickers_appearing_more_than_once` (16,251); document 13 S-02 |
| **Implementation authorized?** | **NO — PROPOSED** |

---

### FIX-04 · Identifier valid at one hierarchy level, one-to-many at another

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-04-IDENTIFIER-LEVEL-CONFUSION` |
| **Source case** | CASE 4 — ISIN fan-out, max 57 |
| **Input records** | Two sub-cases.<br>**F4a (extreme fan-out):** `isin="FR0013269123"`, `name="Rubis"`, `country="France"`, with **57** distinct `symbol` values (a representative subset of ≥8 may be used, e.g. the Paris, Brussels, Amsterdam and German venue listings).<br>**F4b (cross-country fan-out):** `isin="FR0000120578"`, `name="Sanofi"`, **25** symbols, `country ∈ {"France","India"}`.<br>**F4c (coverage control):** the same issuer with `isin=null` on the majority of listings, mirroring the measured 27.0% population rate |
| **Expected resolution behaviour** | All symbols in F4a resolve to **one share-class entity** with **many listings**. The resolver must not create 57 entities, and must not collapse the listings into one |
| **Expected safety behaviour** | Using an ISIN as a **listing-level** key must be rejected. In F4b, `country` must **not** be inferred from the ISIN (two countries share it). In F4c, absent identifiers must yield **`UNKNOWN`**, never a guess and never a silent skip. Any aggregation over listings must state its grouping level explicitly |
| **Rationale** | Directly analogous to AHOS's `token_id` vs `pair_id` split (`TokenIdentity` vs `PoolIdentity.belongs_to_token`). Tests that a globally unique identifier at level *N* is never used as a key at level *N+1* |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `ISIN_max_fanout` (57), `ISIN_distinct` (9,406), `ISIN_populated_rows` (30,429), `ISIN_populated_pct` (27.0), `ISIN_fanout_gt_1` (5,181), `ISIN_top_fanout`; document 04 SC-03; document 13 S-02 |
| **Implementation authorized?** | **NO — PROPOSED** |

---

### FIX-05 · Compound failure: placeholder name + wrong jurisdiction + imputed classification

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-05-COMPOUND-PLACEHOLDER-JURISDICTION-IMPUTATION` |
| **Source case** | CASE 5 — `two`, 129 rows / 29 venue suffixes |
| **Input records** | A representative subset of ≥6 of the 129, all with `name="two"`, `country="United States"`, `sector="Financials"`, `industry_group="Diversified Financials"`, `industry="Diversified Financial Services"`, `isin=null`:<br>`{symbol:"000851.SZ", exchange:"SHZ", mic:"XSHE", currency:"CNY"}`<br>`{symbol:"002447.SZ", exchange:"SHZ", mic:"XSHE", currency:"CNY"}`<br>`{symbol:"046110.KQ", exchange:"KOE", mic:"XKOS", currency:"KRW"}`<br>`{symbol:"0JUZ.L",   exchange:"LSE", mic:"XLON", currency:"USD"}`<br>`{symbol:"0OFR.IL",  exchange:"IOB", mic:"XLON", currency:"PLN"}`<br>`{symbol:"0YW.BE",   exchange:"BER", mic:"XBER", currency:"EUR"}`<br>**Plus the sibling case from document 08:** `{symbol:"SOL1-CAD", cryptocurrency:"SOL1", name:"Solana CAD", summary:"Solana (SOL) is a cryptocurrency."}` — where the **key says `SOL1` and the prose says `SOL`** |
| **Expected resolution behaviour** | `name="two"` must resolve to **`UNKNOWN`**, not to an entity named "two", and must not be used to group the 129 rows into one entity. Jurisdiction must be derived from **`mic`** (`XSHE`→CN, `XKOS`→KR, `XLON`→GB, `XBER`→DE), **never** from `country="United States"`. Classification must be marked `confidence=LOW` / `provenance=INFERRED_UNKNOWN` |
| **Expected safety behaviour** | Three independent gates must each fire: (1) placeholder-name rejection; (2) `country` vs `mic` contradiction detection; (3) zero-variance classification across unrelated records detected as an **imputation signature**. Where `summary` and the identity key disagree (`SOL` vs `SOL1`), the **key** governs identity and the prose is treated as untrusted text — never the reverse. No record may be emitted as actionable |
| **Rationale** | The highest-value fixture: one input tests three separate AHOS disciplines simultaneously, and the zero-variance signature is *empirically proven* to be statistical imputation (§20.2 CASE 5, FOLLOWUP-02) rather than merely suspected. The `SOL1`/`SOL` sibling additionally tests prose-vs-key precedence, which is the exact trap in the crypto table |
| **Evidence reference** | `evidence/followup/f4_identity.json` → `TWO_rows`, `TWO_count` (129), `TWO_distinct_countries`, `TWO_symbol_suffixes` (29); `evidence/followup/f1_objective_a.json` → `sample_fdb_cryptos_row`; imputation mechanism `database_update.yml:87,113`; document 13 S-08/S-09/S-11; document 08 |
| **Implementation authorized?** | **NO — PROPOSED** |

---

### FIX-06 · (new) NA-coercion key loss — proposed as a result of Objective C

| Field | Value |
|---|---|
| **Fixture ID** | `FIX-06-NA-COERCION-KEY-LOSS` |
| **Source case** | Objective C — the `NA` ticker regression, verified in document 21 |
| **Input records** | `{symbol:"NA", name:"Nano Labs Ltd Class A Ordinary Shares", country:"China", exchange:"NMS", mic:"XNAS", market:"NASDAQ Global Select", currency:"USD", sector:"Information Technology", isin:null}` — the exact record at `database/equities/NMS.csv:4346`<br>**Plus the adversarial siblings** from the pandas default-NA list: `N/A`, `NULL`, `NaN`, `None`, `nan`, `null`, `<NA>`, `#N/A`, `-nan`, `1.#IND` |
| **Expected resolution behaviour** | All eleven symbols must survive ingest as **literal strings** and remain **addressable by key**. `"NA"` must be retrievable by lookup, must not become `NaN`, and must not be dropped by any `notna()`-style filter |
| **Expected safety behaviour** | Ingest must use explicit `keep_default_na=False, na_values=[""]` (or a strict-typed reader) and must **assert** that no index/key value is null after parsing. A key that cannot be addressed must raise or be reported — never be silently retained as an unaddressable row. Numeric-looking identifiers must not be float-coerced (`"9763"` must not become `"9763.0"`) |
| **Rationale** | This is the one case where an upstream **code** defect (release 2.4.0's loader) produces a **data** defect (an unaddressable record) with **no error at any layer**. AHOS's own ingest must be provably immune. Cheap to test, high consequence if missed |
| **Evidence reference** | `evidence/followup/f3_na_regression.json` → `C4_source_records_with_symbol_NA`, `C5_release_index_nan_count`, `C5_release_NA_in_index`, `C6_main_loc_NA`; document 21; document 13 S-13/S-19 |
| **Implementation authorized?** | **NO — PROPOSED** |

## 20.5 Summary

| Fixture | Source case | Identity property tested | AHOS relevance | Status |
|---|---|---|---|---|
| **FIX-01** | `CHAD` | symbol is not a global key | HIGH | **PROPOSED — NOT IMPLEMENTED** |
| **FIX-02** | Berkshire ×7 | contradictory corroboration; identifiers on the wrong subset | HIGH | **PROPOSED — NOT IMPLEMENTED** |
| **FIX-03** | `MMM` ×18 | over-merge *and* over-split from one input | HIGH | **PROPOSED — NOT IMPLEMENTED** |
| **FIX-04** | ISIN →57 | identifier level confusion | MEDIUM–HIGH | **PROPOSED — NOT IMPLEMENTED** |
| **FIX-05** | `two` ×129 (+`SOL1`) | compound: placeholder + jurisdiction + imputation + prose-vs-key | **HIGHEST** | **PROPOSED — NOT IMPLEMENTED** |
| **FIX-06** | `NA` ticker | NA-coercion key loss (new, from Objective C) | HIGH | **PROPOSED — NOT IMPLEMENTED** |

**All five originally-reported identity cases are VERIFIED.** Two are **expanded** by re-execution
(CASE 2: 5 → **7** rows, 4 venues; CASE 3: 2 → **4** entities). One original supporting figure is
**withdrawn** (trailing-whitespace 1,774 → not reproducible; the true all-class figure is 11,933).
One **new** fixture (FIX-06) is proposed as a by-product of Objective C.

**No AHOS file was created or modified by this document. Implementation is NOT authorized.**
