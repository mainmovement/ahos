# 07 — Data Quality, Freshness & Trust

**Phase 7.** Every claim below is classified. Vocabulary used exactly as the tasking requires:
`VERIFIED` · `PARTIALLY_VERIFIED` · `UNVERIFIED` · `UNKNOWN` · `STALE` · `NOT_APPLICABLE`.

The words "real-time" and "accurate" are used only with an explicit validation method attached.

---

## 7.1 Update cadence and triggering

| Question | Answer | Status |
|---|---|---|
| How often is data updated? | Weekly, **Sunday 12:00 UTC** (`cron: '0 12 * * SUN'`), plus on every push to `main`. Observed data commits: **2026-08-25, 08-30, 09-06, 09-11, 09-13** | **VERIFIED** — `database_update.yml:7-8` + `git log` + GitHub API |
| What is actually updated? | **US-listed equities only**, from three JSON feeds in `rreichel3/US-Stock-Symbols`. Confirmed by README:465: *"For American exchanges, the database automatically updates every Sunday"* | **VERIFIED** — `:167-185` |
| What is **not** updated? | Non-US equities, and **all** ETFs, funds, indices, currencies, cryptos and money markets. README:467: *"When companies outside American exchanges undergo changes (migrations, mergers, bankruptcies), we depend on community members to identify and update these entries."* There is **no job anywhere in the workflow** that writes to `database/cryptos.csv`, `currencies.csv`, `indices.csv`, `moneymarkets.csv`, `etfs/` or `funds/` — they are only *read* by the compression/categorization jobs | **VERIFIED** — grep of the workflow for every `to_csv` target |
| How are updates triggered? | GitHub Actions schedule + push. Commits authored `GitHub Action <action@github.com>`, pushed with `secrets.PAT` | **VERIFIED** |
| Is the update auditable? | Only through git history of `database/*.csv` in a ~4.85 GB repository. No changelog, no diff artifact, no release notes per data revision | **PARTIALLY_VERIFIED** |

**Finding DQ-01 — the cryptocurrency table has no update mechanism at all.** It is a static
snapshot. Its content (352 token tickers dominated by 2017–2019 altcoins; `SRM`/Serum still
present and not flagged despite the 2022 FTX collapse; no `SOL`, no `PEPE`, no `SHIB`) is
consistent with a **~2020 Yahoo Finance crypto screener export**. The exact origin is
**UNVERIFIED** (U-04) — no script in the repository generates it. Status of the crypto dataset:
**STALE**, on the order of **five to six years**.

## 7.2 Timestamps

| Question | Answer | Status |
|---|---|---|
| Does the data have timestamps? | **No.** Zero columns matching `date\|time\|updated\|asof\|as_of\|timestamp\|snapshot\|version\|source\|provider\|retrieved` across **all seven** schemas | **VERIFIED** (column-name scan, §4.0 SC-01) |
| Do timestamps represent source time or update time? | **NOT_APPLICABLE** — there are none | — |
| Can per-record staleness be computed? | **No.** The finest available granularity is the **file**, whose date comes from the git commit, not from the data | **VERIFIED** |
| Is there a `retrieved_ts` for AHOS's `IdentitySource`? | **No** | **VERIFIED** |

**Consequence for AHOS:** the doctrine `STALE ≠ LIVE` cannot be *enforced* against this data,
because the data provides no basis for the comparison. An AHOS adapter would have to **synthesize**
freshness from the ingest moment and the pinned commit date, and mark every record `STALE`
unless the snapshot is inside a declared window. It must never present a FinanceDatabase value
as current.

## 7.3 Delisted instruments and survivorship bias

