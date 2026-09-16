# FinanceDatabase — Deep Technical Investigation

**Subject:** `financedatabase` (PyPI) / `JerBouma/FinanceDatabase` (GitHub)
**Investigation date:** 2026-09-15 (UTC)
**Classification:** `RESEARCH_ONLY` — no AHOS production code was modified, no integration was implemented.
**Prepared for:** AHOS (Artificial Hybrid Opportunity Scoring System) — Evidence-First Crypto Opportunity Intelligence Platform

---

## 0. What this package is (one paragraph)

FinanceDatabase is a **static, weekly-refreshed, GitHub-hosted CSV catalogue of financial
*listings***, wrapped in a ~1,900-line Python library that downloads bzip2-compressed CSVs
from the `main` branch of its own repository at object-construction time and exposes
`select()` / `search()` / `show_options()` over in-memory pandas DataFrames. It contains
**no market data, no prices, no fundamentals, no timestamps, no on-chain data and no scoring
logic**. Its cryptocurrency table is a ~2020-era Yahoo Finance / CryptoCompare *symbol pair*
list of 352 token tickers with no chain, no contract address and no liquidity — **Solana does
not appear under the ticker `SOL` at all** (it appears as `SOL1`).

## 1. Final judgment

> ### **C. RESEARCH-ONLY VALUE**
> With an explicit **rejection (E)** of the crypto / opportunity-detection use case,
> and a documented conditional path to **B (RECOMMENDED WITH STRICT BOUNDARIES)** that
> opens *only* if and when AHOS starts a non-crypto reference-catalogue lane, under
> separate written authorization **and** a completed legal review (document 12). That
> path is a **vendored, hash-pinned snapshot parsed by AHOS's own code** — never an
> installed package, never a `ProviderRouter` adapter, never the live network path
> (document 14, §14.6).

Full reasoning: [`18_RECOMMENDATION_AND_NEXT_STEPS.md`](18_RECOMMENDATION_AND_NEXT_STEPS.md)

## 2. Reading order

| # | Document | Question it answers |
|---|---|---|
| — | [`00_EXECUTIVE_SUMMARY.md`](00_EXECUTIVE_SUMMARY.md) | What did we find, and what does it mean for AHOS? |
| 1 | [`01_SOURCE_AND_REPOSITORY.md`](01_SOURCE_AND_REPOSITORY.md) | Which repository is authoritative? Package/version/license/deps/activity |
| 2 | [`02_ARCHITECTURE_RECONSTRUCTION.md`](02_ARCHITECTURE_RECONSTRUCTION.md) | What does the code actually do, file by file, line by line? |
| 3 | [`03_DATA_PIPELINE.md`](03_DATA_PIPELINE.md) | Where does the data come from and how does it become queryable? |
| 4 | [`04_SCHEMA_AUDIT.md`](04_SCHEMA_AUDIT.md) | Actual columns, types, nullability, per asset class |
| 5 | [`05_IDENTITY_AND_ENTITY_RESOLUTION.md`](05_IDENTITY_AND_ENTITY_RESOLUTION.md) | Issuer vs security vs listing vs symbol; AHOS compatibility |
| 6 | [`06_QUERY_ENGINE_AUDIT.md`](06_QUERY_ENGINE_AUDIT.md) | `select` / `search` / `show_options` truth table (measured) |
| 7 | [`07_DATA_QUALITY_AND_FRESHNESS.md`](07_DATA_QUALITY_AND_FRESHNESS.md) | Update cadence, staleness, survivorship, look-ahead, reproducibility |
| 8 | [`08_CRYPTOCURRENCY_COVERAGE.md`](08_CRYPTOCURRENCY_COVERAGE.md) | Can it see a new Solana token? (No — and here is the proof) |
| 9 | [`09_EXTERNAL_INTEGRATIONS.md`](09_EXTERNAL_INTEGRATIONS.md) | FinanceToolkit / FMP / Yahoo: what belongs to whom |
| 10 | [`10_PERFORMANCE_AND_SCALABILITY.md`](10_PERFORMANCE_AND_SCALABILITY.md) | Measured load, memory and latency (with environment) |
| 11 | [`11_SECURITY_AND_SUPPLY_CHAIN.md`](11_SECURITY_AND_SUPPLY_CHAIN.md) | Attack surface, integrity, CI/PAT exposure, dependency risk |
| 12 | [`12_LICENSE_AND_LEGAL_REVIEW.md`](12_LICENSE_AND_LEGAL_REVIEW.md) | MIT code vs. unlicensed upstream data, CUSIP/FIGI/GICS |
| 13 | [`13_ADVERSARIAL_FAILURE_ANALYSIS.md`](13_ADVERSARIAL_FAILURE_ANALYSIS.md) | 20 break-it scenarios with evidence and AHOS fail-closed rules |
| 14 | [`14_AHOS_INTEGRATION_ASSESSMENT.md`](14_AHOS_INTEGRATION_ASSESSMENT.md) | Design sketch only — **not implemented** |
| 15 | [`15_AGI_ACI_RESEARCH_VALUE.md`](15_AGI_ACI_RESEARCH_VALUE.md) | Value as a knowledge substrate (not as intelligence) |
| 16 | [`16_EVIDENCE_REGISTER.md`](16_EVIDENCE_REGISTER.md) | Every claim, its source, type, date, confidence, status |
| 17 | [`17_UNKNOWNS_AND_OPEN_QUESTIONS.md`](17_UNKNOWNS_AND_OPEN_QUESTIONS.md) | What we could not verify, and why |
| 18 | [`18_RECOMMENDATION_AND_NEXT_STEPS.md`](18_RECOMMENDATION_AND_NEXT_STEPS.md) | Decision matrix, judgment, gated next steps |

