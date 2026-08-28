#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure .env DATABASE_URL matches Windows Docker Postgres (STATE B / no migrate).

Root cause class this fixes for /api/chat HTTP 500:
  - DATABASE_URL missing, empty, or password not URL-encoded
  - DATABASE_URL password diverged from POSTGRES_PASSWORD (compose auth)
  - Next still healthy-looking while One-Brain snapshot cannot authenticate

Does NOT db:migrate / db:push. Does NOT touch Lane-A. Does NOT claim READY.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$NoWrite
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}
Set-Location -LiteralPath $RepoRoot

function Get-EnvValue([string]$Path, [string]$Key) {
  if (-not (Test-Path -LiteralPath $Path)) { return "" }
  foreach ($line in (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
    $t = $line.Trim()
    if ($t.StartsWith("#") -or ($t.IndexOf("=") -lt 1)) { continue }
    $k = $t.Substring(0, $t.IndexOf("=")).Trim()
    if ($k -ne $Key) { continue }
    $v = $t.Substring($t.IndexOf("=") + 1).Trim()
    if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
      $v = $v.Substring(1, $v.Length - 2)
    }
    return $v
  }
  return ""
}

function Set-EnvValue([string]$Path, [string]$Key, [string]$Value) {
  $lines = @()
  $found = $false
  if (Test-Path -LiteralPath $Path) {
    foreach ($line in (Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
      $t = $line.Trim()
      if (-not $t.StartsWith("#") -and ($t.IndexOf("=") -ge 1)) {
        $k = $t.Substring(0, $t.IndexOf("=")).Trim()
        if ($k -eq $Key) {
          $lines += ($Key + "=" + $Value)
          $found = $true
          continue
        }
      }
      $lines += $line
    }
  }
  if (-not $found) {
    $lines += ""
    $lines += ($Key + "=" + $Value)
  }
  $utf8Bom = New-Object System.Text.UTF8Encoding $true
  [System.IO.File]::WriteAllLines($Path, $lines, $utf8Bom)
}

function Encode-PgUrlPart([string]$Raw) {
  if ($null -eq $Raw) { return "" }
  return [Uri]::EscapeDataString($Raw)
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS ensure DATABASE_URL (G2 / STATE B / no migrate)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$envPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
  Write-Host "FAIL: .env missing" -ForegroundColor Red
  exit 2
}

$pgUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
$pgDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
$pgPass = Get-EnvValue -Path $envPath -Key "POSTGRES_PASSWORD"
if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "ahos_user" }
if ([string]::IsNullOrWhiteSpace($pgDb)) { $pgDb = "ahos" }
if ([string]::IsNullOrWhiteSpace($pgPass)) {
  Write-Host "FAIL: POSTGRES_PASSWORD unset -- required by docker compose postgres" -ForegroundColor Red
  exit 2
}

$expected = "postgresql://{0}:{1}@127.0.0.1:5432/{2}" -f $pgUser, (Encode-PgUrlPart $pgPass), $pgDb
$current = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
$redacted = $expected -replace '(:[^:@/]+)@', ':***@'

if ($current -ne $expected) {
  if ($NoWrite) {
    Write-Host "WARN: DATABASE_URL does not match POSTGRES_* (NoWrite set; not fixing)" -ForegroundColor Yellow
  } else {
    Write-Host "Updating DATABASE_URL to match POSTGRES_* (password URL-encoded)..." -ForegroundColor Yellow
    Set-EnvValue -Path $envPath -Key "DATABASE_URL" -Value $expected
    Write-Host ("  DATABASE_URL=" + $redacted) -ForegroundColor Green
  }
} else {
  Write-Host ("OK DATABASE_URL already matches POSTGRES_* -> " + $redacted) -ForegroundColor Green
}

$probeOut = Join-Path $RepoRoot "reports\pg_probe_latest.json"
$psProbe = Join-Path $RepoRoot "scripts\windows_pg_probe.ps1"
$mjs = Join-Path $RepoRoot "scripts\ahos_pg_probe.mjs"
if (Test-Path -LiteralPath $psProbe) {
  Write-Host "==> windows_pg_probe.ps1 (One-Brain snapshot queries; unlock-safe)" -ForegroundColor Cyan
  & powershell -NoProfile -ExecutionPolicy Bypass -File $psProbe -RepoRoot $RepoRoot -JsonOut $probeOut
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    Write-Host "FAIL: Postgres snapshot probe failed (see reports\pg_probe_latest.json)" -ForegroundColor Red
    Write-Host "Remediation: confirm ahos_postgres_win up; POSTGRES_PASSWORD matches DATABASE_URL; restart npm run dev" -ForegroundColor Yellow
    Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
    exit 2
  }
  Write-Host "OK pg probe -- ahos_* readable" -ForegroundColor Green
} elseif (Test-Path -LiteralPath $mjs) {
  Write-Host "==> node scripts/ahos_pg_probe.mjs" -ForegroundColor Cyan
  & node $mjs --json-out $probeOut
  if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: host DATABASE_URL cannot run snapshot queries" -ForegroundColor Red
    exit 2
  }
  Write-Host "OK pg probe -- ahos_* readable via DATABASE_URL" -ForegroundColor Green
} else {
  Write-Host "WARN: no pg probe script -- DATABASE_URL written but not verified" -ForegroundColor DarkYellow
}

Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
exit 0
