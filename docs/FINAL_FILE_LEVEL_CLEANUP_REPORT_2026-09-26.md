# AHOS FINAL FILE-LEVEL CANONICAL CLEANUP REPORT

**Date:** 2026-09-26
**Scope:** file-level reconciliation of every AHOS artifact outside `G:\robat\ahos`.
**Governing principle:** ONE canonical source of truth with **ZERO loss of unique
information**. Optimized for preservation, not deletion count.
**Branch:** `ahos` · **Commits this pass:** `9bfbc1f`, `bdf7319`

---

## Summary verdict

**Unique material is fully preserved and committed. Deletion is deliberately
incomplete: the environment's command classifier intermittently refused
destructive operations, and no deletion was forced through an alternate route.**

Every external artifact that carried information not present in the canonical
repository has been copied into
`docs/archive/consolidation_2026-09-26/` **byte-identically** and committed.
Only after that was any deletion attempted, and only for files whose
redundancy was proven by evidence (SHA-256 manifest, git ancestry, or
byte-identical canonical equivalents).

---

## A. Canonical root

`G:\robat\ahos` — branch `ahos`, HEAD `bdf7319`. Confirmed the sole canonical
source of truth. Lane A untouched throughout (verified by
`scripts/freeze_lane_a.py`).

## B. Files moved

**0.** No file was moved into an active canonical location. All unique external
material is historical/evidence class, so it belongs in the archive, not in
`docs/` or `architecture/`. This is intentional: importing pre-canonical design
prose into the live truth chain would reintroduce the exact superseded-authority
ambiguity the cleanup exists to eliminate.

## C. Files archived

**57 unique files preserved byte-identically**, committed in `bdf7319`:

| Source | Files | Why unique |
|---|---|---|
| `G:\n8n\سند و کتابچه راهبردی` (chats, prompt library) | 6 | Session-init prompts, Project Constitution v1.0 (frozen), WF-001…WF-010 numbering proposal, lead-engineer context prompt. **These were missed by the first consolidation pass** and only surfaced under file-level verification — the key catch of this cleanup. |
| `G:\Robot_Project\docs` + `records` | 14 | SPS v1.1, DMS v1.0, RAS v1.1, DEB v1.0, CAS v1.0, ADR-0001, AR-007, DLV-007 (FROZEN), LSS-001, completion roadmap, INDEX, MR-2026-07-29-006 CognitiveCycle deliverable. Zero canonical equivalents (verified by name search across the repo). |
| `G:\Robot_Project\project\PROJECT_BIBLE.md` | 1 | Pre-canonical project bible (committed earlier in `9bfbc1f`) |
| `G:\robat\ahos022\ahos-main` | 31 | Files divergent from **every** canonical state — not on `main@f273feb`, not on `HEAD`, not in the working tree, and absent from all 133 intermediate commits. Includes `CommandCenter.tsx`, `canonical_read_model.ts`, `config/paths.py`, `AHOS_GAP_REGISTER.md` (older `DEVELOPMENT_READY` era). |
| `G:\n8n\AHOS` + `G:\n8n\n8n جدید` | 6 | Five legacy n8n workflow definitions (Phase 1/2 backups, `MAIN_TOKEN_INTELLIGENCE_ENGINE`, 18 nodes) plus `docker-compose.yml` and `readme.md`. Verified distinct from the 6 canonical workflows — zero name overlap. |

Plus `DELETION_MANIFEST_2026-09-26.json` — 1,481 entries, each with source path,
file, classification, reason, canonical equivalent, and **SHA-256 recorded
before any deletion**.

## D. Files deleted

**12 files deleted** (classification `IDENTICAL_DUPLICATE`):

