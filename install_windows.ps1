# ==============================================================================
# AHOS Windows 11 Automated One-Click Installer
# Powershell Execution Policy: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS (Artificial Hybrid Opportunity Scoring System)" -ForegroundColor Cyan
Write-Host "  Windows 11 Laptop One-Click Installation & Verification" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 1. Check Python 3.11+ Installation
Write-Host "`n[1/7] Checking Python installation..." -ForegroundColor Yellow
try {
    $PythonVersion = python --version 2>&1
    Write-Host "  Found: $PythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python 3.11+ is required. Please install Python from https://python.org and check 'Add Python to PATH'." -ForegroundColor Red
    Exit 1
}

# 2. Check Docker Desktop (Optional but Recommended)
Write-Host "`n[2/7] Checking Docker Desktop status..." -ForegroundColor Yellow
try {
    $DockerVersion = docker --version 2>&1
    Write-Host "  Found: $DockerVersion" -ForegroundColor Green
} catch {
    Write-Host "  NOTE: Docker Desktop is not found. Standalone Python native mode will be used." -ForegroundColor DarkYellow
}

# 3. Create Python Virtual Environment
Write-Host "`n[3/7] Setting up Python virtual environment (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "  Created virtual environment: .venv" -ForegroundColor Green
} else {
    Write-Host "  Existing virtual environment found." -ForegroundColor Green
}

# Activate virtual environment
$VenvPython = "$ScriptDir\.venv\Scripts\python.exe"
$VenvPip = "$ScriptDir\.venv\Scripts\pip.exe"

# 4. Install Dependencies
Write-Host "`n[4/7] Installing required dependencies..." -ForegroundColor Yellow
& $VenvPip install --upgrade pip --quiet
& $VenvPip install -r requirements.txt --quiet
Write-Host "  Dependencies installed successfully." -ForegroundColor Green

# 5. Create Core Directories
Write-Host "`n[5/7] Verifying workspace directories..." -ForegroundColor Yellow
$Directories = @("data", "reports", "config", "logs", "docs", "research\reports")
foreach ($dir in $Directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created directory: $dir" -ForegroundColor Gray
    }
}
Write-Host "  Directories verified." -ForegroundColor Green

# 6. Initialize Environment & Path Configurations
Write-Host "`n[6/7] Initializing cross-platform configuration..." -ForegroundColor Yellow
if (-not (Test-Path "deployment\.env")) {
    Copy-Item "deployment\.env.example" "deployment\.env"
    Write-Host "  Created default deployment\.env template." -ForegroundColor Gray
}
& $VenvPython config/paths.py
Write-Host "  Generated config/paths.yaml for Windows platform." -ForegroundColor Green

# 7. Run Health Check & Self-Test
Write-Host "`n[7/7] Running initial runtime health check..." -ForegroundColor Yellow
& $VenvPython -m architecture.runtime --single-cycle

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows Installation Complete!" -ForegroundColor Green
Write-Host "  To launch the runtime daemon, run: .\start_ahos.ps1" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
