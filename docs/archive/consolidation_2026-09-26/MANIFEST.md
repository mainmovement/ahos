# AHOS Consolidation Archive — 2026-09-26

**Purpose:** Preserves AHOS material discovered outside the canonical root
(`G:\robat\ahos`) during the 2026-09-26 master canonical consolidation.

**Law applied:** Nothing in this archive is current AHOS authority. Everything
here is **HISTORICAL_EVIDENCE** from a pre-canonical (July 2026) documentation
lineage. It must never be cited as readiness, architecture, or governance
truth. The canonical chain in `docs/DOC_TRUTH_MAP.md` governs.

**No external directory was deleted, moved, or modified.** Every source below is
left untouched in place. This archive is a read-only preservation copy.

---

## Provenance rules

Every imported artifact retains:

| Field | Meaning |
|-------|---------|
| `SOURCE_PATH` | Original absolute location outside the canonical root |
| `SOURCE_DATE` | Filesystem mtime range of the source tree |
| `SOURCE_GIT_STATE` | Git state of the source (none = not a git repo) |
| `REASON_PRESERVED` | Why it was worth importing |
| `CLASSIFICATION` | A–H reconciliation class (see `DOC_TRUTH_MAP`-aligned scheme) |

Classification alphabet used here: `CANONICAL_ACTIVE` · `CANONICAL_FROZEN` ·
`HISTORICAL_EVIDENCE` · `SUPERSEDED` · `DUPLICATE` · `UNIQUE_CANDIDATE` ·
`CONFLICTING` · `UNKNOWN`.

---

## Imported: pre-canonical standards booklet

**Source root:** `G:\n8n\سند و کتابچه راهبردی`
("standards document and strategic booklet")

| Field | Value |
|-------|-------|
| SOURCE_PATH | `G:\n8n\سند و کتابچه راهبردی` |
| SOURCE_DATE | 2026-07-04 → 2026-07-25 (mtimes) |
| SOURCE_GIT_STATE | None — plain directory, not a git repository |
| REASON_PRESERVED | Contains AHOS engineering standards, strategic specifications, workflow catalogs, and daily/session engineering reports that exist **nowhere** in the canonical repository (verified by name search: 0 canonical hits for every standard name). This is the surviving pre-canonical design corpus. |
| CLASSIFICATION | **HISTORICAL_EVIDENCE** (pre-canonical design lineage) |

### Mappings

| Archive path | Original source subpath | Notes |
|---|---|---|
| `booklet_standards/` | `AHOS Standards/` | 10 files. **9 are 0-byte placeholders** (Code Review, Database, Error, JSON, Logging, Naming, Prompt, Versioning, Workflow Standards). Only `AHOS_Universal_Market_Object_Standard_v1.0.md` (86,426 bytes) has content. Placeholders are preserved as evidence of intended-but-unwritten standards, not as content. |
| `booklet_architecture_freeze/` | `Architecture Freeze/` | `AHOS Architecture Freeze v1.1.md` is a **0-byte placeholder**. `AHOS_Roadmap_v1.2.1_Change_Record.md` (60,629 bytes) has content. |
| `booklet_strategic_specs/` | `سند راهبردی/` | 9 real specifications: AECS v1.0, AES v1.0 (Frozen), DDS v1.0, FRS v1.0, AIP v1.0 (Frozen), SAO v1.0, System Objectives v1.0, System Vision v1.0, AWC v1.0. Plus `workflow/` (WF-001 Master Scheduler contracts, parts 1–8) and `آرشیو/` (Architecture Bible v4.0/v4.1, Strategic Master Plan v10.0, Technical Architecture Spec v1.1, Ultimate Vision v1.0, Data Architecture Spec v1.0, Engine Specifications). |
| `booklet_daily_reports/` | `اسناد مکمل روزانه/` | ADER daily engineering reports and SDR development session reports, plus a Persian-language daily-supplement archive (`آرشیو/`). |
| `booklet_timeline/` | `project timeline/` | Pre-reset n8n workflow exports (`AHOS_PreReset_[1..6].json`, Phase 2.1 Discovery Scheduler, Phase 2.2 DexScreener Collector). |
| `booklet_root_new_text_document.txt` | `New Text Document.txt` | Unnamed working note (10,454 bytes), 2026-07-22. |

