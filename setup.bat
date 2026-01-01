@echo off
REM VCS Extra Duty Scraper - Setup Script
REM Author: R. A. Carucci
REM Purpose: One-time setup for dependencies and folder structure

echo ============================================================
echo VCS EXTRA DUTY SCRAPER - INSTALLATION
echo ============================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python found
python --version

REM Install dependencies
echo.
echo [2/4] Installing Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Package installation failed
    pause
    exit /b 1
)

REM Create folder structure
echo.
echo [3/4] Creating folder structure...
if not exist "data" mkdir data
if not exist "data\raw_scraper_csv" mkdir data\raw_scraper_csv
if not exist "data\dataset1" mkdir data\dataset1
if not exist "data\dataset2" mkdir data\dataset2
if not exist "logs" mkdir logs
if not exist "output" mkdir output

REM Create .gitkeep files to preserve empty folders in git
echo. > data\raw_scraper_csv\.gitkeep
echo. > data\dataset1\.gitkeep
echo. > data\dataset2\.gitkeep
echo. > logs\.gitkeep
echo. > output\.gitkeep

REM Verify ChromeDriver
echo.
echo [4/4] Checking Chrome installation...
where chrome.exe >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Chrome found
) else (
    echo [WARNING] Chrome not found in PATH
    echo          Make sure Chrome is installed
)

echo.
echo ============================================================
echo INSTALLATION COMPLETE
echo ============================================================
echo.
echo Next steps:
echo   1. Edit config.json if needed (my_name, target_year)
echo   2. Run: run_scraper.bat
echo.
pause
