# AHOS — OPERATIONS RUNBOOK (P3 activation guide)
# Every step has a success check. Do not skip. Blocking steps marked ■.

## Step 1 — VPS provision (■ user action)
Oracle Free Tier / Hetzner-class, 1 OCPU+, EU region. Success check: `docker --version` works.

## Step 2 — Deploy engine stack
```bash
git clone <ahos repo> && cd ahos/deployment
cp ../config/.env.template ../config/.env   # fill values (Step 3 first)
docker compose up -d
```
Success: `docker ps` shows ahos_postgres (healthy) + ahos_n8n (running);
`psql -h localhost -U ahos_app -d ahos -c '\dt'` lists 8 tables (schema auto-loaded).

## Step 3 — Credentials (■ user action, order matters)
1. @BotFather → /revoke old token → /newbot (or reuse) → put NEW token in .env
2. Message the new bot `/start` from your account → visit
   `https://api.telegram.org/bot<TOKEN>/getUpdates` → copy YOUR numeric chat id → .env
3. Create exchange TRADE-ONLY key (no withdrawal) → .env
4. In n8n UI: create Telegram + Postgres credentials (they replace `__ASSIGN_AFTER_IMPORT__`).
Success: `docker compose logs n8n` shows no auth errors; bot replies to /start.

## Step 4 — Import workflows (LIVE-VERIFIED 2026-08-11 on n8n 2.8.4 — 6/6 import PASS, R-11)
n8n UI → Import from File → the 6 JSONs (01/02/03 control, 10/11/12 research).
For each: open, confirm node parameter mapping, assign credentials, SAVE, then activate (publish).
Success: workflows list + activate; no unknown-node warnings (12/12 types resolve — see note).
■ n8n v2 REQUIRED SETTING: add `NODES_EXCLUDE=[]` to the n8n container env (workflows 10/11/12 use the
Execute Command node, which n8n v2 disables by default — verified live; ISSUE_REGISTER R-10). Alternatively
skip workflows 10/11/12 (control workflows 01/02/03 do not need it).
■ Activation PRECONDITION: Postgres + Telegram credentials must be assigned first — activation otherwise
fails with WorkflowValidationError naming the exact credential-gated nodes (verified live, expected by design).

## Step 5 — First paper cycle verification (live validation, real)
- Wait for next hour tick (or Execute Workflow manually for 01 then 02).
- Check: market_data rows increased; trade_decisions has PAPER rows OR audit NO_TRADE rows;
  Telegram received signal/status message; agent_audit_trail has DATA_INGEST + SIGNAL_EVAL.
- Run workflow 03: /status from your chat → JSON status reply. /kill → halt flag; then
  confirm workflow 02 next cycle emits kill_switch_active NO_TRADE (kill verification!).
- De-kill: delete the KILL_SWITCH row (documented SQL below) and verify signals resume.
```sql
DELETE FROM agent_audit_trail WHERE action='KILL_SWITCH' AND result='ALL_TRADING_HALTED';
```

## Step 6 — Two-week paper phase
Daily: /status review. Weekly: run engine/run_validation.py on fresh dumps; compare paper
PnL vs backtest (variance <15% required — current baseline will FAIL this; that's expected
and is why strategy rebuild precedes any live thought).

## Step 7 — Backups & hygiene
crontab: `0 3 * * * pg_dump ... | gzip > /backups/ahos_$(date +\%F).sql.gz` (7-day retention).
Quarterly: rotate n8n basic-auth password; re-run full CI gate.

## Failure playbook
| Symptom | First check | Then |
|---|---|---|
| No hourly rows | compose logs n8n → workflow 01 last execution | exchange reachable? Alert path fired? |
| Integrity alert telegram | defects list in message | quarantine symbol; notify Agent-09 |
| Bot silent | token rotated? chat id correct? | getUpdates; check polling log |
| Signals stopped | KILL flag row present? | clear only after review (SQL above) |
| Postgres down | docker ps → volume intact | compose up -d; data persists |
