@echo off
REM AHOS -- G2 clear on main + gate (PAPER_ONLY). Pair with MERGE MICRO #61.
REM Empty-gateway fill is already on origin/main (#45 ensure_token + gate).
REM This PR adds leave-open wakes #56+#60 to push/post_gate.
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "AHOS_GATE_PR=56"

echo ==========================================================
echo   AHOS G2 CLEAR MAIN (ensure token + gate + evidence wake)
echo   Will NOT migrate DB or claim READY
echo ==========================================================

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

set "PS=powershell"
where powershell >nul 2>&1
if errorlevel 1 (
  if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
    set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
  ) else (
    echo ERROR: powershell.exe not found
    pause
    exit /b 2
  )
)

echo ==^> git fetch / pull origin main
git fetch origin main
git pull origin main
if errorlevel 1 (
  echo WARNING: git pull failed - continuing with checkout from origin/main
)

echo ==^> checkout gate scripts from origin/main
git checkout origin/main -- scripts/operator_validation_gate.py scripts/windows_ensure_web_api_token.ps1 scripts/windows_run_operator_gate.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_restart_next_dev.ps1 scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_postgres_win.ps1 scripts/windows_ensure_database_url.ps1 scripts/windows_seed_local_evidence.ps1 scripts/windows_publish_owner_paste.ps1
if errorlevel 1 (
  echo WARNING: main checkout returned non-zero
)

REM Wake hardcodes (#56/#60): prefer this PR tree, else curl tip, else main after #61 merge.
findstr /C:"Leave-open paste sinks first" "scripts\windows_push_gate_evidence.ps1" >nul 2>&1
if errorlevel 1 (
  echo ==^> overlay push/post_gate wake hardcodes
  if exist "scripts\windows_push_gate_evidence.ps1" (
    rem keep trying curl
  )
  curl.exe -fsSL -o "scripts\windows_push_gate_evidence.ps1" "https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-wake-hardcode-4bde/scripts/windows_push_gate_evidence.ps1"
  curl.exe -fsSL -o "scripts\windows_post_gate_paste_gh.ps1" "https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-wake-hardcode-4bde/scripts/windows_post_gate_paste_gh.ps1"
)
findstr /C:"Leave-open paste sinks first" "scripts\windows_push_gate_evidence.ps1" >nul 2>&1
if errorlevel 1 (
  git checkout origin/main -- scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 2>nul
)

findstr /C:"must NOT BLOCK" "scripts\operator_validation_gate.py" >nul 2>&1
if errorlevel 1 (
  echo ERROR: gate missing empty-gateway fix - pull main / fix network
  pause
  exit /b 2
)

echo ==^> ensure web API token + fill empty AHOS_GATEWAY_URL
"%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_web_api_token.ps1"

if exist "scripts\windows_ensure_postgres_win.ps1" (
  echo ==^> ensure Postgres (STATE B: no migrate)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_postgres_win.ps1"
)
if exist "scripts\windows_ensure_database_url.ps1" (
  echo ==^> ensure DATABASE_URL
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_database_url.ps1"
)

echo ==^> restart Next so .env reloads
if exist "scripts\windows_restart_next_dev.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_restart_next_dev.ps1"
)

if exist "scripts\windows_wait_for_web_api.ps1" (
  echo ==^> warm /api/chat
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_wait_for_web_api.ps1"
)

echo ==^> full operator gate + evidence push to #56/#60
"%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_run_operator_gate.ps1" -SeedEvidenceIfNeeded
set "RC=!ERRORLEVEL!"

echo.
echo NEXT: leave PR #56 and #60 OPEN. Prefer also merge #59 for MAIN_CLEAR.
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
if exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  echo OWNER_PASTE: %CD%\reports\OWNER_PASTE_WINDOWS_GATE.txt
)
if exist "%USERPROFILE%\Desktop\AHOS_PASTE_TO_CURSOR.txt" (
  echo Desktop: %USERPROFILE%\Desktop\AHOS_PASTE_TO_CURSOR.txt
)
pause
exit /b !RC!
