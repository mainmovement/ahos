# AHOS — FINAL TEST REPORT (Agent-09 QA / Agent-07 LeadEng) — 2026-08-10
# Environment note: sandbox has no n8n runtime/Postgres → live-instance tests are replaced by
# (a) structural workflow validation, (b) logic-equivalent dry-run simulation, (c) pytest unit/integration.
# This substitution is recorded honestly and is listed as a pre-production runbook step.

## 1. pytest suite — 11/11 PASS (2.7s)
| Test | Verifies |
|---|---|
| test_risk_sizing_2pct | 2% equity risk → correct notional |
| test_leverage_cap_binds | 2x leverage hard cap engages |
| test_zero_guards | zero/negative inputs → 0 (no crash/no trade) |
| test_leverage_ladder | micro 2x / strong 10x / default 5x |
| test_no_lookahead_indicators | indicator at row k == computed on data[0..k] (3 checkpoints ×3 indicators) |
| test_spec_frozen_constants | engine constants == frozen spec (tamper alarm) |
| test_backtest_executes_and_records | engine runs end-to-end, full metric set |
| test_walk_forward_window_count | 4 WF windows on 83d dataset (structural) |
| test_monte_carlo_deterministic_seeded | seeded MC fully reproducible |
| test_n8n_workflows_valid | all 3 workflows structurally valid |
| test_live_gate_closed_on_current_evidence | gate math holds: PF<1.3 → CLOSED |

## 2. Workflow dry-run scenarios — 9/9 PASS (reports/dryrun_log.json)
S1 normal paper cycle on real BTC data → valid decision object emitted (NO_TRADE this hour).
S2 exchange fetch failure → error output → alert path; cycle halted, no partial ingest.
S3 injected integrity defect (close>high) → detected, UPSERT skipped, quarantine path.
S4 kill-switch flag set → signal suppressed ("kill_switch_active").
S5 unauthorized /kill from wrong chat_id → rejected + AUTH_FAIL audit.
S6 admin /kill and /approve <sym> → correct handlers invoked.
S7 risk caps → sizing 100/200/0 as designed.
S8 parameter change without approvals → stays PENDING; rollback path mandatory.
S9 leverage ladder → 2x/10x/5x correct.

## 3. n8n structural validation — 3/3 PASS (tests/validate_n8n.py)
JSON parse, unique ids/names, connection endpoints exist, all enabled nodes reachable
from triggers, no secrets, credentials placeholders only, error branches wired.

## 3b. Telegram protocol harness (directive §10/§11) — 11/11 PASS, SIMULATED (2026-08-10)
tests: connectivity(getMe/getUpdates/chat-id), system message "AHOS SYSTEM ONLINE" (timestamp+mode+agent
inventory), command matrix authorized×6 + unauthorized /kill → Reject+AUTH_FAIL, bidirectional integration
chain (outbound send + inbound command→audit rows +2). Evidence: reports/telegram_test_log.json.
REAL-mode rerun is a documented 3-step operation (docs/TELEGRAM_TEST_PROCEDURE.md) awaiting token rotation.

## 3c. Takeover-wave regression fixes verified
- DD-cap permanent stop: enforcement proved before/after (MaxDD 57–59% → 20.4–21.7%; PF conclusion unchanged: NO EDGE)
- W1 batch loop-back; W3 auth-first routing + new commands; W2 activation boot message — validator re-run 3/3 PASS
- pytest re-run after engine change: 11/11 PASS; CI gate now 5 stages (adds telegram harness --simulate)

## 4. NOT executed in this environment (declared — runbook compensates)
- Real n8n import + end-to-end run (needs n8n instance + Postgres) → RUNBOOK step 4.
- REAL Telegram delivery (needs rotated token + chat id) → TELEGRAM_TEST_PROCEDURE (blocked by user action).
- True exchange order round-trip — disabled by design until all gates pass (never in this delivery).
- 3-year OOS/WF/MC — impossible until 3yr dataset acquired (top open item).
- docker compose boot of database (no docker daemon in sandbox) → RUNBOOK step 2.

## 5. Regression rule (continuous)
Any code/strategy change must re-run: data audit → pytest → dry-run → workflow validation.
All four must be green before Agent-10 review. CI script: engine/run_all_checks.sh

## 6. ADDENDUM 2026-08-11 — n8n LIVE smoke test (was section-4 "not executed"; now executed)
Real n8n 2.8.4 runtime (npm, node v20.20.2, sqlite, 127.0.0.1:5678) booted in sandbox:
- RUNTIME: healthz ok; migrations green; Task Broker up.
- IMPORT: CLI `n8n import:workflow` → 6/6 exit=0; `list:workflow` + REST confirm all six persisted across restart.
- NODE-TYPE AUDIT (live registry, authenticated /types/nodes.json): 811 types default; executeCommand MISSING
  by default on v2 (security breaking change) → with NODES_EXCLUDE=[] 814 types, 12/12 workflow types resolve.
- ACTIVATION GATE: W01 activate → 400 WorkflowValidationError (exactly the 2 postgres-credential nodes) —
  engine-level validation of our files confirmed; placeholders work as designed.
- EXECUTION: PENDING — requires Postgres + TELEGRAM_BOT_TOKEN env (user blockers ①②), per directive step wording.
Full transcript: reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt. Issue entries: AHOS_ISSUE_REGISTER R-10 / R-11.
Telegram tests remain SIMULATED (11/11) — REAL rerun awaits token rotation (docs/TELEGRAM_TEST_PROCEDURE.md).
