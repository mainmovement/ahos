# 05 — Identity and Entity Resolution Audit

**Phase 5.** The tasking flags this as high priority for AHOS. It is the single most
consequential part of this investigation: FinanceDatabase's identity model is **listing-symbol
centric with partial external identifiers and no issuer entity**, which is structurally
incompatible with AHOS's `TokenIdentity ≠ PoolIdentity ≠ ChainIdentity` model.

All measurements are from `compression/*.bz2` at commit `a174c97d`, executed 2026-09-15.
Scripts: `evidence/scripts/a4_identity.py`, `a5_verify.py`, `a9_rest.py`, `a10_final.py`.

---

## 5.1 Does FinanceDatabase distinguish these concepts?

| Concept | Modelled? | How | Evidence |
|---|---|---|---|
| **Issuer / company** | **No — not as an entity.** Approximated only by the free-text `name` column | `name` | 47,578 lowercase-duplicate names; 257 rows named `ISHARES`; 129 named `two`. No `issuer_id`, no `parent_company`, no `cik` |
| **Company** | No | — | No column |
| **Security** | **Partially**, via `composite_figi` (54.0% populated, 41,131 unique) and `shareclass_figi` (56.8%, 29,164 unique) | FIGI hierarchy | Semantics are correct — a composite FIGI does identify one security across listings — but coverage is barely over half |
| **Instrument** | **Partially**, via `figi` (52.0% populated, **58,232 unique of 58,556** ⇒ only 324 dups) | `figi` | The strongest listing-level key present |
| **Listing** | **Yes — this is the unit of the table.** One row = one symbol = one listing on one venue | row identity | 112,690 equity rows; 16,251 bare tickers appear more than once |
| **Symbol** | **Yes — it is the primary key** (DataFrame index after `index_col=0`) | index | Unique within each asset class (0 duplicates measured); **not unique across classes** (`CHAD`) |
| **Exchange** | Yes, as a project-local code (84 distinct) **and** an ISO 10383 MIC (71 distinct) | `exchange`, `mic` | `exchange → mic` is strictly 1:1 (0 violations). `mic → exchange` has **4 violations**: `OTCM`→7 codes, `XNAS`→3, `XLON`→2, `XNSE`→2. 3 exchange codes have no MIC |
| **Market** | Weakly — a long name whose semantics vary by row | `market` | Hardcoded `NASDAQ Global Select` for all 7,058 `NMS` rows and `NYSE MKT` for all 1,128 `ASE` rows; elsewhere it is the exchange's name (`Shenzhen Stock Exchange`) |
| **Country** | Yes, but it is the **issuer/HQ country, not the listing jurisdiction** | `country` | 19,413 of 29,984 `United States` rows trade on non-US venues. Confirmed by the workflow's own comment (`database_update.yml:506-507`) |
| **ISIN** | Column present, **27.0% populated** | `isin` | Checksum-valid where present (validator: 0 ISIN findings) |
| **CUSIP** | Column present, **24.2% populated** | `cusip` | 2 checksum mismatches (`QVCGB`, `KMGH`) |
| **FIGI** | Columns present (3 levels), **52–57% populated** | `figi`, `composite_figi`, `shareclass_figi` | Checksum-valid where present (validator: 0 FIGI findings) |
| Other identifiers | **None.** No `cik`, no `sedol`, no `lei`, no `ticker_id`, no `contract_address`, no `chain` | — | CONTRIBUTING:101 lists "Adding ISIN, CIK, FIGI, CUSIP, SEDOL and more" as an *aspiration* |

## 5.2 Direct answers to the eleven questions

**1. Is there a canonical instrument ID?**
**No.** The de facto key is the `symbol` string, which is a *listing-level*, venue-specific,
Yahoo-convention ticker. The closest thing to a canonical instrument ID is `figi` — but it is
absent for 48.0% of equities, absent for 78.3% of ETFs (which only have `isin`), and **absent
entirely from five of the seven asset classes**. There is no synthetic internal ID, no UUID, no
stable surrogate key. Nothing in the schema is guaranteed to identify an instrument.

**2. Is `symbol` globally unique?**
**No.** It is unique *within* each asset class (measured: 0 duplicates in all seven), but it is
**not unique across asset classes**, and the project knows it:

```
FAILED tests/test_invariants.py::test_no_symbol_collisions_across_asset_classes
E   AssertionError: Symbols appear in more than one asset-class file:
E       equities <-> etfs: ['CHAD'] (1 total)
```

