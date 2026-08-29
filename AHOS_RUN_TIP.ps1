#Requires -Version 5.1
<#
.SYNOPSIS
  CRLF-safe Windows entry for PRE_SOAK unlock tip (PAPER_ONLY).

Fetches tip via git when possible; if tip fetch fails, downloads surgical
scripts from raw.githubusercontent.com (TLS1.2) and continues.

STATE B: never db:migrate / db:push. Does NOT invent READY.

One-liner from G:\robat\ahos:
  powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; iex (iwr -UseBasicParsing -Uri 'https://raw.githubusercontent.com/mainmovement/ahos/cursor/windows-main-evidence-push-4bde/AHOS_RUN_TIP.ps1').Content"
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$Tip = "cursor/windows-main-evidence-push-4bde",
  [ValidateSet("fix_g2", "main_first", "bootstrap")]
  [string]$Mode = "fix_g2"
)

$ErrorActionPreference = "Continue"

try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    try {
      $RepoRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
    } catch {
      $RepoRoot = ""
    }
  }
  if ([string]::IsNullOrWhiteSpace($RepoRoot) -or -not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
    $RepoRoot = (Get-Location).Path
  }
}
Set-Location -LiteralPath $RepoRoot

# Nested bats must not git-pull over the tip overlay we just checked out.
$env:AHOS_SKIP_GIT_PULL = "1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  AHOS RUN TIP (CRLF-safe entry)" -ForegroundColor Cyan
Write-Host ("  Tip=" + $Tip + " Mode=" + $Mode) -ForegroundColor DarkGray
Write-Host "  Will NOT migrate DB or claim READY" -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ".git"))) {
  Write-Host ("FAIL: not a git repo: " + $RepoRoot) -ForegroundColor Red
  Write-Host "cd /d G:\robat\ahos first, then re-run." -ForegroundColor Yellow
  exit 2
}

