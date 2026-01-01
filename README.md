# VCS Extra Duty Scraper

Python-based ETL pipeline for extracting extra duty job data from VCS Software portal.

## Purpose

- Scrape extra duty job assignments from VCS portal
- Process manual data entry when scraping unavailable
- Generate Excel reports with awarded/unawarded job breakdown
- Calculate hours, award rates, and monthly summaries

## Quick Start

### First Time Setup

1. **Install dependencies:**
   ```batch
   setup.bat
   ```

2. **Edit config.json:**
   - Update `my_name` under `postprocessor`
   - Verify `target_year` is correct

### Running the Scraper

1. **Start Chrome in debug mode:**
   ```batch
   run_scraper.bat
   ```

2. **Log into VCS portal** in the Chrome window that opens

3. **Press any key** to start scraping

4. **Run post-processor:**
   ```batch
   python scripts\traffic_jobs_postprocessor.py
   ```

5. **Review output:**
   - Open `output/TrafficJobs_2025_Master.xlsx`

## Manual Data Entry (Fallback)

When scraping fails or for historical data:

### Dataset 1: Your Signups

1. Copy job data from VCS portal (Job #, Description, Date, Times, Customer, Address, Status)
2. Open `TEMPLATE_dataset1_my_signups.txt`
3. Update REPORT_DATE and MY_NAME
4. Paste data after `---DATA_START---`
5. Save as `data/dataset1/dataset1_YYYY-MM-DD.txt`

**Format:** 7 lines per job (no blank lines between records)

### Dataset 2: Assigned Workers (for unawarded signups)

1. Go to VCS portal for the date you signed up but weren't selected
2. Copy the list of workers who WERE assigned
3. Open `TEMPLATE_dataset2_assigned_workers.txt`
4. Update SIGNUP_DATE and MY_NAME
5. Paste data after `---DATA_START---`
6. Save as `data/dataset2/dataset2_YYYY-MM-DD.txt`

**Format:** 6 lines per worker (no blank lines between records)

## Output

### Excel Sheets

- **All Jobs** - Complete dataset
- **Awarded** - Status = Invoiced
- **Not Awarded** - Status = Requested
- **Monthly Summary** - Award rate, hours, counts by month

### File Locations

| Type | Location |
|------|----------|
| Raw CSVs | `data/raw_scraper_csv/` |
| Manual entry (Dataset 1) | `data/dataset1/` |
| Manual entry (Dataset 2) | `data/dataset2/` |
| Excel output | `output/` |
| Logs | `logs/` |

## Scraper Modes

```batch
# Default: Q4 2025
python scripts\vcs_extra_duty_scrape.py

# Specific quarter
python scripts\vcs_extra_duty_scrape.py --mode q1
python scripts\vcs_extra_duty_scrape.py --mode q2
python scripts\vcs_extra_duty_scrape.py --mode q3
python scripts\vcs_extra_duty_scrape.py --mode q4

# Full year (4 CSVs, one per quarter)
python scripts\vcs_extra_duty_scrape.py --mode full_year

# All 12 months (12 CSVs)
python scripts\vcs_extra_duty_scrape.py --mode monthly

# Single month
python scripts\vcs_extra_duty_scrape.py --mode month --month 11
```

## Troubleshooting

See `VCS Extra Duty Scraper - Quick Reference.txt` for detailed troubleshooting.

### Common Issues

**"Failed to connect to Chrome"**
- Close all Chrome windows
- Run `run_scraper.bat` again

**"Could not find job grid"**
- Manually navigate to Extra Duty Signup page in Chrome
- Wait for page to fully load
- Re-run scraper

**Empty CSV output**
- Check date range has jobs
- Review log file in `logs/` folder
- Verify toggles are set correctly in UI

## Requirements

- Windows 10/11
- Python 3.8+
- Google Chrome (latest)
- Packages: selenium, pandas, openpyxl

## Typical Workflow

1. **Weekly:** Run scraper for current quarter
2. **Monthly:** Add Dataset 2 files for unawarded signups
3. **Run post-processor** to regenerate master Excel
4. **Review** award rates and trends in Excel

## Files

| File | Purpose |
|------|---------|
| `scripts/vcs_extra_duty_scrape.py` | Main scraper script |
| `scripts/traffic_jobs_postprocessor.py` | Data processing and Excel generation |
| `config.json` | Configuration (paths, settings) |
| `scripts/run_scraper.bat` | Launch script with Chrome debug mode |
| `setup.bat` | First-time installation |
| `requirements.txt` | Python dependencies |

## Repository

**GitHub**: [https://github.com/racmac57/vcs_extra_duty_scraper](https://github.com/racmac57/vcs_extra_duty_scraper)

## Contributing

This is a personal project for internal use at the Hackensack Police Department. For questions or suggestions, please open an issue on GitHub.

## License

Internal use only - Hackensack Police Department

## Author

R. A. Carucci  
Principal Analyst, Hackensack Police Department
