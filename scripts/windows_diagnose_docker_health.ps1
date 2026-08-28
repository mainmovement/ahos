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

# Host TCP :5432 (Next DATABASE_URL typically targets 127.0.0.1:5432)
try {
  $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue
  if ($tcp.TcpTestSucceeded) {
    Write-Check "tcp_5432" "PASS" "127.0.0.1:5432 accepting (host Next can reach Postgres)"
  } else {
    Write-Check "tcp_5432" "FAIL" "127.0.0.1:5432 not accepting -- Postgres publish/port mapping issue"
    $fails++
  }
} catch {
  Write-Check "tcp_5432" "WARN" "could not probe :5432"
  $warns++
}

$dbUrl = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
if ([string]::IsNullOrWhiteSpace($dbUrl)) {
  Write-Check "DATABASE_URL" "FAIL" "unset in .env (One-Brain /api/chat needs it)"
  $fails++
} else {
  $redacted = $dbUrl
  try {
    $redacted = [regex]::Replace($dbUrl, '(:[^:@/]+)@', ':***@')
  } catch {}
  if ($redacted -match '127\.0\.0\.1:5432' -or $redacted -match 'localhost:5432') {
    Write-Check "DATABASE_URL" "PASS" $redacted
  } else {
    Write-Check "DATABASE_URL" "WARN" ("set but host may not be local publish: " + $redacted)
    $warns++
  }
}

# Credential/query probe — string presence alone does not prove /api/chat can snapshot.
$probeOut = Join-Path $RepoRoot "reports\pg_probe_latest.json"
New-Item -ItemType Directory -Force -Path (Split-Path $probeOut) | Out-Null
$psProbe = Join-Path $RepoRoot "scripts\windows_pg_probe.ps1"
$mjsProbe = Join-Path $RepoRoot "scripts\ahos_pg_probe.mjs"
$probeJson = ""
$probeOk = $false
if (Test-Path -LiteralPath $psProbe) {
  $probeJson = & powershell -NoProfile -ExecutionPolicy Bypass -File $psProbe -RepoRoot $RepoRoot -JsonOut $probeOut 2>&1 | Out-String
  $probeOk = ($LASTEXITCODE -eq 0)
} elseif (Test-Path -LiteralPath $mjsProbe) {
  $probeJson = & node $mjsProbe --json-out $probeOut 2>&1 | Out-String
  $probeOk = ($LASTEXITCODE -eq 0)
}
if (-not [string]::IsNullOrWhiteSpace($probeJson) -or (Test-Path -LiteralPath $probeOut)) {
  $probeClass = ""
  try {
    if (Test-Path -LiteralPath $probeOut) {
      $pj = Get-Content -LiteralPath $probeOut -Raw | ConvertFrom-Json
    } else {
      $pj = $probeJson | ConvertFrom-Json
    }
    $probeClass = [string]$pj.error_class
    if ($pj.ok) { $probeOk = $true }
  } catch {}
  if ($probeOk) {
    Write-Check "database_url_query" "PASS" "ahos_system_state readable (pg probe)"
  } else {
    Write-Check "database_url_query" "FAIL" ("One-Brain snapshot blocked: " + $(if ($probeClass) { $probeClass } else { "see reports\pg_probe_latest.json" }))
    $fails++
    Write-Host "         remediation: powershell -ExecutionPolicy Bypass -File .\\scripts\\windows_ensure_database_url.ps1" -ForegroundColor Yellow
    Write-Host "         then: powershell -ExecutionPolicy Bypass -File .\\scripts\\windows_restart_next_dev.ps1" -ForegroundColor Yellow
    Write-Host "         forensics: powershell -ExecutionPolicy Bypass -File .\\scripts\\windows_chat_500_forensics.ps1" -ForegroundColor Yellow
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
    Write-Host "         tip: docker update --no-healthcheck ahos_runtime_win  (no rebuild; G2 uses host Next)" -ForegroundColor DarkYellow
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
