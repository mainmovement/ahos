# 01 — Source and Repository

**Phase 1 of the tasking: repository discovery and source verification.**
All values below were read from authoritative, project-owned sources on **2026-09-15 (UTC)**.
Nothing was taken from an unverified search result.

---

## 1.1 Authoritative source chain (how the repository was identified)

The tasking supplied a project page, not a repository. The repository was resolved by
following the project's own links, then cross-checking against package metadata. Three
independent project-owned sources agree:

| Step | Source | What it asserted | Retrieved |
|---|---|---|---|
| 1 | `https://www.jeroenbouma.com/projects/financedatabase` (official project page, linked in the tasking) | Star badge image URL and "star the project" link both point to `https://github.com/JerBouma/FinanceDatabase`; FinanceToolkit link points to `github.com/JerBouma/FinanceToolkit` | 2026-09-15 |
| 2 | PyPI JSON API `https://pypi.org/pypi/financedatabase/json` | Publisher metadata; no `project_urls`; author `Jeroen Bouma` | 2026-09-15 |
| 3 | sdist `pyproject.toml` (`financedatabase-2.4.0.tar.gz`) | `repository = "https://github.com/JerBouma/FinanceDatabase"`, `homepage = "https://www.jeroenbouma.com/"` | 2026-09-15 |
| 4 | Library source `financedatabase/helpers.py:12-14` | `DATA_REPO = "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"` — the code itself names the repo and branch it trusts | 2026-09-15 |
| 5 | GitHub REST API `repos/JerBouma/FinanceDatabase` | Confirms existence, ownership, branch, licence, activity | 2026-09-15 |

Steps 1, 3 and 4 are **mutually independent** (website, package metadata, runtime code) and
all name the same owner and repository. Confidence: **HIGH**.

## 1.2 Repository facts

