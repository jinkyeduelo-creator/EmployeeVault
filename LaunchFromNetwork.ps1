# ============================================================
# EmployeeVault Network Launcher (PowerShell)
# ============================================================
# This launcher solves the UNC path issue where PySide6/Shiboken
# DLLs cannot load from network paths (\\server\share).
#
# It works by mapping the network path to a temporary drive letter
# before running the application.
# ============================================================

$ErrorActionPreference = "Stop"

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if we're on a UNC path
$IsUNC = $ScriptDir -match '^\\\\[^\\]+\\[^\\]+'

if (-not $IsUNC) {
    Write-Host "Running EmployeeVault directly..." -ForegroundColor Green
    & "$ScriptDir\EmployeeVault.exe"
    exit $LASTEXITCODE
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "EmployeeVault Network Launcher" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Detected UNC path: $ScriptDir" -ForegroundColor Yellow
Write-Host "Mapping to temporary drive letter..." -ForegroundColor White

# Find an available drive letter (Z to D)
$DriveLetter = $null
foreach ($letter in 'Z','Y','X','W','V','U','T','S','R','Q','P','O','N','M','L','K','J','I','H','G','F','E','D') {
    if (-not (Test-Path "${letter}:\")) {
        $DriveLetter = $letter
        break
    }
}

if (-not $DriveLetter) {
    Write-Host "ERROR: No available drive letters!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Using drive letter: ${DriveLetter}:" -ForegroundColor Green

try {
    # Map the network path
    $NetPath = $ScriptDir.TrimEnd('\')
    $null = New-PSDrive -Name $DriveLetter -PSProvider FileSystem -Root $NetPath -ErrorAction Stop
    
    Write-Host "Network path mapped successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "Starting EmployeeVault..." -ForegroundColor Cyan
    Write-Host ""
    
    # Change to mapped drive and run application
    Push-Location "${DriveLetter}:\"
    try {
        & "${DriveLetter}:\EmployeeVault.exe"
        $ExitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    
    # Cleanup
    Write-Host ""
    Write-Host "Cleaning up..." -ForegroundColor Gray
    Remove-PSDrive -Name $DriveLetter -Force -ErrorAction SilentlyContinue
    
    if ($ExitCode -ne 0) {
        Write-Host ""
        Write-Host "============================================================" -ForegroundColor Red
        Write-Host "Application exited with error code: $ExitCode" -ForegroundColor Red
        Write-Host "============================================================" -ForegroundColor Red
        Read-Host "Press Enter to exit"
    }
    
    exit $ExitCode
}
catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try to cleanup if mapping was partially successful
    Remove-PSDrive -Name $DriveLetter -Force -ErrorAction SilentlyContinue
    
    Read-Host "Press Enter to exit"
    exit 1
}
