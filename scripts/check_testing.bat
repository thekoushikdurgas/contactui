@echo off
REM Check Testing (8 points)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py

echo ================================================================================
echo Checking Testing (Points 83-90)
echo ================================================================================
echo.

python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%" --category "Testing"

endlocal
