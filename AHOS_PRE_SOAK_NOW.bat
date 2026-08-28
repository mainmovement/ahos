@echo off
REM AHOS -- one-click path toward Windows PAPER_ONLY PRE_SOAK entry
REM STATE B: never db:migrate / db:push
REM Does NOT invent PRE_SOAK or OPERATOR_READY (needs OWNER_PASTE evidence)
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS PRE_SOAK NOW (Windows PAPER_ONLY)
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
git fetch origin
git fetch origin cursor/windows-chat-500-rootcause-4bde >nul 2>&1
git fetch origin cursor/windows-g2-evidence-autopush-4bde >nul 2>&1
git fetch origin cursor/windows-evidence-push-lease-4bde >nul 2>&1
git fetch origin cursor/windows-g2-empty-gateway-default-4bde >nul 2>&1
git pull origin main
if errorlevel 1 (
  echo WARNING: git pull origin main failed - continuing with local tree
)

REM Prefer newest unlock tip not yet on main (chat-500, then evidence-autopush)
set "UNLOCK_REF="
for %%R in (
  origin/cursor/windows-chat-500-rootcause-4bde
  origin/cursor/windows-g2-evidence-autopush-4bde
  origin/cursor/windows-g2-empty-gateway-default-4bde
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
  echo ==^> applying unlock tip !UNLOCK_REF! onto working tree ^(not a merge^)
  git checkout "!UNLOCK_REF!" -- AHOS_WINDOWS_OPS.bat AHOS_PRE_SOAK_NOW.bat AHOS_VALIDATE_G2_NOW.bat AHOS_PULL_OPS_UNLOCK.bat WINDOWS_RUN_THIS_FIRST.txt "scripts/windows_*.ps1" scripts/ahos_pg_probe.mjs scripts/operator_validation_gate.py scripts/windows_g2_probe.py app/api/chat/route.ts db/index.ts snapshot.ts tests/validate_n8n.py deployment/docker-compose.windows.yml .env.example 2>nul
  if errorlevel 1 (
    echo WARNING: bulk checkout failed - trying core files individually
    git checkout "!UNLOCK_REF!" -- AHOS_WINDOWS_OPS.bat AHOS_PRE_SOAK_NOW.bat AHOS_VALIDATE_G2_NOW.bat scripts/operator_validation_gate.py scripts/windows_validate_g2.ps1 scripts/windows_g2_probe.py scripts/ahos_pg_probe.mjs scripts/windows_wait_for_web_api.ps1 scripts/windows_ensure_web_api_token.ps1 scripts/windows_ensure_postgres_win.ps1 scripts/windows_ensure_database_url.ps1 scripts/windows_chat_500_forensics.ps1 scripts/windows_diagnose_docker_health.ps1 app/api/chat/route.ts db/index.ts snapshot.ts tests/validate_n8n.py deployment/docker-compose.windows.yml
  )
) else (
  echo ==^> unlock tips already on origin/main -- using main tip
)

if exist "scripts\windows_ensure_web_api_token.ps1" (
  echo ==^> ensure token + AHOS_GATEWAY_URL
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_web_api_token.ps1"
)

if exist "scripts\windows_diagnose_docker_health.ps1" (
  echo ==^> docker health diagnose ^(G2 focus; runtime unhealthy OK^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_diagnose_docker_health.ps1"
  if errorlevel 1 (
    echo WARNING: postgres pg_isready FAIL - ensure-pg will attempt one restart ^(no migrate^)
  )
)

if exist "scripts\windows_ensure_database_url.ps1" (
  echo ==^> ensure DATABASE_URL matches POSTGRES_* ^(no migrate^)
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_database_url.ps1"
  if errorlevel 1 (
    echo WARNING: DATABASE_URL probe failed - OPS bat will retry via ensure-pg
  )
)

if exist "scripts\windows_pre_soak_readiness.ps1" (
  echo ==^> readiness checklist
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_pre_soak_readiness.ps1" -AllowDockerStarting
  if errorlevel 1 (
    echo WARNING: readiness FAILs present.
    echo If Docker daemon is still starting, OPS bat will wait up to ~120s for the engine.
    echo If token/gateway FAIL persisted, fix .env then re-run.
    echo STATE B: do NOT db:migrate / db:push
    echo Continuing into AHOS_WINDOWS_OPS.bat anyway...
  )
)

if not exist "AHOS_WINDOWS_OPS.bat" (
  echo ERROR: missing AHOS_WINDOWS_OPS.bat
  pause
  exit /b 2
)

echo ==^> launching AHOS_WINDOWS_OPS.bat
call "AHOS_WINDOWS_OPS.bat"
set "RC=!ERRORLEVEL!"

echo.
echo ==========================================================
echo   After ops bat: paste reports\OWNER_PASTE_WINDOWS_GATE.txt
echo   PRE_SOAK only if pre_soak_entry_ok=true on that paste
echo   Never invent OPERATOR_READY
echo ==========================================================
exit /b !RC!
