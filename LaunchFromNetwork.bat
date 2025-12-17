@echo off
REM ============================================================
REM EmployeeVault Network Launcher
REM ============================================================
REM This launcher solves the UNC path issue where PySide6/Shiboken
REM DLLs cannot load from network paths (\\server\share).
REM 
REM It works by:
REM 1. Mapping the network path to a temporary drive letter
REM 2. Running the application from the mapped drive
REM 3. Unmapping the drive when done
REM ============================================================

setlocal EnableDelayedExpansion

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Check if we're on a UNC path
echo %SCRIPT_DIR% | findstr /i "^\\\\" >nul
if errorlevel 1 (
    REM Not a UNC path, run directly
    echo Running EmployeeVault directly...
    "%SCRIPT_DIR%EmployeeVault.exe"
    goto :end
)

echo ============================================================
echo EmployeeVault Network Launcher
echo ============================================================
echo.
echo Detected UNC path: %SCRIPT_DIR%
echo Mapping to temporary drive letter...

REM Find an available drive letter (starting from Z going backwards)
set "DRIVE_LETTER="
for %%d in (Z Y X W V U T S R Q P O N M L K J I H G F E D) do (
    if not exist %%d:\ (
        set "DRIVE_LETTER=%%d"
        goto :found_drive
    )
)

echo ERROR: No available drive letters!
pause
goto :end

:found_drive
echo Using drive letter: %DRIVE_LETTER%:

REM Remove trailing backslash from SCRIPT_DIR for net use
set "NET_PATH=%SCRIPT_DIR:~0,-1%"

REM Map the network path
net use %DRIVE_LETTER%: "%NET_PATH%" /persistent:no >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to map network drive!
    echo Please try running: net use %DRIVE_LETTER%: "%NET_PATH%"
    pause
    goto :end
)

echo Network path mapped successfully.
echo.
echo Starting EmployeeVault...
echo.

REM Change to the mapped drive and run the application
pushd %DRIVE_LETTER%:\
"%DRIVE_LETTER%:\EmployeeVault.exe"
set "EXIT_CODE=%errorlevel%"
popd

REM Cleanup: Unmap the network drive
echo.
echo Cleaning up...
net use %DRIVE_LETTER%: /delete /yes >nul 2>&1

if %EXIT_CODE% neq 0 (
    echo.
    echo ============================================================
    echo Application exited with error code: %EXIT_CODE%
    echo ============================================================
    pause
)

:end
endlocal
