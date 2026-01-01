# 🕒 2025-12-03-11-00-00

# Extra_Duty/scripts/vcs_extra_duty_scrape.py

# Author: R. A. Carucci

# Purpose: Selenium scraper for VCS Extra Duty portal - extracts job grid data to timestamped CSVs for downstream processing

# “””
VCS Extra Duty Scraper

Attaches to a running Chrome instance, scrapes the Extra Duty job grid,
and saves timestamped CSVs for the post-processor.

Prerequisites:
1. Start Chrome with remote debugging:
chrome.exe –remote-debugging-port=9222 –user-data-dir=“C:\ChromeDebug”
2. Log into VCS portal manually
3. Navigate to Extra Duty Signup page
4. Then run this script

Usage:
python vcs_extra_duty_scrape.py                    # Default: Q4 2025
python vcs_extra_duty_scrape.py –mode q4          # Q4 only
python vcs_extra_duty_scrape.py –mode full_year   # All of 2025
python vcs_extra_duty_scrape.py –mode month –month 11  # November only
“””

import csv
import json
import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Selenium imports

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
StaleElementReferenceException,
TimeoutException,
NoSuchElementException,
ElementClickInterceptedException,
WebDriverException
)

# ============================================================

# CONFIGURATION

# ============================================================

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / 'config.json'
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        CONFIG = config_data.get('scraper', {})
        # Merge paths from config
        CONFIG.update(config_data.get('paths', {}))
        CONFIG['target_year'] = config_data.get('postprocessor', {}).get('target_year', 2025)
else:
    raise FileNotFoundError(f"config.json not found at {CONFIG_PATH}")

# Date windows for 2025

DATE_WINDOWS = {
“q1”: [(“01/01/2025”, “03/31/2025”)],
“q2”: [(“04/01/2025”, “06/30/2025”)],
“q3”: [(“07/01/2025”, “09/30/2025”)],
“q4”: [(“10/01/2025”, “12/31/2025”)],
“full_year”: [
(“01/01/2025”, “03/31/2025”),
(“04/01/2025”, “06/30/2025”),
(“07/01/2025”, “09/30/2025”),
(“10/01/2025”, “12/31/2025”)
],
“monthly”: [
(“01/01/2025”, “01/31/2025”),
(“02/01/2025”, “02/28/2025”),
(“03/01/2025”, “03/31/2025”),
(“04/01/2025”, “04/30/2025”),
(“05/01/2025”, “05/31/2025”),
(“06/01/2025”, “06/30/2025”),
(“07/01/2025”, “07/31/2025”),
(“08/01/2025”, “08/31/2025”),
(“09/01/2025”, “09/30/2025”),
(“10/01/2025”, “10/31/2025”),
(“11/01/2025”, “11/30/2025”),
(“12/01/2025”, “12/31/2025”)
]
}

# ============================================================

# LOGGING SETUP

# ============================================================

def setup_logging():
“”“Configure logging to both console and file.”””
log_folder = Path(CONFIG[“log_folder”])
log_folder.mkdir(parents=True, exist_ok=True)

```
log_filename = f"scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_path = log_folder / log_filename

# Create logger
logger = logging.getLogger("VCSScraper")
logger.setLevel(logging.DEBUG)

# File handler (detailed)
file_handler = logging.FileHandler(log_path, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
file_handler.setFormatter(file_format)

# Console handler (summary)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(message)s')
console_handler.setFormatter(console_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info(f"📝 Log file: {log_path}")
return logger
```

# Global logger

logger = None

# ============================================================

# HELPER FUNCTIONS

# ============================================================

def get_output_filename(prefix=“vcs_extra_duty_jobs”, suffix=””):
“”“Generate timestamped output filename.

```
Args:
    prefix: Base filename
    suffix: Optional suffix like '_Q4' or '_2025M11'

Returns:
    Filename like: vcs_extra_duty_jobs_Q4_20251203_1430.csv
"""
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
return f"{prefix}{suffix}_{timestamp}.csv"
```

def get_suffix_from_dates(start_date, end_date):
“”“Generate suffix based on date range.

