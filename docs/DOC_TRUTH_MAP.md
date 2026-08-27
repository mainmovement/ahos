# AHOS — Document Truth Map

**Purpose:** One place that says which files are current authority vs historical evidence.  
**Law:** UNKNOWN / OPEN gaps beat older “READY” prose. Archive history; do not delete C-class evidence.

## A — Current authority (start here)

| Topic | Path |
|-------|------|
| Immutable master doctrine | `docs/canonical/MASTER_DIRECTIVE_v1.md` + `docs/canonical/master_directive_registry.json` |
| Wave ops directive (living, not registry ACTIVE) | `docs/canonical/MASTER_DIRECTIVE_W43.md` |
| Project state pointer | `docs/canonical/PROJECT_STATE.md` → `reports/PHASE_STATE.md` |
| Open operational gaps | `AHOS_GAP_REGISTER.md` |
| Living change register | `AHOS_ISSUE_REGISTER.md` |
| Local laptop gate (honest) | `AHOS_LOCAL_PRODUCTION_GATE_REPORT.md` |
| Operator start | `README.md`, `QUICKSTART.md`, `AHOS_OPERATOR_QUICKSTART_WINDOWS.md` |
| Lane-A freeze | `config/lane_a_freeze.sha256` + `scripts/freeze_lane_a.py` |

## B — Historical / superseded (do not cite as current readiness)

| Path | Note |
|------|------|
| `AHOS_FINAL_STATUS.md` | SUPERSEDED — contains banned `READY_FOR_DEPLOYMENT` claim |
| `AHOS_PRODUCTION_READINESS_REPORT.md` | SUPERSEDED — score/READY overclaim |
| Other root `AHOS_PHASE*.md` / month reports | Wave evidence; check date vs gap register |
| `docs/archive/oss_research/` | Former root `OSS_*.md` |
| `reports/archive/snaps/` | Former root `ahos_snap_*.txt` |

## C — Do not confuse these layers

| Layer | What it is | Not |
|-------|------------|-----|
| AHOS runtime AI council | In-product advisory routing (`architecture/ai/`, `config/ai_*`) | Cursor Cloud Agent models |
| Web Command Center TS at repo root | One-Brain surface pinned by `tests/test_one_brain_architecture.py` | Orphan Next templates (removed) |
| App Router | `app/page.tsx`, `app/layout.tsx`, `app/api/**` | Deleted root `page.tsx` / `layout.tsx` / `route.ts` |
| Python observation daemon | Lane-A evidence producer (`python -m architecture.runtime`) | Telegram independent scorer (forbidden W57) |
| Telegram Domain Service | Gateway client only (`AHOS_GATEWAY_URL`) | Pre-W57 in-process scoring brain |

**Dual-stack ownership (binding):** Chat/explanation for humans flows through the TS Conversation Gateway. Continuous observation, scoring ledger, and calibration accrue on the Python daemon. Telegram must call the gateway; it must not invent a second brain.

## D — Honesty gate (binding)

Any sentence claiming `READY_FOR_DEPLOYMENT`, `PRODUCTION_READY`, or a readiness percentage without a linked artifact in `AHOS_GAP_REGISTER.md` is **not current truth**.

## E — Completion artifacts (2026-08-27)

| Artifact | Path |
|----------|------|
| Implementation matrix | `docs/CANONICAL_IMPLEMENTATION_MATRIX.md` |
| Final truth audit | `docs/FINAL_TRUTH_AUDIT.md` |
| Next-phase backlog (await owner approval) | `docs/NEXT_DEVELOPMENT_BACKLOG.md` |
| Owner action checklist | `docs/OWNER_ACTION_REQUIRED.md` |
| Stale design snapshots (bannered) | `docs/SECURITY_CHECKLIST.md`, `docs/MISSING_COMPONENT_REGISTER.md`, `docs/STRATEGIC_GAP_ANALYSIS.md` |

**Classification pointer:** `INTEGRATION_READY` (agent-host) — see `docs/FINAL_TRUTH_AUDIT.md`. Operator laptop + soak + Telegram live remain EXTERNAL.
