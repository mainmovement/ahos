# ==============================================================================
# AHOS Windows preflight (READ-MOSTLY) before operator gate
#
# Checks (no migrate / no READY claim):
#   - git HEAD / web_api_auth present
#   - .env DATABASE_URL + AHOS_WEB_API_TOKEN (+ NEXT_PUBLIC match)
#   - docker ahos_postgres_win running (best-effort)
#   - node/npm on PATH
#   - optional: TCP 127.0.0.1:3000 listening
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_preflight_ops.ps1
# Exit 0 = no hard fails; 2 = hard fail (fix before gate)
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [string]$PostgresContainer = "ahos_postgres_win"
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
Write-Host "  AHOS Windows preflight (no migrate / no READY claim)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray

$fails = 0
$warns = 0

$head = "UNKNOWN"
try { $head = (& git rev-parse --short HEAD 2>$null).Trim() } catch {}
Write-Check "git_head" "PASS" $head

if (Test-Path -LiteralPath (Join-Path $RepoRoot "web_api_auth.ts")) {
    Write-Check "web_api_auth" "PASS" "present"
} else {
    Write-Check "web_api_auth" "FAIL" "missing - git pull main (need PR #31+)"
    $fails++
}

$envPath = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $envPath)) {
    Write-Check "dotenv" "FAIL" ".env missing - copy .env.example or run ensure token script"
    $fails++
} else {
    Write-Check "dotenv" "PASS" ".env present"
}

$db = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
if ([string]::IsNullOrWhiteSpace($db)) {
    Write-Check "DATABASE_URL" "FAIL" "unset in .env - G2 will FAIL"
    $fails++
} else {
    Write-Check "DATABASE_URL" "PASS" "set (reachability probed next)"
    # Best-effort TCP to host:port from URL -- no migrate, no READY claim
    try {
        $m = [regex]::Match($db, '(?i)(?:postgres(?:ql)?://[^@]+@)?([^:/?\s]+):(\d+)')
        if ($m.Success) {
            $dbHost = $m.Groups[1].Value
            $dbPort = [int]$m.Groups[2].Value
            $tcp = Test-NetConnection -ComputerName $dbHost -Port $dbPort -WarningAction SilentlyContinue
            if ($tcp.TcpTestSucceeded) {
                Write-Check "DATABASE_URL_tcp" "PASS" ($dbHost + ":" + $dbPort + " accepting")
            } else {
                Write-Check "DATABASE_URL_tcp" "WARN" ($dbHost + ":" + $dbPort + " not accepting - start ahos_postgres_win")
                $warns++
            }
        } else {
            Write-Check "DATABASE_URL_tcp" "WARN" "could not parse host:port from DATABASE_URL"
            $warns++
        }
    } catch {
        Write-Check "DATABASE_URL_tcp" "WARN" "could not probe DATABASE_URL host"
        $warns++
    }
}

$token = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"
$pub = Get-EnvValue -Path $envPath -Key "NEXT_PUBLIC_AHOS_WEB_API_TOKEN"
$open = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_ALLOW_OPEN_ACCESS"
if ([string]::IsNullOrWhiteSpace($token)) {
    if ($open -in @("1", "true", "yes", "on")) {
        Write-Check "AHOS_WEB_API_TOKEN" "WARN" "empty but OPEN_ACCESS enabled (local only)"
        $warns++
    } else {
        Write-Check "AHOS_WEB_API_TOKEN" "FAIL" "unset - run windows_ensure_web_api_token.ps1"
        $fails++
    }
} else {
    Write-Check "AHOS_WEB_API_TOKEN" "PASS" "set"
    if ($pub -ne $token) {
        Write-Check "NEXT_PUBLIC_AHOS_WEB_API_TOKEN" "FAIL" "must match AHOS_WEB_API_TOKEN"
        $fails++
    } else {
        Write-Check "NEXT_PUBLIC_AHOS_WEB_API_TOKEN" "PASS" "matches"
    }
}

