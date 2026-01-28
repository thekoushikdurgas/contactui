@echo off
REM Check Deployment & Ops (5 points)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py

echo ================================================================================
echo Checking Deployment & Ops (Points 91-95)
echo ================================================================================
echo.

python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%" --category "Deployment"

endlocal
