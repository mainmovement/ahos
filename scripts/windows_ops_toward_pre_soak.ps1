# ==============================================================================
# AHOS Windows -- ops toward PRE_SOAK (after web-api auth merge)
#
# One owner path:
#   1) Confirm web_api_auth is on this checkout (PR #31 merged into main)
#   2) Ensure AHOS_WEB_API_TOKEN (+ NEXT_PUBLIC) in .env
#   3) Print exact next commands (Next restart + operator gate)
#   4) Optionally run the operator gate (-RunGate) if Next is already up
#
# Never: db:migrate / db:push / reset / stash / invent OPERATOR_READY
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_ops_toward_pre_soak.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_ops_toward_pre_soak.ps1 -RunGate
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [switch]$RunGate
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host ("==> " + $Message) -ForegroundColor Cyan
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows ops toward PRE_SOAK (PAPER_ONLY)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB or claim OPERATOR_READY." -ForegroundColor DarkGray

$authFile = Join-Path $RepoRoot "web_api_auth.ts"
$ensureScript = Join-Path $RepoRoot "scripts\windows_ensure_web_api_token.ps1"
$gateScript = Join-Path $RepoRoot "scripts\operator_validation_gate.py"

$head = "UNKNOWN"
$branch = "UNKNOWN"
try {
    $head = (& git rev-parse --short HEAD).Trim()
    $branch = (& git rev-parse --abbrev-ref HEAD).Trim()
} catch {
    # git optional for token ensure; still continue with UNKNOWN
}

Write-Host ("  HEAD: " + $head + "  branch: " + $branch) -ForegroundColor DarkGray

if (-not (Test-Path -LiteralPath $authFile)) {
    Write-Host ""
    Write-Host "BLOCKED: web_api_auth.ts missing." -ForegroundColor Red
    Write-Host "Merge GitHub PR #31 into main, then:" -ForegroundColor Yellow
    Write-Host "  git fetch origin"
    Write-Host "  git pull origin main"
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\windows_post_merge_reconcile.ps1"
    Write-Host "Then re-run this script."
    exit 2
}

if (-not (Test-Path -LiteralPath $ensureScript)) {
    throw "Missing scripts\windows_ensure_web_api_token.ps1"
}

Write-Step "Ensuring web API token in .env"
& powershell -ExecutionPolicy Bypass -File $ensureScript
if ($LASTEXITCODE -ne 0) {
    throw ("windows_ensure_web_api_token.ps1 failed with exit " + $LASTEXITCODE)
}

Write-Host ""
Write-Host "BEGIN REPORT" -ForegroundColor Green
Write-Host ("repo=" + $RepoRoot)
Write-Host ("git_head=" + $head)
Write-Host ("git_branch=" + $branch)
Write-Host "web_api_auth=PRESENT"
Write-Host "state_b=MIGRATION_BLOCKED (do not db:migrate/db:push)"
Write-Host "operator_ready=NOT_VERIFIED_UNTIL_G1_G11"
Write-Host "END REPORT" -ForegroundColor Green

Write-Host ""
Write-Host "REQUIRED NEXT (two terminals):" -ForegroundColor Cyan
Write-Host "  Terminal A:"
Write-Host "    npm run dev"
Write-Host "  Terminal B (after Next is up):"
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host '    $env:AHOS_PAPER_ONLY = ''1'''
Write-Host '    $env:AHOS_EVIDENCE_SOURCE = ''local'''
Write-Host "    python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill"
Write-Host "  Paste reports\operator_validation_report_windows_*.json into Cursor."

if ($RunGate) {
    if (-not (Test-Path -LiteralPath $gateScript)) {
        throw "Missing operator_validation_gate.py"
    }
    Write-Step "Running operator validation gate (-RunGate)"
    $py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $py)) {
        $py = "python"
    }
    $env:AHOS_PAPER_ONLY = "1"
    if ([string]::IsNullOrWhiteSpace($env:AHOS_EVIDENCE_SOURCE)) {
        $env:AHOS_EVIDENCE_SOURCE = "local"
    }
    & $py $gateScript --platform windows --probe-providers --backup-drill
    Write-Host ("gate_exit=" + $LASTEXITCODE)
    exit $LASTEXITCODE
}

exit 0