### ⚠ Honesty constraint on this material (binding)

Several archived filenames contain **readiness-like language that is NOT
current truth and was never validated**, e.g.:

- "AHOS Architecture Bible v4.1 — **Production Lock Edition**"
- "**Ultimate Production Lock Edition**"
- "Architecture Freeze v1.1"

These are July 2026 design-document titles only. Under `docs/DOC_TRUTH_MAP.md`
§D, no readiness claim is current truth without a linked artifact in
`AHOS_GAP_REGISTER.md`. None of these documents is such an artifact.
**"Production Lock" here means a documentation freeze decision made in July
2026, not a validated production state.** The current honest classification
remains `INTEGRATION_READY` (agent-host); `PRODUCTION_READY` is a forbidden
claim.

The "Architecture Freeze v1.1" in this booklet is **not** the operative AHOS
freeze. The real, binding freeze is Lane A: `config/lane_a_freeze.sha256` +
`scripts/freeze_lane_a.py` (36 files), governed by `AGENTS.md`.

---

## Imported: project bible

| Field | Value |
|-------|-------|
| SOURCE_PATH | `G:\Robot_Project\project\PROJECT_BIBLE.md` |
| SOURCE_DATE | 2026-07-28 |
| SOURCE_GIT_STATE | None — `G:\Robot_Project\project` is not a git repo |
| REASON_PRESERVED | The only non-empty file (227 lines) in a parallel project-management tree. References a specification set (SPS v1.1, DMS v1.0, RAS v1.1, DEB v1.0, CAS v1.0) that is **not** part of the canonical chain — evidence of a separate, superseded documentation lineage. |
| CLASSIFICATION | **HISTORICAL_EVIDENCE** / **SUPERSEDED** — its spec names (SPS/DMS/RAS/DEB/CAS) do not appear in the canonical truth chain; do not treat them as authority. |

