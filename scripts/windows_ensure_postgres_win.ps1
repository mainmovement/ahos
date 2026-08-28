#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure Windows PAPER_ONLY Postgres (ahos_postgres_win) is listening.

Starts ONLY the postgres service from deployment/docker-compose.windows.yml.
STATE B: do NOT db:migrate / db:push / never wipe volumes.
Does NOT claim OPERATOR_READY or PRE_SOAK.

Encoding: ASCII-only punctuation (WinPS 5.1 safe) + UTF-8 BOM.
#>
[CmdletBinding()]
param(
  [string]$ComposeFile = "",
  [string]$ServiceName = "postgres",
  [string]$ContainerName = "ahos_postgres_win",
  [int]$ReadyTimeoutSec = 90,
  # Owner often starts Docker Desktop then immediately re-runs bat; wait for engine.
  [int]$DockerDaemonWaitSec = 120
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

if ([string]::IsNullOrWhiteSpace($ComposeFile)) {
  $ComposeFile = Join-Path $RepoRoot "deployment\docker-compose.windows.yml"
}

function Write-Step([string]$Msg) {
  Write-Host ("[ensure-pg] {0}" -f $Msg) -ForegroundColor Cyan
}

function Fail([string]$Msg) {
  Write-Host ("[ensure-pg] FAIL: {0}" -f $Msg) -ForegroundColor Red
  Write-Host "[ensure-pg] STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
  exit 1
}

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

if (-not (Test-Path -LiteralPath $ComposeFile)) {
  Fail "Compose file missing: $ComposeFile"
}

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
  Fail "docker not on PATH. Install Docker Desktop, then re-run."
}

# Wait for Docker Desktop Linux Engine (pipe often missing for ~30-90s after launch).
Write-Step ("Waiting for Docker daemon (up to {0}s)..." -f $DockerDaemonWaitSec)
$daemonDeadline = (Get-Date).AddSeconds($DockerDaemonWaitSec)
$daemonOk = $false
$lastDetail = ""
while ((Get-Date) -lt $daemonDeadline) {
  $dockerInfo = & docker info 2>&1 | Out-String
  if ($LASTEXITCODE -eq 0) {
    $daemonOk = $true
    break
  }
  $lastDetail = $dockerInfo
  if ($lastDetail -match "dockerDesktopLinuxEngine" -or $lastDetail -match "pipe") {
    Write-Host "  [ensure-pg] Docker Desktop Linux Engine not ready yet (pipe) -- waiting..." -ForegroundColor DarkYellow
  } else {
    Write-Host "  [ensure-pg] docker info failed -- waiting for Docker Desktop..." -ForegroundColor DarkYellow
  }
  Start-Sleep -Seconds 5
}
if (-not $daemonOk) {
  Fail ("Docker daemon not reachable after {0}s. Start Docker Desktop, wait until green, confirm 'docker ps' works, then re-run. detail={1}" -f $DockerDaemonWaitSec, $lastDetail)
}
Write-Step "Docker daemon reachable"

$envPath = Join-Path $RepoRoot ".env"
$pgUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
$pgDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
$pgPass = Get-EnvValue -Path $envPath -Key "POSTGRES_PASSWORD"
if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "ahos_user" }
if ([string]::IsNullOrWhiteSpace($pgDb)) { $pgDb = "ahos" }
if ([string]::IsNullOrWhiteSpace($pgPass)) {
  Fail "POSTGRES_PASSWORD unset in .env (required by deployment/docker-compose.windows.yml). Set it, then re-run. Do NOT migrate."
}

