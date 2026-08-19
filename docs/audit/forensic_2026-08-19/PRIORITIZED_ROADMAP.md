# Prioritized remediation roadmap and phased implementation plan

## 1. Decision rule

This roadmap optimizes for less code and more verified capability. It does not authorize implementation. Product code, schemas, runtime data, dependencies, architecture, or historical assets should not change until the user explicitly approves a phase or item.

Priority meanings:

- **P0:** containment/safety defect; fix before another broad import validation, real Telegram deployment, or Docker build.
- **P1:** foundation required for reproducible operation and trustworthy evidence.
- **P2:** integration/reliability improvement after foundations pass.
- **P3:** optional advanced capability only after measurable need and host evidence.

## 2. P0 — contain harmful/unsafe surfaces

| ID | Work item | Why now | Bounded implementation | Acceptance evidence |
|---|---|---|---|---|
| P0-01 | Make imports side-effect-free | `engine/telegram_live_test.py` executes/writes on import; import gate caused 20 real-store rows | move harness under `main(argv)`, require explicit mode/output/store, keep simulated behavior and tests; classify all executable modules | import in fresh process causes zero file/DB/network changes; explicit CLI still passes temp-store tests |
| P0-02 | Isolate test/import stores and reports | autouse fixture bootstraps real ignored stores; tests can consume/operator-pollute local state | establish session temp root via environment before application imports; bootstrap there; mark opt-in local-state tests | full suite passes from clean clone; pre/post repository file hashes and real DB row counts unchanged |
| P0-03 | Add safe Docker build context | no `.dockerignore`; `.env`, `.git`, `.venv`, data/reports can be sent and copied into image | minimal `.dockerignore` covering secrets, VCS, venv, runtime DB/WAL, reports/scratch/caches/backups while retaining required source/config | context manifest contains no `.env`, credential, VCS, venv, runtime DB, report secret; image scan confirms no secret; Docker build when host available |
| P0-04 | Fail closed for Telegram authorization | blank allowlist authorizes everyone; template leaves it blank | require non-empty allowlist for network mode or explicit `TELEGRAM_OPEN_ACCESS=1`; console remains available; preflight blocks ambiguity | unauthorized test denied; blank config blocks live poll; explicit open mode loudly reported; authorized Persian flow passes |
| P0-05 | Repair Telegram ownership and delivery evidence | root compose has two pollers; embedded polling supplies no offset; poll failures are swallowed; send failures can be counted/remembered as delivered | choose one inbound poll owner, persist offset, expose scrubbed poll failures/backoff, and require `ok=true` before delivery count/announcement memory | one `getUpdates` owner; no duplicate/drop on restart; tunnel-drop visible/backed off; failed sends produce zero delivery count and no announcement record |
| P0-06 | Preserve and classify 20 contaminated rows | synthetic import writes could be mistaken for operator evidence | write a sanitized row export/hash/attribution artifact; do not delete until explicit data-remediation approval | immutable artifact ties rows to import executions; current DB unchanged until separate approval |
| P0-07 | Publish deployment stop warnings | current canonical docs can lead to unsafe Docker/private bot operation | add concise warnings linked to audit; do not rewrite history | README/canonical Docker/Telegram instructions cannot be followed without seeing blockers |

### P0 stop conditions

- Do not run `scripts/validate_imports.py` against real paths until P0-01/P0-02.
- Do not build the Docker image until P0-03.
- Do not expose a real Telegram bot until P0-04/P0-05.
- Do not delete/normalize contaminated rows during code containment.

## 3. P1 — reproducibility, ownership, and delivered-operation foundations