That is our own execution of the project's own suite at HEAD. The colliding rows:

| asset | symbol | name | exchange | isin |
|---|---|---|---|---|
| equities | `CHAD` | DeFi Development Corp. Variable Rate Series C Perpetual Preferred Stock | `NMS` (NASDAQ Global Select) | *(empty)* |
| etfs | `CHAD` | Direxion Daily CSI 300 China A Share Bear 1X Shares | `PCX` | *(empty)* |

Two unrelated instruments, same symbol, both live on `main`, neither carrying an identifier that
could disambiguate them. The invariant test that exists to prevent exactly this **is failing**.

**3. Can the same symbol represent multiple instruments?**
**Yes, demonstrably, in three distinct ways:**

- **Across asset classes:** `CHAD` (above).
- **Across the bare ticker within equities:** 16,251 bare tickers appear more than once among
  74,690 distinct bare tickers (112,690 rows). Some are the *same* company multi-listed; some
  are *different* companies:

  | bare ticker | symbol | name | country | exchange |
  |---|---|---|---|---|
  | `MMM` | `MMM` | **3M Company** | United States | `NYQ` |
  | `MMM` | `MMM.AX` | **Marley Spoon AG** | Germany | `ASX` |
  | `MMM` | `MMM.BA`/`.BE`/`.DE`/`.DU`/`.F`/`.HA` | 3M Company | United States | various |

  `MMM` has **18 listings**, at least one of which is a completely different company.

- **Across asset classes at the token level:** 86 of 351 crypto token tickers (**24.5%**) are
  also equity symbols:

  | token ticker | crypto meaning | equity meaning |
  |---|---|---|
  | `META` | **Metadium** (10 rows) | **Meta Platforms Inc Class A** (`NMS`) |
  | `GO` | **GoChain** | **Grocery Outlet Holding Corp.** (`NMS`) |
  | `COMP` | Compound (2 rows) | — |
  | `ETH`, `BCH`, `DASH`, `EOS`, `BAND`, `CEL`, `FET`, `FUN`, `GAME`, `ENJ`, `LINK`, `MATIC`, `ACT`, `ADX`, `AR`, `AVA`, `BNT`, `CRU`, `ETN`, `FCT`, `FRST`, `GRC` … | various tokens | various listed companies |

  The cross-asset collision test compares full symbols (`META-CAD` vs `META`), so **it cannot
  catch this class of collision at all.** An AHOS join on a bare ticker would silently merge a
  token with a listed company.

**4. Can one instrument have multiple listings?**
**Yes — this is the dominant structure of the dataset.** 112,690 rows resolve to 74,690
distinct bare tickers. One ISIN maps to as many as **57** symbols:

| ISIN | distinct symbols | entity |
|---|---:|---|
| `FR0013269123` | **57** | Rubis |
| `US6934831099` | 47 | — |
| `AU000000BHP4` | 35 | BHP |
| `US9286625010` | 34 | — |
| `FR0000120578` | 25 | — |
| `DE0007164600` | 24 | — |

The FIGI hierarchy models this correctly *where populated*: `figi` is near-unique per row
(listing), `composite_figi` groups listings of one security (41,131 unique over 60,892 rows),
`shareclass_figi` groups share classes (29,164 unique over 63,990 rows).

**5. Can one company have multiple securities?**
**Yes.** `shareclass_figi` (29,164 unique) vs `composite_figi` (41,131 unique) vs `figi`
(58,232 unique) is a genuine three-level structure. But **there is no company/issuer node**:
the only aggregation above share class is the free-text `name`. Top repeated names:

| `name` | rows |
|---|---:|
| `ISHARES` | **257** |
| `two` | **129** |
| `Rubis` | 57 |
| `Credit Agricole S.A.` | 48 |
| `POSCO` | 47 |
| `CHS Inc.` | 44 |

`ISHARES` (257 rows) is a *brand*, not a company; `two` (129 rows) is corruption. **`name`
cannot serve as an issuer key.**

**6. Are duplicate records possible?**
**Yes, and they exist.** Beyond `CHAD`, the Berkshire Hathaway case shows *the same share class
recorded twice under two symbol conventions, on two different exchanges*:

