@echo off
REM AHOS -- double-click / curl-safe tip runner (CRLF; PAPER_ONLY)
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM   curl.exe -L -o AHOS_RUN_TIP.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.cmd
REM   AHOS_RUN_TIP.cmd
setlocal EnableExtensions
cd /d "%~dp0"

where powershell >nul 2>&1
if errorlevel 1 (
  echo ERROR: powershell not on PATH
  pause
  exit /b 2
)

echo ==^> AHOS_RUN_TIP via PowerShell ^(TLS1.2 + Bypass^)
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex (iwr -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.ps1').Content"
set "RC=%ERRORLEVEL%"
echo.
echo ==========================================================
echo   NEXT: paste OWNER_PASTE into GitHub PR #56 or #38
echo   Leave PR #56 OPEN. Merge PR #58 when ready.
echo   PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
echo ==========================================================
if exist "reports\OWNER_PASTE_WINDOWS_GATE.txt" (
  echo OWNER_PASTE: %CD%\reports\OWNER_PASTE_WINDOWS_GATE.txt
) else (
  echo OWNER_PASTE missing - scroll console for errors
)
if exist "%USERPROFILE%\Desktop\AHOS_PASTE_TO_CURSOR.txt" (
  echo Desktop copy: %USERPROFILE%\Desktop\AHOS_PASTE_TO_CURSOR.txt
)
if exist "reports\PRE_SOAK_STATUS.txt" (
  echo ---- PRE_SOAK_STATUS ----
  type "reports\PRE_SOAK_STATUS.txt"
)
echo.
pause
exit /b %RC%