```
Args:
    start_date: Start date string MM/DD/YYYY
    end_date: End date string MM/DD/YYYY

Returns:
    Suffix like '_2025Q4' or '_2025M11'
"""
try:
    start = datetime.strptime(start_date, "%m/%d/%Y")
    end = datetime.strptime(end_date, "%m/%d/%Y")
    year = start.year
    
    # Single month
    if start.month == end.month:
        return f"_{year}M{start.month:02d}"
    
    # Quarter detection
    quarter_ranges = {
        (1, 3): "Q1",
        (4, 6): "Q2", 
        (7, 9): "Q3",
        (10, 12): "Q4"
    }
    for (sm, em), q in quarter_ranges.items():
        if start.month == sm and end.month == em:
            return f"_{year}{q}"
    
    # Generic range
    return f"_{year}_{start.month:02d}to{end.month:02d}"
except Exception:
    return ""
```

def retry_on_stale(func, max_retries=None, delay=None):
“”“Decorator/wrapper to retry on stale element exceptions.

```
Args:
    func: Function to retry
    max_retries: Number of retries (default from CONFIG)
    delay: Delay between retries (default from CONFIG)

Returns:
    Result of func, or raises last exception
"""
max_retries = max_retries or CONFIG["max_retries"]
delay = delay or CONFIG["retry_delay"]

last_exception = None
for attempt in range(max_retries + 1):
    try:
        return func()
    except (StaleElementReferenceException, NoSuchElementException) as e:
        last_exception = e
        if attempt < max_retries:
            logger.debug(f"Retry {attempt + 1}/{max_retries} after: {type(e).__name__}")
            time.sleep(delay)
        else:
            logger.error(f"Failed after {max_retries} retries: {type(e).__name__}")
raise last_exception
```

# ============================================================

# BROWSER CONNECTION

# ============================================================

def connect_to_chrome():
“”“Attach to already-running Chrome instance with remote debugging.

```
Returns:
    WebDriver instance

Raises:
    WebDriverException if Chrome is not running or not accessible
"""
logger.info("🔗 Connecting to Chrome...")

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", CONFIG["chrome_debugger_address"])

try:
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(CONFIG["page_load_timeout"])
    
    current_url = driver.current_url
    logger.info(f"   Connected to: {current_url[:60]}...")
    
    # Verify we're on the right page
    if "extra-duty" not in current_url.lower() and "vcssoftware" not in current_url.lower():
        logger.warning("⚠️  Current page may not be the Extra Duty portal")
        logger.warning(f"   Expected URL containing: {CONFIG['portal_url']}")
    
    return driver

except WebDriverException as e:
    logger.error("❌ Failed to connect to Chrome")
    logger.error("   Make sure Chrome is running with:")
    logger.error('   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\ChromeDebug"')
    raise
```

def verify_page_state(driver):
“”“Check if page is loaded and ready for interaction.

```
Returns:
    True if page appears ready, False otherwise
"""
try:
    WebDriverWait(driver, 5).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    return True
except TimeoutException:
    return False
```

# ============================================================

# DATE RANGE MANAGEMENT

# ============================================================

def find_date_input(driver, input_type):
“”“Locate the start or end date input field.

```
Args:
    driver: WebDriver instance
    input_type: 'start' or 'end'

Returns:
    WebElement for the date input
"""
# Multiple locator strategies
locators = [
    # By placeholder text
    (By.XPATH, f"//input[contains(@placeholder, '{input_type.capitalize()}')]"),
    (By.XPATH, f"//input[contains(@placeholder, '{input_type}')]"),
    # By aria-label
    (By.XPATH, f"//input[contains(@aria-label, '{input_type}')]"),
    (By.XPATH, f"//input[contains(@aria-label, '{input_type.capitalize()} Date')]"),
    # By name attribute
    (By.XPATH, f"//input[contains(@name, '{input_type}')]"),
    # By ID containing start/end
    (By.XPATH, f"//input[contains(@id, '{input_type}')]"),
    # Generic date inputs (first = start, second = end)
    (By.CSS_SELECTOR, "input[type='date']"),
    (By.CSS_SELECTOR, "input[type='text'][placeholder*='date' i]"),
]

for by, selector in locators:
    try:
        elements = driver.find_elements(by, selector)
        if elements:
            # For generic locators, pick first for start, second for end
            if input_type == 'start' and len(elements) >= 1:
                return elements[0]
            elif input_type == 'end' and len(elements) >= 2:
                return elements[1]
            elif elements:
                return elements[0]
    except Exception:
        continue

raise NoSuchElementException(f"Could not find {input_type} date input")
```

