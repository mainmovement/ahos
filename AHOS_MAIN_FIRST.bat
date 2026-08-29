@echo off
REM AHOS -- main-first PRE_SOAK (empty-gateway fix already on main #45)
REM Use when last paste was G2 empty AHOS_GATEWAY_URL BLOCKED with G3-G10 PASS.
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM From G:\robat\ahos (or download this bat from tip raw URL):
REM   curl.exe -L -o AHOS_MAIN_FIRST.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_MAIN_FIRST.bat
REM   AHOS_MAIN_FIRST.bat
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS MAIN FIRST -- empty-gateway unlock (PAPER_ONLY)
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
    echo ERROR: powershell not found
    pause
    exit /b 2
  )
)

echo ==^> git fetch / pull origin main
git fetch origin main
if defined AHOS_SKIP_GIT_PULL (
  echo ==^> skip git pull ^(MAIN_FIRST tip overlay active^)
) else (
  git pull origin main
  if errorlevel 1 (
    echo WARNING: git pull origin main failed - continuing with local tree
  )
)

REM Tip overlay: main OPS historically wrote OWNER_PASTE then exited without
REM pushing evidence (agents never woke). Overlay OPS + notify scripts from tip
REM before PRE_SOAK so mid-run and end-of-run both push to #56/#38.
REM Named files only (Windows Git pathspec globs for scripts/windows_*.ps1 fail).
git fetch origin cursor/windows-main-evidence-push-4bde cursor/windows-evidence-notify-retarget-4bde >nul 2>&1
set "TIPREF=origin/cursor/windows-main-evidence-push-4bde"
git rev-parse --verify "%TIPREF%" >nul 2>&1
if errorlevel 1 set "TIPREF=origin/cursor/windows-evidence-notify-retarget-4bde"
echo ==^> overlay tip %TIPREF% OPS + evidence notify ^(named files^)
git checkout "%TIPREF%" -- AHOS_WINDOWS_OPS.bat AHOS_PUSH_EVIDENCE_NOW.bat scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 scripts/windows_publish_owner_paste.ps1 scripts/windows_run_operator_gate.ps1 scripts/windows_ensure_web_api_token.ps1 2>nul
if errorlevel 1 (
  echo WARNING: tip overlay checkout failed - MAIN_FIRST end push may still wake agents
)

if exist "scripts\windows_ensure_web_api_token.ps1" (
  echo ==^> scrub empty AHOS_GATEWAY_URL + ensure token
  "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_ensure_web_api_token.ps1"
) else (
  echo ERROR: windows_ensure_web_api_token.ps1 missing - pull main first
  pause
  exit /b 2
)

if not exist "AHOS_PRE_SOAK_NOW.bat" (
  echo ERROR: AHOS_PRE_SOAK_NOW.bat missing
  pause
  exit /b 2
)

echo ==^> launching AHOS_PRE_SOAK_NOW.bat ^(skip nested pull^)
set "AHOS_SKIP_GIT_PULL=1"
call "AHOS_PRE_SOAK_NOW.bat"
set "RC=!ERRORLEVEL!"
set "AHOS_SKIP_GIT_PULL="

REM Re-apply tip OPS after PRE_SOAK (it may reset to main when unlock tips are ancestors).
git checkout "%TIPREF%" -- AHOS_WINDOWS_OPS.bat scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 2>nul

REM Belt-and-suspenders evidence push (avoid AHOS_PUSH_EVIDENCE_NOW.bat pause).
if exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  echo ==^> belt-and-suspenders evidence push + PR notify
  if exist "scripts\windows_post_gate_paste_gh.ps1" (
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_post_gate_paste_gh.ps1" -BodyFile "reports\OWNER_PASTE_WINDOWS_GATE.txt"
  )
  if exist "scripts\windows_push_gate_evidence.ps1" (
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_push_gate_evidence.ps1"
  )
)

echo.
echo Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38
echo Or Desktop AHOS_PASTE_TO_CURSOR.txt if present
echo If still blocked, run tip surgical AHOS_FIX_G2_AND_GATE.bat from PR #58
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
exit /b !RC!
