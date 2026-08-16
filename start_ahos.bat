@echo off
title AHOS Opportunity Intelligence System
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m architecture.runtime --daemon --interval-sec 60
) else (
    powershell -ExecutionPolicy Bypass -File ".\install_windows.ps1"
    ".venv\Scripts\python.exe" -m architecture.runtime --daemon --interval-sec 60
)
pause
