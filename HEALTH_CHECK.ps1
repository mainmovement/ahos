# AHOS Health Check Script
# Validates the portable bundle environment and reports status

param(
    [switch]$Repair,
    [switch]$Confirm,
    [string]$ReportPath,
    [switch]$Quiet
)

# Color constants
$ColorSuccess = [System.ConsoleColor]::Green
$ColorError = [System.ConsoleColor]::Red
$ColorWarning = [System.ConsoleColor]::Yellow
$ColorInfo = [System.ConsoleColor]::White
$ColorDebug = [System.ConsoleColor]::Cyan

function Write-ColorOutput {
    param(
        [string]$Message,
        [System.ConsoleColor]$Color = $ColorInfo,
        [switch]$NoNewLine
    )
    if (-not $Quiet) {
        if ($NoNewLine) {
            Write-Host $Message -ForegroundColor $Color -NoNewLine
        } else {
            Write-Host $Message -ForegroundColor $Color
        }
    }
}

function Test-Port {
    param(
        [int]$Port,
        [string]$Description
    )
    $PortInUse = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -ErrorAction SilentlyContinue
    if ($PortInUse) {
        Write-ColorOutput "  ⚠  $Description ($Port) - IN USE" $ColorWarning
        return $false
    } else {
        Write-ColorOutput "  ✓  $Description ($Port) - AVAILABLE" $ColorSuccess
        return $true
    }
}

function Check-Requirements {
    Write-ColorOutput "`n=== Checking Requirements ===" $ColorInfo

    $ScriptDir = $PSScriptRoot
    $Requirements = @(
        @{ Name = "Python Runtime"; Path = Join-Path $ScriptDir "python\python.exe"; Required = $true },
        @{ Name = "Node.js Runtime"; Path = Join-Path $ScriptDir "node\node.exe"; Required = $true },
        @{ Name = "Python pip"; Path = Join-Path $ScriptDir "python\Scripts\pip.exe"; Required = $false },
        @{ Name = "Python packages"; Path = Join-Path $ScriptDir "python\Lib\site-packages"; Required = $false },
        @{ Name = "Node modules"; Path = Join-Path $ScriptDir "app\node_modules"; Required = $false },
        @{ Name = "Data directory"; Path = Join-Path $ScriptDir "data"; Required = $true },
        @{ Name = "App directory"; Path = Join-Path $ScriptDir "app"; Required = $true }
    )

    $AllPresent = $true
    foreach ($req in $Requirements) {
        if (Test-Path $req.Path) {
            if ($req.Required) {
                Write-ColorOutput "  ✓  $($req.Name) found at $($req.Path)" $ColorSuccess
            } else {
                Write-ColorOutput "  ✔  $($req.Name) found at $($req.Path)" $ColorDebug
            }
        } else {
            if ($req.Required) {
                Write-ColorOutput "  ✗  $($req.Name) missing at $($req.Path)" $ColorError
                $AllPresent = $false
            } else {
                Write-ColorOutput "  ~  $($req.Name) missing at $($req.Path)" $ColorWarning
            }
        }
    }

    return $AllPresent
}

function Check-Secrets {
    Write-ColorOutput "`n=== Checking Secrets ===" $ColorInfo

    $Secrets = @(
        "AHOS/ai/gemini",
        "AHOS/data/finnhub",
        "AHOS/data/twelvedata",
        "AHOS/data/fred",
        "AHOS/telegram",
        "AHOS/webapi"
    )

    $AllPresent = $true
    foreach ($secret in $Secrets) {
        if (Get-Item "Credential::$secret" -ErrorAction SilentlyContinue) {
            Write-ColorOutput "  ✓  $secret" $ColorSuccess
        } else {
            Write-ColorOutput "  ✗  $secret" $ColorError
            $AllPresent = $false
        }
    }

    return $AllPresent
}

function Check-PythonPackages {
    Write-ColorOutput "`n=== Checking Python Packages ===" $ColorInfo

    $PythonPath = Join-Path $PSScriptRoot "python\python.exe"
    if (-not (Test-Path $PythonPath)) {
        Write-ColorOutput "  ✗ Python runtime not found" $ColorError
        return $false
    }

    # Check basic Python packages
    $Packages = @(
        "pip",
        "requests",
        "flask",
        "sqlite3",
        "yaml"
    )

    $MissingPackages = @()
    $PythonVersion = & $PythonPath --version 2>&1
    Write-ColorOutput "  ✓  Python: $PythonVersion" $ColorSuccess

    foreach ($pkg in $Packages) {
        try {
            $result = & $PythonPath -c "import $pkg; print('$pkg available')" 2>$null
            if ($result -match "$pkg available") {
                Write-ColorOutput "  ✓  $pkg" $ColorSuccess
            } else {
                Write-ColorOutput "  ✗  $pkg" $ColorError
                $MissingPackages += $pkg
            }
        } catch {
            Write-ColorOutput "  ✗  $pkg (import failed)" $ColorError
            $MissingPackages += $pkg
        }
    }

    return ($MissingPackages.Count -eq 0)
}

