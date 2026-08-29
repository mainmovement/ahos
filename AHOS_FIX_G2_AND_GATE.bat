@echo off
REM AHOS -- surgical fix when last paste was G2 empty-gateway BLOCKED (G3-G10 already PASS)
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM From G:\robat\ahos:
REM   curl.exe -L -o AHOS_FIX_G2_AND_GATE.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_FIX_G2_AND_GATE.bat
REM   AHOS_FIX_G2_AND_GATE.bat
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS FIX G2 empty gateway + full gate (PAPER_ONLY)
echo   Will NOT migrate DB or claim READY
echo ==========================================================

where powershell >nul 2>&1
if errorlevel 1 (
  echo ERROR: powershell not on PATH
  pause
  exit /b 2
)
where git >nul 2>&1
if errorlevel 1 (
  echo ERROR: git not on PATH
  pause
  exit /b 2
)

if not exist "scripts" mkdir "scripts"

set "TIP=cursor/windows-main-evidence-push-4bde"
set "RAW=https://raw.githubusercontent.com/mainmovement/ahos/%TIP%/scripts"

echo ==^> download tip surgical fixer
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%RAW%/windows_fix_g2_empty_and_gate.ps1' -OutFile 'scripts\windows_fix_g2_empty_and_gate.ps1'"
if errorlevel 1 (
  echo ERROR: failed to download windows_fix_g2_empty_and_gate.ps1
  pause
  exit /b 2
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%RAW%/windows_checkout_unlock_tip.ps1' -OutFile 'scripts\windows_checkout_unlock_tip.ps1'" 2>nul

echo ==^> run windows_fix_g2_empty_and_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_fix_g2_empty_and_gate.ps1" -Tip "%TIP%"
set "RC=!ERRORLEVEL!"
echo.
echo Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
pause
exit /b !RC!
