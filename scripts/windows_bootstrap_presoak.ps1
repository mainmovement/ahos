#Requires -Version 5.1
<#
.SYNOPSIS
  One-shot Windows bootstrap: fetch unlock tip, apply files, run PRE_SOAK path.

STATE B: never db:migrate / db:push. Does NOT invent PRE_SOAK/READY.

Prefer AHOS_BOOTSTRAP_PRESOAK.bat from repo root. Alternate:
  powershell -NoProfile -ExecutionPolicy Bypass -Command "iwr -useb https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/scripts/windows_bootstrap_presoak.ps1 -OutFile scripts\windows_bootstrap_presoak.ps1; powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\windows_bootstrap_presoak.ps1"
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$Tip = "cursor/windows-main-evidence-push-4bde"
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  } else {
    $RepoRoot = (Get-Location).Path
  }
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS bootstrap PRE_SOAK tip (PAPER_ONLY)" -ForegroundColor Cyan
Write-Host "  Tip: $Tip" -ForegroundColor DarkGray
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
  Write-Host "FAIL: git fetch tip failed" -ForegroundColor Red
  exit 2
}

$ref = "origin/" + $Tip
Write-Host ("==> checkout unlock files from " + $ref) -ForegroundColor Cyan

# Prefer shared helper (ls-tree expansion). Seed it first to avoid pathspec glob bugs.
& git checkout $ref -- scripts/windows_checkout_unlock_tip.ps1 AHOS_BOOTSTRAP_PRESOAK.bat 2>&1 | Out-Host
$helper = Join-Path $RepoRoot "scripts\windows_checkout_unlock_tip.ps1"
if (Test-Path -LiteralPath $helper) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -Ref $ref
  if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: windows_checkout_unlock_tip.ps1 failed" -ForegroundColor Red
    exit 2
  }
} else {
  Write-Host "WARN: checkout helper missing - expanding windows_*.ps1 via git ls-tree" -ForegroundColor Yellow
  $winScripts = @()
  try {
    $listed = & git ls-tree -r --name-only $ref 2>$null
    foreach ($p in $listed) {
      if ($p -like "scripts/windows_*.ps1") { $winScripts += $p }
    }
  } catch {}
  $paths = New-Object System.Collections.Generic.List[string]
  foreach ($p in @(
    "AHOS_APPLY_TIP.bat",
    "AHOS_BOOTSTRAP_PRESOAK.bat",
    "AHOS_PRE_SOAK_NOW.bat",
    "AHOS_WINDOWS_OPS.bat",
    "AHOS_VALIDATE_G2_NOW.bat",
    "AHOS_PULL_OPS_UNLOCK.bat",
    "AHOS_PUSH_EVIDENCE_NOW.bat",
    "WINDOWS_RUN_THIS_FIRST.txt",
    "scripts/ahos_pg_probe.mjs",
    "scripts/windows_g2_probe.py",
    "scripts/operator_validation_gate.py",
    "app/api/chat/route.ts",
    "db/index.ts",
    "snapshot.ts",
    "tests/validate_n8n.py",
    "deployment/docker-compose.windows.yml",
    ".env.example"
  )) { [void]$paths.Add($p) }
  foreach ($p in $winScripts) { [void]$paths.Add($p) }
  Write-Host ("  windows_*.ps1 count from tip: " + $winScripts.Count) -ForegroundColor DarkGray
  & git checkout $ref -- @($paths.ToArray()) 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0 -or $winScripts.Count -lt 5) {
    Write-Host "WARN: bulk/list checkout incomplete - trying core set" -ForegroundColor Yellow
    & git checkout $ref -- `
      AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat AHOS_PUSH_EVIDENCE_NOW.bat `
      scripts/operator_validation_gate.py scripts/windows_recover_g2_warm.ps1 `
      scripts/windows_ensure_database_url.ps1 scripts/windows_wait_for_web_api.ps1 `
      scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 `
      scripts/windows_bootstrap_presoak.ps1 scripts/windows_chat_500_forensics.ps1 `
      scripts/windows_restart_next_dev.ps1 scripts/windows_ensure_postgres_win.ps1 `
      scripts/windows_post_merge_reconcile.ps1 scripts/windows_run_operator_gate.ps1 `
      app/api/chat/route.ts 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) {
      Write-Host "FAIL: tip checkout failed" -ForegroundColor Red
      exit 2
    }
  }
}

$pre = Join-Path $RepoRoot "AHOS_PRE_SOAK_NOW.bat"
if (-not (Test-Path -LiteralPath $pre)) {
  Write-Host "FAIL: AHOS_PRE_SOAK_NOW.bat missing after tip checkout" -ForegroundColor Red
  exit 2
}

# Scrub empty AHOS_GATEWAY_URL= before PRE_SOAK (last Windows paste G2 BLOCKED on empty).
$ensureTok = Join-Path $RepoRoot "scripts\windows_ensure_web_api_token.ps1"
if (Test-Path -LiteralPath $ensureTok) {
  Write-Host "==> ensure web API token + AHOS_GATEWAY_URL" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureTok | Out-Host
}

# Same console so OPS bat pause/paste instructions are visible.
Write-Host "==> launching AHOS_PRE_SOAK_NOW.bat (same console)" -ForegroundColor Cyan
cmd.exe /c "`"$pre`""
$code = $LASTEXITCODE

Write-Host ""
Write-Host "Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38" -ForegroundColor Cyan
Write-Host "Or run AHOS_PUSH_EVIDENCE_NOW.bat" -ForegroundColor Cyan
Write-Host "Also see reports\PRE_SOAK_STATUS.txt" -ForegroundColor Cyan
Write-Host "PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY." -ForegroundColor Yellow
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
exit $code
