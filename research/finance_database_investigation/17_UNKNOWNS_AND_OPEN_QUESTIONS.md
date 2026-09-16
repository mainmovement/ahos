# 17 — Unknowns & Open Questions

**Phase 17.** Every question this investigation could **not** answer, with the reason, the impact
on the conclusions, and what would resolve it.

> **Doctrine.** `UNKNOWN ≠ SAFE`. An unanswered question is never treated as a favourable answer.
> Where an unknown could change the recommendation, that is stated explicitly. None of the
> unknowns below reverses the judgment in §18 — and the ones that *could* are flagged as such.

---

## 17.1 Register

### U-01 · The package's **default** (remote) data path could not be exercised

| | |
|---|---|
| **Question** | How does `financedatabase` behave when loading data the supported way — `fd.Equities()` with no arguments, fetching from `raw.githubusercontent.com`? |
| **Why unknown** | That host is **unreachable from the audit environment**: `curl` exit 35, `OpenSSL SSL_connect: SSL_ERROR_SYSCALL`, while `github.com`, `api.github.com`, `codeload.github.com` and `files.pythonhosted.org` all return HTTP 200 (EV-ENV-06). A single probe did execute far enough to confirm the failure mode: `ValueError: Failed to load data from https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/cryptos.bz2: HTTPSConnectionPool(host='raw.githubuserconten…` (EV-ARCH-03) |
| **What we did instead** | Ran every library-level test with `use_local_location=True` from a **sparse clone of the pinned commit**, which resolves to `Path(__file__).parent.parent/"compression"` and yields the identical code path minus the HTTP fetch |
| **Impact** | **LOW on data conclusions** — the bytes parsed are the same bytes. **MEDIUM on latency conclusions** — no cold-start, TLS-handshake or CDN-cache numbers exist (§10.8). **HIGH on the AHOS constraint verdict**, but in the *conservative* direction: a dependency we cannot reach is a dependency we reject |
| **Resolution** | Re-run `evidence/scripts/a6_query_engine.py` with the remote path from a network that can reach `raw.githubusercontent.com`; record timings and artifact SHA-256s |

### U-02 · Whether the served `main` today is byte-identical to the pinned clone

| | |
|---|---|
| **Question** | Does the data a live `fd.Equities()` would download now match `database/*.csv` at commit `a174c97d3b`? |
| **Why unknown** | Follows from U-01 — the remote path is unreachable, and the pinned clone is by definition a snapshot of one commit |
| **Impact** | **LOW.** The automation runs Sunday 12:00 UTC; the pinned commit is 2026-09-13 (a Sunday). A further bot commit before this investigation completed cannot be excluded |
| **Resolution** | Compare per-file SHA-256 of the served `.bz2` artifacts against the clone; or re-clone and diff. **This is also the reason §14.6 mandates hash pinning rather than trusting `main`** |

### U-03 · What a fresh `pip install financedatabase` actually resolves to on the AHOS Windows host

