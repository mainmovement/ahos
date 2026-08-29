@echo off
REM AHOS -- double-click / curl-safe tip runner (CRLF; PAPER_ONLY)
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM
REM Prefer downloading THIS .cmd (CRLF in git blob) then double-click:
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
echo Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38
echo PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY.
pause
exit /b %RC%
