# ==============================================================================
# AHOS Windows - stop anything on 127.0.0.1:3000 then start npm run dev
#
# Why: after windows_ensure_web_api_token.ps1 writes .env, a STALE Next process
# still holds the old token -> G2 WEB_API_UNAUTHORIZED. Port-open != fresh env.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_restart_next_dev.ps1
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [int]$Port = 3000,
    [switch]$NoStart
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  AHOS restart Next.js on 127.0.0.1:" + $Port) -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

function Get-ListenersOnPort([int]$P) {
    $out = @()
    try {
        $conns = Get-NetTCPConnection -LocalPort $P -State Listen -ErrorAction SilentlyContinue
        foreach ($c in $conns) {
            if ($null -ne $c.OwningProcess) { $out += [int]$c.OwningProcess }
        }
    } catch {}
    if ($out.Count -eq 0) {
        try {
            $lines = & netstat -ano -p tcp 2>$null | Select-String (":" + $P + "\s")
            foreach ($line in $lines) {
                $parts = ($line.ToString() -split "\s+") | Where-Object { $_ -ne "" }
                if ($parts.Count -ge 5 -and $parts[-2] -match "LISTENING") {
                    $out += [int]$parts[-1]
                }
            }
        } catch {}
    }
    return @($out | Select-Object -Unique)
}

$pids = Get-ListenersOnPort -P $Port
if ($pids.Count -gt 0) {
    foreach ($procId in $pids) {
        try {
            $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
            $name = if ($null -ne $p) { $p.ProcessName } else { "?" }
            Write-Host ("  Stopping PID " + $procId + " (" + $name + ") on :" + $Port) -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host ("  Could not stop PID " + $procId + ": " + $_.Exception.Message) -ForegroundColor Red
        }
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host ("  No listener on :" + $Port) -ForegroundColor DarkGray
}

if ($NoStart) {
    Write-Host "  NoStart set -- not launching npm." -ForegroundColor DarkGray
    exit 0
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: npm not on PATH" -ForegroundColor Red
    exit 2
}

Write-Host "  Starting npm run dev in a new window..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/k",
    ("cd /d """ + $RepoRoot + """ && echo AHOS Next.js - leave open && npm run dev")
) -WindowStyle Normal

Write-Host "  Launched. Wait for Ready on 127.0.0.1:" + $Port -ForegroundColor Green
exit 0
