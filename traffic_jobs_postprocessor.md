# Traffic Jobs Post-Processor

## Full Script

```python
# 🕒 2025-12-03-10-20-00

# Extra_Duty/traffic_jobs_postprocessor.py

# Author: R. A. Carucci

# Purpose: Post-processor that consumes scraped CSVs and text templates, builds master 2025 dataset, produces Excel workbook with awarded/not-awarded sheets and monthly summaries

import os
import re
import glob
from datetime import datetime
from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import json

# ============================================================

# CONFIGURATION

# ============================================================

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent / 'config.json'
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

# ============================================================

# UTILITY FUNCTIONS

# ============================================================

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

# ============================================================

# PARSING FUNCTIONS

# ============================================================

def parse_date(date_str): """Normalize date string to YYYY-MM-DD format.""" if pd.isna(date_str) or not date_str: return None
    
    
    date_str = str(date_str).strip()
    
    # Try common formats
    formats = [
        "%m/%d/%y",      # 11/03/25
        "%m/%d/%Y",      # 11/03/2025
        "%Y-%m-%d",      # 2025-11-03
        "%m-%d-%Y",      # 11-03-2025
        "%m-%d-%y",      # 11-03-25
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Handle 2-digit years
            if dt.year < 100:
                dt = dt.replace(year=dt.year + 2000)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return date_str  # Return as-is if can't parse
    
    

def normalize_time(time_str): """Normalize time string to HH:MM-HH:MM format.""" if pd.isna(time_str) or not time_str: return None
    
    
    time_str = str(time_str).strip()
    
    # Remove spaces around dash/hyphen
    time_str = re.sub(r'\\\\s*[---]\\\\s*', '-', time_str)
    
    # Handle HHMM format (0800 - 1800 -> 08:00-18:00)
    match = re.match(r'(\\\\d{4})\\\\s*-\\\\s*(\\\\d{4})', time_str)
    if match:
        start, end = match.groups()
        return f"{start[:2]}:{start[2:]}-{end[:2]}:{end[2:]}"
    
    # Handle HH:MM-HH:MM format
    match = re.match(r'(\\\\d{1,2}:\\\\d{2})\\\\s*-\\\\s*(\\\\d{1,2}:\\\\d{2})', time_str)
    if match:
        start, end = match.groups()
        # Pad hours if needed
        start = start.zfill(5)
        end = end.zfill(5)
        return f"{start}-{end}"
    
    return time_str
    
    

def calculate_hours(time_str): """Calculate hours from time range string.""" if pd.isna(time_str) or not time_str: return None
    
    
    try:
        time_str = normalize_time(time_str)
        match = re.match(r'(\\\\d{2}):(\\\\d{2})-(\\\\d{2}):(\\\\d{2})', time_str)
        if match:
            sh, sm, eh, em = map(int, match.groups())
            start_mins = sh * 60 + sm
            end_mins = eh * 60 + em
            return round((end_mins - start_mins) / 60, 2)
    except:
        pass
    return None
    
    

def read_scraped_csvs(folder, pattern): """Read all scraped CSV files and combine into one DataFrame.""" csv_path = Path(folder) files = list(csv_path.glob(pattern))
    
    
    if not files:
        print(f"⚠️ No CSV files found matching {pattern} in {folder}")
        return pd.DataFrame()
    
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f, dtype=str)
            df['_source_file'] = f.name
            df['_source_type'] = 'scraped_csv'
            dfs.append(df)
            print(f"  ✓ Loaded {f.name}: {len(df)} rows")
        except Exception as e:
            print(f"  ✗ Error reading {f.name}: {e}")
    
    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        return combined
    return pd.DataFrame()
    
    

def parse_dataset1_file(filepath): """Parse a Dataset 1 text template file (my signups).""" with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
    
    
    # Extract metadata
    report_date = None
    my_name = None
    
    for line in content.split('\\\\n'):
        if line.startswith('REPORT_DATE:'):
            report_date = line.split(':', 1)[1].strip()
        elif line.startswith('MY_NAME:'):
            my_name = line.split(':', 1)[1].strip()
    
    # Extract data between markers
    data_match = re.search(r'---DATA_START---\\\\s*(.*?)\\\\s*---DATA_END---', content, re.DOTALL)
    if not data_match:
        # Try without markers - assume data starts after metadata
        lines = [l.strip() for l in content.split('\\\\n') if l.strip() and not l.startswith('#') and ':' not in l[:20]]
    else:
        lines = [l.strip() for l in data_match.group(1).split('\\\\n') if l.strip()]
    
    # Parse 7-line blocks
    records = []
    i = 0
    while i + 6 < len(lines):
        record = {
            'Job #': lines[i],
            'Description': lines[i+1],
            'Date': lines[i+2],
            'Times': lines[i+3],
            'Customer': lines[i+4],
            'Address': lines[i+5],
            'Status': lines[i+6],
            '_report_date': report_date,
            '_source_file': Path(filepath).name,
            '_source_type': 'dataset1_txt'
        }
        records.append(record)
        i += 7
    
    return pd.DataFrame(records)
    
    

def parse_dataset2_file(filepath): """Parse a Dataset 2 text template file (assigned workers).""" with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
    
    
    # Extract metadata
    signup_date = None
    my_name = None
    
    for line in content.split('\\\\n'):
        if line.startswith('SIGNUP_DATE:'):
            signup_date = line.split(':', 1)[1].strip()
        elif line.startswith('MY_NAME:'):
            my_name = line.split(':', 1)[1].strip()
    
    # Extract data between markers
    data_match = re.search(r'---DATA_START---\\\\s*(.*?)\\\\s*---DATA_END---', content, re.DOTALL)
    if not data_match:
        lines = [l.strip() for l in content.split('\\\\n') if l.strip() and not l.startswith('#') and ':' not in l[:15]]
    else:
        lines = [l.strip() for l in data_match.group(1).split('\\\\n') if l.strip()]
    
    # Parse 6-line blocks
    records = []
    i = 0
    while i + 5 < len(lines):
        record = {
            'Employee': lines[i],
            'Customer': lines[i+1],
            'Description': lines[i+2],
            'Location': lines[i+3],
            'Times': lines[i+4],
            'Vehicle': lines[i+5],
            '_signup_date': signup_date,
            '_source_file': Path(filepath).name,
            '_source_type': 'dataset2_txt'
        }
        records.append(record)
        i += 6
    
    return pd.DataFrame(records)
    
    

def read_dataset_files(folder, parser_func, file_pattern="*.txt"): """Read all text files from a folder using the specified parser.""" folder_path = Path(folder)
    
    
    if not folder_path.exists():
        print(f"⚠️ Folder does not exist: {folder}")
        return pd.DataFrame()
    
    files = list(folder_path.glob(file_pattern))
    
    if not files:
        print(f"⚠️ No files found in {folder}")
        return pd.DataFrame()
    
    dfs = []
    for f in files:
        try:
            df = parser_func(f)
            if not df.empty:
                dfs.append(df)
                print(f"  ✓ Loaded {f.name}: {len(df)} rows")
        except Exception as e:
            print(f"  ✗ Error parsing {f.name}: {e}")
    
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()
    
    

# ============================================================

# DATA PROCESSING

# ============================================================

def build_master_dataset(scraped_df, dataset1_df, dataset2_df, config): """Build unified master dataset from all sources."""
    
    
    my_name = config["my_name"]
    target_year = config["target_year"]
    
    # Combine scraped CSV and Dataset 1 text files (both are "my signups")
    my_signups_dfs = []
    
    if not scraped_df.empty:
        scraped_df = scraped_df.copy()
        scraped_df['Employee'] = my_name
        my_signups_dfs.append(scraped_df)
    
    if not dataset1_df.empty:
        dataset1_df = dataset1_df.copy()
        dataset1_df['Employee'] = my_name
        my_signups_dfs.append(dataset1_df)
    
    if my_signups_dfs:
        my_signups = pd.concat(my_signups_dfs, ignore_index=True)
    else:
        my_signups = pd.DataFrame()
    
    # Normalize columns
    if not my_signups.empty:
        # Ensure consistent column names
        col_map = {
            'Job #': 'Job #',
            'Job_#': 'Job #',
            'job_#': 'Job #',
            'Description': 'Description',
            'Date': 'Date',
            'Times': 'Times',
            'Customer': 'Customer',
            'Address': 'Address',
            'Location': 'Address',
            'Status': 'Status',
            'Immediate Award': 'Immediate Award'
        }
        my_signups = my_signups.rename(columns={k: v for k, v in col_map.items() if k in my_signups.columns})
    
        # Normalize dates and times
        my_signups['Date'] = my_signups['Date'].apply(parse_date)
        my_signups['Times'] = my_signups['Times'].apply(normalize_time)
        my_signups['Hours'] = my_signups['Times'].apply(calculate_hours)
    
        # Filter to target year
        my_signups['_year'] = my_signups['Date'].apply(lambda x: int(x[:4]) if x and len(x) >= 4 else None)
        my_signups = my_signups[my_signups['_year'] == target_year].copy()
    
        # Add month for summaries
        my_signups['Month'] = my_signups['Date'].apply(lambda x: x[:7] if x else None)
    
    # Process Dataset 2 (assigned workers)
    assigned_others = pd.DataFrame()
    if not dataset2_df.empty:
        assigned_others = dataset2_df.copy()
        assigned_others['Date'] = assigned_others['_signup_date'].apply(parse_date)
        assigned_others['Times'] = assigned_others['Times'].apply(normalize_time)
    
        # Mark which are "me" vs "other"
        assigned_others['IsMe'] = assigned_others['Employee'].str.lower() == my_name.lower()
    
    # Deduplicate my_signups
    if not my_signups.empty:
        dedup_keys = [k for k in config["dedup_keys"] if k in my_signups.columns]
        before_count = len(my_signups)
        my_signups = my_signups.drop_duplicates(subset=dedup_keys, keep='last')
        after_count = len(my_signups)
        if before_count > after_count:
            print(f"  ℹ️ Deduplicated: {before_count} → {after_count} rows")
    
    # Create status flags
    if not my_signups.empty:
        my_signups['Status'] = my_signups['Status'].fillna('Unknown')
        my_signups['IsInvoiced'] = my_signups['Status'].str.lower() == 'invoiced'
        my_signups['IsRequested'] = my_signups['Status'].str.lower() == 'requested'
    
        # Cross-reference with assigned_others to find jobs I didn't get
        # For each of my "Requested" jobs, check if someone else was assigned
        my_signups['AssignedToOther'] = ''
    
        if not assigned_others.empty:
            others_only = assigned_others[~assigned_others['IsMe']].copy()
    
            for idx, row in my_signups[my_signups['IsRequested']].iterrows():
                # Find matching assignments on same date
                matches = others_only[
                    (others_only['Date'] == row['Date']) &
                    (others_only['Customer'].str.lower() == str(row['Customer']).lower())
                ]
                if not matches.empty:
                    assigned_names = ', '.join(matches['Employee'].unique())
                    my_signups.at[idx, 'AssignedToOther'] = assigned_names
    
    return my_signups, assigned_others
    
    

def create_summary_stats(df): """Create monthly and overall summary statistics.""" if df.empty: return pd.DataFrame(), {}
    
    
    # Monthly summary
    monthly = df.groupby('Month').agg({
        'Job #': 'count',
        'IsInvoiced': 'sum',
        'IsRequested': 'sum',
        'Hours': 'sum'
    }).reset_index()
    
    monthly.columns = ['Month', 'Total Signups', 'Awarded', 'Not Awarded', 'Total Hours (Awarded)']
    
    # Recalculate hours for awarded only
    awarded_hours = df[df['IsInvoiced']].groupby('Month')['Hours'].sum().reset_index()
    awarded_hours.columns = ['Month', 'Awarded Hours']
    monthly = monthly.merge(awarded_hours, on='Month', how='left')
    monthly['Awarded Hours'] = monthly['Awarded Hours'].fillna(0)
    monthly = monthly.drop(columns=['Total Hours (Awarded)'])
    
    # Award rate
    monthly['Award Rate %'] = (monthly['Awarded'] / monthly['Total Signups'] * 100).round(1)
    
    # Overall stats
    overall = {
        'Total Signups': len(df),
        'Awarded (Invoiced)': df['IsInvoiced'].sum(),
        'Not Awarded (Requested)': df['IsRequested'].sum(),
        'Award Rate %': round(df['IsInvoiced'].sum() / len(df) * 100, 1) if len(df) > 0 else 0,
        'Total Hours (Awarded)': df[df['IsInvoiced']]['Hours'].sum(),
        'Unique Customers': df['Customer'].nunique(),
        'Date Range': f"{df['Date'].min()} to {df['Date'].max()}"
    }
    
    return monthly, overall
    
    

# ============================================================

# EXCEL OUTPUT

# ============================================================

def style_worksheet(ws, header_row=1): """Apply consistent styling to worksheet.""" header_fill = PatternFill('solid', fgColor='4472C4') header_font = Font(bold=True, color='FFFFFF') thin_border = Border( left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin') )
    
    
    # Style header row
    for cell in ws[header_row]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        cell.border = thin_border
    
    # Auto-width columns
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            except:
                pass
        ws.column_dimensions[col_letter].width = min(max_len + 2, 50)
    
    

def df_to_sheet(ws, df, start_row=1): """Write DataFrame to worksheet.""" for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), start_row): for c_idx, value in enumerate(row, 1): ws.cell(row=r_idx, column=c_idx, value=value)

def create_output_workbook(my_signups, assigned_others, monthly_summary, overall_stats, config): """Create the final Excel workbook."""
    
    
    wb = Workbook()
    
    # Output columns for main sheets
    output_cols = ['Job #', 'Date', 'Month', 'Times', 'Hours', 'Customer', 'Address',
                   'Description', 'Status', 'Employee', 'AssignedToOther']
    
    # Filter to available columns
    if not my_signups.empty:
        available_cols = [c for c in output_cols if c in my_signups.columns]
    else:
        available_cols = output_cols
    
    # === Sheet 1: All Jobs ===
    ws_all = wb.active
    ws_all.title = "All Jobs"
    
    if not my_signups.empty:
        df_to_sheet(ws_all, my_signups[available_cols])
        style_worksheet(ws_all)
    
    # === Sheet 2: Awarded (Invoiced) ===
    ws_awarded = wb.create_sheet("Awarded")
    
    if not my_signups.empty:
        awarded = my_signups[my_signups['IsInvoiced']][available_cols]
        if not awarded.empty:
            df_to_sheet(ws_awarded, awarded)
            style_worksheet(ws_awarded)
    
            # Highlight in green
            green_fill = PatternFill('solid', fgColor='C6EFCE')
            for row in ws_awarded.iter_rows(min_row=2, max_row=ws_awarded.max_row):
                for cell in row:
                    cell.fill = green_fill
    
    # === Sheet 3: Not Awarded ===
    ws_not_awarded = wb.create_sheet("Not Awarded")
    
    if not my_signups.empty:
        not_awarded = my_signups[my_signups['IsRequested']][available_cols]
        if not not_awarded.empty:
            df_to_sheet(ws_not_awarded, not_awarded)
            style_worksheet(ws_not_awarded)
    
            # Highlight rows where someone else got it
            orange_fill = PatternFill('solid', fgColor='FFEB9C')
            assigned_col_idx = available_cols.index('AssignedToOther') + 1 if 'AssignedToOther' in available_cols else None
    
            if assigned_col_idx:
                for row in ws_not_awarded.iter_rows(min_row=2, max_row=ws_not_awarded.max_row):
                    if row[assigned_col_idx - 1].value:  # Has assigned other
                        for cell in row:
                            cell.fill = orange_fill
    
    # === Sheet 4: Assigned Workers (Dataset 2) ===
    ws_assigned = wb.create_sheet("Other Assignments")
    
    if not assigned_others.empty:
        assigned_cols = ['Date', 'Employee', 'Customer', 'Description', 'Location', 'Times', 'Vehicle', 'IsMe']
        assigned_cols = [c for c in assigned_cols if c in assigned_others.columns]
        df_to_sheet(ws_assigned, assigned_others[assigned_cols])
        style_worksheet(ws_assigned)
    
        # Highlight my rows
        green_fill = PatternFill('solid', fgColor='C6EFCE')
        is_me_col = assigned_cols.index('IsMe') + 1 if 'IsMe' in assigned_cols else None
    
        if is_me_col:
            for row in ws_assigned.iter_rows(min_row=2, max_row=ws_assigned.max_row):
                if row[is_me_col - 1].value == True:
                    for cell in row:
                        cell.fill = green_fill
    
    # === Sheet 5: Monthly Summary ===
    ws_summary = wb.create_sheet("Monthly Summary")
    
    if not monthly_summary.empty:
        df_to_sheet(ws_summary, monthly_summary)
        style_worksheet(ws_summary)
    
    # Add overall stats below monthly
    if overall_stats:
        start_row = ws_summary.max_row + 3
        ws_summary.cell(row=start_row, column=1, value="OVERALL STATISTICS").font = Font(bold=True, size=12)
    
        for i, (key, value) in enumerate(overall_stats.items(), start=start_row + 1):
            ws_summary.cell(row=i, column=1, value=key)
            ws_summary.cell(row=i, column=2, value=value)
    
    # === Sheet 6: Instructions ===
    ws_instructions = wb.create_sheet("Instructions")
    
    instructions = [
        ["TRAFFIC JOBS 2025 MASTER WORKBOOK"],
        [""],
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Employee:", config["my_name"]],
        [""],
        ["SHEETS:"],
        ["All Jobs", "Complete list of all signups for 2025"],
        ["Awarded", "Jobs with Status = Invoiced (green highlight)"],
        ["Not Awarded", "Jobs with Status = Requested (orange = someone else got it)"],
        ["Other Assignments", "Dataset 2 data - workers assigned on specific dates"],
        ["Monthly Summary", "Counts and rates by month"],
        [""],
        ["STATUS MEANINGS:"],
        ["Invoiced", "You were awarded and worked this job"],
        ["Requested", "You signed up but were not selected"],
        [""],
        ["COLUMN: AssignedToOther"],
        ["Shows names of workers who were assigned jobs you requested"],
        [""],
        ["DATA SOURCES:"],
        ["1. Scraped CSVs from VCS portal (Selenium)"],
        ["2. Dataset 1 text files (my signups)"],
        ["3. Dataset 2 text files (assigned workers by date)"],
    ]
    
    for row in instructions:
        ws_instructions.append(row)
    
    ws_instructions['A1'].font = Font(bold=True, size=14)
    ws_instructions.column_dimensions['A'].width = 25
    ws_instructions.column_dimensions['B'].width = 60
    
    # Save workbook
    output_path = Path(config["output_folder"]) / config["output_filename"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    
    return output_path
    
    

# ============================================================

# MAIN

# ============================================================

def main():
    print("=" * 60)
    print("TRAFFIC JOBS POST-PROCESSOR")
    print("=" * 60)
    print(f"Employee: {CONFIG['my_name']}")
    print(f"Target Year: {CONFIG['target_year']}")
    print()
    
    # Setup folders
    print("📁 Setting up folders...")
    ensure_folders_exist(CONFIG)
    print()
    
    # Step 1: Read scraped CSVs
    print("📂 Reading scraped CSVs...")
    scraped_df = read_scraped_csvs(CONFIG["scraped_csv_folder"], CONFIG["scraped_csv_pattern"])
    print(f"   Total scraped rows: {len(scraped_df)}")
    print()
    
    # Step 2: Read Dataset 1 text files
    print("📂 Reading Dataset 1 files (my signups)...")
    dataset1_df = read_dataset_files(CONFIG["dataset1_folder"], parse_dataset1_file)
    print(f"   Total Dataset 1 rows: {len(dataset1_df)}")
    print()
    
    # Step 3: Read Dataset 2 text files
    print("📂 Reading Dataset 2 files (assigned workers)...")
    dataset2_df = read_dataset_files(CONFIG["dataset2_folder"], parse_dataset2_file)
    print(f"   Total Dataset 2 rows: {len(dataset2_df)}")
    print()
    
    # Step 4: Build master dataset
    print("🔧 Building master dataset...")
    my_signups, assigned_others = build_master_dataset(scraped_df, dataset1_df, dataset2_df, CONFIG)
    print(f"   Master dataset rows: {len(my_signups)}")
    print()
    
    # Step 5: Generate summaries
    print("📊 Generating summary statistics...")
    monthly_summary, overall_stats = create_summary_stats(my_signups)
    
    if overall_stats:
        print(f"   Total Signups: {overall_stats['Total Signups']}")
        print(f"   Awarded: {overall_stats['Awarded (Invoiced)']}")
        print(f"   Not Awarded: {overall_stats['Not Awarded (Requested)']}")
        print(f"   Award Rate: {overall_stats['Award Rate %']}%")
    print()
    
    # Step 6: Create Excel output
    print("📝 Creating Excel workbook...")
    output_path = create_output_workbook(my_signups, assigned_others, monthly_summary, overall_stats, CONFIG)
    print(f"   ✅ Saved to: {output_path}")
    print()
    
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
    print(f"\n✓ Master Excel: {output_path.name}")
    print(f"  Location: {CONFIG['output_folder']}")
    
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)

if __name__ == "__main__":
    main()

# 🕒 2025-12-03-10-15-00

# Extra_Duty/scraper_filename_update.py

# Author: R. A. Carucci

# Purpose: Drop-in replacement for the output filename section of vcs_extra_duty_scrape.py - adds timestamped filenames

# ============================================================

# REPLACE THIS SECTION IN vcs_extra_duty_scrape.py

# ============================================================

# OLD:

# OUTPUT_CSV = "vcs_extra_duty_jobs.csv"

# NEW:

from datetime import datetime

def get_output_filename(prefix="vcs_extra_duty_jobs", suffix=""): """Generate timestamped output filename.
    
    
    Args:
        prefix: Base filename (default: vcs_extra_duty_jobs)
        suffix: Optional suffix like '_Q4' or '_fullYear'
    
    Returns:
        Filename like: vcs_extra_duty_jobs_Q4_20251203_1430.csv
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"{prefix}{suffix}_{timestamp}.csv"
    
    

# Usage in main script:

# OUTPUT_CSV = get_output_filename(suffix="_Q4") # -> vcs_extra_duty_jobs_Q4_20251203_1430.csv

# ============================================================

# OPTIONAL: Auto-detect quarter from date range

# ============================================================

def get_quarter_suffix(start_date_str, end_date_str): """Determine quarter suffix from date range.
    
    
    Args:
        start_date_str: Start date as MM/DD/YYYY
        end_date_str: End date as MM/DD/YYYY
    
    Returns:
        Suffix like '_2025Q4' or '_2025_FullYear'
    """
    try:
        start = datetime.strptime(start_date_str, "%m/%d/%Y")
        end = datetime.strptime(end_date_str, "%m/%d/%Y")
        year = start.year
    
        # Check if full year
        if start.month == 1 and start.day == 1 and end.month == 12 and end.day == 31:
            return f"_{year}_FullYear"
    
        # Determine quarter based on start month
        quarter = (start.month - 1) // 3 + 1
        return f"_{year}Q{quarter}"
    except:
        return ""
    
    

# Usage:

# suffix = get_quarter_suffix("10/01/2025", "12/31/2025") # -> "_2025Q4"

# OUTPUT_CSV = get_output_filename(suffix=suffix)

# 🕒 2025-12-03-10-45-00

# Extra_Duty/README_PostProcessor.md

# Author: R. A. Carucci

# Purpose: Documentation for the Traffic Jobs Post-Processor system

# Traffic Jobs Post-Processor

Downstream processing system for VCS Extra Duty job data. Consumes scraped CSVs and manual text templates, builds a master 2025 dataset, and produces Excel reports.

## System Architecture
    
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                        DATA SOURCES                              │
    ├─────────────────────────────────────────────────────────────────┤
    │  1. Selenium Scraper (vcs_extra_duty_scrape.py)                 │
    │     └── Output: vcs_extra_duty_jobs_YYYYQ#_YYYYMMDD_HHMM.csv    │
    │                                                                  │
    │  2. Dataset 1 Text Files (my signups)                           │
    │     └── Template: TEMPLATE_dataset1_my_signups.txt              │
    │                                                                  │
    │  3. Dataset 2 Text Files (assigned workers by date)             │
    │     └── Template: TEMPLATE_dataset2_assigned_workers.txt        │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    POST-PROCESSOR                                │
    │                 traffic_jobs_postprocessor.py                    │
    ├─────────────────────────────────────────────────────────────────┤
    │  • Reads all CSV + TXT inputs                                   │
    │  • Normalizes dates/times                                       │
    │  • Deduplicates on Job # + Date + Customer                      │
    │  • Cross-references Dataset 2 to find who got jobs I didn't     │
    │  • Calculates hours and monthly stats                           │
    └─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    OUTPUT                                        │
    │              TrafficJobs_2025_Master.xlsx                        │
    ├─────────────────────────────────────────────────────────────────┤
    │  Sheet 1: All Jobs           - Complete dataset                  │
    │  Sheet 2: Awarded            - Status = Invoiced (green)         │
    │  Sheet 3: Not Awarded        - Status = Requested (orange if     │
    │                                someone else got it)              │
    │  Sheet 4: Other Assignments  - Dataset 2 data by date            │
    │  Sheet 5: Monthly Summary    - Counts/rates by month             │
    │  Sheet 6: Instructions       - Documentation                     │
    └─────────────────────────────────────────────────────────────────┘
    
    

## Folder Structure
    
    
    C:\\\\Users\\\\carucci_r\\\\OneDrive - City of Hackensack\\\\RAC\\\\Extra_Duty\\\\
    ├── scripts\\\\
    │   ├── vcs_extra_duty_scrape.py        # Selenium scraper
    │   ├── traffic_jobs_postprocessor.py   # Post-processor
    │   └── vcs_extra_duty_jobs_*.csv       # Scraped outputs
    │
    ├── data\\\\
    │   ├── dataset1\\\\                        # My signup text files
    │   │   └── dataset1_2025-11-21.txt
    │   └── dataset2\\\\                        # Assigned workers text files
    │       └── dataset2_2025-11-03.txt
    │
    └── output\\\\
        └── TrafficJobs_2025_Master.xlsx     # Final output
    
    

## Usage

### Step 1: Run the Selenium Scraper
    
    
    :: Start Chrome in debug mode
    chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\\\ChromeDebug"
    
    :: Log in to VCS, set date range, then run:
    cd "C:\\\\Users\\\\carucci_r\\\\OneDrive - City of Hackensack\\\\RAC\\\\Extra_Duty\\\\scripts"
    python vcs_extra_duty_scrape.py
    
    

Output: `vcs_extra_duty_jobs_2025Q4_20251203_1430.csv`

### Step 2: Capture Dataset 2 (for days you weren't selected)

1. Go to the VCS portal's "Assigned Workers" view
2. Select a specific date you signed up for but didn't get
3. Copy all assigned worker data
4. Paste into a new text file using the template format
5. Save as `dataset2_YYYY-MM-DD.txt` in the `data\\\\dataset2\\\\` folder

### Step 3: Run the Post-Processor
    
    
    cd "C:\\\\Users\\\\carucci_r\\\\OneDrive - City of Hackensack\\\\RAC\\\\Extra_Duty\\\\scripts"
    python traffic_jobs_postprocessor.py
    
    

Output: `TrafficJobs_2025_Master.xlsx`

## Configuration

Edit the `CONFIG` dict in `traffic_jobs_postprocessor.py`:
    
    
    CONFIG = {
        "my_name": "Carucci, Robert",
        "scraped_csv_folder": r"C:\\\\...\\\\scripts",
        "dataset1_folder": r"C:\\\\...\\\\data\\\\dataset1",
        "dataset2_folder": r"C:\\\\...\\\\data\\\\dataset2",
        "output_folder": r"C:\\\\...\\\\output",
        "output_filename": "TrafficJobs_2025_Master.xlsx",
        "target_year": 2025,
        "dedup_keys": ["Job #", "Date", "Customer"]
    }
    
    

## Output Columns

| Column | Description | 
| ---- | ----  |
| Job # | Unique job identifier | 
| Date | Job date (YYYY-MM-DD) | 
| Month | Year-month for grouping | 
| Times | Shift times (HH:MM-HH:MM) | 
| Hours | Calculated hours | 
| Customer | Company requesting service | 
| Address | Job location | 
| Description | Job type (Traffic Control, Milling, etc.) | 
| Status | Invoiced (awarded) or Requested (not awarded) | 
| Employee | Your name | 
| AssignedToOther | Names of workers who got jobs you didn't | 

## Key Features

### Cross-Reference Logic

When you have a "Requested" job in Dataset 1 and a matching Dataset 2 file for the same date:

- The script matches on **Date + Customer**
- If another worker was assigned that job, their name appears in `AssignedToOther`

### Deduplication

- Jobs are deduplicated on `Job # + Date + Customer`
- Latest source wins (if same job appears in both scraped CSV and text file)

