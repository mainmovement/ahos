@echo off
REM AHOS -- MAIN-ONLY G2 clear + full gate (PAPER_ONLY)
REM Empty-gateway fix is already on origin/main (#45). Last paste 220318 was BEFORE that merge.
REM G12 charmap also fixed on main (validate_n8n UTF-8). Last paste head lacked encoding=.
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM   curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_MAIN_CLEAR_G2.cmd
REM   AHOS_MAIN_CLEAR_G2.cmd
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

REM Wake leave-open paste sink #56 (and tip notify script)
set "AHOS_GATE_PR=56"

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

echo ==^> checkout gate + warm scripts from origin/main
git checkout origin/main -- scripts/operator_validation_gate.py tests/validate_n8n.py scripts/windows_ensure_web_api_token.ps1 scripts/windows_run_operator_gate.ps1 scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 scripts/windows_publish_owner_paste.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_recover_g2_warm.ps1 scripts/windows_restart_next_dev.ps1 scripts/windows_ensure_database_url.ps1 scripts/windows_ensure_postgres_win.ps1 scripts/windows_chat_500_forensics.ps1 AHOS_PUSH_EVIDENCE_NOW.bat 2>nul

echo ==^> overlay tip post_gate notify (#56 sink) via curl SHA pin
if not exist "scripts" mkdir scripts >nul 2>&1
curl.exe -L -o "scripts\windows_post_gate_paste_gh.ps1" "https://raw.githubusercontent.com/mainmovement/ahos/564684d0c585a86aa894b95818ea1c2ac36d461e/scripts/windows_post_gate_paste_gh.ps1"
if errorlevel 1 (
  echo WARNING: tip post_gate overlay failed - AHOS_GATE_PR=56 still set for main script
)

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

REM After ensure token/DB URL, ALWAYS restart Next so .env reloads.
REM A stale :3000 listener (pre-token) would otherwise warm-401 then delay G2.
echo ==^> restart Next so .env token/DATABASE_URL are loaded
if exist "scripts\windows_restart_next_dev.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_restart_next_dev.ps1"
) else if exist "scripts\windows_recover_g2_warm.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_recover_g2_warm.ps1"
) else (
  echo WARNING: no restart_next / recover script - if :3000 is stale, G2 may 401
)

if exist "scripts\windows_wait_for_web_api.ps1" (
  echo ==^> warm /api/chat
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_wait_for_web_api.ps1"
  if errorlevel 1 (
    echo WARNING: warm failed - trying recover_g2_warm then re-warm
    if exist "scripts\windows_recover_g2_warm.ps1" (
      "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_recover_g2_warm.ps1"
    )
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_wait_for_web_api.ps1"
    if errorlevel 1 (
      echo WARNING: /api/chat still not warm - gate will report honest G2
    )
  )
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
