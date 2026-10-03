<#
.SYNOPSIS
  AHOS one-click console (PowerShell 5.1 compatible).

.DESCRIPTION
  Sets the console to UTF-8, resolves the repository root from this script's
  location, and delegates to the Python orchestrator (launcher package).
  The window stays open with a Persian prompt so the owner can read the result.

.PARAMETER Action
  start | stop | status | restart | preflight (default: start)
#>
param(
  [Parameter(Position = 0)]
  [ValidateSet('start', 'stop', 'status', 'restart', 'preflight')]
  [string]$Action = 'start',

  [switch]$Json
)

$ErrorActionPreference = 'Stop'
try {
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  $OutputEncoding = [System.Text.UTF8Encoding]::new($false)
} catch {
  try { chcp 65001 > $null } catch { }
}

$Root = Resolve-Path (Join-Path $PSScriptRoot '..')
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
  Write-Host ''
  Write-Host 'محیط پایتون پیدا نشد. یک بار install_windows.ps1 را اجرا کنید.'
  Write-Host ''
  Read-Host 'برای بستن این پنجره Enter را بزنید' | Out-Null
  exit 3
}

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $Root

$args = @('-X', 'utf8', '-m', 'launcher', $Action)
if ($Json) { $args += '--json' }

& $Python @args
$rc = $LASTEXITCODE

Write-Host ''
Write-Host '--------------------------------------------------'
Read-Host 'برای بستن این پنجره Enter را بزنید' | Out-Null
exit $rc