Note: the sibling files in `G:\Robot_Project\project\` (`DECISION_LOG.md`,
`MILESTONES.md`, `NOTES.md`, `PROJECT_STATUS.md`, `RISKS.md`, `ROADMAP.md`,
`TEAM_WORKFLOW.md`, `TODO.md`) are all **0 bytes** and were not imported.

---

## External copies NOT imported (left untouched)

Each was checked for unique material. None required import.

| External path | Git state | Finding | Classification |
|---|---|---|---|
| `G:\robat\ahos-agent-org\ahos_org` | None | Byte-identical to canonical `ahos_org/`; differs **only** by CRLF vs LF line endings (verified with `diff --strip-trailing-cr`: zero differences). Zero unique value. | **DUPLICATE** |
| `G:\robat\ahos022\ahos-main` | None | Snapshot of the repo at the `main@f273feb` era. **0 unique files** vs canonical working tree (verified with quotepath-disabled comparison). Older truth state — its `AHOS_GAP_REGISTER.md` still says `DEVELOPMENT_READY`, superseded by the current `INTEGRATION_READY`. Its `DOC_TRUTH_MAP.md` lacks all 2026-09-09 addenda. | **SUPERSEDED** |
| `G:\robat\ahos-push-staging` | `main` @ `f869dc1`, clean, remote `github.com/mainmovement/ahos` | A strict ancestor of `origin/main` (0 unique commits, 25 behind). Already fully contained in the canonical history. | **SUPERSEDED** |
| `G:\robat\ahos-transfer` | None (git bundle) | `ahos-pr93-governance-5e9daf5.bundle`. Its commit `5e9daf5` **is an ancestor of `origin/main`** — PR #93 is already merged (recorded in `docs/DOC_TRUTH_MAP.md` as merged at `74d0243`). | **HISTORICAL_EVIDENCE** (already in canonical history) |
| `G:\Robot_Project\AHOS_BACKUP_2026-08-19` | None | Three zip archives: `ahos.zip` (5.5 MB), `ahos-main.zip` (43 MB), `ahos-01.zip` (161 MB). Bulk backups; not inspected byte-for-byte. Left as owner-held backup. | **HISTORICAL_EVIDENCE** (backup) |
| `G:\Robot_Project\ahos-grok` | None | 30-file Next.js app (`name: nextjs-postgresql-template`, Next 16.2.6). A **divergent parallel implementation**: its `src/components/CommandCenter.tsx` is 648 lines vs the canonical root `CommandCenter.tsx` at 1,072 lines — different content. Its README points at `docs/AHOS_WEB_COMMAND_CENTER.md`, which exists only inside that copy, not in the canonical repo. Not imported: importing a second, divergent command-center surface would reintroduce exactly the "second brain" ambiguity `AGENTS.md` forbids. | **CONFLICTING** (parallel implementation, not authority) |
| `G:\home\user\ahos` | None | Legacy Linux-era runtime data directory: `data/ahos_local.sqlite` (16,384 bytes, 2026-08-16) and `data/e01_discovery.sqlite` (0 bytes, 2026-08-15). No documentation, no unique information. Matches the obsolete `/home/user/ahos` path lineage recorded in canonical history. | **HISTORICAL_EVIDENCE** (legacy data root) |
| `G:\n8n\AHOS` | None | July 2026 n8n/docker deployment stack (`docker-compose.yml`, postgres, redis, storage-service, collectors) with Phase-1/Phase-2 workflow backups. Predates the canonical `n8n/workflows/` set (`ahos_01..ahos_12`); no filename overlap. Canonical AHOS requires no VPS/docker (per `docs/supervision/AHOS_PROJECT_TRUTH_MODEL.md` §3). | **SUPERSEDED** |
| `G:\n8n\data` | None | Dead n8n instance runtime database (`database.sqlite` + WAL). **Not copied** — a live-format SQLite store must never be copied into the canonical tree (per `AGENTS.md`: never share SQLite between worktrees). | **HISTORICAL_EVIDENCE** (runtime data, left in place) |

---

## Reconciliation of the branch discrepancy (resolved)

The pre-consolidation investigation flagged that supervision documents describe
the W2 evidence graph (`6f61656`, PR #95) as "on main" while the local `main`
ref did not contain it.

**Root cause: the local `main` branch was stale, not the documents.**

| Ref | Before | After |
|-----|--------|-------|
| local `main` | `f273feb` (2026-09-09) | `8ae411a` (fast-forwarded) |
| `origin/main` | `4b37be3` at session start, `8ae411a` after fetch | `8ae411a` |
| `6f61656` ancestor of `origin/main`? | **YES** | **YES** |

`main` had 0 unique commits versus `origin/main` — it was simply behind, having
last been updated by `pull --ff-only origin main` (confirmed via `git reflog
main`). The supervision documents were correct: they refer to GitHub's `main`,
which does contain `6f61656` and the entire W2/W3/W4 merge sequence up to
`f869dc1`.

**Action taken:** `git fetch origin main:main` — a pure fast-forward of a stale
local ref to its own upstream, matching the repository's established
`pull --ff-only` maintenance pattern. No merge, no checkout, no rebase, no
force-push. The prior SHA `f273feb` remains reachable via `git reflog main`.

**Result:** local `main` == `origin/main` == `8ae411a`. The active development
branch `ahos` was left at `4b37be3`, which the fetch revealed is now 2 commits
behind `origin/main` (PR #116, `deprecate compose_evidence_graph dossier=
kwarg`). That pull was **not** performed — see remaining blockers.

**No documentation needed correction for this item.** The docs were right; the
local ref was stale.