| Item | Value | Source | Evidence type | Date accessed | Confidence | Current / historical |
|---|---|---|---|---|---|---|
| Official repository URL | `https://github.com/JerBouma/FinanceDatabase` | GitHub API + pyproject + helpers.py | Official repository, package metadata, source code | 2026-09-15 | HIGH | Current |
| Repository owner | `JerBouma` (GitHub user id **46355364**, display name "Jeroen Bouma", blog `jeroenbouma.com`, 1,548 followers, account created 2019-01-03) | GitHub API `users/JerBouma` | Official repository | 2026-09-15 | HIGH | Current |
| Repository name | `FinanceDatabase` (repo id **333850832**) | GitHub API | Official repository | 2026-09-15 | HIGH | Current |
| Default branch | `main` | GitHub API | Official repository | 2026-09-15 | HIGH | Current |
| Repository created | 2021-01-28T18:36:09Z | GitHub API | Official repository | 2026-09-15 | HIGH | Historical |
| Latest commit (HEAD) | `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634` | GitHub API + local `git log -1` | Official repository, source code | 2026-09-15 | HIGH | Current |
| HEAD commit date / author / message | 2026-09-13T15:10:38Z · "GitHub Action" · `Update README statistics` | local `git log` | Official repository | 2026-09-15 | HIGH | Current |
| Latest release / tag | **2.4.0**, published **2026-06-02** | GitHub API `releases`, `tags` | Official repository | 2026-09-15 | HIGH | Current |
| All tags | `2.4.0, 2.3.1, 2.3.0, 2.2.0, 2.1.1, 2.1.0, 2.0.0, 1.0.0, 0.1.11, 0.1.10` (10 most recent of more) | GitHub API `tags` | Official repository | 2026-09-15 | HIGH | Current |
| Package name (PyPI) | `financedatabase` | PyPI JSON API | Package metadata | 2026-09-15 | HIGH | Current |
| Current version | **2.4.0**, uploaded 2026-06-02T14:05:45Z, `yanked = False` | PyPI JSON API | Package metadata | 2026-09-15 | HIGH | Current |
| Total PyPI releases | 35 (from `0.1.0`) | PyPI JSON API | Package metadata | 2026-09-15 | HIGH | Current |
| sdist SHA-256 | `a2af519e64e68baa52d369b49a8a16b09e77de0f20bb58e37243fbed225f2e87` (37,901 B) | PyPI JSON API + local `sha256sum` | Package metadata, artifact hash | 2026-09-15 | HIGH | Current |
| wheel SHA-256 | `dee02df0fc132a0cbffcef30294216b67655ddba92f1613dd756e06d5e041fd7` (34,183 B) | PyPI JSON API + local `sha256sum` | Package metadata, artifact hash | 2026-09-15 | HIGH | Current |
| Software licence | **MIT**, `Copyright (c) 2023 Jeroen Bouma`; SPDX `MIT`; present in sdist `LICENSE` and wheel `dist-info/licenses/LICENSE` | GitHub API `license` endpoint (`path: LICENSE`), sdist, wheel | Official repository, package metadata | 2026-09-15 | HIGH | Current |
| **Dataset** licence | **Not separately stated.** See [`12_LICENSE_AND_LEGAL_REVIEW.md`](12_LICENSE_AND_LEGAL_REVIEW.md) | Absence of a NOTICE / data-licence file | Inference from absence | 2026-09-15 | MEDIUM | Current |
| Python requirement | `>=3.10, <3.16` | PyPI JSON API + `pyproject.toml` | Package metadata, source code | 2026-09-15 | HIGH | Current |
| Declared runtime dependencies | **exactly one:** `financetoolkit>=2.0.3,<3.0.0` | PyPI JSON API `requires_dist` + `pyproject.toml` | Package metadata, source code | 2026-09-15 | HIGH | Current |
| *Actual* import-time dependencies | `numpy`, `pandas`, `requests`, stdlib (`io`, `pathlib`, `typing`) — **none of them declared** | Grep of all imports in the shipped package | Source code | 2026-09-15 | HIGH | Current → **packaging defect** |
| Dev dependencies | `pytest>=8.3`, `ipykernel`, `black[jupyter]>=25.1`, `codespell`, `pytest-mock`, `pytest-recording`, `pytest-cov`, `ruff>=0.9`, `pytest-timeout`, `tqdm`; `uv.lock` adds `python-stdnum>=2.2` | `pyproject.toml` `[dependency-groups].dev`, `uv.lock` | Source code | 2026-09-15 | HIGH | Current |
| Build backend | `hatchling`; wheel target `packages = ["financedatabase"]`; sdist `include = ["financedatabase/**"]` | `pyproject.toml` | Source code | 2026-09-15 | HIGH | Current |
| Repository activity | `pushed_at` 2026-09-13; data commits on 2026-08-25, 08-30, 09-06, 09-11, 09-13; **452** total workflow runs | GitHub API | Official repository | 2026-09-15 | HIGH | Current |
| Popularity / maintenance signals | 9,116 stars · 941 forks · 126 subscribers · **4 open issues+PRs** · not archived · not disabled · language Python · repo size 5,088,317 KB (~4.85 GB) | GitHub API | Official repository | 2026-09-15 | HIGH | Current |
| Open issues (all) | #153 *Track `delisted` for ETFs and Funds (currently equities-only)* (2026-06-03) · #78 *[DATA] How can we contribute ISIN codes?* (2024-03-28) · PR #169 bump tornado · PR #156 bump vcrpy | GitHub API `issues?state=open` | Official repository | 2026-09-15 | HIGH | Current |
| Official documentation | `https://www.jeroenbouma.com/projects/financedatabase` (+ `/getting-started` notebook page). `has_wiki = False`, `has_pages = False` — docs live on the personal site, not GitHub | GitHub API, official site | Official documentation | 2026-09-15 | HIGH | Current |
| Data repository | **Same repository**, directories `database/` (plain CSV, 145 MB at HEAD, 85 per-exchange equity files) and `compression/` (bz2 + gzip artifacts, ~21 MB) | Sparse checkout + GitHub API `contents` | Official repository, dataset inspection | 2026-09-15 | HIGH | Current |
| Related packages | `JerBouma/FinanceToolkit` (5,344 stars, pushed 2026-09-10); archived: `ThePassiveInvestor` (624★), `AlgorithmicTrading` (1,102★), `FundamentalsQuantifier` (343★), `PersonalFinance` (128★); active: `FinancePortfolio`, `Finance101`, `awesome-fintech`, `awesome-quant`, `awesome-systematic-trading` | GitHub API `users/JerBouma/repos` | Official repository | 2026-09-15 | HIGH | Current |
| Finance Toolkit integration | Yes — `FinanceFrame.to_toolkit()` at `helpers.py:179-277`. See [`09_EXTERNAL_INTEGRATIONS.md`](09_EXTERNAL_INTEGRATIONS.md) | Source code | 2026-09-15 | HIGH | Current |
| Upstream **data** source | `github.com/rreichel3/US-Stock-Symbols` (574★, created 2021-01-30, pushed 2026-09-15, commits titled `generated`, **`license = None`**) — referenced at `database_update.yml:167,173,179` and disclosed in README:465 | Workflow source + GitHub API | Source code, official documentation | 2026-09-15 | HIGH | Current |

