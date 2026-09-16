# 11 — Security & Supply-Chain Review

**Phase 11.** Scope: the PyPI artifacts for `financedatabase==2.4.0` (hash-verified), the
repository at commit `a174c97d`, its three CI workflows, and the data pipeline they implement.

> **Language discipline required by the tasking.** This is **not** a security certification.
> Where nothing was found, the statement is *"no issue observed in reviewed scope"*, which is
> **not** equivalent to *"secure"*. Absence of evidence is recorded as absence of evidence.

---

## 11.1 The shipped package's attack surface — measured

Grep across every `.py` file in the **PyPI 2.4.0 wheel** (not the repo, not `main`):

| Pattern | Occurrences |
|---|---:|
| `eval(` | **0** |
| `exec(` | **0** |
| `pickle` | **0** |
| `marshal` | **0** |
| `subprocess` | **0** |
| `os.system` | **0** |
| `popen` | **0** |
| `__import__` | **0** |
| `socket` | **0** |
| `ctypes` | **0** |
| `shutil` | **0** |
| `open(` | **0** |
| `shelve` / `dill` | **0** |
| `yaml.load` | **0** |
| `compile(` | **0** |
| `input(` | **0** |

**Complete import list of the shipped package:** `io.BytesIO`, `pathlib.Path`, `typing.Any`,
`numpy`, `pandas`, `requests`, and one lazy `from financetoolkit import Toolkit` inside
`to_toolkit()`. Nothing else.

**Complete network egress surface:** exactly **two** call sites, both identical in shape:

```
helpers.py:65    response = requests.get(the_path, headers=HEADERS, timeout=60)
helpers.py:336   response = requests.get(the_path, headers=HEADERS, timeout=60)
```

**Complete filesystem surface:** **zero** write operations; **zero** `open()` calls. Reads happen
only through `pd.read_csv(path)` when `use_local_location=True`.

**Assessment:** ~1,866 lines, no code execution primitives, no deserialization of untrusted
binary, no file writes, no subprocesses, two GET requests. This is a **genuinely small and
auditable surface**, and it is the strongest positive security finding in this investigation.
Status: **no issue observed in reviewed scope** for code-execution and filesystem risks.

## 11.2 Deserialization — a deliberate, documented decision

`compression/README.md` (project-owned, retrieved 2026-09-15):

> *"The conclusion is that **Pickle (xz)** results in the most efficient loading. However, **to
> solve the vulnerability issue that arises with loading with Pickles I've decided to take the
> next best thing, this is the CSV BZ2 option** which is about the same in terms of loading."*

The author benchmarked pickle, found it fastest, and **rejected it on security grounds**.
`compression/compression.ipynb` (82 KB) preserves the methodology. The distributed format is
CSV+bz2, parsed by pandas' C tokenizer.

**Assessment:** the highest-severity deserialization vector (arbitrary code execution via
`pickle.loads` on remote content) is **structurally absent by design decision**, and that
decision is documented. This is real security engineering, and AHOS's own
`docs/OSS_HARVEST_LOG.md` standing rule would endorse it.

Residual note: pandas' CSV parser has had CVEs historically, and `low_memory=False` is used only
in the categories path (`helpers.py:333,343`). Parsing untrusted CSV is **lower** risk than
unpickling but is **not zero** risk. Status: **no issue observed in reviewed scope**.

## 11.3 Data integrity — the material weakness

**Finding SEC-01 — there is no integrity verification of downloaded data whatsoever.**

