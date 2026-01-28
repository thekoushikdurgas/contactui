@echo off
REM Django-Q Worker Startup Script (Windows)
REM 
REM This script starts the Django-Q worker cluster for background task processing.
REM Run this in a separate command prompt or as a Windows service.

setlocal enabledelayedexpansion

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

REM Change to project directory
cd /d "%PROJECT_DIR%"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Load environment variables from .env if it exists
if exist ".env" (
    echo Loading environment variables from .env...
    REM Note: Windows batch doesn't easily load .env files
    REM Consider using python-dotenv or setting environment variables manually
)

REM Start Django-Q cluster
echo Starting Django-Q worker cluster...
echo Project directory: %PROJECT_DIR%
echo Press Ctrl+C to stop the worker
echo.

python manage.py qcluster

pause
