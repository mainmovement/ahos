# AHOS — SECURITY CHECKLIST FINAL (Agent-04) — 2026-08-10
# ✔ = verified by automation this session · ☐ = user action / pre-production gate

## Secrets & credentials
- ✔ No token/key in any delivered file (regex-scanned in CI: validate_n8n.py step)
- ✔ .env.template only; .env gitignored; n8n credentials referenced by placeholder
- ☐ BLOCKING: revoke old Sun_sniper bot token (@BotFather /revoke) → issue NEW bot → set TELEGRAM_BOT_TOKEN
- ☐ BLOCKING: set TELEGRAM_ADMIN_CHAT_ID (run /start to the NEW bot, read numeric id)
- ☐ Exchange API key: create TRADE-ONLY key (no withdrawal), IP-whitelist if supported
- ✔ n8n: basic auth + N8N_ENCRYPTION_KEY + port bound to 127.0.0.1 behind reverse proxy

## Access control
- ✔ Telegram bot refuses to start without ADMIN_CHAT_ID; HIGH-risk commands admin-gated; attempts audited
- ✔ Workflow-03 auth guard precedes every handler; unauthorized → reject + AUTH_FAIL audit
- ✔ Postgres app user ≠ superuser (provision in runbook; least privilege on 8 tables)

## Trading safety
- ✔ AHOS_MODE defaults PAPER; LIVE requires env change + Agent-10 + human gate
- ✔ LIVE Execution node shipped DISABLED; enabling requires the full gate checklist
- ✔ Kill switch: 3 independent enforcement points; verified in dry-run S4/S6
- ✔ Risk caps pinned by unit tests (2% risk, 2x micro leverage, daily halt, DD stop)

## Data & integrity
- ✔ Ingest integrity gate blocks defective rows before DB write (dry-run S3)
- ✔ UPSERT dedupe key (symbol,timeframe,ts,source); removed-row registry maintained
- ✔ No interpolation anywhere (rule enforced by design; audited in data_audit.py gates)

## Auditability
- ✔ Every decision/command/param-change writes to audit tables (trade_decisions/agent_audit_trail/telegram_audit/model_parameter_history)
- ✔ Parameter change requires rollback_script_path + dual approval before apply (dry-run S8)
- ☐ Enable Telegram-offsite backup of nightly pg_dump (encrypted) — runbook step 7

## Residual risks (declared)
- LBank jurisdiction/KYC risk for Iranian users — mitigated by exchange-agnostic config swap (documented in plan)
- Phone-controller dependency: if F3 offline, VPS engine continues; alerts missed — acceptable (recorded)
- SQL filter typeValidation "loose" in n8n IF/Switch nodes — chosen for import compatibility; validated structurally
