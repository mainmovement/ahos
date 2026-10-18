@echo off
REM AHOS Launcher Batch File
REM Simple launcher for AHOS Portable Bundle

set SCRIPT_DIR=%~dp0
set PYTHON_PATH=%SCRIPT_DIR%python\python.exe
set NODE_PATH=%SCRIPT_DIR%node\node.exe
set APP_DIR=%SCRIPT_DIR%app

echo Starting AHOS Portable...
echo.
echo Checking prerequisites...

REM Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo ERROR: Python runtime not found at %PYTHON_PATH%
    pause
    exit /b 1
)

REM Check if Node.js exists
if not exist "%NODE_PATH%" (
    echo ERROR: Node.js runtime not found at %NODE_PATH%
    pause
    exit /b 1
)

REM Check if app directory exists
if not exist "%APP_DIR%" (
    echo ERROR: Application directory not found at %APP_DIR%
    pause
    exit /b 1
)

echo Prerequisites check passed.
echo.
echo Launching AHOS...

REM Start backend in background
echo Starting backend...
start /B "AHOS Backend" "%PYTHON_PATH%" "%APP_DIR%\backend\main.py"

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Start frontend in background
echo Starting frontend...
start /B "AHOS Frontend" "%NODE_PATH%" run dev --silent --no-open

REM Wait for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo AHOS is starting...
echo Dashboard should open in your default browser soon.
echo.
echo If it doesn't open automatically, visit: http://localhost:3000
echo.
echo For health check, run: HEALTH_CHECK.ps1
echo For full launcher with more options, run: ahos_launcher.ps1
echo.

pause