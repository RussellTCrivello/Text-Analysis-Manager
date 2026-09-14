@echo off
:: Build Portable Version for Text Analysis Manager
:: Creates a single-file executable that can run from anywhere

echo.
echo ============================================================
echo   Text Analysis Manager - Build Portable
echo ============================================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

:: Change to script directory
cd /d "%~dp0"

:: Run the build script with portable flag
echo Building portable executable...
echo.
python build.py --portable

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   BUILD FAILED
    echo ============================================================
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo ============================================================
echo.
echo The portable executable is in: portable\
echo.
pause
