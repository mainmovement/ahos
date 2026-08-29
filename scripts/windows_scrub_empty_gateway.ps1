#Requires -Version 5.1
<#
.SYNOPSIS
  Fill empty AHOS_GATEWAY_URL= in .env (last Windows paste 220318 G2 BLOCKED).

Never overwrites a non-empty value. Never migrates. Does not invent READY.
#>
[CmdletBinding()]
param(
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
  } else {
    $RepoRoot = (Get-Location).Path
  }
}

$envPath = Join-Path $RepoRoot ".env"
$default = "http://127.0.0.1:3000/api/chat"

if (-not (Test-Path -LiteralPath $envPath)) {
  New-Item -ItemType File -Path $envPath | Out-Null
  Write-Host "Created empty .env" -ForegroundColor Yellow
}

$raw = Get-Content -LiteralPath $envPath -Raw -ErrorAction SilentlyContinue
if ($null -eq $raw) { $raw = "" }

if ($raw -match '(?m)^AHOS_GATEWAY_URL\s*=\s*$') {
  $raw = [regex]::Replace(
    $raw,
    '(?m)^AHOS_GATEWAY_URL\s*=\s*$',
    ("AHOS_GATEWAY_URL=" + $default),
    1
  )
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($envPath, $raw, $utf8)
  Write-Host ("Filled empty AHOS_GATEWAY_URL=" + $default) -ForegroundColor Yellow
  exit 0
}

if ($raw -notmatch '(?m)^AHOS_GATEWAY_URL\s*=') {
  $sep = ""
  if (($raw.Length -gt 0) -and -not $raw.EndsWith("`n")) { $sep = "`n" }
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($envPath, ($raw + $sep + "AHOS_GATEWAY_URL=" + $default + "`n"), $utf8)
  Write-Host ("Appended AHOS_GATEWAY_URL=" + $default) -ForegroundColor Yellow
  exit 0
}

Write-Host "AHOS_GATEWAY_URL already set (left unchanged)" -ForegroundColor Green
exit 0
