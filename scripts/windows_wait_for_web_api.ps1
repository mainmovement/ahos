# ==============================================================================
# AHOS Windows - wait until POST /api/chat responds (after Next restart)
#
# Reads AHOS_WEB_API_TOKEN from .env. Does not migrate. Does not claim READY.
# Fail-fast on auth/DB errors once Next is answering HTTP (no silent 180s).
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_wait_for_web_api.ps1
# Exit 0 = warmed (2xx); 2 = timeout or fail-fast remediation needed
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [string]$Url = "http://127.0.0.1:3000/api/chat",
    [int]$Attempts = 90,
    [int]$SleepSec = 2,
    [int]$TimeoutSec = 45
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
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

function Get-HttpStatusFromError($err) {
    try {
        $resp = $err.Exception.Response
        if ($null -eq $resp) { return 0 }
        return [int]$resp.StatusCode
    } catch { return 0 }
}

function Get-HttpBodyFromError($err) {
    try {
        $resp = $err.Exception.Response
        if ($null -eq $resp) { return "" }
        $stream = $resp.GetResponseStream()
        if ($null -eq $stream) { return "" }
        $reader = New-Object System.IO.StreamReader($stream)
        $text = $reader.ReadToEnd()
        $reader.Close()
        if ($text.Length -gt 400) { return $text.Substring(0, 400) }
        return $text
    } catch { return "" }
}

$envPath = Join-Path $RepoRoot ".env"
$tok = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"
$db = Get-EnvValue -Path $envPath -Key "DATABASE_URL"
Write-Host ("  Waiting for " + $Url + " (up to ~" + ($Attempts * $SleepSec) + "s)") -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($tok)) {
    Write-Host "  WARN: AHOS_WEB_API_TOKEN empty -- warm may 401/LOCKED" -ForegroundColor Yellow
}
if ([string]::IsNullOrWhiteSpace($db)) {
    Write-Host "  WARN: DATABASE_URL empty -- /api/chat may HTTP 500" -ForegroundColor Yellow
}

function Test-DockerDaemonUp {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { return $false }
    & docker info 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

$consecutiveServerErrors = 0

for ($i = 0; $i -lt $Attempts; $i++) {
    try {
        $headers = @{ "Content-Type" = "application/json" }
        if (-not [string]::IsNullOrWhiteSpace($tok)) {
            $headers["Authorization"] = "Bearer " + $tok
        }
        $body = '{"message":"ping","locale":"fa"}'
        $r = Invoke-WebRequest -Uri $Url -Method POST -Headers $headers -Body $body -UseBasicParsing -TimeoutSec $TimeoutSec
        Write-Host ("  Warm /api/chat HTTP " + $r.StatusCode + " attempt=" + ($i + 1)) -ForegroundColor Green
        exit 0
    } catch {
        $code = Get-HttpStatusFromError -err $_
        $snippet = Get-HttpBodyFromError -err $_
        $attempt = $i + 1

        if ($code -eq 401) {
            Write-Host ("  FAIL-FAST: /api/chat HTTP 401 attempt=" + $attempt) -ForegroundColor Red
            if ($snippet) { Write-Host ("  body: " + $snippet) -ForegroundColor DarkYellow }
            if ($snippet -match "WEB_API_LOCKED_NO_TOKEN") {
                Write-Host "  Remediation: run windows_ensure_web_api_token.ps1, then windows_restart_next_dev.ps1" -ForegroundColor Yellow
            } elseif ($snippet -match "WEB_API_UNAUTHORIZED" -or $snippet -match "WEB_API") {
                Write-Host "  Remediation: Bearer must match AHOS_WEB_API_TOKEN in .env; restart Next after token change" -ForegroundColor Yellow
            } else {
                Write-Host "  Remediation: ensure token in .env matches Next process; re-run bat" -ForegroundColor Yellow
            }
            exit 2
        }

        if ($code -ge 500) {
            $consecutiveServerErrors++
            $dockerUp = Test-DockerDaemonUp
            # Docker down / no DATABASE_URL: fail fast. Docker up + DATABASE_URL:
            # allow ~60s of 5xx for Postgres pool / just-started container races
            # (PRE_SOAK needs G2 PASS; burning 6s then giving up loses the window).
            $limit = 3
            if ($dockerUp -and -not [string]::IsNullOrWhiteSpace($db)) {
                $limit = 30
            }
            Write-Host ("  /api/chat HTTP " + $code + " attempt=" + $attempt + " consecutive5xx=" + $consecutiveServerErrors + "/" + $limit + " docker_up=" + $dockerUp) -ForegroundColor Yellow
            if ($snippet) { Write-Host ("  body: " + $snippet) -ForegroundColor DarkGray }
            if ($consecutiveServerErrors -ge $limit) {
                Write-Host ("  FAIL-FAST: " + $limit + " consecutive 5xx from /api/chat") -ForegroundColor Red
                Write-Host "  Likely cause: Next is up but Postgres unreachable (One-Brain snapshot needs DB)." -ForegroundColor Yellow
                Write-Host "  Remediation: start Docker Desktop Linux Engine (docker ps must work)," -ForegroundColor Yellow
                Write-Host "    then scripts\windows_ensure_postgres_win.ps1; restart Next; re-run bat." -ForegroundColor Yellow
                Write-Host "  If dockerDesktopLinuxEngine pipe not found: open Docker Desktop, wait green." -ForegroundColor Yellow
                Write-Host "  STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
                exit 2
            }
        } else {
            $consecutiveServerErrors = 0
            # Connection refused / timeout while Next boots -- keep waiting
            if (($attempt % 10) -eq 0) {
                Write-Host ("  still waiting (attempt=" + $attempt + ") -- is npm run dev window up?") -ForegroundColor DarkGray
            }
        }
        Start-Sleep -Seconds $SleepSec
    }
}

Write-Host "  TIMEOUT waiting for /api/chat" -ForegroundColor Red
Write-Host "  Remediation: open the Next.js window, fix compile errors, confirm 127.0.0.1:3000, re-run bat" -ForegroundColor Yellow
exit 2
