@echo off
setlocal enabledelayedexpansion

echo ========================================
echo        PyChat Client Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version

REM Check if virtual environment exists
if not exist ".venv\" (
    echo.
    echo [2/4] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created successfully.
) else (
    echo.
    echo [2/4] Virtual environment already exists.
)

REM Activate virtual environment
echo.
echo [3/4] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)

REM Check and install required packages
echo.
echo [4/4] Installing/checking required packages...

REM Check if cryptography is installed
python -c "import cryptography" >nul 2>&1
if errorlevel 1 (
    echo Installing cryptography...
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install cryptography
    if errorlevel 1 (
        echo [ERROR] Failed to install cryptography!
        pause
        exit /b 1
    )
    echo [OK] cryptography installed successfully.
) else (
    echo [OK] All required packages are already installed.
)

echo.
echo ========================================
echo   Starting Multi-Channel PyChat Client
echo ========================================
echo.

REM Start the multichannel client
python client_multichannel.py

REM If client exits, pause so user can see any error messages
if errorlevel 1 (
    echo.
    echo [ERROR] Client exited with error code: %errorlevel%
    pause
)
