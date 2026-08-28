#Requires -Version 5.1
<#
.SYNOPSIS
  Make OWNER_PASTE hard to miss: Desktop copy + clipboard + Notepad.

Does not invent READY. Does not migrate.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$PastePath,
  [string]$DesktopName = "AHOS_PASTE_TO_CURSOR.txt"
)

$ErrorActionPreference = "Continue"

if (-not (Test-Path -LiteralPath $PastePath)) {
  Write-Host ("publish-paste skip: missing " + $PastePath) -ForegroundColor DarkYellow
  exit 0
}

$body = [System.IO.File]::ReadAllText($PastePath)

try {
  Set-Clipboard -Value $body
  Write-Host "Clipboard: OWNER_PASTE ready -- Ctrl+V into Cursor chat NOW." -ForegroundColor Green
} catch {
  Write-Host ("Clipboard skipped: " + $_.Exception.Message) -ForegroundColor DarkYellow
}

try {
  $desktop = [Environment]::GetFolderPath("Desktop")
  if (-not [string]::IsNullOrWhiteSpace($desktop) -and (Test-Path -LiteralPath $desktop)) {
    $dest = Join-Path $desktop $DesktopName
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($dest, $body, $utf8)
    Write-Host ("Desktop copy: " + $dest) -ForegroundColor Cyan
    Write-Host "Open that Desktop file and paste into Cursor if clipboard failed." -ForegroundColor Yellow
  }
} catch {
  Write-Host ("Desktop copy skipped: " + $_.Exception.Message) -ForegroundColor DarkYellow
}

try {
  Start-Process -FilePath "notepad.exe" -ArgumentList $PastePath | Out-Null
} catch {}

exit 0
