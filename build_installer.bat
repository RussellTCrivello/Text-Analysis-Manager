@echo off
:: Build Installer for Text Analysis Manager
:: This script builds the complete Windows installer

echo.
echo ============================================================
echo   Text Analysis Manager - Build Installer
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

:: Run the build script
echo Starting build process...
echo.
python build.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   BUILD FAILED
    echo ============================================================
    echo.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD COMPLETE
echo ============================================================
echo.
echo The installer is located in: installer_output\
echo.
pause
