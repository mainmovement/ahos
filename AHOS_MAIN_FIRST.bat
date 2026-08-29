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
git pull origin main
if errorlevel 1 (
  echo WARNING: git pull origin main failed - continuing with local tree
)

REM Best-effort: tip notify scripts so evidence push hits open #56/#38 (not merged inboxes).
git fetch origin cursor/windows-main-evidence-push-4bde cursor/windows-evidence-notify-retarget-4bde >nul 2>&1
git checkout "origin/cursor/windows-main-evidence-push-4bde" -- scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 scripts/windows_publish_owner_paste.ps1 AHOS_PUSH_EVIDENCE_NOW.bat 2>nul
if errorlevel 1 git checkout "origin/cursor/windows-evidence-notify-retarget-4bde" -- scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 scripts/windows_publish_owner_paste.ps1 AHOS_PUSH_EVIDENCE_NOW.bat 2>nul

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

echo ==^> launching AHOS_PRE_SOAK_NOW.bat
call "AHOS_PRE_SOAK_NOW.bat"
set "RC=!ERRORLEVEL!"

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
echo If still blocked, run tip surgical AHOS_FIX_G2_AND_GATE.bat from PR #57
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
exit /b !RC!
