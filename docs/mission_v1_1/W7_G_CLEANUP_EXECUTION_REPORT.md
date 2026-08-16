# DOCUMENT CLEANUP EXECUTION REPORT (Deliverable G) — 2026-08-11
# Machine evidence: reports/PROJECT_DOCUMENT_INVENTORY_WAVE7.json · reports/CLEANUP_MANIFEST_WAVE7.json

## 1. Inventory vs 194-file wave-6 baseline
- Current: **230 files**, 17.31 MB (ahos 152 + uploads 78 after archiving moves are re-counted under uploads/_archive_exact_dups_wave7/).
- Delta vs baseline: **+45 added, −9 removed, 16 changed** (changed = wave-6 edits after its own inventory; removed = 5 .pytest_cache snapshot-excluded files + 4 archived-as-moved dups).
- All 45 added files enumerated in the inventory JSON (wave-6 deliverables + wave-7 artifacts).

## 2. Classification (policy v2 classes)
| Class | Files | Bytes | Action law applied |
|---|---|---|---|
| A CANONICAL | 16 | 0.06 MB | untouchable by automation |
| B ACTIVE | 56 | 3.74 MB | keep |
| C HISTORICAL | 152 | 13.40 MB | preserve (never auto-removed) |
| D SUPERSEDED/ARCHIVED | 6 | 0.11 MB | archived, stubs/manifests in place |
| E EXACT DUP | 0 (4 archived this wave) | — | archived → D-pool |
| F REDUNDANT | 0 flagged | — | flag-only; none met the full-representation bar *beyond doubt*, so none acted on |
| G TEMP | 0 (6 deleted this wave) | — | deleted, regenerable |

## 3. Executed actions (11/11 OK, sha-verified, reversible)
- ARCHIVED (uploads → uploads/_archive_exact_dups_wave7/), pre/post sha256 match:
  BTCUSDT_1h_1000_renamed.csv (=BTCUSDT_1h_1000.csv) · FINAL_SOLUSDT_chunk5.csv (=chunk4) ·
  PHASE_2_BACKTEST_REPORT_FINAL.md + PHASE_2_FINAL_REPORT.md (=PHASE_2_BACKTEST_REPORT.md).
- DELETED (regenerable): 6 __pycache__ bytecode files; n8n_runtime/ tree (≈200 MB incl. node_modules,
  snapshot-excluded; regeneration recipe: `npm install n8n@2.8.4`; workflows canonical in
  ahos/n8n/workflows/; live-import evidence preserved: reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt).
- Idempotency: second dry-run planned **0 actions** (release gate met).

## 4. Reduction achieved & context economy
- Exact-duplicate payload removed from the active pool; temp weight eliminated; active tree now
  100% classifiable: 16 canonical docs entry-point (docs/canonical/) + 56 active + archived dups.
- Wave-6 near-dup report (6 similar-content pairs, different basenames) remains the F-review backlog;
  wave-7 basename near-dup detector found 1 pair (README vs strategy_lab/README — distinct content,
  correctly inactionable). Method difference recorded for the Auditor; content-similarity detector
  = wave-8 engine improvement.
