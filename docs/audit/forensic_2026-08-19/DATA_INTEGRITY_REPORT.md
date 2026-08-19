# Data, database, schema, and provenance integrity report

## 1. Scope and method

The audit inspected every database-like file present outside `.git`/`.venv`, opened SQLite files read-only, recorded file size/schema/columns/row counts/timestamp ranges, and ran `PRAGMA integrity_check` plus `quick_check`. It also recomputed SHA-256, row counts, first/last timestamps, timestamp parseability/order/uniqueness, and basic OHLC invariants for every tracked research CSV.

No database row was changed or deleted by the inspection. A separate import-safety experiment identified pre-existing audit-session writes and stopped further unsafe import validation.

## 2. SQLite inventory

No SQLite/database binary is tracked by Git. Exactly four ignored files existed:

| Store | Bytes | Tables | Rows | `integrity_check` | `quick_check` | `user_version` | Ownership / verdict |
|---|---:|---:|---:|---|---|---:|---|
| `data/ahos_knowledge.sqlite` | 20,480 | 2 | 0 | ok | ok | 0 | generated knowledge state; empty |
| `data/ahos_local.sqlite` | 94,208 | 9 | 20 | ok | ok | 0 | generated operational state; contaminated control rows |
| `data/e01_discovery.sqlite` | 147,456 | 17 | 0 | ok | ok | 0 | generated discovery/production-observation state; empty |
| `data/paper_trading.sqlite` | 180,224 | 19 | 0 | ok | ok | 0 | generated versioned paper state; empty |
| **Total** | **442,368** | **47** | **20** | all ok | all ok | all 0 | structural state only; no empirical runtime evidence |

### Integrity conclusion

- Physical SQLite integrity is GREEN.
- Operational/scientific evidence is empty except for control-harness rows.
- Schema migration provenance is YELLOW because all stores keep `user_version=0`; schema version must be inferred from tables/triggers and source files.
- Git suitability is GREEN for the current policy: binaries are ignored and should remain untracked.

## 3. Local-store row attribution

All 20 rows are in `ahos_local.sqlite.control_flags` between `2026-08-19 15:19:49` and `16:07:09` UTC-like SQLite timestamps. Four timestamp groups have the same per-run pattern:

- 1 × `AUTH_FAIL`, detail `cmd=kill`;
- 2 × `KILL_SWITCH`, detail `test`;
- 2 × `KILL_RESET`, detail `test`.

That is five rows per execution, matching `engine/telegram_live_test.py`. The module executes its test harness and audit writes at import time. Four import attempts explain 4 × 5 = 20 rows exactly. The content is synthetic/test control evidence, not an operator kill-switch history.

Disposition:

1. preserve the DB and this attribution;
2. do not count these rows as live system evidence;
3. after an approved fix, export/hash the rows and remove or mark them only under a data-remediation manifest;
4. prevent imports/tests from targeting real ignored stores.

## 4. Store-by-store schema/data reality

### `ahos_knowledge.sqlite`

- Tables: `knowledge_claims`, `claim_contradiction_edges`.
- Composite/versioned identities and provenance fields exist.
- Both tables are empty; no claim, contradiction, confidence, review, or created-time evidence is present.
- Status: schema `IMPLEMENTED`; operational knowledge memory empty.

### `ahos_local.sqlite`

Tables include:

- `control_flags` (20 synthetic/import rows);
- `opportunity_score_ledger` (0);
- current and renamed-legacy Telegram `position_ledger` tables (0/0);
- `runtime_lifecycle_events` (0);
- `runtime_operational_metrics` (0);
- scheduler runs, locks, and heartbeats (0/0/0).

No prediction, lifecycle, metric, heartbeat, scheduler, lock, or Telegram position evidence exists. This directly bounds readiness and calibration claims.

### `e01_discovery.sqlite`

Seventeen tables are present, including canonical discovery/raw/observation/state/gap/security/feature/outcome/rank/holder/wallet tables and collector-owned production tables. Every table is empty.

Consequences:

- no current token/provider/raw-payload provenance chain exists;
- no gaps, observations, feature vectors, lifecycle events, or labels exist;
- historical reports citing hundreds of rows refer to another point-in-time database not present here;
- runtime and Lane-A share a file but not a formal migration/version owner.

### `paper_trading.sqlite`

Nineteen additive v1/v2/v3 tables are present; every table is empty. There are no strategies, decisions, paper entries/exits, portfolio rows, realizable snapshots, lessons, invalidations, or monitoring events. Code-level conservation/event-source tests are valid; current portfolio/outcome claims are not.

## 5. Research data inventory

Tracked `research/data` is about 13 MiB and contains 12 CSV outputs plus two JSON manifests.

