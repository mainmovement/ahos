# 22 — Data Pipeline Governance Findings

**Document 22 — Objective D.** Verification of the reported governance findings:
*0 workflow runs · 0 check-runs · three consecutive GICS validation failures · `1 failed, 85
passed` on `main`.*

**Sources:** GitHub REST API (`/actions/runs`, `/actions/workflows`, `/commits/{sha}/check-runs`,
`/actions/jobs/{id}/logs`), the pinned repository checkout, and **local re-execution** of both the
project's test suite and its CI validation job.
Raw outputs: `evidence/followup/d_gics_sequence.json`, `evidence/followup/f5_gics_replication.json`.

> **Caution required by the tasking.** No single failure is extrapolated into a general security or
> reliability certification. Each finding below is bounded to what was measured. Where a mechanism
> is verified but its cause is not, that is stated.

---

## 22.0 Headline: one figure was **wrong**, and the truth is worse

| Reported | Re-verified | Disposition |
|---|---|---|
| 0 workflow runs on the bot commit | **0** | **REPRODUCED** (and extended to all 3 bot commits) |
| 0 check-runs on the bot commit | **0** | **REPRODUCED** (same) |
| **Three** consecutive GICS validation failures (2026-09-06, 09-11, 09-13) | **TEN** consecutive failures, 2026-08-02 → 2026-09-13 | **CORRECTED — understated by 7 runs / ~5 weeks** |
| `1 failed, 85 passed` on `main` | **`1 failed, 85 passed, 1 deselected in 42.43s`** | **REPRODUCED EXACTLY** |
| U-12: *which* rows fail the GICS invariant — **UNKNOWN** | **10 rows, each classified** | **CLOSED** |

Three additional findings emerged that were **not** in the original report (§22.5, §22.6, §22.7).

## 22.1 D-1 / D-2 · Zero workflow runs and zero check-runs on data-changing commits — **REPRODUCED**

| Query | Result |
|---|---|
| `GET /actions/runs?head_sha=a174c97d3bba…` | **`total_count = 0`** |
| `GET /commits/a174c97d3bba…/check-runs` | **`total_count = 0`** |

**Extended to the full 2026-09-13 bot sequence** (all three commits that changed data):

| Commit | Subject | Runs | Check-runs |
|---|---|---:|---:|
| `a0c8b199de54` | Update database with new tickers | **0** | **0** |
| `9f91e39c537a` | Update Compression Files | **0** | **0** |
| `a174c97d3bba` | Update README statistics | **0** | **0** |

All three authored by **`GitHub Action`**. So **every** commit that actually mutates the dataset is
ungated — not merely the HEAD commit originally tested.

**Why (mechanism, now better understood).** The scheduled run **#398** started at
`2026-09-13T15:07:37Z` with `head_sha = fe5fbd83c6e4` (the previous HEAD) and
`event = schedule`. The workflow then pushed `a0c8b199` (15:08:25), `9f91e39c` (15:09:17) and
`a174c97d` (15:10:38) **during its own execution**. Those commits therefore never became the
`head_sha` of any run: the run that created them was already in flight against an older SHA.

**Cause classification — still UNKNOWN (U-10 unchanged).** Three candidate mechanisms remain
consistent with the observation: GitHub's `GITHUB_TOKEN` recursion guard, an effect of pushing with
`secrets.PAT`, or a repository/path-filter setting. The **effect** is verified; the **cause** is
not. Per the tasking, no cause is asserted.

**Currency: CURRENT.** HEAD is still `a174c97d3bba` (§19.1), so this is the state of the repository
*now*, not a historical snapshot.

**Affects:** **data** (the commits are data commits). Code is gated — human PR commits do trigger
`Run Tests`; the last successful run was 2026-09-11 against human PR commit `61d2feac72b3`.

## 22.2 D-3 · GICS validation failures — **CORRECTED: ten consecutive, not three**

Workflow: **`Database Update`**, id `55219164`, path `.github/workflows/database_update.yml`,
state `active`, **117** runs total. Job under test: **`Check-GICS-Categorisation`**.