function Save-RawTipFile([string]$RelPath) {
  $uri = "https://raw.githubusercontent.com/mainmovement/ahos/" + $Tip + "/" + ($RelPath -replace "\\", "/")
  $out = Join-Path $RepoRoot ($RelPath -replace "/", "\")
  $dir = Split-Path -Parent $out
  if (-not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  Write-Host ("  raw " + $RelPath) -ForegroundColor DarkGray
  $resp = Invoke-WebRequest -UseBasicParsing -Uri $uri
  $ext = [IO.Path]::GetExtension($RelPath).ToLowerInvariant()
  if ($ext -eq ".ps1") {
    $text = [string]$resp.Content
    $bom = New-Object System.Text.UTF8Encoding $true
    [IO.File]::WriteAllText($out, $text, $bom)
  } elseif ($ext -eq ".bat" -or $ext -eq ".cmd") {
    $text = ([string]$resp.Content) -replace "`r?`n", "`r`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($out, $text, $utf8)
  } else {
    $text = [string]$resp.Content
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [IO.File]::WriteAllText($out, $text, $utf8)
  }
}

function Install-TipViaRaw {
  Write-Host "==> tip git fetch failed - downloading surgical scripts via raw HTTPS" -ForegroundColor Yellow
  $files = @(
    "scripts/windows_fix_g2_empty_and_gate.ps1",
    "scripts/windows_checkout_unlock_tip.ps1",
    "scripts/windows_ensure_web_api_token.ps1",
    "scripts/windows_ensure_database_url.ps1",
    "scripts/windows_wait_for_web_api.ps1",
    "scripts/windows_recover_g2_warm.ps1",
    "scripts/windows_run_operator_gate.ps1",
    "scripts/windows_push_gate_evidence.ps1",
    "scripts/windows_post_gate_paste_gh.ps1",
    "scripts/windows_publish_owner_paste.ps1",
    "scripts/windows_write_ops_failure_paste.ps1",
    "scripts/windows_restart_next_dev.ps1",
    "scripts/windows_chat_500_forensics.ps1",
    "scripts/operator_validation_gate.py",
    "scripts/windows_g2_probe.py",
    "scripts/ahos_pg_probe.mjs",
    "AHOS_MAIN_FIRST.bat",
    "AHOS_FIX_G2_AND_GATE.bat",
    "AHOS_WINDOWS_OPS.bat",
    "AHOS_PUSH_EVIDENCE_NOW.bat",
    "AHOS_RUN_TIP.cmd",
    "AHOS_MAIN_CLEAR_G2.cmd",
    "OWNER_ONE_LINER.txt"
  )
  $ok = 0
  foreach ($f in $files) {
    try {
      Save-RawTipFile $f
      $ok++
    } catch {
      Write-Host ("  WARN download failed: " + $f + " :: " + $_.Exception.Message) -ForegroundColor DarkYellow
    }
  }
  Write-Host ("  downloaded_ok=" + $ok + "/" + $files.Count) -ForegroundColor Cyan
  return ($ok -ge 8)
}

$tipReady = $false
$ref = "origin/" + $Tip
if (Get-Command git -ErrorAction SilentlyContinue) {
  Write-Host "==> git fetch origin main + tip" -ForegroundColor Cyan
  & git fetch origin main 2>&1 | Out-Host
  & git fetch origin $Tip 2>&1 | Out-Host
  if ($LASTEXITCODE -eq 0) {
    Write-Host ("==> checkout tip unlock files from " + $ref) -ForegroundColor Cyan
    & git checkout $ref -- `
      AHOS_MAIN_FIRST.bat AHOS_FIX_G2_AND_GATE.bat AHOS_BOOTSTRAP_PRESOAK.bat `
      AHOS_PRE_SOAK_NOW.bat AHOS_WINDOWS_OPS.bat AHOS_PUSH_EVIDENCE_NOW.bat `
      AHOS_RUN_TIP.ps1 AHOS_RUN_TIP.cmd OWNER_ONE_LINER.txt RUN_ME_WINDOWS.txt WINDOWS_RUN_THIS_FIRST.txt `
      scripts/windows_checkout_unlock_tip.ps1 scripts/windows_fix_g2_empty_and_gate.ps1 `
      scripts/windows_bootstrap_presoak.ps1 scripts/windows_ensure_web_api_token.ps1 `
      scripts/windows_push_gate_evidence.ps1 scripts/windows_post_gate_paste_gh.ps1 `
      scripts/windows_publish_owner_paste.ps1 scripts/windows_run_operator_gate.ps1 `
      scripts/windows_recover_g2_warm.ps1 scripts/windows_ensure_database_url.ps1 `
      scripts/windows_wait_for_web_api.ps1 scripts/operator_validation_gate.py 2>&1 | Out-Host
    $helper = Join-Path $RepoRoot "scripts\windows_checkout_unlock_tip.ps1"
    if (Test-Path -LiteralPath $helper) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $helper -Ref $ref
    }
    $tipReady = Test-Path -LiteralPath (Join-Path $RepoRoot "scripts\windows_fix_g2_empty_and_gate.ps1")
  } else {
    Write-Host ("WARN: git fetch tip failed (exit " + $LASTEXITCODE + ")") -ForegroundColor Yellow
  }
} else {
  Write-Host "WARN: git not on PATH - will try raw HTTPS fallback" -ForegroundColor Yellow
}

if (-not $tipReady) {
  $tipReady = Install-TipViaRaw
}
if (-not $tipReady) {
  Write-Host "FAIL: could not install tip scripts via git or raw HTTPS" -ForegroundColor Red
  exit 2
}

function Invoke-BatCrlf([string]$BatName) {
  $path = Join-Path $RepoRoot $BatName
  if (-not (Test-Path -LiteralPath $path)) {
    Write-Host ("FAIL: missing " + $BatName) -ForegroundColor Red
    return 2
  }
  $raw = [System.IO.File]::ReadAllText($path)
  $fixed = $raw -replace "`r?`n", "`r`n"
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($path, $fixed, $utf8NoBom)
  Write-Host ("==> cmd /c " + $BatName) -ForegroundColor Cyan
  & cmd.exe /c "`"$path`""
  return $LASTEXITCODE
}

$rc = 0
switch ($Mode) {
  "main_first" {
    $rc = Invoke-BatCrlf "AHOS_MAIN_FIRST.bat"
  }
  "bootstrap" {
    $boot = Join-Path $RepoRoot "scripts\windows_bootstrap_presoak.ps1"
    if (Test-Path -LiteralPath $boot) {
      & powershell -NoProfile -ExecutionPolicy Bypass -File $boot -Tip $Tip
      $rc = $LASTEXITCODE
    } else {
      $rc = Invoke-BatCrlf "AHOS_BOOTSTRAP_PRESOAK.bat"
    }
  }
  default {
    $fix = Join-Path $RepoRoot "scripts\windows_fix_g2_empty_and_gate.ps1"
    if (-not (Test-Path -LiteralPath $fix)) {
      Write-Host "FAIL: windows_fix_g2_empty_and_gate.ps1 missing" -ForegroundColor Red
      exit 2
    }
    Write-Host "==> windows_fix_g2_empty_and_gate.ps1 (pure PS)" -ForegroundColor Cyan
    & powershell -NoProfile -ExecutionPolicy Bypass -File $fix -Tip $Tip -RepoRoot $RepoRoot
    $rc = $LASTEXITCODE
  }
}

Write-Host ""
$paste = Join-Path $RepoRoot "reports\OWNER_PASTE_WINDOWS_GATE.txt"
$status = Join-Path $RepoRoot "reports\PRE_SOAK_STATUS.txt"
if (Test-Path -LiteralPath $status) {
  Write-Host "----- PRE_SOAK_STATUS.txt -----" -ForegroundColor Yellow
  Get-Content -LiteralPath $status | ForEach-Object { Write-Host $_ }
}
if (Test-Path -LiteralPath $paste) {
  Write-Host ("OWNER_PASTE ready: " + $paste) -ForegroundColor Green
} else {
  Write-Host "OWNER_PASTE missing - check console / ops log" -ForegroundColor DarkYellow
}
Write-Host "Paste reports\OWNER_PASTE_WINDOWS_GATE.txt to PR #56 or #38" -ForegroundColor Cyan
Write-Host "PRE_SOAK only if pre_soak_entry_ok=true. Never invent READY." -ForegroundColor Yellow
Write-Host "STATE B: do NOT db:migrate / db:push" -ForegroundColor Yellow
exit $rc
