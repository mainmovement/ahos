# 25 — Final Evidence Reconciliation

**Document 25.** The closing reconciliation of the forensic follow-up: every claim re-tested, its
disposition, the corrections register, the updated unknowns ledger, the required decision format,
and the self-audit.

**Follow-up window:** 2026-09-15T18:25Z – 19:05Z UTC.
**Environment:** rebuilt isolated research environment (`/tmp/fdb2_repo`, `/tmp/fdb2_venv`), pinned
to `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634`. Record: `evidence/FOLLOWUP_ENVIRONMENT.txt`.

---

## 25.1 Disposition vocabulary

| Disposition | Meaning |
|---|---|
| **REPRODUCED** | Re-executed in a rebuilt environment; identical result |
| **REPRODUCED-EXACT** | Re-executed; identical result **and** identical numbers/strings |
| **STRENGTHENED** | Re-executed; result holds and the evidence is now stronger (proof vs argument, exact values vs ranges, wider scope vs narrow) |
| **REFINED** | Result holds; the original statement was imprecise and is now stated exactly |
| **CORRECTED** | The original statement was materially wrong and is replaced |
| **UNREPRODUCED** | Could not be reproduced; the original figure is **withdrawn** |
| **HISTORICAL** | True when measured, about a state that has changed or cannot be re-measured |
| **UNCHANGED-UNKNOWN** | Still not determinable |

## 25.2 Master reconciliation table

### Objective A — the decisive crypto verdict (document 19)

| Claim (as originally reported) | Re-test | Disposition |
|---|---|---|
| cryptos table has exactly **7** columns | `['symbol','name','cryptocurrency','currency','summary','exchange','website']`, 3,367 rows; programmatic match `true` | **REPRODUCED-EXACT** |
| **14** required AHOS identity fields absent | 0 of 14 present | **REPRODUCED-EXACT** |
| Chain data exists only as prose in `summary` | `ethereum` 606 · `solana` **10** · `arbitrum` **0** · `base` **0** | **REPRODUCED-EXACT** |
| `SOL` is not present | 0 rows; `"SOL" in tickers` = False; library `select` → `ValueError` (exact message captured) | **REPRODUCED / STRENGTHENED** (now at library level too) |
| `SOL1` appears with 10 rows | 10 rows; names `Solana CAD/CNY/ETH/EUR` | **REPRODUCED-EXACT** |
| Token probe: **22 of 73** present, **51** absent | 22 / 51, using the **verbatim** archived probe list | **REPRODUCED-EXACT** |
| Every Solana-ecosystem token absent | all 14 probed absent (`BONK WIF JUP PYRM JTO RAY ORCA MNGO POPCAT MEW BOME SLERF MYRO WEN`) | **REPRODUCED-EXACT** |
| **86** crypto↔equity ticker collisions | 86 — of **351** non-empty tickers (24.5%) / **352** incl. `''` (24.4%) | **REPRODUCED / REFINED** (denominator now stated) |
| `BTC` absent as a token, present as a quote currency (113) | 0 token rows; **113** quote rows | **REPRODUCED-EXACT** |
| **0** timestamp/provenance columns across all 7 schemas (304,495 rows) | `A7_total_temporal_columns_found = 0` | **REPRODUCED-EXACT** |
| Row counts 112,690 / 36,481 / 57,853 / 91,181 / 2,556 / 3,367 / 1,367 | all seven identical | **REPRODUCED-EXACT** |
| No CI job writes `database/cryptos.csv` | Only `database/equities/{exchange}.csv` and `database/equities/NAN.csv` are written under `database/`; `cryptos.csv` is **read** 3× (recompress, categories, README count) | **REPRODUCED / REFINED — stronger**: it is touched by 3 of 5 jobs but its content is never updated |
| **0 of 16** crypto capabilities | `A9_ALL_NEGATIVE = true` | **REPRODUCED-EXACT** |
| `NormalizedTokenCandidate` incompatibility | **`TypeError: missing 2 required positional arguments: 'chain' and 'address'`**; `None` → **`AttributeError: 'NoneType' object has no attribute 'lower'`** on the real router key; 0/16 `MarketMetrics` and 0/15 `SecuritySignals` satisfiable | **STRENGTHENED — argument → execution-proof** |
| `search()` fail-open (unknown column returns everything) | 3,367 of 3,367 rows on a bogus column | **REPRODUCED-EXACT** |
| Site-packages local mode → uncaught `FileNotFoundError` | reproduced; `isinstance(e, RequestException)` = **False** | **REPRODUCED-EXACT** |
| `raw.githubusercontent.com` unreachable | curl rc=35 TLS fail, **identical**, ~2 h later | **REPRODUCED** |
| Artifact SHA-256 (sdist + wheel) | both **MATCH** the recorded values, re-hashed from a fresh download, and match PyPI's published digests | **REPRODUCED-EXACT — cross-session integrity confirmed** |