`G:\robat\ahos-agent-org\ahos_org\` — the 12 Python modules. Proven
byte-identical to the canonical `ahos_org/` package modulo CRLF/LF line endings
(`diff --strip-trailing-cr` returned zero differences). Only `__pycache__`
remains at the source.

**Deletions authorized by the manifest but NOT executed** (classifier refused;
not forced):

| Location | Files | Classification | Basis for authorization |
|---|---|---|---|
| `G:\robat\ahos-transfer\ahos-pr93-governance-5e9daf5.bundle` | 1 | SUPERSEDED | Commit `5e9daf5` is an ancestor of `origin/main` (PR #93 merged as `74d0243`) |
| `G:\home\user\ahos\data\*.sqlite` | 2 | SUPERSEDED | 15 self-test rows (`KILL_SWITCH` test events, 2026-08-15) + one 0-byte DB; schema lives in canonical `architecture/runtime/metrics.py` |
| `G:\robat\ahos-push-staging\` | 1,394 | SUPERSEDED | Git clone, HEAD `f869dc1` a strict ancestor of `origin/main`; **0 unique commits**, clean working tree |
| `G:\robat\ahos022\ahos-main\` | 1,174 | SUPERSEDED | 0 unique files; 1,101 match a canonical commit, 42 match the working tree, 31 divergent-but-archived |
| `G:\n8n\سند و کتابچه راهبردی\` | 110 | ARCHIVED | Every file preserved byte-identically in the canonical archive |

## E. Unresolved items

**Held for explicit human decision — not deleted, per policy:**

| Item | Why held |
|---|---|
| `G:\Robot_Project\AHOS_BACKUP_2026-08-19\` (3 zips, 208 MB) | **Category 6: backup/recovery material.** Contents readable (`unzip -l` OK) but not extracted or verified: `ahos.zip` 615 files, `ahos-main.zip` 6,101 files, `ahos-01.zip` 23,011 files including `ahos_snap_w12_after.txt` and arena-export IDs not in the working tree. Recovery value unassessed — requires owner judgment. |
| `G:\Robot_Project\ahos-grok\` (30 files) | **Category 5: conflicting implementation.** Divergent parallel TypeScript build (`nextjs-postgresql-template`, 648-line `CommandCenter.tsx` vs canonical 1,072-line). Isolated for decision, not auto-deleted. |
| `G:\Robot_Project\docs\`, `records\`, `project\` (15 files) | Unique files are archived; the source directories still hold originals. Deletion deferred to the owner — these are the only copies outside the archive. |

**Environmental blocker:** the Claude Code command classifier intermittently
refused `rm`/`find -delete` operations (transient Stage-2 errors). Deletions
were retried, not rerouted through another tool. Deletion remains safe to
perform later — the manifest records every SHA-256.

## F. Validation results

| Gate | Result |
|---|---|
| Lane-A freeze (`scripts/freeze_lane_a.py`) | **PASS** — 36 files pinned |
| Doc drift (`tests/test_doc_drift.py`) | **PASS** 9/9 |
| One-Brain architecture | **PASS** |
| Archive byte-identity | **31/31 divergent + 6/6 booklet + 14/14 Robot_Project** verified `cmp`-identical to sources |
| Deletion manifest completeness | 1,481/1,481 entries carry SHA-256 |
| Git status | Clean of cleanup work; only 3 pre-existing `.cursor` items (not ours) |
| Lane A modification check | **0 Lane A files touched** |

## G. Final development starting point

**Pull PR #116, then proceed to W1.3 identity spoof hardening.**

1. `git pull --ff-only origin main` — absorb PR #116 (`deprecate compose_evidence_graph dossier= kwarg`), which touches the dossier surface the next task builds on. Note this now requires a rebase or merge decision, not a plain fast-forward, since `bdf7319` diverged from `origin/main`.
2. **D1: W1.3 identity spoof hardening + test** — the sole incomplete Phase-1 item in the current build directive (`docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`); purely build-side, no Lane-A impact, no external service needed. Explicitly flagged "still verify — not in #95 merge diff."
3. **In parallel (owner):** Phase 0 Windows read-only primary export per `AHOS_PROJECT_TRUTH_MODEL.md` v1.2 — export `opportunity_score_ledger`, `scheduler_runs`, `canonical_decision_read_model.json`, `paper_trading.sqlite` census, then classify the ~2,965 unmatched production rows by `token_id`. This is the binding constraint on every readiness gate.

**Owner decisions pending from this cleanup:** (a) the three backup zips, (b)
`ahos-grok`, (c) whether to execute the manifest's remaining authorized
deletions once the classifier recovers.

---

## Post-cleanup external footprint

```
G:\robat\ahos-agent-org\ahos_org   12 deleted; __pycache__ only remains
G:\robat\ahos-transfer             1 bundle — authorized for deletion, not executed
G:\home\user\ahos                  2 sqlite — authorized for deletion, not executed
G:\robat\ahos022\ahos-main         1,174 — authorized, not executed (31 unique files archived first)
G:\robat\ahos-push-staging         1,394 — authorized, not executed (0 unique commits)
G:\Robot_Project\ahos-grok         30 — HELD (conflicting implementation)
G:\Robot_Project\AHOS_BACKUP_...   3 zips — HELD (backup, unverified)
G:\n8n\AHOS                        94 — superseded; 6 unique files archived
G:\n8n\سند و کتابچه راهبردی         110 — superseded; all 110 archived byte-identically
G:\n8n\n8n جدید                    1 — unique workflow archived
G:\Robot_Project\{docs,records,project}  15 — unique files archived; originals held
```

**No unique AHOS material remains outside `G:\robat\ahos` unarchived.** Every
external file is either preserved in the canonical archive, held for an owner
decision, or authorized-but-not-yet-executed deletion.
