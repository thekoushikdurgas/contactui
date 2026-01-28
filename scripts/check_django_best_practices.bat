@echo off
REM Main orchestrator for Django Best Practices Checklist
REM Runs all category checks and generates comprehensive report

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py
set REPORTS_DIR=%PROJECT_ROOT%\reports

echo ================================================================================
echo Django Best Practices Checker - 100 Point Checklist
echo ================================================================================
echo.

REM Create reports directory
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

REM Run main Python checker
echo Running comprehensive Django best practices check...
echo.
python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Check failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

echo.
echo ================================================================================
echo All checks completed!
echo Reports saved to: %REPORTS_DIR%
echo ================================================================================

endlocal
