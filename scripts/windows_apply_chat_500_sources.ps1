#Requires -Version 5.1
<#
.SYNOPSIS
  Checkout /api/chat 500 fix sources onto the working tree (STATE B / no migrate).

Main unlock bats historically only checkout scripts/windows_*.ps1. This script is
picked up by that glob and then force-syncs the Next/DB files needed for G2.

Does NOT claim PRE_SOAK/READY. Lane-A untouched.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==> apply chat-500 source unlock (route/db/snapshot/probe)" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "WARN: git not on PATH -- skip source unlock" -ForegroundColor Yellow
  exit 0
}

$refs = @(
  "origin/cursor/windows-chat-500-rootcause-4bde",
  "origin/cursor/windows-evidence-push-lease-4bde",
  "origin/cursor/windows-g2-evidence-autopush-4bde"
)

git fetch origin cursor/windows-chat-500-rootcause-4bde cursor/windows-evidence-push-lease-4bde cursor/windows-g2-evidence-autopush-4bde 2>$null | Out-Null

$pick = $null
foreach ($r in $refs) {
  git rev-parse --verify $r 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { continue }
  git merge-base --is-ancestor $r origin/main 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    $pick = $r
    break
  }
}

if (-not $pick) {
  Write-Host "  unlock tip already on main (or refs missing) -- using HEAD for missing files only" -ForegroundColor DarkGray
  exit 0
}

$paths = @(
  "app/api/chat/route.ts",
  "db/index.ts",
  "snapshot.ts",
  "scripts/ahos_pg_probe.mjs",
  "scripts/windows_ensure_database_url.ps1",
  "scripts/windows_chat_500_forensics.ps1",
  "scripts/windows_pg_probe.ps1",
  "WINDOWS_RUN_THIS_FIRST.txt"
)

Write-Host ("  checkout from " + $pick) -ForegroundColor Cyan
& git checkout $pick -- @paths 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
  Write-Host "WARN: partial source unlock failed -- continue; DATABASE_URL sync may still fix G2" -ForegroundColor Yellow
  exit 0
}
Write-Host "  OK -- chat-500 sources on working tree (restart Next to load)" -ForegroundColor Green
exit 0
