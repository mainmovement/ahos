# ==============================================================================
# AHOS Windows 11 One-Click Installer (Double-Click Runnable)
#
# Operator prep ONLY. This script does NOT claim OPERATOR_READY and does NOT
# start PRE_SOAK / soak. After install, run the Windows operator gate yourself:
#   docs\WINDOWS_OPERATOR_HANDOFF.md
#   python scripts\operator_validation_gate.py --platform windows ...
#
# Encoding / quoting contract (Windows PowerShell 5.1 + PowerShell 7):
#   - ASCII-only punctuation in this file (no em-dash, no >= glyph)
#   - Python -c payloads use SINGLE-QUOTED PowerShell strings so () is not
#     parsed as a PowerShell subexpression (ParserError on Windows 5.1)
#   - Python -c payloads must contain NO double-quote characters: WinPS 5.1
#     strips embedded " when calling native python.exe, which turned
#     print("%d.%d.%d" % ...) into print(%d.%d.%d % ...) (SyntaxError)
#   - Do NOT import third-party dotenv / config.runtime_env: requirements.txt
#     has no python-dotenv; canonical load is run_bot.load_dotenv and
#     canonical assert is architecture.security.assert_safe_environment
# ==============================================================================

param(
    # Optional: run one observation single-cycle after install to seed local
    # evidence. Default OFF - install must stay conservative and honest.
    [switch]$SeedEvidence
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host ("==> " + $Message) -ForegroundColor Cyan
}

function Assert-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw ("Required command not found on PATH: " + $Name)
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows Installer - operator prep (not readiness)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  This installer prepares a PAPER_ONLY local host." -ForegroundColor DarkGray
Write-Host "  It does NOT set OPERATOR_READY and does NOT start PRE_SOAK." -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

# ------------------------------------------------------------------------------
# 1) Toolchain: Python 3.11+ and Node/npm
# ------------------------------------------------------------------------------
Write-Step "Checking Python 3.11+ and Node/npm"

Assert-Command "python"
Assert-Command "npm"
Assert-Command "node"

# Quote-free -c payload: WinPS 5.1 strips embedded " when invoking python.exe.
$pyVerRaw = & python -c 'import sys; print(sys.version.split()[0])'
if ($LASTEXITCODE -ne 0) {
    throw "python failed while reporting version"
}
$pyParts = $pyVerRaw.Trim().Split(".")
$pyMajor = [int]$pyParts[0]
$pyMinor = [int]$pyParts[1]
if (($pyMajor -lt 3) -or (($pyMajor -eq 3) -and ($pyMinor -lt 11))) {
    throw ("Python 3.11+ required; found " + $pyVerRaw.Trim())
}
Write-Host ("  Python OK: " + $pyVerRaw.Trim()) -ForegroundColor Green
Write-Host ("  Node   OK: " + ((& node --version) | Out-String).Trim()) -ForegroundColor Green
Write-Host ("  npm    OK: " + ((& npm --version) | Out-String).Trim()) -ForegroundColor Green

# ------------------------------------------------------------------------------
# 2) Python venv + requirements.txt
# ------------------------------------------------------------------------------
Write-Step "Creating/updating .venv and installing requirements.txt"

$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "python -m venv .venv failed" }
}

& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }

& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "pip install -r requirements.txt failed" }
Write-Host "  Python dependencies installed." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 3) Node dependencies (n8n structural / gateway tooling)
# ------------------------------------------------------------------------------
Write-Step "Installing npm dependencies (npm install)"
& npm install
if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
Write-Host "  npm dependencies installed." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 4) Root .env from .env.example (never overwrite an existing .env)
# ------------------------------------------------------------------------------
Write-Step "Ensuring root .env exists (from .env.example if needed)"

$EnvPath = Join-Path $ScriptDir ".env"
$EnvExample = Join-Path $ScriptDir ".env.example"
if (-not (Test-Path $EnvExample)) {
    throw ".env.example is missing - cannot bootstrap operator env"
}
if (-not (Test-Path $EnvPath)) {
    Copy-Item -Path $EnvExample -Destination $EnvPath
    Write-Host "  Created .env from .env.example (edit secrets before live providers)." -ForegroundColor Yellow
} else {
    Write-Host "  Existing .env left unchanged." -ForegroundColor Green
}
Write-Host "  Note: deployment\.env is NOT the operator runtime env for this host." -ForegroundColor DarkGray

# ------------------------------------------------------------------------------
# 5) Force PAPER_ONLY and verify safety assert (no fake provider PASS)
# ------------------------------------------------------------------------------
Write-Step "Enforcing AHOS_PAPER_ONLY=1 and running assert_safe_environment"

