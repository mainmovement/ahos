# MISSION DISCOVERY — 2026-10-02 (Grok, Phase 1)

Inputs: GROK_SESSION_2026-10-02_REALITY_INSPECTION.md, TELEGRAM_REALITY_MAP.md, DOCKER_N8N_DEPENDENCY_MAP.md, DASHBOARD_ONECLICK_REALITY.md, Claude's `reports/mission_ledger_20261002.json`, M0 delta, AGENTS.md.
No new agents are proposed. No mission touches Lane A, Canonical Decision Authority internals, security gate logic, Credential Manager boundary, Trusted Command Boundary, execution permission ladder, or `.cursor/hooks*`.

## 1. Capability ladder (VISION/DESIGN/PLANNED/PARTIAL/IMPLEMENTED/TESTED/VERIFIED/OPERATIONAL/BLOCKED/UNKNOWN/CONTRADICTED)

| Capability | Ladder | Basis |
|---|---|---|
| Lane A freeze | VERIFIED | freeze check OK (36) |
| Canonical Decision Authority | VERIFIED (code+tests), not OPERATIONAL-proven in soak | TS selftests, no diff |
| Security overlay | TESTED/VERIFIED | canonical-security 19/19 incl. live Python adapter |
| PAPER_ONLY | VERIFIED | pins + zero positions |
| Control plane / Agent A orchestration | DESIGN (FUTURE_NON_AUTHORITY_ROOT) | tests2b asserts not implemented |
| Agent taxonomy (4 coexisting) | VERIFIED as RECONCILED map, not merged | M2 + test |
| Lifecycle (prediction/observation) | IMPLEMENTED/TESTED; honesty bug | `architecture/learning/prediction_lifecycle.py:326` hard-codes `eligible_join_pairs_estimate=0` (Claude finding; real join 6,037) → CONTRADICTED census field |
| Verification (independent) | PARTIAL | tests + human review; no automated independent verifier |
| Mission ledger / checkpoint | PARTIAL | `scripts/execution_state.py` (M5, append-only, VERIFIED/DEGRADED/NOT_VERIFIED); mission ledgers are ad-hoc untracked JSON (`reports/mission_ledger_20261002.json`); no shared multi-agent handoff schema |
| AI provider abstraction | PARTIAL | TS `types.ts:2-12` has RATE_LIMITED/NO_KEY/AUTH_FAILED (no QUOTA_EXHAUSTED); Python `architecture/providers/contracts.py:96` only OK/DOWN/RATE_LIMITED/ERROR |
| Credential Manager abstraction | DESIGN / NOT_IMPLEMENTED | only negative boundary test |
| Telegram edge | IMPLEMENTED/TESTED (unit); integration PARTIAL; live OWNER_ACTION | 150 pass |
| Telegram capability/identity/audit | PARTIAL/MISSING | user_id "", no capability gate, no audit |
| n8n | IMPLEMENTED as JSON only; not OPERATIONAL; AHOS-03 REJECTED | 0 imported |
| Docker runtime container | OPERATIONAL but unhealthy (stale config) | docker inspect |
| Postgres | OPERATIONAL | pg_isready |
| Gateway | OPERATIONAL on 3500 (manual) / config CONTRADICTED (.env 3000) | LISTEN + .env:99 |
| Dashboard truthfulness | PARTIAL (stale-READY risk) | CommandCenter.tsx:304-306 |
| Nightly backups | PARTIAL (1/7), no scheduler | series json, no task |
| Doc-drift gate on clean checkout | CONTRADICTED (passes only with untracked file) | doc_drift.py:100-104 + untracked artifact |
| Calibration sufficiency | BLOCKED/NOT proven | NOT_MONOTONIC |
| Soak 7 nights / T+72h | WALL_CLOCK_BLOCKED | T0 02:54:19Z |
| G11 Telegram live | OWNER_ACTION_REQUIRED | |
| Research-host isolation | PARTIAL | M1 tests; no Windows process-isolation proof |

## 2. Prioritised missions

### GM-01 — Doc-drift clean-checkout regression (from 25b33cc)
- Objective: make `tests/test_doc_drift.py` green on a clean checkout, not only on this laptop.
- Why now: 25b33cc made the canonical-doc ref depend on the untracked `reports/nightly_backup_series.json`; any CI/fresh clone will fail `test_canonical_docs_have_zero_real_stale_refs`.
- Dependency: Claude's decision — either commit the evidence artifact (it is Claude's untracked file) or restore an INTENTIONAL_REFS-style exemption with "exists-but-untracked" semantics.
- Risk: low; touches only scripts/doc_drift.py/tests or adds one evidence file.
- Authority: Claude (owner of 25b33cc) or Grok with Claude's ack. Not governance-gated.
- Expected files: `reports/nightly_backup_series.json` (add) OR `scripts/doc_drift.py`, `tests/test_doc_drift.py`.
- Runtime impact: none. Tests: `pytest tests/test_doc_drift.py`; verification by running doc_drift against `git archive HEAD` extracted to a temp dir.
- Evidence: `reports/grok/GM01_doc_drift_clean_checkout.json`. Rollback: revert the single commit.
- Status: IMPLEMENTED_UNVERIFIED regression (STRONGLY INDICATED). Next: GM-02.

