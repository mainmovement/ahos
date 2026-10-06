# BOX_PATCHES_MERGED

Written: 2026-10-07 00:25 Asia/Tehran
Source: Grok box branch `grok-box-debug` @ b2c3859 (patches 0001–0023).
Laptop base before merge: `e912fb6` (ahos). Merge branch: `grok/box-security-merge`.
PAPER_ONLY. No secrets. Never push from this merge.

## Claude autopilot: SKIP redoing these

If a mission would re-implement dashboard `#boot=` bootstrap, CSRF header-only,
engine propose→confirm, posix_group_ok/killpg safety, chat `parseChatBody`, or
pglite absolute dataDir — treat as ALREADY DONE here. Prefer extending tests over rewriting.

## Patch status

| ID | Subject | Status | Notes |
|----|---------|--------|-------|
| 0001 | pglite absolute dataDir (db + launcher) | **PRESENT** |  |
| 0002 | venv on POSIX; shortcut powershell.exe | **PRESENT** |  |
| 0003 | record selected gateway port across processes | **SUPERSEDED_BY_CLAUDE** | Claude M11.1–M11.3 already evolved gateway port/identity; box port-record semantics kept where still applicable. |
| 0004 | record_test_run anchors relative executables | **PRESENT** |  |
| 0005 | document AHOS_TELEGRAM_POLL in .env.example | **PRESENT** |  |
| 0006 | track M9.5 / Phase 7b/11 test moves | **PRESENT** |  |
| 0007 | doc_drift: untracked files no longer satisfy refs | **PRESENT** |  |
| 0008 | engines.node >=22.6.0 | **PRESENT** |  |
| 0009 | require X-AHOS-CSRF echo header | **PRESENT** |  |
| 0010 | session issuance under real Next; refuse rebinding | **PRESENT** | Full box `checkSessionIssuance` + Host/Sec-Fetch/Origin path via handleSessionIssuance. |
| 0011 | fix /api/chat JSON.parse(...).catch | **PRESENT** | Uses `parseChatBody`; old `JSON.parse(raw).catch` removed. |
| 0012 | process layer runs off Windows | **PRESENT** |  |
| 0013 | honest Telegram allowlist; soft preflight not failed | **PRESENT** |  |
| 0014 | terminate() waits on each stop stage | **PRESENT** |  |
| 0015 | POSIX stop reaches whole child tree | **PRESENT** |  |
| 0016 | isolate os.environ around operator_validation_gate | **PRESENT** |  |
| 0017 | one-time dashboard bootstrap token (F1) | **PRESENT** | chat_auth + session route + CommandCenter + web_api_client from box; CSRF header-only. |
| 0018 | launcher issue bootstrap tokens + bootstrap-url | **PRESENT** | Helpers in components + orchestrator.bootstrap_url + `__main__ bootstrap-url`; Claude M11 launcher identity kept. |
| 0019 | /api/engine start/stop via propose->confirm (F2) | **PRESENT** |  |
| 0020 | POSIX group signals only for verified leader (F3/F4) | **PRESENT** | posix_group_ok + box terminate; Windows CTRL_BREAK / CREATE_NEW_PROCESS_GROUP retained. |
| 0021 | doc_drift counts only tracked files (F5) | **PRESENT** |  |
| 0022 | stop copying web API token into NEXT_PUBLIC_* (F8) | **PRESENT** |  |
| 0023 | conftest checks stores under AHOS_DATA_DIR | **PRESENT** |  |

## Live marker check (post-merge)

- `consumeBootstrapToken`: YES
- `checkSessionIssuance`: YES
- `handleSessionIssuance`: YES
- `parseChatBody`: YES
- `JSON.parse.catch_gone`: YES
- `engine_propose`: YES
- `boot_fragment`: YES
- `issue_dashboard_boot_token`: YES
- `bootstrap_url_orch`: YES
- `bootstrap_url_cli`: YES
- `posix_group_ok`: YES
- `pglite_data_dir_py`: YES
- `pgliteDataDir_ts`: YES
- `CSRF_header_only`: YES
- `engines_node`: YES
- `AHOS_TELEGRAM_POLL`: YES

## Intentional non-overwrite

- Claude M11.1–M11.4 launcher identity (node next spawn, telegram stability, PS5.1 log),
  dashboard-api control chain, and related tests were **kept** where they conflicted with older box launcher hunks.
- Box security semantics (F1/F2/F3/F4/F5/F8 + chat parse + pglite abs) were **forced present**.


## M10.1 (Grok, 2026-10-07 Asia/Tehran)

PGlite launcher init + `--check` probe — **DONE**. See `reports/grok/M10_1_DONE_BY_GROK.md`.
Claude: do not re-implement. HOLD.flag still present (model/quota), unrelated to this code.

## M54 (Grok, 2026-10-07 Asia/Tehran)

StartupValidator + 	est_f1_s1 honour AHOS_DATA_DIR via config.paths — **DONE**. See eports/grok/M54_DONE_BY_GROK.md.
Claude: do not re-implement. HOLD.flag still present (model/quota), unrelated to this code.