| Control | Present? | Evidence |
|---|---|---|
| SHA-256 / any checksum of the payload | **No** | absence in `helpers.py:61-79` |
| Signature / Sigstore / GPG | **No** | absence |
| PyPI provenance attestation for the *package* | **UNVERIFIED** (U-09) — not exposed by the PyPI JSON API; not checked via Sigstore |
| `ETag` / `If-None-Match` / `Last-Modified` | **No** | absence |
| `Content-Type` validation | **No** — `response.content` is passed straight to `pd.read_csv` | `helpers.py:68-72` |
| Response **size limit** | **No** — `response.content` buffers the entire body in RAM before parsing | `helpers.py:68-69` |
| Schema validation on load (expected columns, dtypes, row count) | **No** | absence — `self.data` is whatever the CSV contained |
| Certificate pinning | **No** (relies on system trust store via `requests`) | absence |
| Version pinning of the data | **No** — the URL hardcodes the **`main`** branch | `helpers.py:12-14` |

Consequences, in ascending severity:

1. **Unbounded memory from a hostile or corrupt response.** No size cap before
   `response.content`, and bz2 is a compression format — a small hostile payload can expand
   enormously during `pd.read_csv` decompression. A decompression-bomb-style denial of service is
   **theoretically available**; we did **not** construct one (**NOT TESTED** — deliberately, as it
   would be an attack on a third-party service).
2. **Silent schema drift.** If the served file gained, lost or renamed a column, the library
   would accept it. Downstream code that does `equities["delisted"]` (`Equities.py:80`) would
   then raise `KeyError` — or, worse, a renamed column would make `select()`'s validation
   (`show_options`) return empty and every filter raise `ValueError`. There is no
   schema-contract check to fail fast with a clear message.
3. **Trust in a mutable branch.** The data is whatever `main` holds at request time. Anyone who
   can push to `main` — the maintainer, a compromised `secrets.PAT`, or a compromised CI action
   (§11.5) — changes what every user of every version receives, with no version bump, no
   checksum and no announcement.
4. **CSV content flows into user environments as text.** If consumed naively (exported to a
   spreadsheet, rendered in a UI), formula-injection-style content in `name`/`summary` would be a
   downstream concern. We observed no `=`-prefixed cells in a spot check, but did **not** scan
   all 304,495 rows for injection payloads: **NOT VERIFIED**.

**Finding SEC-02 — `base_url` is caller-controlled and passed directly to `requests.get`.**
`FinanceDatabase.__init__(base_url=DATA_REPO, …)` (`helpers.py:41`) and
`show_options(…, base_url=DATA_REPO, …)` (`:282`) both interpolate `base_url` into a URL that is
then fetched (`:65`, `:336`). If an AHOS caller ever forwarded untrusted input into `base_url`,
the process would issue a GET to an attacker-chosen URL. Bounded impact: GET only, no
credentials or cookies attached, no redirect restrictions configured (`requests` follows redirects
by default — a redirect to an internal address would be followed). **No such call path exists in
FinanceDatabase itself**; this is a risk in *how a consumer might use it*. Recorded so that any
future AHOS adapter hardcodes the URL and never exposes it.

**Finding SEC-03 — a hardcoded spoofed browser User-Agent.**
```python
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}   # helpers.py:18-22
```
Every request misidentifies the client as Chrome 58 on Windows 10, regardless of the actual OS or
library version. Effects: (a) the traffic is not attributable to the library, which impedes
incident response on both sides; (b) it asserts a Windows origin from Linux/macOS hosts;
(c) Chrome 58 is from 2017 and some CDNs/WAFs treat such strings as bot signatures, so it may
*increase* rather than reduce blocking. Not a vulnerability in itself. **No policy violation is
asserted** — GitHub raw serves public repository content to any client.

## 11.4 Dependency and pinning review

