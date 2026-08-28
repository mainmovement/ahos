#Requires -Version 5.1
<#
.SYNOPSIS
  Push Windows gate OWNER_PASTE + report JSON to a durable evidence branch.

Creates/updates branch cursor/windows-gate-evidence-4bde and opens/updates a PR
so Cloud agents can fetch evidence without chat paste.

Does NOT invent PRE_SOAK / OPERATOR_READY. Does NOT db:migrate.
Never force-pushes main. Uses --force-with-lease only on the evidence branch.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$EvidenceBranch = "cursor/windows-gate-evidence-4bde",
  [string]$PastePath = "",
  [string]$SlimPath = "",
  [string]$LatestPath = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location -LiteralPath $RepoRoot

function Write-Step([string]$Msg) {
  Write-Host ("[gate-evidence] {0}" -f $Msg) -ForegroundColor Cyan
}

$git = Get-Command git -ErrorAction SilentlyContinue
if ($null -eq $git) {
  Write-Host "[gate-evidence] git missing — skip push; Ctrl+V paste still required." -ForegroundColor DarkYellow
  exit 0
}

$reports = Join-Path $RepoRoot "reports"
if ([string]::IsNullOrWhiteSpace($PastePath)) {
  $PastePath = Join-Path $reports "OWNER_PASTE_WINDOWS_GATE.txt"
}
if ([string]::IsNullOrWhiteSpace($SlimPath)) {
  $SlimPath = Join-Path $reports "OWNER_PASTE_WINDOWS_GATE_SLIM.txt"
}
if ([string]::IsNullOrWhiteSpace($LatestPath)) {
  $LatestPath = Join-Path $reports "LATEST_WINDOWS_GATE.txt"
}

if (-not (Test-Path -LiteralPath $PastePath) -and -not (Test-Path -LiteralPath $LatestPath)) {
  Write-Host "[gate-evidence] no paste/latest to push — skip." -ForegroundColor DarkYellow
  exit 0
}

# Stage copies under a tracked path (OWNER_PASTE* is gitignored at reports root)
$evDir = Join-Path $reports "windows_gate_evidence"
if (-not (Test-Path -LiteralPath $evDir)) {
  New-Item -ItemType Directory -Path $evDir -Force | Out-Null
}
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$utf8 = New-Object System.Text.UTF8Encoding $false

$bundle = Join-Path $evDir ("OWNER_PASTE_" + $stamp + ".txt")
$latestOut = Join-Path $evDir "LATEST_WINDOWS_GATE.txt"
$pointer = Join-Path $evDir "README_EVIDENCE.md"

if (Test-Path -LiteralPath $PastePath) {
  Copy-Item -LiteralPath $PastePath -Destination $bundle -Force
  Copy-Item -LiteralPath $PastePath -Destination (Join-Path $evDir "OWNER_PASTE_WINDOWS_GATE.txt") -Force
}
if (Test-Path -LiteralPath $SlimPath) {
  Copy-Item -LiteralPath $SlimPath -Destination (Join-Path $evDir "OWNER_PASTE_WINDOWS_GATE_SLIM.txt") -Force
}
if (Test-Path -LiteralPath $LatestPath) {
  Copy-Item -LiteralPath $LatestPath -Destination $latestOut -Force
}

$newestJson = Get-ChildItem -LiteralPath $reports -Filter "operator_validation_report_windows_*.json" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
if ($null -ne $newestJson) {
  Copy-Item -LiteralPath $newestJson.FullName -Destination (Join-Path $evDir $newestJson.Name) -Force
  Copy-Item -LiteralPath $newestJson.FullName -Destination (Join-Path $evDir "operator_validation_report_windows_LATEST.json") -Force
}