| symbol | name | exchange | country | isin |
|---|---|---|---|---|
| `BRK-A` | Berkshire Hathaway Inc. | `NYQ` | United States | *(empty)* |
| `BRK/A` | Berkshire Hathaway Inc. | **`ASE`** | United States | *(empty)* |
| `BRK-B` | Berkshire Hathaway Inc. | `NYQ` | United States | *(empty)* |
| `BRK/B` | Berkshire Hathaway Inc. | **`ASE`** | United States | *(empty)* |
| `BRKA.VI` | Berkshire Hathaway Inc. | `VIE` | United States | *(empty)* |
| `BRK.AX` | **Brookside Energy Limited** | `ASX` | **Australia** | *(empty)* |
| `BRK.L` | **Brooks Macdonald Group plc** | `LSE` | **United Kingdom** | *(empty)* |

Four rows (`BRK-A`, `BRK/A`, `BRK-B`, `BRK/B`) represent two share classes with **conflicting
exchange attribution** (`NYQ` vs `ASE`), and **none of them carries an ISIN, CUSIP or FIGI** —
the identifiers that would resolve the duplication are missing exactly where they are needed.
The `/`-form rows also carry the hardcoded `ASE`/`NYSE MKT` values from §3.4.1, which is how
they were created.

**7. How are conflicts resolved?**
**Silently, by position.** `database_update.yml:260`:
```python
equities = equities[~equities.index.duplicated(keep='first')]
```
`keep='first'` on a frame assembled from `sorted(glob.glob('database/equities/*.csv'))` — so the
survivor is determined by **exchange-code filename sort order**, not by data quality, recency,
identifier completeness or venue primacy. There is no conflict record, no warning, no log line,
no `IdentityState.CONFLICT` analogue. The losing row simply ceases to exist.

**8. Are identifiers validated?**
**Yes — genuinely, and well, but only on `main` and only in CI/PR context.**
`financedatabase/validation/validate_identifiers.py` (533 lines, **[MAIN] only, absent from
release 2.4.0**) implements ISO 6166 ISIN check digits, CUSIP check digits, OpenFIGI check
digits, and US/CA ISIN↔CUSIP embedding consistency, with deterministic-only repair and
`actionable` vs `review-only` classification.

**We executed it** against the project's own `database/` tree (read-only):

```
Checked 249085 populated identifiers and 14804 US/Canadian ISIN-CUSIP pairs in 137 CSV files;
found 2 invalid values (0 repairable, 0 removable, 2 review-only) and 0 consistency issues.
```

| file | line | symbol | field | value | problem | actionable |
|---|---:|---|---|---|---|---|
| `database/equities/NMS.csv` | 5316 | `QVCGB` | cusip | `74915L301` | checksum mismatch | False |
| `database/equities/PNK.csv` | 5982 | `KMGH` | cusip | `483325109` | checksum mismatch | False |

**99.9992% of populated identifiers are internally valid.** The identifier problem is
**coverage, not correctness**. This distinction matters: it means the identifiers that *do*
exist can be trusted as checksums, while their *absence* (48–76% of rows) is the binding
constraint.

However: `testing.yml:34` **deselects** `test_database_identifiers_have_no_actionable_issues`
from the main test job into a separate `validate-identifiers` job, and when we ran it directly
it passed with a `UserWarning` about the 2 review-only findings. So it is a warn-not-fail gate.

**9. Are identifiers missing?**
**Massively.**

| Field | Populated | % | Unique | Duplicate values |
|---|---:|---:|---:|---:|
| `isin` (equities) | 30,429 | 27.0% | 9,406 | 21,023 |
| `cusip` (equities) | 27,286 | 24.2% | 12,946 | 14,340 |
| `figi` (equities) | 58,556 | 52.0% | 58,232 | 324 |
| `composite_figi` | 60,892 | 54.0% | 41,131 | 19,761 |
| `shareclass_figi` | 63,990 | 56.8% | 29,164 | 34,826 |
| `isin` (ETFs) | 7,932 | 21.7% | — | — |
| any identifier (funds / indices / currencies / cryptos / money markets) | **0** | **0%** | — | — |

And structurally: **every ticker discovered by the automated pipeline has all five identifiers
empty and is never revisited** (§3.4.2 DP-05). Measured footprint: **7,425 equity rows (6.59%)**
have `isin`, `cusip`, `figi` **and** `summary` all empty simultaneously — the pipeline's
signature.

**10. Are identifiers stable across updates?**
**Unverifiable from the data — and that is the answer.** There is no versioning, no history
table, no `valid_from`/`valid_to`, no change log. The only audit trail is the git history of
`database/*.csv` in a ~4.85 GB repository. Symbols are reused as keys; if an upstream feed
renames a symbol, the old row is not marked — it simply stops being touched (and, because of
DP-03, is never updated again). `delisted` is the *only* lifecycle flag and exists for equities
only. Status: **UNKNOWN** (U-15) for cross-version identifier stability; we did not diff two
historical snapshots.

