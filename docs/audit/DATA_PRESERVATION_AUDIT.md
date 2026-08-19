# AHOS Data Preservation Audit

**Audit date:** 2026-08-19
**Scope:** tracked datasets, manifests, schemas, operational evidence, ignored runtime state.

## SQLite state at the start of audit

No SQLite/DB artifact existed anywhere in the checkout before validation. The `data/`
directory and its four stores were created later by the executed bootstrap/import tests;
they are reproducible empty runtime state and are correctly ignored. Therefore there is no
uncommitted historical SQLite content to merge or delete in this checkout.

The generated stores were inspected after bootstrap:

| Store | Integrity | Tables | Rows of note |
|---|---|---:|---|
| `e01_discovery.sqlite` | `ok` | 16 | all evidence tables 0 |
| `paper_trading.sqlite` | `ok` | 19 | all paper tables 0 |
| `ahos_local.sqlite` | `ok` | 8 | 5 bootstrap control flags; score/position/runtime rows 0 |
| `ahos_knowledge.sqlite` | `ok` | 2 | 0 |

These files are not release artifacts and are not committed. Versioned SQL, bootstrap code,
append-only guards and backup/restore tooling are the reproducible source of truth.

## Tracked research datasets

All 12 CSV files were opened, headers and row counts checked, and SHA-256 values recomputed.
Every value matches `research/data/MANIFEST.json` or `MANIFEST_ext.json`:

| Dataset group | Rows |
|---|---:|
| BTC/ETH/SOL 1h 3-year candles | 31,608 each |
| BTC/ETH/SOL funding 3-year | 3,924 each |
| BTC/ETH/SOL daily open interest 3-year | 1,317 each |
| BTC extended 1h candles | 57,912 |
| BTC extended funding | 7,212 |
| BTC extended daily open interest | 2,169 |

The manifests originally embedded historical `/home/user/ahos/...` acquisition paths. Those
provenance strings were normalized to repository-relative `research/data/...` paths. Dataset
bytes, row counts, timestamps, and recorded SHA-256 values were not changed.

## Operational and historical evidence

`research/experiments/`, `research/reports/`, and dated `reports/` contain unique
observations, replay results, provider probes, paper cycles and failure evidence. They are
preserved. Exact duplicate report aliases may be removed only after their hash and canonical
replacement are recorded in the deletion manifest.

The raw patch files are also unique historical evidence because the uploaded Git history has
one commit. After their SHA-256 values and recovered capabilities were documented, all three
were relocated without content changes to `docs/history/source-patches/`; none was discarded.

## Secrets

No real `.env` file or credential database was present. Templates contain placeholders only.
The validator's secret scan passed. Runtime DBs, `.env*` (except examples), tokens, keys and
credential directories remain ignored. No credentials are migrated into source control.
