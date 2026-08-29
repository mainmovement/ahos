@echo off
REM ============================================================================
REM AHOS Windows Runtime Launcher (double-click runnable)
REM
REM Starts the OFFICIAL local observation daemon:
REM   -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
REM with AHOS_EVIDENCE_SOURCE=local so predictions are calibration-eligible.
REM
REM Observation-only: no trading, no wallet, no order execution.
REM Full soak procedure: AHOS_OPERATOR_QUICKSTART_WINDOWS.md
REM STATE B: never db:migrate / db:push. Does NOT invent READY.
REM ============================================================================
title AHOS Opportunity Intelligence System
cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo Virtual environment not found. Running installer first...
    powershell -ExecutionPolicy Bypass -File ".\install_windows.ps1"
)

if not exist "%VENV_PY%" (
    echo ERROR: %VENV_PY% still missing after install. Aborting.
    pause
    exit /b 1
)

REM Idempotent: creates the local SQLite stores if they are absent.
"%VENV_PY%" scripts\init_databases.py --with-guards
if errorlevel 1 (
    echo ERROR: database initialization failed. Aborting.
    pause
    exit /b 1
)

REM Calibration-eligible evidence namespace, also passed explicitly below.
set "AHOS_EVIDENCE_SOURCE=local"
set "AHOS_PAPER_ONLY=1"

echo ==========================================================
echo   Starting AHOS Continuous Opportunity Intelligence Daemon
echo   Mode           : observation-only (no trading, no wallet)
echo   Evidence source: local (calibration-eligible)
echo   PAPER_ONLY     : 1
echo   Cycle interval : 60s, with E-01 observation cycle
echo   Press Ctrl+C to stop gracefully.
echo ==========================================================
echo.
echo   WARNING: Not OPERATOR_READY / not PRE_SOAK yet.
echo   BEFORE soak - run MAIN_CLEAR (SHA-pinned .cmd is CRLF-safe):
echo     curl.exe -L -o AHOS_MAIN_CLEAR_G2.cmd https://raw.githubusercontent.com/mainmovement/ahos/c7b3c5e7542051ae6999a7f5607e6b1c31f35e1c/AHOS_MAIN_CLEAR_G2.cmd
echo     AHOS_MAIN_CLEAR_G2.cmd
echo   Or: AHOS_RUN_TIP.cmd from tip branch (also CRLF-safe).
echo   Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38.
echo   Keep #56 OPEN. Merge #58. PRE_SOAK only if pre_soak_entry_ok=true.
echo   STATE B: no db:migrate / db:push.
echo.

"%VENV_PY%" -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local
pause