| Dataset family | Files | Rows/time reality |
|---|---:|---|
| BTC 3-year | hourly 31,608; funding 3,924; OI 1,317 | 2023-01-01 through 2026-08-09 (funding ends 2026-07-31) |
| ETH 3-year | hourly 31,608; funding 3,924; OI 1,317 | same declared windows |
| SOL 3-year | hourly 31,608; funding 3,924; OI 1,317 | same declared windows |
| BTC extended | hourly 57,912; funding 7,212; OI 2,169 | hourly/funding from 2020; OI from 2020-09; ends as above |

### Recomputed output checks

For all 12 CSVs:

- file SHA-256 exactly matches the referenced manifest output hash;
- row count exactly matches;
- first and last timestamps exactly match;
- timestamps parse with mixed ISO fractional-second forms, have no nulls, are strictly monotonic, and have no duplicates;
- all hourly OHLC rows have positive OHLC values, `high >= low`, and close within `[low, high]`.

The fractional milliseconds in some funding timestamps are source values and require a mixed ISO parser in pandas 3; treating one rigid timestamp shape as canonical would falsely report parse failures.

### Continuity and missing source files

Manifest verdicts honestly record:

- hourly kline continuity PASS;
- 3-year funding continuity `FAIL 980 gaps` for each symbol;
- extended BTC funding continuity `FAIL 2222 gaps`;
- extended OI includes 366 missing/failed source days.

These are data limitations, not hash corruption, and must remain visible to downstream research.

## 6. Acquisition provenance and replayability

The manifests are stronger than simple output hashes:

- `MANIFEST.json`: 1,421 source records per symbol, all with URLs; 1,412 `OK` records with source SHA-256 and 9 excluded/failed records per symbol.
- `MANIFEST_ext.json`: 2,719 BTC source records, all with URLs; 2,336 `OK` hashes and 383 excluded/failed records.
- source is declared as BinanceVision USDT-M futures; acquisition timestamps, requested windows, output paths, and duration are recorded.

However, complete replay is still YELLOW:

1. source ZIP bytes are not retained, so replay depends on an external archive remaining available and byte-stable;
2. failed records have a coarse `EXCLUDED(download-failed-404?)` status rather than exact HTTP status/time/attempt evidence;
3. tool/environment versions and the exact source commit are not embedded in the manifests;
4. no signed/immutable manifest or acquisition command line is included;
5. external data redistribution/license/terms suitability is not documented in the repository;
6. the manifest requested end is midnight `2026-08-09`, while daily acquisition outputs intentionally include that day's later hours; inclusive-window semantics should be explicit.

Recommendation: do not alter dataset bytes. Add a replay descriptor containing commit, Python/package fingerprint, exact CLI/options, timezone/inclusive-end semantics, source response statuses, and licensing/redistribution assessment. Then replay in a separate output directory and compare hashes.

## 7. Prediction/outcome lineage and calibration

Current intended lineage:

```text
runtime normalized candidate
  -> deterministic score
  -> ahos_local.opportunity_score_ledger (source + engine/weights/evidence fingerprints)
Lane-A observation materialization
  -> e01_discovery.outcome_label
CalibrationHarness
  -> no-peeking/source-filtered join
```

Mechanics are strongly tested, but current facts are:

- predictions: 0;
- eligible local predictions: 0;
- labels: 0;
- fresh calibration: `INSUFFICIENT_DATA`;
- no score band or event class can be empirically assessed.

No score should be represented as a probability. No calibration threshold should be lowered to create a result.

## 8. Schema lineage risks

- Runtime DDL is distributed among domain modules; bootstrap reuses many constants but no migration registry declares owner/version/checksum.
- SQLite `user_version=0` provides no applied-migration proof.
- `production_observations` and frozen discovery tables coexist in one database under different architecture owners.
- PostgreSQL schemas are target artifacts and are not proven equivalent to SQLite.
- Telegram legacy ledger rename is timestamp-suffixed, preserving data safely but lacking a formal migration record.

P1 should add non-destructive migration metadata and schema checksums before PostgreSQL/n8n or long-running operator data begins.

## 9. Git/runtime ownership verdict

| Artifact | Keep in Git? | Rationale |
|---|---|---|
| schema SQL, bootstrap, migration metadata | yes | reproducible source |
| research CSV/manifests | currently yes, YELLOW | small enough now and hash-manifested; external terms and future growth need policy |
| runtime SQLite/WAL/SHM | no | machine-local mutable state, secrets/PII/control history risk |
| generated backups | no by default | potentially large/sensitive; store outside Git with hashes and retention policy |
| point-in-time JSON evidence | selective | only sanitized, commit/host-scoped, justified artifacts |

**Overall data verdict: structural integrity GREEN; provenance/replay YELLOW; current operational evidence RED/empty; runtime test isolation RED.**
