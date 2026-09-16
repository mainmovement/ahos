# 21 — Release Regression Verification

**Document 21 — Objective C.** Verification of the reported `NA` ticker regression:
*"Release 2.4.0 lacks `keep_default_na=False`, causing the ticker `NA` to be silently lost, while
main contains a fix."*

**Method:** isolated testing only. `evidence/scripts/f3_na_regression.py` against the pinned commit
in `/tmp/fdb2_repo`, using the release-2.4.0 wheel installed in `/tmp/fdb2_venv`.
Raw output: `evidence/followup/f3_na_regression.json`.

> The upstream repository was **not** modified. AHOS was **not** modified. Nothing was installed
> into the AHOS environment. No claim below is made without source **and** execution evidence.

---

## 21.1 Verdict

> ## **CONFIRMED — and the original claim is REFINED in one respect and STRENGTHENED in three.**
>
> The regression is real, reproducible, currently shipped, and **not** fixed in any release.
> **Refinement:** the row is **not deleted** — it is retained with a **null key**, which makes it
> *unaddressable* rather than absent. That distinction matters for detection.
> **Strengthened:** (a) the exact fix commit, author, PR and date are now known; (b) git ancestry
> proves the fix is **not** in tag `2.4.0`; (c) the defect scope is now proven to be
> **equities-only, one record** — and both loader branches are affected, not just the local one.

## 21.2 C-1 · The release loader implementation — **VERIFIED**

`financedatabase/helpers.py` **as shipped in the PyPI 2.4.0 wheel**
(`/tmp/fdb2_venv/lib/python3.11/site-packages/financedatabase/helpers.py`, 358 lines):

```python
 61        try:
 62            if use_local_location:
 63                self.data = pd.read_csv(the_path, compression="bz2", index_col=0)
 64            else:
 65                response = requests.get(the_path, headers=HEADERS, timeout=60)
 66                response.raise_for_status()
 67
 68                self.data = pd.read_csv(
 69                    BytesIO(response.content),
 70                    compression="bz2",
 71                    index_col=0,
 72                )
 73        except requests.exceptions.RequestException as error:
 74            raise ValueError(
 75                f"Failed to load data from {the_path}: {str(error)}.\n"
```

`C1_release_has_keep_default_na = **false**`. **Neither** branch (local **nor** remote) sets it.

## 21.3 C-2 · The `main` loader implementation — **VERIFIED**

`financedatabase/helpers.py` **at commit `a174c97d3b`** (366 lines):

```python
 61        try:
 62            if use_local_location:
 63                self.data = pd.read_csv(
 64                    the_path,
 65                    compression="bz2",
 66                    index_col=0,
 67                    keep_default_na=False,
 68                    na_values=[""],
 69                )
 70            else:
 71                response = requests.get(the_path, headers=HEADERS, timeout=60)
 72                response.raise_for_status()
 73
 74                self.data = pd.read_csv(
 75                    BytesIO(response.content),
 76                    compression="bz2",
 77                    index_col=0,
 78                    keep_default_na=False,
 79                    na_values=[""],
 80                )
 81        except requests.exceptions.RequestException as error:
```

`C2_main_has_keep_default_na = **true**` — in **both** branches.

## 21.4 C-3 · The exact difference — **VERIFIED**