## 3. Evidence artifacts

Everything under [`evidence/`](evidence/) is machine-generated output, not prose.

| Artifact | Contents |
|---|---|
| `evidence/ENVIRONMENT.txt` | Exact interpreter, library versions, host, CPU/RAM, **measured network reachability**, artifact SHA-256s |
| `evidence/schema_audit.json` | Per-asset row counts, column lists, per-column empty counts, duplicate-symbol counts |
| `evidence/query_truth_table.json` | Every `select` / `search` / `show_options` case with expected vs. actual behaviour |
| `evidence/identifier_issues.csv` | Output of the project's **own** validator run against the project's **own** data |
| `evidence/scripts/a1…a12*.py` | The 12 scripts that produced the above. Re-runnable. |

### Reproducing this investigation

```bash
# 1. Isolated venv (NEVER the AHOS environment)
python3 -m venv /tmp/fdb_venv
/tmp/fdb_venv/bin/pip install "pandas==3.0.5" numpy requests pytest "python-stdnum>=2.2" \
                              pytest-mock pytest-recording pytest-timeout tqdm openpyxl
/tmp/fdb_venv/bin/pip install --no-deps <financedatabase-2.4.0 wheel>

# 2. Source-of-truth checkout at the exact audited commit
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/JerBouma/FinanceDatabase.git /tmp/fdb_repo
cd /tmp/fdb_repo && git sparse-checkout set compression database tests .github financedatabase

# 3. Run the evidence scripts from the repo root (the package resolves local
#    data as Path(__file__).parent.parent/"compression", so cwd/import path matters)
cd /tmp/fdb_repo && /tmp/fdb_venv/bin/python /path/to/evidence/scripts/a6_query_engine.py

# 4. Run the project's own suite
cd /tmp/fdb_repo && /tmp/fdb_venv/bin/python -m pytest tests/ -q
#    -> expected at commit a174c97d: 1 failed, 85 passed  (CHAD symbol collision)
```

> **Note:** `raw.githubusercontent.com` is unreachable from the audit host, so the package's
> *default* (remote) data path could not be exercised. All library-level tests were run with
> `use_local_location=True` from a repository checkout. This is recorded, not hidden — see
> [`17_UNKNOWNS_AND_OPEN_QUESTIONS.md`](17_UNKNOWNS_AND_OPEN_QUESTIONS.md) U-01.

## 4. Governance statement

This investigation complied with the constraints in §1 of the tasking:

- **No AHOS production code was modified.** The only files created are under
  `research/finance_database_investigation/` (this directory).
- **Nothing was installed into the AHOS environment.** All Python work happened in
  `/tmp/fdb_venv`, an isolated virtualenv outside the repository.
- **No dependency was added** to `requirements.txt` or `requirements-optional.txt`.
- **No provider was added** to `architecture/providers/registry.py`.
- **No integration was implemented.** `14_AHOS_INTEGRATION_ASSESSMENT.md` is a design
  sketch and is explicitly marked *not authorized for implementation*.
- Frozen Lane A, Canonical Decision Authority, scoring, security gates, identity
  resolution, runtime, calibration, the active soak, production data, database state,
  secrets and operational services were **not touched**.
- No `UNKNOWN` was upgraded to `SAFE`. No stale value is presented as live. No document
  is presented as proof where a test was possible.

Where a claim could not be verified it is written **UNVERIFIED** or **UNKNOWN** and listed
in document 17. Where behaviour was measured, the measurement environment is stated.
