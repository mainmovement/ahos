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
git fetch origin cursor/windows-evidence-notify-retarget-4bde >nul 2>&1
git fetch origin cursor/windows-presoak-unblock-4bde >nul 2>&1
git fetch origin cursor/windows-dburl-probe-first-4bde >nul 2>&1
git fetch origin cursor/windows-presoak-followup-4bde >nul 2>&1
git fetch origin cursor/windows-chat-500-rootcause-4bde >nul 2>&1
git fetch origin cursor/windows-g2-evidence-autopush-4bde >nul 2>&1
git fetch origin cursor/windows-evidence-push-lease-4bde >nul 2>&1
git pull origin main
if errorlevel 1 (
  echo WARNING: git pull origin main failed - continuing with local tree
)

set "UNLOCK_REF="
for %%R in (
  origin/cursor/windows-evidence-notify-retarget-4bde
  origin/cursor/windows-presoak-unblock-4bde
  origin/cursor/windows-dburl-probe-first-4bde
  origin/cursor/windows-presoak-followup-4bde
  origin/cursor/windows-chat-500-rootcause-4bde
  origin/cursor/windows-g2-evidence-autopush-4bde
) do (
  if not defined UNLOCK_REF (
    git rev-parse --verify %%R >nul 2>&1
    if not errorlevel 1 (
      git merge-base --is-ancestor %%R origin/main >nul 2>&1
      if errorlevel 1 set "UNLOCK_REF=%%R"
    )
  )
)
if defined UNLOCK_REF (
  echo ==^> applying unlock tip !UNLOCK_REF!
  git checkout "!UNLOCK_REF!" -- AHOS_VALIDATE_G2_NOW.bat AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat WINDOWS_RUN_THIS_FIRST.txt "scripts/windows_*.ps1" scripts/ahos_pg_probe.mjs scripts/windows_g2_probe.py scripts/operator_validation_gate.py app/api/chat/route.ts db/index.ts snapshot.ts deployment/docker-compose.windows.yml tests/validate_n8n.py 2>nul
  if errorlevel 1 (
    echo WARNING: bulk checkout failed - trying core files
    git checkout "!UNLOCK_REF!" -- AHOS_VALIDATE_G2_NOW.bat scripts/windows_validate_g2.ps1 scripts/windows_g2_probe.py scripts/ahos_pg_probe.mjs scripts/windows_diagnose_docker_health.ps1 scripts/windows_ensure_postgres_win.ps1 scripts/windows_ensure_database_url.ps1 scripts/windows_chat_500_forensics.ps1 scripts/windows_ensure_web_api_token.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_restart_next_dev.ps1 scripts/operator_validation_gate.py app/api/chat/route.ts db/index.ts snapshot.ts deployment/docker-compose.windows.yml
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
if "!RC!"=="0" (
  echo ==========================================================
  echo   G2 PASS -- continuing to full G1-G10 via AHOS_PRE_SOAK_NOW
  echo   Still will NOT invent PRE_SOAK/READY without paste evidence
  echo ==========================================================
  if exist "AHOS_PRE_SOAK_NOW.bat" (
    call "AHOS_PRE_SOAK_NOW.bat"
    set "RC=!ERRORLEVEL!"
  ) else if exist "AHOS_WINDOWS_OPS.bat" (
    call "AHOS_WINDOWS_OPS.bat"
    set "RC=!ERRORLEVEL!"
  ) else (
    echo ERROR: missing AHOS_PRE_SOAK_NOW.bat / AHOS_WINDOWS_OPS.bat after unlock
  )
) else (
  echo ==========================================================
  echo   G2 not PASS -- fix health/gateway, then re-run
  echo   Paste reports\OWNER_PASTE_G2_VALIDATE.txt into Cursor
  echo   Never invent OPERATOR_READY / PRE_SOAK
  echo ==========================================================
  pause
)
exit /b !RC!