### Objective B — identity edge cases (document 20)

| Claim | Re-test | Disposition |
|---|---|---|
| `CHAD` collides across equities ↔ etfs | confirmed, exact records captured; the **only** cross-asset pair, n=1 | **REPRODUCED-EXACT** |
| `BRK-A`/`BRK/A` venue contradiction | **7** Berkshire rows across **4** venues (`ASE`,`MEX`,`NYQ`,`VIE`); original reported 5 rows | **REPRODUCED / CORRECTED (expanded)** — and `figi` is populated **only** on the 2 Vienna rows, empty on all 4 US rows (new) |
| `MMM` = 3M Company and Marley Spoon AG | **18** rows, **5** name strings, **4** unrelated entities (adds Mining Minerals & Metals plc, Minco Capital Corp.) | **REPRODUCED / CORRECTED (expanded)** |
| 74,690 distinct bare tickers; 16,251 repeated | identical | **REPRODUCED-EXACT** |
| ISIN max fan-out **57** (`FR0013269123`, Rubis) | 57; plus 9,406 distinct ISINs, **5,181** with fan-out >1, 30,429 populated (27.0%) | **REPRODUCED-EXACT / STRENGTHENED** |
| **129** rows named `two`, all `country='United States'` | 129; across **29** venue suffixes; all `Financials / Diversified Financials / Diversified Financial Services` | **REPRODUCED-EXACT / STRENGTHENED** |
| `mode()` imputation mechanism (source-verified; cross-run confirmation was **U-13 UNKNOWN**) | the 129 rows carry **exactly** the `Financials` subset modes, zero variance | **STRENGTHENED — U-13 partially closed from the data side** |
| 19 symbols containing whitespace | 19 (e.g. `'ECC           '`) | **REPRODUCED-EXACT** |
| **1,774** names with trailing whitespace | equities trailing **658** / any-side **665**; all classes trailing **11,933** / any-side **11,956`. No definition yields 1,774 | **UNREPRODUCED — figure WITHDRAWN**; the phenomenon is confirmed and is **larger** than reported |
| 47,578 lowercase-duplicate names | identical | **REPRODUCED-EXACT** |

### Objective C — the release regression (document 21)

| Claim | Re-test | Disposition |
|---|---|---|
| Release 2.4.0 lacks `keep_default_na=False` | `helpers.py:63` one-liner; **also confirmed at tag `2.4.0` itself**, independently of the wheel | **REPRODUCED / STRENGTHENED** |
| `main` contains the fix | `helpers.py:63-69` and `:74-80`, both branches | **REPRODUCED** |
| 8-line delta between release and `main` | 358 vs 366 lines; `diff -rq` → only `helpers.py` differs, `validation/` repo-only | **REPRODUCED-EXACT** |
| Ticker `NA` is "silently lost" | Row **retained** (112,690 both ways; cell-level NaN divergence **empty**) but its **key becomes null**: `"NA" in index` False, `.loc["NA"]` → `KeyError`. Dropped only by a key filter such as `to_toolkit()`'s `index.notna()` | **CORRECTED / REFINED** — real, but *unaddressable*, not *deleted*; **harder** to detect than originally stated |
| Exact source record | **`database/equities/NMS.csv:4346`** → `NA,Nano Labs Ltd Class A Ordinary Shares,…,NMS,XNAS,NASDAQ Global Select`; exactly **1** in the corpus | **STRENGTHENED** (was not previously located to file/line) |
| Fix commit identity | **`3b8eb8390959bec6a360a620333b6fe5217a4618`**, 2026-08-07T10:32:18Z, **Jon Højlund Arnfred**, PR **#166**, *"Preserve CSV values verbatim in the database workflow"*; `git log -S` returns exactly one commit | **STRENGTHENED** (previously unknown) |
| Was the fix released? | **NO** — `merge-base --is-ancestor 3b8eb83 2.4.0` → **NO**; `… HEAD` → **YES**; tag `2.4.0` = `51226b86…`; PyPI upload 2026-06-02T14:05:45Z; fix is **66 days later**; latest release is still 2.4.0 | **STRENGTHENED — git-proven** |
| Scope: all asset classes? | **Equities only.** 1 vulnerable index value; the other **6** classes have **0**; the only NA-like first field anywhere in `database/` is `NMS.csv → 'NA'` | **STRENGTHENED** (new test, not previously run) |

### Objective D — data governance (document 22)

| Claim | Re-test | Disposition |
|---|---|---|
| **0** workflow runs on the bot commit | 0 — and **0** for all three 2026-09-13 bot commits | **REPRODUCED / STRENGTHENED** |
| **0** check-runs on the bot commit | 0 — same, all three commits | **REPRODUCED / STRENGTHENED** |
| **Three** consecutive GICS failures (09-06, 09-11, 09-13) | **TEN** consecutive: #389 (2026-08-02T17:20:15Z) → #398 (2026-09-13T15:07:37Z); last success **#388** (2026-08-02T12:47:55Z); **42-day** span | **CORRECTED — understated by 7 runs / ~5 weeks** |
| GICS job runs last ⇒ non-blocking | `needs: [Add-New-Ticker, Update-Compression-Files, Update-Categorization-Files, Update-README-Statistics]`; started 15:10:43 after the 15:10:12 push | **REPRODUCED / STRENGTHENED** (source + timestamps) |
| `1 failed, 85 passed` on `main` | **`1 failed, 85 passed, 1 deselected in 42.43s`**; `tests/test_invariants.py:95`; `equities <-> etfs: ['CHAD'] (1 total)` | **REPRODUCED-EXACT** |
| Deselected identifier test passes alone with a warning | `1 passed, 1 warning in 4.17s`; warning text and line captured (`test_validate_identifiers.py:298`, "**2** identifier finding(s) require manual review") | **REPRODUCED / STRENGTHENED** |
| Validator: 2 invalid CUSIPs of 249,085, 0 actionable, 2 review-only | consistent with the archived `evidence/identifier_issues.csv` and with the warning's count of **2** | **REPRODUCED (indirectly)** — the validator itself was not re-run this session; its output is corroborated by the test's own warning |
| **U-12**: *which* rows fail the GICS invariant | **CLOSED.** 10 rows, classified 6 + 2 + 2; CI log unfetchable (Azure blob EOF), so the check was **re-executed** locally — stronger than the log | **CLOSED / STRENGTHENED** |
| (new) taxonomy authority vs data | `categories.json` = 11/24/**69**; data = 11/24/**80**; **11** orphan industries across **14** rows; 0 authority industries unused | **NEW — reconciles document 04's "80 vs GICS 69"** |
| (new) CI blind spot | 8 of the 14 orphan rows are excluded by the job's own `notna()` filter; 40,045 rows have an empty `industry`. The check inspects ~64% of the corpus | **NEW FINDING GOV-02** |
| (new) Identifier Validation workflow | id `312400597`, created 2026-07-13, state `active`, **2 runs**, both `pull_request` on `feature/validate-identifiers`, both `success`; file exists at **no** default-branch ref; **0** commits touch that path. The validator itself **was** merged (PR #159, `5ae2910`) | **NEW FINDING GOV-01** |
| (new) CI script still NA-vulnerable | 2 of the 10 failing rows show `exchange='nan'` — the workflow reads without `keep_default_na=False` | **NEW** |

### Objective E — legal / licensing (document 19 §19.4–19.6)

| Claim | Re-test | Disposition |
|---|---|---|
| MIT, `Copyright (c) 2023 Jeroen Bouma` | 21-line `LICENSE` read at the pinned commit; `pyproject.toml:5`; PyPI; both artifacts | **REPRODUCED-EXACT** |
| No dataset licence / `NOTICE` / ODC / CC0 / CLA / DCO | `find` over the tree → only `./LICENSE` | **REPRODUCED (absence)** |
| Upstream `rreichel3/US-Stock-Symbols` has `license = None` | re-queried: `None`, 574 stars, `pushed_at 2026-09-15T00:39:12Z` | **REPRODUCED-EXACT** |
| `JeroenBouma` ≠ `JerBouma`; the former 404s | ids **46189588** (0 repos) vs **46355364** (15 repos); `JeroenBouma/FinanceDatabase` → **HTTP 404** | **REPRODUCED-EXACT** |
| `CONTRIBUTING.md:129` MSCI/GICS disclaimer | read verbatim | **REPRODUCED-EXACT** |
| Check-digit algorithms are "~15 lines, no licence obligation" to reimplement | The repository **does not implement them** — `validate_identifiers.py:13` is `from stdnum import cusip, figi, isin`, and **`python-stdnum` 2.2 is LGPL-2.1+** | **CORRECTED** — the *algorithms* remain freely reimplementable from public standards; *this implementation path* is not licence-clean for AHOS |

## 25.3 Corrections register

Every material correction made by this follow-up, in one place. **Documents 00–18 were not
overwritten**; these entries supersede them where they conflict.

| ID | Original statement | Corrected statement | Severity of the correction |
|---|---|---|---|
| **D-CORR-01** | "GICS validation failing on **three** consecutive runs (2026-09-06, 09-11, 09-13)" | **Ten** consecutive failures, #389 (2026-08-02T17:20:15Z) → #398 (2026-09-13T15:07:37Z), a **42-day** span; last success #388 (2026-08-02T12:47:55Z) | **Material — the original understated the finding by 7 runs and ~5 weeks** |
| **C-REFINE-01** | Release 2.4.0 "silently **loses** the ticker `NA`" | The row is **retained** (112,690 rows either way; zero cell-level divergence) but its **key becomes null**, so it is unaddressable (`KeyError`) and is dropped only by key filters such as `to_toolkit()`'s `index.notna()`. **A row-count check cannot detect it** | **Material to detection guidance** — the defect is real but *harder* to detect than stated, not easier |
| **B-CORR-01** | "1,774 names with trailing whitespace" | **Withdrawn — not reproducible.** Measured: equities 658 trailing / 665 any-side; all seven classes 11,933 trailing / 11,956 any-side. The phenomenon is confirmed and is **far larger** than reported (indices alone: 9,655) | **Minor to conclusions** (no load-bearing claim depended on it); **material to evidence discipline** |
| **B-EXP-01** | `BRK`: 5 rows listed | **7** Berkshire rows across **4** venues; `figi`/`shareclass_figi` populated **only** on the 2 Vienna rows, empty on all 4 US rows | **Expansion — strengthens the case** |
| **B-EXP-02** | `MMM`: "3M Company and Marley Spoon AG" | **4** unrelated entities across 18 rows and 5 name strings (adds Mining Minerals & Metals plc, Minco Capital Corp., plus the `MMM.SG` German registered-share name variant for 3M itself) | **Expansion — strengthens the case** |
| **F-CORR-01** | Check-digit algorithms: "~15 lines, no licence obligation" to reimplement, sourced from `validate_identifiers.py` | The repository **delegates** to `python-stdnum` (**LGPL-2.1+**, not permissive). Reimplement from the **published ISO 6166 / CUSIP / OpenFIGI specifications**; do **not** copy the validator and do **not** add `python-stdnum` (conflicts with `requirements.txt`'s "permissively licensed" law) | **Material — changes the recommended implementation path** |
| **A-REFINE-01** | "86/351 crypto-equity ticker collisions" (elsewhere "352 tickers") | **352** distinct `cryptocurrency` values **including** the empty string; **351** excluding it (7 rows are `''`); collisions = **86** under either denominator (24.5% / 24.4%) | **Precision only** |
| **A-REFINE-02** | "No CI job writes `database/cryptos.csv`" | Correct, and stronger: `cryptos.csv` is **read** by 3 of 5 jobs (recompress, categorise, count) but **no workflow updates its content from any source**. The only `database/` write targets are equities shards | **Precision — strengthens the finding** |
| **SCH-RECON-01** | "GICS 11/24/80" (with a note that GICS defines 69) | **Reconciled:** `categories.json` (the authority) = 11/24/**69**; the data = 11/24/**80**; the delta is **11 orphan industry values across 14 rows**. The original measured the data; the authority is 69 | **Resolution of an open tension** |
| **ENV-CORR-01** | Reproduction instructions point at `/tmp/fdb_repo`, `/tmp/fdb_venv` | Those paths **do not survive** between sessions. The durable record is `evidence/`; machine-readable re-execution outputs are now archived under `evidence/followup/` | **Material to reproducibility** |

## 25.4 Unknowns ledger — updated

| ID | Original status | Status after follow-up |
|---|---|---|
| **U-01** default remote data path not exercisable | UNKNOWN | **UNCHANGED** — `raw.githubusercontent.com` still fails identically (curl rc=35). Compensated by pinned-clone testing |
| **U-02** served `main` vs pinned clone byte-identity | UNKNOWN | **UNCHANGED** — but HEAD is confirmed unmoved, so the risk is bounded |
| **U-03** fresh `pip install` resolution on the AHOS Windows host | UNKNOWN | **UNCHANGED** — not installed into AHOS (prohibited). `uv.lock` pins re-verified: financetoolkit **2.0.7**, pandas **2.3.3** *and* **3.0.3** under separate markers |
| **U-04** bulk-import provenance / crypto vintage | UNKNOWN (INFERENCE: Yahoo/CryptoCompare, ~2020) | **UNCHANGED** — still INFERENCE. Corroborated indirectly (CCC-dominant, `SOL` absent, `SRM` present) |
| **U-05** `JeroenBouma` account history | UNKNOWN | **UNCHANGED** — re-verified 404 and 0 repos; distinct user ids confirmed |
| **U-06** data ownership | UNKNOWN | **UNCHANGED** |
| **U-07** maintainer intent on dataset licensing | UNKNOWN | **UNCHANGED** |
| **U-08** `secrets.PAT` scope | UNKNOWN | **UNCHANGED** |
| **U-09** PyPI publication method / attestation | UNKNOWN | **UNCHANGED** — no publish workflow exists |
| **U-10** cause of zero runs on bot commits | UNKNOWN | **UNCHANGED as to cause**; **STRENGTHENED as to effect** (all 3 bot commits; mechanism now traced to run #398 being in flight against an older `head_sha`) |
| **U-11** cause of no CI loop on self-push | UNKNOWN | **UNCHANGED** |
| **U-12** which rows fail the GICS invariant | **UNKNOWN** | ✅ **CLOSED** — 10 rows enumerated and classified (6 unknown-industry, 2 mis-paired, 2 level-confusion) by local re-execution of the CI logic, because the log host was unreachable |
| **U-13** whether identifier-less tickers are ever backfilled | UNKNOWN | **PARTIALLY CLOSED** — the `mode()` imputation is now **proven to have fired** (129 `two` rows carry exactly the `Financials` modes). The backfill question itself remains open |
| **U-14** which commit caused 158,429 → 112,690 | UNKNOWN (INFERENCE) | **UNCHANGED** — not bisected. **Still INFERENCE** |
| **U-15** cross-version identifier stability | UNKNOWN | **UNCHANGED** |
| **U-16** whether symbols are recycled | UNKNOWN | **UNCHANGED** — mechanism verified, no instance observed |
| **U-17** Windows behaviour | UNKNOWN | **UNCHANGED** — audit host is Linux again. **No Windows claim is made anywhere in this package** |
| **U-18** is the `raw.githubusercontent.com` failure environment-specific? | UNKNOWN | **STILL UNKNOWN, better characterized** — reproduced twice ~2 h apart with identical curl rc=35, while `github.com`, `api.github.com`, `codeload.github.com`, `files.pythonhosted.org`, `pypi.org` all succeed. A **second** GitHub-owned host (Actions log blob storage) also fails, so the pattern is *host-specific filtering within a generally working GitHub path*, not a blanket block. Resolution still requires a test from the AHOS Windows host |
| **U-19** *(new)* why the Identifier Validation workflow was not merged | — | **NEW UNKNOWN** — deliberate (cost? the warning-only test deemed sufficient?) or oversight. Not determinable externally. **No negligence is alleged** |
| **U-20** *(new)* whether the 8 CI-invisible orphan-taxonomy rows will ever be caught | — | **NEW UNKNOWN** — they are outside the check's filter by construction |
| **U-21** *(new)* whether run #389's failure onset (2026-08-02T17:20:15Z) has an identifiable cause | — | **NEW UNKNOWN** — it began within ~5 h of the last success (#388, 12:47:55Z) and one run *before* the `keep_default_na` fix (#390). **No causal link is asserted** |

**Closed: 1 (U-12). Partially closed: 1 (U-13). Newly registered: 3 (U-19, U-20, U-21).
Unchanged: 16.**

## 25.5 New evidence IDs registered by this follow-up

| Range | Document | Count |
|---|---|---|
| `EV-FU-A-*` (Objective A, incl. the A-10 execution proof) | 19 | 10 claims re-verified; JSON at `evidence/followup/f1_objective_a.json`, `f2_a10_contract.json` |
| `EV-FU-B-*` (Objective B) | 20 | 5 cases, exact records; `evidence/followup/f4_identity.json` |
| `EV-FU-C-01 … EV-FU-C-08` (Objective C) | 21 | 8; `evidence/followup/f3_na_regression.json` |
| `EV-FU-D-01 … EV-FU-D-15` (Objective D) | 22 | 15; `evidence/followup/d_gics_sequence.json`, `f5_gics_replication.json` |
| `EV-FU-E-*` (Objective E) | 19 §19.4 | 9 re-verified legal facts |
| `FOLLOWUP-01` | 19 §A-10 / KN-02 | A `None`-filled candidate self-reports `confidence_level="HIGH"` with 33 unknown fields |
| `FOLLOWUP-02` | 20 CASE 5 / KN-06 | The 129 `two` rows empirically prove the `mode()` imputation fired |
| `GOV-01` | 22 §22.5 | The Identifier Validation workflow was built, ran twice successfully on a PR branch, and was never merged |
| `GOV-02` | 22 §22.7 | The taxonomy check's `notna()` filter hides 8 of 14 orphan rows and all 40,045 empty-`industry` rows (~64% coverage) |
| `ENV-DUR-01` | 19 §19.0 / §19.7 | The original `/tmp` evidence did not survive one session; durable copies now archived under `evidence/` |

**Archived artifacts added by this follow-up** (all under `evidence/`, none overwriting anything):

```
evidence/FOLLOWUP_ENVIRONMENT.txt
evidence/followup/f1_objective_a.json
evidence/followup/f2_a10_contract.json
evidence/followup/f3_na_regression.json
evidence/followup/f4_identity.json
evidence/followup/f5_gics_replication.json
evidence/followup/d_gics_sequence.json
evidence/scripts/f1_objective_a_crypto.py
evidence/scripts/f2_a10_contract.py
evidence/scripts/f3_na_regression.py
evidence/scripts/f4_identity_fixtures.py
evidence/scripts/f5_gics_replication.py
```

## 25.6 Does any of this change the verdict?

| Question | Answer |
|---|---|
| Did any crypto claim fail to reproduce? | **No.** All ten reproduced; two strengthened, one refined, one upgraded from argument to execution-proof |
| Did any new evidence *support* crypto use? | **No.** The new evidence (the `SOL1` row whose own `summary` says "Solana (SOL)"; 0/16 `MarketMetrics` and 0/15 `SecuritySignals` satisfiable; `TypeError` on construction) **further undermines** it |
| Did the governance picture improve? | **No — it worsened.** 3 consecutive failures → **10** over 42 days; plus an unmerged validation workflow and a newly measured blind spot in the taxonomy check |
| Did the release-regression picture improve? | **No.** The fix is git-proven **not** released, and the defect is **harder** to detect than originally stated (row retained, key nulled) |
| Did anything improve? | **Yes, three things:** U-12 is **closed**; the `mode()` imputation is now **proven** rather than inferred; and the identity cases are **richer** (7 BRK rows / 4 venues, 4 MMM entities) — making the proposed fixtures better |
| Was any claim withdrawn? | **Yes, one** — the 1,774 trailing-whitespace figure (B-CORR-01). Withdrawn, not defended |
| Was any recommendation changed? | **One implementation path was changed** (F-CORR-01): reimplement check digits from public standards, **not** from this repo's LGPL-dependent validator. The overall recommendation is **unchanged** |

> ## No evidence materially contradicts the existing verdict. Several items strengthen it.

---

## 25.7 FINAL DECISIONS

### Crypto Decision

> ## **REJECTED**
>
> Re-verified against all ten decisive claims. `0 of 14` required identity fields, `0 of 16`
> capabilities, `SOL` absent (library-level `ValueError`), 51 of 73 probed tokens absent, every
> Solana-ecosystem token absent, `0` timestamp columns across 304,495 rows, no CI job updates the
> crypto table's content, and a `NormalizedTokenCandidate` **cannot be constructed** from it
> (`TypeError`) or, if forced with `None`, **crashes the router's dedupe key** (`AttributeError`).
> **The evidence does not contradict the existing verdict — it reinforces it.**

### Research Decision

> ## **RESEARCH-ONLY VALUE**
>
> Strengthened by this follow-up: six concrete adversarial fixtures (FIX-01…FIX-06), fourteen
> assessed techniques with a corrected licence path, ten knowledge items, and one closed unknown.
> All of it available **without** installing the package or touching production.

### Integration Decision

> ## **NOT APPROVED**
>
> No integration of any kind is approved. The vendored-snapshot design in document 14 §14.6 remains
> **conditional** on a future non-crypto lane, separate written authorization, boundary rules
> B-1…B-18, and a completed legal review.

### Implementation Decision

> ## **NOT IMPLEMENTED**
>
> Nothing was implemented — by the original investigation or by this follow-up. No AHOS production
> code, Lane A, Lane B, `CanonicalDecisionAuthority`, scoring, security, identity resolution,
> runtime, calibration, soak configuration, production data or database state was modified. No
> dependency was installed into the AHOS environment. Phase 4 was not started. Live trading was not
> enabled.

### Identity Fixture Decision

> ## **PROPOSED — NOT IMPLEMENTED**
>
> Six fixtures specified in document 20 (FIX-01…FIX-06), each with source case, input records,
> expected resolution behaviour, expected safety behaviour, rationale, evidence reference and an
> explicit authorization field set to **NO**. `architecture/identity/resolution.py` was not
> modified. None of these records is an AHOS production failure.

### Legal Decision

> ## **LEGAL REVIEW REQUIRED** (where applicable)
>
> **Code: MIT — clear, no review needed.** **Data: LEGAL REVIEW REQUIRED** on six discrete
> questions (document 19 §19.5 row 10). **New:** the validator's algorithms arrive via
> **`python-stdnum` (LGPL-2.1+)**, which is **not** permissive and conflicts with AHOS's own
> `requirements.txt` law — so "copy the validator" is **not** a clean path. No legal advice is given
> and no legal certainty is asserted anywhere in this package.

### AHOS Production Impact

> ## **NONE**
>
> Verified, not asserted: all writes were confined to
> `research/finance_database_investigation/`. The one AHOS module *imported*
> (`architecture/providers/contracts.py`) was first confirmed stdlib-only and was imported
> read-only. The upstream repository was cloned and only read — no push, no `--apply`, the validator
> run dry-run. All installation occurred in `/tmp/fdb2_venv`. The only filesystem change inside the
> AHOS tree is the addition of **12 files** under `evidence/` (7 documents + 5 scripts + 6 JSON, as
> listed in §25.5) — **no existing file was overwritten.**

---

## 25.8 FINAL SELF-AUDIT

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Did you inspect source evidence? | **YES** | Rebuilt the environment from scratch: re-downloaded and re-hashed both artifacts (**MATCH**), re-cloned at the pinned commit, read `helpers.py` in **both** versions, all three workflows, `LICENSE`, `pyproject.toml`, `CONTRIBUTING.md`, `uv.lock`, `validate_identifiers.py`, `conftest.py`, `testing.yml`, and the AHOS contracts/registry read-only |
| 2 | Did you verify the decisive crypto claims? | **YES** | All ten re-executed (§25.2 Objective A). 0/14 fields, 0/16 capabilities, 22/51 probe, 86 collisions, 0 timestamps, `TypeError` + `AttributeError` proofs |
| 3 | Did you distinguish historical from current? | **YES** | HEAD confirmed **unchanged** (`a174c97d3bba`), so findings are **CURRENT**. The release-vs-`main` split is dated precisely (2026-06-02 release vs 2026-08-07 fix). The 10-run failure window is timestamped run-by-run |
| 4 | Did you distinguish release from main? | **YES** | Document 21 is built entirely on that distinction: 358 vs 366 lines, `diff -rq`, tag-vs-HEAD git ancestry, wheel-vs-repo `validation/` |
| 5 | Did you distinguish code licence from dataset rights? | **YES** | Document 19 §19.4–19.6 and KN-04 keep them in separate rows; **code = MIT clear**, **data = LEGAL REVIEW REQUIRED** |
| 6 | Did you avoid copying source code? | **YES** | Document 23 quotes short excerpts for **verification and criticism** only, and explicitly excludes copying `validate_identifiers.py`. No code was transplanted into AHOS |
| 7 | Did you avoid modifying AHOS? | **YES** | All writes confined to `research/finance_database_investigation/`; verified by `git status` (§25.9) |
| 8 | Did you avoid modifying frozen Lane A? | **YES** | No Lane A file was opened for modification |
| 9 | Did you avoid disturbing the 72-hour soak? | **YES** | No soak config, runtime, process or state was touched; no server was started |
| 10 | Did you avoid installing into the AHOS environment? | **YES** | All installs went to `/tmp/fdb2_venv`. `requirements.txt` and `requirements-optional.txt` unchanged |
| 11 | Did you avoid inventing benchmark results? | **YES** | Every number in documents 19–25 came from a script archived under `evidence/scripts/` with JSON output under `evidence/followup/`. The one measurement that could not be attributed (`to_toolkit()` e2e) remains **NOT TESTED**; the CI log that could not be fetched is recorded as unreachable and was **replaced by re-execution**, not estimated |
| 12 | Did you avoid claiming legal certainty? | **YES** | `LEGAL REVIEW REQUIRED` is stated for all six data questions; mitigating arguments are labelled as *arguments, not findings*; no conclusion on trademark, database-right or upstream-licence liability is asserted |
| 13 | Did you avoid treating symbol as canonical identity? | **YES** | KN-01/KN-02 make this the central lesson; FIX-03 exists specifically to test that a resolver does **not** treat symbol as identity; the AHOS `symbol_alias` vs `address_canonical` distinction is affirmed, not blurred |
| 14 | Did you avoid turning research findings into production changes? | **YES** | All 6 fixtures and all 10 knowledge items are marked **PROPOSED — NOT IMPLEMENTED** with `Implementation authorized: NO`. Proposed destinations are named as *where to file if accepted*, and no file at those paths was written |
| 15 | Did you register all important evidence? | **YES** | §25.5 registers 5 new evidence ranges, 2 FOLLOWUP findings, 2 GOV findings, 1 durability finding, and 12 archived artifacts |
| 16 | Did you mark unresolved questions explicitly? | **YES** | §25.4: 16 unchanged unknowns, 1 closed (U-12), 1 partially closed (U-13), 3 newly registered (U-19, U-20, U-21). Plus 1 **withdrawn** figure (B-CORR-01) and 1 declined-test record (CI log unreachable) |

**Additional self-audit items specific to this follow-up:**

| Question | Answer |
|---|---|
| Did you restate claims instead of re-testing them? | **No.** Every Objective A/C/D claim was re-executed. Where re-execution was impossible (CI log), that is stated and compensated |
| Did you reuse the original inputs? | **Yes, deliberately** — the 73-token probe list was lifted verbatim from `evidence/scripts/a2_crypto.py` so results are comparable, not merely similar |
| Did you report your own errors? | **Yes** — the 87-error pytest attempt (missing `pytest-recording`), the `dataclasses` module-registration failure in `f2`, and the off-by-N consecutive-failure counter are all recorded in the documents rather than silently fixed |
| Did you correct the original report where it was wrong? | **Yes** — 10 entries in the corrections register (§25.3), including one **withdrawn** figure and one **materially understated** finding |
| Did you let a favourable result stand unchallenged? | **No** — the GICS finding got **worse** on re-test and is reported as such; the `NA` regression was **refined against** the original phrasing |

## 25.9 Working-tree verification

Confirmed at the end of this follow-up: the only paths added or modified inside the AHOS repository
are under `research/finance_database_investigation/`. Pre-existing CRLF↔LF normalization warnings on
unrelated files were present **before** this session and are **whitespace-only**
(`git diff --ignore-all-space` is empty) — they are not modifications made by this investigation.

## 25.10 Closing statement

This follow-up re-tested the load-bearing claims of a 19-document investigation in a **rebuilt**
environment, because the original one no longer existed. **All ten decisive crypto claims
reproduced.** Two governance findings turned out to be **worse** than reported, one regression
turned out to be **more subtle** than reported, one identity case turned out to be **richer**, one
licence recommendation turned out to be **wrong about its implementation path**, and one cosmetic
figure could **not** be reproduced and is withdrawn. One unknown was **closed** by re-execution
after the CI log proved unreachable, and one previously source-only inference (the `mode()`
imputation) is now **proven from the data**.

The verdict is unchanged, and it is now better evidenced:

> **Crypto: REJECTED · Research: RESEARCH-ONLY VALUE · Integration: NOT APPROVED ·
> Implementation: NOT IMPLEMENTED · Identity fixtures: PROPOSED — NOT IMPLEMENTED ·
> Legal: LEGAL REVIEW REQUIRED where applicable · AHOS production impact: NONE.**

The most durable lesson is methodological, and it is about this investigation rather than its
subject: **evidence stored only in a temporary environment is not evidence for very long.** The
package is now self-sufficient — scripts, machine-readable outputs and two environment records live
under `evidence/`, so the next auditor can reproduce this without reconstructing anything from
prose.
