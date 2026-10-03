@echo off
REM AHOS console wrapper -- MANUAL TERMINAL USE ONLY.
REM
REM The owner's desktop shortcut and the dashboard control panel go through
REM ahos.ps1 with -WindowStyle Hidden, which leaves no console behind. This .bat
REM is the opposite contract: it always opens a visible console and waits, so a
REM human running it from a terminal can read the result. Nothing on the
REM one-click path may call it, and no child of the launcher may be spawned
REM through cmd.exe without CREATE_NO_WINDOW (see launcher/processkit.py).
REM Usage: ahos.bat [start|stop|status|restart|preflight]
setlocal
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0\.."

set ACTION=%1
if "%ACTION%"=="" set ACTION=start

if not exist "%CD%\.venv\Scripts\python.exe" (
  echo.
  echo محیط پایتون پیدا نشد. یک بار install_windows.ps1 را اجرا کنید.
  echo.
  pause > nul
  exit /b 3
)

"%CD%\.venv\Scripts\python.exe" -X utf8 -m launcher %ACTION%
set RC=%ERRORLEVEL%

echo.
echo --------------------------------------------------
echo برای بستن این پنجره Enter را بزنید.
pause > nul
exit /b %RC%
