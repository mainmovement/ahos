#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure .env DATABASE_URL can run One-Brain snapshot queries (STATE B / no migrate).

Strategy (important for Windows STATE B volumes):
  1) If DATABASE_URL is set, probe it FIRST.
  2) Only rewrite from POSTGRES_* when missing/empty OR probe fails.
  3) Never overwrite a working DATABASE_URL just because it differs from
     POSTGRES_PASSWORD text (container volume may still use the original password).

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

function Invoke-PgProbe([string]$Root, [string]$OutJson) {
  $psProbe = Join-Path $Root "scripts\windows_pg_probe.ps1"
  $mjs = Join-Path $Root "scripts\ahos_pg_probe.mjs"
  if (Test-Path -LiteralPath $psProbe) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $psProbe -RepoRoot $Root -JsonOut $OutJson | Out-Host
    return ($LASTEXITCODE -eq 0)
  }
  if (Test-Path -LiteralPath $mjs) {
    & node $mjs --json-out $OutJson | Out-Host
    return ($LASTEXITCODE -eq 0)
  }
  Write-Host "WARN: no pg probe script present" -ForegroundColor DarkYellow
  return $false
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
$redactedExpected = $expected -replace '(:[^:@/]+)@', ':***@'
$probeOut = Join-Path $RepoRoot "reports\pg_probe_latest.json"
New-Item -ItemType Directory -Force -Path (Split-Path $probeOut) | Out-Null

$currentOk = $false
if (-not [string]::IsNullOrWhiteSpace($current)) {
  $redactedCurrent = $current -replace '(:[^:@/]+)@', ':***@'
  Write-Host ("==> probe current DATABASE_URL first -> " + $redactedCurrent) -ForegroundColor Cyan
  $currentOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut
  if ($currentOk) {
    Write-Host "OK current DATABASE_URL already runs One-Brain queries -- leaving it unchanged" -ForegroundColor Green
    if ($current -ne $expected) {
      Write-Host "NOTE: differs from POSTGRES_* text (likely volume was created with an older password)." -ForegroundColor DarkYellow
      Write-Host "      Not overwriting a working URL (STATE B / no wipe)." -ForegroundColor DarkYellow
    }
    Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
    Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
    exit 0
  }
  Write-Host "Current DATABASE_URL probe FAILED -- will try POSTGRES_* sync" -ForegroundColor Yellow
} else {
  Write-Host "DATABASE_URL empty -- will write from POSTGRES_*" -ForegroundColor Yellow
}

if ($NoWrite) {
  Write-Host "WARN: NoWrite set; not updating DATABASE_URL" -ForegroundColor Yellow
  exit 2
}

Write-Host "Updating DATABASE_URL from POSTGRES_* (password URL-encoded)..." -ForegroundColor Yellow
Set-EnvValue -Path $envPath -Key "DATABASE_URL" -Value $expected
Write-Host ("  DATABASE_URL=" + $redactedExpected) -ForegroundColor Green

Write-Host "==> probe DATABASE_URL after sync" -ForegroundColor Cyan
$afterOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut
if ($afterOk) {
  Write-Host "OK pg probe -- ahos_* readable via DATABASE_URL" -ForegroundColor Green
  Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
  Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
  exit 0
}

# Host TCP auth failed but container local psql often still works (volume password drift).
# STATE B recovery: ALTER ROLE password to match .env POSTGRES_PASSWORD (no wipe / no migrate).
Write-Host "Host DATABASE_URL probe still failing -- trying docker-exec password realign (STATE B)" -ForegroundColor Yellow
$errorClass = ""
try {
  if (Test-Path -LiteralPath $probeOut) {
    $pj = Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json
    $errorClass = [string]$pj.error_class
  }
} catch {}

$container = "ahos_postgres_win"
$dockerOk = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
  $names = (& docker ps --format "{{.Names}}" 2>$null)
  if ($names -match [regex]::Escape($container)) {
    $ping = & docker exec $container psql -U $pgUser -d $pgDb -t -A -c "SELECT 1" 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $ping.Trim() -match "1") {
      $dockerOk = $true
    } else {
      Write-Host ("docker exec psql failed: " + $ping.Trim()) -ForegroundColor DarkYellow
    }
  } else {
    Write-Host ("container not running: " + $container) -ForegroundColor DarkYellow
  }
}

if ($dockerOk) {
  $tag = "ahospw" + [guid]::NewGuid().ToString("N").Substring(0, 10)
  # Dollar-quote password so special chars cannot break SQL.
  $alterSql = ('ALTER ROLE "' + $pgUser + '" WITH PASSWORD $' + $tag + '$' + $pgPass + '$' + $tag + '$;')
  Write-Host ("==> ALTER ROLE " + $pgUser + " password to match .env POSTGRES_PASSWORD (via docker exec)") -ForegroundColor Cyan
  $alterOut = & docker exec $container psql -U $pgUser -d $pgDb -v ON_ERROR_STOP=1 -c $alterSql 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) {
    Write-Host ("ALTER ROLE failed: " + $alterOut.Trim()) -ForegroundColor Red
  } else {
    Write-Host "ALTER ROLE ok -- re-probing host DATABASE_URL" -ForegroundColor Green
    $realignOk = Invoke-PgProbe -Root $RepoRoot -OutJson $probeOut
    if ($realignOk) {
      Write-Host "OK pg probe after password realign -- ahos_* readable via DATABASE_URL" -ForegroundColor Green
      Write-Host "Next must be restarted to load DATABASE_URL: scripts\windows_restart_next_dev.ps1" -ForegroundColor Cyan
      Write-Host "STATE B: do NOT db:migrate / db:push / do NOT docker volume rm" -ForegroundColor Yellow
      exit 0
    }
  }
} else {
  Write-Host ("docker-exec realign skipped (error_class=" + $errorClass + ")") -ForegroundColor DarkYellow
}

Write-Host "FAIL: Postgres snapshot probe still failing after sync/realign (see reports\pg_probe_latest.json)" -ForegroundColor Red
Write-Host "Remediation:" -ForegroundColor Yellow
Write-Host "  1) Confirm ahos_postgres_win is up (pg_isready)" -ForegroundColor Yellow
Write-Host "  2) If POSTGRES_PASSWORD was changed after first compose up, realign failed -- put the ORIGINAL password into POSTGRES_PASSWORD + DATABASE_URL (do NOT wipe volume under STATE B)." -ForegroundColor Yellow
Write-Host "  3) scripts\windows_recover_g2_warm.ps1" -ForegroundColor Yellow
Write-Host "STATE B: do NOT db:migrate / db:push / do NOT docker volume rm" -ForegroundColor Yellow
exit 2
