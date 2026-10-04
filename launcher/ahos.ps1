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

.PARAMETER Skip
  Components to leave out of a start/restart (repeatable). The dashboard control
  panel forwards the previous run's explicit exclusions so that Restart restores
  the stack that was actually running instead of silently widening it.
#>
param(
  [Parameter(Position = 0)]
  [ValidateSet('start', 'stop', 'status', 'restart', 'preflight')]
  [string]$Action = 'start',

  [string[]]$Skip = @(),

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
foreach ($component in $Skip) {
  if ([string]::IsNullOrWhiteSpace($component)) { continue }
  $PyArgs += @('--skip', $component)
}

if ($Console) {
  & $Python @PyArgs
} else {
  # Hidden path: nobody is watching, so keep the progress lines as a log the
  # owner can read later instead of dropping them. UTF-8 so Persian survives.
  #
  # Two PowerShell 5.1 traps live here, and both silently cost us the log:
  #   1. Tee-Object has no -Encoding on 5.1 (that is a PowerShell 7 parameter),
  #      so the whole pipeline threw "a parameter cannot be found" before python
  #      ever ran, and the catch below re-ran python with no log at all.
  #   2. Under $ErrorActionPreference='Stop' a native command's stderr line is
  #      a terminating error, so the first warning from python aborted the pipe
  #      and dropped everything after it.
  # Out-File -Encoding utf8 plus a local 'Continue' preference fixes both, and
  # $LASTEXITCODE still comes from python (verified: exit 7 reaches exit $rc).
  $LogDir = Join-Path $Root 'logs\launcher'
  try {
    if (-not (Test-Path -LiteralPath $LogDir)) {
      New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    $LogPath = Join-Path $LogDir 'launcher.log'
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
      & $Python @PyArgs 2>&1 |
        Out-File -FilePath $LogPath -Encoding utf8 -Append
    } finally {
      $ErrorActionPreference = $prevEAP
    }
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
