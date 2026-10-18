# M62 Portable Bundle for AHOS

## Overview
This portable bundle allows AHOS to run on any Windows machine without installation. It includes all necessary dependencies and a simple launcher.

## Bundle Contents
```
AHOS_Portable/
├── ahos_launcher.exe          # Main launcher application
├── ahos_icon.ico              # Application icon
├── ahos.bat                  # Command launcher
├── README.md                 # This file
├── INSTALL.md               # Installation instructions
├── HEALTH_CHECK.ps1         # Post-move health validation
├── DATA_MOVE_GUIDE.md       # Data transfer instructions
├── python/                  # Python runtime + packages
├── node/                    # Node.js runtime
├── app/                     # AHOS application code
└── data/                    # Empty directory for user data
```

## Quick Start
1. Copy the entire `AHOS_Portable` folder to your Windows machine
2. Double-click `ahos_launcher.exe` to run
3. Follow the prompts to restore secrets from Windows Credential Manager
4. Run `HEALTH_CHECK.ps1` to verify everything works

## Requirements
- Windows 10 or later
- Internet connection for first-time setup
- Approximately 500MB free disk space

## Security
- Secrets are stored in Windows Credential Manager, not in the bundle
- Bundle contains no API keys or sensitive information
- All communications use HTTPS