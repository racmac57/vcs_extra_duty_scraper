# Cursor AI Orchestration Prompt for VCS Extra Duty Scraper

Copy this entire prompt into Cursor AI to set up and fix the project:

***

```markdown
# PROJECT: VCS Extra Duty Scraper - Law Enforcement ETL Pipeline

## CONTEXT
You are maintaining a Python-based web scraping and data processing system for the Hackensack Police Department. This tool extracts extra duty job assignments from the VCS Software portal and processes them into Excel reports for operational analysis and payroll audit.

**User Profile:**
- Police analyst with 20+ years experience
- Works with CAD/RMS data, Power BI, ArcGIS Pro
- Needs production-ready code with minimal maintenance
- Prefers clear, concise documentation

**Current Status:**
- Scraper is functional but has file naming/organization issues
- Post-processor exists but needs fixes
- No dependency management or version control setup
- Hardcoded paths prevent portability

---

## IMMEDIATE TASKS

### 1. Fix File Naming Issues

**Problem:** Files have wrong names/extensions
- `vcs_extra_duty_scrape.py.py` should be `vcs_extra_duty_scrape.py`
- `vcs_extra_duty_scrape.py` (7KB version) is duplicate - DELETE this
- `2025-12-03-10-20-00.txt` should be `traffic_jobs_postprocessor.py`

**Action:**
```bash
# Delete the smaller duplicate scraper
rm vcs_extra_duty_scrape.py

# Rename the full-featured scraper
mv vcs_extra_duty_scrape.py.py vcs_extra_duty_scrape.py

# Rename the post-processor
mv 2025-12-03-10-20-00.txt traffic_jobs_postprocessor.py
```

---

### 2. Create requirements.txt

**File: `requirements.txt`**
```txt
# VCS Extra Duty Scraper Dependencies
# Python 3.8+

selenium==4.16.0
pandas==2.1.4
openpyxl==3.1.2
```

---

### 3. Make Scripts Load config.json

**Current Problem:** Both scripts have hardcoded CONFIG dicts instead of loading from `config.json`

**Add this to TOP of `vcs_extra_duty_scrape.py` (after imports, before CONFIG):**
```python
import json
from pathlib import Path

# Load configuration
CONFIG_PATH = Path(__file__).parent / 'config.json'
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        CONFIG = config_data.get('scraper', {})
        # Merge paths from config
        CONFIG.update(config_data.get('paths', {}))
        CONFIG['target_year'] = config_data.get('postprocessor', {}).get('target_year', 2025)
else:
    raise FileNotFoundError(f"config.json not found at {CONFIG_PATH}")
```

**Add this to TOP of `traffic_jobs_postprocessor.py` (after imports, before CONFIG):**
```python
import json
from pathlib import Path

# Load configuration
CONFIG_PATH = Path(__file__).parent / 'config.json'
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r') as f:
        config_data = json.load(f)
        CONFIG = {
            'my_name': config_data['postprocessor']['my_name'],
            'target_year': config_data['postprocessor']['target_year'],
            'output_filename': config_data['postprocessor']['output_filename'],
            'dedup_keys': config_data['postprocessor']['dedup_keys'],
            'scraped_csv_folder': config_data['paths']['output_folder'],
            'scraped_csv_pattern': config_data['scraper']['csv_pattern'],
            'dataset1_folder': config_data['paths']['dataset1_folder'],
            'dataset2_folder': config_data['paths']['dataset2_folder'],
            'output_folder': config_data['paths']['output_excel_folder']
        }
else:
    raise FileNotFoundError(f"config.json not found at {CONFIG_PATH}")
```

---

### 4. Add Folder Auto-Creation to Post-Processor

**Add this function after imports in `traffic_jobs_postprocessor.py`:**
```python
def ensure_folders_exist(config):
    """Create all required folders if they don't exist."""
    folders = [
        config['scraped_csv_folder'],
        config['dataset1_folder'],
        config['dataset2_folder'],
        config['output_folder']
    ]
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Folder ready: {Path(folder).name}")
```

**Add this call at the start of main processing (after CONFIG is loaded):**
```python
print("📁 Setting up folders...")
ensure_folders_exist(CONFIG)
```

---

### 5. Add Output Summary to Post-Processor

**Add this at the END of the main processing (before final print):**
```python
# Print summary
print("\n" + "="*60)
print("📊 PROCESSING SUMMARY")
print("="*60)
if not my_signups.empty:
    print(f"Total signups: {len(my_signups)}")
    print(f"Awarded (Invoiced): {my_signups['IsInvoiced'].sum()}")
    print(f"Not awarded (Requested): {my_signups['IsRequested'].sum()}")
    if len(my_signups) > 0:
        award_rate = (my_signups['IsInvoiced'].sum() / len(my_signups) * 100)
        print(f"Award rate: {award_rate:.1f}%")
    total_hours = my_signups[my_signups['IsInvoiced']]['Hours'].sum()
    print(f"Total hours (awarded): {total_hours:.1f}")
    print(f"Date range: {my_signups['Date'].min()} to {my_signups['Date'].max()}")
