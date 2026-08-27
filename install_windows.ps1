# ==============================================================================
# AHOS Windows Installer / Activation (canonical transfer path)
#
# Aligns with: docs/WINDOWS_OPERATOR_HANDOFF.md
#              docs/OPERATOR_VALIDATION_PROTOCOL.md
#
# This script prepares the laptop for Operator Validation.
# It does NOT:
#   - claim OPERATOR_READY or PRODUCTION_READY
#   - run live provider probes (unless -SeedEvidence)
#   - start PRE_SOAK / the ≥72h daemon
#   - invent gateway/provider/Telegram/calibration evidence
#   - modify Lane-A frozen sources
#   - overwrite an existing .env
#
# Usage (PowerShell, repo root):
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\install_windows.ps1
#   .\install_windows.ps1 -SeedEvidence   # optional: one paper single-cycle
#
# Next step after success:
#   docs\WINDOWS_OPERATOR_HANDOFF.md  (G2 gateway + operator_validation_gate)
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$SeedEvidence,
    [switch]$SkipNpm
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Msg) {
    Write-Host "`n$Msg" -ForegroundColor Yellow
}
function Write-Ok([string]$Msg) {
    Write-Host "  $Msg" -ForegroundColor Green
}
function Write-Warn([string]$Msg) {
    Write-Host "  $Msg" -ForegroundColor DarkYellow
}
function Write-Err([string]$Msg) {
    Write-Host "  ERROR: $Msg" -ForegroundColor Red
}
function Require-Cmd([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        # Windows often exposes npm as npm.cmd
        $cmd = Get-Command "$Name.cmd" -ErrorAction SilentlyContinue
    }
    if (-not $cmd) {
        Write-Err "$Name not found on PATH."
        exit 1
    }
    return $cmd.Source
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows Installer (Operator Validation prep)" -ForegroundColor Cyan
Write-Host "  Classification : INTEGRATION_READY (agent-host)" -ForegroundColor DarkGray
Write-Host "  OPERATOR_READY : NOT_VERIFIED (this script never changes that)" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ---- 1) Platform + tool versions -------------------------------------------
Write-Step "[1/9] Verifying Windows + Python + Node/npm..."
if ($env:OS -ne "Windows_NT") {
    Write-Warn "OS env is not Windows_NT; continuing (cross-host dry run)."
}

try {
    $pyVerOut = & python --version 2>&1
    Write-Ok "Python: $pyVerOut"
} catch {
    Write-Err "Python 3.11+ required. Install from https://python.org (Add to PATH)."
    exit 1
}

$pyCheck = & python -c "import sys; print(sys.version_info[:2] >= (3,11))"
if ($pyCheck.Trim() -ne "True") {
    Write-Err "Python 3.11+ required (found: $pyVerOut)."
    exit 1
}

$nodePath = Require-Cmd "node"
$npmPath = Require-Cmd "npm"
$nodeVer = & node --version 2>&1
$npmVer = & npm --version 2>&1
Write-Ok "Node: $nodeVer ($nodePath)"
Write-Ok "npm:  $npmVer ($npmPath)"

# ---- 2) Virtualenv ---------------------------------------------------------
Write-Step "[2/9] Creating/reusing .venv..."
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$VenvPip = Join-Path $ScriptDir ".venv\Scripts\pip.exe"
if (-not (Test-Path $VenvPython)) {
    & python -m venv .venv
    Write-Ok "Created .venv"
} else {
    Write-Ok "Existing .venv reused"
}
if (-not (Test-Path $VenvPython)) {
    Write-Err ".venv\Scripts\python.exe missing after venv create."
    exit 1
}

# ---- 3) Python deps --------------------------------------------------------
Write-Step "[3/9] Installing Python requirements..."
if (-not (Test-Path "requirements.txt")) {
    Write-Err "requirements.txt missing."
    exit 1
}
& $VenvPython -m pip install -U pip
& $VenvPython -m pip install -r requirements.txt
Write-Ok "requirements.txt installed (no editable install; no pyproject.toml)"

# ---- 4) Node deps (One-Brain / G2) -----------------------------------------
Write-Step "[4/9] Installing Node dependencies (npm install)..."
if ($SkipNpm) {
    Write-Warn "Skipped (-SkipNpm). G2 / npm run dev will fail until you run: npm install"
} else {
    if (-not (Test-Path "package.json")) {
        Write-Err "package.json missing."
        exit 1
    }
    # Prefer npm.cmd resolution via Require-Cmd above; call through cmd for .cmd safety
    & npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Err "npm install failed (exit $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
    Write-Ok "npm install complete"
}

# ---- 5) Directories --------------------------------------------------------
Write-Step "[5/9] Ensuring workspace directories..."
foreach ($dir in @("data", "reports", "logs", "research\reports")) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Ok "Created $dir"
    }
}
Write-Ok "Directories ready (SQLite DBs are gitignored runtime state)"

# ---- 6) Canonical env contract (root .env — never overwrite) ---------------
Write-Step "[6/9] Establishing PAPER_ONLY / env contract..."
$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"
Write-Ok "Process env: AHOS_PAPER_ONLY=1, AHOS_EVIDENCE_SOURCE=local"