def set_date_range(driver, start_date, end_date):
“”“Set the date range filter on the portal.

```
Args:
    driver: WebDriver instance
    start_date: Start date as MM/DD/YYYY
    end_date: End date as MM/DD/YYYY

Returns:
    True if successful
"""
logger.info(f"📅 Setting date range: {start_date} to {end_date}")

def set_single_date(input_type, date_value):
    """Set a single date input with retry."""
    def action():
        element = find_date_input(driver, input_type)
        
        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(CONFIG["action_delay"])
        
        # Clear existing value
        element.click()
        time.sleep(0.2)
        element.send_keys(Keys.CONTROL + "a")
        time.sleep(0.1)
        element.send_keys(Keys.DELETE)
        time.sleep(0.2)
        
        # Type new value
        element.send_keys(date_value)
        time.sleep(0.2)
        
        # Tab out to trigger change event
        element.send_keys(Keys.TAB)
        time.sleep(CONFIG["action_delay"])
        
        logger.debug(f"   Set {input_type} date to: {date_value}")
        return True
    
    return retry_on_stale(action)

# Set start date
set_single_date('start', start_date)

# Set end date
set_single_date('end', end_date)

# Wait for grid to start refreshing
time.sleep(CONFIG["grid_refresh_wait"])

logger.info("   ✓ Date range set")
return True
```

# ============================================================

# TOGGLE MANAGEMENT

# ============================================================

def find_toggle_element(driver, toggle_name):
“”“Locate a toggle/checkbox element by its label text.

```
Args:
    driver: WebDriver instance
    toggle_name: Text label of the toggle (e.g., "Show Closed Jobs")

Returns:
    Tuple of (toggle_element, is_checked)
"""
# Multiple locator strategies for toggles
locators = [
    # Material UI style toggle with label
    (By.XPATH, f"//label[contains(text(), '{toggle_name}')]//input"),
    (By.XPATH, f"//label[contains(text(), '{toggle_name}')]/preceding-sibling::input"),
    (By.XPATH, f"//label[contains(text(), '{toggle_name}')]/following-sibling::input"),
    # Span label with adjacent input
    (By.XPATH, f"//span[contains(text(), '{toggle_name}')]//ancestor::label//input"),
    (By.XPATH, f"//span[contains(text(), '{toggle_name}')]//preceding::input[1]"),
    # Checkbox with aria-label
    (By.XPATH, f"//input[@aria-label='{toggle_name}']"),
    (By.XPATH, f"//input[contains(@aria-label, '{toggle_name}')]"),
    # Button-style toggle
    (By.XPATH, f"//button[contains(text(), '{toggle_name}')]"),
    (By.XPATH, f"//button[contains(@aria-label, '{toggle_name}')]"),
    # Switch/slider style
    (By.XPATH, f"//*[contains(text(), '{toggle_name}')]//ancestor::*[contains(@class, 'switch') or contains(@class, 'toggle')]//input"),
    # Generic clickable element near label
    (By.XPATH, f"//*[contains(text(), '{toggle_name}')]//ancestor::*[1]//*[@role='checkbox' or @role='switch']"),
]

for by, selector in locators:
    try:
        elements = driver.find_elements(by, selector)
        for element in elements:
            # Check if it's interactable
            if element.is_displayed():
                # Determine checked state
                is_checked = (
                    element.is_selected() or 
                    element.get_attribute("checked") == "true" or
                    element.get_attribute("aria-checked") == "true" or
                    "checked" in (element.get_attribute("class") or "").lower()
                )
                return element, is_checked
    except Exception:
        continue

raise NoSuchElementException(f"Could not find toggle: {toggle_name}")
```

def ensure_toggle_state(driver, toggle_name, desired_state=True):
“”“Ensure a toggle is in the desired state (on/off).