### GM-02 — Telegram no-credential hardening + fake-transport integration harness (tests first)
- Objective: add an offline harness (MockTelegramAdapter → TelegramBotRunner → TelegramDomainService → stub HTTP gateway) asserting envelope, sender identity propagation, fail-closed auth, rate-limit, replay dedupe, offline fallback, footer; then (separate step) forward `chat_id/user_id`, add runner-level update_id dedupe, append-only audit JSONL with hashed ids.
- Why now: the only remaining Telegram gate (G11) is owner-gated; everything else can be proven without credentials, and the authority check found sender identity missing and no audit.
- Dependency: none (no token, no network). Risk: low for tests; medium for code changes in `telegram_ai/` (edge only).
- Authority: Lane B edge code; no authority surfaces. Capability gating of `start/stop/paper_buy` for `channel=telegram` in `chat.ts` touches the paper path → **design note + review first** (GM-04).
- Files: `tests/test_telegram_integration_harness.py` (new), later `telegram_ai/bot.py`, `telegram_ai/service.py`, `telegram_ai/audit.py` (new).
- Runtime impact: none until bot restarted by owner. Tests: new harness + existing 150. Evidence: `reports/grok/GM02_telegram_harness_<utc>.json`. Rollback: revert commit.
- Status: IMPLEMENTED_VERIFIED offline (self-tests, Phase 2 Grok commit; 203 passed/1 xfailed). Live E2E LIVE_E2E_UNVERIFIED / OWNER_ACTION_REQUIRED. Note: implemented as `telegram_ai/envelope.py` + `tests/test_telegram_offline_harness.py` (not audit.py / integration_harness names). Next: GM-03.

### GM-03 — Dashboard truthfulness (stale-READY)
- Objective: when a poll fails after a successful load, mark the whole view STALE (age + red banner, run pill neutral); add freshness thresholds to health dims; render policy dims as POLICY not OK.
- Why now: a dead gateway currently leaves green "OK"/running visible.
- Dependency: none. Risk: low (presentation only; must not create authority — AGENTS.md TS rule).
- Authority: TS presentation surface. Files: `CommandCenter.tsx`, `snapshot.ts` (dim status only), selftest (new `scripts/dashboard_staleness_selftest.ts` + npm script).
- Runtime impact: Next dev hot-reload only. Tests: new selftest + `npm run typecheck` + existing canonical selftests. Evidence: `reports/grok/GM03_dashboard_staleness.json`. Rollback: revert.
- Status: IMPLEMENTED_VERIFIED (self-tests; presentation only; implemented as `dashboard_truth.ts` + `scripts/dashboard_truth_selftest.ts` / `npm run test:dashboard-truth`). Next: GM-05.

### GM-04 — Telegram/chat operational-control capability gate (design → review → implement)
- Objective: free-text Telegram messages must not start/stop the engine or open paper positions without an explicit capability (admin principal + confirmation), with audit.
- Why: `chat.ts:233-234` regex start/stop → `startEngine/stopEngine`; paper_buy reachable (gated by canonical+overlay, PAPER only).
- Authority: touches TS route behaviour for the paper path → requires independent security review. Status: IMPLEMENTED/TESTED (self-tests only; conservative capability-reducing form) — PENDING INDEPENDENT REVIEW (سپهر/قاسم/رضا). `/api/chat` refuses start/stop/paper_buy for every channel (client `channel` never a grant); whole-message command matching ("stop loss"/"stoploss"/"start-up" never match); hash-chained audit with hashed ids at `data/control_audit/chat_control_audit.jsonl`; dashboard buttons (`/api/engine`, `/api/paper`) unchanged; dashboard chat control now refused (documented). Live E2E OWNER_ACTION_REQUIRED via `reports/grok/G11_LIVE_E2E_RUNBOOK.md`. Local commit only (pushes paused).

### GM-05 — Port single-source + non-mutating gateway preflight
- Objective: introduce one source for gateway port/URL used by launchers and gate, plus a read-only preflight that reports "configured URL has no listener; AHOS gateway detected on :NNNN".
- Why: `.env:99` (3000) vs running 3500; ~40 refs on 3000; Claude bypassed main() to get G2.
- Authority: script change OK; choosing 3000 vs 3500 and editing `.env` = **OWNER_ACTION**. Do NOT blind-replace 3000→3500.
- Files: `scripts/operator_validation_gate.py`, `scripts/windows_run_operator_gate.ps1`, tests. Status: IMPLEMENTED_VERIFIED (self-tests; `scripts/gateway_port.py`; default 3000 kept, env override honoured, .env untouched). Real diagnosis: CONFIGURED_PORT_NO_LISTENER, listener on 3500. Canonical port choice = OWNER_ACTION_REQUIRED. Next: GM-06.

