@echo off
REM Check Performance & Optimization (10 points)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py

echo ================================================================================
echo Checking Performance & Optimization (Points 73-82)
echo ================================================================================
echo.

python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%" --category "Performance"

endlocal
