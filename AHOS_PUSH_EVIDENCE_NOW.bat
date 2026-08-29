@echo off
REM AHOS -- push existing OWNER_PASTE to evidence branch + PR comments
REM Does NOT re-run gates. Does NOT invent PRE_SOAK/READY.
REM STATE B: never db:migrate / db:push
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS PUSH EVIDENCE NOW (existing paste only)
echo   Will NOT migrate / will NOT invent READY
echo ==========================================================

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

if not exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  if exist "reports\OWNER_PASTE_G2_VALIDATE.txt" (
    copy /Y "reports\OWNER_PASTE_G2_VALIDATE.txt" "reports\OWNER_PASTE_WINDOWS_GATE.txt" >nul
  )
)

if not exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  echo ERROR: no reports\OWNER_PASTE_WINDOWS_GATE.txt
  echo Run AHOS_PRE_SOAK_NOW.bat or AHOS_VALIDATE_G2_NOW.bat first.
  pause
  exit /b 2
)

if not exist "reports\LATEST_WINDOWS_GATE.txt" (
  echo pre_soak_entry_ok=False> "reports\LATEST_WINDOWS_GATE.txt"
  echo operator_ready=False>> "reports\LATEST_WINDOWS_GATE.txt"
  echo note=push_evidence_only>> "reports\LATEST_WINDOWS_GATE.txt"
  echo STATE B: do not db:migrate / db:push.>> "reports\LATEST_WINDOWS_GATE.txt"
)

echo ==^> post paste to open PRs via gh
if exist "scripts\windows_post_gate_paste_gh.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_post_gate_paste_gh.ps1" -BodyFile "reports\OWNER_PASTE_WINDOWS_GATE.txt"
)

echo ==^> push evidence branch
if exist "scripts\windows_push_gate_evidence.ps1" (
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_push_gate_evidence.ps1"
) else (
  echo ERROR: missing scripts\windows_push_gate_evidence.ps1 - pull unlock tip first
  echo   AHOS_PULL_OPS_UNLOCK.bat
  pause
  exit /b 2
)

echo.
echo Done. Also Ctrl+V reports\OWNER_PASTE_WINDOWS_GATE.txt into Cursor if needed.
echo PRE_SOAK only if paste shows pre_soak_entry_ok=true. Never invent READY.
pause
exit /b 0
