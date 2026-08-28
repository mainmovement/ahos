# Goal status — Windows PAPER_ONLY operational (honest)

**Generated (UTC):** 2026-08-28T21:05Z  
**main tip:** `d9a50f3` (PR #31 + #32)  
**PR #33 tip:** harden bat/gate against stale Next + token/env traps  
**Claim:** tooling improved for owner Windows run — **OPERATOR_READY = NOT_VERIFIED**

## Requirement audit

| Requirement | Evidence | Status |
|-------------|----------|--------|
| Merge web-api auth | PR #31 on main | **DONE** |
| Set tokens on laptop | No Windows REPORT / paste | **MISSING** (owner) |
| STATE B / no migrate | Scripts forbid migrate | **ENFORCED** |
| Operator validation G1–G10 | No Windows gate JSON | **MISSING** (owner) |
| Toward PRE_SOAK | Needs `pre_soak_entry_ok=true` | **BLOCKED** |
| No invented READY | Honored | **HONORED** |

## PR #33 hardening (this wave)

- `-KeepCurrentBranch` on reconcile (bat does not self-delete helpers)
- `windows_restart_next_dev.ps1` — kill stale `:3000`, start fresh Next after token write
- Bat warms `POST /api/chat` (not just `/`) up to ~180s
- G2 HTTP timeout 8s → 45s; force-load `.env` auth/DB keys over stale shell
- Preflight: `pg_isready` + SQLite evidence WARN
- Paste bundle → clipboard + Notepad

## Owner action

Merge or checkout PR #33, then double-click `AHOS_WINDOWS_OPS.bat` on `G:\robat\ahos`, Ctrl+V paste into Cursor. **No** `db:migrate` / `db:push`.
