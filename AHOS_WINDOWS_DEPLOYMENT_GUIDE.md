# AHOS Windows 11 Laptop Deployment & User Guide

This guide provides step-by-step instructions for installing and running AHOS on a Windows 11 laptop.

---

## 1. System Requirements
- **Operating System:** Windows 11 (64-bit) / Windows 10 (Build 19041+)
- **Python:** Python 3.11, 3.12, or 3.13 (Ensure "Add python.exe to PATH" was checked during install)
- **RAM:** Minimum 4 GB RAM (8 GB recommended)
- **Storage:** 2 GB free SSD space
- **Optional:** Docker Desktop for Windows (if running containerized PostgreSQL/n8n services)

---

## 2. One-Click Installation
1. Open **PowerShell** as an administrator or standard user.
2. Navigate to your AHOS project directory:
   ```powershell
   cd C:\path\to\ahos
   ```
3. Allow script execution for the current session:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
4. Run the installer:
   ```powershell
   .\install_windows.ps1
   ```
   *The script will create a `.venv` virtual environment, install dependencies, initialize directories, configure Windows paths, and run an initial health check.*

---

## 3. Starting the AHOS Daemon
You can start AHOS in any of the following ways:
- **Method A (PowerShell):**
  ```powershell
  .\start_ahos.ps1
  ```
- **Method B (File Explorer):**
  Double-click `start_ahos.bat` in File Explorer.

The continuous intelligence daemon will launch and begin polling market opportunities every 60 seconds. To stop gracefully, press `Ctrl + C`.

---

## 4. Configuring Telegram Interface (Optional)
1. Open `deployment\.env` in a text editor (e.g. Notepad).
2. Set your Telegram Bot token:
   ```env
   TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
   TELEGRAM_ALLOWED_CHATS=YOUR_CHAT_ID_HERE
   ```
3. Restart the daemon via `.\start_ahos.ps1`.

---

## 5. Running Health Checks & Diagnostics
To check system health at any time:
```powershell
.\.venv\Scripts\python.exe engine/health_manager.py
```
Outputs a full diagnostic report to `reports/health_report.json`.
