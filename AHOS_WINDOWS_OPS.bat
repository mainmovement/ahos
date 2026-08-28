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

call :log ==^> git fetch / pull origin main
git fetch origin >> "%LOG%" 2>&1
git pull origin main >> "%LOG%" 2>&1
if errorlevel 1 (
  call :log WARNING: git pull origin main failed - continuing if scripts present
)

if not exist "scripts\windows_post_merge_reconcile.ps1" (
  call :log ERROR: missing scripts\windows_post_merge_reconcile.ps1 - pull main first
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

if exist "scripts\windows_preflight_ops.ps1" (
  call :log ==^> Windows preflight
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_preflight_ops.ps1"
  if errorlevel 1 (
    call :log PREFLIGHT failed - fix FAIL lines, then re-run this bat
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
    pause
    exit /b 2
  )
  start "AHOS Next.js :3000" cmd /k "cd /d ""%~dp0"" && echo AHOS Next.js - leave this window open && npm run dev"
)

if exist "scripts\windows_wait_for_web_api.ps1" (
  call :log ==^> wait + warm /api/chat
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_wait_for_web_api.ps1"
) else (
  call :log ERROR: missing windows_wait_for_web_api.ps1
  pause
  exit /b 2
)
if errorlevel 1 (
  call :log ERROR: Next.js /api/chat not ready on 127.0.0.1:3000
  call :log Fix the other window, then re-run bat or windows_run_operator_gate.ps1
  call :log Log: %CD%\%LOG%
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
call :log STATE B: never db:migrate / db:push
call :log Full log: %CD%\%LOG%
echo.
pause
endlocal
exit /b 0

:log
echo %*
echo %* >> "%LOG%"
goto :eof
