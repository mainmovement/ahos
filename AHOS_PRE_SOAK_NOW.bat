@echo off
REM AHOS -- one-click path toward Windows PAPER_ONLY PRE_SOAK entry
REM Delegates to AHOS_G2_CLEAR_MAIN.cmd (empty-gateway clear + gate + #56/#60 wake).
REM STATE B: never db:migrate / db:push
REM Does NOT invent PRE_SOAK or OPERATOR_READY
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==========================================================
echo   AHOS PRE_SOAK NOW -^> G2_CLEAR_MAIN
echo   Will NOT migrate DB or claim READY
echo ==========================================================

if not exist "AHOS_G2_CLEAR_MAIN.cmd" (
  echo ==^> downloading AHOS_G2_CLEAR_MAIN.cmd from unlock tip
  curl.exe -L -o AHOS_G2_CLEAR_MAIN.cmd https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-ops-evidence-push-main-4bde/AHOS_G2_CLEAR_MAIN.cmd
  if errorlevel 1 (
    echo ERROR: could not download AHOS_G2_CLEAR_MAIN.cmd
    pause
    exit /b 2
  )
)

call AHOS_G2_CLEAR_MAIN.cmd
exit /b %ERRORLEVEL%
