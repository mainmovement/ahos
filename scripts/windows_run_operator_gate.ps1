# ==============================================================================
# AHOS Windows - run operator validation gate (G1-G12 report)
#
# Prerequisites:
#   - Already on main with web_api_auth (PR #31+)
#   - .env has DATABASE_URL + AHOS_WEB_API_TOKEN (use windows_ensure_web_api_token.ps1)
#   - npm run dev is listening on 127.0.0.1:3000 (other terminal)
#   - Never db:migrate / db:push (STATE B)
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\windows_run_operator_gate.ps1
# ==============================================================================

param(
    [string]$RepoRoot = "",
    [switch]$SkipNetwork,
    [switch]$NoProviderProbe,
    [switch]$NoBackupDrill,
    [switch]$SeedEvidenceIfNeeded,
    [string]$TelegramE2eArtifact = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
}
Set-Location -LiteralPath $RepoRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS Windows operator validation gate" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("  Repo: " + $RepoRoot) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB or invent OPERATOR_READY." -ForegroundColor DarkGray

# Force-load auth/DB keys from .env into THIS process so stale $env cannot beat .env.
$envPath = Join-Path $RepoRoot ".env"
if (Test-Path -LiteralPath $envPath) {
    $forceKeys = @(
        "AHOS_WEB_API_TOKEN",
        "NEXT_PUBLIC_AHOS_WEB_API_TOKEN",
        "AHOS_WEB_API_ALLOW_OPEN_ACCESS",
        "DATABASE_URL",
        "AHOS_GATEWAY_URL",
        "AHOS_PAPER_ONLY",
        "AHOS_EVIDENCE_SOURCE"
    )
    foreach ($line in (Get-Content -LiteralPath $envPath -ErrorAction SilentlyContinue)) {
        $t = $line.Trim()
        if ($t.StartsWith("#") -or ($t.IndexOf("=") -lt 1)) { continue }
        $k = $t.Substring(0, $t.IndexOf("=")).Trim()
        if ($forceKeys -notcontains $k) { continue }
        $v = $t.Substring($t.IndexOf("=") + 1).Trim()
        if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
            $v = $v.Substring(1, $v.Length - 2)
        }
        Set-Item -Path ("Env:" + $k) -Value $v
    }
}

$py = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $py)) {
    $py = "python"
}

$env:AHOS_PAPER_ONLY = "1"
if ([string]::IsNullOrWhiteSpace($env:AHOS_EVIDENCE_SOURCE)) {
    $env:AHOS_EVIDENCE_SOURCE = "local"
}

$argsList = @(
    (Join-Path $RepoRoot "scripts\operator_validation_gate.py"),
    "--platform", "windows"
)
if ($SkipNetwork) {
    $argsList += "--skip-network"
} else {
    if (-not $NoProviderProbe) { $argsList += "--probe-providers" }
    if (-not $NoBackupDrill) { $argsList += "--backup-drill" }
}
if (-not [string]::IsNullOrWhiteSpace($TelegramE2eArtifact)) {
    $argsList += @("--telegram-e2e-artifact", $TelegramE2eArtifact)
}

Write-Host ("  python: " + $py) -ForegroundColor DarkGray
Write-Host ("  args: " + ($argsList -join " ")) -ForegroundColor DarkGray

if ($SeedEvidenceIfNeeded) {
    $seed = Join-Path $RepoRoot "scripts\windows_seed_local_evidence.ps1"
    if (Test-Path -LiteralPath $seed) {
        Write-Host "  SeedEvidenceIfNeeded: checking/running local single-cycle..." -ForegroundColor Cyan
        & powershell -ExecutionPolicy Bypass -File $seed
    }
}

& $py @argsList
$code = $LASTEXITCODE
Write-Host ("gate_exit=" + $code)

$reportsDir = Join-Path $RepoRoot "reports"
$latest = Join-Path $reportsDir "LATEST_WINDOWS_GATE.txt"
$paste = Join-Path $reportsDir "OWNER_PASTE_WINDOWS_GATE.txt"
$reportPath = $null
if (Test-Path -LiteralPath $latest) {
    Write-Host "----- LATEST_WINDOWS_GATE.txt -----" -ForegroundColor Yellow
    Get-Content -LiteralPath $latest | ForEach-Object { Write-Host $_ }
    foreach ($line in (Get-Content -LiteralPath $latest)) {
        if ($line -like "report=*") {
            $reportPath = $line.Substring(7).Trim()
            break
        }
    }
}
if ([string]::IsNullOrWhiteSpace($reportPath) -or -not (Test-Path -LiteralPath $reportPath)) {
    $newest = Get-ChildItem -LiteralPath $reportsDir -Filter "operator_validation_report_windows_*.json" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($null -ne $newest) { $reportPath = $newest.FullName }
}