| ID | Work item | Bounded scope | Acceptance evidence |
|---|---|---|---|
| P1-01 | Dependency lock and clean install | create platform-aware Python 3.11 lock/constraints with hashes or documented resolver method; retain source requirements; no environment commit | clean Linux and Windows x64 installs; dependency fingerprint; offline wheel manifest test; vulnerability/license report |
| P1-02 | Resolve repository license claim | owner chooses/adds actual license and notices, or removes Apache claim; audit dependency/data terms | tracked license matches README; legal provenance for research data and dependencies documented |
| P1-03 | Schema owner/version registry | define each table owner, schema checksum, ordered additive migrations, `user_version`/migration ledger, bootstrap parity | fresh + upgrade-from-copy + rollback drill; table/trigger/data integrity and idempotency pass |
| P1-04 | Protect evidence namespaces | bind calibration-eligible rows to eligible baseline ID/hash, host fingerprint, commit, and run ID; keep sandbox/local-unqualified paths | source spoof test fails closed; join/no-peeking tests pass; existing rows preserved/migrated non-destructively |
| P1-05 | Provider architecture reconciliation | inventory Lane-A PAL/runtime router/ProviderCollector; unify envelopes/config projections without altering frozen scientific behavior | no provider behavior regression; provenance/conflict/failure tests; Lane-A hashes unchanged unless separately governed |
| P1-06 | AI routing/config reconciliation | keep active LiveCouncil; port only proven circuit/health/provenance semantics; deprecate nothing yet | one generated registry view, blocking-timeout test, deterministic offline behavior, no paid route by default |
| P1-07 | n8n/compose reality choice | select either PG-node or command workflow family for one profile; add exact mounts, schema, credentials, import | compose config/build plus automatic/manual import artifact and one harmless end-to-end workflow; other family labeled experimental |
| P1-08 | Docker hardening | pin images by version/digest policy, remove meaningless 8000 mapping, health/read-only mounts, non-root and secret handling | Docker build/config/run on target; health, restart, no secret, writable-path, resource evidence |
| P1-09 | Native Windows clean-install proof | execute installer/PS/batch on clean Windows path with spaces; record host/commit/deps | all gates and exact exit codes; UTF-8 Persian; store integrity; no Docker required |
| P1-10 | One process/runtime owner | reconcile canonical runtime, control plane, OS supervisor, n8n, bot responsibilities | architecture contract and process graph; no duplicate schedulers/pollers; start/stop/status semantics proven |
| P1-11 | Current-status generation | make agent/capability status time/commit/artifact scoped; retain historical fields | generated current matrix reports UNKNOWN when artifact absent; stale historic evidence never becomes live automatically |
| P1-12 | Test lane taxonomy/CI | add markers and offline CI; preserve all assertions; separate host/live lanes | unit/integration/architecture/security counts; code coverage baseline; zero real-store writes; external lanes explicitly NOT RUN |
| P1-13 | Research replay descriptor | add exact acquisition command, environment, source status, inclusive-window, data terms; do not alter CSV bytes | replay in separate directory reproduces output hashes or records exact source drift |
| P1-14 | Repair/update truthfulness | make health/update outputs reflect actual actions; empty-DB creation cannot be success | missing DB uses canonical bootstrap/restore or refuses; “apply” cannot return applied when no action ran |

## 4. P2 — integration and resilience

| ID | Work item | Bounded scope | Acceptance evidence |
|---|---|---|---|
| P2-01 | Reconcile paper identities/ledgers | explicit adapters among canonical positions, versioned research, and Telegram statements; never infer allocation | schema/identity mapping; no duplicate positions; unknown allocation stays unknown; replay tests |
| P2-02 | Empirical evidence accumulation | operate observation-first on approved Windows host; no threshold changes | provider probe, eligible baseline/t0, real observations/predictions/outcomes, honest insufficient status until guards pass |
| P2-03 | Windows supervision/recovery | one Task Scheduler/service wrapper, restart limits, stop/uninstall, rotating logs | hard crash, sleep/resume, reboot, stale lease, disk fault, and log rotation drills |
| P2-04 | Backup/restore and data retention | encrypted/off-Git backups as appropriate; restore to isolated path; retention policy | seven distinct-day backups for soak, restore equality/integrity, documented deletion approval |
| P2-05 | Native/live contract probes | opt-in provider, Telegram, Ollama, PostgreSQL/n8n lanes with recorded artifacts | each lane reports PASS/FAIL/NOT RUN independently; deterministic offline suite remains green |
| P2-06 | Whale/intelligence vocabulary adapter | reconcile evidence-composed and specialist whale concentration semantics | one shared field/evidence contract; no double penalty; risk/score/panel regression tests |
| P2-07 | Control-plane disposition | either integrate bounded status/start ownership or keep target-only | no second orchestration architecture; injected simulations separated from production probes |
| P2-08 | Persistent governance proposals | append-only proposal stage events with JSON-schema and evidence hash validation | resume/idempotency, authenticated approval reference, no stage skip, artifacts exist and match commit |
| P2-09 | Local Ollama chat proof | one optional model, configurable host, health/model probe, hardware benchmark | offline Persian structured benchmark, latency/RAM/disk, model digest, cancellation, deterministic fallback |
| P2-10 | Real soak | only after P0/P1 and recovery drills | Windows-bound valid baseline/t0, downtime-adjusted 168 hours, end report, no readiness inflation |

