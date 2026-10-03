@echo off
REM AHOS one-click console wrapper: keeps the window UTF-8 and readable.
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
