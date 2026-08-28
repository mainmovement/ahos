# ==============================================================================
# AHOS Windows G11 helper -- scaffold Telegram E2E artifact (not auto-PASS)
#
# Creates reports\telegram_e2e_<UTC>.md checklist for the owner to fill after
# live BotFather checks (docs\TELEGRAM_OPERATOR_E2E_PROTOCOL.md).
# Does NOT invent PASS / OPERATOR_READY. Does NOT migrate.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_g11_telegram_e2e_helper.ps1
# ==============================================================================

param(
    [string]$RepoRoot = ""
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

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS G11 Telegram E2E scaffold (no READY claim)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$envPath = Join-Path $RepoRoot ".env"
$token = Get-EnvValue -Path $envPath -Key "TELEGRAM_BOT_TOKEN"
$allow = Get-EnvValue -Path $envPath -Key "TELEGRAM_ALLOWED_CHAT_IDS"
$web = Get-EnvValue -Path $envPath -Key "AHOS_WEB_API_TOKEN"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host "  [FAIL] TELEGRAM_BOT_TOKEN unset in .env" -ForegroundColor Red
} else {
    Write-Host "  [OK] TELEGRAM_BOT_TOKEN set" -ForegroundColor Green
}
if ([string]::IsNullOrWhiteSpace($allow)) {
    Write-Host "  [FAIL] TELEGRAM_ALLOWED_CHAT_IDS unset (fail-closed)" -ForegroundColor Red
} else {
    Write-Host "  [OK] TELEGRAM_ALLOWED_CHAT_IDS set" -ForegroundColor Green
}
if ([string]::IsNullOrWhiteSpace($web)) {
    Write-Host "  [WARN] AHOS_WEB_API_TOKEN unset -- gateway may 401" -ForegroundColor Yellow
} else {
    Write-Host "  [OK] AHOS_WEB_API_TOKEN set" -ForegroundColor Green
}

$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd_HHmmss")
$out = Join-Path $RepoRoot ("reports\telegram_e2e_" + $stamp + ".md")
$reports = Join-Path $RepoRoot "reports"
if (-not (Test-Path -LiteralPath $reports)) {
    New-Item -ItemType Directory -Path $reports -Force | Out-Null
}

$lines = @(
    "# AHOS Telegram operator E2E transcript",
    "",
    ("- generated_utc: " + $stamp),
    "- platform: windows",
    "- PAPER_ONLY: 1",
    "- STATE B: do not db:migrate / db:push",
    "- OPERATOR_READY: NOT claimed by this scaffold",
    "",
    "## Preconditions checked by owner",
    "",
    "- [ ] TELEGRAM_BOT_TOKEN set",
    "- [ ] TELEGRAM_ALLOWED_CHAT_IDS set to my chat id",
    "- [ ] AHOS_WEB_API_TOKEN + NEXT_PUBLIC match; npm run dev on 127.0.0.1:3000",
    "- [ ] Bot / domain service running",
    "",
    "## Protocol checks (fill after live chat)",
    "",
    "1. Persian greeting -- reply exists; not independent score when gateway down",
    "   - result:",
    "   - notes:",
    "",
    "2. Stop npm run dev; send message -- EMERGENCY_FALLBACK_ONLY / honesty",
    "   - result:",
    "   - notes:",
    "",
    "3. Restart gateway; ask for new opportunities -- source=conversation_gateway",
    "   - result:",
    "   - notes:",
    "",
    "4. Ask risk for a known symbol -- no fabricated prices",
    "   - result:",
    "   - notes:",
    "",
    "5. Honeypot/rejected token (if available) -- security veto language",
    "   - result:",
    "   - notes:",
    "",
    "## Redaction",
    "",
    "- Do not paste TELEGRAM_BOT_TOKEN or AHOS_WEB_API_TOKEN into this file.",
    "- Paste anonymized message excerpts only.",
    "",
    "## Gate re-run (after filling above, file must be >64 bytes)",
    "",
    "powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1 -TelegramE2eArtifact reports\telegram_e2e_$stamp.md",
    "",
    "See docs\TELEGRAM_OPERATOR_E2E_PROTOCOL.md",
    ""
)

$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($out, ($lines -join "`n"), $utf8)
Write-Host ("  Wrote scaffold: " + $out) -ForegroundColor Green
Write-Host "  Fill from a LIVE Telegram session, then re-run gate with -TelegramE2eArtifact." -ForegroundColor Yellow
Write-Host "  Scaffold alone is NOT G11 PASS / NOT OPERATOR_READY." -ForegroundColor Yellow
Write-Host "STATE B: do not db:migrate / db:push" -ForegroundColor Yellow
exit 0
