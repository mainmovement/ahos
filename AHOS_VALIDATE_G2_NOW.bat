@echo off
REM AHOS -- focused G2 validation (Docker health + gateway)
REM STATE B: never db:migrate / db:push
REM Does NOT invent PRE_SOAK or OPERATOR_READY
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS VALIDATE G2 NOW (health + gateway)
echo   Will NOT migrate DB or claim READY / PRE_SOAK
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
git fetch origin
git fetch origin cursor/windows-evidence-push-lease-4bde >nul 2>&1
git pull origin main
if errorlevel 1 (
  echo WARNING: git pull origin main failed - continuing with local tree
)

set "UNLOCK_REF="
git rev-parse --verify origin/cursor/windows-evidence-push-lease-4bde >nul 2>&1
if not errorlevel 1 (
  git merge-base --is-ancestor origin/cursor/windows-evidence-push-lease-4bde origin/main >nul 2>&1
  if errorlevel 1 set "UNLOCK_REF=origin/cursor/windows-evidence-push-lease-4bde"
)
if defined UNLOCK_REF (
  echo ==^> applying unlock tip !UNLOCK_REF!
  git checkout "!UNLOCK_REF!" -- AHOS_VALIDATE_G2_NOW.bat AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat WINDOWS_RUN_THIS_FIRST.txt "scripts/windows_*.ps1" scripts/windows_g2_probe.py scripts/operator_validation_gate.py deployment/docker-compose.windows.yml tests/validate_n8n.py 2>nul
  if errorlevel 1 (
    echo WARNING: bulk checkout failed - trying core files
    git checkout "!UNLOCK_REF!" -- AHOS_VALIDATE_G2_NOW.bat scripts/windows_validate_g2.ps1 scripts/windows_g2_probe.py scripts/windows_diagnose_docker_health.ps1 scripts/windows_ensure_postgres_win.ps1 scripts/windows_ensure_web_api_token.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_restart_next_dev.ps1 scripts/operator_validation_gate.py deployment/docker-compose.windows.yml
  )
) else (
  echo ==^> unlock tip already on origin/main
)

if not exist "scripts\windows_validate_g2.ps1" (
  echo ERROR: missing scripts\windows_validate_g2.ps1 - fetch unlock tip
  pause
  exit /b 2
)
if not exist "scripts\windows_g2_probe.py" (
  echo ERROR: missing scripts\windows_g2_probe.py - fetch unlock tip
  pause
  exit /b 2
)

"%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_validate_g2.ps1"
set "RC=!ERRORLEVEL!"

echo.
echo ==========================================================
echo   Paste reports\OWNER_PASTE_G2_VALIDATE.txt into Cursor
echo   G2 PASS alone is NOT PRE_SOAK -- need G1-G10 via OPS bat
echo   Never invent OPERATOR_READY
echo ==========================================================
pause
exit /b !RC!
