#Requires -Version 5.1
<#
.SYNOPSIS
  CRLF-safe Windows entry for PRE_SOAK unlock tip (PAPER_ONLY).

Why: raw.githubusercontent.com serves .bat blobs as LF. cmd.exe is unreliable
with LF-only bats. This script uses git checkout (eol=crlf) then runs MAIN_FIRST.

STATE B: never db:migrate / db:push. Does NOT invent READY.

One-liner from G:\robat\ahos:
  powershell -NoProfile -ExecutionPolicy Bypass -Command "iex (iwr -useb https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.ps1).Content"
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$Tip = "cursor/windows-main-evidence-push-4bde",
  [ValidateSet("main_first", "fix_g2", "bootstrap")]
  [string]$Mode = "main_first"
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path
    # When iex'd, PSScriptRoot may be empty; fall back to cwd.
  }
  if ([string]::IsNullOrWhiteSpace($RepoRoot) -or -not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
    $RepoRoot = (Get-Location).Path
  }
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS RUN TIP (CRLF-safe entry)" -ForegroundColor Cyan
Write-Host ("  Tip=" + $Tip + " Mode=" + $Mode) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB or claim READY" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "FAIL: git not on PATH" -ForegroundColor Red
  exit 2
}

Write-Host "==> git fetch origin main + tip" -ForegroundColor Cyan
& git fetch origin main 2>&1 | Out-Host
& git fetch origin $Tip 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
  Write-Host ("FAIL: git fetch " + $Tip) -ForegroundColor Red
  exit 2
}

$ref = "origin/" + $Tip
Write-Host ("==> checkout tip bats/scripts from " + $ref + " (eol=crlf on Windows)") -ForegroundColor Cyan
& git checkout $ref -- `
  AHOS_MAIN_FIRST.bat AHOS_FIX_G2_AND_GATE.bat AHOS_BOOTSTRAP_PRESOAK.bat `
  AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat AHOS_PUSH_EVIDENCE_NOW.bat `
  AHOS_RUN_TIP.ps1 OWNER_ONE_LINER.txt RUN_ME_WINDOWS.txt WINDOWS_RUN_THIS_FIRST.txt `
  scripts/windows_checkout_unlock_tip.ps1 scripts/windows_fix_g2_empty_and_gate.ps1 `
  scripts/windows_bootstrap_presoak.ps1 scripts/windows_ensure_web_api_token.ps1 `
  scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 `
  scripts/windows_publish_owner_paste.ps1 scripts/windows_run_operator_gate.ps1 `
  scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_database_url.ps1 `
  scripts/operator_validation_gate.py 2>&1 | Out-Host

$helper = Join-Path $RepoRoot "scripts\windows_checkout_unlock_tip.ps1"
if (Test-Path -LiteralPath $helper) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -Ref $ref
}

function Invoke-BatCrlf([string]$BatName) {
  $path = Join-Path $RepoRoot $BatName
  if (-not (Test-Path -LiteralPath $path)) {
    Write-Host ("FAIL: missing " + $BatName) -ForegroundColor Red
    return 2
  }
  # Belt: rewrite CRLF in case checkout did not convert (rare).
  $raw = [System.IO.File]::ReadAllText($path)
  $fixed = $raw -replace "`r?`n", "`r`n"
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($path, $fixed, $utf8NoBom)
  Write-Host ("==> cmd /c " + $BatName) -ForegroundColor Cyan
  & cmd.exe /c "`"$path`""
  return $LASTEXITCODE
}

$rc = 0
switch ($Mode) {
  "fix_g2" {
    $rc = Invoke-BatCrlf "AHOS_FIX_G2_AND_GATE.bat"
  }
  "bootstrap" {
    $boot = Join-Path $RepoRoot "scripts\windows_bootstrap_presoak.ps1"
    if (Test-Path -LiteralPath $boot) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $boot -Tip $Tip
      $rc = $LASTEXITCODE
    } else {
      $rc = Invoke-BatCrlf "AHOS_BOOTSTRAP_PRESOAK.bat"
    }
  }
  default {
    $rc = Invoke-BatCrlf "AHOS_MAIN_FIRST.bat"
  }
}

Write-Host ""
Write-Host "Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38" -ForegroundColor Cyan
Write-Host "PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY." -ForegroundColor Yellow
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
exit $rc