print(f"\n✓ Master Excel: {output_file}")
print(f"  Location: {CONFIG['output_folder']}")
```

---

### 6. Create .gitignore

**File: `.gitignore`**
```txt
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Data files (don't commit raw data)
*.csv
*.xlsx
*.xls

# Logs
*.log
logs/

# Chrome debugging
ChromeDebug/

# Output folders
data/raw_scraper_csv/*.csv
data/dataset1/*.txt
data/dataset2/*.txt
output/*.xlsx

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Keep folder structure but ignore contents
data/raw_scraper_csv/.gitkeep
data/dataset1/.gitkeep
data/dataset2/.gitkeep
output/.gitkeep
logs/.gitkeep

# Config - UNCOMMENT if it contains credentials
# config.json
```

---

### 7. Update config.json for Portability

**Replace hardcoded paths with relative paths:**

**File: `config.json`**
```json
{
  "paths": {
    "output_folder": "./data/raw_scraper_csv",
    "dataset1_folder": "./data/dataset1",
    "dataset2_folder": "./data/dataset2",
    "log_folder": "./logs",
    "output_excel_folder": "./output"
  },
  "scraper": {
    "chrome_debugger_address": "127.0.0.1:9222",
    "portal_url": "https://app10.vcssoftware.com/extra-duty-signup",
    "page_load_timeout": 30,
    "element_wait_timeout": 15,
    "grid_refresh_wait": 3,
    "action_delay": 0.5,
    "max_retries": 3,
    "retry_delay": 2,
    "csv_pattern": "vcs_extra_duty_jobs*.csv",
    "csv_columns": [
      "Job #",
      "Description",
      "Date",
      "Times",
      "Customer",
      "Address",
      "Immediate Award",
      "Status"
    ]
  },
  "postprocessor": {
    "my_name": "Carucci, Robert",
    "target_year": 2025,
    "output_filename": "TrafficJobs_2025_Master.xlsx",
    "dedup_keys": ["Job #"]
  }
}
```

---

### 8. Create Installation Script

**File: `setup.bat`**
```batch
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
```

---

### 9. Update README.md

**Replace existing README with this improved version:**

**File: `README.md`**
```markdown
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
   python traffic_jobs_postprocessor.py
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
python vcs_extra_duty_scrape.py

# Specific quarter
python vcs_extra_duty_scrape.py --mode q1
python vcs_extra_duty_scrape.py --mode q2
python vcs_extra_duty_scrape.py --mode q3
python vcs_extra_duty_scrape.py --mode q4

# Full year (4 CSVs, one per quarter)
python vcs_extra_duty_scrape.py --mode full_year

# All 12 months (12 CSVs)
python vcs_extra_duty_scrape.py --mode monthly

# Single month
python vcs_extra_duty_scrape.py --mode month --month 11
```

## Troubleshooting

See `VCS-Extra-Duty-Scraper-Quick-Reference.txt` for detailed troubleshooting.

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
| `vcs_extra_duty_scrape.py` | Main scraper script |
| `traffic_jobs_postprocessor.py` | Data processing and Excel generation |
| `config.json` | Configuration (paths, settings) |
| `run_scraper.bat` | Launch script with Chrome debug mode |
| `setup.bat` | First-time installation |
| `requirements.txt` | Python dependencies |

## Author

R. A. Carucci  
Principal Analyst, Hackensack Police Department
```

---

### 10. Create Project Structure

**File: `PROJECT_STRUCTURE.md`**
```markdown
# VCS Extra Duty Scraper - Directory Structure

## Current Structure

```
Extra_Duty/
│
├── scripts/                           # Main code folder
│   ├── vcs_extra_duty_scrape.py      # Selenium scraper (main)
│   ├── traffic_jobs_postprocessor.py # Data processor
│   ├── run_scraper.bat               # Launch script
│   ├── setup.bat                     # Installation script
│   ├── config.json                   # Configuration
│   ├── requirements.txt              # Python dependencies
│   ├── .gitignore                    # Git exclusions
│   │
│   ├── README.md                     # Main documentation
│   ├── CHANGELOG.md                  # Version history
│   ├── SUMMARY.md                    # Project summary
│   ├── NEXT_STEPS.md                 # Roadmap
│   ├── VCS-Extra-Duty-Scraper-Quick-Reference.txt  # User guide
│   │
│   ├── TEMPLATE_dataset1_my_signups.txt         # Manual entry template
│   ├── TEMPLATE_dataset2_assigned_workers.txt   # Manual entry template
│   │
│   └── ChatGPT-*.md                  # AI prompts (archive)
│
├── data/                             # Data storage
│   ├── raw_scraper_csv/             # Scraped CSVs
│   │   └── .gitkeep
│   ├── dataset1/                    # Manual signups
│   │   └── .gitkeep
│   └── dataset2/                    # Manual assigned workers
│       └── .gitkeep
│
├── output/                           # Excel reports
│   ├── TrafficJobs_2025_Master.xlsx
│   └── .gitkeep
│
└── logs/                             # Execution logs
    ├── scraper_YYYYMMDD_HHMMSS.log
    └── .gitkeep
```

## Future Structure (Planned)

```
Extra_Duty/
│
├── scripts/                          # Core code
│   ├── scrapers/                     # Scraper modules
│   │   ├── vcs_extra_duty_scrape.py
│   │   └── vcs_assigned_workers_scrape.py  # Future: Dataset 2 scraper
│   │
│   ├── processors/                   # Processing modules
│   │   ├── traffic_jobs_postprocessor.py
│   │   └── data_validator.py        # Future: Data quality checks
│   │
│   ├── utils/                        # Shared utilities
│   │   ├── config_loader.py
│   │   ├── date_parser.py
│   │   └── excel_styler.py
│   │
│   └── tests/                        # Unit tests
│       ├── test_scraper.py
│       └── test_postprocessor.py
│
├── data/                             # Data storage
│   ├── raw/                          # Raw scraped data
│   │   ├── csv/
│   │   └── json/                     # Future: JSON output option
│   │
│   ├── manual/                       # Manual entry
│   │   ├── signups/
│   │   └── assigned/
│   │
│   └── archive/                      # Historical data
│       ├── 2025/
│       └── 2024/
│
├── output/                           # Reports
│   ├── excel/
│   │   └── TrafficJobs_2025_Master.xlsx
│   ├── reports/                      # Future: PDF/HTML reports
│   └── dashboards/                   # Future: Power BI files
│
├── logs/                             # Logging
│   ├── scraper/
│   ├── processor/
│   └── errors/
│
├── config/                           # Configuration files
│   ├── config.json
│   ├── config.dev.json               # Future: Dev environment
│   └── config.prod.json              # Future: Production
│
├── docs/                             # Documentation
│   ├── README.md
│   ├── USER_GUIDE.md
│   ├── API.md                        # Future: If APIs added
│   └── TROUBLESHOOTING.md
│
└── templates/                        # Templates
    ├── dataset_templates/
    │   ├── TEMPLATE_dataset1_my_signups.txt
    │   └── TEMPLATE_dataset2_assigned_workers.txt
    └── report_templates/             # Future: Custom Excel templates
```

## Migration Path

### Phase 1: Current → Organized (Immediate)
- Move scrapers to `scripts/scrapers/`
- Move processors to `scripts/processors/`
- Move templates to `templates/dataset_templates/`
- Update all path references in config.json

### Phase 2: Modularization (Next Month)
- Extract utility functions to `scripts/utils/`
- Create config loader module
- Add data validation module

### Phase 3: Testing & CI (Next Quarter)
- Add unit tests
- Set up automated testing
- Create test data fixtures

### Phase 4: Advanced Features (Long-term)
- Database backend
- API endpoints
- Power BI direct integration
- Multi-user support
```

---

## DIRECTORY SETUP COMMANDS

Run these commands to create the proper structure:

```batch
@echo off
REM Create current structure

cd /d "C:\Users\carucci_r\OneDrive - City of Hackensack\RAC\Extra_Duty"

REM Create main folders
mkdir scripts
mkdir data
mkdir data\raw_scraper_csv
mkdir data\dataset1
mkdir data\dataset2
mkdir output
mkdir logs

REM Move files to scripts folder
move *.py scripts\
move *.bat scripts\
move *.json scripts\
move *.md scripts\
move *.txt scripts\

REM Create .gitkeep files
type nul > data\raw_scraper_csv\.gitkeep
type nul > data\dataset1\.gitkeep
type nul > data\dataset2\.gitkeep
type nul > output\.gitkeep
type nul > logs\.gitkeep

echo Folder structure created!
```

---

## VALIDATION CHECKLIST

After making all changes, verify:

- [ ] Only ONE `vcs_extra_duty_scrape.py` exists
- [ ] `traffic_jobs_postprocessor.py` has `.py` extension (not `.txt`)
- [ ] `requirements.txt` exists and has 3 packages
- [ ] `.gitignore` exists
- [ ] `config.json` uses relative paths (`./data/...`)
- [ ] Both scripts load config from `config.json`
- [ ] `setup.bat` exists and is executable
- [ ] Folder structure matches PROJECT_STRUCTURE.md
- [ ] README.md documents manual data entry
- [ ] All templates are in root or dedicated folder

---

## TESTING PROCEDURE

After fixes are complete:

1. **Run setup:**
   ```batch
   setup.bat
   ```

2. **Test scraper** (dry run):
   ```batch
   run_scraper.bat
   ```
   - Log in to VCS
   - Run for Q4 2025
   - Verify CSV created in `data/raw_scraper_csv/`

3. **Test post-processor:**
   ```batch
   python scripts\traffic_jobs_postprocessor.py
   ```
   - Verify Excel created in `output/`
   - Check all 4 sheets exist
   - Verify monthly summary calculations

4. **Test manual entry:**
   - Copy template file
   - Paste sample data
   - Save to `data/dataset1/`
   - Re-run post-processor
   - Verify data appears in Excel

---

## CRITICAL NOTES FOR CURSOR AI

1. **DO NOT** modify the core scraping logic in `vcs_extra_duty_scrape.py` - it's working
2. **DO NOT** change the Excel styling in `traffic_jobs_postprocessor.py` - it's correct
3. **PRESERVE** all comments and docstrings - they're essential for maintenance
4. **USE** relative paths in config.json (NOT absolute paths)
5. **TEST** each change incrementally - don't make all changes at once
6. **KEEP** the ChatGPT-*.md files for reference (move to `docs/archive/` folder)

---

## COMPLETION CRITERIA

Project is ready for production when:

1. All files have correct names and locations
2. `setup.bat` runs without errors
3. Scraper → Post-processor → Excel pipeline works end-to-end
4. Manual data entry templates work correctly
5. README accurately documents all features
6. No hardcoded absolute paths remain
7. Git repository is initialized with proper .gitignore

---

## QUESTIONS TO ASK USER BEFORE STARTING

1. Do you want to keep the current absolute paths in config.json, or switch to relative paths?
2. Should the ChatGPT-*.md files be archived or deleted?
3. Do you want the folder structure reorganized now, or after testing?
4. What's your Git repository location (if using version control)?

---

END OF PROMPT
```

***

**Copy everything above (including the code blocks) into Cursor AI, then answer its questions before it starts making changes.**

[1](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/10459886/35982695-7a60-41c1-8424-c0df528dfbcb/image.jpg)
[2](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/04b05a0f-1f39-415d-bc40-0435f6391dfd/ChatGPT-Improve-my-prompt.md)
[3](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/15706bbe-9373-4afc-83cd-3a9dd7e2419a/CHANGELOG.md)
[4](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/516921f9-0a7e-4742-bf7b-210b7bd2204d/vcs_extra_duty_scrape.py.py)
[5](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/64c6588b-4358-40c1-92ac-e8b19a7b2d61/ChatGPT-Excel-data-cleanup.md)
[6](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/77cf1da3-7611-42b0-a0c2-e8ffbc7b6f9c/config.json)
[7](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/94a9c929-7736-4c95-a892-c58b44877e00/README.md)
[8](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/c76ed5e0-4f62-4fdd-b0d9-61cd8add20a8/SUMMARY.md)
[9](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/cf9d9f3f-5490-4749-85e4-b3f5d22c1ebc/run_scraper.bat)
[10](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/f0e1866e-5e74-4858-b5bf-2c19da21eaa1/vcs_extra_duty_scrape.py)
[11](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/641b413e-a17b-4a1f-9156-ba46627687ce/TEMPLATE_dataset1_my_signups.txt)
[12](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/800b86ca-e784-402f-9dea-72bb8a50a659/NEXT_STEPS.md)
[13](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/c5087550-2545-40aa-bdab-fcee233b63cc/TEMPLATE_dataset2_assigned_workers.txt)
[14](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/d8d0abf1-7f96-4877-9c07-a1a1bdb85de8/2025-12-03-10-20-00.txt)
[15](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/10459886/d8f5dfd6-02d8-48ff-9b62-f286a0aad214/VCS-Extra-Duty-Scraper-Quick-Reference.txt)