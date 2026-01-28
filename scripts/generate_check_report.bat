@echo off
REM Generate comprehensive check report from all category checks

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYTHON_SCRIPT=%SCRIPT_DIR%django_checker.py
set REPORTS_DIR=%PROJECT_ROOT%\reports

echo ================================================================================
echo Generating Comprehensive Django Best Practices Report
echo ================================================================================
echo.

REM Create reports directory
if not exist "%REPORTS_DIR%" mkdir "%REPORTS_DIR%"

REM Run full check and generate report
python "%PYTHON_SCRIPT%" "%PROJECT_ROOT%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Report generated successfully!
    echo Location: %REPORTS_DIR%
    echo.
    echo Opening reports directory...
    start "" "%REPORTS_DIR%"
) else (
    echo.
    echo ERROR: Report generation failed with exit code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

endlocal
