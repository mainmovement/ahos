@echo off
REM AHOS -- apply newest unlock tip onto working tree, then PRE_SOAK path
REM Use when tip PR is not yet merged to main.
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM Bootstrap (from repo root) if this file is missing:
REM   powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_APPLY_TIP.bat' -OutFile 'AHOS_APPLY_TIP.bat'"
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

set "TIP=cursor/windows-main-evidence-push-4bde"

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
REM Avoid scripts/windows_*.ps1 pathspec glob ^(unreliable on Windows Git^).
git checkout "origin/%TIP%" -- scripts/windows_checkout_unlock_tip.ps1
if exist "scripts\windows_checkout_unlock_tip.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_checkout_unlock_tip.ps1" -Ref "origin/%TIP%"
  if errorlevel 1 (
    echo ERROR: unlock tip helper failed
    pause
    exit /b 2
  )
) else (
  echo WARNING: checkout helper missing - applying explicit core set
  git checkout "origin/%TIP%" -- AHOS_APPLY_TIP.bat AHOS_BOOTSTRAP_PRESOAK.bat AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat AHOS_VALIDATE_G2_NOW.bat AHOS_PUSH_EVIDENCE_NOW.bat scripts/windows_bootstrap_presoak.ps1 scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_database_url.ps1 scripts/windows_ensure_postgres_win.ps1 scripts/windows_ensure_web_api_token.ps1 scripts/windows_wait_for_web_api.ps1 scripts/windows_restart_next_dev.ps1 scripts/windows_chat_500_forensics.ps1 scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 scripts/windows_run_operator_gate.ps1 scripts/windows_validate_g2.ps1 scripts/windows_post_merge_reconcile.ps1 scripts/operator_validation_gate.py scripts/windows_g2_probe.py scripts/ahos_pg_probe.mjs app/api/chat/route.ts db/index.ts snapshot.ts
  if errorlevel 1 (
    echo ERROR: checkout tip core files failed
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
if not exist "scripts\windows_ensure_database_url.ps1" (
  echo ERROR: windows_ensure_database_url.ps1 missing after tip checkout
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