| Question | Answer | Status |
|---|---|---|
| Do delisted instruments remain? | **Yes, for equities.** `delisted`: `False` 102,286 · `True` **10,404** (9.23% of 112,690). README:465: *"Delisted tickers are intentionally retained for historical research purposes."* | **VERIFIED** |
| Are stale records removed? | **No** — retention is deliberate and documented | **VERIFIED** |
| Is the dataset survivorship-biased? | **Partially mitigated for US equities.** Retaining 10,404 delisted rows is a genuine and unusual anti-survivorship property. **But**: (a) only equities have the flag — ETFs and Funds do not (open issue **#153**, 2026-06-03); (b) non-US equities have no automated maintenance, so non-US delistings are almost certainly under-recorded; (c) the crypto class has no delisting concept at all, so dead tokens like `SRM`, `BURST`, `DIME`, `GBYTE`, `MAID`, `NYZO`, `PZM` sit alongside live ones with no distinction | **PARTIALLY_VERIFIED** |
| Are symbols recycled? | **Possible and unguarded.** Symbols are the primary key; nothing records a symbol's prior holder. `delisted=True` rows keep their symbol, so a recycled symbol would collide with the historical row and be resolved by `keep='first'` (§3.4.3). We found **no** confirmed instance of recycling | **UNKNOWN** (U-16) — mechanism verified, instance not observed |
| Default query behaviour | `Equities.select(exclude_delisted=True)` **by default** → a naive caller sees only 102,286 rows and silently loses the delisted population. `search()` does **not** exclude them by default → the two APIs return different populations for identical criteria (§6.3) | **VERIFIED** |

## 7.4 Versioning, reproducibility and history

| Question | Answer | Status |
|---|---|---|
| Are records versioned? | **No.** No `valid_from`/`valid_to`, no SCD-2, no revision column | **VERIFIED** |
| Can historical states be reconstructed? | **Only via git.** `git checkout <sha> -- database/` on a ~4.85 GB repository. There is no published per-date snapshot, no data release, and **no tag on the data** — tags (`2.4.0`, `2.3.1`, …) mark *code*, not data | **PARTIALLY_VERIFIED** (mechanism exists; not exercised) |
| Is source provenance retained? | **Effectively no.** The only provenance signals in the entire dataset are `cryptos.exchange == 'CCC'` (CryptoCompare, 3,362 rows) and `currencies.exchange == 'CCY'` (2,556 rows). Equities, ETFs, funds, indices and money markets carry **no source field**. Commit messages are generic (`Update database with new tickers`) | **VERIFIED** |
| Are changes auditable? | At file level via git; **not at record level**. No per-row change log | **PARTIALLY_VERIFIED** |
| Can the dataset be reproduced from a specific version? | **No — this is the central reproducibility defect.** `DATA_REPO` is hardcoded to `…/**main**/compression/` (`helpers.py:12-14`). There is no data-version parameter, no ETag, no `If-Modified-Since`, no manifest, no checksum. The *code* is pinned by PyPI version; the *data* is not pinned by anything | **VERIFIED** |
| Do two machines with the same pinned package version get the same data? | **Only if they install on the same day.** Between weekly runs, `main` changes under them | **VERIFIED** (mechanism) |

**Finding DQ-02 — code and data are version-decoupled, and they have already diverged.**

```
2026-06-02  release 2.4.0  ─────────────── code that users install
                 │  3.5 months
2026-09-13  main a174c97d  ─────────────── data that ALL users download
                 │
                 └─ main's helpers.py changed read_csv semantics
                    (+ keep_default_na=False, na_values=[""])
                    release 2.4.0 did NOT
```

Measured consequence (§3.4.4, `evidence/scripts/a11_na_bug.py`): reading the **same**
`equities.bz2` with the two versions' semantics gives

| Read semantics | index NaN count | `'NA' in index` | `.loc['NA']` |
|---|---:|---|---|
| **release 2.4.0** | **1** | **False** | **KeyError** |
| **main HEAD** | 0 | True | row returned |

So **every `pip install financedatabase==2.4.0` user loses the ticker `NA` (Nano Labs) today**,
and `FinanceFrame.to_toolkit()` compounds it: `symbols = self[self.index.notna()].index.to_list()`
(`helpers.py:257`) silently drops NaN index entries, so the symbol never reaches downstream code
and no error is raised. Cell-level NaN counts were **identical** between the two semantics — the
damage is confined to the index. **VERIFIED** by direct execution.

## 7.5 Look-ahead bias and backtest suitability

| Question | Answer | Status |
|---|---|---|
| Does it contain look-ahead bias risks? | **Yes, structurally.** The dataset is a **current-state snapshot with no temporal dimension**. Every classification field (`sector`, `industry_group`, `industry`, `country`, `currency`, `market_cap`) reflects *today's* understanding and is applied to all 112,690 rows, including the 10,404 delisted ones. Any backtest that filters on `sector` or `market_cap` is implicitly using future knowledge of how each security was eventually classified | **VERIFIED** (structural); magnitude **UNKNOWN** |
| Is `market_cap` point-in-time? | **No.** It is a bucket label derived once, from a third-party JSON `marketCap` field, at first sight — and, per the dead-code bug at `database_update.yml:230`, **never refreshed thereafter** for existing tickers | **VERIFIED** (source); cross-run confirmation **UNKNOWN** (U-13) |
| Can a historical universe be reconstructed for date *T*? | **No**, not without a git checkout of the data as of *T*, and even then only for dates after the repository's history begins, and only approximately (the snapshot at *T* still carries *T*-current classifications) | **VERIFIED** (mechanism) |
| Is it suitable for backtesting? | **For universe/classification context: marginally, with explicit caveats and a pinned git SHA.** **For anything price- or volume-based: NO — there are no prices or volumes.** **For point-in-time-correct classification: NO** | Judgment on verified facts |
| Is it suitable for live decisions? | **NO.** No timestamps, unpinned mutable source, no integrity verification, no per-record freshness, fail-open query API, and a currently-failing validation job | **VERIFIED** |

## 7.6 Validation posture — what the project checks, and whether it works

| Check | Where | Runs on data commits? | Current status |
|---|---|---|---|
| GICS triple `(sector, industry_group, industry)` vs `categories.json` | `database_update.yml:582-627` | Yes — but **last**, after the data is committed and pushed, so it **cannot block** | **FAILING** on the 2026-09-13, 2026-09-11 and 2026-09-06 runs (run 34764660277: 4 jobs `success`, `Check-GICS-Categorisation` `failure`) |
| Cross-asset symbol collisions | `tests/test_invariants.py:66-100` | **No** | **FAILING at HEAD** — reproduced by us: `equities <-> etfs: ['CHAD']`; `1 failed, 85 passed` |
| Cross-asset ISIN collisions | `tests/test_invariants.py:103-122` | **No** | passing |
| `delisted` strict boolean dtype | `tests/test_invariants.py:125-140` | **No** | passing |
| Byte-identical equity read/rewrite | `tests/test_invariants.py:14-49` | **No** | passing |
| ISIN/CUSIP/FIGI checksums + ISIN↔CUSIP consistency | `validation/validate_identifiers.py`, `tests/test_validate_identifiers.py` | Only via the separate `validate-identifiers` CI job on PRs/human pushes | passing with a `UserWarning` for 2 review-only findings |
| Per-asset snapshot regression | `tests/csv/`, `tests/json/` + `conftest.py` harness | **No** | passing |

**Finding DQ-03 — data commits receive no CI validation whatsoever.**

```
GET /repos/JerBouma/FinanceDatabase/actions/runs?head_sha=a174c97d3b…   → total_count: 0
GET /repos/JerBouma/FinanceDatabase/commits/a174c97d3b…/check-runs      → total_count: 0
```

The last successful `Run Tests` was on **2026-09-11** against human PR commit `61d2feac`.
The bot commits that actually change the data (`Update database with new tickers`,
`Update Compression Files`, `Update Categorization Files`, `Update README statistics`) trigger
**zero** workflow runs. Whether this is GitHub's `GITHUB_TOKEN` recursion guard, an effect of
using `secrets.PAT`, or a repository setting is **UNKNOWN** (U-10) — the *effect* is verified
and is what matters: **the invariant tests do not gate the data.** That is precisely how `CHAD`
reached `main` and stayed.

**Finding DQ-04 — the dataset currently violates two of the project's own invariants**, and has
done so across at least three weekly cycles. Neither violation is visible to a user, because
neither is surfaced at load time or query time.

## 7.7 Trust classification of the dataset as a whole

| Property | Classification |
|---|---|
| Software provenance (PyPI publisher, repo owner, hashes) | **VERIFIED** |
| Data provenance (which upstream produced which field) | **UNVERIFIED** for the bulk; **VERIFIED** for US equities (rreichel3) and weakly signalled for cryptos (`CCC`) / currencies (`CCY`) |
| Data currency — US equities | **PARTIALLY_VERIFIED** — weekly, but see DP-03 (fields frozen after first sight) |
| Data currency — non-US equities | **STALE** — community-maintained only, by the project's own admission |
| Data currency — ETFs, funds, indices | **STALE / UNKNOWN** — no update job exists |
| Data currency — currencies, money markets | **UNKNOWN** — no update job exists |
| Data currency — **cryptocurrencies** | **STALE** — ~2020-era snapshot, no update job exists |
| Internal consistency (GICS triple) | **FAILING** as of 2026-09-13 |
| Internal consistency (cross-asset symbol uniqueness) | **FAILING** as of 2026-09-13 |
| Identifier *validity* where populated | **VERIFIED — high** (249,083 / 249,085 valid; 99.9992%) |
| Identifier *coverage* | **VERIFIED — low** (24–57% equities; 21.7% ETFs; 0% elsewhere) |
| Field-level completeness | **VERIFIED — highly variable** (0% to 78% empty, §4) |
| Reproducibility of a (code, data) pair | **NOT ACHIEVABLE** through the public API |
| Integrity of the transfer | **UNVERIFIED** — no checksum, signature, ETag or size guard |
| Suitability for live decisions | **NOT SUITABLE** |
| Suitability for point-in-time research | **NOT SUITABLE** |
| Suitability for static universe/taxonomy research, pinned to a git SHA and hash | **SUITABLE WITH CAVEATS** |

## 7.8 Positive findings (stated for balance)

An evidence-first review reports favourable evidence too:

1. **Delisted retention is real and intentional** — 10,404 rows, documented rationale. Very few
   free datasets of this size preserve delisted securities.
2. **Identifier checksums are genuinely implemented and genuinely pass** — ISO 6166 ISIN, CUSIP,
   OpenFIGI, plus ISIN↔CUSIP embedding consistency, with deterministic-only repair and an
   explicit `actionable` vs `review-only` distinction. That is epistemically disciplined design.
3. **Byte-reproducible artifacts** — the categorization job writes gzip with `mtime=0`
   (`database_update.yml:377`) so unchanged content produces identical bytes and clean diffs.
4. **dtype discipline learned the hard way** — `dtype=str, keep_default_na=False` with a comment
   recording the exact corruption it prevents (`"9763" → "9763.0"`, `"031162100" → "31162100.0"`,
   symbol `NA` → NaN).
5. **Real invariant tests exist** and one of them caught a real defect. The tests are good;
   the *triggering* is not.
6. **Honest self-description** — README:467 openly states the $25,000/yr Bloomberg comparison
   and that non-US maintenance depends on volunteers. That candour is itself evidence of
   trustworthy intent.
