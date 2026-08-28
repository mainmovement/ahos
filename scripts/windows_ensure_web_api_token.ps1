# ==============================================================================
# AHOS Windows — ensure Lane-B web API token in .env (idempotent)
#
# What this does:
#   - If AHOS_WEB_API_TOKEN is missing/empty in .env, generate a random token
#   - Write BOTH AHOS_WEB_API_TOKEN and NEXT_PUBLIC_AHOS_WEB_API_TOKEN (same value)
#   - Force AHOS_WEB_API_ALLOW_OPEN_ACCESS=0 when absent
#   - Never overwrite a non-empty existing AHOS_WEB_API_TOKEN
#   - Never migrate / reset / stash / touch Lane-A
#
# Usage (from G:\robat\ahos):
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_ensure_web_api_token.ps1
#
# Encoding: ASCII-only punctuation (WinPS 5.1 safe).
# ==============================================================================

param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

function Get-EnvValue([string]$Path, [string]$Key) {
    if (-not (Test-Path -LiteralPath $Path)) { return "" }
    $lines = Get-Content -LiteralPath $Path -ErrorAction Stop
    foreach ($line in $lines) {
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

function Set-Or-Append-EnvKey([string]$Path, [string]$Key, [string]$Value) {
    $lines = @()
    if (Test-Path -LiteralPath $Path) {
        $lines = @(Get-Content -LiteralPath $Path -ErrorAction Stop)
    }
    $found = $false
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($line in $lines) {
        $t = $line.Trim()
        if (-not $t.StartsWith("#") -and ($t.IndexOf("=") -ge 1)) {
            $k = $t.Substring(0, $t.IndexOf("=")).Trim()
            if ($k -eq $Key) {
                $out.Add($Key + "=" + $Value) | Out-Null
                $found = $true
                continue
            }
        }
        $out.Add($line) | Out-Null
    }
    if (-not $found) {
        if ($out.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($out[$out.Count - 1])) {
            $out.Add("") | Out-Null
        }
        $out.Add($Key + "=" + $Value) | Out-Null
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($Path, $out.ToArray(), $utf8NoBom)
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

$EnvPath = Join-Path $RepoRoot ".env"
$Example = Join-Path $RepoRoot ".env.example"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS ensure web API token (fail-closed Lane-B gate)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB or overwrite a non-empty token." -ForegroundColor DarkGray

if (-not (Test-Path -LiteralPath $EnvPath)) {
    if (Test-Path -LiteralPath $Example) {
        Copy-Item -LiteralPath $Example -Destination $EnvPath
        Write-Host "Created .env from .env.example" -ForegroundColor Yellow
    } else {
        New-Item -ItemType File -Path $EnvPath | Out-Null
        Write-Host "Created empty .env" -ForegroundColor Yellow
    }
}

$existing = Get-EnvValue -Path $EnvPath -Key "AHOS_WEB_API_TOKEN"
$pubExisting = Get-EnvValue -Path $EnvPath -Key "NEXT_PUBLIC_AHOS_WEB_API_TOKEN"
$created = $false

if ([string]::IsNullOrWhiteSpace($existing)) {
    $token = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))
    Set-Or-Append-EnvKey -Path $EnvPath -Key "AHOS_WEB_API_TOKEN" -Value $token
    Set-Or-Append-EnvKey -Path $EnvPath -Key "NEXT_PUBLIC_AHOS_WEB_API_TOKEN" -Value $token
    $created = $true
    Write-Host "Generated new AHOS_WEB_API_TOKEN (+ matching NEXT_PUBLIC_)." -ForegroundColor Green
} else {
    Write-Host "AHOS_WEB_API_TOKEN already set — left unchanged." -ForegroundColor Green
    if ([string]::IsNullOrWhiteSpace($pubExisting) -or ($pubExisting -ne $existing)) {
        Set-Or-Append-EnvKey -Path $EnvPath -Key "NEXT_PUBLIC_AHOS_WEB_API_TOKEN" -Value $existing
        Write-Host "Synced NEXT_PUBLIC_AHOS_WEB_API_TOKEN to match server token." -ForegroundColor Yellow
    } else {
        Write-Host "NEXT_PUBLIC_AHOS_WEB_API_TOKEN already matches." -ForegroundColor Green
    }
}

$open = Get-EnvValue -Path $EnvPath -Key "AHOS_WEB_API_ALLOW_OPEN_ACCESS"
if ([string]::IsNullOrWhiteSpace($open)) {
    Set-Or-Append-EnvKey -Path $EnvPath -Key "AHOS_WEB_API_ALLOW_OPEN_ACCESS" -Value "0"
    Write-Host "Set AHOS_WEB_API_ALLOW_OPEN_ACCESS=0" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1) Restart Next:  npm run dev"
Write-Host "  2) Restart Telegram bot if used"
Write-Host "  3) Do NOT run db:migrate / db:push (STATE B)"
Write-Host "  4) Run operator gate when ready:"
Write-Host "     python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill"
if ($created) {
    Write-Host "  Token was newly created this run." -ForegroundColor DarkGray
}
Write-Host "==========================================================" -ForegroundColor Cyan