| | |
|---|---|
| **Question** | Which `financetoolkit`, `pandas`, `numpy` and `yfinance` versions land on Python 3.11+ / Windows under AHOS's constraints? |
| **Why unknown** | Not installed into the AHOS environment (prohibited without authorization). The research venv installed `financedatabase 2.4.0 --no-deps` and `financetoolkit` was **deliberately not installed** (EV-ENV-03, EV-EXT-11) |
| **What is known** | The resolver *must* pick `financetoolkit ≥2.2.0` on Python ≥3.11 (2.1.3 is the last to allow 3.10), which requires `pandas>=3.0` and an **unpinned `yfinance`** (EV-EXT-05, EV-EXT-08) |
| **Impact** | **MEDIUM.** Reinforces EI-04 (pandas 3 vs AHOS's `pandas>=2.1.0` floor) but does not prove the exact tree |
| **Resolution** | `pip install --dry-run --report - financedatabase==2.4.0` on the target host, in a throwaway venv, with the report archived |

### U-04 · Provenance of the bulk dataset, and the vintage of the crypto table

| | |
|---|---|
| **Question** | Where did the ~304,495 rows originally come from, and when was the crypto table last substantively refreshed? |
| **Why unknown** | **No script in the repository generates** `cryptos.csv`, `currencies.csv`, `indices.csv`, `moneymarkets.csv`, `etfs/`, `funds/`, or the non-US `equities/` shards (EV-LEG-05). No provenance manifest, no source column, no ingest date exists anywhere (EV-SCH-08). README:467 attributes ongoing maintenance to community contributions but says nothing about origin |
| **What is inferred** | Yahoo Finance and CryptoCompare, from the `CCC`/`CCY` exchange codes, the `<TOKEN>-<QUOTE>` and `BASEQUOTE=X` symbol conventions, and the profile-style `summary` prose (EV-LEG-07, EV-CR-11). The crypto universe's composition — 352 tickers, `SRM` still present, no post-2021 asset — points to **~2020**. **This is INFERENCE, not verified provenance** |
| **Impact** | **HIGH for §12** (the legal question turns on it) and **HIGH for §08** (the crypto verdict). But both verdicts are *conservative under uncertainty*: undocumented provenance ⇒ legal review required; ~2020 vintage ⇒ stale ⇒ reject |
| **Resolution** | Ask the maintainer; inspect the earliest commits touching each CSV (`git log --diff-filter=A --follow`); search the issue tracker for a provenance discussion |

### U-05 · The `JeroenBouma` account and whether that repository path ever existed

| | |
|---|---|
| **Question** | Did `github.com/JeroenBouma/FinanceDatabase` ever exist? Why does an account with that name hold zero repositories? |
| **Why unknown** | GitHub's API exposes no rename history and no deleted-repository records. The two accounts have **different user IDs** (46189588 vs 46355364), which rules out a simple rename (EV-SRC-02) |
| **What is known** | As of 2026-09-15 the path returns **404** and the account has **0** public repos, 1 follower, created 2018-12-27, last updated 2023-10-05 (EV-SRC-01, EV-SRC-02) |
| **Impact** | **LOW on technical conclusions.** Recorded as SEC-04 — an **ecosystem/typosquatting exposure**, because much third-party material (including this tasking) cites the 404 path for a project whose clients fetch data over HTTPS from a hardcoded URL |
| **Resolution** | Wayback Machine lookup of the URL; GitHub Support. **No allegation is made about any party** |

### U-06 · Data ownership

| | |
|---|---|
| **Question** | Who owns the dataset — the maintainer, the contributors, or the upstream sources? |
| **Why unknown** | No CLA, no DCO, no copyright assignment, no `NOTICE`, no dataset licence (EV-LEG-03, EV-LEG-10). The MIT notice names one individual and covers "software and associated documentation files" |
| **Impact** | **HIGH for §12.** Ownership determines who could grant a licence to vendor or redistribute |
| **Resolution** | **LEGAL REVIEW REQUIRED**, plus a direct question to the maintainer |

### U-07 · Whether the maintainer intends the dataset to be MIT-licensed

| | |
|---|---|
| **Question** | Is the single root `LICENSE` meant to cover `database/` and `compression/`, or only `financedatabase/`? |
| **Why unknown** | No public statement located in the reviewed scope: not in `README.md`, not in `CONTRIBUTING.md` (which discusses contribution mechanics and identifier validation but never data licensing), not in `compression/README.md` (which discusses only file format and download cost), not in the issue tracker items retrieved |
| **Impact** | **HIGH for §12** — this is the crux of LEG-01 |
| **Resolution** | Open an issue asking explicitly; or obtain written confirmation. Until then: **LEGAL REVIEW REQUIRED** |

### U-08 · The scope of `secrets.PAT`

| | |
|---|---|
| **Question** | Is the personal access token used by `database_update.yml` minimally scoped (e.g. `repo` on this repository only), or broader? |
| **Why unknown** | Repository secrets are not readable by design |
| **What is known** | Its **usage** is verified: materialised into a `git pull` URL (`:17,294,359,475`) and followed by `git push` (`:275-282`) in the same job ⇒ it has **write** access to `main` (EV-SEC-07) |
| **Impact** | **MEDIUM for §11.** Determines blast radius if the third-party action or the upstream repo is compromised |
| **Resolution** | Only the maintainer can answer. The AHOS control (pin by SHA + hash) is effective regardless of the answer |

### U-09 · PyPI publication method and provenance attestation

| | |
|---|---|
| **Question** | How are releases published to PyPI, and does the publisher have 2FA and/or PEP 740 provenance attestations? |
| **Why unknown** | There is **no publish/release workflow** in `.github/workflows/` (only `database_update.yml`, `testing.yml`, `linting.yml`), so publication appears manual — but the absence of a workflow does not prove the method. The PyPI JSON API exposes no attestation data for this project, and Sigstore was not consulted (EV-SEC-11, EV-SEC-17) |
| **Impact** | **LOW–MEDIUM.** The artifacts themselves are hash-verified (EV-ENV-04) and the code surface is tiny and clean (EV-SEC-01) |
| **Resolution** | `https://pypi.org/project/financedatabase/2.4.0/` provenance page; `sigstore` verification; PyPI publisher settings |

### U-10 · Why bot data commits trigger zero workflow runs

| | |
|---|---|
| **Question** | What suppresses CI on the commits that actually change the data? |
| **Why unknown** | Three candidate mechanisms are consistent with the observation: GitHub's `GITHUB_TOKEN` recursion guard, an effect of pushing with `secrets.PAT`, or a repository/path-filter setting. The **effect** is verified; the **cause** is not |
| **What is known** | `GET /actions/runs?head_sha=a174c97d3b…` → `total_count: 0`; `GET /commits/a174c97d3b…/check-runs` → `total_count: 0` (EV-PIPE-09). The last successful `Run Tests` was 2026-09-11 against human PR commit `61d2feac` |
| **Impact** | **MEDIUM.** The cause does not change the finding (DQ-03): data-changing commits are ungated, so the invariant tests never see them |
| **Resolution** | Inspect repository Actions settings and the workflow's path filters; or observe the next bot commit with the maintainer's cooperation |

### U-11 · Why the `push: branches: [main]` trigger does not loop

| | |
|---|---|
| **Question** | `database_update.yml` triggers on every push to `main`, **including its own pushes**. What prevents an infinite loop? |
| **Why unknown** | Candidates: GitHub's recursion guard, the `git diff-index --quiet HEAD ||` guard at `:281`, or the push identity. Observed behaviour at HEAD shows no loop; the mechanism is not determinable from outside |
| **Impact** | **LOW.** No runaway automation was observed |
| **Resolution** | Same as U-10 |

### U-12 · Which rows fail the GICS invariant

| | |
|---|---|
| **Question** | `Check-GICS-Categorisation` fails on three consecutive runs (2026-09-06, 09-11, 09-13). **Which** sector/industry-group/industry triples are invalid, and in how many rows? |
| **Why unknown** | The job log was not retrieved. The API exposes the **conclusion** (`failure`) but the log content was not fetched |
| **Impact** | **MEDIUM.** We know the invariant is violated (verified) but not the extent. It does not weaken the finding — only its precision |
| **Resolution** | `GET /repos/JerBouma/FinanceDatabase/actions/runs/<id>/logs`; or re-run the project's own GICS consistency check locally against the pinned clone — which is cheap and is the recommended first action if this matters |

### U-13 · Whether identifier-less new tickers are ever backfilled

| | |
|---|---|
| **Question** | `build_new_ticker` writes `NaN` into all five identifier fields and the refresh guard is unreachable for existing rows (EV-PIPE-06). Is there **any** path — another job, a manual process, a community PR — that later fills them in? |
| **Why unknown** | Confirming a negative across run history would require diffing many weekly snapshots, which was not done |
| **What is known** | At the pinned commit, 73–78% of equities and ETFs have no `isin`/`cusip`/`figi`, and **7,425 rows (6.59%)** have `isin`, `cusip`, `figi` and `summary` all empty simultaneously (EV-PIPE-07) — consistent with "never backfilled", but not proof |
| **Impact** | **MEDIUM.** If backfilling exists, the coverage numbers would improve over time; the *current* numbers are measured and stand |
| **Resolution** | Diff two snapshots N weeks apart and track a cohort of newly-added symbols |

### U-14 · Which commit reduced the equity count from 158,429 to 112,690

| | |
|---|---|
| **Question** | The official website still shows **158,429** equities; the data and the auto-generated README show **112,690**. When and why did ~29% disappear? |
| **Why unknown** | The repository was not bisected. The **mechanism** is verified — a global `drop_duplicates(keep='first')` at `database_update.yml:260` over three `pd.concat`'d feeds (`:185`) — but the specific commit was not identified |
| **Impact** | **LOW on the conclusion** (SR-02 stands either way: the website is stale and the reduction is real). **MEDIUM on interpretation** — a deliberate cleanup and an accidental mass-deletion look identical in the final counts |
| **Resolution** | `git log --follow -p database/equities/` with row counts per commit; or diff weekly snapshots. **Status of the causal claim: INFERENCE** |

### U-15 · Cross-version identifier stability

| | |
|---|---|
| **Question** | Is a given row's `isin`/`cusip`/`figi` stable across releases and across data commits? |
| **Why unknown** | Two versions were not diffed field-by-field. Release 2.4.0 (2026-06-02) and `main` (2026-09-13) were compared structurally (EV-SRC-05: `validation/` absent from the wheel, 8-line `helpers.py` delta) but not row-by-row on identifiers |
| **Impact** | **MEDIUM.** Identifier instability would make any long-lived AHOS mapping unsafe. Stability is *assumed by no one* here — the recommendation is to pin by SHA and re-derive, which is safe under either answer |
| **Resolution** | Join two pinned snapshots on symbol and diff the five identifier columns |

### U-16 · Whether symbols are actually recycled

| | |
|---|---|
| **Question** | Has any symbol in this dataset been reassigned from one instrument to another over time? |
| **Why unknown** | There is **no temporal dimension** — no `valid_from`/`valid_to`, no epoch, no prior-holder record — so recycling is **undetectable from a single snapshot**. The *mechanism* by which it would be mishandled is verified: `keep='first'` at `:260`, where the survivor depends on `sorted(glob(...))` filename order |
| **Impact** | **MEDIUM.** Recorded as scenario S-06 with status **UNKNOWN** — mechanism verified, instance not observed. No claim of recycling is made, and no claim of its absence is made |
| **Resolution** | Diff snapshots over months and look for a symbol whose `name`/`isin`/`country` changed wholesale |

### U-17 · Windows behaviour — paths, encoding, locale

| | |
|---|---|
| **Question** | Does the mixed-separator path construction (`helpers.py:59`, `:327`) and the absence of an explicit `encoding=` to `pd.read_csv` cause failures or mojibake on a Windows host, particularly under a non-UTF-8 active code page? |
| **Why unknown** | **The audit host is Linux** (EV-ENV-01). Per AHOS doctrine, *Linux validation ≠ Windows validation*, and the designated AHOS host is Windows |
| **What is known** | Mixed separators are tolerated by Windows APIs and pandas, so the path risk is assessed **LOW**. The data demonstrably contains non-ASCII (`Börslich handelbare Krügerrand`, `S.p.A.`, `Crédit Agricole`), so the encoding risk is assessed **MEDIUM**. Both are **INFERENCE / PARTIALLY_VERIFIED** (EV-PERF-09, EV-PERF-10) |
| **Impact** | **LOW on the recommendation** — the recommendation does not depend on Windows behaviour, because the runtime dependency is rejected on other grounds |
| **Resolution** | Re-run the evidence scripts on the AHOS Windows host with a non-UTF-8 locale; record results separately. **This is the one unknown that must be closed before any Windows-specific claim is made** |

### U-18 · Whether the `raw.githubusercontent.com` failure is environment-specific

| | |
|---|---|
| **Question** | Is the TLS failure (EV-ENV-06) an artifact of this sandbox, or would it also affect the designated AHOS Windows host and the Iran-resilient network path AHOS is designed for? |
| **Why unknown** | Only one environment was tested. No diagnosis of *why* the TLS handshake fails was performed (no cipher-suite inspection, no SNI test, no alternate-resolver test) |
| **What is known** | Other GitHub-owned hosts (`github.com`, `api.github.com`, `codeload.github.com`) succeed from the **same** host, which makes a blanket GitHub block unlikely and points at something specific to `raw.githubusercontent.com` — a CDN edge, a certificate, or a filtering rule |
| **Impact** | **HIGH on the AHOS constraint verdict, in the conservative direction.** S-14/S-15 are rated CRITICAL on the strength of a *measured* failure. If the failure is sandbox-specific, the finding weakens to "untested under the target network" — but the underlying architectural problem (a hard runtime dependency on a single mutable remote host, with no cache, no fallback and no offline mode for pip installs) is **independent of this unknown** and is verified from source |
| **Resolution** | Test from the AHOS Windows host and from a representative Iran-path network (with and without `PySocks`/`ALL_PROXY`). Until then the finding stands as measured |

---

## 17.2 Deliberate non-tests

These were **not attempted**, on principle. Recorded so the absence is not mistaken for a gap.

| # | Not tested | Reason |
|---|---|---|
| N-1 | Decompression bomb / resource-exhaustion PoC against the live host | Would constitute an attack on a third-party service. The **mechanism** is verified from source (no size cap on `response.content`, unbounded bz2 expansion, no row-count guard) |
| N-2 | End-to-end `to_toolkit()` performance | `financetoolkit` was deliberately not installed, so any timing would mix FinanceDatabase, FinanceToolkit, `yfinance` and network latency with no way to attribute. **Attribution rule: a measurement you cannot attribute is not evidence** |
| N-3 | Installing anything into the AHOS environment | Prohibited by the tasking without separate authorization |
| N-4 | Modifying any AHOS file | Prohibited. All AHOS-side access was read-only (EV-AHOS-09, EV-AHOS-10) |
| N-5 | Running the project's validator with `--apply` | Would modify the dataset. Run **read-only** only (EV-DQ-01) |
| N-6 | Full 304,495-row formula-injection scan | Out of proportion to the risk; spot checks found no `=`-prefixed cells. Recorded as **NOT VERIFIED**, not as "clean" |
| N-7 | Confusable-name (typosquat) enumeration on PyPI | Not required for the decision; recorded as **UNVERIFIED** |
| N-8 | Fetching the failing GICS job log | Available and cheap — see U-12. Not fetched within this investigation's scope |

## 17.3 Open questions worth asking the maintainer

If AHOS ever engages with this project, these are the highest-value questions, in priority order:

1. **Is the dataset in `database/` and `compression/` intended to be covered by the root MIT
   `LICENSE`, and if so, does that extend to the underlying facts, identifiers and `summary`
   prose?** (U-06, U-07, LEG-01) — *the single question that most affects any reuse decision*
2. **What is the provenance of the non-US equities and of the `cryptos`, `currencies`, `indices`,
   `funds`, `etfs` and `moneymarkets` tables?** (U-04, LEG-03)
3. **Is the `cryptos` table maintained at all, and is `SOL`/`BTC` absence known?** (EV-CR-06,
   EV-CR-10) — *no CI job writes it*
4. **Why does `Check-GICS-Categorisation` run last, after the data is pushed, and is its failure
   known?** (U-12, DQ-03, DQ-04)
5. **Is the `CHAD` cross-asset symbol collision known, given that
   `test_no_symbol_collisions_across_asset_classes` fails on `main`?** (EV-ID-04)
6. **Was the ~29% reduction in equity rows (158,429 → 112,690) intentional?** (U-14, SR-02)
7. **Will release 2.4.0's loader gain `keep_default_na=False, na_values=[""]`, so that installed
   users stop losing the ticker `NA`?** (EV-DQ-05, S-13)
8. **Will `numpy`, `pandas` and `requests` be declared as direct dependencies?** (EV-EXT-02, EI-01)
9. **Will `jannekem/run-python-script-action@v1.8` be pinned to a commit SHA, and the other
   actions likewise?** (EV-SEC-07, EV-SEC-08, SEC-05)
10. **Will the website's statistics be regenerated from the data?** (EV-SRC-04, SR-02)

## 17.4 Do any unknowns change the recommendation?

| Unknown | Could it reverse the judgment? |
|---|---|
| U-01, U-02 | **No.** Data conclusions rest on the pinned clone; the conservative direction is unaffected |
| U-03 | **No.** Reinforces an existing FAIL |
| **U-04, U-06, U-07** | **Partially — and only upward.** Clear, permissive dataset licensing with documented provenance would remove the LEGAL REVIEW REQUIRED gate and make the §14.6 vendored-snapshot path viable for a future non-crypto lane. It would **not** create crypto value, fix the missing identifiers, add timestamps, or repair the fail-open query API |
| U-05 | **No.** Ecosystem note only |
| U-08, U-09, U-10, U-11 | **No.** Controls in §14.5 are effective regardless |
| U-12 | **No.** Precision only |
| U-13, U-15 | **No.** Pinning + re-derivation is safe under either answer |
| U-14 | **No.** The discrepancy is verified either way |
| U-16 | **No.** Recorded as UNKNOWN; no claim is made in either direction |
| U-17 | **No** for the recommendation. **Yes** for any Windows-specific statement — which is why none is made |
| **U-18** | **No.** Even if the TLS failure is sandbox-specific, the architectural dependency (single mutable remote host, no cache, no fallback, no offline mode for pip installs) is verified from source and independently disqualifying for AHOS's constraints |

**Conclusion: no unknown reverses the judgment.** The only unknowns with upward force are the legal
ones (U-04, U-06, U-07), and even a fully favourable answer would move the assessment from
**C. RESEARCH-ONLY VALUE** to at most **B. RECOMMENDED WITH STRICT BOUNDARIES — for a future
non-crypto lane that does not currently exist**. The crypto rejection (**E**) rests on the absence
of `chain`, `address`, price, volume, liquidity, market cap and freshness — none of which is
unknown, and all of which were verified by direct measurement.
