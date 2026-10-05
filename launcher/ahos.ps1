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

# The hidden path tees python's own output into the log the owner reads later;
# the console path needs no tee because the owner is watching that window.
$LogDir = Join-Path $Root 'logs\launcher'
if (-not $Console) {
  try {
    if (-not (Test-Path -LiteralPath $LogDir)) {
      New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    }
    $env:AHOS_LAUNCHER_LOG = Join-Path $LogDir 'launcher.log'
  } catch {
    # A log we cannot name must never break the launcher itself.
    Remove-Item Env:\AHOS_LAUNCHER_LOG -ErrorAction SilentlyContinue
  }
} else {
  Remove-Item Env:\AHOS_LAUNCHER_LOG -ErrorAction SilentlyContinue
}

# $args is an automatic variable; shadowing it breaks splatting of real args.
$PyArgs = @('-X', 'utf8', '-m', 'launcher', $Action)
if ($Json) { $PyArgs += '--json' }
foreach ($component in $Skip) {
  if ([string]::IsNullOrWhiteSpace($component)) { continue }
  # $Skip may carry a comma-joined list from the dashboard route: Start-Process
  # re-parses -ArgumentList into a single command line and PowerShell's binder
  # rejects a repeated -Skip, so the exclusions arrive as one element here and
  # launcher/__main__ splits them again.
  $PyArgs += @('--skip', $component)
}

if ($Console) {
  & $Python @PyArgs
} else {
  # Hidden path: nobody is watching, so python tees its progress lines to
  # $env:AHOS_LAUNCHER_LOG (set above) instead of dropping them.
  #
  # Do NOT redirect python through a PowerShell pipe here (`... | Out-File`):
  # a pipe does not end when python ends, it ends when the write end of the
  # pipe closes, and python's detached children inherit that handle. A restart
  # stops the very gateway that spawned this shell, python then exits, and the
  # shell stays pinned on the pipe reader forever -- a hidden powershell.exe
  # holding the module lock the dashboard's next stop/restart reports as
  # ALREADY_RUNNING. Confirmed on this host: the wedged shell's only live child
  # was conhost.exe, python was long gone. With python writing the log itself
  # the shell waits on nothing but python, and $LASTEXITCODE still reaches
  # exit $rc.
  & $Python @PyArgs
}
$rc = $LASTEXITCODE

if ($Console) {
  Write-Host ''
  Write-Host '--------------------------------------------------'
  Read-Host 'برای بستن این پنجره Enter را بزنید' | Out-Null
}
exit $rc
