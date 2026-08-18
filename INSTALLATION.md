# AHOS Installation & Setup Guide

AHOS supports standalone Python execution on Windows 11, Linux, Mac, and containerized Docker Desktop environments.

---

## 1. Prerequisites
- **Python:** 3.11, 3.12, or 3.13 (64-bit)
- **Git:** Installed and available in PATH
- **Docker Desktop (Optional):** If running containerized services (n8n, PostgreSQL)

---

## 2. Windows 11 One-Click Setup
1. Clone or download the repository to your Windows machine:
   ```powershell
   git clone https://github.com/your-org/ahos.git
   cd ahos
   ```
2. Run the automated installer:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\install_windows.ps1
   ```
3. Start the continuous intelligence daemon:
   ```powershell
   .\start_ahos.ps1
   # Or double-click start_ahos.bat
   ```

---

## 3. Linux / macOS Setup
1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Initialize and verify runtime:
   ```bash
   python3 config/paths.py
   python3 -m architecture.runtime --single-cycle
   ```
3. Start background daemon:
   ```bash
   python3 -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
   ```

   `--observation-cycle` is required for real operation. Without it the daemon
   runs the scoring pipeline but never runs the E-01 observation poller or the
   outcome labeler, so predictions accumulate against zero outcome labels and
   calibration stays permanently empty.

---

## 4. Docker Compose Setup (Production / VPS)
```bash
cp deployment/.env.example deployment/.env
# Edit deployment/.env with your configuration
docker compose -f deployment/docker-compose.production.yml up -d --build
```
