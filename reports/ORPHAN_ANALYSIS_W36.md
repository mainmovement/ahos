# AHOS Orphan-Module Analysis — W36 Phase 8

**Generated:** 2026-08-20 · **Method:** `scripts/validate_imports.py --ORPHANS` full import graph
(absolute + resolved relative imports incl. lazy in-function imports and
string-based `__getattr__` lazy imports in `__init__.py`).

**W35 baseline:** 14 candidates. **W36:** 13 candidates — `architecture.security.engine`
was a detector FALSE_POSITIVE (imported via the package `__init__.py`'s string-based
lazy mapping `("SecurityIntelligence": (".engine", ...))`); the detector now resolves
those, so it is no longer reported.

Classification alphabet: `SAFE_TO_REMOVE` · `KEEP_ENTRYPOINT` · `KEEP_LEGACY` ·
`NEEDS_MIGRATION` · `FALSE_POSITIVE` · `GOVERNANCE_REVIEW`.

| Module | Why it exists | Imports | Tests | CLI/doc refs | Replacement | Classification |
|---|---|---|---|---|---|---|
| `engine.acquire_3yr` | frozen backtest data acquisition | none | none | `docs/COMPONENT_REUSE_MAP.md`, `docs/STRATEGIC_GAP_ANALYSIS.md` | none (research lane tool) | **KEEP_LEGACY** (frozen-lane doc-referenced tool) |
| `engine.agent_matrix_v2` | deterministic generator for `docs/architecture/agent_matrix_v2.md` | none | `tests/test_agent_matrix_v2.py` (doc freshness pinned) | KNOWLEDGE_MAP W-part J | none | **KEEP_ENTRYPOINT** (doc generator, test-pinned) |
| `engine.coverage_audit` | F12 observation coverage guardrail | none | `tests/test_coverage_audit.py` | W27/W14 docs | none | **KEEP_ENTRYPOINT** (operational guardrail) |
| `engine.data_audit` | stage [1/6] of `engine/run_all_checks.sh` | none | none | `engine/run_all_checks.sh` | none | **KEEP_ENTRYPOINT** (CI gate stage) |
| `engine.doc_hygiene` | document hygiene engine (W7 policy v2) | none | none | W7-F/G docs, `reports/CLEANUP_MANIFEST_WAVE7.json` | none | **KEEP_ENTRYPOINT** (governance tool) |
| `engine.dryrun_simulation` | stage [4/6] of `engine/run_all_checks.sh` | none | none | `engine/run_all_checks.sh` | none | **KEEP_ENTRYPOINT** (CI gate stage) |
| `engine.oss_audit` | OSS capability audit generator | none | `tests/test_oss_audit.py` | `docs/OSS_HARVEST_LOG.md` | none | **KEEP_ENTRYPOINT** |
| `engine.pal_probe` | user-side PAL reachability probe | none | none | 11 doc refs (KNOWLEDGE_MAP, agent_matrix_v2, G_PROVIDER_MATRIX) | none | **KEEP_ENTRYPOINT** (operator tool) |
| `engine.research_report_bot` | stage [6/6] of `engine/run_all_checks.sh` (--simulate) | none | none | `engine/run_all_checks.sh` | none | **KEEP_ENTRYPOINT** (CI gate stage) |
| `engine.telegram_live_test` | stage [5/6] of `engine/run_all_checks.sh` (--simulate) | none | none | `engine/run_all_checks.sh` | none | **KEEP_ENTRYPOINT** (CI gate stage) |
| `discovery.collect` | E-01 collection CLI (Lane-A frozen) | none (CLI) | `tests/test_discovery.py` (via behavior) | Lane-A freeze list, canonical docs | none | **KEEP_ENTRYPOINT** (frozen — removal forbidden) |
| `paper_trading.cycle` | Wave-8 Track-B cycle runner (`run_full_cycle`) | none | none | none (no caller anywhere) | `paper_trading/engine_v3.py` runtime path | **KEEP_LEGACY** — **Lane-A pinned (freeze forbids removal)**; note: `run_full_cycle` has zero callers, so it is a genuine consolidation candidate for a future governance-reviewed freeze amendment |
| `config.offline_mode` | offline-first config helper (`get_offline_config`, `OfflineModeConfig`) | none | none (only a test *name* mentions offline mode) | module docstring only | none — the offline concept is realized by `architecture/providers` (ALL_PROXY) + `engine/update_manager` | **GOVERNANCE_REVIEW** — genuinely unreferenced; either wire it into a runtime consumer or propose removal via the `improvement_proposal_v1` flow |

## Summary
- **SAFE_TO_REMOVE:** 0 — no candidate has conclusive, safe deletion evidence (all either
  CI-gate stages, doc-referenced tools, test-pinned generators, frozen-Lane files, or
  governance-review items).
- **KEEP_ENTRYPOINT:** 10 · **KEEP_LEGACY:** 2 (both Lane-A frozen) ·
  **GOVERNANCE_REVIEW:** 1 (`config.offline_mode`).
- No file was deleted. Removal remains a governance decision per the W35 orphan-gate design.

## Detector improvement (W36)
The ORPHANS check now also resolves **string-based lazy imports** in `__init__.py`
(the `("__getattr__", {attr: (".module", "Name")})` pattern), eliminating the
`architecture.security.engine` false positive. Pinned by
`tests/test_validate_orphans.py`.
