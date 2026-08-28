#Requires -Version 5.1
<#
.SYNOPSIS
  Best-effort post OWNER_PASTE to one or more GitHub PRs via gh.

Never fails the gate. Does not invent READY. Does not migrate.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$BodyFile,
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if (-not (Test-Path -LiteralPath $BodyFile)) {
  Write-Host ("gh paste skip: body missing " + $BodyFile) -ForegroundColor DarkYellow
  exit 0
}

$gh = Get-Command gh -ErrorAction SilentlyContinue
if ($null -eq $gh) {
  Write-Host "gh CLI not on PATH -- Ctrl+V paste into Cursor still required." -ForegroundColor DarkYellow
  exit 0
}

try {
  & gh auth status 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "gh not authenticated -- Ctrl+V paste into Cursor still required." -ForegroundColor DarkYellow
    exit 0
  }
} catch {
  Write-Host ("gh auth check failed: " + $_.Exception.Message) -ForegroundColor DarkYellow
  exit 0
}

$targets = New-Object System.Collections.Generic.List[string]
function Add-Target([string]$n) {
  if ([string]::IsNullOrWhiteSpace($n)) { return }
  $n = $n.Trim()
  if (-not ($targets -contains $n)) { [void]$targets.Add($n) }
}

Add-Target $env:AHOS_GATE_PR

try {
  Add-Target (& gh pr view --json number -q ".number" 2>$null)
} catch {}

# Open unlock/docs PRs first, then durable merged evidence PRs
try {
  $open = & gh pr list --state open --limit 15 --json number,headRefName 2>$null | ConvertFrom-Json
  foreach ($p in $open) {
    if ($p.headRefName -match 'windows|harden|unlock|ops|gate|pre.?soak|g2|evidence|lease|inbox') {
      Add-Target ([string]$p.number)
    }
  }
} catch {}

# Dedicated evidence inbox + known sinks (comments wake subscribed agents)
Add-Target "51"
Add-Target "50"
# Open durable inbox (replace number after PR create if needed — also matched by head name)
try {
  $openInbox = & gh pr list --head cursor/windows-evidence-inbox-open-4bde --state open --json number -q ".[0].number" 2>$null
  Add-Target $openInbox
} catch {}
Add-Target "45"
Add-Target "44"
Add-Target "43"
Add-Target "38"
Add-Target "37"
Add-Target "36"
Add-Target "34"

$posted = 0
foreach ($prNum in $targets) {
  try {
    & gh pr comment $prNum --body-file $BodyFile 2>&1 | Out-Host
    if ($LASTEXITCODE -eq 0) {
      Write-Host ("Posted gate paste to PR #" + $prNum + " via gh.") -ForegroundColor Green
      $posted++
    } else {
      Write-Host ("gh pr comment #" + $prNum + " failed exit=" + $LASTEXITCODE) -ForegroundColor DarkYellow
    }
  } catch {
    Write-Host ("gh pr comment #" + $prNum + " skipped: " + $_.Exception.Message) -ForegroundColor DarkYellow
  }
}

if ($posted -eq 0) {
  Write-Host "No gh PR comment succeeded -- Ctrl+V reports\OWNER_PASTE_WINDOWS_GATE.txt into Cursor." -ForegroundColor Yellow
} else {
  Write-Host ("gh paste posts succeeded=" + $posted + " (agent can fetch).") -ForegroundColor Green
}
exit 0
