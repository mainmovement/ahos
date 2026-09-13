# PR #95 merged — supervision event

**Timestamp:** 2026-09-13T16:28Z  
**PR:** [#95](https://github.com/mainmovement/ahos/pull/95) — W2 read-only claim/evidence graph  
**Action:** `ready_for_review` → **MERGED** to `main`  
**Merge commit:** `6f61656a0cf575bfa40a3f1ae02ee9f649fcfbab`  
**Prior `main`:** `8eb78d5` (PR #94)

## Scope landed

- `architecture/knowledge/evidence_graph.py`
- `architecture/knowledge/EVIDENCE_GRAPH.md`
- `tests/test_evidence_graph.py`

## Governance impact

| Item | Before | After |
|------|--------|-------|
| W2 on `main` | **NO** (branch-only) | **YES** |
| Phase 1 D2 (merge #95) | Pending | **COMPLETE** |
| Phase 1 D1 (W1.3) | Pending | **UNKNOWN** — not in #95 diff |
| W4 stack vs main | Ahead | **Still ahead** (#97–#103) |
| §20 locks | #103 BLOCK, Slice 8 BLOCK | **UNCHANGED** |
| Soak / evidence gates | D-009 open | **UNCHANGED** |

## G3 integration

**PARTIAL improvement** — W2 evidence graph available on `main`. Telegram live and operator Windows export remain open.

## Council STATUS

**`MONITOR`** — no directive change. Do **not** interpret W2 merge as Launch readiness or soak closure.

## Next

- Verify W1.3 status if not yet on `main`
- Build agent: complete remaining Phase 1 items (DOSSIER, POST-FLIGHT) before Phase 2
- Owner: Windows primary export (D-009) remains binding