## 5. P3 — optional advanced capabilities

| ID | Work item | Entry condition | Acceptance evidence |
|---|---|---|---|
| P3-01 | Additional calibration metrics | enough real eligible score/outcome pairs | current no-peeking/source contract retained; Brier/Murphy/probability mapping only if mathematically appropriate |
| P3-02 | RAG/vector retrieval benchmark | defined corpus/query need not served by structured claims/FTS | sqlite/local candidate beats simpler baseline on citations/recall/resource cost; Windows/offline pass |
| P3-03 | Sandboxed engineering assistant | P0/P1 evidence isolation and P2 persistent governance complete | read-only planner first; typed allowlisted tools; bounded patches/tests; approval; audit; executable rollback |
| P3-04 | OSS candidate sandbox | explicit user approves one candidate audit | license/security/SBOM/source/test/Windows/offline/benchmark/replay comparison; no direct production integration |
| P3-05 | Standard telemetry | real multi-process diagnosis need established | OpenTelemetry candidate beats current tracer with bounded dependencies and local/no-export mode |
| P3-06 | Durable orchestration evaluation | single-laptop baseline proves scheduler limitation | Temporal benchmark compares crash/replay/resource/migration complexity; no parallel production orchestrator |
| P3-07 | PostgreSQL migration | SQLite concurrency/scale evidence justifies it | full schema/data/replay parity, backups, rollback, n8n integration, Windows host cost |

## 6. Proposed implementation phases and approval gates

### Phase 0 — containment patch

Scope: P0-01 through P0-07 only. Expected change is small: entry-point guards, temp path harness, authorization semantics, Docker ignore, process ownership config/docs, and preservation artifact. No feature expansion.

**Gate:** user explicitly approves Phase 0.
**Exit:** full offline suite, import/store side-effect proof, secret/context check, and diff review.

### Phase 1A — reproducible source and state

Scope: dependency/license decisions, schema ownership, evidence namespaces, test lanes, replay descriptor.

**Gate:** separate approval because locks/license/schema metadata affect repository governance.
**Exit:** clean Linux + Windows installs, fresh/upgrade schema drills, zero store contamination, current-status artifact.

### Phase 1B — delivered process topology

Scope: one bot poller, one scheduler owner, one chosen Docker/n8n profile, Docker hardening.

**Gate:** approval of selected topology; alternatives remain preserved.
**Exit:** target-host Docker/native proofs and harmless workflow E2E.

### Phase 2 — evidence/reliability operation

Scope: Windows supervision, crash/sleep/reboot/backup/provider/Telegram drills, then real evidence collection and soak.

**Gate:** operator confirms laptop availability and accepts external calls/credential use.
**Exit:** host-bound artifacts; calibration may honestly remain insufficient.

### Phase 3 — optional AI/autonomy/OSS

Scope: one measured need at a time. No framework migration or dependency inflation.

**Gate:** candidate-specific proposal after prior phases.
**Exit:** benchmark demonstrates improvement over current smaller implementation, with rollback.

## 7. Explicit non-goals

- no live trading, exchange orders, wallet signing, or real financial execution;
- no wholesale repository replacement;
- no deletion of duplicate/history/data without manifests and approval;
- no lowering calibration/sample/security thresholds;
- no marketing-only AI wrappers, persona swarms, dashboards, or vector stores;
- no PostgreSQL/Temporal/n8n adoption because they look more “production”;
- no force push, history rewrite, environment/cache/credential commit;
- no major rename/refactor before integration evidence.

## 8. Approval request

The recommended next action is **Phase 0 only**. Please approve a specific scope, for example:

> “Approve Phase 0 containment only; preserve all data/history; show the diff and test evidence before proceeding to P1.”

Without explicit approval, this audit stops at documentation and planning.
