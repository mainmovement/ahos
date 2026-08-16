# AHOS — TELEGRAM TEMPORARY TEST PROCEDURE (Directive §10/§11)
# Scope: TEMPORARY integration testing only (connectivity/commands/audit chain).
# Bot: Sun_sniperbot (temporary). NOT production deployment.

## 0. Token hygiene (binding)
- Token exists ONLY in `TELEGRAM_BOT_TOKEN` environment variable. Never in files/git/logs/JSON.
- This package's workflows reference credentials by placeholder `__ASSIGN_AFTER_IMPORT__` only.
- After a successful test cycle: revoke temporary token (@BotFather /revoke), create production bot,
  move to secure env, update n8n credential, remove temporary references. Production without rotation = PROHIBITED.

## 1. Test 1 — Connectivity (operator steps)
1. `export TELEGRAM_BOT_TOKEN=<temporary>` `export TELEGRAM_ADMIN_CHAT_ID=<yours>`
2. `python3 engine/telegram_live_test.py` (no --simulate)
3. In Telegram: send `/start` to Sun_sniperbot.
4. Pass criteria: harness getMe PASS; /start receives command list; chat id captured
   (or fetch it via `getUpdates` and export before rerun). All rows land in reports/telegram_test_log.json.

## 2. Test 2 — System message
Harness sends exactly: "AHOS SYSTEM ONLINE" + timestamp + mode + agent inventory.
Import n8n workflow 02 afterwards: on workflow ACTIVATION, node "Workflow Activated" sends the
same boot frame end-to-end (n8n → Agent-05 → Telegram → user phone).

## 3. Test 3 — Command matrix
| Command | Authorized (your id) | Unauthorized (anyone else) |
|---|---|---|
| /start /status /health /agents /report /risk /signals | handler runs + audit | works (read-only) but still logged |
| /kill /emergency_stop /reset /approve /reject | executes + audit | REJECTED + AUTH_FAIL audit row |
Harness covers: all 6 protocol commands × auth paths; n8n workflow 03 enforces identically in live mode.

## 4. Test 4 — Integration chain
A) n8n → Agent-05 → Telegram → user phone (boot/signal messages)
B) Telegram command → n8n workflow 03 → Postgres `agent_audit_trail` (row per command)
Pass criteria: both directions produce artifacts (message on phone + audit row).

## 5. Post-test mandatory shutdown (temporary env teardown)
1. @BotFather → /revoke (old Sun_sniperbot token is already exposed → revoke NOW, before any production)
2. New production bot → new token → `.env` only
3. n8n: replace credential, re-run Tests 1–4 once on production bot
4. Record rotation time in agent_audit_trail via workflow 03 /status ping
