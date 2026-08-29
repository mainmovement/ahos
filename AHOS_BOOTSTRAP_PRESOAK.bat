@echo off
REM AHOS -- lowest-friction Windows PRE_SOAK bootstrap (downloadable from tip)
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM From G:\robat\ahos (even if tip files are missing):
REM   curl.exe -L -o AHOS_BOOTSTRAP_PRESOAK.bat https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_BOOTSTRAP_PRESOAK.bat
REM   AHOS_BOOTSTRAP_PRESOAK.bat
REM Or PowerShell:
REM   powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_BOOTSTRAP_PRESOAK.bat' -OutFile 'AHOS_BOOTSTRAP_PRESOAK.bat'"
REM   AHOS_BOOTSTRAP_PRESOAK.bat
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS BOOTSTRAP PRE_SOAK (PAPER_ONLY tip unlock)
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

echo ==^> download tip bootstrap helpers
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%RAW%/windows_bootstrap_presoak.ps1' -OutFile 'scripts\windows_bootstrap_presoak.ps1'"
if errorlevel 1 (
  echo ERROR: failed to download windows_bootstrap_presoak.ps1
  pause
  exit /b 2
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%RAW%/windows_checkout_unlock_tip.ps1' -OutFile 'scripts\windows_checkout_unlock_tip.ps1'"
if errorlevel 1 (
  echo WARNING: checkout helper download failed - bootstrap will use its own ls-tree path
)

echo ==^> run windows_bootstrap_presoak.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\windows_bootstrap_presoak.ps1" -Tip "%TIP%"
set "RC=!ERRORLEVEL!"
echo.
echo Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
exit /b !RC!