| Item | Value | Risk |
|---|---|---|
| Declared runtime dependencies | `financetoolkit>=2.0.3,<3.0.0` — **a range, not a pin** | A new `financetoolkit` 2.x release is adopted automatically on fresh installs |
| Undeclared direct imports | `numpy`, `pandas`, `requests` | **Packaging defect.** Their versions are governed entirely by a transitive dependency (§9.2) |
| Transitive tree via `financetoolkit 2.2.0` | `pandas>=3.0`, `scikit-learn>=1.6`, **`yfinance` (completely unpinned)**, `openpyxl>=3.1`, `pyyaml>=6.0`, `requests>=2.32` | **Large.** `yfinance` is unpinned *and* talks to Yahoo endpoints at runtime; a breaking or compromised `yfinance` release lands with no version movement in `financedatabase` |
| `uv.lock` | Present, 428 KB, revision 3, pins `financetoolkit 2.0.7`, `pandas 2.3.3` for `<3.11`, seven resolution markers | **Good practice** — but it governs **CI only**. It does not affect what `pip install financedatabase` produces (§9.3 EI-03) |
| Dependabot | Active — observed runs `uv in /. for pillow`, `uv in /. for black`, PR #169 (tornado 6.5.6→6.5.8), PR #156 (vcrpy 8.1.1→8.2.1). Several runs concluded **failure** | Dependency maintenance is attempted; some update PRs are stale (e.g. #156 open since 2026-06-23) |
| `.pre-commit-config.yaml` | Present (795 B) | Local hygiene only |
| Python floor | `>=3.10,<3.16` while `financetoolkit 2.2.0` needs `>=3.11` | Resolution depends on interpreter version (§9.2 EI-02) |
| Typosquatting exposure on `financedatabase` | The canonical PyPI name has **35 releases since `0.1.0`**, publisher `Jeroen Bouma`, SHA-256 recorded here. Established and consistent | Low. We did **not** enumerate confusable PyPI names: **UNVERIFIED** |
| Typosquatting exposure on the **repository URL** | See SEC-04 | **Elevated** |

**Finding SEC-04 — a stale authoritative-looking repository URL, and a live empty account
holding that name.**

```
GET api.github.com/repos/JeroenBouma/FinanceDatabase  → 404 Not Found
GET api.github.com/users/JeroenBouma                  → 200, login "jeroenbouma", id 46189588,
                                                        public_repos 0, followers 1,
                                                        created 2018-12-27, updated 2023-10-05
GET api.github.com/users/JerBouma                     → 200, login "JerBouma",     id 46355364,
                                                        public_repos 15, followers 1548,
                                                        created 2019-01-03, updated 2026-09-06
```

The **user IDs differ** (46189588 vs 46355364), so this is **not** a GitHub rename — a rename
preserves the ID and redirects. `JeroenBouma` is a distinct account that currently holds **zero**
public repositories, and much third-party material (including the tasking itself) cites
`github.com/JeroenBouma/FinanceDatabase`.

If a `FinanceDatabase` repository were ever created under that name, it would appear authoritative
to readers of older documentation, blog posts, notebooks and Q&A threads — for a project with
9,116 stars whose clients fetch data over HTTPS from a hardcoded URL. **No such repository exists
as of 2026-09-15 (VERIFIED).** Whether the path ever existed and why the account is empty is
**UNKNOWN** (U-05). This is recorded as an **ecosystem risk**, not as an allegation about any
party, and not as a defect in FinanceDatabase.

**AHOS control (mandatory if ever consumed):** pin by **commit SHA** and **artifact SHA-256**, and
verify the owner is `JerBouma` (user id **46355364**) — never by URL string alone.

## 11.5 CI / release / data-pipeline security — the highest-severity chain

**Finding SEC-05 — a third-party, tag-pinned GitHub Action executes inline Python with access to
a push-capable personal access token, and its output is distributed to every user without
integrity verification.**

```yaml
# database_update.yml — the same shape in all five jobs
- name: pull changes
  run: git pull https://${{secrets.PAT}}@github.com/JerBouma/FinanceDatabase.git main   # :17,294,359,475
- run: pip install "pandas[excel]" financedatabase                                       # :24,299,364,480,592
- name: Add New Tickers and Update Old Ones
  uses: jannekem/run-python-script-action@v1.8                                           # :25-26
  with:
    script: |
      <250+ lines of inline Python that reads a third-party URL and writes database/*.csv>
- name: Commit files and log
  run: |
    git config --global user.name 'GitHub Action'
    git add -A && git checkout main
    git diff-index --quiet HEAD || git commit -am "Update database with new tickers"
    git push                                                                              # :275-282
```

