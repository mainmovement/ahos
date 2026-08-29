#Requires -Version 5.1
<#
.SYNOPSIS
  Checkout Windows PRE_SOAK unlock files from a git ref using git ls-tree.

Why: cmd/PowerShell do not reliably expand git pathspecs like scripts/windows_*.ps1,
so OPS/PRE_SOAK bats can silently keep stale scripts and miss G2 recover / evidence push.

STATE B: never db:migrate / db:push. Does NOT invent PRE_SOAK/READY.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Ref,

  [string]$RepoRoot = ""
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

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Write-Host "FAIL: git not on PATH" -ForegroundColor Red
  exit 2
}

$verify = & git rev-parse --verify $Ref 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($verify)) {
  Write-Host ("FAIL: ref not found: " + $Ref) -ForegroundColor Red
  exit 2
}

Write-Host ("==> checkout unlock files from " + $Ref) -ForegroundColor Cyan

$winScripts = @()
$listed = & git ls-tree -r --name-only $Ref 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host ("FAIL: git ls-tree failed for " + $Ref) -ForegroundColor Red
  exit 2
}
foreach ($p in $listed) {
  if ($p -like "scripts/windows_*.ps1") { $winScripts += $p }
}

$fixed = @(
  "AHOS_APPLY_TIP.bat",
  "AHOS_BOOTSTRAP_PRESOAK.bat",
  "AHOS_MAIN_FIRST.bat",
  "AHOS_FIX_G2_AND_GATE.bat",
  "AHOS_PRE_SOAK_NOW.bat",
  "AHOS_WINDOWS_OPS.bat",
  "AHOS_VALIDATE_G2_NOW.bat",
  "AHOS_PULL_OPS_UNLOCK.bat",
  "AHOS_PUSH_EVIDENCE_NOW.bat",
  "WINDOWS_RUN_THIS_FIRST.txt",
  "RUN_ME_WINDOWS.txt",
  "scripts/ahos_pg_probe.mjs",
  "scripts/windows_g2_probe.py",
  "scripts/operator_validation_gate.py",
  "app/api/chat/route.ts",
  "db/index.ts",
  "snapshot.ts",
  "tests/validate_n8n.py",
  "deployment/docker-compose.windows.yml",
  ".env.example"
)

$inTree = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
foreach ($p in $listed) { [void]$inTree.Add($p) }

$paths = New-Object System.Collections.Generic.List[string]
foreach ($p in $fixed) {
  if ($inTree.Contains($p)) { [void]$paths.Add($p) }
  else { Write-Host ("  skip missing in ref: " + $p) -ForegroundColor DarkGray }
}
foreach ($p in $winScripts) { [void]$paths.Add($p) }

Write-Host ("  windows_*.ps1 count: " + $winScripts.Count) -ForegroundColor DarkGray
if ($paths.Count -lt 1) {
  Write-Host "FAIL: no unlock paths resolved from ref" -ForegroundColor Red
  exit 2
}
& git checkout $Ref -- @($paths.ToArray()) 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
  Write-Host "WARN: bulk checkout failed - trying explicit core set" -ForegroundColor Yellow
  $core = @(
    "AHOS_APPLY_TIP.bat", "AHOS_BOOTSTRAP_PRESOAK.bat", "AHOS_FIX_G2_AND_GATE.bat",
    "AHOS_PRE_SOAK_NOW.bat", "AHOS_WINDOWS_OPS.bat",
    "AHOS_VALIDATE_G2_NOW.bat", "AHOS_PUSH_EVIDENCE_NOW.bat", "WINDOWS_RUN_THIS_FIRST.txt",
    "scripts/windows_checkout_unlock_tip.ps1", "scripts/windows_bootstrap_presoak.ps1",
    "scripts/windows_fix_g2_empty_and_gate.ps1",
    "scripts/windows_recover_g2_warm.ps1", "scripts/windows_ensure_database_url.ps1",
    "scripts/windows_ensure_postgres_win.ps1", "scripts/windows_ensure_web_api_token.ps1",
    "scripts/windows_wait_for_web_api.ps1", "scripts/windows_restart_next_dev.ps1",
    "scripts/windows_chat_500_forensics.ps1", "scripts/windows_push_gate_evidence.ps1",
    "scripts/windows_post_gate_paste_gh.ps1", "scripts/windows_run_operator_gate.ps1",
    "scripts/windows_validate_g2.ps1", "scripts/windows_post_merge_reconcile.ps1",
    "scripts/windows_write_ops_failure_paste.ps1", "scripts/windows_preflight_ops.ps1",
    "scripts/windows_pre_soak_readiness.ps1", "scripts/operator_validation_gate.py",
    "scripts/windows_g2_probe.py", "scripts/ahos_pg_probe.mjs",
    "app/api/chat/route.ts", "db/index.ts", "snapshot.ts"
  )
  $corePresent = @()
  foreach ($p in $core) { if ($inTree.Contains($p)) { $corePresent += $p } }
  if ($corePresent.Count -lt 1) {
    Write-Host "FAIL: unlock tip checkout failed (no core paths in ref)" -ForegroundColor Red
    exit 2
  }
  & git checkout $Ref -- @($corePresent) 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: unlock tip checkout failed" -ForegroundColor Red
    exit 2
  }
}

$must = @(
  "AHOS_WINDOWS_OPS.bat",
  "scripts\windows_ensure_database_url.ps1",
  "scripts\windows_ensure_web_api_token.ps1",
  "scripts\operator_validation_gate.py"
)
$missing = @()
foreach ($rel in $must) {
  if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot $rel))) { $missing += $rel }
}
if ($missing.Count -gt 0) {
  Write-Host ("FAIL: missing after checkout: " + ($missing -join ", ")) -ForegroundColor Red
  exit 2
}

if ($winScripts.Count -lt 5) {
  Write-Host "WARN: fewer than 5 windows_*.ps1 paths from ls-tree; core set applied anyway" -ForegroundColor Yellow
}

Write-Host ("OK -- unlock files applied from " + $Ref) -ForegroundColor Green
exit 0
