@echo off
REM ============================================================================
REM AHOS Windows Runtime Launcher (double-click runnable)
REM
REM Starts the OFFICIAL local observation daemon:
REM   -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
REM with AHOS_EVIDENCE_SOURCE=local so predictions are calibration-eligible.
REM
REM Without --observation-cycle the E-01 poller and outcome labeler never run,
REM so predictions pile up against zero outcome labels and calibration stays
REM INSUFFICIENT_DATA forever. Without the `local` evidence source the rows are
REM stamped `sandbox` and can never be used for calibration.
REM
REM Observation-only: no trading, no wallet, no order execution.
REM Full soak procedure: AHOS_OPERATOR_QUICKSTART_WINDOWS.md
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

echo ==========================================================
echo   Starting AHOS Continuous Opportunity Intelligence Daemon
echo   Mode           : observation-only (no trading, no wallet)
echo   Evidence source: local (calibration-eligible)
echo   Cycle interval : 60s, with E-01 observation cycle
echo   Press Ctrl+C to stop gracefully.
echo ==========================================================
echo.

"%VENV_PY%" -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local
pause
