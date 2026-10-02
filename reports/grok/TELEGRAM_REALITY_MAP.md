# TELEGRAM REALITY MAP — 2026-10-02 (Grok, read-only)

Doctrine (AGENTS.md / DOC_TRUTH_MAP C): Telegram is an **interaction edge**, a gateway client only (W57). It must not score, decide, or invent a second brain. Dashboard/Telegram/Grok/Claude are NOT decision authority.

## 1. Where it lives

| Layer | Path | Role |
|---|---|---|
| Launcher | `run_bot.py` | `--preflight`, `--console` (no network), long-poll; loads `.env`; persists offset in `data/telegram_offset.json` (advanced BEFORE handling, line 235-238) |
| Adapter + gate | `telegram_ai/adapter.py` (253 l) | `TelegramUpdate`, `TelegramSecurityGate` (allowlist chat ids + admin user ids; empty allowlist FAIL-CLOSED unless `AHOS_TELEGRAM_ALLOW_OPEN_ACCESS`; rate limit), `TelegramBotAdapterInterface`, `MockTelegramAdapter` (fake transport), `ProductionTelegramAdapter` (token scrub `_scrub`, proxy transport via `ALL_PROXY`/`HTTPS_PROXY`) |
| Runner | `telegram_ai/bot.py` (80 l) | authorize → rate-limit → map `/start` `/help` `/top` `/market` to text → `TelegramDomainService.handle_message` → send (parse_mode=None) |
| Domain service | `telegram_ai/service.py` (108 l) | POST to `AHOS_GATEWAY_URL` with `channel:"telegram"` + optional `Authorization: Bearer $AHOS_WEB_API_TOKEN`; else `EMERGENCY_FALLBACK_ONLY`; `_route` raises `W57_BRAIN_LOCKDOWN` |
| Outbound alerts (Python) | `telegram_ai/pump_alert.py` | `push_telegram_alert` → all `TELEGRAM_ALLOWED_CHAT_IDS`; cooldown state `reports/pump_alert_state.json` |
| Outbound alerts (TS) | `alerts.ts`, `engine.ts:377` | OPPORTUNITY alert requires Python `alerts_allowed` (BUY) AND overlay PASS |
| Other | `telegram_ai/intent.py`, `positions.py` (ledger `log_buy`), `response_contract.py` (FOOTER_MANDATED), `providers.py`, `alerts.py` | `positions.log_buy` imported by service but NOT reachable from `handle_message` |
| Live test / helpers | `engine/telegram_live_test.py`, `scripts/windows_g11_telegram_e2e_helper.ps1`, `scripts/windows_telegram_send_gate_paste.ps1` | owner-driven |
| n8n edge | `n8n/workflows/ahos_03_telegram_control.json` | see §5 (dormant, dangerous) |
| Docs | `docs/canonical/TELEGRAM.md`, `docs/TELEGRAM_OPERATOR_E2E_PROTOCOL.md`, `docs/TELEGRAM_TEST_PROCEDURE.md`, `docs/engineering/TELEGRAM_HTML_ESCAPE.md` | |

## 2. Credential consumption (names only)
- `TELEGRAM_BOT_TOKEN` (env, loaded from `.env` by `run_bot.py::load_dotenv` and by operator scripts). **CREDENTIAL_PRESENT_BUT_REDACTED** in `.env` (gitignored, `git check-ignore` rc=0).
- `TELEGRAM_ALLOWED_CHAT_IDS`, `TELEGRAM_ADMIN_USER_IDS`, `TELEGRAM_ADMIN_CHAT_ID` (n8n), `AHOS_TELEGRAM_ALLOW_OPEN_ACCESS`, `AHOS_WEB_API_TOKEN`, `AHOS_GATEWAY_URL`, `ALL_PROXY`/`HTTPS_PROXY`.
- **No Credential Manager abstraction exists** (only a negative boundary test `tests2b/test_boundaries_windows.py:66-71` asserting Slice-2B never touches keyring/env). Status: DESIGN_ONLY / NOT_IMPLEMENTED.