$readme = @(
  "# Windows gate evidence (not a READY claim)",
  "",
  ("- generated_utc: " + $stamp),
  "- STATE B: do not db:migrate / db:push",
  "- OPERATOR_READY: NOT claimed by this push",
  "- pre_soak_entry_ok: only if LATEST / JSON says so on a real Windows host",
  "",
  "Files in this folder are produced by AHOS_WINDOWS_OPS.bat / gate runner.",
  "Agents: read OWNER_PASTE_WINDOWS_GATE.txt and operator_validation_report_windows_LATEST.json."
)
[System.IO.File]::WriteAllText($pointer, ($readme -join "`n") + "`n", $utf8)

$prevBranch = "main"
try { $prevBranch = (& git rev-parse --abbrev-ref HEAD 2>$null).Trim() } catch {}
$dirty = $false
try {
  $status = (& git status --porcelain 2>$null)
  if (-not [string]::IsNullOrWhiteSpace(($status | Out-String))) { $dirty = $true }
} catch {}

if ($dirty) {
  Write-Step "working tree dirty — committing only evidence paths on evidence branch"
}

Write-Step ("checkout -B " + $EvidenceBranch)
& git fetch origin 2>$null | Out-Null
& git checkout -B $EvidenceBranch 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
  Write-Host "[gate-evidence] checkout failed — Ctrl+V paste still required." -ForegroundColor Yellow
  exit 0
}

& git add -- "reports/windows_gate_evidence"
# Also force-add ignored paste mirrors if present at reports root (belt/suspenders)
if (Test-Path -LiteralPath $PastePath) { & git add -f -- $PastePath 2>$null }
if (Test-Path -LiteralPath $LatestPath) { & git add -f -- $LatestPath 2>$null }

$staged = (& git diff --cached --name-only 2>$null)
if ([string]::IsNullOrWhiteSpace(($staged | Out-String))) {
  Write-Host "[gate-evidence] nothing staged — skip commit." -ForegroundColor DarkYellow
  & git checkout $prevBranch 2>&1 | Out-Null
  exit 0
}

$msg = @"
Windows gate evidence bundle ($stamp).

Not a PRE_SOAK or OPERATOR_READY claim. STATE B: no migrate.
Interpret LATEST / JSON honestly on agent side.
"@
& git commit -m $msg 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
  Write-Host "[gate-evidence] commit failed — Ctrl+V paste still required." -ForegroundColor Yellow
  & git checkout $prevBranch 2>&1 | Out-Null
  exit 0
}

Write-Step ("push --force-with-lease origin " + $EvidenceBranch)
& git push --force-with-lease -u origin $EvidenceBranch 2>&1 | Out-Host
$pushOk = ($LASTEXITCODE -eq 0)
if (-not $pushOk) {
  Write-Host "[gate-evidence] push failed — Ctrl+V Desktop AHOS_PASTE_TO_CURSOR.txt into Cursor." -ForegroundColor Yellow
}

# Best-effort open/update PR for evidence branch
$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($pushOk -and ($null -ne $gh)) {
  try {
    & gh auth status 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $existing = & gh pr list --head $EvidenceBranch --state open --json number -q ".[0].number" 2>$null
      if ([string]::IsNullOrWhiteSpace($existing)) {
        & gh pr create --base main --head $EvidenceBranch `
          --title "Windows gate evidence (not READY)" `
          --body "Auto-pushed OWNER_PASTE / gate JSON from laptop. **Not** an OPERATOR_READY claim. STATE B: no migrate. Agent: read ``reports/windows_gate_evidence/``." `
          2>&1 | Out-Host
      } else {
        Write-Host ("[gate-evidence] evidence PR already open #" + $existing) -ForegroundColor Green
      }
    }
  } catch {}
}

Write-Step ("return to " + $prevBranch)
& git checkout $prevBranch 2>&1 | Out-Host

if ($pushOk) {
  Write-Host "[gate-evidence] OK — agents can fetch origin/cursor/windows-gate-evidence-4bde" -ForegroundColor Green
} else {
  Write-Host "[gate-evidence] incomplete — Ctrl+V paste still required." -ForegroundColor Yellow
}
exit 0
