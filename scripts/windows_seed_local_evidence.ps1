# ==============================================================================
# AHOS Windows - seed local SQLite evidence if G4/G5/G8/G9 would FAIL
#
# STATE B Postgres row counts do NOT satisfy those gates. They read local SQLite
# via lifecycle_status(). This script runs ONE local cycle only when census is
# empty. Never claims PRE_SOAK / OPERATOR_READY. Never migrates.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_seed_local_evidence.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_seed_local_evidence.ps1 -Force
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [switch]$Force,
    [int]$Limit = 5
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS seed local SQLite evidence (no migrate / no READY)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"

$censusJson = & $py -c @"
import json
try:
    from architecture.learning.prediction_lifecycle import lifecycle_status
    st = lifecycle_status()
except Exception as e:
    st = {'_error': type(e).__name__ + ':' + str(e)}
print(json.dumps(st, ensure_ascii=False))
"@
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($censusJson)) {
    Write-Host "  WARN: could not read lifecycle_status — skipping seed" -ForegroundColor Yellow
    exit 0
}

try {
    $st = $censusJson | ConvertFrom-Json
} catch {
    Write-Host ("  WARN: bad census JSON: " + $_.Exception.Message) -ForegroundColor Yellow
    exit 0
}

if ($st._error) {
    Write-Host ("  WARN: lifecycle_status error: " + $st._error) -ForegroundColor Yellow
    exit 0
}

$disc = 0; $prod = 0; $preds = 0; $obs = 0
try { $disc = [int]$st.discovery_observations } catch {}
try { $prod = [int]$st.production_observations } catch {}
try { $preds = [int]$st.local_predictions } catch {}
try { $obs = [int]$st.observation_state_total } catch {}

Write-Host ("  census discovery_observations=" + $disc + " production_observations=" + $prod + " local_predictions=" + $preds + " observation_state_total=" + $obs) -ForegroundColor DarkGray

$need = ($disc -le 0 -and $prod -le 0) -or ($preds -le 0) -or ($obs -le 0)
if (-not $Force -and -not $need) {
    Write-Host "  Local evidence already present — skip single-cycle." -ForegroundColor Green
    exit 0
}

Write-Host ("  Running one local single-cycle (limit=" + $Limit + ")...") -ForegroundColor Cyan
& $py -m architecture.runtime --single-cycle --evidence-source local --limit $Limit
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ("  WARNING: single-cycle exit=" + $code + " — gate may still FAIL G4/G5/G8/G9; do not invent PASS.") -ForegroundColor Yellow
    exit 0
}
Write-Host "  Single-cycle finished (still NOT OPERATOR_READY / NOT PRE_SOAK)." -ForegroundColor Green
exit 0