**11. Does the package model issuer identity separately from listing identity?**
**No.** There is no issuer table, no issuer ID, and no issuer-level record. The row *is* the
listing. Issuer grouping is only *implicit*, recoverable — partially — through
`shareclass_figi` → `composite_figi` (57%/54% coverage) or by string-matching `name`
(unreliable, §5.1). For five of seven asset classes there is **no issuer concept whatsoever**.

## 5.3 Duplicate and ambiguity risk register

| Risk | Measured magnitude | Mechanism |
|---|---:|---|
| Same symbol, two asset classes | **1 live** (`CHAD`) | No cross-asset uniqueness enforcement at write time; the test that checks it does not run on data commits |
| Same bare ticker, different companies | **≥16,251 bare tickers** appear >1×; `MMM`→3M vs Marley Spoon; `BRK`→Berkshire vs Brookside Energy vs Brooks Macdonald | Multi-venue symbol conventions |
| Same share class, two rows, conflicting exchange | `BRK-A`/`BRK/A`, `BRK-B`/`BRK/B` | Two symbol conventions ingested from the same upstream feed and assigned different hardcoded exchange codes |
| Same ISIN, many symbols | up to **57** symbols per ISIN | Correct for multi-listing — **fatal if `isin` is treated as a primary key** |
| Same MIC, many exchange codes | up to **7** (`OTCM`) | MIC is coarser than the project's exchange code |
| Crypto token ticker = equity symbol | **86 / 351 (24.5%)** | Different namespaces, no disambiguation |
| Token ticker is a Yahoo collision suffix | **26** (`SOL1`, `DOT1`, `UNI3`, `LUNA1`, `ATOM1`, `COMP1`, `BTC2`, `GRT2`, `HNT1`, `STX1`, `MTC2`, `NLC2`, `ONE2`, `SCC3`, `VAL1`, `XNS1`, `AMP1`, `BTT1`, `CMT1`, `CTC1`, `DNA1`, `EMC2`, `GCC1`, `GHOST1`, `SONO1`) | The suffix is part of Yahoo's symbol, not the token's ticker. **`COMP1` is CompoundCoin, not Compound** (which is `COMP`) |
| `symbol` field holds an ISIN string | **503 of 1,356** `.VI` rows | Vienna rows mix local codes (`1COV.VI`) with ISIN-derived strings (`AT0000A288S5.VI`) |
| Duplicate free-text names | **47,578** lowercase duplicates | `name` is the only issuer proxy |
| Whitespace-damaged keys | 4 symbols with lead/trail space, **19 with internal spaces** (`'ECC           '`) | No normalization or trimming anywhere in the pipeline |
| Placeholder names | 129 rows named `two`, 257 named `ISHARES` | Uncurated bulk import |

## 5.4 The `only_primary_listing` heuristic — a false friend

There is **no `is_primary` field**. `Equities.py:208-211` (and `:112-117` in `search`)
approximates it syntactically:

```python
only = equities[~equities.index.str.contains(r"\.", na=False)]
```

Measured consequences:

| Scope | Rows before | Rows after | Dropped |
|---|---:|---:|---:|
| `select(country="China", only_primary_listing=True, exclude_delisted=False)` | 6,961 | **866** | **6,095 (87.6%)** |
| `select(only_primary_listing=True)` (all equities) | 112,690 | **25,468** | 87,222 (77.4%) |
| ETFs — share of dotted symbols | 36,481 | — | **92.3% would be dropped** |
| Funds — share of dotted symbols | 57,853 | — | 45.7% |

**It destroys true primary listings.** `000002.SZ` — the **primary Shenzhen listing of China
Vanke Co., Ltd.**, ISIN `CNE100001SR9`, FIGI `BBG006KY4KD6` — is dropped, because Chinese,
Korean, Indian, Brazilian, Australian and most European primary listings use a dotted local
convention. Verified: `'000002.SZ' in select(country="China").index → True`, but
`in select(country="China", only_primary_listing=True).index → False`.

**It retains genuine duplicates.** `BRK-A`, `BRK/A`, `BRK-B`, `BRK/B` are all dotless and all
survive, so the "primary listings only" result still contains two rows per share class.