function Check-NodeModules {
    Write-ColorOutput "`n=== Checking Node.js Dependencies ===" $ColorInfo

    $NodePath = Join-Path $PSScriptRoot "node\node.exe"
    $PackageJson = Join-Path $PSScriptRoot "app\package.json"

    if (-not (Test-Path $NodePath)) {
        Write-ColorOutput "  ✗ Node.js runtime not found" $ColorError
        return $false
    }

    if (-not (Test-Path $PackageJson)) {
        Write-ColorOutput "  ✗ package.json not found" $ColorError
        return $false
    }

    # Check package.json exists
    Write-ColorOutput "  ✓  package.json found" $ColorSuccess

    # Check if node_modules exists
    $NodeModules = Join-Path $PSScriptRoot "app\node_modules"
    if (Test-Path $NodeModules) {
        Write-ColorOutput "  ✓  node_modules exists" $ColorSuccess

        # Count packages
        $PackageCount = (Get-ChildItem $NodeModules | Where-Object { $_.Name -like "*.json" }).Count
        Write-ColorOutput "  ✓  ~$PackageCount packages installed" $ColorDebug
    } else {
        Write-ColorOutput "  ✗  node_modules missing" $ColorWarning
        return $false
    }

    # Check ports
    Write-ColorOutput "`n=== Checking Service Ports ===" $ColorInfo
    $Port3000OK = Test-Port -Port 3000 -Description "Frontend (Next.js)"
    $Port5000OK = Test-Port -Port 5000 -Description "Backend (Flask)"

    return $Port3000OK -and $Port5000OK
}

function Initialize-Data {
    Write-ColorOutput "`n=== Initializing Data Directory ===" $ColorInfo

    $ScriptDir = $PSScriptRoot
    $DataDir = Join-Path $ScriptDir "data"
    $LogsDir = Join-Path $DataDir "logs"

    # Create data directory
    if (-not (Test-Path $DataDir)) {
        New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
        Write-ColorOutput "  ✓  Created data directory" $ColorSuccess
    }

    # Create logs directory
    if (-not (Test-Path $LogsDir)) {
        New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null
        Write-ColorOutput "  ✓  Created logs directory" $ColorSuccess
    }

    # Create config directory
    $ConfigDir = Join-Path $DataDir "config"
    if (-not (Test-Path $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
        Write-ColorOutput "  ✓  Created config directory" $ColorSuccess
    }

    return $true
}

function Generate-Report {
    param(
        [hashtable]$Results
    )

    $ScriptDir = $PSScriptRoot
    $DefaultReportPath = Join-Path $ScriptDir "data\health_report.json"
    $ReportPath = if ($ReportPath) { $ReportPath } else { $DefaultReportPath }

    $Report = @{
        timestamp_utc = Get-Date -Format "o" -UTC
        status = if ($Results.AllOK) { "GREEN" } elseif ($Results.SomeOK) { "YELLOW" } else { "RED" }
        checks = @(
            @{ name = "Requirements"; passed = $RequirementsOK; details = $RequirementsDetails },
            @{ name = "Secrets"; passed = $SecretsOK; details = $SecretsDetails },
            @{ name = "Python"; passed = $PythonOK; details = $PythonDetails },
            @{ name = "Node.js"; passed = $NodeOK; details = $NodeDetails },
            @{ name = "Ports"; passed = $PortsOK; details = $PortsDetails }
        )
    } | ConvertTo-Json -Depth 3

    $Report | Out-File -FilePath $ReportPath -Encoding UTF8
    Write-ColorOutput "  ✓  Report saved to $ReportPath" $ColorSuccess
}

# Main execution
try {
    $ScriptDir = $PSScriptRoot
    $Start = Get-Date

    Write-ColorOutput "AHOS Portable Health Check" $ColorInfo
    Write-ColorOutput "Started: $((Get-Date).ToString())" $ColorInfo
    Write-ColorOutput "Location: $ScriptDir" $ColorInfo

    # Run all checks
    $RequirementsOK = Check-Requirements
    $SecretsOK = Check-Secrets
    $PythonOK = Check-PythonPackages
    $NodeOK = Check-NodeModules
    $PortsOK = ($NodeDetails | Where-Object { $_.Name -eq "Frontend (Next.js)" }).Status -eq "AVAILABLE"

    # Initialize data if needed
    if ($RequirementsOK -and -not (Test-Path (Join-Path $ScriptDir "data"))) {
        Initialize-Data
    }

    # Generate results
    $Results = @{
        AllOK = $RequirementsOK -and $SecretsOK -and $PythonOK -and $NodeOK -and $PortsOK
        SomeOK = $RequirementsOK -or $SecretsOK -or $PythonOK -or $NodeOK -or $PortsOK
        RequirementsOK = $RequirementsOK
        SecretsOK = $SecretsOK
        PythonOK = $PythonOK
        NodeOK = $NodeOK
        PortsOK = $PortsOK
    }

    # Generate report
    Generate-Report -Results $Results

    # Summary
    $Duration = [math]::Round(((Get-Date) - $Start).TotalSeconds, 1)
    Write-ColorOutput "`n" $ColorInfo
    Write-ColorOutput "==========================================================" $ColorInfo
    Write-ColorOutput "  AHOS Portable Health Check — Complete" $ColorInfo
    Write-ColorOutput "  Duration: $Duration seconds" $ColorInfo
    Write-ColorOutput "  Overall Status: $($Results.Status)" $ColorInfo
    Write-ColorOutput "==========================================================" $ColorInfo

    # Exit codes
    if ($Results.AllOK) {
        if (-not $Quiet) { Write-ColorOutput "✓ All systems operational" $ColorSuccess }
        exit 0
    } elseif ($Results.SomeOK) {
        if (-not $Quiet) { Write-ColorOutput "⚠ Some issues detected" $ColorWarning }
        if ($Repair -and $Confirm) {
            Write-ColorOutput "Attempting repairs..." $ColorInfo
            Initialize-Data
        }
        exit 1
    } else {
        Write-ColorOutput "✗ Critical issues detected" $ColorError
        exit 2
    }

} catch {
    Write-ColorOutput "`n✗ Health check failed: $_" $ColorError
    exit 99
}