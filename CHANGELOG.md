# CHANGELOG – VCS Extra Duty Scraper

All notable changes to this project are documented here.

## [1.0.0] - 2025-12-31

### Added
- **Configuration Management**
  - Centralized configuration in `config.json` with relative paths for portability
  - Both scraper and post-processor now load settings from `config.json`
  - Support for different environments without hardcoded paths

- **Project Structure**
  - Created `requirements.txt` with pinned dependencies (selenium, pandas, openpyxl)
  - Added `.gitignore` to exclude data files, logs, and IDE files
  - Created `setup.bat` for one-time installation and folder setup
  - Added `PROJECT_STRUCTURE.md` documenting current and planned structure

- **Post-Processor Enhancements**
  - Automatic folder creation for all required directories
  - Enhanced output summary with award rates, hours, and date ranges
  - Improved error handling and user feedback

- **Documentation**
  - Comprehensive `README.md` with quick start guide
  - Updated `CHANGELOG.md` for version tracking
  - `PROJECT_STRUCTURE.md` for architecture documentation

### Changed
- **File Organization**
  - Renamed `traffic_jobs_postprocessor.py` from `.txt` extension
  - Consolidated duplicate scraper files
  - Standardized file naming conventions

- **Configuration**
  - Migrated from hardcoded paths to relative paths in `config.json`
  - All paths now use `./data/...` format for portability

### Fixed
- Import statements in post-processor (previously malformed single-line imports)
- Main function syntax in post-processor
- Configuration loading to handle missing config files gracefully

## [0.1.0] - 2025-12-03 – Initial Selenium Version

### Added
- Selenium-based scraper that:
  - Attaches to a running Chrome instance via remote debugging
  - Navigates (only if needed) to `https://app10.vcssoftware.com/extra-duty-signup`
  - Waits for the Extra Duty job grid to load
  - Extracts all visible rows and exports them to CSV

### Key Features

1. **Conditional Navigation**
   - Before calling `driver.get()`, the script checks `driver.current_url`
   - Only navigates to the Extra Duty URL if not already on that page
   - Prevents toggles like "Show Closed Jobs" and "Show Jobs with Scheduling Conflicts" from flipping unintentionally

2. **Robust Grid Locators**
   - Implemented multiple locator strategies for the job grid:
     - Standard `<table>` element
     - `<div role="grid">` (common in JavaScript UI frameworks)
     - Elements with class names containing "grid" or "table"
     - Fallback: find the "Job #" header cell and move up to the parent container
   - Script logs which strategy succeeds and basic element details

3. **Row and Cell Extraction**
   - Uses `.find_elements()` to get:
     - Rows (`<tr>` or elements with `role="row"`)
     - Cells (`<td>` or elements with `role="cell"`)
   - Extracts text from each cell in order and maps to:
     - Job #, Description, Date, Times, Customer, Address, Immediate Award, Status
   - Includes debug output:
     - First row's HTML structure (truncated)
     - First few parsed rows

4. **Date Range Helper**
   - Added `set_date_range(start_date, end_date)`:
     - Locates Start/End Date inputs by placeholder or aria-label
     - Clears existing values, types new dates, and sends TAB to trigger change events
   - Hook is present in the main flow; can be toggled on to automate full-year pulls

5. **Error Handling and Debugging**
   - If the grid cannot be found:
     - Saves full page source to `page_source_debug.html` for inspection
   - Skips malformed rows with too few columns
   - Prints any row-level parsing issues without crashing the script

6. **Post-Processor**
   - Processes scraped CSVs and manual text templates
   - Generates Excel workbooks with multiple sheets:
     - All Jobs, Awarded, Not Awarded, Monthly Summary
   - Calculates award rates, hours, and statistics

## Future Changes (Planned)

- Add monthly/quarterly looping to handle date range limits
- Add CLI arguments or config file for:
  - Date range
  - Output filename
  - Employee selection
- Optional: insert records directly into a database instead of CSV only
- Dataset 2 scraper for automated "Assigned Workers" page scraping
- Database backend for historical queries
- Power BI direct integration
- Multi-user support
