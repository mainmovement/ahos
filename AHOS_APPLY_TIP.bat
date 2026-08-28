@echo off
REM AHOS -- apply newest unlock tip onto working tree, then PRE_SOAK path
REM Use when tip PR is not yet merged to main.
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM Bootstrap (from repo root) if this file is missing:
REM   powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-evidence-notify-retarget-4bde/AHOS_APPLY_TIP.bat' -OutFile 'AHOS_APPLY_TIP.bat'"
REM   AHOS_APPLY_TIP.bat
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS APPLY TIP then PRE_SOAK (PAPER_ONLY)
echo   Will NOT migrate DB or claim READY
echo ==========================================================

where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

set "TIP=cursor/windows-evidence-notify-retarget-4bde"

echo ==^> git fetch origin main + %TIP%
git fetch origin main
if errorlevel 1 echo WARNING: fetch main failed - continuing
git fetch origin %TIP%
if errorlevel 1 (
  echo ERROR: git fetch tip failed - check network / remotes
  pause
  exit /b 2
)

echo ==^> checkout unlock files from origin/%TIP% ^(overwrites listed unlock files only^)
git checkout "origin/%TIP%" -- AHOS_APPLY_TIP.bat AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat AHOS_VALIDATE_G2_NOW.bat AHOS_PULL_OPS_UNLOCK.bat AHOS_PUSH_EVIDENCE_NOW.bat WINDOWS_RUN_THIS_FIRST.txt "scripts/windows_*.ps1" scripts/ahos_pg_probe.mjs scripts/windows_g2_probe.py scripts/operator_validation_gate.py app/api/chat/route.ts db/index.ts snapshot.ts tests/validate_n8n.py deployment/docker-compose.windows.yml .env.example
if errorlevel 1 (
  echo WARNING: bulk checkout failed - trying core files
  git checkout "origin/%TIP%" -- AHOS_APPLY_TIP.bat AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat AHOS_VALIDATE_G2_NOW.bat AHOS_PUSH_EVIDENCE_NOW.bat scripts/operator_validation_gate.py scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_database_url.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 app/api/chat/route.ts
  if errorlevel 1 (
    echo ERROR: checkout tip files failed
    pause
    exit /b 2
  )
)

echo OK -- tip files applied from origin/%TIP%
echo ==^> launching AHOS_PRE_SOAK_NOW.bat
if not exist "AHOS_PRE_SOAK_NOW.bat" (
  echo ERROR: AHOS_PRE_SOAK_NOW.bat missing after tip checkout
  pause
  exit /b 2
)
call "AHOS_PRE_SOAK_NOW.bat"
set "RC=!ERRORLEVEL!"
echo.
echo Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38
echo Or run AHOS_PUSH_EVIDENCE_NOW.bat
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
exit /b !RC!
