@echo off
REM Check Views & APIs (12 points)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py

echo ================================================================================
echo Checking Views & APIs (Points 41-52)
echo ================================================================================
echo.

python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%" --category "Views & APIs"

endlocal
