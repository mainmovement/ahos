#Requires -Version 5.1
<#
.SYNOPSIS
  Focused Windows G2 validation (Docker health + gateway) under STATE B.

Does NOT claim PRE_SOAK or OPERATOR_READY.
Does NOT db:migrate / db:push.
Lane-A freeze: does not touch Lane-A paths.

Exit 0 = G2 probe PASS.
Exit 2 = blocked/fail (see detail).
Encoding: ASCII-only + UTF-8 BOM.
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

$reports = Join-Path $RepoRoot "reports"
if (-not (Test-Path -LiteralPath $reports)) {
  New-Item -ItemType Directory -Path $reports -Force | Out-Null
}
$utf8 = New-Object System.Text.UTF8Encoding $false

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS G2 validate (health + gateway only)" -ForegroundColor Cyan
Write-Host "  STATE B: no migrate / no READY claim" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$diag = Join-Path $RepoRoot "scripts\windows_diagnose_docker_health.ps1"
if (Test-Path -LiteralPath $diag) {
  Write-Host "==> diagnose docker health" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $diag -RepoRoot $RepoRoot
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Diagnose hard-FAIL -- ensure-pg will still try one restart." -ForegroundColor Yellow
  }
}

$ensurePg = Join-Path $RepoRoot "scripts\windows_ensure_postgres_win.ps1"
if (Test-Path -LiteralPath $ensurePg) {
  Write-Host "==> ensure postgres (pg_isready; no wipe)" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $ensurePg
  if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: postgres not ready. Fix Docker/pg_isready, do NOT migrate." -ForegroundColor Red
    exit 2
  }
}

$ensureTok = Join-Path $RepoRoot "scripts\windows_ensure_web_api_token.ps1"
if (Test-Path -LiteralPath $ensureTok) {
  Write-Host "==> ensure web API token + gateway URL" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureTok
}

$restart = Join-Path $RepoRoot "scripts\windows_restart_next_dev.ps1"
if (Test-Path -LiteralPath $restart) {
  Write-Host "==> restart Next.js so .env is loaded" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $restart
} else {
  Write-Host "WARN: windows_restart_next_dev.ps1 missing -- start npm run dev manually" -ForegroundColor Yellow
}

$wait = Join-Path $RepoRoot "scripts\windows_wait_for_web_api.ps1"
if (Test-Path -LiteralPath $wait) {
  Write-Host "==> wait + warm /api/chat" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $wait
  if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: warm failed -- one recovery ensure-pg + restart + wait" -ForegroundColor Yellow
    if (Test-Path -LiteralPath $ensurePg) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $ensurePg
    }
    if (Test-Path -LiteralPath $restart) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $restart
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $wait
    if ($LASTEXITCODE -ne 0) {
      Write-Host "FAIL: /api/chat not ready after recovery. G2 will FAIL. No migrate." -ForegroundColor Red
    }
  }
}

$py = "python"
$venvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPy) { $py = $venvPy }

$env:AHOS_PAPER_ONLY = "1"
if ([string]::IsNullOrWhiteSpace($env:AHOS_EVIDENCE_SOURCE)) {
  $env:AHOS_EVIDENCE_SOURCE = "local"
}
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$outJson = Join-Path $reports ("g2_validate_windows_" + $stamp + ".json")
$probe = Join-Path $RepoRoot "scripts\windows_g2_probe.py"

Write-Host "==> G2-only probe (not a PRE_SOAK claim)" -ForegroundColor Cyan
& $py $probe --json-out $outJson
$code = $LASTEXITCODE

$paste = Join-Path $reports "OWNER_PASTE_G2_VALIDATE.txt"
$lines = @()
$lines += "===== BEGIN WINDOWS G2 VALIDATE PASTE ====="
$lines += ("report_path=" + $outJson)
$lines += ("exit_code=" + $code)
$lines += "STATE B: do not db:migrate / db:push"
$lines += "This path does NOT invent PRE_SOAK or OPERATOR_READY."
$lines += "ahos_runtime_win unhealthy is OK for host Next G2."
if (Test-Path -LiteralPath $outJson) {
  try {
    $j = Get-Content -LiteralPath $outJson -Raw | ConvertFrom-Json
    $lines += ("host_is_windows=" + $j.host_is_windows)
    $lines += ("G2.status=" + $j.gate.status)
    $lines += ("G2.detail=" + $j.gate.detail)
    $lines += ("g2_pass=" + $j.g2_pass)
    $lines += ("http_status=" + $j.gate.http_status)
    Write-Host ("G2=" + $j.gate.status + " g2_pass=" + $j.g2_pass) -ForegroundColor Cyan
  } catch {
    $lines += ("parse_error=" + $_.Exception.Message)
  }
}
$lines += "Next for PRE_SOAK (G1-G10): AHOS_PRE_SOAK_NOW.bat"
$lines += "===== END WINDOWS G2 VALIDATE PASTE ====="
[System.IO.File]::WriteAllText($paste, ($lines -join "`n") + "`n", $utf8)
Write-Host ("Wrote " + $paste) -ForegroundColor Green

$publish = Join-Path $RepoRoot "scripts\windows_publish_owner_paste.ps1"
if (Test-Path -LiteralPath $publish) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File $publish -PastePath $paste -DesktopName "AHOS_PASTE_G2_TO_CURSOR.txt"
}

if ($code -eq 0) {
  Write-Host "G2 PASS -- next run AHOS_PRE_SOAK_NOW.bat for full G1-G10 (still no READY invent)." -ForegroundColor Green
} else {
  Write-Host ("G2 not PASS (exit " + $code + ") -- fix health/gateway, re-run. No migrate.") -ForegroundColor Yellow
}

exit $code
