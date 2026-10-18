# PowerShell Script to Create AHOS Desktop Shortcut
param(
    [string]$TargetPath = ".\ahos_launcher.exe",
    [string]$ShortcutName = "AHOS Portable",
    [string]$Description = "AHOS Portable - Automated Hybrid Operating System",
    [switch]$Force = $false
)

$ErrorActionPreference = "Stop"

# Get the full path to the target executable
$TargetFullPath = (Get-Location).Path | Join-Path -ChildPath $TargetPath

if (-not (Test-Path $TargetFullPath)) {
    Write-Error "Target executable not found: $TargetFullPath"
    exit 1
}

# Get the user's desktop path
$DesktopPath = [Environment]::GetFolderPath("Desktop")

# Create shortcut path
$ShortcutPath = $DesktopPath | Join-Path -ChildPath "$ShortcutName.lnk"

Write-Host "Creating desktop shortcut..."
Write-Host "Target: $TargetFullPath"
Write-Host "Shortcut: $ShortcutPath"

# Create shortcut using Windows Script Host
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)

$shortcut.TargetPath = $TargetFullPath
$shortcut.WorkingDirectory = (Get-Location).Path
$shortcut.Description = $Description
$shortcut.IconLocation = (Get-Location).Path + "\ahos_icon.ico, 0"

# Additional properties
$shortcut.WindowStyle = 1  # Normal window
$shortcut.HotKey = ""

$shortcut.Save()

Write-Host "✓ Desktop shortcut created successfully: $ShortcutPath"

# Verify the shortcut was created
if (Test-Path $ShortcutPath) {
    Write-Host "✓ Shortcut verification successful"
} else {
    Write-Warning "⚠ Shortcut verification failed"
    exit 1
}

# Set hidden attribute to the shortcut
Set-ItemProperty -Path $ShortcutPath -Name Attributes -Value "Hidden"

Write-Host "✓ Shortcut configured for hidden execution"

# Register in Windows Registry for uninstall
$RegistryPath = "HKCU:\Software\AHOS Portable"
$RegistryName = "InstallPath"
$RegistryValue = (Get-Location).Path

# Create registry key if it doesn't exist
if (-not (Test-Path $RegistryPath)) {
    New-Item -Path $RegistryPath -Force | Out-Null
}

# Set registry values
New-ItemProperty -Path $RegistryPath -Name $RegistryName -Value $RegistryValue -PropertyType String -Force | Out-Null
New-ItemProperty -Path $RegistryPath -Name "InstallDate" -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss") -PropertyType String -Force | Out-Null

Write-Host "✓ Registration complete"