# Prefer existing container (no recreate / no volume wipe). Unhealthy != dead:
# G2 needs pg_isready, not the Docker health label.
$running = (& docker ps --format "{{.Names}}" 2>$null)
if ($running -match [regex]::Escape($ContainerName)) {
  $statusLine = (& docker ps --filter ("name=^/" + $ContainerName + "$") --format "{{.Status}}" 2>$null | Select-Object -First 1)
  Write-Step ("$ContainerName already running -- " + $statusLine)
  if ($statusLine -match "unhealthy") {
    Write-Host "[ensure-pg] Docker health=unhealthy -- will still require pg_isready (no migrate / no wipe)" -ForegroundColor Yellow
  }
} else {
  Write-Step "docker compose -f $ComposeFile up -d $ServiceName (container $ContainerName)"
  if (Test-Path -LiteralPath $envPath) {
    & docker compose --env-file $envPath -f $ComposeFile up -d $ServiceName
  } else {
    & docker compose -f $ComposeFile up -d $ServiceName
  }
  if ($LASTEXITCODE -ne 0) {
    Fail "docker compose up failed (exit $LASTEXITCODE). Need Docker Desktop green + POSTGRES_PASSWORD in .env"
  }
}

function Test-PgReady {
  & docker exec $ContainerName pg_isready -U $pgUser -d $pgDb 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}

Write-Step "Waiting for pg_isready -U $pgUser -d $pgDb (timeout ${ReadyTimeoutSec}s)..."
$deadline = (Get-Date).AddSeconds($ReadyTimeoutSec)
$ready = $false
while ((Get-Date) -lt $deadline) {
  if (Test-PgReady) {
    $ready = $true
    break
  }
  Start-Sleep -Seconds 2
}

if (-not $ready) {
  Write-Host "[ensure-pg] pg_isready still failing -- one docker restart (no volume wipe, no migrate)" -ForegroundColor Yellow
  & docker restart $ContainerName 2>&1 | Out-Host
  if ($LASTEXITCODE -ne 0) {
    Fail "docker restart $ContainerName failed (exit $LASTEXITCODE)"
  }
  $deadline2 = (Get-Date).AddSeconds($ReadyTimeoutSec)
  while ((Get-Date) -lt $deadline2) {
    if (Test-PgReady) {
      $ready = $true
      break
    }
    Start-Sleep -Seconds 2
  }
}

if (-not $ready) {
  try {
    $healthJson = & docker inspect --format "{{json .State.Health}}" $ContainerName 2>$null
    Write-Host ("[ensure-pg] health inspect: " + $healthJson) -ForegroundColor DarkYellow
  } catch {}
  Fail "Postgres ($ContainerName) did not become ready within ${ReadyTimeoutSec}s (+restart). Do NOT db:migrate / db:push."
}

# Re-apply compose healthcheck definition if file changed (no recreate of volume)
Write-Step "Refreshing postgres service definition (compose up -d, keep volume)"
if (Test-Path -LiteralPath $envPath) {
  & docker compose --env-file $envPath -f $ComposeFile up -d $ServiceName 2>&1 | Out-Host
} else {
  & docker compose -f $ComposeFile up -d $ServiceName 2>&1 | Out-Host
}

Write-Step "OK -- $ContainerName listening (pg_isready). Docker healthy label may lag; G2 uses TCP/SQL."
Write-Step "STATE B: do NOT db:migrate / db:push. ahos_runtime_win unhealthy is OK for host Next G2."

# Sync DATABASE_URL to POSTGRES_* so host Next /api/chat can authenticate (common 500 cause).
$ensureDbUrl = Join-Path $RepoRoot "scripts\windows_ensure_database_url.ps1"
if (Test-Path -LiteralPath $ensureDbUrl) {
  Write-Step "ensure DATABASE_URL matches POSTGRES_* (no migrate)"
  & powershell -NoProfile -ExecutionPolicy Bypass -File $ensureDbUrl -RepoRoot $RepoRoot
  if ($LASTEXITCODE -ne 0) {
    Write-Host "[ensure-pg] WARN: DATABASE_URL probe failed -- /api/chat may still HTTP 500 until fixed" -ForegroundColor Yellow
  }
}

exit 0
