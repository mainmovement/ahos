@echo off
REM ============================================================================
REM AHOS one-click entry point (double-click runnable).
REM
REM Thin delegate: the single source of truth is now the launcher package
REM (launcher\ahos.bat -> python -m launcher start), which boots the full
REM stack in dependency order -- stores, DB backend, gateway, Telegram bot and
REM the observation daemon -- with idempotency, health checks and a Persian
REM progress console. This file exists so existing docs and muscle memory keep
REM working; do not add launch logic here.
REM
REM Observation-only: no trading, no wallet, no order execution. The launcher
REM hard-sets AHOS_PAPER_ONLY=1 and AHOS_EVIDENCE_SOURCE=local for every child,
REM so the daemon's rows stay calibration-eligible.
REM Full soak procedure: AHOS_OPERATOR_QUICKSTART_WINDOWS.md
REM ============================================================================
cd /d "%~dp0"
call "%~dp0launcher\ahos.bat" start
exit /b %ERRORLEVEL%
