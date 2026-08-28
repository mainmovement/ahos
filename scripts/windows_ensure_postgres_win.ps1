#Requires -Version 5.1
<#
.SYNOPSIS
  Ensure Windows PAPER_ONLY Postgres (ahos_postgres_win) is listening.

Starts ONLY the postgres service from deployment/docker-compose.windows.yml.
STATE B: do NOT db:migrate / db:push / never wipe volumes.
Does NOT claim OPERATOR_READY or PRE_SOAK.
#>
[CmdletBinding()]
param(
  [string]$ComposeFile = "",
  [string]$ServiceName = "postgres",
  [string]$ContainerName = "ahos_postgres_win",
  [int]$ReadyTimeoutSec = 90
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

$envPath = Join-Path $RepoRoot ".env"
$pgUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
$pgDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
if ([string]::IsNullOrWhiteSpace($pgUser)) { $pgUser = "ahos_user" }
if ([string]::IsNullOrWhiteSpace($pgDb)) { $pgDb = "ahos" }

# Prefer existing healthy container (no recreate / no volume wipe)
$running = (& docker ps --format "{{.Names}}" 2>$null)
if ($running -match [regex]::Escape($ContainerName)) {
  Write-Step "$ContainerName already running -- checking pg_isready"
} else {
  Write-Step "docker compose -f $ComposeFile up -d $ServiceName (container $ContainerName)"
  if (Test-Path -LiteralPath $envPath) {
    & docker compose --env-file $envPath -f $ComposeFile up -d $ServiceName
  } else {
    & docker compose -f $ComposeFile up -d $ServiceName
  }
  if ($LASTEXITCODE -ne 0) {
    Fail "docker compose up failed (exit $LASTEXITCODE). Need Docker Desktop + POSTGRES_PASSWORD in .env"
  }
}

Write-Step "Waiting for pg_isready -U $pgUser -d $pgDb (timeout ${ReadyTimeoutSec}s)..."
$deadline = (Get-Date).AddSeconds($ReadyTimeoutSec)
$ready = $false
while ((Get-Date) -lt $deadline) {
  & docker exec $ContainerName pg_isready -U $pgUser -d $pgDb 2>$null | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $ready = $true
    break
  }
  Start-Sleep -Seconds 2
}

if (-not $ready) {
  Fail "Postgres ($ContainerName) did not become ready within ${ReadyTimeoutSec}s"
}

Write-Step "OK -- $ContainerName listening. STATE B: do NOT db:migrate / db:push."
exit 0