Full sequence of the last 25 runs, per-job conclusion retrieved for each:

| Run # | Created (UTC) | head_sha | Event | GICS conclusion |
|---:|---|---|---|---|
| **398** | 2026-09-13T15:07:37Z | `fe5fbd83c6e4` | schedule | **failure** |
| **397** | 2026-09-11T11:27:32Z | `61d2feac72b3` | push | **failure** |
| **396** | 2026-09-06T14:27:26Z | `5865ce3b26e6` | schedule | **failure** |
| **395** | 2026-08-30T15:31:24Z | `e3c554bb5110` | schedule | **failure** |
| **394** | 2026-08-25T20:18:44Z | `19b5b8cab8dc` | push | **failure** |
| **393** | 2026-08-23T12:11:59Z | `268be5d29898` | schedule | **failure** |
| **392** | 2026-08-16T12:11:13Z | `3a437c3e1da1` | schedule | **failure** |
| **391** | 2026-08-09T12:19:35Z | `652b5f73e495` | schedule | **failure** |
| **390** | 2026-08-07T10:32:21Z | `3b8eb8390959` | push | **failure** |
| **389** | 2026-08-02T17:20:15Z | `bf0a6c13114c` | push | **failure** |
| 388 | 2026-08-02T12:47:55Z | `bf839b234a26` | schedule | **success** ← last success |
| 387 | 2026-07-26T16:32:13Z | `99d541ba9ad4` | push | success |
| 386 … 374 | 2026-07-26 … 2026-06-07 | — | — | success (13 further runs) |

> **CORRECTED FINDING.** `Check-GICS-Categorisation` has failed on **ten consecutive runs**, from
> **#389 (2026-08-02T17:20:15Z)** through **#398 (2026-09-13T15:07:37Z)** — a span of **42 days**.
> The last success was **#388 at 2026-08-02T12:47:55Z**, i.e. it broke **within five hours** of
> its last passing run.
>
> The original report's "three consecutive (2026-09-06, 09-11, 09-13)" was **correct as far as it
> went but materially understated**: those are simply the three most recent. Recorded as
> **CORRECTION D-CORR-01** in document 25.

**Note the coincidence worth flagging:** run **#390** has `head_sha = 3b8eb8390959` — the
`keep_default_na` fix commit from document 21. The GICS check began failing at run **#389**, one
run **earlier**, so the fix commit is **not** the cause. Whether the two are related at all is
**UNKNOWN**; no causal claim is made.

**Job ordering confirms non-blocking placement** (verified from the workflow source):

```yaml
Check-GICS-Categorisation:
  needs: [Add-New-Ticker, Update-Compression-Files, Update-Categorization-Files,
          Update-README-Statistics]
```

Run #398 job start times, in order: `Add-New-Ticker` 15:07:40 → `Update-Compression-Files` 15:08:32
→ `Update-Categorization-Files` 15:09:25 → `Update-README-Statistics` 15:10:12 →
**`Check-GICS-Categorisation` 15:10:43 (failure)**. All four data-mutating jobs **succeeded and
pushed** before validation ran. The dataset on `main` has therefore **not satisfied the project's
own GICS invariant for 42 days**, across at least six update cycles, while remaining published and
served.

## 22.3 D-4 · `1 failed, 85 passed` — **REPRODUCED EXACTLY**

Executed at the pinned commit with the project's own CI-equivalent invocation
(`testing.yml` runs `uv run pytest tests/ --deselect
tests/test_validate_identifiers.py::test_database_identifiers_have_no_actionable_issues`):

```
FAILED tests/test_invariants.py::test_no_symbol_collisions_across_asset_classes
1 failed, 85 passed, 1 deselected in 42.43s
```

Failure output, verbatim:

```
>       assert (
            not collisions
        ), "Symbols appear in more than one asset-class file:\n" + …
E       AssertionError: Symbols appear in more than one asset-class file:
E           equities <-> etfs: ['CHAD'] (1 total)
E       assert not {('equities', 'etfs'): {'CHAD'}}

tests/test_invariants.py:95: AssertionError
```

