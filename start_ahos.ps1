# ==============================================================================
# AHOS one-click entry point (double-click runnable).
#
# Thin delegate: the single source of truth is now the launcher package
# (launcher\ahos.ps1 -> python -m launcher start), which boots the full stack
# in dependency order -- stores, DB backend, gateway, Telegram bot and the
# observation daemon -- with idempotency, health checks and a Persian progress
# console. This file exists so existing docs and muscle memory keep working;
# do not add launch logic here.
#
# Observation-only: no trading, no wallet, no order execution. The launcher
# hard-sets AHOS_PAPER_ONLY=1 and AHOS_EVIDENCE_SOURCE=local for every child,
# so the daemon's rows stay calibration-eligible (never `sandbox`).
# Full soak procedure: AHOS_OPERATOR_QUICKSTART_WINDOWS.md
# ==============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

& (Join-Path $ScriptDir 'launcher\ahos.ps1') -Action start
exit $LASTEXITCODE
