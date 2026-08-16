# ==============================================================================
# AHOS Windows 11 Runtime Launcher (Double-Click Runnable)
# ==============================================================================

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$VenvPython = "$ScriptDir\.venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Virtual environment not found. Running installer first..." -ForegroundColor Yellow
    & ".\install_windows.ps1"
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting AHOS Continuous Opportunity Intelligence Daemon" -ForegroundColor Cyan
Write-Host "  Press Ctrl+C to stop gracefully." -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

# Launch continuous runtime daemon with 60-second cycle interval
& $VenvPython -m architecture.runtime --daemon --interval-sec 60
