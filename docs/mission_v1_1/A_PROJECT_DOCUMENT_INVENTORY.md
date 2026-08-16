# A. PROJECT DOCUMENT INVENTORY — Wave-6 (2026-08-11)
Machine form: reports/PROJECT_DOCUMENT_INVENTORY.json (path/size/sha/title/category per file).

| Category | Files | Policy |
|---|---|---|
| historical | 78 | kept read-only / archived |
| active-code | 36 | CI-referenced; keep |
| canonical-detail | 17 | keep; referenced by canonical set |
| source-dataset | 14 | IMMUTABLE sha-pinned |
| canonical | 13 | never archive; update in place |
| canonical-report | 10 | keep; current evidence |
| research-evidence | 9 | IMMUTABLE (Part XXIV) |
| research-code | 6 | keep |
| temporary | 5 | snapshot-excluded; may vanish |
| generated-report | 4 | regenerable; keep latest linked in TEST_REPORT |
| runtime-store | 2 | keep (wal/continuity) |

TOTAL: 194 files (ahos=116, uploads=78)

Component marks: canonical set EXISTS · inventory LIVE VERIFIED (hashes computed this run) · uploads historical.