### Monthly Summary

Auto-calculated stats:

- Total Signups
- Awarded count
- Not Awarded count
- Award Rate %
- Hours worked

## Text File Templates

### Dataset 1 (My Signups) - 7 lines per job
    
    
    REPORT_DATE: 2025-11-21
    MY_NAME: Carucci, Robert
    
    ---DATA_START---
    6119
    Traffic Control - Milling
    11/21/25
    07:00-15:00
    PSE&G Gas (Oradell) MC 314
    Euclid ave/Grand ave
    Requested
    ---DATA_END---
    
    

### Dataset 2 (Assigned Workers) - 6 lines per person
    
    
    SIGNUP_DATE: 2025-11-03
    MY_NAME: Carucci, Robert
    
    ---DATA_START---
    Briggs, Sean
    Veolia Water - Construction
    Traffic Control
    147 Holt St
    0730 - 1530
    110
    ---DATA_END---
    
    

## Future Enhancements

1. **Dataset 2 Scraper** - Automate the "Assigned Workers" page
2. **Database Backend** - SQLite for historical queries
3. **Power BI Integration** - Direct refresh from master Excel
4. **Multi-Employee Support** - Track multiple workers

# 🕒 2025-11-29-14-45-00

# traffic_jobs/TEMPLATE_dataset1_my_signups.txt

