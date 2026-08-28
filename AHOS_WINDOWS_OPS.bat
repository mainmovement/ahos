@echo off
REM AHOS Windows ops toward PRE_SOAK (PAPER_ONLY) - double-click runnable
REM STATE B: do NOT db:migrate / db:push
REM Does NOT invent OPERATOR_READY
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

if not exist "reports" mkdir "reports"
set "LOG=reports\windows_ops_last_run.log"
echo ==== AHOS_WINDOWS_OPS start %DATE% %TIME% ==== > "%LOG%"

call :log ==========================================================
call :log   AHOS Windows ops (main harden path)
call :log   Will NOT migrate DB or claim OPERATOR_READY
call :log ==========================================================

REM Ensure powershell is usable (Explorer double-click often lacks profile PATH)
set "PS=powershell"
where powershell >nul 2>&1
if errorlevel 1 (
  if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
    set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
  ) else (
    call :log ERROR: powershell.exe not found
    pause
    exit /b 2
  )
)

where git >nul 2>&1
if errorlevel 1 (
  call :log ERROR: git not on PATH - install Git for Windows and reopen
  pause
  exit /b 2
)

call :log ==^> git fetch / pull origin main (+ current branch if not main)
git fetch origin >> "%LOG%" 2>&1
git fetch origin cursor/windows-chat-500-rootcause-4bde >nul 2>&1
git fetch origin cursor/windows-g2-evidence-autopush-4bde >nul 2>&1
git fetch origin cursor/windows-evidence-push-lease-4bde >> "%LOG%" 2>&1
git fetch origin cursor/windows-reconcile-ops-artifacts-4bde >> "%LOG%" 2>&1
git fetch origin cursor/windows-g2-empty-gateway-default-4bde >> "%LOG%" 2>&1
git pull origin main >> "%LOG%" 2>&1
if errorlevel 1 (
  call :log WARNING: git pull origin main failed - continuing if scripts present
)
REM Prefer newest unlock tip not yet contained in origin/main.
set "OPS_SYNC_REF=origin/main"
git rev-parse --verify origin/cursor/windows-chat-500-rootcause-4bde >nul 2>&1
if not errorlevel 1 (
  git merge-base --is-ancestor origin/cursor/windows-chat-500-rootcause-4bde origin/main >nul 2>&1
  if errorlevel 1 (
    set "OPS_SYNC_REF=origin/cursor/windows-chat-500-rootcause-4bde"
  )
)
if "!OPS_SYNC_REF!"=="origin/main" (
  git rev-parse --verify origin/cursor/windows-g2-evidence-autopush-4bde >nul 2>&1
  if not errorlevel 1 (
    git merge-base --is-ancestor origin/cursor/windows-g2-evidence-autopush-4bde origin/main >nul 2>&1
    if errorlevel 1 (
      set "OPS_SYNC_REF=origin/cursor/windows-g2-evidence-autopush-4bde"
    )
  )
)
if "!OPS_SYNC_REF!"=="origin/main" (
  git rev-parse --verify origin/cursor/windows-g2-empty-gateway-default-4bde >nul 2>&1
  if not errorlevel 1 (
    git merge-base --is-ancestor origin/cursor/windows-g2-empty-gateway-default-4bde origin/main >nul 2>&1
    if errorlevel 1 (
      set "OPS_SYNC_REF=origin/cursor/windows-g2-empty-gateway-default-4bde"
    )
  )
)
if "!OPS_SYNC_REF!"=="origin/main" (
  git rev-parse --verify origin/cursor/windows-reconcile-ops-artifacts-4bde >nul 2>&1
  if not errorlevel 1 (
    git merge-base --is-ancestor origin/cursor/windows-reconcile-ops-artifacts-4bde origin/main >nul 2>&1
    if errorlevel 1 (
      set "OPS_SYNC_REF=origin/cursor/windows-reconcile-ops-artifacts-4bde"
    )
  )
)
call :log ==^> force-sync ops scripts from !OPS_SYNC_REF!
git checkout "!OPS_SYNC_REF!" -- "scripts/windows_*.ps1" scripts/ahos_pg_probe.mjs AHOS_WINDOWS_OPS.bat AHOS_PRE_SOAK_NOW.bat AHOS_VALIDATE_G2_NOW.bat AHOS_PULL_OPS_UNLOCK.bat WINDOWS_RUN_THIS_FIRST.txt scripts/operator_validation_gate.py scripts/windows_g2_probe.py app/api/chat/route.ts db/index.ts snapshot.ts tests/validate_n8n.py deployment/docker-compose.windows.yml .env.example >> "%LOG%" 2>&1
if errorlevel 1 (
  call :log WARNING: force-sync ops scripts failed - parse preflight may catch stale scripts
)
for /f "delims=" %%B in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "CURBRANCH=%%B"
if defined CURBRANCH if /I not "!CURBRANCH!"=="main" (
  call :log ==^> git pull origin !CURBRANCH!
  git pull origin !CURBRANCH! >> "%LOG%" 2>&1
)

