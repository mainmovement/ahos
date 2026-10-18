# AHOS Launcher
# Portable bundle launcher that checks dependencies, sets up environment, and launches AHOS

param(
    [switch]$CheckOnly,
    [switch]$Help
)

if ($Help) {
    Write-Host "AHOS Launcher - Portable Bundle"
    Write-Host ""
    Write-Host "Usage: .\ahos_launcher.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -CheckOnly    Check environment and report status without launching"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "Requirements:"
    Write-Host "  - Windows 10 or later"
    Write-Host "  - Python and Node.js in bundled runtimes"
    Write-Host "  - Secrets in Windows Credential Manager"
    exit 0
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Color constants
$ColorSuccess = [System.ConsoleColor]::Green
$ColorError = [System.ConsoleColor]::Red
$ColorWarning = [System.ConsoleColor]::Yellow
$ColorInfo = [System.ConsoleColor]::White

function Write-ColorOutput {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = $ColorInfo
    )
    Write-Host $Message -ForegroundColor $Color
}

function Test-Environment {
    Write-ColorOutput "`n=== AHOS Environment Check ===" $ColorInfo

    # Test Python
    $PythonPath = Join-Path $ScriptDir "python\python.exe"
    if (Test-Path $PythonPath) {
        Write-ColorOutput "✓ Python found: $PythonPath" $ColorSuccess
    } else {
        Write-ColorOutput "✗ Python not found at: $PythonPath" $ColorError
        return $false
    }

    # Test Node.js
    $NodePath = Join-Path $ScriptDir "node\node.exe"
    if (Test-Path $NodePath) {
        Write-ColorOutput "✓ Node.js found: $NodePath" $ColorSuccess
    } else {
        Write-ColorOutput "✗ Node.js not found at: $NodePath" $ColorError
        return $false
    }

    # Check data directory
    $DataDir = Join-Path $ScriptDir "data"
    if (Test-Path $DataDir) {
        Write-ColorOutput "✓ Data directory exists: $DataDir" $ColorSuccess
    } else {
        Write-ColorOutput "✗ Data directory not found: $DataDir" $ColorError
        return $false
    }

    return $true
}

function Test-Secrets {
    Write-ColorOutput "`n=== Secret Check ===" $ColorInfo

    $Secrets = @(
        "AHOS/ai/gemini",
        "AHOS/data/finnhub",
        "AHOS/data/twelvedata",
        "AHOS/data/fred",
        "AHOS/telegram",
        "AHOS/webapi"
    )

    $MissingSecrets = @()

    foreach ($Secret in $Secrets) {
        if (Get-Item "Credential::$Secret" -ErrorAction SilentlyContinue) {
            Write-ColorOutput "✓ $Secret found" $ColorSuccess
        } else {
            Write-ColorOutput "✗ $Secret not found" $ColorError
            $MissingSecrets += $Secret
        }
    }

    if ($MissingSecrets.Count -gt 0) {
        Write-ColorOutput "`n⚠ Missing secrets. Please add them to Windows Credential Manager." $ColorWarning
        return $false
    }

    return $true
}

function Test-Ports {
    Write-ColorOutput "`n=== Port Check ===" $ColorInfo

    # Check port 3000 (Next.js dev server)
    $PortInUse = Test-NetConnection -ComputerName localhost -Port 3000 -InformationLevel Quiet -ErrorAction SilentlyContinue

    if ($PortInUse) {
        Write-ColorOutput "✗ Port 3000 is already in use" $ColorError
        Write-ColorOutput "  Close applications using port 3000 or specify a different port." $ColorWarning
        return $false
    } else {
        Write-ColorOutput "✓ Port 3000 is available" $ColorSuccess
    }

    return $true
}

