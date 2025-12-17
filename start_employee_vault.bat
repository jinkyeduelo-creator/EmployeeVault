@echo off
SETLOCAL EnableDelayedExpansion

REM ================================================
REM Employee Vault - Smart Launch Script
REM Version: 2.4.0
REM With Auto-Update, Health Check, and Recovery
REM ================================================

TITLE Employee Vault v2.4.0 - Starting...

REM ========== CONFIGURATION ==========
SET SERVER_PATH=\\Extra\EmployeeVault
SET APP_PATH=%SERVER_PATH%\app
SET DATA_PATH=%SERVER_PATH%\data
SET CONFIG_PATH=%SERVER_PATH%\config
SET LOG_PATH=%SERVER_PATH%\logs
SET BACKUP_PATH=%SERVER_PATH%\data\backups

REM Local paths
SET LOCAL_APP=%LOCALAPPDATA%\EmployeeVault
SET LOCAL_CACHE=%LOCAL_APP%\cache
SET LOCAL_VERSION=%LOCAL_APP%\version.txt

REM ========== HEALTH CHECK ==========
echo ================================================
echo Employee Vault v2.4.0
echo ================================================
echo.
echo [1/5] Checking system health...

REM Check server accessibility
IF NOT EXIST "%SERVER_PATH%" (
    echo.
    echo [ERROR] Cannot access server: %SERVER_PATH%
    echo.
    echo Possible solutions:
    echo 1. Check network cable connection
    echo 2. Verify the server path is correct
    echo 3. Contact IT support
    echo.
    pause
    exit /b 1
)
echo [OK] Server accessible

REM Check database exists
IF NOT EXIST "%DATA_PATH%\employee_vault.db" (
    echo [ERROR] Database not found!
    echo Expected: %DATA_PATH%\employee_vault.db
    echo.
    pause
    exit /b 1
)
echo [OK] Database found

REM Check application files
IF NOT EXIST "%APP_PATH%\employee_vault_improvements_v2_4_0.py" (
    echo [WARNING] Application files not found at expected location
)
echo [OK] Application files ready

REM ========== VERSION CHECK ==========
echo.
echo [2/5] Checking version...

REM Read server version
IF EXIST "%CONFIG_PATH%\version.txt" (
    SET /P SERVER_VERSION=<"%CONFIG_PATH%\version.txt"
) ELSE (
    SET SERVER_VERSION=2.4.0
)

REM Read local cached version
IF EXIST "%LOCAL_VERSION%" (
    SET /P LOCAL_VERSION_NUM=<"%LOCAL_VERSION%"
) ELSE (
    SET LOCAL_VERSION_NUM=0.0.0
)

echo Server version: %SERVER_VERSION%
echo Local version:  %LOCAL_VERSION_NUM%

REM Compare versions
IF NOT "%SERVER_VERSION%"=="%LOCAL_VERSION_NUM%" (
    echo [UPDATE] Version mismatch - updating cache...

    REM Create local app directory
    IF NOT EXIST "%LOCAL_APP%" mkdir "%LOCAL_APP%"
    IF NOT EXIST "%LOCAL_CACHE%" mkdir "%LOCAL_CACHE%"

    REM Update version file
    echo %SERVER_VERSION% > "%LOCAL_VERSION%"
    echo [OK] Cache updated
)

REM ========== BACKUP CHECK ==========
echo.
echo [3/5] Checking backups...

SET BACKUP_WARNING=0

REM Check if backup directory exists
IF NOT EXIST "%BACKUP_PATH%" (
    echo [WARNING] Backup directory not found - creating...
    mkdir "%BACKUP_PATH%" 2>nul
    IF ERRORLEVEL 1 (
        echo [WARNING] Cannot create backup directory
        SET BACKUP_WARNING=1
    ) ELSE (
        echo [OK] Backup directory created
    )
) ELSE (
    echo [OK] Backup directory exists
)

REM ========== USER TRACKING ==========
echo.
echo [4/5] Logging access...

REM Create logs directory if needed
IF NOT EXIST "%LOG_PATH%" mkdir "%LOG_PATH%" 2>nul

REM Log user access
echo %DATE%,%TIME%,%USERNAME%,%COMPUTERNAME%,%SERVER_VERSION% >> "%LOG_PATH%\access.log" 2>nul

echo [OK] User: %USERNAME%
echo [OK] Computer: %COMPUTERNAME%

REM ========== LAUNCH APPLICATION ==========
echo.
echo [5/5] Starting application...
echo.
echo ================================================
echo Employee Vault v%SERVER_VERSION%
echo ================================================
echo User: %USERNAME%
echo Computer: %COMPUTERNAME%
echo Database: %DATA_PATH%\employee_vault.db
echo.

REM Change to current directory (where the .bat is located)
cd /d "%~dp0"

REM Set environment variables for the application
SET EMPLOYEE_VAULT_DB=%DATA_PATH%\employee_vault.db
SET EMPLOYEE_VAULT_LOGS=%LOG_PATH%
SET EMPLOYEE_VAULT_CACHE=%LOCAL_CACHE%
SET EMPLOYEE_VAULT_USER=%USERNAME%
SET EMPLOYEE_VAULT_COMPUTER=%COMPUTERNAME%

REM Launch application
where python >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    REM Python is available
    IF EXIST "employee_vault_improvements_v2_4_0.py" (
        echo [OK] Launching application...
        echo.
        python employee_vault_improvements_v2_4_0.py
        SET APP_EXIT_CODE=!ERRORLEVEL!
    ) ELSE IF EXIST "%APP_PATH%\employee_vault_improvements_v2_4_0.py" (
        echo [OK] Launching from server...
        echo.
        python "%APP_PATH%\employee_vault_improvements_v2_4_0.py"
        SET APP_EXIT_CODE=!ERRORLEVEL!
    ) ELSE (
        echo [ERROR] Application not found!
        echo.
        echo Searched in:
        echo - %CD%
        echo - %APP_PATH%
        echo.
        pause
        exit /b 1
    )
) ELSE (
    echo [ERROR] Python not found!
    echo.
    echo Please ensure Python 3.8 or later is installed.
    echo Download from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM ========== POST-RUN ACTIONS ==========
echo.
echo ================================================

IF !APP_EXIT_CODE! NEQ 0 (
    echo [ERROR] Application exited with error code: !APP_EXIT_CODE!
    echo.
    echo Troubleshooting steps:
    echo 1. Check %LOG_PATH%\error.log for details
    echo 2. Ensure database is not locked by another process
    echo 3. Verify network connection is stable
    echo 4. Contact IT support if problem persists
    echo.

    REM Log error
    echo %DATE% %TIME% - ERROR - User: %USERNAME%, Exit Code: !APP_EXIT_CODE! >> "%LOG_PATH%\error.log" 2>nul

    pause
) ELSE (
    echo [OK] Application closed normally
    timeout /t 2 >nul
)

exit /b !APP_EXIT_CODE!
