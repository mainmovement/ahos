# AHOS Portable Installation Guide

## Step 1: Download and Extract
1. Download the `AHOS_Portable.zip` file
2. Extract it to a permanent location on your Windows machine (e.g., `C:\AHOS_Portable`)
3. Do NOT extract to temporary directories like `C:\Users\<YourName>\Downloads\` as the application won't work properly

## Step 2: Run Initial Setup
1. Double-click `ahos_launcher.exe`
2. The launcher will:
   - Check for required dependencies (Python, Node.js)
   - Set up environment variables
   - Create necessary directories
   - Check for secrets in Windows Credential Manager

## Step 3: Restore Secrets (First Time Only)
1. If this is your first time running AHOS on this machine, you'll be prompted to restore secrets
2. Open Windows Credential Manager (search for it in the Start Menu)
3. Under "Windows Credentials", add the following:
   - **AHOS/ai/gemini**: Your Gemini API key
   - **AHOS/data/finnhub**: Your Finnhub API key
   - **AHOS/data/twelvedata**: Your TwelveData API key
   - **AHOS/data/fred**: Your FRED API key
   - **AHOS/telegram**: Your Telegram bot token
   - **AHOS/webapi**: Your web API token (if applicable)
4. Restart the launcher after adding credentials

## Step 4: Run Health Check
1. Open PowerShell as Administrator
2. Navigate to the AHOS_Portable directory
3. Run: `.\HEALTH_CHECK.ps1`
4. Verify all checks pass

## Step 5: Launch AHOS
1. Double-click `ahos_launcher.exe` again
2. Wait for the dashboard to open in your default browser
3. The application will run on `http://localhost:3000`

## Troubleshooting
**Common Issues:**
- "Python not found": Make sure the `python` folder exists and contains Python
- "Port 3000 in use": Close other applications using port 3000
- "Secrets not found": Verify credentials in Windows Credential Manager
- "Database error": Delete the `data/` folder and restart (your data will be recreated)

## Support
If you encounter issues:
1. Check the `HEALTH_CHECK.ps1` output
2. Review the troubleshooting section
3. Contact support with the error message and your system information