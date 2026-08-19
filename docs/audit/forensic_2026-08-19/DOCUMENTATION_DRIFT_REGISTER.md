# Documentation precedence and drift register

## 1. Precedence

This audit accepts the repository's current precedence with one clarification: executable evidence from the audited commit outranks all prose, including a canonical document written earlier the same day.

1. immutable law, current code, versioned schemas, safety tests, Lane-A hashes;
2. re-executed evidence tied to the audited commit/environment;
3. `docs/canonical/CANONICAL_STATUS.md`;
4. canonical domain and operational documents;
5. research/design proposals;
6. historical phase/readiness reports.

A filename containing “FINAL”, “PRODUCTION”, “READY”, or a score does not establish current readiness.

## 2. Classification reality

| Class | Representative files | Audit treatment |
|---|---|---|
| Immutable/normative law | `docs/canonical/MASTER_DIRECTIVE_v1.md`, safety invariants, Lane-A freeze | must not be silently changed; current code/tests determine enforcement |
| Canonical current architecture/status | `README.md`, `ARCHITECTURE.md`, `docs/canonical/CANONICAL_STATUS.md` | preferred prose, but subject to evidence corrections below |
| Operational | quickstarts, installation, Windows/soak runbooks, n8n setup | procedure, not proof that the procedure ran |
| Implementation/test evidence | current source, schemas, tests, dated machine reports | valid only for identified commit/host/time and actual command |
| Research/design | `docs/architecture/*`, `docs/mission_v1_1/*`, research reports | proposals/experiments; do not imply runtime integration |
| Historical | root phase/final/production reports, `reports/PHASE_STATE.md`, archived patches/snapshots | chronology; not current status |
| Contradictory/stale | specific entries below | preserve, banner, correct link/index; no destructive cleanup |

## 3. Drift register

