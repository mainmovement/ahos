# ==============================================================================
# AHOS Windows - run operator validation gate (G1-G12 report)
#
# Prerequisites:
#   - Already on main with web_api_auth (PR #31+)
#   - .env has DATABASE_URL + AHOS_WEB_API_TOKEN (use windows_ensure_web_api_token.ps1)
#   - npm run dev is listening on 127.0.0.1:3000 (other terminal)
#   - Never db:migrate / db:push (STATE B)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [switch]$SkipNetwork,
    [switch]$NoProviderProbe,
    [switch]$NoBackupDrill,
    [string]$TelegramE2eArtifact = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows operator validation gate" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB or invent OPERATOR_READY." -ForegroundColor DarkGray

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
    $py = "python"
}

$env:AHOS_PAPER_ONLY = "1"
if ([string]::IsNullOrWhiteSpace($env:AHOS_EVIDENCE_SOURCE)) {
    $env:AHOS_EVIDENCE_SOURCE = "local"
}

$argsList = @(
    (Join-Path $RepoRoot "scripts\operator_validation_gate.py"),
    "--platform", "windows"
)
if ($SkipNetwork) {
    $argsList += "--skip-network"
} else {
    if (-not $NoProviderProbe) { $argsList += "--probe-providers" }
    if (-not $NoBackupDrill) { $argsList += "--backup-drill" }
}
if (-not [string]::IsNullOrWhiteSpace($TelegramE2eArtifact)) {
    $argsList += @("--telegram-e2e-artifact", $TelegramE2eArtifact)
}

Write-Host ("  python: " + $py) -ForegroundColor DarkGray
Write-Host ("  args: " + ($argsList -join " ")) -ForegroundColor DarkGray
& $py @argsList
$code = $LASTEXITCODE
Write-Host ("gate_exit=" + $code)
Write-Host "Paste reports\operator_validation_report_windows_*.json into Cursor." -ForegroundColor Yellow
Write-Host "STATE B: do not db:migrate / db:push." -ForegroundColor Yellow
exit $code
