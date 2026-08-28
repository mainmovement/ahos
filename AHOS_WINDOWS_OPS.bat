@echo off
REM AHOS Windows ops toward PRE_SOAK (PAPER_ONLY) - double-click runnable
REM STATE B: do NOT db:migrate / db:push
REM Does NOT invent OPERATOR_READY
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================================
echo   AHOS Windows ops (post web-api auth on main)
echo   Will NOT migrate DB or claim OPERATOR_READY
echo ==========================================================

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

echo.
echo ==^> git pull origin main
git fetch origin
git pull origin main
if errorlevel 1 (
  echo WARNING: git pull failed - continuing if scripts already present
)

if not exist "scripts\windows_post_merge_reconcile.ps1" (
  echo ERROR: missing scripts\windows_post_merge_reconcile.ps1 - clone/pull main first
  pause
  exit /b 2
)

echo.
echo ==^> post-merge reconcile + web API token ensure
powershell -ExecutionPolicy Bypass -File ".\scripts\windows_post_merge_reconcile.ps1"
if errorlevel 1 (
  echo WARNING: reconcile exited %ERRORLEVEL% - paste REPORT into Cursor anyway
)

if exist "scripts\windows_preflight_ops.ps1" (
  echo.
  echo ==^> Windows preflight
  powershell -ExecutionPolicy Bypass -File ".\scripts\windows_preflight_ops.ps1"
  if errorlevel 1 (
    echo PREFLIGHT failed - fix FAIL lines above before gate
    pause
    exit /b 2
  )
)

echo.
echo ==^> start Next.js in a new window (npm run dev)
where npm >nul 2>&1
if errorlevel 1 (
  echo ERROR: npm not on PATH
  pause
  exit /b 2
)
start "AHOS Next.js :3000" cmd /k "cd /d ""%~dp0"" && echo AHOS Next.js - leave this window open && npm run dev"

echo ==^> wait for http://127.0.0.1:3000 (up to ~120s)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ok=$false; for($i=0;$i -lt 60;$i++){ try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 2; $ok=$true; break } catch { Start-Sleep -Seconds 2 } }; if(-not $ok){ Write-Host 'TIMEOUT waiting for :3000'; exit 2 }; Write-Host 'Next.js reachable on :3000'; exit 0"
if errorlevel 1 (
  echo ERROR: Next.js did not become ready on 127.0.0.1:3000
  echo Fix the other window, then re-run this bat or windows_run_operator_gate.ps1
  pause
  exit /b 2
)

if exist "scripts\windows_run_operator_gate.ps1" (
  echo ==^> windows_run_operator_gate.ps1
  powershell -ExecutionPolicy Bypass -File ".\scripts\windows_run_operator_gate.ps1"
) else (
  echo ==^> operator_validation_gate.py fallback ^(main without PR #32^)
  if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
  ) else (
    set "PY=python"
  )
  set AHOS_PAPER_ONLY=1
  if "%AHOS_EVIDENCE_SOURCE%"=="" set AHOS_EVIDENCE_SOURCE=local
  "%PY%" scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
)

echo.
if exist "reports\LATEST_WINDOWS_GATE.txt" (
  echo ----- reports\LATEST_WINDOWS_GATE.txt -----
  type "reports\LATEST_WINDOWS_GATE.txt"
)
echo Paste BEGIN REPORT + reports\operator_validation_report_windows_*.json into Cursor.
echo Or open reports\OWNER_PASTE_WINDOWS_GATE.txt if present.
echo STATE B: never db:migrate / db:push
echo.
pause
endlocal