# Author: R. A. Carucci

# Purpose: Template for pasting Dataset 1 - My job signups from the web portal

# ============================================================

# INSTRUCTIONS:

# 1. Copy your signup data from the portal (Job #, Description, Date, Times, Customer, Address, Status)

# 2. Paste below the DATA_START line

# 3. Save this file as: dataset1_YYYY-MM-DD.txt (e.g., dataset1_2025-11-03.txt)

# 4. Each record = 7 lines (no blank lines between records)

# ============================================================

REPORT_DATE: 2025-11-03 MY_NAME: Carucci, Robert

# ============================================================

# EXPECTED FORMAT (7 lines per job):

# Line 1: Job

# Line 2: Description

# Line 3: Date (MM/DD/YY)

# Line 4: Times (HH:MM-HH:MM)

# Line 5: Customer

# Line 6: Address

# Line 7: Status (Invoiced or Requested)

# ============================================================

--DATA_START-- 6059 Traffic Control 11/03/25 07:30-15:30 Veolia Water - Construction 147 Holt St Requested 6083 Traffic Control 11/05/25 07:30-15:30 Veolia Water - Construction American Legion Dr & Prospect Ave Requested 6113 Traffic Control - Milling 11/13/25 07:00-16:00 PSE&G Gas (Oradell) MC 314 Berry st/Railroad ave Invoiced --DATA_END--

