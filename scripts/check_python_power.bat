@echo off
REM Check Python/Django Power Features (5 points)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py

echo ================================================================================
echo Checking Python/Django Power Features (Points 96-100)
echo ================================================================================
echo.

python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%" --category "Python Power"

endlocal
