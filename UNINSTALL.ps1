# AHOS Portable Uninstaller
# This script removes AHOS from the system

param(
    [string]$InstallDir,
    [switch]$Confirm = $false,
    [switch]$Silent = $false,
    [switch]$Help = $false
)

# Color functions for output
function Write-HostColor {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    if (-not $Silent) {
        Write-Host $Message -ForegroundColor $Color
    }
}

# Function to confirm uninstallation
function Confirm-Uninstall {
    if ($Confirm) {
        return $true
    }

    Write-HostColor "This will completely uninstall AHOS Portable from your system." "Yellow"
    Write-HostColor "All data, configuration, and shortcuts will be removed." "Yellow"
    Write-HostColor ""
    Write-HostColor "Are you sure you want to continue?" "Yellow"
    Write-HostColor "Press Y to uninstall, any other key to cancel."

    $response = Read-Host
    return ($response -eq "Y" -or $response -eq "y")
}

# Function to remove desktop shortcut
function Remove-Shortcuts {
    Write-HostColor "`n=== Removing Shortcuts ===" "Green"

    # Remove desktop shortcut
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $desktopShortcut = Join-Path $desktopPath "AHOS Portable.lnk"
    if (Test-Path $desktopShortcut) {
        Remove-Item $desktopShortcut -Force
        Write-HostColor "✓ Removed desktop shortcut" "Green"
    } else {
        Write-HostColor "~ Desktop shortcut not found" "Yellow"
    }

    # Remove Start Menu shortcut
    $startMenuPath = [Environment]::GetFolderPath("Programs") + "\AHOS Portable.lnk"
    if (Test-Path $startMenuPath) {
        Remove-Item $startMenuPath -Force
        Write-HostColor "✓ Removed Start Menu shortcut" "Green"
    } else {
        Write-HostColor "~ Start Menu shortcut not found" "Yellow"
    }
}

# Function to remove environment configuration
function Remove-Environment {
    Write-HostColor "`n=== Removing Environment Configuration ===" "Green"

    # Remove environment file
    $envPath = [Environment]::GetFolderPath("UserProfile") + "\ahos-env.ps1"
    if (Test-Path $envPath) {
        Remove-Item $envPath -Force
        Write-HostColor "✓ Removed environment configuration" "Green"
    } else {
        Write-HostColor "~ Environment configuration not found" "Yellow"
    }

    # Remove from PATH (this requires user intervention)
    Write-HostColor "⚠ AHOS may still be in your PATH environment variable" "Yellow"
    Write-HostColor "  You may need to manually edit your PATH settings to remove AHOS paths." "Yellow"
}

# Function to remove AHOS installation
function Remove-Installation {
    param(
        [string]$InstallPath
    )

    Write-HostColor "`n=== Removing AHOS Installation ===" "Green"

    if (Test-Path $InstallPath) {
        # Check if AHOS is currently running
        $ahosProcesses = Get-Process -Name "*ahos*" -ErrorAction SilentlyContinue
        if ($ahosProcesses) {
            Write-HostColor "⚠ AHOS processes found. Attempting to terminate..." "Yellow"
            try {
                Stop-Process -Name "*ahos*" -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
            } catch {
                Write-HostColor "⚠ Could not terminate AHOS processes. Please close them manually." "Yellow"
            }
        }

        # Remove installation directory
        Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-HostColor "✓ Removed AHOS installation directory" "Green"
    } else {
        Write-HostColor "~ Installation directory not found: $InstallPath" "Yellow"
    }

    # Remove registry entries
    $registryPaths = @(
        "HKCU:\Software\AHOS Portable",
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\AHOS_Portable"
    )

    foreach ($path in $registryPaths) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
            Write-HostColor "✓ Removed registry entry: $path" "Green"
        }
    }
}

# Function to remove data (optional)
function Remove-Data {
    param(
        [string]$DataPath
    )

    Write-HostColor "`n=== Removing Data ===" "Green"
    Write-HostColor "⚠ This will permanently delete all AHOS data including:" "Yellow"
    Write-HostColor "  - Database files" "Yellow"
    Write-HostColor "  - Configuration files" "Yellow"
    Write-HostColor "  - Logs" "Yellow"
    Write-HostColor "  - User preferences" "Yellow"
    Write-HostColor ""
    Write-HostColor "This action cannot be undone!" "Red"
    Write-HostColor ""
    Write-HostColor "Remove all data? Press Y to continue, any other key to skip." "Yellow"

    $response = Read-Host
    if ($response -eq "Y" -or $response -eq "y") {
        if (Test-Path $DataPath) {
            Remove-Item -Path $DataPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-HostColor "✓ Removed all data" "Green"
        } else {
            Write-HostColor "~ Data directory not found" "Yellow"
        }
    } else {
        Write-HostColor "~ Data preserved" "Yellow"
    }
}

# Function to show help
function Show-Help {
    Write-HostColor "AHOS Portable Uninstaller" "Green"
    Write-HostColor ""
    Write-HostColor "Usage: .\UNINSTALL.ps1 [OPTIONS]" "White"
    Write-HostColor ""
    Write-HostColor "Options:" "White"
    Write-HostColor "  -InstallDir <path>     Path to AHOS installation (default: C:\Program Files\AHOS_Portable)" "Cyan"
    Write-HostColor "  -Confirm              Skip confirmation prompts" "Cyan"
    Write-HostColor "  -Silent              Run without any output" "Cyan"
    Write-HostColor "  -Help               Show this help message" "Cyan"
    Write-HostColor ""
    Write-HostColor "Note: This will remove AHOS Portable from your system." "Yellow"
    Write-HostColor "Your data will be preserved unless you choose to delete it." "Yellow"
    exit 0
}

# Show help if requested
if ($Help) {
    Show-Help
}

# Get installation directory
if (-not $InstallDir) {
    $InstallDir = "C:\Program Files\AHOS_Portable"
}

# Confirm uninstallation
if (-not (Confirm-Uninstall)) {
    Write-HostColor "Uninstallation cancelled." "Green"
    exit 0
}

# Perform uninstallation
Write-HostColor "Starting AHOS Portable Uninstallation..." "Green"
Write-HostColor "Installation path: $InstallDir" "White"

try {
    Remove-Shortcuts
    Remove-Environment
    Remove-Installation -InstallPath $InstallDir
    Remove-Data -DataPath "C:\AHOS_Portable\data"

    Write-HostColor ""
    Write-HostColor "==============================" "Green"
    Write-HostColor "Uninstallation Complete!" "Green"
    Write-HostColor "==============================" "Green"
    Write-HostColor ""
    Write-HostColor "AHOS Portable has been successfully removed from your system." "White"
    Write-HostColor ""
    Write-HostColor "Note: You may need to restart your computer to complete all cleanup." "Yellow"

    exit 0
}
catch {
    Write-HostColor ""
    Write-HostColor "==============================" "Red"
    Write-HostColor "Uninstallation Failed!" "Red"
    Write-HostColor "Error: $_" "Red"
    Write-HostColor "==============================" "Red"
    exit 1
}