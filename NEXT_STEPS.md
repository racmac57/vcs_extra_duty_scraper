# Next Steps – VCS Extra Duty Scraper

## 1. Validate Current Extract

- Run the script for 10/01/2025–12/31/2025.
- Open the CSV and spot-check:
  - Row count vs. what the UI shows.
  - Column mapping (Job #, Description, Date, Times, etc.).
  - Check a few jobs with different statuses (Open/Closed).

## 2. Enable Full-Year Extraction

- In `vcs_extra_duty_scrape.py`, enable the date helper:

```
set_date_range("01/01/2025", "12/31/2025")
```

- Re-run the script and confirm:
  - All 2025 jobs appear.
  - No obvious gaps or duplicates.

If the UI limits max date range, plan to:
- Loop over smaller windows (e.g., monthly or quarterly) and append to a combined CSV.

## 3. Integrate with Your ETL

- Create a Power Query or Python step that:
  - Imports `vcs_extra_duty_jobs.csv`.
  - Normalizes date/time formats.
  - Cleans up customer/address text as needed.
- Join with:
  - CAD / RMS data for cross-checking assignments.
  - Payroll/extra-duty payment records for audit reports.

## 4. Add Configuration and Automation

- Replace hard-coded values with configurable options:
  - Date range (start/end).
  - Output file name/path.
  - Flags for including closed jobs or conflicts.
- Options:
  - Simple `.ini`/`.json` config file.
  - Command-line arguments (argparse).

- Add a simple batch file or PowerShell script to:
  - Start Chrome in debug mode.
  - Run the Python script.
  - Optionally move the CSV into your monthly reporting folder.

## 5. Future Enhancements

- Pagination:
  - Detect and click "next page" if the grid supports multiple pages.
  - Collect all pages into one dataset.

- Multi-employee support:
  - Switch the "Employee" dropdown and pull jobs for multiple profiles.
  - Add an `Employee` column in the CSV.

- Database Load:
  - Instead of (or in addition to) CSV, insert data into a local SQL database for:
    - Historical archiving.
    - Faster joins and reporting.

Each of these steps can be implemented incrementally; the current script already provides a working base to iterate on.
