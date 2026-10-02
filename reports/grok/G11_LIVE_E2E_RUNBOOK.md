# G11 live Telegram E2E runbook (owner-run): @Sun_sniperbot + GM-04 gate

| Field | Value |
|---|---|
| Status | Live refusal path PASSED by the owner on 2026-10-02 (`reports/telegram_e2e/telegram_e2e_20261002T1221Z.md`). Phase 5 changed reply wording/formatting only (expected texts below updated). Phase 5: Grok restarted only the Telegram bot (see GROK_HANDOFF Phase 5). |
| Purpose | Prove live: Telegram → bot → Conversation Gateway → reply. GM-04 must refuse engine start/stop and paper_buy over chat, and casual "stop loss" text must never count as a command. |
| Mode | PAPER_ONLY. Live trading stays disabled. |
| Written | Grok, 2026-10-02 (Phase 4). Local commit only. |
| Self-test baseline | Offline only, not independent verification: npm `test:chat-control-gate` 126/126, pytest Telegram + canonical sets 271 passed / 1 xfailed, tsc 0 errors |

## 0. Current reality (observed 2026-10-02 ~15:25 Tehran)

**Gateway**
- `next dev --hostname 127.0.0.1 -p 3500` is running manually (node PIDs 14820/13120, started 04:39).
- It is listening on **127.0.0.1:3500**.

**`.env`**
- `.env` has `AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` (port 3000).
- Nothing listens on 3000. `scripts/gateway_port.py` diagnosis: `CONFIGURED_PORT_NO_LISTENER`.
- `.env` sets neither `AHOS_DATA_DIR` nor `AHOS_CONTROL_AUDIT_PATH`.

**Bot**
- **No `run_bot.py` process is running**, so nothing needs a restart.
- A fresh start picks up GM-02 (replay guard, hashed audit, user_id).

**How the bot reads its settings**
- `run_bot.py` loads `.env` with `setdefault`, so **a variable set in the bot's PowerShell session wins over `.env`**.
- `telegram_ai/service.py` reads **only `AHOS_GATEWAY_URL`**. It does not honour `AHOS_GATEWAY_PORT`.
- So the override is the session variable `AHOS_GATEWAY_URL`. `.env` is not edited.

**Gateway code reload**
- Next dev recompiles changed server modules (`chat.ts`, `chat_control_gate.ts`) on the next request. A restart is normally **not** needed.
- Step 2 checks this. If the old help text appears, restart the gateway (§5).

**Control audit file**
- Written by the gateway at `G:\robat\ahos\data\control_audit\chat_control_audit.jsonl`. `data/` is gitignored.

## 1. Before you start: record the engine state

Open the dashboard at http://127.0.0.1:3500 and note whether the engine is **running or stopped**. The test must leave this state **unchanged**.

## 2. Optional pre-flight probe without Telegram

Run in PowerShell window A from `G:\robat\ahos`. The token is read from `.env` into a variable and is never printed.

```powershell
cd G:\robat\ahos
Get-NetTCPConnection -State Listen -LocalPort 3500 | Select LocalAddress,LocalPort,OwningProcess
$tok = ((Select-String -Path .env -Pattern '^AHOS_WEB_API_TOKEN=').Line -split '=',2)[1].Trim().Trim('"')
$body = [Text.Encoding]::UTF8.GetBytes((@{ message = 'توقف'; channel = 'web' } | ConvertTo-Json))
(Invoke-RestMethod -Method Post -Uri http://127.0.0.1:3500/api/chat -Headers @{ Authorization = "Bearer $tok" } -ContentType 'application/json; charset=utf-8' -Body $body) | ConvertTo-Json -Depth 6
Remove-Variable tok
npm run audit:control-verify
```

Expected results:
- The reply contains «غیرفعال است» and «هیچ تغییری اعمال نشد».
- The intent is `stop`, with evidence `control.decision = REFUSED` and `reason = CHAT_PATH_CANNOT_PROVE_LOCAL_DASHBOARD`. The spoofed `channel:"web"` does not grant anything.
- `audit:control-verify` prints `CHAIN_OK` and `chat:stop:REFUSED: 1`.

This message is refused before any snapshot or DB access, so it has no side effects. If the reply instead says the engine stopped, the gateway is running old code: restart it (§5) before continuing.

## 3. Start the bot (PowerShell window B)

