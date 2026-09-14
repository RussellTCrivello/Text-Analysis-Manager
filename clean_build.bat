@echo off
:: Clean Build Artifacts
:: Removes all build-related files and folders

echo.
echo ============================================================
echo   Text Analysis Manager - Clean Build
echo ============================================================
echo.

:: Change to script directory
cd /d "%~dp0"

:: Run the clean command
python build.py --clean

echo.
echo Clean complete!
echo.
pause
