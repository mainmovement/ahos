@echo off
REM AHOS -- MAIN-ONLY G2 clear + full gate (PAPER_ONLY)
REM Empty-gateway fix is already on origin/main (#45). Last paste 220318 was BEFORE that merge.
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM   curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_MAIN_CLEAR_G2.cmd
REM   AHOS_MAIN_CLEAR_G2.cmd
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS MAIN CLEAR G2 (origin/main only)
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
  echo WARNING: git pull failed - continuing with local tree + checkout from origin/main
)

echo ==^> checkout gate scripts from origin/main
git checkout origin/main -- scripts/operator_validation_gate.py scripts/windows_ensure_web_api_token.ps1 scripts/windows_run_operator_gate.ps1 scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 scripts/windows_publish_owner_paste.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_database_url.ps1 AHOS_PUSH_EVIDENCE_NOW.bat 2>nul

if not exist "scripts\windows_ensure_web_api_token.ps1" (
  echo ERROR: missing windows_ensure_web_api_token.ps1 after main checkout
  pause
  exit /b 2
)
if not exist "scripts\windows_run_operator_gate.ps1" (
  echo ERROR: missing windows_run_operator_gate.ps1 after main checkout
  pause
  exit /b 2
)

echo ==^> scrub empty AHOS_GATEWAY_URL + ensure web API token
"%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_web_api_token.ps1"
if errorlevel 1 (
  echo WARNING: ensure token returned non-zero - continuing
)

if exist "scripts\windows_ensure_database_url.ps1" (
  echo ==^> ensure DATABASE_URL (probe-first; STATE B)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_database_url.ps1"
)

echo ==^> full operator gate G1-G12 + evidence push
"%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_run_operator_gate.ps1"
set "RC=!ERRORLEVEL!"

echo.
echo ==========================================================
echo   NEXT: paste OWNER_PASTE into GitHub PR #56 or #38
echo   Leave PR #56 OPEN. Prefer merge PR #58 for tip OPS push.
echo   PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
echo ==========================================================
if exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  echo OWNER_PASTE: %CD%\reports\OWNER_PASTE_WINDOWS_GATE.txt
) else (
  echo OWNER_PASTE missing - scroll console for errors
)
if exist "%USERPROFILE%\Desktop\AHOS_PASTE_TO_CURSOR.txt" (
  echo Desktop copy: %USERPROFILE%\Desktop\AHOS_PASTE_TO_CURSOR.txt
)
if exist "reports\PRE_SOAK_STATUS.txt" (
  echo ---- PRE_SOAK_STATUS ----
  type "reports\PRE_SOAK_STATUS.txt"
)
if exist "reports\LATEST_WINDOWS_GATE.txt" (
  echo ---- LATEST_WINDOWS_GATE ----
  type "reports\LATEST_WINDOWS_GATE.txt"
)
echo.
pause
exit /b !RC!