$env:AHOS_PAPER_ONLY = "1"
# Canonical AHOS path (no python-dotenv): load root .env then security assert.
# SINGLE-QUOTED -c payload: Windows PowerShell must not parse Python () as PS.
# Quote-free payload: WinPS 5.1 strips embedded " when invoking python.exe.
& $VenvPython -c 'from run_bot import load_dotenv; load_dotenv(); from architecture.security import assert_safe_environment; print(assert_safe_environment())'
if ($LASTEXITCODE -ne 0) {
    throw "assert_safe_environment failed - fix .env / PAPER_ONLY before continuing"
}
Write-Host "  Safety assert OK (PAPER_ONLY enforced)." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 6) Explicit Postgres / DATABASE_URL reminder (G2 remains blocked without it)
# ------------------------------------------------------------------------------
Write-Step "DATABASE_URL / Postgres reminder (required for G2 gateway)"

$dbUrl = $env:DATABASE_URL
if (-not $dbUrl) {
    # Best-effort read from .env without claiming the gateway is ready.
    $line = Get-Content $EnvPath -ErrorAction SilentlyContinue |
        Where-Object { $_ -match '^\s*DATABASE_URL\s*=' } |
        Select-Object -First 1
    if ($line) {
        $dbUrl = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    }
}

if (-not $dbUrl -or $dbUrl -match 'CHANGE_ME|your-password|example\.com|localhost:5432\/ahos(\s|$)' ) {
    Write-Host "  WARNING: DATABASE_URL is missing or still a placeholder." -ForegroundColor Yellow
    Write-Host "  G2 (gateway POST /api/chat) REQUIRES a reachable Postgres DATABASE_URL." -ForegroundColor Yellow
    Write-Host "  Edit .env, start Postgres, then re-run the operator gate." -ForegroundColor Yellow
    Write-Host "  Installer continues (SQLite init still needed); G2 will FAIL until fixed." -ForegroundColor Yellow
} else {
    Write-Host "  DATABASE_URL is set in the environment or .env (operator must still verify reachability)." -ForegroundColor Green
}

# ------------------------------------------------------------------------------
# 7) Initialize local SQLite stores (guarded; never invents readiness)
# ------------------------------------------------------------------------------
Write-Step "Initializing local SQLite databases (scripts\init_databases.py --with-guards)"
& $VenvPython scripts\init_databases.py --with-guards
if ($LASTEXITCODE -ne 0) {
    throw ("init_databases.py --with-guards failed with exit " + $LASTEXITCODE)
}
Write-Host "  Local SQLite stores ready (or already present)." -ForegroundColor Green

# ------------------------------------------------------------------------------
# 8) Optional evidence seed (OFF by default) - never auto PRE_SOAK / never ready
# ------------------------------------------------------------------------------
if ($SeedEvidence) {
    Write-Step "Optional -SeedEvidence: one observation single-cycle (local evidence)"
    $env:AHOS_EVIDENCE_SOURCE = "local"
    & $VenvPython -m architecture.runtime --once --observation-cycle --evidence-source local
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("  WARNING: single-cycle exited " + $LASTEXITCODE + " - diagnose honestly; do not claim PASS.") -ForegroundColor Yellow
    } else {
        Write-Host "  Single-cycle completed (still NOT OPERATOR_READY)." -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "  Skipping live single-cycle (default). Use -SeedEvidence only if you want local evidence seed." -ForegroundColor DarkGray
}

# ------------------------------------------------------------------------------
# 9) Explicit next step: Windows operator gate (NOT auto-run)
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Install prep finished. OPERATOR_READY remains NOT_VERIFIED." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT (required - not started by this installer):" -ForegroundColor Cyan
Write-Host "  1. Edit .env: API keys, Telegram, and a real DATABASE_URL (Postgres for G2)." -ForegroundColor White
Write-Host "  2. Start Postgres and ensure the gateway can reach DATABASE_URL." -ForegroundColor White
Write-Host "  3. Follow docs\WINDOWS_OPERATOR_HANDOFF.md" -ForegroundColor White
Write-Host "  4. Run the Windows operator gate, for example:" -ForegroundColor White
Write-Host ""
Write-Host "     .\.venv\Scripts\python.exe scripts\operator_validation_gate.py ``" -ForegroundColor Yellow
Write-Host "       --platform windows ``" -ForegroundColor Yellow
Write-Host "       --repo-root . ``" -ForegroundColor Yellow
Write-Host "       --out reports\operator_validation_windows.json ``" -ForegroundColor Yellow
Write-Host "       --require-owner-action" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Do NOT claim OPERATOR_READY until that gate reports it on Windows." -ForegroundColor Yellow
Write-Host "  Do NOT start PRE_SOAK until summary.pre_soak_entry_ok == true." -ForegroundColor Yellow
Write-Host "  PAPER_ONLY remains mandatory. No live trading." -ForegroundColor Yellow
Write-Host ""
