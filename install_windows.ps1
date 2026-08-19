# ==============================================================================
# AHOS Windows 10/11 native installer (Python 3.11+, observation/paper only)
# Run from PowerShell:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\install_windows.ps1
# ==============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function Stop-OnNativeFailure([string]$Step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows native installation and verification" -ForegroundColor Cyan
Write-Host "  Observation + paper mode only; no live execution" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

# Locate an interpreter that proves it is Python >=3.11. `py -3.11` is tried
# first because it bypasses the Windows Store `python.exe` alias.
$PythonCommand = $null
$PythonPrefix = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonCommand = "py"
        $PythonPrefix = @("-3.11")
    }
}
if (-not $PythonCommand -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonCommand = "python"
    }
}
if (-not $PythonCommand) {
    Write-Host "ERROR: CPython 3.11+ was not found." -ForegroundColor Red
    Write-Host "Install it from https://www.python.org/downloads/windows/ and enable the Python launcher." -ForegroundColor Yellow
    exit 1
}
$Version = & $PythonCommand @PythonPrefix --version 2>&1
Write-Host "[1/7] Found $Version" -ForegroundColor Green

Write-Host "[2/7] Creating isolated .venv..." -ForegroundColor Yellow
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $PythonCommand @PythonPrefix -m venv .venv
    Stop-OnNativeFailure "virtual environment creation"
}
$VenvPython = "$ScriptDir\.venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment interpreter was not created: $VenvPython"
}

Write-Host "[3/7] Installing declared dependencies..." -ForegroundColor Yellow
$PipArgs = @("-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt")
if ($env:AHOS_WHEELHOUSE) {
    $PipArgs += @("--no-index", "--find-links", $env:AHOS_WHEELHOUSE)
    Write-Host "  Offline wheelhouse: $env:AHOS_WHEELHOUSE" -ForegroundColor DarkGray
}
& $VenvPython @PipArgs
Stop-OnNativeFailure "dependency installation"

Write-Host "[4/7] Preparing local configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  Created .env. Add TELEGRAM_BOT_TOKEN only if you want the bot." -ForegroundColor DarkYellow
}
& $VenvPython config\paths.py
Stop-OnNativeFailure "path snapshot generation"

Write-Host "[5/7] Initializing versioned SQLite schemas..." -ForegroundColor Yellow
& $VenvPython scripts\init_databases.py --with-guards
Stop-OnNativeFailure "database initialization"

Write-Host "[6/7] Running offline import and configuration checks..." -ForegroundColor Yellow
& $VenvPython -B -c "from config.paths import get_project_root; from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator; from telegram_ai.service import TelegramDomainService; assert get_project_root().is_dir(); print('AHOS imports: OK')"
Stop-OnNativeFailure "import smoke test"
& $VenvPython tests\validate_n8n.py
Stop-OnNativeFailure "n8n static validation"

Write-Host "[7/7] Checking optional tools..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker --version
    Write-Host "  Docker is available (optional)." -ForegroundColor Green
} else {
    Write-Host "  Docker Desktop not found; native Python mode is fully supported." -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Installation complete" -ForegroundColor Green
Write-Host "  1. Edit .env (optional Telegram/proxy/provider settings)" -ForegroundColor Cyan
Write-Host "  2. Run .\start_ahos.ps1" -ForegroundColor Cyan
Write-Host "  3. For an official soak, follow AHOS_OPERATOR_QUICKSTART_WINDOWS.md" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