$gw = Get-EnvValue -Path $envPath -Key "AHOS_GATEWAY_URL"
if ([string]::IsNullOrWhiteSpace($gw)) {
    Write-Check "AHOS_GATEWAY_URL" "FAIL" "empty - run windows_ensure_web_api_token.ps1 (sets http://127.0.0.1:3000/api/chat)"
    $fails++
} else {
    Write-Check "AHOS_GATEWAY_URL" "PASS" $gw
}

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Check "node" "PASS" ((& node --version) | Out-String).Trim()
} else {
    Write-Check "node" "FAIL" "not on PATH"
    $fails++
}
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Check "npm" "PASS" ((& npm --version) | Out-String).Trim()
} else {
    Write-Check "npm" "FAIL" "not on PATH"
    $fails++
}

$dockerOk = $false
if (Get-Command docker -ErrorAction SilentlyContinue) {
    $running = (& docker ps --format "{{.Names}}" 2>$null)
    if ($running -match [regex]::Escape($PostgresContainer)) {
        Write-Check "postgres_container" "PASS" ($PostgresContainer + " running")
        $dockerOk = $true
    } else {
        Write-Check "postgres_container" "WARN" ($PostgresContainer + " not running - start compose windows")
        $warns++
    }
} else {
    Write-Check "docker" "WARN" "docker not on PATH - ensure Postgres reachable for DATABASE_URL"
    $warns++
}

if ($dockerOk) {
    $PostgresUser = Get-EnvValue -Path $envPath -Key "POSTGRES_USER"
    $PostgresDb = Get-EnvValue -Path $envPath -Key "POSTGRES_DB"
    if ([string]::IsNullOrWhiteSpace($PostgresUser)) { $PostgresUser = "ahos_user" }
    if ([string]::IsNullOrWhiteSpace($PostgresDb)) { $PostgresDb = "ahos" }
    try {
        $ping = & docker exec $PostgresContainer pg_isready -U $PostgresUser -d $PostgresDb 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Check "postgres_ready" "PASS" (($ping | Out-String).Trim())
        } else {
            Write-Check "postgres_ready" "WARN" "pg_isready failed - G2 may HTTP 500"
            $warns++
        }
    } catch {
        Write-Check "postgres_ready" "WARN" "could not pg_isready"
        $warns++
    }
}

# Lane-A / One-Brain evidence is SQLite census -- STATE B Postgres rows do not satisfy G4/G5/G8/G9.
$discDb = Join-Path $RepoRoot "data\e01_discovery.sqlite"
$localDb = Join-Path $RepoRoot "data\ahos_local.sqlite"
$hasSqlite = (Test-Path -LiteralPath $discDb) -or (Test-Path -LiteralPath $localDb)
if ($hasSqlite) {
    Write-Check "sqlite_evidence_files" "PASS" "e01_discovery and/or ahos_local present"
} else {
    Write-Check "sqlite_evidence_files" "WARN" "missing data\\*.sqlite -- run a local single-cycle before gate or G4/G5/G8/G9 FAIL"
    $warns++
}

# Best-effort port 3000
try {
    $tcp = Test-NetConnection -ComputerName 127.0.0.1 -Port 3000 -WarningAction SilentlyContinue
    if ($tcp.TcpTestSucceeded) {
        Write-Check "next_3000" "PASS" "127.0.0.1:3000 accepting TCP (restart Next after token changes)"
    } else {
        Write-Check "next_3000" "WARN" "not listening - start npm run dev before gate"
        $warns++
    }
} catch {
    Write-Check "next_3000" "WARN" "could not probe port 3000"
    $warns++
}

Write-Host ""
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
Write-Host "OPERATOR_READY is NOT claimed by preflight." -ForegroundColor Yellow

if ($fails -gt 0) {
    Write-Host ("PREFLIGHT_FAIL count=" + $fails + " warns=" + $warns) -ForegroundColor Red
    Write-Host "Fix FAILs, then: windows_run_operator_gate.ps1" -ForegroundColor Yellow
    exit 2
}

Write-Host ("PREFLIGHT_OK warns=" + $warns) -ForegroundColor Green
Write-Host "Next: windows_restart_next_dev.ps1 (if needed), then windows_run_operator_gate.ps1" -ForegroundColor Cyan
exit 0
