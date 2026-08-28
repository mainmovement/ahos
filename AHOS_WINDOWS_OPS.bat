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
echo ==========================================================
echo   NEXT: start Next.js in ANOTHER window, then come back:
echo     npm run dev
echo   Press any key HERE after http://127.0.0.1:3000 is Ready
echo ==========================================================
pause

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
echo Paste BEGIN REPORT + reports\operator_validation_report_windows_*.json into Cursor.
echo STATE B: never db:migrate / db:push
echo.
pause
endlocal
