# DASHBOARD & ONE-CLICK REALITY — 2026-10-02 (Grok, read-only)

## 1. Where
- App Router: `app/page.tsx` → `CommandCenter.tsx` (repo root, 1,072 lines). API routes: `app/api/{alerts,canonical,chat,command,engine,metrics,paper,watch}/route.ts`.
- Data: `CommandCenter.tsx:282-283` polls `GET /api/command` + `GET /api/alerts` via `webApiFetch` (bearer token); actions POST `/api/engine` (372), `/api/chat` (399), `/api/watch` (426), `/api/paper` (453).
- `/api/command` (`app/api/command/route.ts`) → `snapshot.ts::commandSnapshot()` (Postgres via Drizzle + Python canonical read model); on error → `failClosedCommandSnapshot` (`snapshot.ts:49-97`: `executionMode PAPER_ONLY`, `running:false`, `lastCycleStatus:"CODE_FAILURE"`, DB item flagged).
- Data is **real backend data, not mock/hardcoded**. Third-party UI experiments (`advanced-3d-audiovisual-website*`, Persian-named platform folders) are separate templates, not the AHOS dashboard (DOC_TRUTH_MAP: orphan templates).

## 2. Fake-READY risk
| Scenario | Behaviour | Risk |
|---|---|---|
| Postgres down, gateway up | fail-closed snapshot, CODE_FAILURE, running=false | LOW (honest) |
| Canonical read model STALE/UNAVAILABLE | red banner `CommandCenter.tsx:532-537`, status `:635` | LOW |
| **Gateway process dies after first successful load** | `catch` sets `bootError` (`CommandCenter.tsx:304-306`) but **keeps the last `snap`**; health dims keep showing "OK", run pill keeps "running" colour (`:558-561`); only a short suffix at `:607` reveals the error | **MEDIUM — stale-READY** |
| Policy dims | `snapshot.ts:161` (paper) and `:163` (PAPER_ONLY) are hard-coded `"OK"` | LOW (policy statement, but shown with same OK style as measured health) |
| Health dims "OK" semantics | e.g. `snapshot.ts:154` cycle OK if `finishedAt` exists regardless of age | MEDIUM (no freshness threshold) |

## 3. Coverage of requested panels
| Panel | Shown? |
|---|---|
| System health | PARTIAL (health dims from snapshot) |
| DB | PARTIAL (only in fail-closed item) |
| Runtime / engine running | YES |
| Current mission | NO |
| Agents / roles | NO (council summary only) |
| AI provider | YES (providers list `:689-709`, statuses incl. RATE_LIMITED/AUTH_FAILED per `types.ts:2-12`) |
| Telegram | NO (snapshot lists "Telegram scrape OUT_OF_POLICY" only, `snapshot.ts:292`) |
| Docker / n8n dependency | NO |
| Tests | NO |
| Evidence | NO (canonical decisions show evidence/unknowns per token) |
| Blockers | NO |
| Next action | NO |
| PAPER_ONLY | YES (`:488`, disclaimer `:81`) |
| Canonical decision state | YES (`:487`, `:635`, `:647-665`, `:960-965`) |

## 4. One-click launchers
| File | What it does | Port |
|---|---|---|
| `start_ahos.bat` / `start_ahos.ps1` | native observation daemon (`--daemon --interval-sec 60 --observation-cycle`, `AHOS_EVIDENCE_SOURCE=local`) | n/a |
| `AHOS_WINDOWS_OPS.bat` | ops menu; starts Next in a new window (`:179` title "AHOS Next.js :3000", `npm run dev` → default 3000) | 3000 |
| `AHOS_PRE_SOAK_NOW.bat`, `AHOS_BOOTSTRAP_PRESOAK.bat`, `AHOS_FIX_G2_AND_GATE.bat`, `AHOS_VALIDATE_G2_NOW.bat`, `AHOS_MAIN_FIRST.bat`, `AHOS_APPLY_TIP.bat`, `AHOS_PULL_OPS_UNLOCK.bat`, `AHOS_PUSH_EVIDENCE_NOW.bat` | wrappers over `scripts/windows_*.ps1` | 3000 via scripts |
| `scripts/windows_run_operator_gate.ps1` | operator gate runner | `:7`, `:64-65` default 3000 when `AHOS_GATEWAY_URL` empty |

## 5. Port 3000 vs 3500 drift (exact)
- Running gateway: `next dev --hostname 127.0.0.1 -p 3500` (manual, started 04:39 local). **No tracked file references port 3500.**
- Binding config: `.env:99 AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat` (operator file, gitignored) → loaded over process env by `scripts/operator_validation_gate.py:772-777`; default/persist logic `:782-789` (only when empty).
- Repo defaults on 3000: `.env.example:109`; `package.json` `dev` (Next default 3000); `scripts/windows_run_operator_gate.ps1:7,64,65`; `scripts/operator_validation_gate.py:224,228,615,618,783,784,787`; `scripts/windows_g2_probe.py:51`; `scripts/windows_preflight_ops.ps1:9,131,210-220`; `scripts/windows_pre_soak_readiness.ps1:18,159,182`; `scripts/windows_wait_for_web_api.ps1:14,149`; `scripts/windows_ensure_web_api_token.ps1:122`; `scripts/windows_restart_next_dev.ps1:2`; `scripts/windows_fix_g2_empty_and_gate.ps1:90,97`; `scripts/windows_chat_500_forensics.ps1:16,17`; `scripts/windows_diagnose_docker_health.ps1:185`; `scripts/windows_g11_telegram_e2e_helper.ps1:85`; `AHOS_WINDOWS_OPS.bat:179,257`; `deployment/docker-compose.windows.yml:74`; tests `tests/test_operator_validation_gate.py` (many), `tests/test_web_api_auth_gate.py:113`, `scripts/web_api_auth_selftest.ts:31`.
- Claude's own G2 report notes both ports were measured FREE before launch — there is no evidence Windows cannot bind 3000.
- **Conclusion:** this is not a one-line drift in the gate script. 3000 is the canonical repo default; 3500 is a one-off runtime choice. A blind 3000→3500 rewrite would break ~40 references and tests. Safe options: (a) owner restarts gateway on 3000 (OWNER_ACTION, service restart), or (b) owner edits `.env:99` to 3500 (OWNER_ACTION, config), or (c) code mission: single-source the port (`AHOS_GATEWAY_PORT` read by launchers + gate) plus a non-mutating preflight that detects "configured URL has no listener but another AHOS gateway port does" — executable, test-backed.