### GM-06 — Quarantine n8n AHOS-03 + validator rules
- Objective: mark `ahos_03_telegram_control.json` quarantined; extend `tests/validate_n8n.py` to reject interpolated SQL, DELETE on audit tables, and `trade_decisions.execution_status` mutation.
- Why: dormant now (0 imported) but target tables exist; import would bypass canonical authority, allow SQL injection, delete audit.
- Authority: governance-visible but non-runtime; changing workflow JSON content may need owner sign-off → start with validator test (failing → xfail with reason) + report. Status: IMPLEMENTED_VERIFIED (static self-tests). ahos_03 QUARANTINED via `QUARANTINED_WORKFLOWS` in `tests/validate_n8n.py` + `reports/grok/GM06_N8N_QUARANTINE.md`; file kept; G12 unchanged. Lifting quarantine = rewrite + security review. Next: GM-04 review.

### GM-07 — prediction_lifecycle census honesty fix
- Objective: compute (or label UNKNOWN) `eligible_join_pairs_estimate` instead of hard-coded 0 (`architecture/learning/prediction_lifecycle.py:326`). Lane B, not frozen.
- Authority: Claude proposed for human review → OWNER_ACTION_REQUIRED (approval), then executable. Must not imply calibration sufficiency.

### GM-08 — Mission ledger / multi-agent handoff schema
- Objective: one append-only schema for Claude+Grok mission/handoff records (extend M5 `execution_state.py` vocabulary; no authority fields), with a test.
- Why: today ledgers are ad-hoc untracked JSON; two agents share one tree. Status: IMPLEMENTED_VERIFIED (self-tests; ladder IMPLEMENTED+TESTED, not INTEGRATED): `architecture/mission/ledger.py` + `scripts/mission_ledger.py`; append-only hash-chained JSONL, checkpoint/resume, secret redaction, not an authority. Local commit only (pushes paused by owner).

### GM-09 — Provider abstraction states
- Objective: add QUOTA_EXHAUSTED (and AUTH_FAILED parity) to Python `architecture/providers/contracts.py` and TS `types.ts`, with mapping tests (HTTP 402/429-quota vs 401/403). Status: IMPLEMENTED_VERIFIED (offline self-tests; ladder IMPLEMENTED+TESTED, not INTEGRATED): `architecture/ai/{provider_status,credential_store,mission_guard}.py`; credential store interface only; Windows Credential Manager backend DESIGN_ONLY (GM-12 review). Local commit only (pushes paused).

### GM-10 — Docker decoupling / single runtime owner (design)
- Objective: decide container vs native daemon as the single SQLite writer; design native Postgres or SQLite-Drizzle option; replace n8n schedules with the Python scheduler. DESIGN_ONLY; any container recreate/stop = OWNER_ACTION.

### GM-11 — Control plane (Agent A) foundation
- DESIGN only; AGENT_ONE_STATUS = FUTURE_NON_AUTHORITY_ROOT; governance request required. NOT executable in this session.

### GM-12 — Credential Manager abstraction
- DESIGN only (Windows Credential Manager behind an interface; env fallback); boundary-sensitive → owner + security review. NOT executable now.

### P3-M1 — tsconfig excludes docs/archive
- Status: IMPLEMENTED_VERIFIED (self-tests): `tsc --noEmit` 0 errors (was 9, all archive); file list diff = exactly 7 archive files.

### Gated / not selectable
| Item | Status |
|---|---|
| G11 Telegram live E2E | OWNER_ACTION_REQUIRED |
| Soak nights 2–7, T+72h outcome labels (≥ 2026-10-05T02:54Z) | WALL_CLOCK_BLOCKED |
| Nightly backup scheduled task creation | OWNER_ACTION_REQUIRED (system mutation) |
| Recreate `ahos_runtime_win` (healthcheck/port drift) | OWNER_ACTION_REQUIRED (service restart) |
| Gateway port decision / `.env:99` edit | OWNER_ACTION_REQUIRED |
| Calibration sufficiency | BLOCKED (NOT proven — never CLOSED) |
| Legacy exited containers cleanup | OWNER_ACTION_REQUIRED (deletion) |
| Fresh-host restore drill | OWNER_ACTION_REQUIRED |

## 3. Recommended first executable missions
1. **GM-01** (tiny, fixes a real CI regression from today's push; coordinate with Claude since it is Claude's commit/artifact).
2. **GM-02** (Telegram offline harness — tests only first; highest value toward G11 readiness with zero credentials, zero runtime impact).
3. **GM-03** (dashboard stale-READY fix — presentation only, removes a misleading-health risk).
Then GM-05 (port preflight, after owner states the canonical port) and GM-06 (n8n validator rules).