```
Args:
    driver: WebDriver instance
    toggle_name: Text label of the toggle
    desired_state: True for ON, False for OFF

Returns:
    True if toggle is now in desired state
"""
state_text = "ON" if desired_state else "OFF"
logger.debug(f"   Ensuring toggle '{toggle_name}' is {state_text}")

def action():
    element, is_checked = find_toggle_element(driver, toggle_name)
    
    if is_checked == desired_state:
        logger.debug(f"   Toggle already {state_text}")
        return True
    
    # Need to click to change state
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(CONFIG["action_delay"])
    
    try:
        element.click()
    except ElementClickInterceptedException:
        # Try clicking via JavaScript
        driver.execute_script("arguments[0].click();", element)
    
    time.sleep(CONFIG["action_delay"])
    
    # Verify state changed
    _, new_state = find_toggle_element(driver, toggle_name)
    if new_state == desired_state:
        logger.debug(f"   Toggle changed to {state_text}")
        return True
    else:
        logger.warning(f"   Toggle click did not change state")
        return False

return retry_on_stale(action)
```

def set_all_toggles(driver):
“”“Set both required toggles to ON state.

```
Args:
    driver: WebDriver instance

Returns:
    True if all toggles are set correctly
"""
logger.info("🔘 Setting toggles...")

toggles = [
    "Show Closed Jobs",
    "Show Jobs with Scheduling Conflicts"
]

all_success = True
for toggle_name in toggles:
    try:
        result = ensure_toggle_state(driver, toggle_name, desired_state=True)
        if result:
            logger.info(f"   ✓ {toggle_name}: ON")
        else:
            logger.warning(f"   ⚠ {toggle_name}: Could not verify state")
            all_success = False
    except NoSuchElementException:
        logger.warning(f"   ⚠ Toggle not found: {toggle_name}")
        all_success = False

return all_success
```

def verify_toggles_still_on(driver):
“”“Check if toggles are still in the ON state.

```
Returns:
    True if both toggles are ON, False if any reset
"""
toggles = [
    "Show Closed Jobs",
    "Show Jobs with Scheduling Conflicts"
]

for toggle_name in toggles:
    try:
        _, is_checked = find_toggle_element(driver, toggle_name)
        if not is_checked:
            logger.warning(f"   Toggle reset detected: {toggle_name}")
            return False
    except NoSuchElementException:
        pass  # Toggle might not exist on this portal version

return True
```

# ============================================================

# GRID SCRAPING

# ============================================================

def find_job_grid(driver):
“”“Locate the main job grid/table element.

```
Returns:
    WebElement for the grid container
"""
# Multiple locator strategies for the grid
locators = [
    # Standard table
    (By.CSS_SELECTOR, "table.job-grid, table.data-grid, table.extra-duty-grid"),
    (By.TAG_NAME, "table"),
    # Div-based grid (React/Angular)
    (By.CSS_SELECTOR, "div[role='grid']"),
    (By.CSS_SELECTOR, "div.ag-body-viewport"),  # AG Grid
    (By.CSS_SELECTOR, "div[class*='grid'][class*='body']"),
    # By header content
    (By.XPATH, "//th[contains(text(), 'Job #')]//ancestor::table"),
    (By.XPATH, "//*[contains(text(), 'Job #')]//ancestor::*[contains(@class, 'grid') or contains(@role, 'grid')]"),
]

for by, selector in locators:
    try:
        elements = driver.find_elements(by, selector)
        for element in elements:
            # Verify it looks like a data grid (has multiple rows)
            rows = element.find_elements(By.CSS_SELECTOR, "tr, div[role='row']")
            if len(rows) >= 2:  # Header + at least one data row
                logger.debug(f"   Found grid with {len(rows)} rows using: {selector}")
                return element
    except Exception:
        continue

raise NoSuchElementException("Could not find job grid")
```

def wait_for_grid_refresh(driver, timeout=None):
“”“Wait for the grid to finish loading/refreshing.

```
Args:
    driver: WebDriver instance
    timeout: Max seconds to wait

Returns:
    True when grid appears stable
"""
timeout = timeout or CONFIG["element_wait_timeout"]

logger.debug("   Waiting for grid refresh...")

# Wait for loading indicators to disappear
loading_selectors = [
    "div.loading",
    "div.spinner",
    "*[class*='loading']",
    "*[class*='spinner']",
    "div[role='progressbar']"
]

for selector in loading_selectors:
    try:
        WebDriverWait(driver, 2).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
    except TimeoutException:
        pass  # Loading indicator not found or already gone

# Wait for grid to be present and stable
time.sleep(CONFIG["grid_refresh_wait"])

return True
```

