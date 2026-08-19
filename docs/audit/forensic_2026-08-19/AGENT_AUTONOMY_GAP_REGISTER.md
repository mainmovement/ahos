# Agent/autonomous-engineering gap register

## 1. Scope

This report distinguishes:

- **market/intelligence automation** — scheduling observations, scoring, alerts, and paper advice; from
- **autonomous engineering** — inspecting a repository, planning changes, executing tools, repairing defects, testing, using Git, producing evidence, and rolling back under approval boundaries.

AHOS has meaningful market/intelligence automation. It does **not** have an autonomous engineering agent. Agent names, council roles, a control plane, and an improvement-proposal state machine do not by themselves provide that capability.

## 2. Existing building blocks worth preserving

| Building block | Real capability | Boundary |
|---|---|---|
| `architecture/control_plane.py` | idempotent start/status/stop/safe-halt/resume model, topology checks, append-only ledger, injected health | isolated; no production launcher/probers/process controller |
| `config/agent_registry.yaml` | 25-role machine-readable design/operability matrix | historical/stale evidence; explicitly zero orchestrated agents |
| `architecture/evolution/engine.py` | in-memory sequential proposal stage validation and human approval rule | no persistent/action loop; contract loaded but not enforced |
| `architecture/evolution/hindsight.py` | structured outcome explanation/lesson logic | Telegram advice, not engineering diagnosis |
| `engine/health_manager.py` | selected diagnostics and repair proposals | no safe general repair loop |
| `engine/update_manager.py` | drift/approval-plan data object | no update executor |
| evidence scripts | command metadata, state snapshots, backups, import/secret checks | human-invoked utilities |
| broad pytest suite | strong offline regression contract | no autonomous planner/runner owner; runtime-store isolation defect |
| immutable laws/human gates | strong authority constraints | must remain non-bypassable in any future agent |

## 3. Gap register

| ID | Required capability | Current evidence | Status | Minimum safe closure |
|---|---|---|---|---|
| AGAP-001 | Goal decomposition and bounded planning | proposal contains diagnosis/diff reference/test list supplied by caller; no planner | `MISSING` | produce a read-only plan with scope, files, risks, tests, approval level, and stop conditions |
| AGAP-002 | Repository inventory/inspection | no agent filesystem/search/AST/schema/Git inspection tools | `MISSING` | read-only tools with workspace root confinement, size limits, binary/secret handling, and evidence IDs |
| AGAP-003 | Architecture/import impact analysis | human/static scripts exist, not agent-composed | `PARTIAL` | invoke existing AST/import/schema gates and summarize inbound/outbound impact before edits |
| AGAP-004 | Tool registry and typed calls | no tool protocol, permissions, or result envelopes | `MISSING` | explicit tool schemas, per-tool authority, timeout, output cap, and immutable audit log |
| AGAP-005 | Python command execution | evidence scripts use subprocess, but no bounded agent executor | `MISSING` | allowlisted `.venv` Python commands in sandbox/temp state; no arbitrary shell by default |
| AGAP-006 | PowerShell/Windows execution | no PowerShell host/tool | `MISSING` | remote/local Windows worker with command allowlist, working-dir pin, timeout, UTF-8, and sanitized artifacts |
| AGAP-007 | Test selection and execution | test commands are human-run; no planner maps changes to tests | `MISSING` | conservative affected-test map plus mandatory architecture/full gates; never delete/weaken failing tests |
| AGAP-008 | Diagnosis from failures | health manager reports selected issues; no traceback/root-cause loop | `PARTIAL` | structured failure parser, hypothesis/evidence ranking, reproduction before change |
| AGAP-009 | Code editing/patch generation | no agent edit engine | `MISSING` | bounded unified patch in a clean worktree, file/line/size scope, forbidden paths, review before apply |
| AGAP-010 | Repair loop | no inspect -> reproduce -> edit -> test -> reassess loop | `MISSING` | capped iterations, explicit stop/escalate states, regression/full-suite gate, no silent retries |
| AGAP-011 | Database-safe migration repair | bootstrap exists; health “repair” may create blank file | `BROKEN/PARTIAL` | backup/hash/copy, versioned migration, integrity/replay checks, approved cutover and rollback |
| AGAP-012 | Git awareness | evidence scripts read SHA/status; no change staging/commit/revert logic | `PARTIAL read-only` | clean-tree precondition, diff review, branch pin, signed evidence, no force push/history rewrite |
| AGAP-013 | Commit/PR workflow | absent from product | `MISSING` | human-approved commit and PR only; never merge/promote autonomously |
| AGAP-014 | Evidence packaging | strong utility scripts, no unified proposal/run ledger | `PARTIAL` | tie plan, tool calls, diffs, test artifacts, environment, approval, and final status to one run ID |
| AGAP-015 | Persistent proposal state | `SelfEvolutionEngine` returns in-memory dataclass | `MISSING` | append-only versioned store with schema, actor identity, stage events, evidence hashes, resume semantics |
| AGAP-016 | Contract enforcement | improvement contract is loaded but create/advance do not validate instances against it | `BROKEN/PARTIAL` | JSON-schema validation plus semantic gates at creation and each transition |
| AGAP-017 | Evidence-gated stage transitions | `evidence_ref` argument is not validated or stored; stage fields are not automatically tied to artifacts | `BROKEN` | require existing immutable artifact IDs, expected verdicts, commit match, and hash verification |
| AGAP-018 | Human identity/approval verification | caller supplies string/bool; self-approval string check only | `SCAFFOLD` | external authenticated approval record, role/scope, expiration, challenge, non-repudiation appropriate to local system |
| AGAP-019 | Approval boundaries | laws are strong; implementation has no tool-level scopes | `PARTIAL` | read-only auto; edits/tests in sandbox; DB/schema/deps/Lane A/deploy always explicit human gates |
| AGAP-020 | Rollback planning | proposal requires a trigger string | `SCAFFOLD` | machine-checkable restore point, rollback command, data compatibility, verification and owner |
| AGAP-021 | Rollback execution | no executor; `MONITORING` is terminal so rollback from it is blocked | `BROKEN/MISSING` | tested rollback from deployment/monitoring with append-only event; never erase evidence |
| AGAP-022 | Deployment/monitoring | proposal stage names exist, no deploy/process/metric integration | `MISSING` | bounded canary/local deployment only after approval, health SLO, auto-stop, human promotion |
| AGAP-023 | Security/secret sandbox | scanners/redaction exist; no agent sandbox or egress policy | `PARTIAL` | deny credential files/network by default, redact tool output, dependency/source quarantine, resource limits |
| AGAP-024 | Dependency/license/security audit | OSS spec exists, metadata only | `SCAFFOLD` | SBOM, license full-text, vulnerability/advisory, transitive deps, maintenance, Windows/offline audit |
| AGAP-025 | Learning without self-promotion | laws forbid auto-promotion; no measured engineering feedback loop | `PARTIAL safe` | aggregate anonymized run outcomes into proposals only; human gate remains mandatory |
| AGAP-026 | Concurrency/ownership | canonical runtime, control plane, n8n, and OS launch assets can become competing orchestrators | `ARCHITECTURE GAP` | select one process owner; other surfaces become adapters, not parallel authorities |
| AGAP-027 | Windows rollback/recovery | operational docs are manual; no agent/host supervisor | `MISSING` | Windows-native snapshot/restore/restart worker tested on actual laptop |
| AGAP-028 | User-visible capability honesty | agent registry/docs mix EXISTS/PARTIAL/live/history | `BROKEN/PARTIAL` | generate status from artifact+test+runtime evidence with timestamps; UNKNOWN on absent evidence |