if exist "scripts\windows_validate_ps1_parse.ps1" (
  call :log ==^> validate windows_*.ps1 parse ^(PS 5.1^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_validate_ps1_parse.ps1"
  if errorlevel 1 (
    call :log PARSE preflight failed - writing OWNER_PASTE for Cursor
    call :failpaste ps1_parse "windows_*.ps1 failed Parser check - pull main with ASCII+BOM fix"
    call :log Log: %CD%\%LOG%
    pause
    exit /b 2
  )
)

if exist "scripts\windows_pre_soak_readiness.ps1" (
  call :log ==^> pre-soak readiness checklist ^(no READY claim^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_pre_soak_readiness.ps1" -AllowDockerStarting
  if errorlevel 1 (
    call :log WARNING: readiness FAILs present - ensure-pg / token ensure may still fix Docker+gateway
  )
)

if not exist "scripts\windows_post_merge_reconcile.ps1" (
  call :log ERROR: missing scripts\windows_post_merge_reconcile.ps1 - pull main first
  call :failpaste missing_reconcile_script "pull harden branch or main first"
  pause
  exit /b 2
)

if exist "scripts\windows_ensure_postgres_win.ps1" (
  call :log ==^> ensure ahos_postgres_win running ^(no migrate^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_postgres_win.ps1"
  if errorlevel 1 (
    call :log WARNING: postgres ensure failed - G2 may HTTP 500; continuing
  )
)

call :log ==^> post-merge reconcile + web API token ensure (KeepCurrentBranch)
"%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_post_merge_reconcile.ps1" -KeepCurrentBranch >> "%LOG%" 2>&1
if errorlevel 1 (
  call :log WARNING: reconcile exited !ERRORLEVEL! - paste REPORT into Cursor anyway
)

REM Belt-and-suspenders: token ensure even if reconcile STOP'd early on dirty paths
if exist "scripts\windows_ensure_web_api_token.ps1" (
  call :log ==^> ensure AHOS_WEB_API_TOKEN in .env ^(idempotent^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_web_api_token.ps1"
  if errorlevel 1 (
    call :log WARNING: web API token ensure failed - preflight may FAIL
  )
)

if exist "scripts\windows_preflight_ops.ps1" (
  call :log ==^> Windows preflight
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_preflight_ops.ps1"
  if errorlevel 1 (
    call :log PREFLIGHT failed - writing OWNER_PASTE for Cursor, then stop
    call :failpaste preflight "fix FAIL lines in preflight output, then re-run bat"
    call :log Log: %CD%\%LOG%
    pause
    exit /b 2
  )
)

call :log ==^> restart Next.js so .env token is loaded
if exist "scripts\windows_restart_next_dev.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_restart_next_dev.ps1"
) else (
  where npm >nul 2>&1
  if errorlevel 1 (
    call :log ERROR: npm not on PATH
    call :failpaste npm_missing "install Node.js / ensure npm on PATH"
    pause
    exit /b 2
  )
  start "AHOS Next.js :3000" cmd /k "cd /d ""%~dp0"" && echo AHOS Next.js - leave this window open && npm run dev"
)

set "WAIT_FAIL=0"
if exist "scripts\windows_wait_for_web_api.ps1" (
  call :log ==^> wait + warm /api/chat
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_wait_for_web_api.ps1"
  if errorlevel 1 (
    call :log WARNING: /api/chat warm failed - one recovery: ensure-pg + restart Next + wait again
    if exist "scripts\windows_ensure_postgres_win.ps1" (
      "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_postgres_win.ps1"
    )
    if exist "scripts\windows_restart_next_dev.ps1" (
      "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_restart_next_dev.ps1"
    )
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_wait_for_web_api.ps1"
    if errorlevel 1 (
      set "WAIT_FAIL=1"
      call :log WARNING: /api/chat still not ready after recovery - writing failure paste, then still run gate for honest G2 JSON
      call :failpaste wait_web_api "Next /api/chat not ready after ensure-pg recovery; gate will likely G2 FAIL"
    ) else (
      call :log Recovery warm OK - continuing to gate
    )
  )
) else (
  call :log ERROR: missing windows_wait_for_web_api.ps1
  call :failpaste missing_wait_script "checkout cursor/windows-g2-empty-gateway-default-4bde"
  pause
  exit /b 2
)

if exist "scripts\windows_seed_local_evidence.ps1" (
  call :log ==^> seed local SQLite evidence if census empty ^(Postgres rows do NOT count^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_seed_local_evidence.ps1"
  if errorlevel 1 (
    call :log WARNING: seed census still insufficient - G4/G5/G8/G9 may FAIL honestly
  )
)

if exist "scripts\windows_run_operator_gate.ps1" (
  call :log ==^> windows_run_operator_gate.ps1
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_run_operator_gate.ps1"
) else (
  call :log ==^> operator_validation_gate.py fallback
  if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
  set AHOS_PAPER_ONLY=1
  if "%AHOS_EVIDENCE_SOURCE%"=="" set AHOS_EVIDENCE_SOURCE=local
  "%PY%" scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
)

echo. >> "%LOG%"
echo.
if exist "reports\LATEST_WINDOWS_GATE.txt" (
  call :log ----- LATEST_WINDOWS_GATE.txt -----
  type "reports\LATEST_WINDOWS_GATE.txt"
  type "reports\LATEST_WINDOWS_GATE.txt" >> "%LOG%"
)
if exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  call :log Paste file ready: reports\OWNER_PASTE_WINDOWS_GATE.txt
  call :log Prefer Ctrl+V into Cursor, or forward Telegram doc if sent.
) else (
  call :log Paste reports\operator_validation_report_windows_*.json into Cursor.
)
if "!WAIT_FAIL!"=="1" (
  call :log NOTE: 127.0.0.1:3000 /api/chat warm failed earlier - check G2 in paste; STATE B no migrate
)
call :log STATE B: never db:migrate / db:push
call :log Full log: %CD%\%LOG%
echo.
pause
endlocal
exit /b 0

:failpaste
if exist "scripts\windows_write_ops_failure_paste.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_write_ops_failure_paste.ps1" -Stage "%~1" -Detail "%~2"
) else (
  call :log WARNING: failure paste helper missing - copy %LOG% into Cursor
)
goto :eof

:log
echo %*
echo %* >> "%LOG%"
goto :eof
