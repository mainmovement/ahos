# ==============================================================================
# AHOS Windows - best-effort Telegram delivery of OWNER_PASTE
#
# Sends reports\OWNER_PASTE_WINDOWS_GATE.txt (or LATEST summary) to the first
# TELEGRAM_ALLOWED_CHAT_IDS entry when TELEGRAM_BOT_TOKEN is set.
# Never fails the caller. Never claims READY. Does not migrate.
#
# Usage (usually invoked by windows_run_operator_gate.ps1):
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_telegram_send_gate_paste.ps1
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [string]$PastePath = ""
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
$token = Get-EnvValue -Path $envPath -Key "TELEGRAM_BOT_TOKEN"
if ([string]::IsNullOrWhiteSpace($token)) { $token = $env:TELEGRAM_BOT_TOKEN }
$allow = Get-EnvValue -Path $envPath -Key "TELEGRAM_ALLOWED_CHAT_IDS"
if ([string]::IsNullOrWhiteSpace($allow)) { $allow = $env:TELEGRAM_ALLOWED_CHAT_IDS }

if ([string]::IsNullOrWhiteSpace($token) -or [string]::IsNullOrWhiteSpace($allow)) {
    Write-Host "  telegram_send: skipped (TELEGRAM_BOT_TOKEN or TELEGRAM_ALLOWED_CHAT_IDS unset)" -ForegroundColor DarkGray
    exit 0
}

$chatId = ($allow -split ",")[0].Trim()
if ([string]::IsNullOrWhiteSpace($chatId)) {
    Write-Host "  telegram_send: skipped (empty allowlist entry)" -ForegroundColor DarkGray
    exit 0
}

if ([string]::IsNullOrWhiteSpace($PastePath)) {
    $PastePath = Join-Path $RepoRoot "reports\OWNER_PASTE_WINDOWS_GATE.txt"
}
$latest = Join-Path $RepoRoot "reports\LATEST_WINDOWS_GATE.txt"
if (-not (Test-Path -LiteralPath $PastePath)) {
    Write-Host "  telegram_send: skipped (paste file missing)" -ForegroundColor DarkYellow
    exit 0
}

$caption = "AHOS Windows gate paste (NOT OPERATOR_READY). STATE B: no migrate. Forward/paste into Cursor."
if (Test-Path -LiteralPath $latest) {
    $caption = "AHOS gate (NOT READY). " + ((Get-Content -LiteralPath $latest -Raw) -replace "`r?`n", " | ").Trim()
    if ($caption.Length -gt 900) { $caption = $caption.Substring(0, 900) }
}

$api = "https://api.telegram.org/bot" + $token + "/sendDocument"
Write-Host ("  telegram_send: posting OWNER_PASTE to chat_id=" + $chatId + " ...") -ForegroundColor Cyan

# Prefer curl.exe multipart (Win10+); fall back to message-only summary.
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if ($null -ne $curl) {
    $argsCurl = @(
        "-sS", "-X", "POST", $api,
        "-F", ("chat_id=" + $chatId),
        "-F", ("caption=" + $caption),
        "-F", ("document=@" + $PastePath + ";filename=OWNER_PASTE_WINDOWS_GATE.txt")
    )
    if (-not [string]::IsNullOrWhiteSpace($env:ALL_PROXY)) {
        $argsCurl = @("--proxy", $env:ALL_PROXY) + $argsCurl
    } elseif (-not [string]::IsNullOrWhiteSpace($env:HTTPS_PROXY)) {
        $argsCurl = @("--proxy", $env:HTTPS_PROXY) + $argsCurl
    }
    try {
        $out = & curl.exe @argsCurl 2>&1 | Out-String
        if ($out -match '"ok"\s*:\s*true') {
            Write-Host "  telegram_send: OK (document). Forward that file into Cursor." -ForegroundColor Green
            exit 0
        }
        Write-Host ("  telegram_send: document response not ok -- " + $out.Substring(0, [Math]::Min(180, $out.Length))) -ForegroundColor DarkYellow
    } catch {
        Write-Host ("  telegram_send: curl failed -- " + $_.Exception.Message) -ForegroundColor DarkYellow
    }
}

# Fallback: short sendMessage with LATEST pointer only (no secrets expected in LATEST).
try {
    $msgApi = "https://api.telegram.org/bot" + $token + "/sendMessage"
    $body = @{
        chat_id = $chatId
        text = $caption + "`nOpen reports\OWNER_PASTE_WINDOWS_GATE.txt and paste into Cursor."
    } | ConvertTo-Json -Compress
    $resp = Invoke-RestMethod -Uri $msgApi -Method Post -ContentType "application/json; charset=utf-8" -Body $body -TimeoutSec 30
    if ($resp.ok) {
        Write-Host "  telegram_send: OK (message fallback)." -ForegroundColor Green
    } else {
        Write-Host "  telegram_send: message fallback not ok." -ForegroundColor DarkYellow
    }
} catch {
    Write-Host ("  telegram_send: skipped -- " + $_.Exception.Message) -ForegroundColor DarkYellow
}
exit 0
