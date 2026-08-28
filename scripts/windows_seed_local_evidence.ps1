# ==============================================================================
# AHOS Windows - seed local SQLite evidence if G4/G5/G8/G9 would FAIL
#
# STATE B Postgres row counts do NOT satisfy those gates. They read local SQLite
# via lifecycle_status(). This script runs ONE local cycle only when census is
# empty. Never claims PRE_SOAK / OPERATOR_READY. Never db:migrate / db:push.
#
# Exit 0 = census already OK or seed succeeded
# Exit 2 = still insufficient after seed (gate will honest-FAIL G4/G5/G8/G9)
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
Write-Host "  NOTE: Postgres ahos_* rows do NOT satisfy G4/G5/G8/G9" -ForegroundColor DarkYellow
Write-Host "==========================================================" -ForegroundColor Cyan

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) { $py = "python" }

$env:AHOS_PAPER_ONLY = "1"
$env:AHOS_EVIDENCE_SOURCE = "local"

function Get-LifecycleCensus([string]$PythonExe) {
    $censusJson = & $PythonExe -c @"
import json
try:
    from architecture.learning.prediction_lifecycle import lifecycle_status
    st = lifecycle_status()
    obs = sum(int(v) for v in (st.get('observation_state') or {}).values())
    st['observation_state_total'] = obs
except Exception as e:
    st = {'_error': type(e).__name__ + ':' + str(e), 'observation_state_total': 0}
print(json.dumps(st, ensure_ascii=False))
"@
    return $censusJson
}

function Read-CensusObject([string]$censusJson) {
    if ([string]::IsNullOrWhiteSpace($censusJson)) { return $null }
    try { return ($censusJson | ConvertFrom-Json) } catch { return $null }
}

function Test-CensusSufficient($st) {
    if ($null -eq $st) { return $false }
    if ($st._error) { return $false }
    $disc = 0; $prod = 0; $preds = 0; $obs = 0
    try { $disc = [int]$st.discovery_observations } catch {}
    try { $prod = [int]$st.production_observations } catch {}
    try { $preds = [int]$st.local_predictions } catch {}
    try { $obs = [int]$st.observation_state_total } catch {}
    # G4: discovery or production obs; G5: local_predictions; G8: observation_state sum; G9: discovery_observations
    $g4 = ($disc -gt 0) -or ($prod -gt 0)
    $g5 = ($preds -gt 0)
    $g8 = ($obs -gt 0)
    $g9 = ($disc -gt 0)
    return ($g4 -and $g5 -and $g8 -and $g9)
}

function Write-Census($st, [string]$Label) {
    $disc = 0; $prod = 0; $preds = 0; $obs = 0
    try { $disc = [int]$st.discovery_observations } catch {}
    try { $prod = [int]$st.production_observations } catch {}
    try { $preds = [int]$st.local_predictions } catch {}
    try { $obs = [int]$st.observation_state_total } catch {}
    Write-Host ("  " + $Label + " discovery_observations=" + $disc + " production_observations=" + $prod + " local_predictions=" + $preds + " observation_state_total=" + $obs) -ForegroundColor DarkGray
}

$censusJson = Get-LifecycleCensus -PythonExe $py
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($censusJson)) {
    Write-Host "  WARN: could not read lifecycle_status — skipping seed" -ForegroundColor Yellow
    exit 0
}

$st = Read-CensusObject -censusJson $censusJson
if ($null -eq $st) {
    Write-Host "  WARN: bad census JSON — skipping seed" -ForegroundColor Yellow
    exit 0
}
if ($st._error) {
    Write-Host ("  WARN: lifecycle_status error: " + $st._error) -ForegroundColor Yellow
    exit 0
}

Write-Census -st $st -Label "census"
if (-not $Force -and (Test-CensusSufficient -st $st)) {
    Write-Host "  Local evidence already present — skip single-cycle." -ForegroundColor Green
    exit 0
}

Write-Host ("  Running one local single-cycle (limit=" + $Limit + ")...") -ForegroundColor Cyan
& $py -m architecture.runtime --single-cycle --evidence-source local --limit $Limit
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host ("  WARNING: single-cycle exit=" + $code + " — gate may still FAIL G4/G5/G8/G9; do not invent PASS.") -ForegroundColor Yellow
    exit 2
}

$afterJson = Get-LifecycleCensus -PythonExe $py
$after = Read-CensusObject -censusJson $afterJson
if ($null -eq $after) {
    Write-Host "  WARNING: could not re-read census after seed — do not invent PASS." -ForegroundColor Yellow
    exit 2
}
Write-Census -st $after -Label "after_seed"
if (Test-CensusSufficient -st $after) {
    Write-Host "  Seed OK for G4/G5/G8/G9 census (still NOT OPERATOR_READY / NOT PRE_SOAK)." -ForegroundColor Green
    exit 0
}

Write-Host "  WARNING: census still insufficient after single-cycle — gate will honest-FAIL G4/G5/G8/G9." -ForegroundColor Yellow
Write-Host "  Hint: re-run with -Force or scripts\backfill_lane_a_from_production.py (Lane-A rules apply)." -ForegroundColor Yellow
exit 2
