# AHOS Data Transfer Guide

## Overview
This guide explains how to transfer AHOS data between machines when using the portable bundle. Unlike an installed version, the portable bundle doesn't have a centralized data location by default, so you need to properly back up and restore your data.

## Data Directory Structure
```
AHOS_Portable/
├── data/
│   ├── config/          # Configuration files
│   ├── logs/            # Application logs
│   ├── databases/       # SQLite database files
│   │   ├── discovery.db
│   │   ├── paper_trading.db
│   │   ├── local.db
│   │   └── knowledge.db
│   └── user_data/       # User preferences and settings
```

## Before Moving Data

### Step 1: Create a Complete Backup
1. **Stop AHOS** if it's running
2. Navigate to your AHOS_Portable directory
3. Compress the entire `data` folder:
   ```powershell
   Compress-Archive -Path "data" -DestinationPath "AHOS_Data_Backup_$(Get-Date -Format 'yyyyMMdd').zip"
   ```

### Step 2: Verify Your Backup
1. Check the backup file integrity:
   ```powershell
   Test-Archive -Path "AHOS_Data_Backup_*.zip"
   ```
2. Ensure all databases are healthy:
   ```powershell
   cd AHOS_Portable
   .\HEALTH_CHECK.ps1
   ```

### Step 3: Export Critical Data
If you want to preserve specific data:

#### Export Configuration
```powershell
# Copy config files
Copy-Item -Path "data\config\*" -Destination "config_backup\"
```

#### Export Database Snapshots
```powershell
# Create database snapshots
foreach ($db in @("discovery.db", "paper_trading.db", "local.db", "knowledge.db")) {
    $source = Join-Path "data" "databases\$db"
    $dest = Join-Path "data_backup" "snapshots\$db"
    if (Test-Path $source) {
        Copy-Item -Path $source -Destination $dest
    }
}
```

#### Export User Preferences
```powershell
# Copy user settings
Copy-Item -Path "data\user_data\*" -Destination "user_data_backup\"
```

## Moving Data to a New Machine

### Method 1: Complete Data Transfer

#### 1. Prepare New Machine
1. Install AHOS Portable on the new machine
2. Run initial setup without importing data
3. Add all API keys to Windows Credential Manager
4. Run `HEALTH_CHECK.ps1` to verify baseline setup

#### 2. Transfer Data
1. Copy the `data` backup to the new machine
2. Place it in the AHOS_Portable directory, overwriting the empty `data` folder
   ```powershell
   # On the new machine:
   Copy-Item -Path "AHOS_Data_Backup_*.zip" -Destination "C:\AHOS_Portable\"
   Expand-Archive -Path "C:\AHOS_Portable\AHOS_Data_Backup_*.zip" -DestinationPath "C:\AHOS_Portable\data\" -Force
   ```

#### 3. Verify Data Integrity
```powershell
cd C:\AHOS_Portable
.\HEALTH_CHECK.ps1
```

#### 4. Test Functionality
1. Launch AHOS using `ahos_launcher.ps1`
2. Verify all features work:
   - Dashboard loads correctly
   - API calls succeed
   - Historical data is available
   - Paper trading status is preserved

### Method 2: Selective Data Transfer

If you only want certain data:

#### 1. Transfer Only Configuration
```powershell
# Copy only config files
Copy-Item -Path "config_backup\*" -Destination "C:\AHOS_Portable\data\config\" -Recurse -Force
```

#### 2. Transfer Databases
```powershell
# Copy only database files
Copy-Item -Path "data_backup\databases\*.db" -Destination "C:\AHOS_Portable\data\databases\" -Force
```

#### 3. Transfer User Settings
```powershell
# Copy only user preferences
Copy-Item -Path "user_data_backup\*" -Destination "C:\AHOS_Portable\data\user_data\" -Recurse -Force
```

## After Moving Data

### 1. Validate System Health
```powershell
cd C:\AHOS_Portable
.\HEALTH_CHECK.ps1
```

### 2. Check Database Integrity
```powershell
# Run SQLite database checks
sqlite3 data/databases/discovery.db "PRAGMA integrity_check;"
sqlite3 data/databases/paper_trading.db "PRAGMA integrity_check;"
```

### 3. Verify API Connections
1. Open the AHOS dashboard
2. Check that all API connections work:
   - Gemini AI
   - Finnhub
   - TwelveData
   - FRED
   - Telegram

### 4. Test Data Access
1. Check that historical data is accessible
2. Verify paper trading status is correct
3. Ensure user preferences are restored

## Troubleshooting Common Issues

### Issue: Database Corruption
**Symptoms:** Error messages when accessing data, crashes on startup
**Solution:**
```powershell
# Remove corrupted databases
Remove-Item -Path "data/databases/*.db" -Force

# Recreate databases
cd C:\AHOS_Portable
.\HEALTH_CHECK.ps1 --repair --confirm
```

### Issue: Configuration Mismatch
**Symptoms:** Settings not applied, unexpected behavior
**Solution:**
```powershell
# Reset configuration
Remove-Item -Path "data/config/*" -Recurse -Force
cd C:\AHOS_Portable
.\HEALTH_CHECK.ps1
```

### Issue: Missing Secrets
**Symptoms:** API calls fail, feature unavailable
**Solution:**
1. Open Windows Credential Manager
2. Add all required API keys (see INSTALL.md for list)
3. Restart AHOS

### Issue: Path Issues
**Symptoms:** Files not found, permission errors
**Solution:**
```powershell
# Fix permissions
icacls "C:\AHOS_Portable" /grant Everyone:(OI)(CI)F /T

# Verify paths
Get-ChildItem -Path "C:\AHOS_Portable\data" -Recurse
```

## Best Practices

1. **Regular Backups:** Create backups at least weekly
2. **Multiple Copies:** Keep backups on:
   - External drive
   - Cloud storage
   - Separate physical media
3. **Incremental Backups:** For large datasets, use incremental backups
4. **Test Restores:** Always test your backup process before needing it
5. **Document Changes:** Keep a log of data changes and when they were made

## Data Export Script

Create this script for easy data backup:

```powershell
# Backup-AHOSData.ps1
param(
    [string]$BackupPath,
    [switch]$FullBackup = $true
)

$InstallDir = "C:\AHOS_Portable"
$DataDir = Join-Path $InstallDir "data"

if (-not $BackupPath) {
    $BackupPath = Join-Path $env:USERPROFILE "AHOS_Backups"
}

# Ensure backup directory exists
New-Item -ItemType Directory -Path $BackupPath -Force | Out-Null

# Create timestamp
$Timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'

if ($FullBackup) {
    # Full backup
    $BackupFile = Join-Path $BackupPath "AHOS_Full_Backup_$Timestamp.zip"
    Compress-Archive -Path $DataDir -DestinationPath $BackupFile
    Write-Host "Full backup created: $BackupFile"
} else {
    # Incremental backup (config and user data only)
    $BackupFile = Join-Path $BackupPath "AHOS_Config_Backup_$Timestamp.zip"
    Compress-Archive -Path "$DataDir\config","$DataDir\user_data" -DestinationPath $BackupFile
    Write-Host "Config backup created: $BackupFile"
}

# Verify backup
if (Test-Archive -Path $BackupFile) {
    Write-Host "✓ Backup verified successfully"
} else {
    Write-Host "✗ Backup verification failed"
    exit 1
}
```

## Contact Support

If you encounter issues with data transfer:
1. Collect health check results
2. Note any error messages
3. Provide information about:
   - Source and destination machine specifications
   - Version of AHOS being used
   - Size of data being transferred