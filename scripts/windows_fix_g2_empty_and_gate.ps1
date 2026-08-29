#Requires -Version 5.1
<#
.SYNOPSIS
  Surgical Windows path when last paste was G2 empty-gateway BLOCKED with G3-G10 PASS.

Does NOT invent PRE_SOAK/READY. STATE B: never db:migrate / db:push.

Steps:
  1) fetch tip + checkout unlock files (ls-tree helper)
  2) scrub empty AHOS_GATEWAY_URL= + ensure token
  3) warm /api/chat (recover if needed)
  4) run full operator gate (G1-G12)
  5) push OWNER_PASTE evidence
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

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
# Wake leave-open paste sink #56 (post_gate / evidence push notify)
$env:AHOS_GATE_PR = "56"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS FIX G2 empty gateway + full gate (PAPER_ONLY)" -ForegroundColor Cyan
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
$tipFetched = ($LASTEXITCODE -eq 0)
if (-not $tipFetched) {
  Write-Host ("WARN: git fetch tip failed - continuing with local scripts if present") -ForegroundColor Yellow
}

$ref = "origin/" + $Tip
if ($tipFetched) {
  & git checkout $ref -- scripts/windows_checkout_unlock_tip.ps1 2>&1 | Out-Host
  $helper = Join-Path $RepoRoot "scripts\windows_checkout_unlock_tip.ps1"
  if (Test-Path -LiteralPath $helper) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -Ref $ref
    if ($LASTEXITCODE -ne 0) {
      Write-Host "WARN: unlock tip checkout helper failed - continuing with local scripts" -ForegroundColor Yellow
    }
  } else {
    Write-Host "WARN: checkout helper missing - applying explicit core set" -ForegroundColor Yellow
    & git checkout $ref -- `
      scripts/operator_validation_gate.py scripts/windows_run_operator_gate.ps1 `
      scripts/windows_ensure_web_api_token.ps1 scripts/windows_wait_for_web_api.ps1 `
      scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_database_url.ps1 `
      scripts/windows_ensure_postgres_win.ps1 scripts/windows_scrub_empty_gateway.ps1 `
      scripts/windows_seed_local_evidence.ps1 scripts/windows_restart_next_dev.ps1 `
      scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 `
      scripts/windows_publish_owner_paste.ps1 scripts/windows_g2_probe.py `
      scripts/ahos_pg_probe.mjs app/api/chat/route.ts `
      AHOS_FIX_G2_AND_GATE.bat AHOS_PUSH_EVIDENCE_NOW.bat 2>&1 | Out-Host
  }
} else {
  Write-Host "WARN: skipping tip checkout (fetch failed)" -ForegroundColor Yellow
}

$scrub = Join-Path $RepoRoot "scripts\windows_scrub_empty_gateway.ps1"
if (Test-Path -LiteralPath $scrub) {
  Write-Host "==> scrub empty AHOS_GATEWAY_URL in .env" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $scrub -RepoRoot $RepoRoot
}

$ensure = Join-Path $RepoRoot "scripts\windows_ensure_web_api_token.ps1"
if (Test-Path -LiteralPath $ensure) {
  Write-Host "==> scrub empty AHOS_GATEWAY_URL + ensure token" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $ensure
} else {
  Write-Host "FAIL: windows_ensure_web_api_token.ps1 missing" -ForegroundColor Red
  exit 2
}

$pg = Join-Path $RepoRoot "scripts\windows_ensure_postgres_win.ps1"
if (Test-Path -LiteralPath $pg) {
  Write-Host "==> ensure Postgres container ready (STATE B: no migrate)" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $pg
  if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: postgres ensure failed - G2 may HTTP 500; continuing" -ForegroundColor Yellow
  }
}

$dbUrl = Join-Path $RepoRoot "scripts\windows_ensure_database_url.ps1"
if (Test-Path -LiteralPath $dbUrl) {
  Write-Host "==> ensure DATABASE_URL (probe-first; STATE B)" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $dbUrl
}

# After ensure token/DB URL, ALWAYS restart Next so .env reloads.
# A stale :3000 listener (pre-token) would otherwise warm-401 then delay G2.
Write-Host "==> restart Next so .env token/DATABASE_URL are loaded" -ForegroundColor Cyan
$restart = Join-Path $RepoRoot "scripts\windows_restart_next_dev.ps1"
$recover = Join-Path $RepoRoot "scripts\windows_recover_g2_warm.ps1"
if (Test-Path -LiteralPath $restart) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $restart -RepoRoot $RepoRoot
} elseif (Test-Path -LiteralPath $recover) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $recover
} else {
  Write-Host "WARN: no restart_next / recover script - if :3000 is stale, G2 may 401" -ForegroundColor Yellow
}

$wait = Join-Path $RepoRoot "scripts\windows_wait_for_web_api.ps1"
if (Test-Path -LiteralPath $wait) {
  Write-Host "==> warm /api/chat" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $wait
  if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: warm failed - trying recover_g2_warm" -ForegroundColor Yellow
    $recover = Join-Path $RepoRoot "scripts\windows_recover_g2_warm.ps1"
    if (Test-Path -LiteralPath $recover) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $recover
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $wait
    if ($LASTEXITCODE -ne 0) {
      Write-Host "WARN: /api/chat still not warm - gate will report honest G2" -ForegroundColor Yellow
    }
  }
}

$gate = Join-Path $RepoRoot "scripts\windows_run_operator_gate.ps1"
if (-not (Test-Path -LiteralPath $gate)) {
  Write-Host "FAIL: windows_run_operator_gate.ps1 missing" -ForegroundColor Red
  exit 2
}

Write-Host "==> full operator gate (G1-G12) + SeedEvidenceIfNeeded" -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File $gate -SeedEvidenceIfNeeded
$gateCode = $LASTEXITCODE

$pastePath = Join-Path $RepoRoot "reports\OWNER_PASTE_WINDOWS_GATE.txt"
if (-not (Test-Path -LiteralPath $pastePath)) {
  $failPaste = Join-Path $RepoRoot "scripts\windows_write_ops_failure_paste.ps1"
  if (Test-Path -LiteralPath $failPaste) {
    Write-Host "==> writing failure OWNER_PASTE (gate produced none)" -ForegroundColor Yellow
    & powershell -NoProfile -ExecutionPolicy Bypass -File $failPaste -Stage "fix_g2_gate" -Detail "gate did not write OWNER_PASTE; see console"
  }
}

$push = Join-Path $RepoRoot "scripts\windows_push_gate_evidence.ps1"
if (Test-Path -LiteralPath $push) {
  if (Test-Path -LiteralPath $pastePath) {
    Write-Host "==> push OWNER_PASTE evidence" -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File $push
  }
}

Write-Host ""
if (Test-Path -LiteralPath (Join-Path $RepoRoot "reports\PRE_SOAK_STATUS.txt")) {
  Write-Host "----- PRE_SOAK_STATUS.txt -----" -ForegroundColor Yellow
  Get-Content -LiteralPath (Join-Path $RepoRoot "reports\PRE_SOAK_STATUS.txt") | ForEach-Object { Write-Host $_ }
}
Write-Host "Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38" -ForegroundColor Cyan
Write-Host "PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY." -ForegroundColor Yellow
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
exit $gateCode