## 4. Self-evolution state-machine forensic findings

`SelfEvolutionEngine` is safety-oriented but not an evolution engine in an operational sense:

1. `create_proposal()` rejects Lane A and forces a human requirement for AI/governance proposals.
2. `advance_stage()` prevents ordinary stage skipping and requires a human flag/name for `APPROVED`.
3. The loaded JSON contract is not applied to proposal validation.
4. `evidence_ref` is accepted but neither stored nor verified.
5. replay, test, red-team, council, governance, deployment, and monitoring stages do not invoke those systems.
6. proposal state is not persisted, transactionally logged, or resumable.
7. human identity is a caller-supplied string/bool.
8. `MONITORING` is terminal; `ROLLED_BACK` cannot be reached from it through the current guard, despite rollback appearing later in `VALID_STAGES`.
9. no candidate diff is created/applied; no version bump, deployment, metric observation, or rollback runs.

Classification: **governance contract scaffold with a stage-transition implementation**, not controlled autonomous self-evolution.

## 5. Safe target architecture (proposal only)

A future bounded engineering assistant should be a thin orchestrator over existing deterministic tools:

```text
human request
  -> read-only inventory/impact plan
  -> approval scope decision
  -> isolated workspace + temp stores
  -> reproduce failing contract
  -> small patch proposal
  -> affected tests + architecture/security/import gates
  -> human diff approval for governed scope
  -> commit/evidence artifact
  -> optional host validation
  -> monitoring
  -> executable rollback or human promotion
```

Hard boundaries:

- no live trading/wallet/order capability;
- no Lane-A edits without a separately named, explicit gate;
- no self-approval, merge, deployment, dependency update, schema migration, or data deletion;
- no external repository cloning during the current audit phase;
- no arbitrary shell/network by default;
- all state changes replayable, evidenced, and reversible;
- maximum patch/iteration/time/resource limits;
- failures remain visible; assertions and thresholds are not weakened for green status.

## 6. Priority

- **P0/P1:** fix import/store isolation and truthful status surfaces first. An agent built on contaminated state would automate false evidence.
- **P2:** persist/validate proposals and integrate read-only planning/test evidence only.
- **P3:** consider a sandboxed edit/repair loop after Windows/Docker/data foundations are proven.

Do not adopt a persona/multi-agent framework merely to fill this table. Fewer tools with enforceable contracts are a better fit than more “agents.”
