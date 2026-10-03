<#
.SYNOPSIS
  AHOS one-click console (PowerShell 5.1 compatible).

.DESCRIPTION
  Sets the console to UTF-8, resolves the repository root from this script's
  location, and delegates to the Python orchestrator (launcher package).

  The desktop shortcut and the dashboard control panel launch this script with
  -WindowStyle Hidden. A hidden window has no console to read from, so the
  default (hidden) path NEVER blocks on Read-Host -- it would leave a
  powershell.exe pinned forever waiting for a key nobody can press, and the
  dashboard's next stop/restart would find the module lock still held. Pass
  -Console to get the interactive behaviour back for manual terminal use.

.PARAMETER Action
  start | stop | status | restart | preflight (default: start)

.PARAMETER Console
  Keep an interactive console open after the run (terminal use only).
#>
param(
  [Parameter(Position = 0)]
  [ValidateSet('start', 'stop', 'status', 'restart', 'preflight')]
  [string]$Action = 'start',

  [switch]$Json,

  [switch]$Console
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
  if ($Console) { Read-Host 'برای بستن این پنجره Enter را بزنید' | Out-Null }
  exit 3
}

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $Root

# $args is an automatic variable; shadowing it breaks splatting of real args.
$PyArgs = @('-X', 'utf8', '-m', 'launcher', $Action)
if ($Json) { $PyArgs += '--json' }

if ($Console) {
  & $Python @PyArgs
} else {
  # Hidden path: nobody is watching, so keep the progress lines as a log the
  # owner can read later instead of dropping them. UTF-8 so Persian survives.
  $LogDir = Join-Path $Root 'logs\launcher'
  try {
    if (-not (Test-Path -LiteralPath $LogDir)) {
      New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    $LogPath = Join-Path $LogDir 'launcher.log'
    & $Python @PyArgs 2>&1 |
      Tee-Object -FilePath $LogPath -Encoding utf8 -Append |
      Out-Null
  } catch {
    # A log we cannot write must never break the launcher itself.
    & $Python @PyArgs
  }
}
$rc = $LASTEXITCODE

if ($Console) {
  Write-Host ''
  Write-Host '--------------------------------------------------'
  Read-Host 'برای بستن این پنجره Enter را بزنید' | Out-Null
}
exit $rc