| | Release 2.4.0 | `main` @ `a174c97d3b` |
|---|---|---|
| `helpers.py` line count | **358** | **366** |
| Delta | — | **+8 lines** (matches the original report's "8-line delta") |
| `keep_default_na=False, na_values=[""]` | absent | present ×2 |

`diff -u` added lines (verbatim):

```
+                self.data = pd.read_csv(
+                    the_path,
+                    compression="bz2",
+                    index_col=0,
+                    keep_default_na=False,
+                    na_values=[""],
+                )
+                    keep_default_na=False,
+                    na_values=[""],
```

`diff -u` removed line (verbatim):

```
-                self.data = pd.read_csv(the_path, compression="bz2", index_col=0)
```

`diff -rq` over the whole package — **only two substantive differences**:

```
Files .../site-packages/financedatabase/helpers.py and /tmp/fdb2_repo/financedatabase/helpers.py differ
Only in /tmp/fdb2_repo/financedatabase: validation
```

(plus `__pycache__`, a build artifact). So the release-vs-`main` divergence is exactly:
**the NA-parsing fix**, and **the `validation/` subpackage** — re-confirming EV-SRC-05.

## 21.5 C-4 · The exact `NA` record in the source data — **VERIFIED**

Scanning every `database/equities/*.csv` at the pinned commit for a first field equal to `NA`:

```
file          : database/equities/NMS.csv
line          : 4346
first field   : NA
record        : NA,Nano Labs Ltd Class A Ordinary Shares,,USD,Information Technology,
                Semiconductors & Semiconductor Equipment,
                Semiconductors & Semiconductor Equipment,NMS,XNAS,NASDAQ Global Select
```

`C4_count = **1**` — exactly one such record in the equities corpus. Note the **empty third
field** (an unpopulated identifier) and that the row is otherwise complete: a real, listed security
(Nano Labs Ltd Class A Ordinary Shares, NASDAQ Global Select, `XNAS`).

Retrieved through the `main` loader, the same record reads as:
`name='Nano Labs Ltd Class A Ordinary Shares'`, `country='China'`, `exchange='NMS'`,
`isin=NaN`, `summary` present.

## 21.6 C-5 / C-6 · Both behaviours on the **same bytes** — **VERIFIED**

Reading `/tmp/fdb2_repo/compression/equities.bz2` twice, once with each semantics:

| Measurement | **Release 2.4.0** semantics | **`main`** semantics |
|---|---|---|
| `pd.read_csv` call | `compression="bz2", index_col=0` | `+ keep_default_na=False, na_values=[""]` |
| Rows | **112,690** | **112,690** |
| Index entries that are NaN | **1** | **0** |
| `"NA" in index` | **False** | **True** |
| `.loc["NA"]` | **`KeyError: 'NA'`** | **returns the row** → `Nano Labs Ltd Class A Ordinary Shares`, `country='China'`, `exchange='NMS'` |
| Cell-level NaN divergence per column | — | **`{}` — none** |

**Two conclusions follow, and the second is a refinement of the original report.**

1. **The symbol `NA` is unretrievable under release semantics.** `"NA" in index` is `False` and
   `.loc["NA"]` raises `KeyError`. Any symbol-keyed lookup for Nano Labs **fails**.
2. **REFINEMENT — the row is not lost from the frame.** Row counts are **identical** (112,690 both
   ways) and cell-level NaN divergence is **empty**. The record survives with a **null index
   value**. So the precise defect is:

> The row is **retained but rendered unaddressable** — its primary key becomes `NaN`. It is
> *silently dropped only when something filters on the key*, which `FinanceFrame.to_toolkit()` does
> (`helpers.py`: `self[self.index.notna()]`). The original phrasing "the ticker `NA` is silently
> lost" is **correct for symbol-keyed access and for `to_toolkit()`**, but **overstates it as row
> deletion**.

This refinement matters operationally: a consumer who counts rows sees **no anomaly at all**
(112,690 either way). Only a *key-based lookup* or an explicit null-index assertion reveals it.
That makes the defect **harder** to detect than the original wording implied, not easier — so the
severity assessment stands, but the detection guidance must change. **Recorded as CORRECTION
C-REFINE-01 in document 25.**

## 21.7 C-7 · Reproducibility — **VERIFIED, twice**

| Run | Session | Result |
|---|---|---|
| Original (`a11_na_bug.py`) | 2026-09-15T~16:00Z, `/tmp/fdb_repo` + `/tmp/fdb_venv` | 1 index NaN under release semantics, `'NA' in index` False, `KeyError` on `.loc['NA']` |
| **Follow-up (`f3_na_regression.py`)** | 2026-09-15T18:3xZ, `/tmp/fdb2_repo` + `/tmp/fdb2_venv` | **identical** |

The environment was rebuilt from scratch between runs (document 19 §19.0) and the result
reproduced exactly, including the empty cell-level divergence. The repository did not move
(HEAD unchanged). **Reproducible: YES.**

## 21.8 C-8 · Was the fix released? — **VERIFIED: NO**

Git ancestry, decisive:

```
$ git merge-base --is-ancestor 3b8eb8390959bec6a360a620333b6fe5217a4618 2.4.0
  → NO   (the fix is NOT in tag 2.4.0)

$ git merge-base --is-ancestor 3b8eb8390959bec6a360a620333b6fe5217a4618 HEAD
  → YES  (the fix IS in main)

$ git rev-list -n1 2.4.0
  → 51226b86758b116fb9e1065645c62fcb342af2f5

$ git show 2.4.0:financedatabase/helpers.py | grep -n read_csv
  → 63:  self.data = pd.read_csv(the_path, compression="bz2", index_col=0)
     (no keep_default_na — confirmed at the TAG itself, independently of the wheel)
```

| Event | Date | Source |
|---|---|---|
| Tag `2.4.0` cut (commit `51226b86`) | — | `git rev-list -n1 2.4.0` |
| PyPI upload of `financedatabase 2.4.0` (wheel + sdist) | **2026-06-02T14:05:45Z / 14:05:46Z** | PyPI JSON `upload_time_iso_8601` |
| Latest `helpers.py` change *before* the release | **2026-06-02** — `fa1940d5`, *jeroen*, "Add adjustments to automatically filter out delisted companies" | `git log -- helpers.py` |
| **The fix** | **`3b8eb8390959bec6a360a620333b6fe5217a4618`, 2026-08-07T10:32:18Z (12:32:18 +0200), Jon Højlund Arnfred, "Preserve CSV values verbatim in the database workflow (#166)"** | `git log -S keep_default_na -- helpers.py` |
| Latest release on PyPI (still) | **2.4.0** | PyPI JSON `info.version`, re-fetched 2026-09-15 |

**The fix postdates the release by 66 days and is not contained in it.** `git log -S
keep_default_na` returns exactly **one** commit, so there is no earlier partial fix.

## 21.9 C-9 · Does the fix exist only on `main`? — **VERIFIED: YES**

`3b8eb83` is an ancestor of `HEAD` (`main`) and **not** an ancestor of tag `2.4.0`. There is no tag
after `2.4.0` (`git tag --sort=-creatordate` → `2.4.0, 2.3.1, 2.3.0, 2.2.0, 2.1.1, 2.1.0, …`).
Therefore the fix exists **only on `main`**, and any `pip install financedatabase` today — which
resolves to **2.4.0**, the latest release — gets the **unfixed** loader.

**Note the inversion this creates.** A user who installs the *released, versioned, hash-pinned*
package gets the **defective** loader. A user who imports from a **git checkout of `main`** gets
the **fixed** one. Version pinning — normally the safe choice — selects the broken code here,
because the data is pinned to `main` while the code is pinned to a release. This is the concrete
harm of the version-decoupling finding (document 07, DQ-02).

## 21.10 C-10 · Scope: all asset classes, or only equities? — **VERIFIED: equities only, one record**

**New test, not present in the original investigation.** Each of the seven `.bz2` artifacts was
read twice; the index was tested against the full pandas default-NA string set
(`'', '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan', '1.#IND', '1.#QNAN',
'<NA>', 'N/A', 'NA', 'NULL', 'NaN', 'None', 'n/a', 'nan', 'null'`):

| Asset class | Rows | Index values matching pandas default-NA | Release index-NaN count |
|---|---:|---|---:|
| **equities** | 112,690 | **`['NA']`** → **1** | **1** |
| etfs | 36,481 | `[]` | 0 |
| funds | 57,853 | `[]` | 0 |
| indices | 91,181 | `[]` | 0 |
| currencies | 2,556 | `[]` | 0 |
| cryptos | 3,367 | `[]` | 0 |
| money markets | 1,367 | `[]` | 0 |

`C10_classes_affected = ['equities']` · `C10_ONLY_EQUITIES_AFFECTED = **true**`

Independently confirmed from the **source CSVs** across all seven classes: the only first field
matching a pandas default-NA string anywhere in `database/` is
**`database/equities/NMS.csv → 'NA'`**.

**Scope verdict:** the defect is **narrow** — one asset class, one record, today. **Two caveats
that prevent this from being reassuring:**

1. **It is data-dependent, not code-bounded.** The loader is defective for *any* symbol that
   pandas treats as NA. The corpus happens to contain exactly one such symbol now; a future
   listing with the ticker `NA`, `N/A`, `NULL`, `NONE`, `NAN` or `NA.V` (Nano Labs is a 2022 SPAC
   listing) would be silently affected too. The **mechanism** is general; the **instance** is
   currently singular.
2. **The same class of bug already fired twice more**, per the project's own comment at
   `database_update.yml:196-202`: `"9763"` → `"9763.0"` and `"031162100"` → `"31162100.0"`
   (numeric coercion of zipcode/CUSIP), which the workflow comment says *"dropped that row on every
   run"*. The `keep_default_na=False` + `dtype=str` combination in `main` is the fix for that whole
   class — which is why the fix commit is titled *"Preserve CSV values verbatim"*, not *"Fix NA"*.

## 21.11 Supporting: the uncaught-`FileNotFoundError` path — **REPRODUCED**

Re-executed with the release wheel and no local data present:

```
FileNotFoundError: [Errno 2] No such file or directory:
  '/tmp/fdb2_venv/lib/python3.11/site-packages/compression/cryptos.bz2'
isinstance(e, requests.exceptions.RequestException) -> False
```

The `except requests.exceptions.RequestException` clause at `helpers.py:73` does **not** cover the
`use_local_location` branch, so the raw `FileNotFoundError` escapes the library's error
normalization. Re-confirms EV-QE-12 exactly.

## 21.12 Claim-by-claim disposition

| # | Reported claim | Disposition | Evidence |
|---|---|---|---|
| 1 | Release 2.4.0 lacks `keep_default_na=False` | **VERIFIED** | §21.2 — `helpers.py:63`, and confirmed at tag `2.4.0` independently of the wheel |
| 2 | This causes ticker `NA` to be silently lost | **VERIFIED, REFINED** | §21.6 — lost **as a key** (`KeyError`, `"NA" in index` False); the **row is retained** with a null index. Row counts identical |
| 3 | `main` contains a fix | **VERIFIED** | §21.3, §21.4 — `keep_default_na=False, na_values=[""]` in both branches |
| 4 | (implicit) the two differ only here | **VERIFIED** | §21.4 — `diff -rq` shows `helpers.py` + `validation/` only; 358 vs 366 lines |
| 5 | The fix was released | **VERIFIED FALSE — the fix was NOT released** | §21.8 — `merge-base --is-ancestor … 2.4.0` → **NO**; latest PyPI release is still 2.4.0 |
| 6 | The fix exists only on `main` | **VERIFIED** | §21.9 |
| 7 | Affects all asset classes | **VERIFIED FALSE — equities only, 1 record** | §21.10 — 6 of 7 classes have zero vulnerable index values |
| 8 | Reproducible | **VERIFIED** | §21.7 — reproduced in a rebuilt environment, identical results |

## 21.13 New evidence IDs

| ID | Claim | Method | Status |
|---|---|---|---|
| **EV-FU-C-01** | Tag `2.4.0` = commit `51226b86758b116fb9e1065645c62fcb342af2f5`; PyPI upload 2026-06-02T14:05:45Z | `git rev-list` + PyPI JSON | **EXECUTION-VERIFIED** |
| **EV-FU-C-02** | The fix is commit `3b8eb8390959bec6a360a620333b6fe5217a4618`, 2026-08-07T10:32:18Z, Jon Højlund Arnfred, PR **#166**, *"Preserve CSV values verbatim in the database workflow"*; `git log -S keep_default_na` returns exactly one commit | `git log -S` | **EXECUTION-VERIFIED** |
| **EV-FU-C-03** | The fix is **not** an ancestor of tag `2.4.0` and **is** an ancestor of `main` | `git merge-base --is-ancestor` (both directions) | **EXECUTION-VERIFIED** |
| **EV-FU-C-04** | The exact affected record is `database/equities/NMS.csv:4346` → `NA,Nano Labs Ltd Class A Ordinary Shares,…,NMS,XNAS,NASDAQ Global Select`; exactly **1** such record in the equities corpus | line-level scan of all `database/equities/*.csv` | **EXECUTION-VERIFIED** |
| **EV-FU-C-05** | Under release semantics the row is **retained** (112,690 rows both ways) with a **null index**; cell-level NaN divergence is **empty** — the damage is confined to the key | dual read of one file | **EXECUTION-VERIFIED** |
| **EV-FU-C-06** | Scope is **equities only**: 1 vulnerable index value; the other six asset classes have **0**; the only NA-like first field anywhere in `database/` is `NMS.csv → 'NA'` | index scan of all 7 `.bz2` + first-field scan of all source CSVs | **EXECUTION-VERIFIED** |
| **EV-FU-C-07** | `helpers.py` is 358 lines in the release, 366 on `main`; `diff -rq` over the package shows only `helpers.py` differing plus `validation/` present only in the repo | `diff -u`, `diff -rq`, `wc -l` | **EXECUTION-VERIFIED** |
| **EV-FU-C-08** | Both loader branches (local **and** remote) lack `keep_default_na` in the release; both have it on `main` | read of both files | **VERIFIED** |

## 21.14 AHOS implications (analysis only — no changes made)

| Implication | Note |
|---|---|
| Version pinning does **not** protect against this | The released, hash-verified 2.4.0 is the **defective** artifact; `main` is fixed. Pinning the *package* while the *data* floats on `main` selects the broken combination |
| Row-count checks would **not** detect it | 112,690 either way. Only a **key-null assertion** detects it — which is what fixture **FIX-06** (document 20) proposes |
| Any AHOS ingest must own its reader | Explicit `dtype=str, keep_default_na=False, na_values=[""]` plus a post-parse assertion that no key is null. This is boundary rule **B-8** of document 14 §14.5, now with a concrete, reproduced justification |
| `notna()`-style filters are load-bearing hazards | `to_toolkit()`'s `self[self.index.notna()]` is what converts "unaddressable" into "gone". Any AHOS code that filters on a key's non-nullness must log what it discarded |
| The defect class is general | Numeric-string coercion (`"9763"` → `"9763.0"`, `"031162100"` → `"31162100.0"`) is the same root cause and already fired twice per the project's own workflow comment. Strict-typed reading is the general control |

**No AHOS file was modified. No recommendation in this section has been implemented.**