def extract_grid_rows(driver):
“”“Extract all data rows from the job grid.

```
Returns:
    List of dictionaries, one per job
"""
logger.info("📋 Scraping grid rows...")

def action():
    grid = find_job_grid(driver)
    
    # Get all rows
    rows = grid.find_elements(By.CSS_SELECTOR, "tr, div[role='row']")
    
    if not rows:
        logger.warning("   No rows found in grid")
        return []
    
    # Skip header row(s)
    data_rows = []
    for row in rows:
        cells = row.find_elements(By.CSS_SELECTOR, "td, div[role='cell'], div[role='gridcell']")
        if cells and len(cells) >= len(CONFIG["csv_columns"]) - 1:
            cell_texts = [cell.text.strip() for cell in cells]
            data_rows.append(cell_texts)
    
    logger.debug(f"   Found {len(data_rows)} data rows")
    
    # Map to column names
    jobs = []
    columns = CONFIG["csv_columns"]
    
    for row_data in data_rows:
        job = {}
        for i, col_name in enumerate(columns):
            if i < len(row_data):
                job[col_name] = row_data[i]
            else:
                job[col_name] = ""
        
        # Skip rows that look like headers or are empty
        if job.get("Job #", "").lower() in ["job #", "job", ""] or not job.get("Job #"):
            continue
        
        jobs.append(job)
    
    return jobs

return retry_on_stale(action)
```

# ============================================================

# CSV OUTPUT

# ============================================================

def save_to_csv(jobs, output_path):
“”“Save job data to CSV file.

```
Args:
    jobs: List of job dictionaries
    output_path: Full path to CSV file

Returns:
    Path to saved file
"""
output_path = Path(output_path)
output_path.parent.mkdir(parents=True, exist_ok=True)

columns = CONFIG["csv_columns"]

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(jobs)

logger.info(f"   💾 Saved: {output_path.name} ({len(jobs)} rows)")
return output_path
```

# ============================================================

# MAIN SCRAPING FLOW

# ============================================================

def scrape_date_window(driver, start_date, end_date):
“”“Scrape jobs for a single date window.

```
Args:
    driver: WebDriver instance
    start_date: Start date as MM/DD/YYYY
    end_date: End date as MM/DD/YYYY

Returns:
    List of job dictionaries, or empty list on failure
"""
logger.info(f"\n{'='*60}")
logger.info(f"📆 Scraping window: {start_date} to {end_date}")
logger.info(f"{'='*60}")

try:
    # Step 1: Verify page is ready
    if not verify_page_state(driver):
        logger.warning("⚠️  Page may not be fully loaded")
    
    # Step 2: Set date range
    set_date_range(driver, start_date, end_date)
    
    # Step 3: Set toggles
    set_all_toggles(driver)
    
    # Step 4: Wait for grid refresh
    wait_for_grid_refresh(driver)
    
    # Step 5: Verify toggles didn't reset (common portal bug)
    if not verify_toggles_still_on(driver):
        logger.info("   Re-applying toggles after grid refresh...")
        set_all_toggles(driver)
        wait_for_grid_refresh(driver)
    
    # Step 6: Extract grid data
    jobs = extract_grid_rows(driver)
    
    logger.info(f"   ✓ Extracted {len(jobs)} jobs")
    return jobs

except TimeoutException as e:
    logger.error(f"❌ Timeout during scrape: {e}")
    return []
except NoSuchElementException as e:
    logger.error(f"❌ Element not found: {e}")
    return []
except Exception as e:
    logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
    return []
```

def run_scraper(mode=“q4”, specific_month=None):
“”“Main entry point for the scraper.