**It fails open when empty.** `Equities.py:213-217`: if the filter yields nothing, the code
`print`s *"No primary listings found. Returning all equities matching your criteria."* and
returns the **unfiltered-by-primacy** result. A caller cannot distinguish "these are the primary
listings" from "primacy filtering was abandoned". Status: **VERIFIED** (source); the empty-branch
was **not** triggered in our runs (**NOT VERIFIED** at runtime).

**Conclusion:** `only_primary_listing` must be treated by AHOS as an *advisory, unreliable
syntactic filter*, never as an authority on listing primacy.

## 5.5 FinanceDatabase identity model (reconstructed)

```
                       [ no issuer entity ]
                                │
                     free-text `name`  (47,578 lowercase dups; 'ISHARES'×257; 'two'×129)
                                │  ← the ONLY issuer proxy, and it is not a key
              ┌─────────────────┴──────────────────┐
   shareclass_figi (56.8%, 29,164 uniq)   composite_figi (54.0%, 41,131 uniq)
              │                                     │
              └──────────────┬──────────────────────┘
                             │
                    figi (52.0%, 58,232 uniq of 58,556)   ← nearest thing to a listing key
                             │
        isin (27.0%, 9,406 uniq / 30,429)   cusip (24.2%, 12,946 uniq / 27,286)
                             │
        ╔════════════════════▼═══════════════════════════════════════╗
        ║  ROW = SYMBOL = LISTING   (the actual primary key)          ║
        ║  symbol + exchange + mic + market + country(HQ) + currency  ║
        ╚════════════════════════════════════════════════════════════╝
                             │
      unique within an asset class · NOT unique across classes (CHAD)
      NOT normalized (whitespace) · NOT one kind of thing (503 .VI symbols are ISINs)
```

**Properties:** listing-centric · no temporal validity · no conflict state · no confidence ·
silent positional dedup · identifier coverage insufficient to serve as the key · zero issuer
entities.

## 5.6 AHOS identity compatibility assessment

AHOS's model, read from `architecture/identity/types.py` and `architecture/identity/resolution.py`:

```python
class IdentityState(str, Enum):
    VERIFIED; CONFLICT; UNRESOLVED; INVALID; STALE; UNSUPPORTED

@dataclass(frozen=True)
class IdentitySource:  provider; chain; address; retrieved_ts; source_ts; kind
@dataclass(frozen=True)
class ChainIdentity:   input_chain; canonical_chain; state; reason
@dataclass(frozen=True)
class TokenIdentity:   chain; address_canonical; address_input; token_id;
                       symbol_alias; name_alias; state; reason; checksum_ok
@dataclass(frozen=True)
class PoolIdentity:    chain; dex_id; pair_address; pair_id; token_id;
                       base_token_address; state; reason; belongs_to_token
@dataclass(frozen=True)
class IdentityResolution:
    chain; token; pool; dex; sources; conflicts; provenance; choices; pools
    policy_version = "identity-resolution-v1"; computed_ts
```

and `ProviderRouter.discover_candidates()` dedupes on `(c.chain, c.address.lower())`
(`architecture/providers/registry.py`).

### Compatibility matrix

| AHOS requirement | FinanceDatabase provides it? | Gap |
|---|---|---|
| **`chain`** | **No.** No chain field in any asset class. Chain appears only as prose in `summary` (`'ethereum'` in 606 crypto rows, `'solana'` in 10) | **Total** |
| **`address_canonical` / contract address** | **No.** No address column anywhere | **Total** |
| **`token_id` (canonical hash)** | **No.** | **Total** |
| **`pair_address` / `pair_id` (pool identity)** | **No.** No pool concept | **Total** |
| **`dex_id`, `factory`, `router`** | **No.** | **Total** |
| **`checksum_ok`** | **No** for tokens. **Yes, in spirit**, for ISIN/CUSIP/FIGI — the `main`-only validator implements all three check-digit schemes | Partial, different domain |
| **`state` ∈ {VERIFIED, CONFLICT, UNRESOLVED, INVALID, STALE, UNSUPPORTED}** | **No.** Binary existence only. Conflicts are resolved silently by `keep='first'`; nothing is ever marked `CONFLICT` | **Total** |
| **`reason` for the state** | **No.** | **Total** |
| **`retrieved_ts` / `source_ts`** | **No.** No timestamp column in any schema (§4.0 SC-01) | **Total** |
| **`provenance`** | **Almost none.** The only provenance signal in the entire dataset is `cryptos.exchange == 'CCC'` (CryptoCompare) and `currencies.exchange == 'CCY'`. Equities/ETFs/funds/indices carry no source attribution | **Near-total** |
| **`conflicts` list** | **No.** | **Total** |
| **`policy_version`** | **No.** The dataset is not versioned at all | **Total** |
| `symbol_alias` / `name_alias` | **Yes** — `symbol` and `name` exist and are exactly alias-grade (non-canonical, non-unique, unnormalized) | Compatible **only** as aliases |
| Multi-listing awareness | **Partially** — via the FIGI hierarchy at 52–57% coverage | Usable as a *hint*, not a key |