Independent corroboration: the collision census in `f4_identity_fixtures.py` finds exactly one
cross-asset pair (`equities <-> etfs`) with exactly one symbol (`CHAD`) — document 20, CASE 1.

**Environment fidelity note (recorded for honesty).** A first attempt returned **87 errors**, not
`1 failed, 85 passed`, with `fixture 'disable_recording' not found` at `tests/conftest.py:503`.
Diagnosis: that fixture is supplied by **`pytest-recording`**, which the project's CI obtains via
`uv sync` from `uv.lock` but which was absent from the initially rebuilt venv. After pinning the
test stack to `uv.lock` exactly (pytest **9.0.3**, pytest-recording **0.13.4**, vcrpy **8.1.1**,
pytest-mock 3.15.1, pytest-timeout 2.4.0), the suite reproduced the reported result.

> **This is itself a governance datapoint.** The project's test suite **cannot be run at all**
> without the exact locked dependency set; a plausible-looking environment yields 87 spurious
> errors rather than a clear signal. `uv.lock` is therefore load-bearing for reproducibility, and
> — as document 09 established — `uv.lock` governs **CI only**, not what `pip install
> financedatabase` produces.

**Currency: CURRENT.** HEAD unchanged; the failure is live on `main` now.
**Affects: DATA** (the collision is in the dataset), detected by **CODE** (the invariant test).

## 22.4 D-5 · The deselected identifier test, run alone — **REPRODUCED, exact warning captured**

CI runs it as a separate job (`validate-identifiers`). Executed standalone:

```
tests/test_validate_identifiers.py::test_database_identifiers_have_no_actionable_issues
  /tmp/fdb2_repo/tests/test_validate_identifiers.py:298: UserWarning:
  2 identifier finding(s) require manual review (ambiguous CUSIPs or ISIN/CUSIP mismatches,
  e.g. dual-listed shares) and were left unchanged; run
  `uv run python -m financedatabase.validation.validate_identifiers database` for the full report.

1 passed, 1 warning in 4.17s
```

**Reproduced:** `1 passed` with a `UserWarning` — matching the original report, and now with the
**exact warning text and line number** (`test_validate_identifiers.py:298`), which the original did
not capture. The count **2** matches `evidence/identifier_issues.csv` (2 rows: `QVCGB` cusip
`74915L301` at `database/equities/NMS.csv:5316`, and `KMGH` cusip `483325109` at
`database/equities/PNK.csv:5982`, both `actionable=False`).

**Governance observation.** The suite's headline is green (`85 passed`) only because the one test
that inspects the live database is **deselected into a separate job** where it passes **with a
warning** rather than failing. Meanwhile the test that *does* fail (`CHAD`) is in the main job. So
the project simultaneously has a **failing** invariant in its main job and a **warning-only**
identifier check in its side job — two different tolerance regimes for two different data
invariants.

## 22.5 D-6 · **NEW FINDING** — an Identifier Validation workflow was built, tested, and never merged

The repository's registered workflows include one that **does not exist in the repository**:

| Property | Value |
|---|---|
| Name | **`Identifier Validation`** |
| Workflow id | `312400597` |
| Declared path | `.github/workflows/identifier_validation.yml` |
| State | **`active`** |
| Created | **2026-07-13T15:45:05Z** |
| Total runs | **2** |
| Run 1 | 2026-07-13T15:45:05Z · branch **`feature/validate-identifiers`** · event **`pull_request`** · conclusion **`success`** · `ea5521ad8e0e` · *"Add utility for validating security identifiers"* |
| Run 2 | 2026-07-16T09:16:11Z · branch **`feature/validate-identifiers`** · event **`pull_request`** · conclusion **`success`** · `73654f648e2c` · *"Add utility for validating security identifiers"* |

Verification that the file is **not** on the default branch:

