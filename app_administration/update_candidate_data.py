#!/usr/bin/env python3
"""
NC Board of Elections Candidate Data Updater

Automatically downloads candidate filing data during active filing periods.
Knows when to pull data based on NC election calendar.
"""

import os
import sys
import hashlib
import requests
from datetime import datetime, date
from pathlib import Path
import pandas as pd

# Configuration
BASE_URL = "https://s3.amazonaws.com/dl.ncsbe.gov/Elections"
DOC_DIR = Path(__file__).parent.parent / "doc"
ENCODING = "latin-1"

# NC Election Filing Periods (approximate - may vary by year)
FILING_PERIODS = {
    # Municipal elections (odd years) - typically mid-June to early July
    "municipal": {
        "months": [6, 7],  # June-July
        "odd_year_only": True,
        "url_pattern": "{year}/Candidate%20Filing/Candidate_Listing_{year}.csv",
        "description": "Municipal Election Filing"
    },
    # State/Federal primary (even years) - typically December to February
    "state_federal": {
        "months": [12, 1, 2],  # Dec-Feb (Dec is previous year)
        "odd_year_only": False,
        "url_pattern": "{year}/Candidate%20Filing/Candidate_Listing_{year}.csv",
        "description": "State/Federal Election Filing"
    }
}

def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    if not filepath.exists():
        return None
    
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def is_filing_period_active(check_date=None):
    """
    Determine if we're currently in a filing period.
    
    Returns:
        tuple: (bool, str, int) - (is_active, period_type, target_year)
    """
    if check_date is None:
        check_date = date.today()
    
    current_month = check_date.month
    current_year = check_date.year
    
    # Check municipal filing (June-July of odd years for that year's election)
    if current_year % 2 == 1 and current_month in FILING_PERIODS["municipal"]["months"]:
        return True, "municipal", current_year
    
    # Check state/federal filing (Dec-Feb for next year's election)
    if current_year % 2 == 1 and current_month == 12:
        # December of odd year = filing for next year (even year)
        return True, "state_federal", current_year + 1
    elif current_year % 2 == 0 and current_month in [1, 2]:
        # Jan-Feb of even year = still filing for that year
        return True, "state_federal", current_year
    
    return False, None, None

def build_download_url(year, period_type):
    """Build the download URL for the candidate file."""
    pattern = FILING_PERIODS[period_type]["url_pattern"]
    filename = pattern.format(year=year)
    return f"{BASE_URL}/{filename}"

def download_candidate_data(url, dest_path):
    """Download candidate data from NC BOE."""
    print(f"Downloading from: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save to temporary file first
        temp_path = dest_path.with_suffix('.tmp')
        temp_path.write_bytes(response.content)
        
        return temp_path
    
    except requests.exceptions.RequestException as e:
        print(f"✗ Download failed: {e}")
        return None

def verify_data_quality(filepath):
    """Verify the downloaded CSV has expected structure."""
    try:
        df = pd.read_csv(filepath, encoding=ENCODING, nrows=10)
        
        # Check for key columns
        required_cols = ['county_name', 'contest_name', 'name_on_ballot']
        missing = [col for col in required_cols if col not in df.columns]
        
        if missing:
            print(f"⚠️  Warning: Missing columns: {missing}")
            return False
        
        return True
    
    except Exception as e:
        print(f"✗ Data verification failed: {e}")
        return False

def analyze_new_data(filepath):
    """Provide quick summary of the candidate data."""
    try:
        df = pd.read_csv(filepath, encoding=ENCODING)
        
        print("\n" + "="*80)
        print("DATA SUMMARY")
        print("="*80)
        print(f"Total candidates: {len(df):,}")
        print(f"Counties: {df['county_name'].nunique()}")
        print(f"Contests: {df['contest_name'].nunique()}")
        
        # Forsyth County specific
        forsyth = df[df['county_name'] == 'FORSYTH']
        if len(forsyth) > 0:
            print(f"\nFORSYTH COUNTY:")
            print(f"  Candidates: {len(forsyth)}")
            print(f"  Contests: {forsyth['contest_name'].nunique()}")
            
            # Party breakdown
            if 'party_candidate' in forsyth.columns:
                party_counts = forsyth['party_candidate'].value_counts()
                print(f"\n  Party breakdown:")
                for party, count in party_counts.items():
                    print(f"    {party}: {count}")
            
            # Top contests
            contest_counts = forsyth['contest_name'].value_counts().head(5)
            print(f"\n  Top contests:")
            for contest, count in contest_counts.items():
                print(f"    {contest}: {count} candidates")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"⚠️  Analysis warning: {e}")