$RootEnv = Join-Path $ScriptDir ".env"
$RootEnvExample = Join-Path $ScriptDir ".env.example"
if (-not (Test-Path $RootEnvExample)) {
    Write-Err ".env.example missing (canonical operator template)."
    exit 1
}
if (-not (Test-Path $RootEnv)) {
    Copy-Item $RootEnvExample $RootEnv
    Write-Ok "Created .env from .env.example (gitignored; fill secrets locally)"
    Write-Warn "Edit .env: set DATABASE_URL for G2 (Postgres) before npm run dev."
    Write-Warn "Do NOT commit .env."
} else {
    Write-Ok "Existing .env left untouched (never overwritten by installer)"
}

# deployment\.env is NOT the One-Brain / operator canonical path.
if (Test-Path "deployment\.env.example") {
    Write-Warn "Note: deployment\.env.example is a deployment template — operator runtime uses root .env"
}

# Validate PAPER_ONLY cannot be explicitly disabled in process (security module).
& $VenvPython -c "from architecture.security import assert_safe_environment; print(assert_safe_environment())"
if ($LASTEXITCODE -ne 0) {
    Write-Err "Security assert_safe_environment failed."
    exit $LASTEXITCODE
}
Write-Ok "Security assert_safe_environment OK (PAPER_ONLY contract)"

# DATABASE_URL presence check (do not invent Postgres).
$dbUrl = $env:DATABASE_URL
if (-not $dbUrl -and (Test-Path $RootEnv)) {
    $line = Select-String -Path $RootEnv -Pattern '^\s*DATABASE_URL\s*=\s*(.+)$' | Select-Object -First 1
    if ($line) {
        $dbUrl = $line.Matches[0].Groups[1].Value.Trim()
    }
}
if ([string]::IsNullOrWhiteSpace($dbUrl)) {
    Write-Warn "DATABASE_URL unset — G2 (One-Brain /api/chat) will FAIL until Postgres is configured."
    Write-Warn "Set in .env: DATABASE_URL=postgresql://USER:PASS@127.0.0.1:5432/ahos"
} else {
    Write-Ok "DATABASE_URL is set in environment/.env (value not printed)."
}

# ---- 7) Initialize SQLite stores -------------------------------------------
Write-Step "[7/9] Initializing SQLite stores (canonical)..."
& $VenvPython scripts\init_databases.py --with-guards
if ($LASTEXITCODE -ne 0) {
    Write-Err "init_databases.py failed (exit $LASTEXITCODE)."
    exit $LASTEXITCODE
}
Write-Ok "SQLite stores healthy (or repaired idempotently)"

# Optional local path dump — never commit; write under reports/ (machine-local).
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$pathOut = Join-Path $ScriptDir "reports\paths_local_$stamp.yaml"
& $VenvPython -c "from config.paths import export_paths_yaml; export_paths_yaml(r'$pathOut'); print(r'$pathOut')"
Write-Ok "Wrote local path diagnostic: reports\paths_local_$stamp.yaml (do not commit secrets)"

# ---- 8) Optional seed (NOT a readiness claim) ------------------------------
Write-Step "[8/9] Evidence seed..."
if ($SeedEvidence) {
    Write-Warn "Running ONE paper single-cycle with --evidence-source local (live network may be used)."
    Write-Warn "This does NOT prove OPERATOR_READY."
    & $VenvPython -m architecture.runtime --single-cycle --evidence-source local --limit 5
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "single-cycle exited $LASTEXITCODE — diagnose honestly; do not mock providers."
    } else {
        & $VenvPython scripts\prediction_lifecycle_status.py
        Write-Ok "Seed cycle finished (inspect lifecycle status; labels may be 0 until T+72h)."
    }
} else {
    Write-Ok "Skipped live seed (default). Use -SeedEvidence to run one paper cycle."
}

# ---- 9) Next operator commands (no auto gate / no auto soak) ---------------
Write-Step "[9/9] Installer complete — next human steps"
Write-Host ""
Write-Host "  STATUS" -ForegroundColor Cyan
Write-Host "    INTEGRATION_READY     : prior agent-host claim (unchanged by installer)" -ForegroundColor DarkGray
Write-Host "    OPERATOR_READY        : NOT_VERIFIED" -ForegroundColor DarkGray
Write-Host "    PRE_SOAK              : do NOT start until pre_soak_entry_ok" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  NEXT (Terminal A) — One-Brain gateway for G2:" -ForegroundColor Cyan
Write-Host "    1. Ensure .env has DATABASE_URL + AHOS_GATEWAY_URL=http://127.0.0.1:3000/api/chat" -ForegroundColor White
Write-Host "    2. npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "  NEXT (Terminal B) — Operator Validation Gate:" -ForegroundColor Cyan
Write-Host "    .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "    `$env:AHOS_PAPER_ONLY = `"1`"" -ForegroundColor White
Write-Host "    `$env:AHOS_EVIDENCE_SOURCE = `"local`"" -ForegroundColor White
Write-Host "    `$env:AHOS_GATEWAY_URL = `"http://127.0.0.1:3000/api/chat`"" -ForegroundColor White
Write-Host "    python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill" -ForegroundColor White
Write-Host ""
Write-Host "  Full protocol: docs\WINDOWS_OPERATOR_HANDOFF.md" -ForegroundColor Cyan
Write-Host "  Do NOT run .\start_ahos.ps1 (soak daemon) until summary.pre_soak_entry_ok == true." -ForegroundColor DarkYellow
Write-Host "==========================================================" -ForegroundColor Cyan

exit 0
