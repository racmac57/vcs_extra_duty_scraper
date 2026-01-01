@echo off
REM 🕒 2025-12-03-11-15-00
REM Extra_Duty/scripts/run_scraper.bat
REM Author: R. A. Carucci
REM Purpose: Launch Chrome in debug mode and run the VCS Extra Duty scraper

echo ============================================================
echo VCS EXTRA DUTY SCRAPER LAUNCHER
echo ============================================================
echo.

REM Configuration
set CHROME_PATH=“C:\Program Files\Google\Chrome\Application\chrome.exe”
set DEBUG_PORT=9222
set USER_DATA=“C:\ChromeDebug”
set SCRIPT_DIR=C:\Users\carucci_r\OneDrive - City of Hackensack\RAC\Extra_Duty\scripts
set PORTAL_URL=https://app10.vcssoftware.com/extra-duty-signup

REM Check if Chrome is already running with debug port
netstat -an | findstr “:%DEBUG_PORT%” >nul
if %ERRORLEVEL%==0 (
echo [OK] Chrome debug port %DEBUG_PORT% is active
goto :run_scraper
)

REM Start Chrome with remote debugging
echo [INFO] Starting Chrome with remote debugging…
start “” %CHROME_PATH% –remote-debugging-port=%DEBUG_PORT% –user-data-dir=%USER_DATA% %PORTAL_URL%

echo.
echo ============================================================
echo MANUAL STEPS REQUIRED:
echo ============================================================
echo 1. Log into VCS portal in the Chrome window that just opened
echo 2. Make sure you’re on the Extra Duty Signup page
echo 3. Press any key when ready to run the scraper…
echo ============================================================
pause

:run_scraper
echo.
echo [INFO] Running scraper…
cd /d “%SCRIPT_DIR%”

REM Default mode - change as needed
REM Options: q1, q2, q3, q4, full_year, monthly
set MODE=q4

python vcs_extra_duty_scrape.py –mode %MODE%

echo.
echo ============================================================
echo SCRAPER COMPLETE
echo ============================================================
echo.
echo Next step: Run the post-processor to update the master Excel
echo Command: python traffic_jobs_postprocessor.py
echo.
pause