| ID | Document/claim | Current evidence | Classification / action |
|---|---|---|---|
| DOC-001 | `AHOS_FINAL_STATUS.md`: runtime smoke scored 13 tokens and emitted 1 alert | This may be a historical run, but current `e01_discovery.sqlite`, local score ledger, and metrics are empty. No live provider run occurred in this audit. | Historical claim. Add a historical banner and artifact/commit link; never display as current. |
| DOC-002 | `AHOS_PRODUCTION_READINESS_REPORT.md`, `reports/phase21_production_readiness.md`: production-ready wording/91.81 score | Docker, native Windows, Telegram, providers, n8n, PostgreSQL, and Ollama were not executed here; calibration has 0 pairs. | Superseded historical readiness assessment. Preserve; banner prominently. |
| DOC-003 | Root phase reports and `reports/PHASE_STATE.md`: 411/450/475/481/493/500/505/516/996-test milestones | Current executed suite is 1,414 passed. Old counts are valid only as dated phase evidence. | Historical; index by date/commit. Do not globally replace counts inside history. |
| DOC-004 | `AHOS_LOCAL_PRODUCTION_GATE_REPORT.md`: “Full test suite PASS — 996 tests” | Current suite 1,414 passes; host-dependent gates remain unrun. | Historical point-in-time report, not a gate for current checkout. |
| DOC-005 | `AHOS_PROJECT_STATE_MAP.md` and issue register: live token/observation counts and live provider probe results | Current ignored generated discovery DB has 0 rows. Historical source DB/artifact is not present in this workspace. | Retain as dated historical evidence; add artifact ownership/retention caveat. |
| DOC-006 | `config/agent_registry.yaml`: agents marked `live: true` and evidence references live row counts | Current stores lack those rows; “live” has no `observed_at`, host, commit, or artifact existence condition. Registry also says zero orchestrated agents. | Machine-readable documentation drift. Add time-scoped evidence and generated current projection. |
| DOC-007 | `config/agent_registry.yaml` AG-11 status `PLANNED` while implementation is true; canonical status says integrated panel/council capabilities | Registry mixes capability status, code existence, and runtime operation. Some entries were overtaken by current integration. | Reconcile dimensions; never use one status field for all realities. |
| DOC-008 | `docs/canonical/CANONICAL_STATUS.md`: Docker root compose described as canonical laptop convenience | Canonical intent is valid, but no `.dockerignore` means a normal `.env` can be copied into the image and large/machine-local state enters build context. Docker was unavailable. | Current doc needs a **do-not-build-until-fixed** warning. |
| DOC-009 | `docs/canonical/CANONICAL_STATUS.md`: n8n static 6/6 limitation is honest | Operational docs can still imply import/use after starting UI. Root compose lacks PostgreSQL for workflows 01–03, and no compose mounts `/opt/ahos` for workflows 10–12. | Add explicit workflow-family prerequisites and disconnected status. |
| DOC-010 | `README.md`: “Licensed under the Apache-2.0 License” | No `LICENSE`, `LICENSE.txt`, `COPYING`, or tracked license file exists. | **Contradictory/legal P1.** Add the actual approved license text or stop claiming a license; human/legal owner decision required. |
| DOC-011 | Requirements header: every package is free, permissively licensed, and installable offline from a wheel cache | Licenses were not locked/audited in repository metadata; no wheel cache, lockfile, hashes, or SBOM is supplied. Installer only honors an operator-provided `AHOS_WHEELHOUSE`. | Overbroad. Change to a tested dependency/license table after verification. |
| DOC-012 | Requirements/optional header: deterministic floor runs at “100% capability” on core dependencies | Optional parsing and AI client conveniences are not required for deterministic score, but live providers, data, Telegram, and host services still govern capability. | Replace “100% capability” with “core deterministic code path.” |
| DOC-013 | `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`: exact commands verified at commit `164766b` | Audited code snapshot is `c775978`; commands may still exist but the pinned statement is stale. | Update generated commit/evidence linkage or remove fixed SHA from current runbook. |
| DOC-014 | Windows installer says native Python mode is “fully supported” when Docker absent | Scripts are plausible and Linux static tests pass, but no PowerShell/Windows host was available. | Replace with “intended/supported by design; native validation required” until a Windows artifact exists. |
| DOC-015 | Multiple operational reports call cross-platform/Windows verification complete | Current tests inspect text, paths, subprocess CLIs on Linux; they do not execute PowerShell, batch behavior, sleep/restart, or Docker Desktop. | Historical/static evidence only. Explicitly label host. |
| DOC-016 | Self-evolution reports call a 14-stage “engine” verified/integrated | State transition validation is tested, but there is no persistence, repo planning, tool use, change execution, deployment, monitoring, or rollback. | Reclassify capability as contract/state-machine scaffold. |
| DOC-017 | Update manager docs imply governed updates can be applied | `apply_update()` only records approval in memory and returns success; it executes no update. | Misleading current implementation description. Rename to plan/approval validator or implement bounded action later. |
| DOC-018 | Self-repair design/phase reports imply self-repair | Health manager can diagnose selected checks and create an empty missing SQLite file. It does not restore schema/data or run a repair-test-rollback loop. | `PARTIALLY_IMPLEMENTED`; avoid “self-healing” claim. |
| DOC-019 | AI provider registry notes claim a configured local model “keeps working” offline and is strong for Persian | No Ollama host/model/hardware/Persian benchmark ran. Model presence is a user action; routing is chat-only. | Treat as unverified model-selection rationale, not measured capability. |
| DOC-020 | AI comments list provider costs/accessibility/model names as factual | Provider plans, model IDs, sanctions/access, and endpoints can drift. Most `iran_accessibility` fields are honestly UNKNOWN, but prose is stronger. | Require dated probes/links; otherwise mark external metadata UNVERIFIED. |
| DOC-021 | n8n setup guidance treats mounted JSON as ready to import/run | Workflows are not auto-imported, credentials are absent, DB/path assumptions differ by family. | Add exact import, credential, schema, mount, and dry-run gates. |
| DOC-022 | Root compose says `run_bot.py` “does the same thing” as Docker/runtime | Root compose starts both a runtime that polls Telegram and a standalone long-poller; behavior and offset/backoff ownership differ. | Correct architecture docs and choose one inbound polling owner. |
| DOC-023 | `ARCHITECTURE.md` shows one provider -> score -> alert flow | Actual system also has the separate frozen Lane-A observation/outcome flow, two table families in the discovery DB, score ledger/calibration, specialist veto/panel/advisor, and three paper lineages. | Current but incomplete. Link to this architecture map or expand carefully. |
| DOC-024 | `docs/canonical/CANONICAL_STATUS.md`: “all twelve CSV datasets read/row-counted/matched” | Recomputed and confirmed true. However this does not by itself reproduce external acquisition failures/continuity verdicts or establish redistribution rights. | Keep claim; add scope clarification. |
| DOC-025 | Historical E-01 reports preserve validated/live experiment narrative | Later canonical history also records `INSUFFICIENT_DATA` / not validated. Current generated DB is empty. | Retain unique science history; current conclusion remains not empirically validated. |
| DOC-026 | Import validation described as deterministic/network-free architecture safety gate | It is network-free, but importing `engine.telegram_live_test.py` executes writes/report generation. | Current validator claim is false for side-effect freedom; fix P0 and add store-diff evidence. |
| DOC-027 | `README.md` says `.start_ahos` makes observation polling/outcome labeling/calibration-eligible predictions active | Command wiring is correct. “Active” still depends on provider returns, open tracked tokens, and uninterrupted operator host. | Clarify active scheduling vs successful data production. |
| DOC-028 | `docs/DOCUMENT_CLASSIFICATION.md` precedence puts code first and labels old reports historical | This is correct and is the strongest current anti-drift control. | Keep; add this audit directory to the index. |
| DOC-029 | `run_bot.py` and compose comments promise visible backoff/recovery on tunnel/network failure | Adapter polling swallows exceptions and returns an empty update list, so the launcher's documented outer error/backoff branch is bypassed. | Correct code and add a live/injected failure test before retaining the claim. |
| DOC-030 | Pipeline metrics/announcement memory imply Telegram delivery | Adapter failures return `ok=false`; callers count and remember sends without checking acknowledgement. | Treat counts as attempts until P0 repair; do not claim delivered alerts from current metrics. |

## 4. Current facts that should replace broad readiness language

- Full suite: **1,414 passed in 171.47s**, with caveats in `TEST_REALITY_REPORT.md`.
- Current generated evidence: **0 predictions, 0 labels, 0 discovery rows**, not a failure but not validation.
- External services: **not executed** in this audit.
- Native Windows and Docker: **not executed** in this audit.
- n8n: **six JSON files structurally valid**, not operationally connected.
- Ollama: **chat endpoint configured**, host/model unproven; no embeddings/RAG/tools.
- Safety: no live-trading execution surface found.

## 5. Preservation rule

Do not delete stale documents merely to make search results cleaner. First add a machine-readable/front-matter classification, point to the current status, preserve commit/date and unique evidence, and then—only with approval—relocate clearly historical files under an archive path with a manifest.