function Initialize-Environment {
    Write-ColorOutput "`n=== Initializing Environment ===" $ColorInfo

    # Create data directory if it doesn't exist
    $DataDir = Join-Path $ScriptDir "data"
    if (-not (Test-Path $DataDir)) {
        New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
        Write-ColorOutput "✓ Created data directory" $ColorSuccess
    }

    # Create logs directory
    $LogsDir = Join-Path $DataDir "logs"
    if (-not (Test-Path $LogsDir)) {
        New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
        Write-ColorOutput "✓ Created logs directory" $ColorSuccess
    }

    # Set environment variables
    $envPath = Join-Path $ScriptDir "env"
    if (-not (Test-Path $envPath)) {
        New-Item -ItemType Directory -Path $envPath -Force | Out-Null
        Write-ColorOutput "✓ Created env directory" $ColorSuccess
    }

    # Set Python path
    $env:PYTHONPATH = "$envPath;$env:PYTHONPATH"

    # Set Node path
    $env:PATH = "$envPath;$env:PATH"

    Write-ColorOutput "✓ Environment initialized" $ColorSuccess
}

function Start-AHOS {
    Write-ColorOutput "`n=== Starting AHOS ===" $ColorInfo

    $AppDir = Join-Path $ScriptDir "app"
    $LogsDir = Join-Path $ScriptDir "data\logs"

    # Start backend (Python) in background
    Write-ColorOutput "Starting backend..." $ColorInfo
    $PythonPath = Join-Path $ScriptDir "python\python.exe"
    $BackendScript = Join-Path $AppDir "backend\main.py"

    Start-Process -FilePath $PythonPath -ArgumentList $BackendScript -NoNewWindow -RedirectStandardOutput "$LogsDir\backend.log" -RedirectStandardError "$LogsDir\backend_error.log"

    # Wait for backend to start
    Write-ColorOutput "Waiting for backend to initialize..." $ColorWarning
    Start-Sleep -Seconds 5

    # Start frontend (Node.js) in background
    Write-ColorOutput "Starting frontend..." $ColorInfo
    $NodePath = Join-Path $ScriptDir "node\node.exe"
    $FrontendScript = Join-Path $AppDir "frontend\package.json"

    Start-Process -FilePath $NodePath -ArgumentList "run", "dev", "--silent" -WorkingDirectory $AppDir -NoNewWindow -RedirectStandardOutput "$LogsDir\frontend.log" -RedirectStandardError "$LogsDir\frontend_error.log"

    # Wait for frontend to start
    Write-ColorOutput "Waiting for frontend to initialize..." $ColorWarning
    Start-Sleep -Seconds 5

    # Open browser
    Write-ColorOutput "Opening AHOS dashboard..." $ColorInfo
    Start-Process "http://localhost:3000"

    Write-ColorOutput "`n✓ AHOS is now running!" $ColorSuccess
    Write-ColorOutput "Dashboard: http://localhost:3000" $ColorInfo
    Write-ColorOutput "Logs: $LogsDir" $ColorInfo
}

# Main execution
try {
    # Check environment
    if (-not (Test-Environment)) {
        Write-ColorOutput "`n✗ Environment check failed" $ColorError
        if (-not $CheckOnly) {
            Write-ColorOutput "Please fix the issues above and run again." $ColorWarning
            exit 1
        }
    }

    # Check secrets
    if (-not (Test-Secrets)) {
        Write-ColorOutput "`n⚠ Secrets missing" $ColorWarning
        Write-ColorOutput "Please add secrets to Windows Credential Manager and run again." $ColorWarning
        if (-not $CheckOnly) {
            exit 1
        }
    }

    # Check ports
    if (-not (Test-Ports)) {
        Write-ColorOutput "`n⚠ Port check failed" $ColorWarning
        if (-not $CheckOnly) {
            Write-ColorOutput "Please close applications using port 3000 and run again." $ColorWarning
            exit 1
        }
    }

    # Check only mode
    if ($CheckOnly) {
        Write-ColorOutput "`n✓ All checks passed" $ColorSuccess
        exit 0
    }

    # Initialize environment
    Initialize-Environment

    # Start AHOS
    Start-AHOS

} catch {
    Write-ColorOutput "`n✗ Error: $_" $ColorError
    Write-ColorOutput "Stack trace: $_.ScriptStackTrace" $ColorError
    exit 1
}
