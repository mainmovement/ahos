# ==============================================================================
# AHOS Windows - wait until POST /api/chat responds (after Next restart)
#
# Reads AHOS_WEB_API_TOKEN from .env. Does not migrate. Does not claim READY.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_wait_for_web_api.ps1
# Exit 0 = warmed; 2 = timeout
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

$envPath = Join-Path $RepoRoot ".env"
$tok = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"
Write-Host ("  Waiting for " + $Url + " (up to ~" + ($Attempts * $SleepSec) + "s)") -ForegroundColor Cyan
if ([string]::IsNullOrWhiteSpace($tok)) {
    Write-Host "  WARN: AHOS_WEB_API_TOKEN empty — warm may 401/LOCKED" -ForegroundColor Yellow
}

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
        try {
            $null = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 2
        } catch {}
        Start-Sleep -Seconds $SleepSec
    }
}

Write-Host "  TIMEOUT waiting for /api/chat" -ForegroundColor Red
exit 2