## 1.3 Finding SR-01 — the URL in the tasking does not resolve

The tasking (and a great deal of third-party material) refers to
`github.com/JeroenBouma/FinanceDatabase`. That is **not** the repository.

| Observation | Value | Source |
|---|---|---|
| `GET api.github.com/repos/JeroenBouma/FinanceDatabase` | **HTTP 404** `{"message":"Not Found"}` | GitHub API, 2026-09-15 |
| `GET api.github.com/users/JeroenBouma` | HTTP 200 → login `jeroenbouma`, **id 46189588**, `public_repos = 0`, followers 1, created 2018-12-27, **updated 2023-10-05** | GitHub API, 2026-09-15 |
| `GET api.github.com/users/JerBouma` | HTTP 200 → login `JerBouma`, **id 46355364**, `public_repos = 15`, followers 1,548, created 2019-01-03, updated 2026-09-06 | GitHub API, 2026-09-15 |

The two accounts have **different user IDs**, so this is **not** a GitHub rename (a rename
preserves the ID and redirects). Whether `JeroenBouma/FinanceDatabase` ever existed, and why
the older account now holds zero repositories, is **UNKNOWN** (see U-05 in document 17).

**Why this matters to AHOS (not trivia):**

1. **Documentation rot is a real, measurable property of this project.** Anyone following the
   commonly cited URL gets a 404. AHOS doctrine says *Documentation ≠ Proof*; this is a clean
   instance where following documentation would have produced a wrong repository.
2. **A latent repo-squatting surface.** The name `JeroenBouma` is a live account with zero
   public repositories. If a `FinanceDatabase` repository were ever created there, it would
   appear authoritative to readers of older documentation, blog posts and Stack Overflow
   answers — for a project with 9.1k stars whose clients download data over HTTPS from a
   hardcoded URL. This is recorded as a **risk in the ecosystem around the project**, not as
   an allegation about any party. No such repository exists as of 2026-09-15 (**VERIFIED**).
3. **AHOS must pin by commit SHA and hash, never by URL.** See §11 and §14.

## 1.4 Finding SR-02 — the official website is stale and contradicts the repository

Two project-owned sources disagree about the size of the dataset. Only one matches reality.

| Asset class | Official website (jeroenbouma.com) | Repo `README.md` (auto-generated 2026-09-13) | **Measured** from `compression/*.bz2` | Verdict |
|---|---:|---:|---:|---|
| Equities | **158,429** | 112.690 | **112,690** | Website **wrong by 45,739 (−29%)** |
| ETFs | 36,786 | 36.481 | **36,481** | Website wrong by 305 |
| Funds | 57,881 | 57.853 | **57,853** | Website wrong by 28 |
| Indices | 91,183 | 91.181 | **91,181** | Website wrong by 2 |
| Currencies | 2,556 | 2.556 | **2,556** | Agree |
| Cryptocurrencies | 3,367 | 3.367 | **3,367** | Agree |
| Money Markets | 1,367 | 1.367 | **1,367** | Agree |