```
Args:
    mode: One of 'q1', 'q2', 'q3', 'q4', 'full_year', 'monthly', 'month'
    specific_month: If mode='month', which month (1-12)

Returns:
    List of paths to saved CSV files
"""
global logger
logger = setup_logging()

logger.info("=" * 60)
logger.info("VCS EXTRA DUTY SCRAPER")
logger.info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"Mode: {mode}")
logger.info("=" * 60)

# Determine date windows
if mode == "month" and specific_month:
    windows = [DATE_WINDOWS["monthly"][specific_month - 1]]
elif mode in DATE_WINDOWS:
    windows = DATE_WINDOWS[mode]
else:
    logger.error(f"Invalid mode: {mode}")
    logger.info("Valid modes: q1, q2, q3, q4, full_year, monthly, month")
    return []

logger.info(f"Date windows to process: {len(windows)}")

# Connect to Chrome
try:
    driver = connect_to_chrome()
except WebDriverException:
    return []

# Process each date window
saved_files = []
total_jobs = 0

for start_date, end_date in windows:
    try:
        # Scrape this window
        jobs = scrape_date_window(driver, start_date, end_date)
        
        if jobs:
            # Generate filename
            suffix = get_suffix_from_dates(start_date, end_date)
            filename = get_output_filename(suffix=suffix)
            output_path = Path(CONFIG["output_folder"]) / filename
            
            # Save to CSV
            saved_path = save_to_csv(jobs, output_path)
            saved_files.append(saved_path)
            total_jobs += len(jobs)
        else:
            logger.warning(f"   No jobs found for {start_date} to {end_date}")
    
    except Exception as e:
        logger.error(f"❌ Failed window {start_date}-{end_date}: {e}")
        continue

# Summary
logger.info("\n" + "=" * 60)
logger.info("SCRAPER COMPLETE")
logger.info("=" * 60)
logger.info(f"Windows processed: {len(windows)}")
logger.info(f"Files saved: {len(saved_files)}")
logger.info(f"Total jobs: {total_jobs}")

if saved_files:
    logger.info("\nSaved files:")
    for f in saved_files:
        logger.info(f"   • {f.name}")

logger.info("\n📌 Next step: Run traffic_jobs_postprocessor.py")

return saved_files
```

# ============================================================

# COMMAND LINE INTERFACE

# ============================================================

# def print_usage():
“”“Print usage instructions.”””
print(”””
VCS Extra Duty Scraper - Usage

BEFORE RUNNING:

1. Start Chrome with remote debugging:
   chrome.exe –remote-debugging-port=9222 –user-data-dir=“C:\ChromeDebug”
1. Log into VCS portal manually
1. Navigate to the Extra Duty Signup page

COMMANDS:
python vcs_extra_duty_scrape.py                    # Default: Q4 2025
python vcs_extra_duty_scrape.py –mode q1          # Q1 2025 only
python vcs_extra_duty_scrape.py –mode q2          # Q2 2025 only
python vcs_extra_duty_scrape.py –mode q3          # Q3 2025 only
python vcs_extra_duty_scrape.py –mode q4          # Q4 2025 only
python vcs_extra_duty_scrape.py –mode full_year   # All 4 quarters
python vcs_extra_duty_scrape.py –mode monthly     # All 12 months
python vcs_extra_duty_scrape.py –mode month –month 11  # November only
python vcs_extra_duty_scrape.py –help             # Show this message

OUTPUT:
CSVs saved to: {output_folder}
Logs saved to: {log_folder}
“””.format(
output_folder=CONFIG[“output_folder”],
log_folder=CONFIG[“log_folder”]
))

def main():
“”“Parse command line arguments and run scraper.”””
args = sys.argv[1:]

```
# Defaults
mode = "q4"
specific_month = None

# Parse arguments
i = 0
while i < len(args):
    arg = args[i].lower()
    
    if arg in ["--help", "-h"]:
        print_usage()
        return
    elif arg == "--mode":
        if i + 1 < len(args):
            mode = args[i + 1].lower()
            i += 1
    elif arg == "--month":
        if i + 1 < len(args):
            try:
                specific_month = int(args[i + 1])
                mode = "month"
                i += 1
            except ValueError:
                print(f"Invalid month: {args[i + 1]}")
                return
    i += 1

# Validate
valid_modes = ["q1", "q2", "q3", "q4", "full_year", "monthly", "month"]
if mode not in valid_modes:
    print(f"Invalid mode: {mode}")
    print(f"Valid modes: {', '.join(valid_modes)}")
    return

if mode == "month" and (not specific_month or specific_month < 1 or specific_month > 12):
    print("Month mode requires --month 1-12")
    return

# Run
run_scraper(mode=mode, specific_month=specific_month)
```

if **name** == “**main**”:
main()