### Verdict

**The two identity models are not mergeable, and no mapping should be attempted at the identity
layer.** FinanceDatabase identifies *exchange-listed securities by venue-local symbol*; AHOS
identifies *on-chain tokens and pools by (chain, contract address)*. There is no shared key, no
shared namespace, and no overlapping temporal model.

Per the tasking's explicit instruction: **do NOT propose merging FinanceDatabase identity into
AHOS token identity.** We do not. Specifically:

- ❌ Never use a FinanceDatabase `symbol` as, or as a component of, an AHOS `token_id`.
- ❌ Never use `cryptos.cryptocurrency` as a token identity — it is a Yahoo-mangled pair prefix
  (`SOL1` ≠ `SOL`, `COMP1` ≠ `COMP`) with no chain and no address.
- ❌ Never treat `isin`/`cusip`/`figi` as unique keys — they are 1:N (up to 57:1) and 48–76% absent.
- ❌ Never treat `country` as listing jurisdiction, or `exchange`/`market` as observed venue.
- ❌ Never treat `name` as an issuer identity.

### Required normalization boundary (if ever consumed)

Any AHOS-side consumption must sit behind an adapter that treats FinanceDatabase output as
**untrusted, unversioned, timestamp-less text** and re-derives everything AHOS needs:

1. **Namespace isolation.** Prefix every key: `fdb:<asset_class>:<symbol>` — never a bare symbol.
2. **Snapshot pinning.** Record the source git commit SHA and the bz2 SHA-256 for every ingest;
   refuse to load a snapshot whose hash is not in an allowlist (§14).
3. **Synthetic freshness.** Attach `retrieved_ts` (ingest time) and a *file-level* `source_ts`
   (the commit date), and mark every record `IdentityState.STALE` unless the snapshot is inside
   a declared window. There is no record-level `source_ts` to propagate — so AHOS must not
   pretend there is.
4. **Explicit UNKNOWN for absent identifiers.** Empty `isin`/`cusip`/`figi` ⇒ `UNKNOWN`, never
   `""`, never `None`-coalesced into a plausible-looking value.
5. **Conflict detection, not resolution.** Where a bare symbol maps to >1 row (across asset
   classes or via FIGI grouping), emit `IdentityState.CONFLICT` with the full candidate list in
   `conflicts`. Never pick one silently.
6. **Reject the `only_primary_listing` heuristic.** Compute primacy from `mic`/`exchange` and the
   FIGI hierarchy if needed, or leave it `UNKNOWN`.
7. **No crypto bridging.** The `cryptos` asset class must be **excluded from any AHOS token path**
   entirely (§8).
8. **Trim and case-fold defensively** on ingest (4 symbols with edge whitespace, 19 with internal
   whitespace, 1,774 names with trailing whitespace).
9. **Provenance stamping** on every field: `provider="financedatabase"`, `kind="reference"`,
   `source_commit`, `ingest_ts`, and a per-field `confidence` derived from population rate.
10. **Fail closed.** Any adapter error ⇒ empty result + `UNKNOWN` status, never a partial frame.

### Collision risks if the boundary is not enforced

| Collision | Consequence in AHOS |
|---|---|
| `META` (Metadium) ↔ `META` (Meta Platforms) | A TradFi security record attached to a crypto token candidate |
| `SOL1` read as "Solana" ↔ AHOS `chain="solana"` | Confusing an L1 *token ticker* with a *chain identity* — the two are different axes in `ChainIdentity` |
| `CHAD` equities ↔ `CHAD` etfs | Two different instruments merged into one AHOS entity |
| `BTC` absent, `BTC2` = Bitcoin2 | A lookup for Bitcoin returns nothing; a naive fuzzy match returns a dead 2019 clone |
| `isin` FR0013269123 → 57 symbols | An ISIN-keyed join fans out 57×, inflating any aggregate |
| `BRK-A` / `BRK/A` | Double-counting one share class with contradictory venue attribution |
| `country='United States'` on `FRA`/`STU`/`BER` listings | Wrong jurisdiction for any geo-filtered or sanctions-aware logic |
