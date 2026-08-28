#Requires -Version 5.1
<#
.SYNOPSIS
  One recovery pass when /api/chat warm fails (HTTP 5xx / timeout) under STATE B.

Runs forensics, ensure DATABASE_URL (probe-first), ensure postgres container,
then restarts Next so .env is reloaded. Does NOT db:migrate / db:push.
Does NOT invent PRE_SOAK or OPERATOR_READY.
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

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS G2 warm recovery (STATE B / no migrate)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$steps = @(
  @{ Name = "chat_500_forensics"; Rel = "scripts\windows_chat_500_forensics.ps1"; PassRoot = $true },
  @{ Name = "ensure_postgres"; Rel = "scripts\windows_ensure_postgres_win.ps1"; PassRoot = $false },
  @{ Name = "ensure_database_url"; Rel = "scripts\windows_ensure_database_url.ps1"; PassRoot = $true },
  @{ Name = "restart_next"; Rel = "scripts\windows_restart_next_dev.ps1"; PassRoot = $true }
)

$failed = New-Object System.Collections.Generic.List[string]
foreach ($s in $steps) {
  $path = Join-Path $RepoRoot $s.Rel
  if (-not (Test-Path -LiteralPath $path)) {
    Write-Host ("SKIP missing " + $s.Rel) -ForegroundColor DarkYellow
    continue
  }
  Write-Host ("==> " + $s.Name) -ForegroundColor Cyan
  if ($s.PassRoot) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $path -RepoRoot $RepoRoot
  } else {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $path
  }
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("WARN: " + $s.Name + " exit=" + $LASTEXITCODE) -ForegroundColor Yellow
    [void]$failed.Add($s.Name)
  }
}

$reports = Join-Path $RepoRoot "reports"
New-Item -ItemType Directory -Force -Path $reports | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$paste = Join-Path $reports ("OWNER_PASTE_G2_WARM_RECOVERY_" + $stamp + ".txt")
$lines = @(
  "===== BEGIN WINDOWS G2 WARM RECOVERY PASTE =====",
  ("generated_local=" + (Get-Date -Format "o")),
  "focus=G2_/api/chat_warm_recovery",
  "STATE_B=no_db_migrate_no_db_push",
  ("failed_steps=" + (($failed -join ",") )),
  "next=re-run windows_wait_for_web_api.ps1 then operator gate",
  "paste=reports\OWNER_PASTE_WINDOWS_GATE.txt after gate",
  "===== END WINDOWS G2 WARM RECOVERY PASTE ====="
)
$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllLines($paste, $lines, $utf8Bom)
Write-Host ("Wrote " + $paste) -ForegroundColor Green

$postGh = Join-Path $RepoRoot "scripts\windows_post_gate_paste_gh.ps1"
if (Test-Path -LiteralPath $postGh) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $postGh -BodyFile $paste -RepoRoot $RepoRoot
}

# Exit 0 so OPS bat continues to second wait / gate with honest evidence.
# Individual step failures are recorded in the paste above.
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
exit 0