Chain of exposure, each link verified:

| Link | Fact | Status |
|---|---|---|
| 1 | `jannekem/run-python-script-action@v1.8` is a **third-party** action referenced by a **mutable tag**, not a commit SHA | **VERIFIED** |
| 2 | It executes an **arbitrary inline Python script** supplied in the workflow YAML | **VERIFIED** |
| 3 | `secrets.PAT` is materialised into a `git pull` URL in the same job, and `git push` runs later in the same job ⇒ the token has **write** access to `main` | **VERIFIED** (usage); the token's actual **scope** is **UNKNOWN** (U-08) |
| 4 | All other actions are also mutable tag refs: `actions/checkout@v6`, `actions/setup-python@v6`, `astral-sh/setup-uv@v7`, `docker://avtodev/markdown-lint:v1` | **VERIFIED** |
| 5 | `pip install … financedatabase` inside the workflow installs the **latest** release from PyPI at run time — the pipeline is not self-contained | **VERIFIED** |
| 6 | The script writes `database/equities/*.csv`, which the next job compresses to `compression/*.bz2`, which **every user downloads from `main` with no checksum** | **VERIFIED** |
| 7 | Upstream content comes from `raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/*.json` — an **unpinned `main`** branch of a **574-star single-maintainer repo with `license = None`**, whose commits are titled `generated` | **VERIFIED** |
| 8 | Bot data commits trigger **0** workflow runs and **0** check runs, so the invariant tests never see them | **VERIFIED** |
| 9 | The one validation job that does run (`Check-GICS-Categorisation`) executes **last**, after the data is pushed, and is **currently failing** | **VERIFIED** |

**Consequence:** compromising either the third-party action or the upstream ticker repo would
allow arbitrary content to be written to `database/`, compressed, pushed to `main`, and served to
every FinanceDatabase user on every version — with no checksum, no signature, no schema check and
no test gate. This is the **most consequential finding in the security review**.

It is important to be precise about severity: this is an **exposure**, not an observed incident.
No compromise was found. Nothing in the reviewed data suggests tampering. The point is that the
*defences that would detect tampering are absent*, which for AHOS means the data must be treated
as **untrusted input**, exactly as AHOS already treats provider responses.

**Finding SEC-06 — secrets handling.** `secrets.PAT` is referenced but never echoed; it is
embedded in a `git pull` URL, which means it can appear in **CI logs** if git echoes the remote
(e.g. on authentication failure) and in the **process list** of the runner. GitHub masks
registered secrets in logs, which mitigates this; whether the mask caught every occurrence is
**UNKNOWN**. No secret is present in the distributed package (**VERIFIED** — the wheel contains
only 9 modules plus metadata and `LICENSE`). A `.gitignore` (2,085 B) is present. No
`.env` handling exists in the package.

**Finding SEC-07 — release security.** Releases are tags (`2.4.0` … `0.1.10`) with GitHub
release objects. We found **no** release-signing, **no** attestation workflow and **no**
publish workflow in `.github/workflows/` (only `database_update.yml`, `testing.yml`,
`linting.yml`) — so publication to PyPI appears to be **manual** from a maintainer machine.
That is not inherently insecure, but it means PyPI artifact provenance rests on the maintainer's
credentials alone. Status: **PARTIALLY_VERIFIED** (absence of a publish workflow is verified;
the actual publication method is **UNKNOWN**, U-09).

## 11.6 Untrusted-data handling and malicious-dataset risk

