# Summary – VCS Extra Duty Scraper

## What This Project Does

A complete ETL pipeline for extracting and processing extra duty job assignment data from the VCS Software portal. The system consists of:

1. **Web Scraper** - Selenium-based automation that connects to an already-authenticated Chrome session and extracts job grid data
2. **Post-Processor** - Data processing engine that combines scraped data with manual entries and generates comprehensive Excel reports
3. **Manual Data Entry** - Fallback templates for capturing data when scraping is unavailable

## Why It Was Needed

- The VCS grid is rendered by a modern web app, so simple `pandas.read_html()` does not work
- The job list is not a basic static `<table>`; it needs a real browser (Selenium) to:
  - Render the page
  - Apply date filters
  - Read the grid structure
- Manual tracking of extra duty assignments was time-consuming and error-prone
- Need for automated reporting on award rates, hours worked, and monthly summaries

## How It Works

### Scraper Flow

1. Start Chrome with remote debugging (`run_scraper.bat`)
2. Log in and manually go to the Extra Duty grid with the desired date range
3. Run the Python script:
   - Attaches to Chrome via remote debugging
   - Locates the grid using resilient locators (table/div/role-based)
   - Iterates through each row and cell
   - Writes timestamped CSV files with the core job fields

### Post-Processor Flow

1. Reads all scraped CSV files from `data/raw_scraper_csv/`
2. Reads manual entry files from `data/dataset1/` and `data/dataset2/`
3. Normalizes dates, times, and formats
4. Deduplicates records based on Job #, Date, and Customer
5. Cross-references assigned workers to identify jobs you didn't get
6. Generates Excel workbook with multiple analysis sheets

## Current Output

### CSV Files (Scraper)
- Timestamped files: `vcs_extra_duty_jobs_2025Q4_20251203_1430.csv`
- Columns: Job #, Description, Date, Times, Customer, Address, Immediate Award, Status

### Excel Workbook (Post-Processor)
- **All Jobs** - Complete dataset with all signups
- **Awarded** - Jobs with Status = Invoiced (green highlight)
- **Not Awarded** - Jobs with Status = Requested (orange if someone else got it)
- **Other Assignments** - Dataset 2 data showing who was assigned on specific dates
- **Monthly Summary** - Award rates, hours, counts by month
- **Instructions** - Documentation sheet

## Use Cases

- **Operational Analysis**: Track signup patterns and award rates
- **Payroll Auditing**: Calculate hours worked and verify assignments
- **Performance Tracking**: Monitor award rates over time
- **Data Integration**: CSV output can be loaded into Power Query/Power BI for dashboards
- **Historical Analysis**: Join with other CAD/RMS data for comprehensive reporting

## Technology Stack

- **Python 3.8+** - Core language
- **Selenium** - Web scraping and browser automation
- **Pandas** - Data processing and manipulation
- **OpenPyXL** - Excel workbook generation and formatting
- **JSON** - Configuration management

## Repository

**GitHub**: [https://github.com/racmac57/vcs_extra_duty_scraper](https://github.com/racmac57/vcs_extra_duty_scraper)

## Author

R. A. Carucci  
Principal Analyst, Hackensack Police Department
