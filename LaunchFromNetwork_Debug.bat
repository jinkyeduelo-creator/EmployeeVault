@echo off
REM ============================================================
REM EmployeeVault Network Launcher - DEBUG VERSION
REM ============================================================
REM This debug launcher shows detailed information at each step
REM to help diagnose network launch issues.
REM ============================================================

setlocal EnableDelayedExpansion

echo ============================================================
echo EmployeeVault Network Launcher - DEBUG MODE
echo ============================================================
echo.
echo [DEBUG] Current time: %DATE% %TIME%
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
echo [DEBUG] Raw SCRIPT_DIR: %SCRIPT_DIR%

REM Remove trailing backslash for cleaner paths
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
echo [DEBUG] Cleaned SCRIPT_DIR: %SCRIPT_DIR%
echo.

REM Check if EmployeeVault.exe exists
echo [DEBUG] Checking for EmployeeVault.exe...
if exist "%SCRIPT_DIR%\EmployeeVault.exe" (
    echo [OK] EmployeeVault.exe found!
) else (
    echo [ERROR] EmployeeVault.exe NOT FOUND in %SCRIPT_DIR%
    echo.
    echo Please ensure you copied all files from dist\EmployeeVault\
    pause
    exit /b 1
)
echo.

REM Check if we're on a UNC path
echo [DEBUG] Checking if path is UNC...
echo %SCRIPT_DIR% | findstr /i "^\\\\" >nul
if errorlevel 1 (
    echo [INFO] Not a UNC path - running directly
    echo.
    echo Press any key to launch EmployeeVault.exe...
    pause >nul
    
    cd /d "%SCRIPT_DIR%"
    echo [DEBUG] Changed directory to: %CD%
    echo [DEBUG] Launching EmployeeVault.exe...
    echo.
    
    EmployeeVault.exe
    
    set EXIT_CODE=%ERRORLEVEL%
    echo.
    echo [DEBUG] Exit code: %EXIT_CODE%
    goto :end
)

echo [INFO] UNC path detected: %SCRIPT_DIR%
echo [INFO] Will map to temporary drive letter
echo.

REM Find an available drive letter (Z to D)
echo [DEBUG] Searching for available drive letter...
set "DRIVE_LETTER="
for %%L in (Z Y X W V U T S R Q P O N M L K J I H G F E D) do (
    if not exist "%%L:\" (
        set "DRIVE_LETTER=%%L"
        echo [OK] Found available drive: %%L:
        goto :found_drive
    ) else (
        echo [DEBUG] Drive %%L: is in use
    )
)

:found_drive
if "%DRIVE_LETTER%"=="" (
    echo [ERROR] No available drive letters found!
    echo All drive letters from D: to Z: are in use.
    pause
    exit /b 1
)
echo.

REM Map the network path to the drive letter
echo [DEBUG] Mapping network path...
echo [DEBUG] Command: net use %DRIVE_LETTER%: "%SCRIPT_DIR%" /PERSISTENT:NO
echo.

net use %DRIVE_LETTER%: "%SCRIPT_DIR%" /PERSISTENT:NO

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to map network drive!
    echo Error code: %ERRORLEVEL%
    echo.
    echo Possible causes:
    echo - Network share not accessible
    echo - Insufficient permissions
    echo - Network connection issue
    echo.
    pause
    exit /b 1
)

echo [OK] Successfully mapped to %DRIVE_LETTER%:
echo.

REM Change to the mapped drive
echo [DEBUG] Changing to mapped drive...
cd /d %DRIVE_LETTER%:\

if errorlevel 1 (
    echo [ERROR] Failed to change to %DRIVE_LETTER%:
    net use %DRIVE_LETTER%: /DELETE /YES >nul 2>&1
    pause
    exit /b 1
)

echo [OK] Current directory: %CD%
echo.

REM List files to verify
echo [DEBUG] Listing files in directory:
dir /b *.exe *.dll 2>nul | findstr /i "." >nul
if errorlevel 1 (
    echo [WARNING] No .exe or .dll files found!
) else (
    echo ----------------------------------------
    dir /b EmployeeVault.exe _internal 2>nul
    echo ----------------------------------------
)
echo.

REM Ready to launch
echo ============================================================
echo Ready to launch EmployeeVault.exe
echo ============================================================
echo.
echo Press any key to start the application...
pause >nul

echo.
echo [DEBUG] Launching EmployeeVault.exe from %DRIVE_LETTER%:\
echo [DEBUG] Time: %TIME%
echo.

REM Run the application
EmployeeVault.exe

set EXIT_CODE=%ERRORLEVEL%

echo.
echo ============================================================
echo [DEBUG] Application exited
echo [DEBUG] Exit code: %EXIT_CODE%
echo [DEBUG] Time: %TIME%
echo ============================================================
echo.

REM Cleanup - unmap the drive
echo [DEBUG] Cleaning up - unmapping drive %DRIVE_LETTER%:
cd /d %TEMP%
net use %DRIVE_LETTER%: /DELETE /YES >nul 2>&1

if %EXIT_CODE% equ 0 (
    echo [OK] Application exited normally
) else (
    echo [WARNING] Application exited with error code: %EXIT_CODE%
    echo.
    echo If you saw Python errors above, common causes include:
    echo - Missing DLL files in _internal folder
    echo - Database connection issues
    echo - Permission problems
    echo.
)

:end
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXIT_CODE%