| Vector | Assessment | Status |
|---|---|---|
| Malicious CSV content → code execution | **Not available.** CSV parsed by pandas; no pickle, no eval, no template rendering | **VERIFIED** (grep + source) |
| Malicious CSV content → resource exhaustion | **Available in principle.** No size cap on `response.content`; bz2 expansion is unbounded; no row-count guard | Source-verified mechanism; **NOT TESTED** |
| Malicious CSV content → schema subversion | **Available.** No expected-column assertion on load. A missing `delisted` column would raise `KeyError` at `Equities.py:80`; a renamed `country` column would make every `select(country=…)` raise `ValueError` | **VERIFIED** (source) |
| Formula injection into downstream tools (`=cmd|…` in `name`/`summary`) | Possible in principle for any text dataset. Spot checks found no such cells; a full 304,495-row scan was **not** performed | **NOT VERIFIED** |
| Untrusted `exchange` value interpolated into a filesystem path (`f'database/equities/{exchange}.csv'`, `:272`) | Constrained in practice because `exchange` is **assigned** by the workflow (`:169,175,181`), never taken from the JSON. The safety is **incidental, not defensive** | **No issue observed in reviewed scope** |
| Regex denial of service via `search()` | User-supplied strings are compiled as regexes against 112,690 rows with no escaping and no timeout. Four pathological patterns were tested: `(a+)+$` 0.19 s, `(a|a)*$` 0.17 s, `^(a+)+b$` 0.06 s, `(x+x+)+y` 0.11 s — **no catastrophic backtracking observed** | **No issue observed in reviewed scope** — this is *not* a proof of immunity |
| External API trust | The library calls **no** APIs. Only static file GETs. `to_toolkit()` delegates trust entirely to FinanceToolkit/FMP/Yahoo | **VERIFIED** |

## 11.7 Recommended classification for AHOS

The tasking asks for one of: trusted dependency · isolated research dependency · optional adapter
· vendored dataset · periodic ingestion source · non-production-only research tool.

| Classification | Appropriate? | Reasoning |
|---|---|---|
| **Trusted dependency** | **NO** | Unpinned mutable data source, no integrity verification, fail-open query API, failing CI, undeclared direct dependencies, heavy transitive tree |
| **Isolated research dependency** | **Acceptable, with conditions** | Install only into a throwaway venv outside the AHOS environment (as done here). Never into `requirements.txt` |
| **Optional adapter** | **Not now.** Conditionally later | Would require: offline snapshot ingestion, hash pinning, an AHOS-side parser, and an explicit `UNKNOWN`-by-default contract. See §14 |
| **Vendored dataset** | **PREFERRED, if ever used** | Snapshot `database/*.csv` at a pinned git SHA, record SHA-256 per file, store outside the runtime path, consume read-only. Removes the network dependency, the integrity gap and the version-decoupling problem simultaneously. **Subject to the legal review in §12** |
| **Periodic ingestion source** | **NO** | Would mean polling mutable `main` on a schedule — reintroducing every problem the vendored approach solves, with no integrity check |
| **Non-production-only research tool** | **YES — this is the recommendation** | Consistent with the overall judgment **C. RESEARCH-ONLY VALUE** (§18) |

**Mandatory controls if any consumption is ever authorized:**

1. Never install into the AHOS environment. Use a separate venv or consume raw CSV with AHOS's own code.
2. Pin by **git commit SHA** + **per-file SHA-256**; refuse any snapshot whose hash is not allowlisted.
3. Hardcode the source URL; **never** expose `base_url` to any caller or config surface.
4. Treat every value as untrusted text: trim, case-fold defensively, and map empty → `UNKNOWN`.
5. Validate the schema on ingest (expected column list per asset class); reject on mismatch.
6. Impose a size cap and a row-count cap before parsing.
7. Escape all user-derived query strings; never pass them to `search()`.
8. Record `provider`, `source_commit`, `ingest_ts` and per-field confidence on every emitted record.
9. Fail closed: any error ⇒ empty result + `UNKNOWN`, never a partial frame.
10. Keep it out of reach of `CanonicalDecisionAuthority`, scoring, security gates and the runtime (§14).