def main():
    """Main execution."""
    print("="*80)
    print("NC Board of Elections - Candidate Data Updater")
    print(f"Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Check if we're in a filing period
    is_active, period_type, target_year = is_filing_period_active()
    
    if not is_active:
        # Not in filing period - check if user wants to force download
        if '--force' in sys.argv:
            # Allow manual year specification
            try:
                target_year = int(sys.argv[sys.argv.index('--force') + 1])
                # Guess period type based on year
                period_type = "municipal" if target_year % 2 == 1 else "state_federal"
                print(f"⚠️  Not in filing period, but forcing download for {target_year}")
            except (IndexError, ValueError):
                print("✗ Not currently in a filing period.")
                print("\nFiling Periods:")
                print("  Municipal (odd years): June-July")
                print("  State/Federal (even years): December-February")
                print("\nTo force download: python3 update_candidate_data.py --force YEAR")
                sys.exit(0)
        else:
            print("ℹ️  Not currently in a filing period.")
            print("\nNext filing periods:")
            current_year = date.today().year
            if current_year % 2 == 1:
                print(f"  Municipal {current_year}: June-July {current_year}")
                print(f"  State/Federal {current_year + 1}: December {current_year} - February {current_year + 1}")
            else:
                print(f"  Municipal {current_year + 1}: June-July {current_year + 1}")
            
            print("\nTo force download: python3 update_candidate_data.py --force YEAR")
            sys.exit(0)
    
    period_info = FILING_PERIODS[period_type]
    print(f"✓ Active filing period detected: {period_info['description']}")
    print(f"  Target year: {target_year}")
    print(f"  Period type: {period_type}\n")
    
    # Build URL and file path
    url = build_download_url(target_year, period_type)
    dest_path = DOC_DIR / f"Candidate_Listing_{target_year}.csv"
    
    # Check if file exists and get hash
    existing_hash = get_file_hash(dest_path)
    if existing_hash:
        print(f"ℹ️  Existing file found: {dest_path.name}")
        print(f"  Hash: {existing_hash[:12]}...")
    
    # Download new data
    temp_path = download_candidate_data(url, dest_path)
    if not temp_path:
        sys.exit(1)
    
    # Verify data quality
    if not verify_data_quality(temp_path):
        print("✗ Data quality check failed")
        temp_path.unlink()
        sys.exit(1)
    
    # Check if file changed
    new_hash = get_file_hash(temp_path)
    print(f"✓ Download complete")
    print(f"  New hash: {new_hash[:12]}...")
    
    if existing_hash == new_hash:
        print("\nℹ️  No changes detected - file is already current")
        temp_path.unlink()
        
        if '--analyze' in sys.argv:
            analyze_new_data(dest_path)
    else:
        # Move temp file to final location
        temp_path.replace(dest_path)
        print(f"\n✓ File updated: {dest_path}")
        print(f"  Size: {dest_path.stat().st_size:,} bytes")
        
        # Analyze new data
        analyze_new_data(dest_path)
        
        # Suggest next steps
        print("NEXT STEPS:")
        print("  1. Run ballot matching analysis:")
        print(f"     python3 analyze_candidates.py --year {target_year}")
        print("  2. Check for new Forsyth County candidates")
        print("  3. Update strategic analysis documents")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
