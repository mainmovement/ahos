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
echo ==^> git fetch / pull (stay on current branch helpers)
git fetch origin
git pull
if errorlevel 1 (
  echo WARNING: git pull failed - continuing if scripts already present
)

if not exist "scripts\windows_post_merge_reconcile.ps1" (
  echo ERROR: missing scripts\windows_post_merge_reconcile.ps1 - clone/pull main first
  pause
  exit /b 2
)

echo.
echo ==^> post-merge reconcile + web API token ensure (KeepCurrentBranch)
REM KeepCurrentBranch avoids deleting unmerged bat/preflight when syncing main.
powershell -ExecutionPolicy Bypass -File ".\scripts\windows_post_merge_reconcile.ps1" -KeepCurrentBranch
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
echo ==^> restart Next.js so .env token is loaded (stale :3000 is a G2 trap)
if exist "scripts\windows_restart_next_dev.ps1" (
  powershell -ExecutionPolicy Bypass -File ".\scripts\windows_restart_next_dev.ps1"
) else (
  where npm >nul 2>&1
  if errorlevel 1 (
    echo ERROR: npm not on PATH
    pause
    exit /b 2
  )
  start "AHOS Next.js :3000" cmd /k "cd /d ""%~dp0"" && echo AHOS Next.js - leave this window open && npm run dev"
)

echo ==^> wait + warm http://127.0.0.1:3000/api/chat (up to ~180s)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Continue';" ^
  "$envPath=Join-Path (Get-Location) '.env';" ^
  "$tok=''; foreach($line in (Get-Content $envPath -ErrorAction SilentlyContinue)){ if($line -match '^\s*AHOS_WEB_API_TOKEN\s*=\s*(.*)$'){ $tok=$Matches[1].Trim().Trim('\"').Trim(\"'\"); break } };" ^
  "$ok=$false; for($i=0;$i -lt 90;$i++){" ^
  "  try {" ^
  "    $headers=@{ 'Content-Type'='application/json' };" ^
  "    if($tok){ $headers['Authorization']=('Bearer '+$tok) };" ^
  "    $body='{\"message\":\"ping\",\"locale\":\"fa\"}';" ^
  "    $r=Invoke-WebRequest -Uri 'http://127.0.0.1:3000/api/chat' -Method POST -Headers $headers -Body $body -UseBasicParsing -TimeoutSec 45;" ^
  "    Write-Host ('Warm /api/chat HTTP '+$r.StatusCode); $ok=$true; break" ^
  "  } catch {" ^
  "    try { $null=Invoke-WebRequest -Uri 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 2 } catch {};" ^
  "    Start-Sleep -Seconds 2" ^
  "  }" ^
  "}; if(-not $ok){ Write-Host 'TIMEOUT waiting for /api/chat'; exit 2 }; exit 0"
if errorlevel 1 (
  echo ERROR: Next.js /api/chat did not become ready on 127.0.0.1:3000
  echo Fix the other window, then re-run this bat or windows_run_operator_gate.ps1
  pause
  exit /b 2
)

if exist "scripts\windows_seed_local_evidence.ps1" (
  echo.
  echo ==^> seed local SQLite evidence if G4/G5/G8/G9 census empty
  powershell -ExecutionPolicy Bypass -File ".\scripts\windows_seed_local_evidence.ps1"
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
echo Paste BEGIN REPORT + reports\OWNER_PASTE_WINDOWS_GATE.txt into Cursor.
echo STATE B: never db:migrate / db:push
echo.
pause
endlocal
