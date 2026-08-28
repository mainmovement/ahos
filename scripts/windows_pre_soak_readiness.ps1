#Requires -Version 5.1
# AHOS Windows -- pre-soak readiness checklist (READ-MOSTLY)
#
# Prints an honest blocker card before/without inventing PRE_SOAK or READY.
# STATE B: never db:migrate / db:push.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_pre_soak_readiness.ps1
#
# Exit 0 = no hard blockers for attempting AHOS_WINDOWS_OPS.bat
# Exit 2 = hard blockers (token/gateway/docker/postgres/node)
# Encoding: ASCII-only + UTF-8 BOM (WinPS 5.1 safe).
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [string]$PostgresContainer = "ahos_postgres_win",
    [string]$GatewayDefault = "http://127.0.0.1:3000/api/chat"
)

$ErrorActionPreference = "Continue"

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

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS pre-soak readiness (no migrate / no READY claim)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray

$fails = 0
$warns = 0
$envPath = Join-Path $RepoRoot ".env"

$head = "UNKNOWN"
try { $head = (& git rev-parse --short HEAD 2>$null).Trim() } catch {}
Write-Check "git_head" "PASS" $head

$token = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"
$pub = Get-EnvValue -Path $envPath -Key "NEXT_PUBLIC_AHOS_WEB_API_TOKEN"
if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Check "AHOS_WEB_API_TOKEN" "FAIL" "unset - run windows_ensure_web_api_token.ps1"
    $fails++
} else {
    Write-Check "AHOS_WEB_API_TOKEN" "PASS" "set"
    if ($pub -ne $token) {
        Write-Check "NEXT_PUBLIC_match" "FAIL" "NEXT_PUBLIC must match token"
        $fails++
    } else {
        Write-Check "NEXT_PUBLIC_match" "PASS" "matches"
    }
}

$gw = Get-EnvValue -Path $envPath -Key "AHOS_GATEWAY_URL"
if ([string]::IsNullOrWhiteSpace($gw)) {
    Write-Check "AHOS_GATEWAY_URL" "FAIL" ("empty - ensure will set " + $GatewayDefault)
    $fails++
} else {
    Write-Check "AHOS_GATEWAY_URL" "PASS" $gw
}

$db = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
if ([string]::IsNullOrWhiteSpace($db)) {
    Write-Check "DATABASE_URL" "FAIL" "unset in .env"
    $fails++
} else {
    Write-Check "DATABASE_URL" "PASS" "set"
}

$pgPass = Get-EnvValue -Path $envPath -Key "POSTGRES_PASSWORD"
if ([string]::IsNullOrWhiteSpace($pgPass)) {
    Write-Check "POSTGRES_PASSWORD" "FAIL" "unset - compose cannot start ahos_postgres_win"
    $fails++
} else {
    Write-Check "POSTGRES_PASSWORD" "PASS" "set"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Check "docker" "FAIL" "docker not on PATH - install Docker Desktop"
    $fails++
} else {
    $info = & docker info 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Check "docker_daemon" "FAIL" "Docker Desktop Linux Engine not reachable (start Desktop; wait green)"
        $fails++
        if ($info -match "dockerDesktopLinuxEngine" -or $info -match "pipe") {
            Write-Host "         hint: dockerDesktopLinuxEngine pipe not found = engine still starting" -ForegroundColor DarkYellow
        }
    } else {
        Write-Check "docker_daemon" "PASS" "docker info ok"
        $running = (& docker ps --format "{{.Names}}" 2>$null)
        if ($running -match [regex]::Escape($PostgresContainer)) {
            Write-Check "postgres_container" "PASS" ($PostgresContainer + " running")
        } else {
            Write-Check "postgres_container" "WARN" ($PostgresContainer + " not running - bat/ensure-pg will start it")
            $warns++
        }
    }
}

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Check "node" "PASS" ((& node --version) | Out-String).Trim()
} else {
    Write-Check "node" "FAIL" "not on PATH"
    $fails++
}

try {
    $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 3000 -WarningAction SilentlyContinue
    if ($tcp.TcpTestSucceeded) {
        Write-Check "next_3000" "PASS" "listening (restart Next after .env token/gateway changes)"
    } else {
        Write-Check "next_3000" "WARN" "not listening yet - bat will restart npm run dev"
        $warns++
    }
} catch {
    Write-Check "next_3000" "WARN" "could not probe :3000"
    $warns++
}

Write-Host ""
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
Write-Host "This checklist does NOT claim PRE_SOAK or OPERATOR_READY." -ForegroundColor Yellow

if ($fails -gt 0) {
    Write-Host ("READINESS_FAIL hard=" + $fails + " warns=" + $warns) -ForegroundColor Red
    Write-Host "Fix FAILs, then: AHOS_WINDOWS_OPS.bat" -ForegroundColor Yellow
    if ($fails -gt 0) {
        Write-Host "Typical remaining blocker: start Docker Desktop, wait green, docker ps" -ForegroundColor Yellow
    }
    exit 2
}

Write-Host ("READINESS_OK warns=" + $warns + " -- safe to run AHOS_WINDOWS_OPS.bat") -ForegroundColor Green
Write-Host "After bat: paste reports\OWNER_PASTE_WINDOWS_GATE.txt (need pre_soak_entry_ok=true)." -ForegroundColor Cyan
exit 0
