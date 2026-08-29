# ==============================================================================
# AHOS Windows 11 Runtime Launcher (Double-Click Runnable)
#
# Starts the OFFICIAL local observation daemon:
#   python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
# with AHOS_EVIDENCE_SOURCE=local, so predictions are calibration-eligible.
#
# WHY BOTH PARTS MATTER (Phase 17 audit finding):
#   --observation-cycle  registers the E-01 observation task. Without it the
#                        daemon runs scoring only: the frozen Lane-A poller and
#                        the outcome labeler never run, predictions accumulate
#                        against ZERO outcome labels, and calibration stays
#                        INSUFFICIENT_DATA forever no matter how long it runs.
#   evidence source      only rows stamped `local` are calibration-eligible.
#                        The runtime default is `sandbox` (opt-in by design), so
#                        a launcher that does not declare `local` produces a
#                        healthy-looking daemon whose output can never be used.
#
# Observation-only. No trading, no wallet, no order execution.
# For the full 168-hour soak procedure see AHOS_OPERATOR_QUICKSTART_WINDOWS.md.
# ==============================================================================

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = "$ScriptDir\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Virtual environment not found. Running installer first..." -ForegroundColor Yellow
    & ".\install_windows.ps1"
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: $VenvPython still missing after install. Aborting." -ForegroundColor Red
    exit 1
}

# Ensure the local SQLite stores exist before the daemon touches them.
# Idempotent: a no-op when they are already present.
& $VenvPython scripts\init_databases.py --with-guards
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: database initialization failed (exit $LASTEXITCODE). Aborting." -ForegroundColor Red
    exit $LASTEXITCODE
}

# Calibration-eligible evidence namespace. Exported for this process tree AND
# passed explicitly below, so the namespace is unambiguous either way.
$env:AHOS_EVIDENCE_SOURCE = "local"
$env:AHOS_PAPER_ONLY = "1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AHOS Continuous Opportunity Intelligence Daemon" -ForegroundColor Cyan
Write-Host "  Mode           : observation-only (no trading, no wallet)" -ForegroundColor DarkGray
Write-Host "  Evidence source: local (calibration-eligible)" -ForegroundColor DarkGray
Write-Host "  PAPER_ONLY     : 1 (mandatory)" -ForegroundColor DarkGray
Write-Host "  Cycle interval : 60s, with E-01 observation cycle" -ForegroundColor DarkGray
Write-Host "  Press Ctrl+C to stop gracefully." -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  WARNING: Do NOT treat this as OPERATOR_READY." -ForegroundColor DarkYellow
Write-Host "  BEFORE soak: run AHOS_RUN_TIP.ps1 (or AHOS_MAIN_FIRST.bat after tip checkout)" -ForegroundColor Yellow
Write-Host "  Prefer: powershell -NoProfile -ExecutionPolicy Bypass -File .\AHOS_RUN_TIP.ps1" -ForegroundColor Yellow
Write-Host "  Do NOT curl .bat from raw GitHub (LF breaks cmd.exe)." -ForegroundColor Yellow
Write-Host "  Paste reports\OWNER_PASTE_WINDOWS_GATE.txt into Cursor / PR #56." -ForegroundColor Yellow
Write-Host "  PRE_SOAK only after summary.pre_soak_entry_ok == true." -ForegroundColor DarkYellow
Write-Host "  Need AHOS_WEB_API_TOKEN in .env; STATE B = no db:migrate/db:push." -ForegroundColor DarkYellow
Write-Host ""

# Launch the continuous runtime daemon.
& $VenvPython -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local
exit $LASTEXITCODE