The website is also structurally stale:

- It claims Equities "12 Sectors · 63 Industries · 111 Countries"; the auto-generated README
  says **11 sectors, 80 industries, 117 countries, 84 exchanges** (and our measurement of the
  live data agrees with the README: 114 countries among non-delisted rows, 117 including
  delisted — see §6.4).
- It labels ETFs with "295 Sectors · 22 Industries", but the ETF schema has **no** sector or
  industry columns at all — it has `category_group`, `category` and `family`. The website's
  column semantics are transposed/wrong.
- Its sample `select()` output table shows **19 columns with no `mic` and no `delisted`**.
  The actual current equities schema has **22 columns including both**. The website documents
  a superseded schema.
- It says Money Markets have "3 Exchanges"; the README says 2.
- It says Cryptocurrencies have "352 Categories"; the README says 351 cryptocurrencies.

**Consequence for AHOS:** the project's marketing page cannot be used as an authority for
schema or scale. The repo README is regenerated by CI from the data and matched our
measurement exactly on all seven asset classes. This is the strongest single piece of evidence
in this investigation for the doctrine *REALITY > DOCUMENTATION*.

## 1.5 Version landscape and the code/data decoupling

```
2026-06-02  PyPI 2.4.0 released  ── tag 2.4.0
                │
                │   3.5 months of unreleased code accumulate on main:
                │     • financedatabase/validation/  (+534 lines, NOT in 2.4.0)
                │     • helpers.py read_csv semantics changed (358 → 366 lines)
                │
2026-09-13  main HEAD a174c97d  ◄── DATA is served from here (hardcoded "/main/")
```

| Fact | Evidence |
|---|---|
| Released wheel 2.4.0 contains 9 modules, **no** `validation/` subpackage | `diff -rq` of sdist vs. repo checkout; `find` on both trees |
| Repo `main` contains `financedatabase/validation/__init__.py` and `validation/validate_identifiers.py` (533 lines) | `find financedatabase -type f` |
| `tests/test_validate_identifiers.py:7` imports `from financedatabase.validation.validate_identifiers import …` | Source code — so **CI on `main` exercises code that no released version contains** |
| `helpers.py` differs: `main` adds `keep_default_na=False, na_values=[""]` to both `read_csv` calls | `diff -u` (see §13, scenario S-13) |
| `DATA_REPO` is hardcoded to `…/main/compression/` in **both** versions | `helpers.py:12-14` |

**Therefore:** a user on the current release gets **2026-06-02 code** reading **whatever
`main` holds today**. There is no data-version parameter, no ETag, no `If-Modified-Since`, no
manifest and no checksum. Two machines installing the same pinned version on different days
get different data. This is the project's most consequential architectural property and is
developed in §3, §7 and §13 (S-13).

## 1.6 What could NOT be verified in Phase 1

| Item | Status | Why |
|---|---|---|
| Whether `github.com/JeroenBouma/FinanceDatabase` ever existed | **UNKNOWN** (U-05) | Would require GitHub's internal rename history; not exposed by the API |
| Provenance of the pre-2023 bulk import (the ~112k non-US equities, all ETFs, funds, indices, currencies, cryptos, money markets) | **UNVERIFIED** (U-04) | The workflow only *adds* US tickers. README:467 says non-US changes depend on community contributions. The original bulk source is not documented anywhere in the repo |
| Publisher identity verification on PyPI (2FA, provenance attestations) | **UNVERIFIED** (U-09) | PyPI JSON API exposes no attestation data for this project; not checked via Sigstore |
| Whether the `secrets.PAT` is scoped minimally | **UNKNOWN** (U-08) | Secrets are not readable; scope is not observable from outside |
