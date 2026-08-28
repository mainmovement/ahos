#Requires -Version 5.1
<#
.SYNOPSIS
  Diagnose Windows Docker health for PAPER_ONLY G2 (no migrate).

Focus: ahos_postgres_win accepting connections + honest notes on
ahos_runtime_win unhealthy (NOT required for host Next /api/chat G2).

STATE B: never db:migrate / db:push. Does NOT claim PRE_SOAK or READY.
Encoding: ASCII-only + UTF-8 BOM (WinPS 5.1 safe).
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$PostgresContainer = "ahos_postgres_win",
  [string]$RuntimeContainer = "ahos_runtime_win",
  [string]$N8nContainer = "ahos_n8n_win"
)

$ErrorActionPreference = "Continue"

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

function Write-Check([string]$Name, [string]$Status, [string]$Detail) {
  $color = "Green"
  if ($Status -eq "FAIL") { $color = "Red" }
  elseif ($Status -eq "WARN") { $color = "Yellow" }
  Write-Host ("  [" + $Status + "] " + $Name + " - " + $Detail) -ForegroundColor $color
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Docker health diagnose (G2 / STATE B / no migrate)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$fails = 0
$warns = 0
$envPath = Join-Path $RepoRoot ".env"
$pgUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
$pgDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "ahos_user" }
if ([string]::IsNullOrWhiteSpace($pgDb)) { $pgDb = "ahos" }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Check "docker" "FAIL" "docker not on PATH"
  exit 2
}

& docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
  Write-Check "docker_daemon" "FAIL" "Docker Desktop Linux Engine not reachable"
  exit 2
}
Write-Check "docker_daemon" "PASS" "docker info ok"

# --- postgres (required for G2 / One-Brain) ---
$psRow = (& docker ps -a --filter ("name=^/" + $PostgresContainer + "$") --format "{{.Status}}" 2>$null | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($psRow)) {
  Write-Check "postgres_present" "FAIL" ($PostgresContainer + " missing - run windows_ensure_postgres_win.ps1")
  $fails++
} else {
  Write-Check "postgres_status" "PASS" $psRow
  if ($psRow -match "unhealthy") {
    Write-Check "postgres_docker_health" "WARN" "Docker label unhealthy -- G2 still OK if pg_isready passes (healthcheck may be stale/wrong)"
    $warns++
    try {
      $log = & docker inspect --format "{{json .State.Health}}" $PostgresContainer 2>$null
      if ($log) {
        Write-Host "         health_json (truncated):" -ForegroundColor DarkGray
        $trim = $log
        if ($trim.Length -gt 500) { $trim = $trim.Substring(0, 500) + "..." }
        Write-Host ("         " + $trim) -ForegroundColor DarkGray
      }
    } catch {}
  } elseif ($psRow -match "healthy") {
    Write-Check "postgres_docker_health" "PASS" "healthy"
  } else {
    Write-Check "postgres_docker_health" "WARN" "no health label yet / starting"
    $warns++
  }

  & docker exec $PostgresContainer pg_isready -U $pgUser -d $pgDb 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) {
    Write-Check "pg_isready" "PASS" ("-U " + $pgUser + " -d " + $pgDb + " (G2 DB path usable)")
  } else {
    Write-Check "pg_isready" "FAIL" ("not accepting connections as " + $pgUser + "/" + $pgDb + " -- restart container once, do NOT migrate")
    $fails++
    Write-Host "         remediation: docker restart ahos_postgres_win" -ForegroundColor Yellow
    Write-Host "         then: powershell -File .\scripts\windows_ensure_postgres_win.ps1" -ForegroundColor Yellow
  }
}

# --- runtime (NOT required for host Next G2 PAPER_ONLY) ---
$rt = (& docker ps -a --filter ("name=^/" + $RuntimeContainer + "$") --format "{{.Status}}" 2>$null | Select-Object -First 1)
if ([string]::IsNullOrWhiteSpace($rt)) {
  Write-Check "runtime" "WARN" ($RuntimeContainer + " absent -- OK for host npm run dev G2")
  $warns++
} else {
  if ($rt -match "unhealthy") {
    Write-Check "runtime" "WARN" ($rt + " -- NOT a G2 blocker; PAPER_ONLY uses host Next :3000, not container :8000")
    $warns++
  } else {
    Write-Check "runtime" "PASS" $rt
  }
}

$n8n = (& docker ps -a --filter ("name=^/" + $N8nContainer + "$") --format "{{.Status}}" 2>$null | Select-Object -First 1)
if (-not [string]::IsNullOrWhiteSpace($n8n)) {
  Write-Check "n8n" "PASS" $n8n
}

Write-Host ""
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
Write-Host "Lane-A freeze: do not touch frozen Lane-A paths." -ForegroundColor Yellow
Write-Host "G2 needs: pg_isready PASS + host Next POST /api/chat (AHOS_WINDOWS_OPS.bat)." -ForegroundColor Cyan
Write-Host "ahos_runtime_win unhealthy does NOT block PRE_SOAK entry." -ForegroundColor Cyan

if ($fails -gt 0) {
  Write-Host ("DIAGNOSE_FAIL hard=" + $fails + " warns=" + $warns) -ForegroundColor Red
  exit 2
}
Write-Host ("DIAGNOSE_OK warns=" + $warns + " -- safe to continue G2 validation") -ForegroundColor Green
exit 0
