# AHOS Portable Bundle

## What is this?

This is a self-contained portable version of AHOS (Automated Hybrid Operating System) that runs on Windows without installation. It includes all necessary dependencies, runtimes, and application code.

## Quick Start

1. **Copy** the entire `AHOS_Portable` folder to your Windows machine
2. **Extract** the zip file (if downloaded)
3. **Double-click** `ahos_launcher.exe` to run
4. **Restore** your API keys from Windows Credential Manager
5. **Run** `HEALTH_CHECK.ps1` to verify everything works

## Bundle Contents

```
AHOS_Portable/
├── ahos_launcher.exe          # Main launcher application
├── ahos_launcher.ps1          # PowerShell launcher script
├── HEALTH_CHECK.ps1           # System health validation script
├── INSTALL.ps1                # Installation script (admin only)
├── UNINSTALL.ps1              # Uninstallation script
├── CREATE_DESKTOP_SHORTCUT.ps1 # Desktop shortcut creator
├── M62_PORTABLE_README.md     # This file
├── M62_INSTALL_GUIDE.md       # Detailed installation guide
├── DATA_MOVE_GUIDE.md         # Data transfer instructions
├── ahos.inf                   # Windows installer file
├── python/                    # Python 3.11 runtime + packages
├── node/                      # Node.js runtime
├── app/                       # AHOS application code
│   ├── backend/              # Flask backend
│   ├── frontend/             # Next.js frontend
│   └── node_modules/         # Node.js dependencies
└── data/                      # Empty directory for your data
    ├── config/               # Configuration files
    ├── logs/                 # Application logs
    ├── databases/            # SQLite databases
    └── user_data/            # User preferences
```

## Requirements

- **OS:** Windows 10 or later
- **RAM:** Minimum 4GB (8GB recommended)
- **Disk Space:** ~500MB free space
- **Network:** Internet connection for initial setup and API calls
- **Permissions:** Administrator privileges for installation (optional)

## Features

### ✅ Self-Contained
- No external dependencies or installation required
- Runs from any location on your system
- Portable across different machines

### ✅ Health Checks
- Automatic dependency validation
- Port availability checks
- Secret verification
- Database integrity checks

### ✅ Data Isolation
- Separate data directory
- Configuration management
- User preferences persistence
- Easy data backup and restore

### ✅ Service Management
- Automatic service startup
- Background process handling
- Log file generation
- Error monitoring and reporting

## Usage

### Running AHOS

```powershell
# Start AHOS
.\ahos_launcher.exe

# Or use PowerShell
.\ahos_launcher.ps1

# Or use the command launcher
.\ahos.bat
```

### Running Health Check

```powershell
# Run health check
.\HEALTH_CHECK.ps1

# Generate report
.\HEALTH_CHECK.ps1 -ReportPath "data\health_report.json"

# Repair auto-repairable issues
.\HEALTH_CHECK.ps1 --repair --confirm
```

### Installing to System

```powershell
# Run installer as administrator
.\INSTALL.ps1 -TargetDir "C:\Program Files\AHOS_Portable"
```

### Uninstalling

```powershell
# Run uninstaller as administrator
.\UNINSTALL.ps1 -InstallDir "C:\Program Files\AHOS_Portable" -Confirm
```

## API Keys Required

Before running AHOS, add these to Windows Credential Manager:

- **AHOS/ai/gemini** - Your Gemini API key
- **AHOS/data/finnhub** - Your Finnhub API key
- **AHOS/data/twelvedata** - Your TwelveData API key
- **AHOS/data/fred** - Your FRED API key
- **AHOS/telegram** - Your Telegram bot token
- **AHOS/webapi** - Your web API token (if applicable)

See `M62_INSTALL_GUIDE.md` for detailed instructions.

## Troubleshooting

### Common Issues

**"Python not found"**
- Make sure the `python` folder exists and contains Python executable
- Run `HEALTH_CHECK.ps1` to diagnose the issue

**"Port 3000 is already in use"**
- Close other applications using port 3000
- Modify launcher script to use a different port

**"Secrets not found"**
- Verify credentials in Windows Credential Manager
- Restart the launcher after adding credentials

**"Database error"**
- Delete the `data/` folder and restart (your data will be recreated)
- Run `HEALTH_CHECK.ps1 --repair --confirm` to fix database issues

### Getting Help

1. Check the `HEALTH_CHECK.ps1` output for detailed diagnostics
2. Review the troubleshooting section in `M62_INSTALL_GUIDE.md`
3. Check logs in the `data/logs/` directory
4. Contact support with your system information and error messages

## Security

### Secret Management
- Secrets are stored in **Windows Credential Manager**, never in the bundle
- The bundle contains **no API keys or sensitive information**
- All communications use **HTTPS** for secure connections

### File Permissions
- Application files are protected by Windows
- Data directory is user-writable
- Logs are stored in the data directory

### Best Practices
- Do not share the bundle with untrusted users
- Keep backups of your data directory
- Regularly update secrets in Credential Manager
- Monitor logs for suspicious activity

## Data Persistence

### Default Locations
- **Configuration:** `data/config/`
- **Logs:** `data/logs/`
- **Databases:** `data/databases/`
- **User Data:** `data/user_data/`

### Backup and Restore
See `DATA_MOVE_GUIDE.md` for detailed instructions on:
- Creating backups
- Restoring data
- Selective data transfer
- Troubleshooting common issues

## Version Information

- **Bundle Version:** 1.0
- **AHOS Version:** (Current version)
- **Python Version:** 3.11.x
- **Node.js Version:** (Current version)
- **Last Updated:** $(Get-Date -Format 'yyyy-MM-dd')

## Contributing

When modifying the portable bundle:
1. Test all scripts in the portable environment
2. Verify health checks still pass
3. Ensure compatibility with different Windows versions
4. Update documentation as needed

## License

See the main AHOS project license for usage terms.

## Support

For issues, questions, or support:
1. Check this README and documentation files
2. Run `HEALTH_CHECK.ps1` for diagnostics
3. Review logs in `data/logs/`
4. Open an issue on the AHOS project repository

---

**⚠️ Important:** This portable bundle is intended for use on systems where you have full control. Never run AHOS on untrusted or shared systems.