# 🕒 2025-11-29-14-45-00

# traffic_jobs/TEMPLATE_dataset2_assigned_workers.txt

# Author: R. A. Carucci

# Purpose: Template for pasting Dataset 2 - Workers assigned to jobs on a specific date (to identify jobs I signed up for but was NOT awarded)

# ============================================================

# INSTRUCTIONS:

# 1. Go to the portal for the DATE you signed up but were NOT awarded

# 2. Copy the list of workers who WERE assigned that day

# 3. Paste below the DATA_START line

# 4. Save this file as: dataset2_YYYY-MM-DD.txt (e.g., dataset2_2025-11-03.txt)

# 5. Each record = 6 lines (no blank lines between records)

# ============================================================

# DATE THIS DATA REPRESENTS (the day you were NOT selected):

SIGNUP_DATE: 2025-11-03 MY_NAME: Carucci, Robert

# ============================================================

# EXPECTED FORMAT (6 lines per assigned worker):

# Line 1: Employee (Last, First)

# Line 2: Customer

# Line 3: Description

# Line 4: Location

# Line 5: Times (HHMM - HHMM)

# Line 6: Vehicle

# ============================================================

--DATA_START-- Briggs, Sean Legacy Development Group Traffic Control 359 Main Street 0800 - 1800 110 Scarpa, Frank Veolia Water - Construction Traffic Control 147 Holt St 0730 - 1530 139 --DATA_END--
```
