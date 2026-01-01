# VCS Extra Duty Scraper - Directory Structure

## Current Structure

```
Extra_Duty/
│
├── scripts/                           # Main code folder
│   ├── vcs_extra_duty_scrape.py      # Selenium scraper (main)
│   ├── traffic_jobs_postprocessor.py # Data processor
│   ├── run_scraper.bat               # Launch script
│   │
│   ├── config.json                   # Configuration
│   ├── requirements.txt              # Python dependencies
│   ├── .gitignore                    # Git exclusions
│   │
│   ├── README.md                     # Main documentation
│   ├── CHANGELOG.md                  # Version history
│   ├── SUMMARY.md                    # Project summary
│   ├── NEXT_STEPS.md                 # Roadmap
│   ├── VCS Extra Duty Scraper - Quick Reference.txt  # User guide
│   │
│   ├── TEMPLATE_dataset1_my_signups.txt         # Manual entry template
│   ├── TEMPLATE_dataset2_assigned_workers.txt   # Manual entry template
│   │
│   └── doc/                          # Documentation archive
│       └── ChatGPT-*.md              # AI prompts (archive)
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