## 3. Leak scan (values never printed)
- Pattern `\b\d{8,10}:[A-Za-z0-9_-]{35}\b`.
- Tracked tree at HEAD: 1 hit — `tests/test_engine_import_safety.py:101` — **synthetic fixture** (numeric part is a single repeated digit; does not equal the `.env` token). Not a leak.
- Untracked files + `reports/`, `logs/`, `data/` *.log/*.txt/*.json/*.md (<20 MB): **0 hits**.
- Not scanned: full git history (`git log -p`), binary/SQLite stores, node_modules. Recommend a history scan as a follow-up (read-only).

## 4. Authority-leak check

| Path | Can Telegram reach it? | Gate | Verdict |
|---|---|---|---|
| Canonical decision (`architecture/decision/authority.py`) | No write path; reads via read model only | — | NO LEAK |
| Live trade / wallet / order | No code path found | PAPER_ONLY pins | NO LEAK |
| `chat.ts` intent `paper_buy` → `engine.addPaper` (paper position OPEN) | **Yes**, via gateway `/api/chat` (`chat.ts:94-125`, regex `chat.ts:236`) | `paperAllowedFromCanonical` (Python BUY) + overlay PASS (`engine.ts:781-794`, `PaperSecurityDenied`) | Gated, PAPER only — acceptable per AGENTS.md, but no per-channel capability check |
| `chat.ts` intents `start` / `stop` → `startEngine()` / `stopEngine()` (`chat.ts:43-48`, regex `chat.ts:233-234`) | **Yes** | only gateway bearer token + Telegram allowlist | **OPERATIONAL-CONTROL LEAK (MEDIUM)**: a free-text Persian/English message containing a stop-word can halt the observation engine; no confirmation, no capability check, no audit record tied to sender |
| `watch_add` → `addWatch` (`chat.ts:78-83`) | Yes | none beyond auth | low (watchlist only) |
| Sender identity | `bot.py` passes ctx without `user_id`; `service.py:84` sends `user_id: ""` | — | gateway cannot attribute Telegram actions to a principal |
| Replay | offset persisted (run_bot) but runner has no `update_id` dedupe; `MockTelegramAdapter` assigns ids sequentially | — | PARTIAL |
| Audit | no Telegram-command audit trail in Python path | — | MISSING |

## 5. n8n AHOS-03 "Telegram Control + Kill Switch" (file only; **0 workflows imported** in live n8n DB)
Static findings in `n8n/workflows/ahos_03_telegram_control.json`:
- `/approve <sym>` / `/reject <sym>` → `UPDATE trade_decisions SET execution_status='PAPER'|'REJECTED' WHERE symbol = upper('{{arg}}')` — **bypasses Canonical Decision Authority** and **string-interpolates user input into SQL (injection)**.
- `/reset` → `DELETE FROM agent_audit_trail WHERE action='KILL_SWITCH' …` — **deletes audit evidence**.
- Kill switch is an audit-row flag, not an independent kill.
- Target tables `trade_decisions`, `agent_audit_trail`, `agent_registry` DO exist in the live `ahos` Postgres DB → importing this workflow would make it live.
- Verdict: **REJECTED for import** until rewritten; recommend quarantine marker + `validate_n8n` rule (no interpolated SQL, no DELETE on audit tables, no `execution_status` mutation).

## 6. Test coverage

| Level | State | Evidence |
|---|---|---|
| Unit | IMPLEMENTED_VERIFIED | 44 `def test_` across 6 `tests/test_telegram_*.py`; Grok run: 150 passed + 1 xfailed (incl. parametrised + import-safety) |
| Integration (fake transport) | PARTIAL | `MockTelegramAdapter` exists; no end-to-end harness that drives runner → service → **real local gateway** with a fake Telegram transport and asserts envelope/identity/audit |
| Live E2E (G11) | OWNER_ACTION_REQUIRED | `reports/telegram_e2e_20260909_165348.md` exists (historical); G11 currently NOT_VERIFIED in `operator_validation_report_windows_20261002.json` |

## 7. Buildable WITHOUT real credentials

| Capability | Exists? | Gap |
|---|---|---|
| Adapter contract (interface) | YES (`TelegramBotAdapterInterface`) | add contract tests shared by Mock & Production (with stub transport) |
| Message envelope (update_id, chat, user, text, ts, channel) | PARTIAL (`TelegramUpdate`) | add explicit versioned envelope + schema test |
| Sender identity propagation | NO (`user_id:""`) | forward chat_id/user_id → gateway; gateway logs principal |
| Command routing | YES (`/start` `/help` `/top` `/market`) | table-driven tests |
| Capability checks per command | NO | deny `start/stop/paper_buy` from `channel=telegram` unless admin + confirm token |
| Auth boundary (allowlist, fail-closed) | YES | add tests for admin-only commands |
| Replay protection | PARTIAL | runner-level `update_id` dedupe window + test |
| Audit trail | NO | append-only JSONL `reports/telegram_audit_<date>.jsonl` (no text bodies with secrets; hashed chat ids) |
| Offline behaviour | YES (`EMERGENCY_FALLBACK_ONLY`, `--console`) | tests exist for fallback; add gateway-timeout test |
| Fake transport | YES (`MockTelegramAdapter`; `ProductionTelegramAdapter(transport=…)`) | — |
| Integration harness | NO | pytest harness spinning a stub HTTP gateway (no Postgres) or pointing at local gateway in opt-in mode |

## 8. OWNER_ACTION remaining
1. G11 live E2E: run a real Telegram session through `run_bot.py` against the live gateway, archive `reports/telegram_e2e_<UTC>.md`, re-run gate with `--telegram-e2e-artifact`.
2. Decide gateway port (3000 vs 3500) so `AHOS_GATEWAY_URL` in `.env` matches the running gateway (Telegram service uses the same variable).
3. Proxy/tunnel availability (api.telegram.org filtered) — operator environment.