if (-not [string]::IsNullOrWhiteSpace($reportPath) -and (Test-Path -LiteralPath $reportPath)) {
    $lines = @()
    $lines += "===== BEGIN WINDOWS GATE PASTE (into Cursor) ====="
    $lines += ("report_path=" + $reportPath)
    if (Test-Path -LiteralPath $latest) {
        $lines += "--- LATEST_WINDOWS_GATE ---"
        $lines += (Get-Content -LiteralPath $latest)
    }
    $lines += "--- GATE_JSON ---"
    $lines += (Get-Content -LiteralPath $reportPath -Raw)
    $lines += "===== END WINDOWS GATE PASTE ====="
    $lines += "STATE B: do not db:migrate / db:push"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($paste, ($lines -join "`n") + "`n", $utf8)
    Write-Host ("Wrote paste bundle: " + $paste) -ForegroundColor Green
    $clipOk = $false
    try {
        Set-Clipboard -Value ([System.IO.File]::ReadAllText($paste))
        $clipOk = $true
        Write-Host "Copied paste bundle to clipboard — Ctrl+V into Cursor." -ForegroundColor Green
    } catch {
        Write-Host ("Clipboard copy skipped: " + $_.Exception.Message) -ForegroundColor DarkYellow
    }
    try {
        Start-Process -FilePath "notepad.exe" -ArgumentList $paste | Out-Null
        Write-Host "Opened OWNER_PASTE_WINDOWS_GATE.txt in Notepad." -ForegroundColor Cyan
    } catch {
        Write-Host "Open that file and paste its full contents into Cursor." -ForegroundColor Yellow
    }
    if (-not $clipOk) {
        Write-Host "Open that file and paste its full contents into Cursor." -ForegroundColor Yellow
    }

    # Best-effort: post paste to GitHub PR so Cursor agents can fetch without chat paste.
    # Never fails the gate. Prefer current PR; override with AHOS_GATE_PR.
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if ($null -ne $gh) {
        $prNum = $env:AHOS_GATE_PR
        if ([string]::IsNullOrWhiteSpace($prNum)) {
            try {
                $prNum = (& gh pr view --json number -q ".number" 2>$null)
            } catch { $prNum = "" }
        }
        if ([string]::IsNullOrWhiteSpace($prNum)) { $prNum = "34" }
        $pasteBytes = (Get-Item -LiteralPath $paste).Length
        $commentFile = $paste
        if ($pasteBytes -gt 55000) {
            # GitHub comment size guard — post pointer + LATEST only.
            $slim = Join-Path $reportsDir "OWNER_PASTE_WINDOWS_GATE_SLIM.txt"
            $slimLines = @()
            $slimLines += "===== BEGIN WINDOWS GATE PASTE (slim; full in reports\\OWNER_PASTE_WINDOWS_GATE.txt) ====="
            $slimLines += ("report_path=" + $reportPath)
            if (Test-Path -LiteralPath $latest) {
                $slimLines += "--- LATEST_WINDOWS_GATE ---"
                $slimLines += (Get-Content -LiteralPath $latest)
            }
            $slimLines += "Full JSON too large for PR comment; paste OWNER_PASTE_WINDOWS_GATE.txt into Cursor."
            $slimLines += "STATE B: do not db:migrate / db:push"
            [System.IO.File]::WriteAllText($slim, ($slimLines -join "`n") + "`n", $utf8)
            $commentFile = $slim
        }
        try {
            & gh auth status 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                & gh pr comment $prNum --body-file $commentFile 2>&1 | Out-Host
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ("Posted gate paste to PR #" + $prNum + " via gh (agent can fetch).") -ForegroundColor Green
                } else {
                    Write-Host ("gh pr comment failed exit=" + $LASTEXITCODE + " — Ctrl+V paste still required.") -ForegroundColor DarkYellow
                }
            } else {
                Write-Host "gh not authenticated — Ctrl+V paste into Cursor still required." -ForegroundColor DarkYellow
            }
        } catch {
            Write-Host ("gh post skipped: " + $_.Exception.Message) -ForegroundColor DarkYellow
        }
    } else {
        Write-Host "gh CLI not on PATH — Ctrl+V paste into Cursor still required." -ForegroundColor DarkYellow
    }
} else {
    Write-Host "Paste reports\operator_validation_report_windows_*.json into Cursor." -ForegroundColor Yellow
}

Write-Host "STATE B: do not db:migrate / db:push." -ForegroundColor Yellow
exit $code