| Check | Result |
|---|---|
| `GET /contents/.github/workflows?ref=a174c97d3bba` | `database_update.yml`, `linting.yml`, `testing.yml` — **3 files, no `identifier_validation.yml`** |
| `GET /contents/.github/workflows?ref=main` | **identical — 3 files** |
| `GET /commits?path=.github/workflows/identifier_validation.yml` | **`0` commits** |
| `git log --all --diff-filter=A -- '.github/workflows/*'` | no `identifier_validation.yml` addition anywhere |
| Local `git ls-tree HEAD .github/workflows/` | 3 files |

Meanwhile the **validator itself was merged**: `financedatabase/validation/validate_identifiers.py`
exists at the pinned commit, added by `5ae2910` (2026-07-16, Jon Højlund Arnfred,
*"Add utility for validating security identifiers (#159)"*).

> **Finding GOV-01 (new).** The project built a CI workflow to run identifier validation
> automatically, ran it **twice successfully on the PR branch**, merged the **validator** (PR #159)
> — and **did not merge the workflow**. On `main`, identifier validation is therefore
> **manual-only**: it runs when a human invokes it, and the one automated touchpoint is the
> **warning-only** test in §22.4.
>
> The workflow registration persists because GitHub retains workflow metadata after the file is
> removed from the branch — the `active` state is a **stale registration**, not evidence of a live
> gate.

**Bounded interpretation.** This is **not** evidence of negligence or of a security problem; the
same author (`Jon Højlund Arnfred`) also authored the `keep_default_na` fix (PR #166), so
data-quality work was clearly ongoing. Whether the omission was deliberate (e.g. runtime cost, or
the warning-only test was judged sufficient) is **UNKNOWN**. What is **verified** is the resulting
state: a validator with no automated schedule on `main`.

## 22.6 D-7 · **U-12 CLOSED** — the exact GICS failures, by re-execution

The CI log could **not** be fetched: GitHub's Actions log storage
(`productionresultssa12.blob.core.windows.net`) returned **EOF** from this host — a second
unreachable host alongside `raw.githubusercontent.com` (§19.1).

Instead the check was **re-executed locally** (`evidence/scripts/f5_gics_replication.py`),
replicating the workflow's inline script **exactly** — same `categories.json`, same
`pd.concat([pd.read_csv(f, index_col=0) for f in sorted(glob('database/equities/*.csv'))])`, same
`notna()` triple filter, same nested `gics[sector][industry_group][industry]` lookup, same
`KeyError` handling. **This is stronger evidence than the log would have been**: it is
reproducible, inspectable, and independent of log retention.

**Result: `invalid_row_count = 10`, `WORKFLOW_WOULD_RAISE = true`** — the workflow's
`raise ValueError(...)` fires, exactly reproducing the CI failure.

| # | Symbol | Violation | sector / industry_group / industry | Name | Country |
|---|---|---|---|---|---|
| 1 | `ACBA.DU` | industry **not in authority at all** | Financials / Diversified Financials / **Multi-Sector Holdings** | Ace Global Business Acquisition Li… | Hong Kong |
| 2 | `LTDH.DU` | industry **not in authority at all** | Information Technology / Software & Services / **Application Software** | Living 3D Holdings, Inc. | Hong Kong |
| 3 | `NOAC.DU` | industry **not in authority at all** | Financials / Diversified Financials / **Multi-Sector Holdings** | Natural Order Acquisition Corp. | United States |
| 4 | `1QY.F` | industry **not in authority at all** | Real Estate / Real Estate / **REIT - Industrial** | IND.LOG.PROP.TR. DL -,01 | United States |
| 5 | `1ZR0.F` | industry **not in authority at all** | Financials / Diversified Financials / **Multi-Sector Holdings** | ATLANTIC COASTAL ACQ. UT | United States |
| 6 | `MOP.F` | industry **not in authority at all** | Financials / Diversified Financials / **Asset Management** | Palmboomen Cultuur Maatschappij Mo… | Belgium |
| 7 | `1802.TW` | industry valid **elsewhere** (under Industrials), not under Materials | Materials / Materials / **Building Products** | Taiwan Glass Industry Corp | Taiwan |
| 8 | `1808.TW` | industry valid **elsewhere** (under Industrials), not under Real Estate | Real Estate / Real Estate / **Construction & Engineering** | Run Long Construction Co Ltd | Taiwan |
| 9 | `E1DU34.SA` | **industry_group not valid under this sector** | Consumer Staples / **Consumer Services** / Hotels, Restaurants & Leisure | NEW ORIENTALDRN | China |
| 10 | `T1AL34.SA` | **industry_group not valid under this sector** | Consumer Staples / **Consumer Services** / Hotels, Restaurants & Leisure | TAL EDUCATIODRN | China |

**Breakdown: 6 + 2 + 2 = 10.** Rows 9–10 are a **level-confusion** defect: `Consumer Services` is a
**sector** name being used in the **industry_group** position. Rows 7–8 are **pairing** violations
(the industry exists, but under a different industry group). Rows 1–6 use industry values that the
authority does not define at all.

**Common signature:** all 10 are **non-US-primary** listings — exchanges `DUS`(3), `FRA`(3),
`SAO`(2), and 2 whose `exchange` reads as `nan`; countries United States(3), Hong Kong(2),
Taiwan(2), China(2), Belgium(1). Several are depositary receipts (`…DRN`) or German
`Registered Shares DL -,0` style listings. **The invariant is violated at the edges of the corpus,
not in its US core** — consistent with README:467 (non-US data has no automated maintenance).

**Secondary observation.** Two of the 10 rows report `exchange = 'nan'`. That is the *same*
NA-coercion mechanism as document 21: the workflow's own check reads with
`pd.read_csv(f, index_col=0)` and **no** `keep_default_na=False`, so empty fields surface as the
string/float `nan`. The GICS job is therefore itself vulnerable to the defect that PR #166 fixed in
the library loader — the fix was applied to `helpers.py`, not to the workflow's inline script.

## 22.7 D-8 · **NEW FINDING** — the CI check has a blind spot, and the taxonomy discrepancy is now explained

**Root cause of the 10 failures, quantified:**

| Authority vs data | sectors | industry groups | industries |
|---|---:|---:|---:|
| `compression/categories/categories.json` (**the authority** the CI job checks against) | 11 | 24 | **69** |
| `database/equities/*.csv` (**the data**) | 11 | 24 | **80** |
| Delta | 0 | 0 | **+11 orphan industry values** |

The **11 orphan industry values** (present in the data, absent from the authority) and their row
counts:

```
Application Software 1 · Asset Management 1 · Conglomerates 1 · Industrial - Machinery 1 ·
Multi-Sector Holdings 3 · Oil & Gas Midstream 1 · REIT - Industrial 1 · Railroads 1 ·
Real Estate - Development 1 · Telecommunications Services 1 · Waste Management 2
= 14 rows total
```

`0` industries exist in the authority but are unused in the data; sectors and industry groups match
exactly on both sides.

> **This reconciles the original report's "GICS 11/24/80".** Document 04 reported 80 industries —
> that is the **data** count, and it is correct. The **authority** defines **69** (which happens to
> equal GICS's own published industry count). The original report noted the tension
> ("80 vs GICS's 69") without resolving it; the mechanism is now measured: **11 industry values
> were introduced into the data without being added to `categories.json`.**

> **Finding GOV-02 (new) — the check under-reports.** Of the **14** rows carrying an orphan
> industry, only **6** have a complete `sector`/`industry_group`/`industry` triple and therefore
> reach the CI check. The other **8** have an incomplete triple and are **excluded by the job's own
> `notna()` filter** — so they are **invisible to the validation entirely**.
>
> The 10 CI failures = 6 orphan-industry rows + 2 pairing violations + 2 level-confusion rows.
> Adding the 8 invisible orphan rows, the true count of taxonomy-inconsistent rows is **at least
> 18**, of which CI reports **10**.
>
> Context: 40,045 equity rows have an **empty** `industry` (35.5%) and are likewise outside the
> check's scope. The invariant therefore covers roughly **64%** of the corpus by construction and
> reports failures only within that subset. **A green run of this job would not mean the taxonomy is
> consistent** — it would mean the *fully-classified subset* is consistent.

## 22.8 D-9 · Release-blocker assessment

| Question | Answer |
|---|---|
| Is the `CHAD` failure a release blocker? | **No release is affected** — it is a **data** invariant failing on `main`. The last release (2.4.0, 2026-06-02) predates it. But it **is** a blocker for *trusting the current dataset* for any multi-asset join, and the project's own test suite treats it as a failure |
| Is the GICS failure a release blocker? | **Structurally, no — and that is the problem.** The job is placed last (`needs:` all four mutating jobs), so it **cannot** block: the data is committed and pushed before it runs. It has been failing for 42 days with no effect on publication |
| Does either affect the **released package**? | **No.** Release 2.4.0 contains only code (9 modules + metadata + LICENSE), no data. The data is fetched from `main` at runtime, so **released code consumes unvalidated `main` data** — the version-decoupling hazard of document 07 |
| Does either affect **code**? | No code defect is implied by either. `CHAD` is a dataset collision; the GICS failures are dataset taxonomy drift |
| Do they affect **data**? | **Yes, both** |
| Are they current? | **Yes** — HEAD unchanged since 2026-09-13; both reproduce today |
| Would they block an AHOS ingest? | **Yes, under document 14's boundary rule B-10** (cross-asset collisions ⇒ reject the snapshot) and **B-8** (schema/consistency assertion ⇒ reject on mismatch). AHOS's own proposed gates are **stricter** than the upstream project's |

## 22.9 Reproducibility of the Objective D evidence

| Finding | Reproducible? | How |
|---|---|---|
| 0 runs / 0 check-runs | **Yes** | Two GitHub API endpoints, no auth required; re-queryable at any time while the commit exists |
| 10 consecutive GICS failures | **Yes** | `/actions/workflows/55219164/runs` + per-run `/jobs`; archived in `evidence/followup/d_gics_sequence.json` |
| The 10 invalid GICS rows | **Yes, and better than the log** | `f5_gics_replication.py` re-executes the CI logic offline against the pinned commit |
| `1 failed, 85 passed` | **Yes, with a caveat** | Requires the `uv.lock`-exact test stack (§22.3). Without `pytest-recording`, the suite yields 87 spurious errors |
| The deselected test's warning | **Yes** | `pytest tests/test_validate_identifiers.py::test_database_identifiers_have_no_actionable_issues` |
| The unmerged Identifier Validation workflow | **Yes** | Workflow API + contents API at two refs + commits-by-path + `git log --all` |
| CI **log** contents | **No** | Log storage host unreachable from this sandbox. **Compensated** by local re-execution |

## 22.10 New and corrected evidence IDs

| ID | Claim | Method | Status |
|---|---|---|---|
| **EV-FU-D-01** | 0 workflow runs **and** 0 check-runs on **all three** 2026-09-13 bot commits (`a0c8b199`, `9f91e39c`, `a174c97d`) | GitHub API, both endpoints, per commit | **EXECUTION-VERIFIED** |
| **EV-FU-D-02** | Run #398 started at 15:07:37Z against `head_sha=fe5fbd83c6e4` and pushed all three commits during its own execution (15:08:25 / 15:09:17 / 15:10:38) | run + commit timestamps | **EXECUTION-VERIFIED** |
| **EV-FU-D-03** | **10** consecutive `Check-GICS-Categorisation` failures, #389 (2026-08-02T17:20:15Z) → #398 (2026-09-13T15:07:37Z); last success #388 (2026-08-02T12:47:55Z); 42-day span | per-job conclusions over 25 runs | **EXECUTION-VERIFIED** |
| **EV-FU-D-04** | `Check-GICS-Categorisation` declares `needs:` all four mutating jobs and started last (15:10:43) in run #398 — it cannot block publication | workflow source + job start times | **VERIFIED** |
| **EV-FU-D-05** | Suite result `1 failed, 85 passed, 1 deselected in 42.43s`; failure `tests/test_invariants.py:95`, `equities <-> etfs: ['CHAD'] (1 total)` | `pytest` at pinned commit, CI-equivalent deselect | **EXECUTION-VERIFIED** |
| **EV-FU-D-06** | Without `pytest-recording` (source of the `disable_recording` fixture, `tests/conftest.py:503`) the suite yields **87 errors**, not a clear signal | failed first attempt, then diagnosed and fixed | **EXECUTION-VERIFIED** |
| **EV-FU-D-07** | The deselected identifier test passes standalone with a `UserWarning` at `test_validate_identifiers.py:298` reporting **2** findings requiring manual review | `pytest` single test | **EXECUTION-VERIFIED** |
| **EV-FU-D-08** | Workflow **`Identifier Validation`** (id 312400597, created 2026-07-13, state `active`) ran **twice**, both on branch `feature/validate-identifiers` as `pull_request`, both `success`; the file exists at **no** ref on the default branch and has **0** commits touching that path | workflow API + contents API ×2 refs + commits-by-path + `git log --all` | **EXECUTION-VERIFIED** |
| **EV-FU-D-09** | The validator **was** merged: `financedatabase/validation/validate_identifiers.py` added by `5ae2910`, 2026-07-16, PR **#159** | `git log -- financedatabase/validation` | **EXECUTION-VERIFIED** |
| **EV-FU-D-10** | Local replication of the CI GICS check yields exactly **10** invalid rows and would raise: 6 unknown-industry, 2 mis-paired industry, 2 level-confusion (`Consumer Services` used as an industry_group) | `f5_gics_replication.py` | **EXECUTION-VERIFIED — closes U-12** |
| **EV-FU-D-11** | `categories.json` = 11/24/**69**; data = 11/24/**80**; **11** orphan industry values across **14** rows; 0 authority industries unused | set comparison | **EXECUTION-VERIFIED** |
| **EV-FU-D-12** | **Blind spot:** of the 14 orphan-industry rows, only **6** have a complete triple and reach the check; **8** are excluded by the job's own `notna()` filter. 40,045 rows have an empty `industry` and are out of scope | filter replication | **EXECUTION-VERIFIED** |
| **EV-FU-D-13** | 2 of the 10 failing rows show `exchange='nan'` — the CI script reads without `keep_default_na=False`, so it remains vulnerable to the defect PR #166 fixed in the library | replication output | **EXECUTION-VERIFIED** |
| **EV-FU-D-14** | GitHub Actions log storage (`productionresultssa12.blob.core.windows.net`) is unreachable from this host (EOF) | `gh api …/logs` | **EXECUTION-VERIFIED** |
| **EV-FU-D-15** | Cause of the zero-run behaviour (recursion guard vs `secrets.PAT` vs repo setting) | not determinable externally | **UNKNOWN — U-10 unchanged** |

## 22.11 Bounded conclusion

What is established: **the upstream project's data-mutating commits are ungated; its taxonomy
invariant has been failing for 42 days without blocking publication; its cross-asset symbol
invariant fails on `main` today; its identifier validator has no automated schedule on `main`; and
its taxonomy check under-reports by excluding incompletely-classified rows.**

What is **not** established, and is not claimed: that the project is unreliable in general, that
these failures caused any data corruption beyond the 18 identified rows, that the maintainers are
unaware, or that any of this constitutes a security defect. The dataset's identifier quality
remains **excellent** where identifiers exist (2 invalid of 249,085 — 99.9992%), and the project's
willingness to ship a failing test visibly on `main` is, if anything, a transparency credit.

**For AHOS the operational conclusion is unchanged and does not depend on any of this:** the data
must be treated as **untrusted input**, ingest must assert its own invariants, and none of it may
reach a decision surface. Document 14's boundary rules B-8 and B-10 are **stricter** than the
upstream gates, which is the correct posture when consuming a dataset whose own gates are
non-blocking.

**No AHOS file was modified. No extrapolation to a security or reliability certification is made.**