```powershell
cd G:\robat\ahos
$env:AHOS_GATEWAY_URL = "http://127.0.0.1:3500/api/chat"   # this session only; .env untouched
.venv\Scripts\python.exe scripts\gateway_port.py            # expect a listener on 3500 for the override URL
.venv\Scripts\python.exe scripts\gateway_port.py --env-file .env   # documents the .env reality (3000, no listener)
.venv\Scripts\python.exe run_bot.py --preflight
.venv\Scripts\python.exe run_bot.py
```

Expected: preflight is ✅, then «🤖 AHOS در حال گوش دادن است … برای توقف: Ctrl+C». Telegram goes through the `ALL_PROXY`/`HTTPS_PROXY` already in `.env`.

## 4. What to send from your allowlisted Telegram account to @Sun_sniperbot

| # | Send | Expected reply | Audit line? |
|---|---|---|---|
| 1 | `/start` | Help text «🤖 راهنمای AHOS» (bold in Telegram), including «روشن/خاموش کردن موتور و ثبت خرید کاغذی فقط از داشبورد محلی انجام می‌شود.» (Phase 5 wording, no internal ids) | no |
| 2 | `بازار چه خبر؟` | Normal market answer with the mandated footer | no |
| 3 | `stop loss چنده؟` | Normal answer. **Must NOT** stop the engine and must NOT be refused. | **no** |
| 4 | `stoploss` | Normal answer. Not a command. | **no** |
| 5 | `توقف` | Persian refusal: «⛔ کنترل موتور از طریق گفتگو غیرفعال است. … هیچ تغییری اعمال نشد.» | `chat:stop:REFUSED` |
| 6 | `/stop` | Same refusal | `chat:stop:REFUSED` |
| 7 | `شروع کن` | Same refusal (start) | `chat:start:REFUSED` |
| 8 | `خریدم PEPE` | Refusal: «⛔ ثبت خرید کاغذی از طریق گفتگو غیرفعال است. …» | `chat:paper_buy:REFUSED` |
| 9 | `توقف` again (resend the same text) | Refused again. The audit shows the same `message_sha256` as #5. | `chat:stop:REFUSED` |

About replays: the Telegram client cannot resend the same `update_id`. A true duplicate-update replay is covered offline by the GM-02 ReplayGuard tests. Step 9 shows that a repeated text never becomes a grant.

After sending, check the dashboard: the engine state must equal what you recorded in §1.

## 5. Evidence to capture

Run in window A:

```powershell
cd G:\robat\ahos
npm run audit:control-verify
Get-Content data\control_audit\chat_control_audit.jsonl -Tail 10
Select-String -Path data\control_audit\chat_control_audit.jsonl -Pattern 'stop loss|PEPE|توقف'
```

Check that:
- `audit:control-verify` shows `CHAIN_OK` with `chat:stop:REFUSED` ≥ 3, `chat:start:REFUSED` ≥ 1 and `chat:paper_buy:REFUSED` ≥ 1.
- The tail lines contain only hashes and lengths: no raw text and no raw ids.
- The `Select-String` for raw text finds **no matches**.

Also capture:
- **Gateway console (window running `next dev`):** the `POST /api/chat 200` lines for each message, and any compile output after the reload.
- **Bot console (window B):** startup lines and any errors.
- **Telegram:** screenshots of messages #1–#9 and their replies.
- **Dashboard:** the engine state before and after.

Then archive the evidence in `reports/telegram_e2e_<UTC-timestamp>.md`. Include the `audit:control-verify` JSON, the screenshots or transcript, and the before/after engine state. Label it as the owner's live run.

## 6. Stop and clean up

- Bot: press **Ctrl+C** in window B, then `Remove-Item Env:AHOS_GATEWAY_URL`. The override only lived in that session.
- Gateway: leave it running as before, or stop it with Ctrl+C in its own window.
  - To restart: `cd G:\robat\ahos; npm run dev -- -p 3500` (the `dev` script already binds 127.0.0.1).
  - Restart only if step 2 or message #1 showed old behaviour.
- `.env`, the DB and the engine state are untouched by this runbook. Control refusals happen before any DB access. Normal questions (#2–#4) go through the usual chat path.

## 7. Pass / fail

**PASS** requires all of:
- #1–#4 answered normally.
- #3/#4 not refused, and the engine was not stopped.
- #5–#9 refused in Persian.
- The audit chain is OK, with the expected counts and no raw text.
- The engine state is unchanged.

**FAIL** means anything else. Report the failing step with its gateway and bot console output. **Rollback:** `git revert <GM-04 commit>`, which leaves the audit file in place.

Self-tests are not independent verification. GM-04 stays pending independent review by سپهر, قاسم and رضا.
